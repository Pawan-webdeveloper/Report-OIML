"""
FORM 5 — Repeatability (A.4.10) [V].

Loads: ~50% Max and Max (if blanking, Max − 5e). Weighings: 10 per load;
3 per load if Max > 1000 kg [M].
Pass [V]: (a) every |E| ≤ |mpe|  AND  (b) Pmax − Pmin ≤ |mpe|.

Golden [M]: e=5 g, L=7.5 kg: ΔL 2.5/3.0 → P = 7500.0/7499.5, spread 0.5 ≤ 5 → PASS.
"""
from decimal import Decimal as D

from ..error import point_error
from ..mpe import mpe
from ..units import dec


def evaluate_repeatability(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    expected_n = 3 if inst.max > dec("1000000") else 10      # [M]
    warnings = []
    series_out, ok, any_obs = [], True, False

    for series in obs.get("series") or []:
        L = dec(series["L"])
        m = mpe(rs, inst, L, ctx.mpe_context)
        r = inst.range_for_load(L)
        st = ctx.resolution or r.d
        Ps, Es = [], []
        for w in series.get("weighings") or []:
            P, E = point_error(w.get("I", "0"), L, w.get("dL", "0"), st)
            Ps.append(P)
            Es.append(E)
            any_obs = True
        if not Ps:
            continue
        spread = max(Ps) - min(Ps)
        all_within = all(abs(E) <= m for E in Es)
        spread_ok = spread <= m
        ok &= all_within and spread_ok
        if len(Ps) != expected_n:
            warnings.append({"severity": "WARN", "code": "REP_COUNT",
                             "message": f"L={L} g: {len(Ps)} weighings — expected {expected_n} [M]"})
        series_out.append({"L": str(L), "mpe": str(m), "n": len(Ps),
                           "Pmin": str(min(Ps)), "Pmax": str(max(Ps)),
                           "spread": str(spread),
                           "all_within_mpe": all_within, "spread_ok": spread_ok,
                           "pass": all_within and spread_ok})

    warnings.append if False else None
    if not any_obs:
        return {"series": series_out}, "PENDING", warnings
    return {"series": series_out}, ("PASSED" if ok else "FAILED"), warnings