"""Compile an Evaluation (+ related rows) into the complete report model."""
from __future__ import annotations

import base64
from pathlib import Path

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models import Attachment, Evaluation, Party, User
from ..services.evaluation_service import outcome_preview
from .renderers import blocks_for_kind
from .qr import qr_data_url

settings = get_settings()


def _b64_data_url(path: str, mime: str) -> str | None:
    try:
        raw = Path(path).read_bytes()
        return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
    except OSError:
        return None


def build_report_model(db: Session, ev: Evaluation) -> dict:
    inst = ev.instrument
    lab = ev.laboratory
    unit = inst.unit
    preview = outcome_preview(db, ev)

    observer = db.get(User, ev.observer_id) if ev.observer_id else None
    approver = db.get(User, ev.approved_by) if ev.approved_by else None
    creator = db.get(User, ev.created_by) if ev.created_by else None
    manufacturer = db.get(Party, inst.manufacturer_id) if inst.manufacturer_id else None

    # ---- pages (ordered like the R 76-2 report) -----------------------------
    pages_out = []
    for rec in sorted(ev.test_records,
                      key=lambda r: (r.form_no or "99", r.instance_no, r.kind)):
        env_lines: list[tuple[str, str]] = []
        for phase in ("start", "max", "end"):
            b = (rec.environment or {}).get(phase)
            if b:
                env_lines.append((phase.capitalize(),
                                  f"T={b.get('temp', '—')} °C · RH={b.get('rh', '—')} %"
                                  f" · t={b.get('time', '—')}"))
        blocks = blocks_for_kind(rec.kind, rec.computed or {}, unit)
        if env_lines:
            blocks.insert(0, {"type": "kv", "title": "Environmental conditions",
                              "items": [[k, v] for k, v in env_lines]})
        if rec.remarks:
            blocks.append({"type": "note", "text": f"Remarks: {rec.remarks}"})
        pages_out.append({
            "form_no": rec.form_no or "?",
            "instance_no": rec.instance_no,
            "condition": rec.condition_label,
            "date": rec.test_date.isoformat() if rec.test_date else None,
            "blocks": blocks,
            "warnings": [w.get("message", str(w)) if isinstance(w, dict) else str(w)
                         for w in (rec.warnings or [])],
            "verdict": rec.verdict or "PENDING",
        })

    # ---- conformity ----------------------------------------------------------
    conformity = [[kind, preview["verdicts"].get(kind, "PENDING")]
                  for kind in preview["required"]]
    outcome = ev.outcome or preview["outcome"]

    # ---- attachments / photos ------------------------------------------------
    atts = db.scalars(
        select_att := __import__("sqlalchemy").select(Attachment)
        .where(Attachment.evaluation_id == ev.id,
               Attachment.include_in_report.is_(True))
    ).all()
    photos = []
    for a in atts:
        if a.mime and a.mime.startswith("image/") and len(photos) < 4 and a.storage_path:
            url = _b64_data_url(a.storage_path, a.mime)
            if url:
                photos.append({"caption": a.caption or a.file_name, "data_url": url})
    att_rows = [[a.kind, a.file_name or "—", a.caption or "—",
                 (a.sha256 or "—")[:16]] for a in atts]

    # ---- approval block -------------------------------------------------------
    approval_hash = ev.approval_hash
    qr = None
    if ev.status in ("APPROVED", "ARCHIVED") and approval_hash:
        qr = qr_data_url(
            f"NAWI-REPORT|{ev.report_no}|sha256:{approval_hash}"
            f"|ruleset:{ev.ruleset_sha256[:16]}"
        )

    return {
        "report_no": ev.report_no,
        "generated_note": f"Generated from {ev.ruleset_id} (sha256 {ev.ruleset_sha256[:16]}…)",
        "laboratory": {"name": lab.name, "address": lab.address or "—",
                       "accreditation_no": lab.accreditation_no or "—"},
        "instrument": {
            "application_no": inst.application_no or "—",
            "type_designation": inst.type_designation,
            "manufacturer": manufacturer.name if manufacturer else "—",
            "category": inst.category or "—",
            "accuracy_class": inst.accuracy_class,
            "indication_type": inst.indication_type,
            "display_kind": inst.display_kind or "—",
            "range_kind": inst.range_kind,
            "min_capacity": f"{inst.min_capacity} {unit}",
            "max_safe_load": (f"{inst.max_safe_load} {unit}"
                              if inst.max_safe_load is not None else "—"),
            "tare_plus": f"{inst.tare_plus} {unit}",
            "tare_minus": f"{inst.tare_minus} {unit}",
            "power_supply": ", ".join(inst.power_supply_category or []) or "—",
            "temp_limits": f"{inst.temp_min_c} °C … {inst.temp_max_c} °C",
            "printer": inst.printer or "—",
            "software_version": inst.software_version or "—",
            "submitted_serial": inst.submitted_identification_no or "—",
        },
        "ranges": [[r.idx, f"{r.e} {unit}", f"{r.d} {unit}",
                    f"{r.max_capacity} {unit}",
                    f"{r.max_capacity / r.e:.0f}"] for r in inst.ranges],
        "equipment": [[e.equipment.kind, e.equipment.name or "—",
                       e.equipment.serial_no or "—",
                       e.equipment.accuracy_class_or_uncertainty or "—",
                       e.equipment.cert_no or "—"]
                      for e in ev.equipment_links],
        "conditions": {
            "purpose": ev.purpose,
            "mpe_context": ev.mpe_context,
            "auto_zero_status": ev.auto_zero_status or "—",
            "resolution_during_test": (f"{ev.resolution_during_test} {unit}"
                                       if ev.resolution_during_test is not None else "—"),
            "period": (f"{ev.evaluation_period_from or '—'} → {ev.evaluation_period_to or '—'}"),
            "ruleset_id": ev.ruleset_id,
            "ruleset_sha256": ev.ruleset_sha256,
        },
        "pages": pages_out,
        "conformity": conformity,
        "outcome": outcome,
        "status": ev.status,
        "observer": observer.full_name if observer else (creator.full_name if creator else "—"),
        "approver": approver.full_name if approver else None,
        "approved_at": ev.approved_at.isoformat() if ev.approved_at else None,
        "approval_hash": approval_hash,
        "qr": qr,
        "attachments": att_rows,
        "photos": photos,
    }