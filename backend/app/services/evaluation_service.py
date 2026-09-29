"""
Bridge between the database layer and the PURE calculation engine.

Responsibilities:
- Convert a DB Instrument row → engine Instrument (declared unit → base grams).
- Derive catalogue Features from instrument attributes.
- Build the EvaluationContext (MPE context, resolution during test in grams,
  auto-zero status).
- Save a test page: RAW observations (immutable intent) + engine output
  (computed cache, verdict, warnings) per Golden Rules #1/#3.
- Preview the overall outcome (required kinds vs current verdicts).
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..engine.adapter import to_base_obs
from ..engine.catalogue import Features, find_entry, required_kinds
from ..engine.classification import build_instrument
from ..engine.context import EvaluationContext
from ..engine.evaluate import evaluate_test, overall_outcome
from ..engine.ruleset import load_ruleset
from ..engine.units import to_base
from ..engine.validate import validate_instrument
from ..models import Evaluation, Instrument, TestRecord, User

# Statuses in which observations may still be written (doc §5.2 / §4 rules)
EDITABLE_STATUSES = ("DRAFT", "IN_PROGRESS", "RETURNED")


# ------------------------------------------------------------------ converters
def to_engine_instrument(inst: Instrument):
    """DB row (values in the DECLARED unit) → engine Instrument (base grams)."""
    return build_instrument(
        inst.accuracy_class,
        str(inst.min_capacity),
        inst.unit,
        [{"e": str(r.e), "d": str(r.d), "max": str(r.max_capacity)} for r in inst.ranges],
    )


def features_from(inst: Instrument) -> Features:
    """Catalogue applicability flags derived from instrument attributes (doc §6.8)."""
    zd = inst.zero_devices or {}
    td = inst.tare_devices or {}
    category = (inst.category or "").lower()
    supplies = set(inst.power_supply_category or [])
    return Features(
        non_self=inst.indication_type == "NON_SELF",
        has_tare=any(bool(v) for v in td.values()),
        has_printer_or_storage=inst.printer in ("BUILT_IN", "CONNECTED"),
        has_zero_setting=any(bool(v) for v in zd.values()),
        mains_ac="MAINS_AC" in supplies,
        vehicle_powered=bool(supplies & {"VEHICLE_12V", "VEHICLE_24V"}),
        liable_to_tilt=(inst.level_indicator is False) or bool(inst.direct_sales_to_public),
        rolling_load=("weighbridge" in category) or ("rail" in category),
        direct_sales=bool(inst.direct_sales_to_public),
    )


def engine_context(ev: Evaluation, inst: Instrument) -> EvaluationContext:
    resolution = None
    if ev.resolution_during_test is not None:
        resolution = to_base(ev.resolution_during_test, inst.unit)   # declared → grams
    return EvaluationContext(
        mpe_context=ev.mpe_context,
        resolution=resolution,
        auto_zero_status=ev.auto_zero_status or "NON_EXISTENT",
    )


def validate_new_instrument(inst: Instrument) -> None:
    """Reject instruments violating R 76-1 Table 3 with a structured 400."""
    errors, _warns = validate_instrument(load_ruleset(), to_engine_instrument(inst))
    if errors:
        raise HTTPException(
            status_code=400,
            detail={"message": "Instrument violates OIML R 76-1 Table 3 (classification)",
                    "errors": errors},
        )


# ----------------------------------------------------------------- report no.
def next_report_no(db: Session) -> str:
    """LM/NAWI/<year>/0001 — zero-padded, per-year sequence."""
    year = Evaluation.created_at.server_default  # not used; see below
    from datetime import datetime, timezone
    year = datetime.now(timezone.utc).year
    prefix = f"LM/NAWI/{year}/"
    last = db.scalar(
        select(Evaluation.report_no)
        .where(Evaluation.report_no.like(prefix + "%"))
        .order_by(Evaluation.report_no.desc())
        .limit(1)
    )
    seq = int(last.rsplit("/", 1)[-1]) + 1 if last else 1
    return f"{prefix}{seq:04d}"


# -------------------------------------------------------------- observation RBAC
def can_enter_observations(user: User, ev: Evaluation) -> bool:
    """
    Doc §5.1: only the ENGINEER enters/edits observations — 'own or assigned'.
    Allowed when the user created the evaluation or is its assigned observer;
    an unassigned evaluation is closed to everyone else.
    """
    return user.role == "ENGINEER" and (
        ev.created_by == user.id or ev.observer_id == user.id
    )


# ------------------------------------------------------------------ save page
def save_test_record(
    db: Session, ev: Evaluation, user: User, *, kind: str, instance_no: int,
    observations: dict, condition_label: str | None, test_date, environment: dict | None,
    remarks: str | None,
) -> TestRecord:
    """
    Upsert one R 76-2 page (kind + instance_no unique per evaluation):
      1. status guard (read-only once SUBMITTED — doc §4),
      2. unit-convert RAW observations to base grams (adapter),
      3. run the pure engine → computed + verdict + warnings,
      4. persist; auto-transition DRAFT/RETURNED → IN_PROGRESS.
    """
    if ev.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Observations are read-only while the evaluation is {ev.status}. "
                   f"A reviewer must RETURN it for corrections.",
        )

    rs = load_ruleset(ev.ruleset_id)
    inst = ev.instrument
    engine_inst = to_engine_instrument(inst)
    ctx = engine_context(ev, inst)
    obs_grams = to_base_obs(observations, inst.unit)     # Golden Rule #4 at the boundary

    try:
        result = evaluate_test(kind, rs, engine_inst, ctx, obs_grams)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    row = db.scalar(
        select(TestRecord).where(
            TestRecord.evaluation_id == ev.id,
            TestRecord.kind == kind,
            TestRecord.instance_no == instance_no,
        )
    )
    if row is None:
        row = TestRecord(evaluation_id=ev.id, kind=kind, instance_no=instance_no,
                         created_by=user.id)
        db.add(row)

    entry = find_entry(rs, kind) or {}
    row.form_no = entry.get("form_no")
    row.condition_label = condition_label
    row.test_date = test_date
    row.environment = environment
    row.observations = observations          # RAW as entered (audit trail)
    row.computed = result["computed"]
    row.verdict = result["verdict"]
    row.warnings = result["warnings"]
    row.remarks = remarks
    row.observer_id = user.id

    if ev.status in ("DRAFT", "RETURNED"):
        ev.status = "IN_PROGRESS"            # doc §5.2 transitions

    db.flush()
    return row


# ------------------------------------------------------------------ outcome
def verdicts_map(db: Session, ev: Evaluation) -> dict[str, str]:
    rows = db.scalars(select(TestRecord).where(TestRecord.evaluation_id == ev.id)).all()
    return {r.kind: (r.verdict or "PENDING") for r in rows}


def outcome_preview(db: Session, ev: Evaluation) -> dict:
    """Required kinds for THIS instrument + current verdicts + overall outcome."""
    rs = load_ruleset(ev.ruleset_id)
    engine_inst = to_engine_instrument(ev.instrument)
    required = required_kinds(rs, engine_inst, features_from(ev.instrument))
    verdicts = verdicts_map(db, ev)
    return {
        "required": required,
        "verdicts": verdicts,
        "outcome": overall_outcome(required, verdicts),
    }