"""
FORM 6.1 — Zero return (A.4.11.2) [V].
Pass: |P30 − P0| ≤ 0.5 e (multi-interval: e1; multiple-range: e_i of the range returned to).
Multiple-range extra [V]: after a load above Max₁, lowest range, 5 min unloaded:
|P35 − P30| ≤ e1.
"""
from decimal import Decimal as D

from ..error import point_error
from ..units import dec


def _P(block: dict, step: D) -> D:
    return point_error(block.get("I", "0"), block.get("L", "0"),
                       block.get("dL", "0"), step)[0]


def evaluate_zero_return(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    e1 = inst.smallest_e()
    step = ctx.resolution or inst.ranges[0].d
    limit = dec(rs["constants"]["zero_return_limit_e"]["value"]) * e1    # 0.5 e1

    P0 = _P(obs["P0"], step)
    P30 = _P(obs["P30"], step)
    change = P30 - P0
    ok = abs(change) <= limit

    computed = {"P0": str(P0), "P30": str(P30), "change": str(change),
                "limit": str(limit), "pass": ok}

    mr = obs.get("multiple_range")
    if mr and mr.get("P35"):
        P35 = _P(mr["P35"], step)
        mr_change = P35 - P30
        mr_ok = abs(mr_change) <= e1
        ok &= mr_ok
        computed["multiple_range"] = {"P35": str(P35), "change": str(mr_change),
                                      "limit": str(e1), "pass": mr_ok}
    return computed, ("PASSED" if ok else "FAILED"), []