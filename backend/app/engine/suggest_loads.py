"""
Automatic test-load suggestion (doc §7.4):
1. ≥ n_min loads (default 10; initial intrinsic is also 10) [M/C]
2. Min → Max span
3. MPE change points INCLUDED (class III: 500e, 2000e)
4. Multi-interval: ~5e BELOW each scale-interval change
5. blanking_at_max → Max − 5e
6. Weights error ≤ ⅓ MPE check will use equipment in Phase 5 (3.7.1)
"""
from decimal import Decimal as D

from .units import dec


def suggest_loads(rs: dict, inst, n_min: int = 10, blanking_at_max: bool = False) -> list[D]:
    e_last = inst.ranges[-1].e
    loads: set[D] = {inst.min_cap}

    for r in inst.ranges:
        for b in rs["mpe_bands"][inst.cls]:
            if b["up_to"]:
                x = dec(b["up_to"]) * r.e
                if r.min < x <= r.max:
                    loads.add(x)                       # MPE change point within range
        if r.idx < len(inst.ranges):
            loads.add(r.max - 5 * r.e)                 # 5e below the scale-interval change

    loads.add(inst.max - (5 * e_last if blanking_at_max else D(0)))

    # Fill up to n_min: iteratively halve the largest gap (deterministic)
    while len(loads) < n_min:
        s = sorted(loads)
        lo, hi, gap, mid = s[0], s[-1], None, None
        for a, b in zip(s, s[1:]):
            if b - a > (gap or D(0)):
                lo, hi, gap = a, b, b - a
        if gap is None:
            break
        loads.add((lo + hi) / 2)

    return sorted(loads)