"""
FORM 10 — Warm-up time (A.5.2) [V]: even BEFORE the DECLARED warm-up after
power-on, readings must be within MPE (readings taken at intervals).
obs = {"declared_warmup_min": "30", "zero": {...},
       "readings": [{"t_min": "5", "L": "...", "I": "...", "dL": "..."}]}
"""
from decimal import Decimal as D

from ..error import passes, point_error
from ..mpe import mpe
from ..units import dec
from .weighing import zero_error


def evaluate_warmup(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    step = ctx.resolution or inst.ranges[0].d
    E0 = zero_error(obs.get("zero"), step)
    warnings = []
    rows, ok, any_obs = [], True, False

    for rd in obs.get("readings") or []:
        L = dec(rd["L"])
        m = mpe(rs, inst, L, ctx.mpe_context)
        r = inst.range_for_load(L)
        st = ctx.resolution or r.d
        _, E = point_error(rd.get("I", "0"), L, rd.get("dL", "0"), st)
        Ec = E - E0
        ok_i = passes(Ec, m)
        ok &= ok_i
        any_obs = True
        rows.append({"t_min": rd.get("t_min"), "L": str(L), "Ec": str(Ec),
                     "mpe": str(m), "pass": ok_i})

    declared = dec(obs.get("declared_warmup_min", "0"))
    first_t = dec(obs["readings"][0]["t_min"]) if obs.get("readings") else None
    if first_t is not None and first_t >= declared:
        warnings.append({"severity": "WARN", "code": "WARMUP_LATE",
                         "message": f"Pehli reading ({first_t} min) declared warm-up "
                                    f"({declared} min) ke BAAD hai — test inconclusive [A.5.2]"})
    if not any_obs:
        return {"rows": rows}, "PENDING", warnings
    return {"E0": str(E0), "rows": rows}, ("PASSED" if ok else "FAILED"), warnings