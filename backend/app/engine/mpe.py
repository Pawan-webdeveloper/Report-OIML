"""
MPE lookup — R 76-1 Table 6 [V] + in-service multiplier (3.5.2 [V])
+ multi-interval handling (3.3 [V]).

GOLDEN DESIGN RULE #2: all constants come from the RULESET JSON.
No MPE number is hardcoded in the code.
"""
from decimal import Decimal as D

from .classification import Instrument
from .units import dec


def band_multiplier(rs: dict, cls: str, m_in_e: D) -> D:
    """
    Table 6 [V]: load expressed in e → |MPE| multiplier.

    The boundary is INCLUSIVE: m_in_e == up_to  →  smaller band.
      e.g. Class III, exactly 500 e → 0.5 band ('0 ≤ m ≤ 500').
    """
    bands = rs["mpe_bands"].get(cls)
    if bands is None:
        raise ValueError(
            f"Unknown accuracy class {cls!r}; allowed: {sorted(rs['mpe_bands'])}"
        )
    for band in bands:
        up_to = band["up_to"]
        if up_to is None or m_in_e <= dec(up_to):
            return dec(band["mult"])
    raise ValueError(
        f"Load {m_in_e} e class {cls} ki sabse badi band se bahar hai — "
        "n = Max/e Table 3 limit check karo (Phase 3: validate.py)"
    )


def mpe(rs: dict, inst: Instrument, load, context: str = "INITIAL") -> D:
    """
    Absolute MPE (base unit: g) for a gross/net load.

    - Multi-interval: the e_i of the partial range the load falls in is used [V].
    - context='IN_SERVICE' → in-service multiplier (2×) [V, 3.5.2].
    """
    m = dec(load)
    if m < 0:
        raise ValueError("Load negative nahi ho sakta")
    r = inst.range_for_load(m)
    mult = band_multiplier(rs, inst.cls, m / r.e)
    value = mult * r.e
    if context == "IN_SERVICE":
        value *= dec(rs["in_service_multiplier"])
    return value