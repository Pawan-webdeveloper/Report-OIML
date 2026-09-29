"""
FORM 3 — Eccentricity (A.4.7) [V]. Pass: at every location |Ec| ≤ mpe(test_load).

Test load (3.6.2): default 1/3 × (Max + T+) [V]; >4 supports → 1/(n−1);
tank/hopper → 1/10; rolling → heaviest rolling ≤ 0.8 (Max+T+) [V].
obs: {"test_load": "5000", "zero": {...},
      "locations": [{"location": 1, "I": "...", "dL": "...", "zero": {...}(optional)}]}
"""
from decimal import Decimal as D

from ..error import passes, point_error
from ..mpe import mpe
from ..units import dec
from .weighing import zero_error


def evaluate_eccentricity(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    step = ctx.resolution or inst.ranges[0].d
    E0 = zero_error(obs.get("zero"), step)
    L = dec(obs["test_load"])
    m = mpe(rs, inst, L, ctx.mpe_context)
    expected_load = (inst.max + inst.tare_plus) / 3          # 3.6.2.1 default [V]

    rows, ok, any_obs = [], True, False
    for loc in obs.get("locations") or []:
        e0_loc = zero_error(loc.get("zero"), step) if loc.get("zero") else E0
        r = inst.range_for_load(L)
        st = ctx.resolution or r.d
        P, E = point_error(loc.get("I", "0"), L, loc.get("dL", "0"), st)
        Ec = E - e0_loc
        ok_i = passes(Ec, m)
        ok &= ok_i
        any_obs = True
        rows.append({"location": loc.get("location"), "P": str(P),
                     "Ec": str(Ec), "mpe": str(m), "pass": ok_i})

    warnings = []
    if L != expected_load:
        warnings.append({"severity": "WARN", "code": "ECC_LOAD",
                         "message": f"Test load {L} g — default 1/3(Max+T+) = "
                                    f"{expected_load} g hai (3.6.2.1); confirm karo ki "
                                    f"receptor type ke hisaab se sahi hai"})
    if not any_obs:
        return {"E0": str(E0), "test_load": str(L), "rows": rows}, "PENDING", warnings
    computed = {"E0": str(E0), "test_load": str(L), "mpe": str(m),
                "expected_load_default_1_3": str(expected_load), "rows": rows}
    return computed, ("PASSED" if ok else "FAILED"), warnings