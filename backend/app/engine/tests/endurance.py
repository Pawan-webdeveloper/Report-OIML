"""
FORM 15 — Endurance (A.6) [V]: Max ≤ 100 kg; performed VERY LAST
(3.10.1 — the service layer will enforce this, warning-level). Final weighing within MPE.
obs = {"cycles": "100000", "weighing": {zero, points}}
"""
from decimal import Decimal as D

from ..units import dec
from .weighing import evaluate_weighing


def evaluate_endurance(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    if inst.max > dec(rs["constants"]["endurance_applies_if_max_kg"]["value"]) * dec("1000"):
        return {"applicable": False,
                "note": f"Max {inst.max} g > 100 kg — endurance NA [V 3.9.4.3]"}, \
               "NOT_APPLICABLE", []
    computed, verdict, warnings = evaluate_weighing(rs, inst, ctx, obs.get("weighing") or {})
    computed["cycles"] = obs.get("cycles")
    computed["order_note"] = "Endurance sabse LAST me hota hai [V 3.10.1]"
    return computed, verdict, warnings