"""
FORM 12.x — Disturbances (B.3.x) [V].
Pass: EITHER no significant fault (|ΔI| ≤ e), OR a significant fault (> e) was DETECTED
and action was taken on it (recovery / inhibit) [T.5.5.6].
obs = {"trials": [{"load": "...", "reference_I": "...", "disturbed_I": "...",
                   "detected": true, "acted_upon": true, "remarks": ""}]}
"""
from ..mpe import mpe
from ..units import dec, to_base


def evaluate_disturbance(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    rows, ok, any_obs = [], True, False
    for t in obs.get("trials") or []:
        L = dec(t.get("load", "0"))
        # the disturbance reference can also be a 10e no-load point — take e from the range
        r = inst.range_for_load(L) if L <= inst.max else inst.ranges[-1]
        e_r = r.e
        fault = dec(t["disturbed_I"]) - dec(t["reference_I"])
        significant = abs(fault) > e_r
        detected = bool(t.get("detected"))
        acted = bool(t.get("acted_upon"))
        ok_i = (not significant) or (significant and detected and acted)
        ok &= ok_i
        any_obs = True
        rows.append({"load": str(L), "fault": str(fault), "e": str(e_r),
                     "significant": significant, "detected": detected,
                     "acted_upon": acted, "pass": ok_i,
                     "remarks": t.get("remarks", "")})
    if not any_obs:
        return {"rows": rows}, "PENDING", []
    return {"rows": rows}, ("PASSED" if ok else "FAILED"), []