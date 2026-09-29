"""
FORM 6.2 — Creep (A.4.11.1) [V].
Condition a) [V]: |ΔP| ≤ 0.5 e (0–30 min) AND |P30 − P15| ≤ 0.2 e → PASS (test ends)
Condition b) [V]: otherwise up to 4 h — |ΔP| ≤ |mpe| throughout → PASS
Data a) fail + 4h missing → PENDING (more readings needed).
|ΔP| > mpe after the 30-min window (b active) → FAILED immediately —
condition b) requires |ΔP| ≤ mpe *throughout*, so it can no longer pass.
Golden [M]: e=5 g, L=15 kg: P = 14999.0/14999.5/15000.0/15000.0 → PASS a).
"""
from decimal import Decimal as D

from ..error import point_error
from ..mpe import mpe
from ..units import dec


def evaluate_creep(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    e = inst.smallest_e()
    step = ctx.resolution or inst.ranges[0].d
    L = dec(obs.get("load", "0"))
    m = mpe(rs, inst, L, ctx.mpe_context)
    a_lim = dec(rs["constants"]["creep_30min_e"]["value"]) * e          # 0.5 e
    b_lim = dec(rs["constants"]["creep_15_to_30min_e"]["value"]) * e    # 0.2 e

    pts = []
    for rd in obs.get("readings") or []:
        P = point_error(rd.get("I", "0"), "0", rd.get("dL", "0"), step)[0]
        pts.append((dec(rd["t_min"]), P))
    pts.sort(key=lambda x: x[0])
    if not pts:
        return {"rows": []}, "PENDING", []

    P0 = pts[0][1]
    rows = [{"t_min": str(t), "P": str(P), "dP": str(P - P0)} for t, P in pts]

    within_30 = [(t, P) for t, P in pts if t <= 30]
    cond_a1 = len(within_30) >= 2 and all(abs(P - P0) <= a_lim for _, P in within_30)
    P15 = next((P for t, P in pts if t == 15), None)
    P30 = next((P for t, P in pts if t == 30), None)
    cond_a2 = P15 is not None and P30 is not None and abs(P30 - P15) <= b_lim

    if cond_a1 and cond_a2:
        return {"load": str(L), "mode": "a) 30-min", "rows": rows,
                "limits": {"a": str(a_lim), "a2": str(b_lim)}}, "PASSED", []

    has_4h = pts[-1][0] >= 240
    if has_4h:
        cond_b = all(abs(P - P0) <= m for _, P in pts)
        return {"load": str(L), "mode": "b) 4-h", "rows": rows,
                "limits": {"b_mpe": str(m)}}, ("PASSED" if cond_b else "FAILED"), []
    if any(t > 30 and abs(P - P0) > m for t, P in pts):
        return {"load": str(L), "mode": "b) 4-h", "rows": rows,
                "limits": {"b_mpe": str(m)}}, "FAILED", []

    return {"load": str(L), "mode": "b) 4-h (data pending)", "rows": rows}, "PENDING", []