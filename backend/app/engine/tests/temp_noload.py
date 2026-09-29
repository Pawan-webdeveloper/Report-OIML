"""
FORM 2 — Temperature effect on no-load indication (A.5.3.2) [V].

Pass (3.9.2.3 [V]): zero change per 5 °C < e (class I: per 1 °C).
Multi-interval → smallest e.  Golden [M]: P(20.1)=20.0 g, P(40.3)=22.6 g
→ ΔP=2.6, ΔT=20.2 → 0.6436 g per 5 °C.
"""
from decimal import Decimal as D

from ..error import point_error
from ..units import dec


def evaluate_temp_noload(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    step = ctx.resolution or inst.ranges[0].d
    e = inst.smallest_e()
    per_deg = dec("1") if inst.cls == "I" else dec("5")

    pts = []
    for rd in obs.get("readings") or []:
        P, _ = point_error(rd.get("I", "0"), rd.get("L", "0"), rd.get("dL", "0"), step)
        pts.append((dec(rd["temp"]), P))
    pts.sort(key=lambda x: x[0])

    rows, ok, any_pair = [], True, False
    for (T1, P1), (T2, P2) in zip(pts, pts[1:]):
        dT = T2 - T1
        if dT == 0:
            continue
        any_pair = True
        dP = P2 - P1
        change = abs(dP) / abs(dT) * per_deg
        ok_i = change < e                     # strictly < e [V]
        ok &= ok_i
        rows.append({"T1": str(T1), "T2": str(T2), "dP": str(dP), "dT": str(dT),
                     "change": str(change), "limit": str(e), "pass": ok_i})

    if not any_pair:
        return {"rows": rows}, "PENDING", []
    return {"rows": rows}, ("PASSED" if ok else "FAILED"), []