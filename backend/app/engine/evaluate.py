"""
Dispatch: kind → evaluator. Return: {"kind", "computed", "verdict", "warnings"}.
Verdicts: PASSED | FAILED | NOT_APPLICABLE | PENDING  (R 76-2 page semantics)
Overall: FAIL if any required FAILED; INCOMPLETE if any required PENDING; else PASS.
"""
from .tests import (checklist, construction, creep, discrimination, disturbances,
                    eccentricity, endurance, repeatability, span_stability,
                    stability_eq, temp_noload, tilting, warmup, weighing,
                    zero_return)
from .validate import check_weighing_observations

_WEIGHING_FAMILY = {"WEIGHING", "TARE", "VOLTAGE", "DAMP_HEAT"}

_DIST_KINDS = (
    "DIST_DIPS", "DIST_BURST_MAINS", "DIST_BURST_IO", "DIST_SURGE_AC",
    "DIST_SURGE_OTHER", "DIST_ESD_DIRECT", "DIST_ESD_INDIRECT",
    "DIST_RADIATED", "DIST_CONDUCTED_RF", "DIST_VEHICLE_SUPPLY",
    "DIST_VEHICLE_COUPLING",
)

_EVALUATORS = {
    "WEIGHING": weighing.evaluate_weighing,
    "TARE": weighing.evaluate_weighing,           # MPE on net loads [V 3.5.3.3]
    "VOLTAGE": weighing.evaluate_weighing,        # per voltage instance (service splits)
    "DAMP_HEAT": weighing.evaluate_weighing,      # per phase (initial/high/final)
    "TEMP_NOLOAD": temp_noload.evaluate_temp_noload,
    "ECC_WEIGHTS": eccentricity.evaluate_eccentricity,
    "ECC_ROLLING": eccentricity.evaluate_eccentricity,
    "DISC_DIGITAL": discrimination.evaluate_disc_digital,
    "DISC_ANALOG": discrimination.evaluate_disc_analog,
    "DISC_NONSELF": discrimination.evaluate_disc_nonself,
    "SENSITIVITY": discrimination.evaluate_sensitivity,
    "REPEATABILITY": repeatability.evaluate_repeatability,
    "ZERO_RETURN": zero_return.evaluate_zero_return,
    "CREEP": creep.evaluate_creep,
    "STABILITY_EQ": stability_eq.evaluate_stability_eq,
    "TILTING": tilting.evaluate_tilting,
    "WARMUP": warmup.evaluate_warmup,
    "SPAN_STABILITY": span_stability.evaluate_span_stability,
    "ENDURANCE": endurance.evaluate_endurance,
    "CHECKLIST": checklist.evaluate_checklist,
    "CONSTRUCTION": construction.evaluate_construction,
}
_EVALUATORS.update({k: disturbances.evaluate_disturbance for k in _DIST_KINDS})
# ^ NOTE: ZERO_RETURN imported directly from .tests — no circularity


def evaluate_test(kind: str, rs: dict, inst, ctx, obs: dict) -> dict:
    fn = _EVALUATORS.get(kind)
    if fn is None:
        raise ValueError(f"Unknown test kind: {kind!r} — ruleset catalogue check karo")
    computed, verdict, warnings = fn(rs, inst, ctx, obs)
    if kind in _WEIGHING_FAMILY:
        warnings = list(warnings) + check_weighing_observations(rs, inst, ctx, obs)
    return {"kind": kind, "computed": computed, "verdict": verdict, "warnings": warnings}


def overall_outcome(required: list[str], verdicts: dict[str, str]) -> str:
    """
    required = required_kinds(...) (from the catalogue); verdicts = {kind: verdict}.
    Missing kind = PENDING.
    """
    v = {k: verdicts.get(k, "PENDING") for k in required}
    if any(x == "FAILED" for x in v.values()):
        return "FAIL"
    if any(x == "PENDING" for x in v.values()):
        return "INCOMPLETE"
    return "PASS"