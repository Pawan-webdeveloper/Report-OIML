"""
FORM 1 — Weighing performance (A.4.4, A.5.3.1) [V].

The same evaluator is also used for TARE (form 9, net loads), VOLTAGE (form 11
instances), DAMP_HEAT (form 13 phases) and ENDURANCE final weighing.

obs (BASE GRAMS):
    {"zero": {"L": "20", "I": "20", "dL": "1.0"},            # near-zero row (*)
     "points": [{"L": "5000",
                 "up":   {"I": "5005", "dL": "2.6"},
                 "down": {"I": "5005", "dL": "3.1"}}]}

E0: non-automatic zero → E0 = ½r − ΔL0 (I0=0, L0=0) [M]
    auto-zero in operation → the zero row has L = 10e; same formula:
    E0 = I0 + ½r − ΔL0 − L0 [M]
"""
from decimal import Decimal as D

from ..error import passes, point_error
from ..mpe import mpe
from ..units import dec


def zero_error(zero: dict | None, step: D) -> D:
    if not zero or zero.get("I") in (None, ""):
        return D(0)
    _, e0 = point_error(zero.get("I", "0"), zero.get("L", "0"),
                        zero.get("dL", "0"), step)
    return e0


def evaluate_weighing(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    zero = obs.get("zero") or {}
    step0 = ctx.resolution or inst.ranges[0].d
    E0 = zero_error(zero, step0)

    rows, ok, any_obs = [], True, False
    for p in obs.get("points") or []:
        if p.get("L") in (None, ""):
            continue
        L = dec(p["L"])
        m = mpe(rs, inst, L, ctx.mpe_context)
        r = inst.range_for_load(L)
        st = ctx.resolution or r.d
        row = {"L": str(L), "mpe": str(m)}
        for dirn in ("up", "down"):
            entry = p.get(dirn) or {}
            if entry.get("I") in (None, ""):
                continue
            any_obs = True
            P, E = point_error(entry["I"], L, entry.get("dL", "0"), st)
            Ec = E - E0
            ok_i = passes(Ec, m)
            row[dirn] = {"P": str(P), "E": str(E), "Ec": str(Ec), "pass": ok_i}
            ok &= ok_i
        rows.append(row)

    warnings = []
    if not zero or zero.get("I") in (None, ""):
        warnings.append({"severity": "WARN", "code": "ZERO_MISSING",
                         "message": "Zero row nahi hai — E0 = 0 maan ke calculate kiya"})
    if not any_obs:
        return {"E0": str(E0), "rows": rows}, "PENDING", warnings
    return {"E0": str(E0), "rows": rows}, ("PASSED" if ok else "FAILED"), warnings