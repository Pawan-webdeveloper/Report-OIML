"""
FORM 14 — Span stability (B.4). [C — CONFIRM against B.4 text]
Criterion (implementation): against the initial test errors, at every check the
variation |E_check − E_initial| ≤ ½ × mpe AND |E| ≤ mpe.
obs = {"load": "...", "initial": {"I","dL"}, "checks": [{"label","I","dL"}]}
"""
from decimal import Decimal as D

from ..error import point_error
from ..mpe import mpe
from ..units import dec


def evaluate_span_stability(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    step = ctx.resolution or inst.ranges[0].d
    L = dec(obs["load"])
    m = mpe(rs, inst, L, ctx.mpe_context)
    frac = D("0.5")            # [C] confirm B.4

    _, E_init = point_error(obs["initial"].get("I", "0"), L,
                            obs["initial"].get("dL", "0"), step)
    rows, ok, any_obs = [], True, False
    for c in obs.get("checks") or []:
        _, E = point_error(c.get("I", "0"), L, c.get("dL", "0"), step)
        variation = E - E_init
        ok_i = abs(variation) <= frac * m and abs(E) <= m
        ok &= ok_i
        any_obs = True
        rows.append({"label": c.get("label"), "E": str(E), "E_initial": str(E_init),
                     "variation": str(variation),
                     "limit": str(frac * m), "pass": ok_i})
    if not any_obs:
        return {"E_initial": str(E_init), "rows": rows}, "PENDING", []
    return {"E_initial": str(E_init), "rows": rows}, ("PASSED" if ok else "FAILED"), []