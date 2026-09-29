"""
FORM 8 — Tilting (A.5.1) [V].
No-load tilted: change ≤ 2 e — does NOT apply to class II unless direct sales
(3.9.1.1). Loaded tilted: weighing test, |Ec| ≤ mpe. Class I: level indicator
required but the test is NOT performed.
obs = {"no_load": {"I_level","dL_level","I_tilted","dL_tilted"} (optional),
       "loaded": {zero, points} (optional)}
"""
from decimal import Decimal as D

from ..error import point_error
from ..units import dec
from .weighing import evaluate_weighing


def evaluate_tilting(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    e = inst.smallest_e()
    step = ctx.resolution or inst.ranges[0].d
    computed: dict = {}
    ok, any_obs = True, False
    warnings = []

    if inst.cls == "I":
        return {"applicable": False,
                "note": "Class I: level indicator required, tilt test not performed [V]"}, \
               "NOT_APPLICABLE", []

    nl = obs.get("no_load")
    if nl:
        applicable = not (inst.cls == "II" and not obs.get("direct_sales"))
        if applicable:
            P_lvl = point_error(nl.get("I_level", "0"), "0", nl.get("dL_level", "0"), step)[0]
            P_tlt = point_error(nl.get("I_tilted", "0"), "0", nl.get("dL_tilted", "0"), step)[0]
            change = P_tlt - P_lvl
            limit = dec(rs["constants"]["tilt_no_load_limit_e"]["value"]) * e   # 2 e
            ok &= abs(change) <= limit
            any_obs = True
            computed["no_load"] = {"change": str(change), "limit": str(limit),
                                   "pass": abs(change) <= limit}
        else:
            computed["no_load"] = {"applicable": False,
                                   "note": "class II, direct sales nahi — skip [V 3.9.1.1]"}

    if obs.get("loaded"):
        sub, sub_verdict, sub_warns = evaluate_weighing(rs, inst, ctx, obs["loaded"])
        computed["loaded"] = sub
        warnings += sub_warns
        ok &= (sub_verdict == "PASSED")
        any_obs = True

    if not any_obs:
        return computed, "PENDING", warnings
    return computed, ("PASSED" if ok else "FAILED"), warnings