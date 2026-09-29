"""
FORM 11 — Voltage variation (A.5.4). Evaluator = weighing (dispatcher maps),
THIS FILE provides the voltage limit calculator (3.9.3 [V]) — for the test schedule.
"""
from decimal import Decimal as D

from ..units import dec


def voltage_limits(u_nom, u_min=None, u_max=None, supply: str = "MAINS_AC") -> list[dict]:
    """
    3.9.3 [V]. If a U_min/U_max range is marked, reference = AVERAGE [V, form 11].
    Returns: [{"label": ..., "voltage": "..."}] — test instances are built from the labels.
    """
    u_nom = dec(u_nom)
    if u_min is not None and u_max is not None:
        uref = (dec(u_min) + dec(u_max)) / 2
    else:
        uref = u_nom

    if supply == "MAINS_AC":
        lo, hi = D("0.85") * uref, D("1.10") * uref
    elif supply in ("EXTERNAL_PLUGIN", "BATTERY_RECHARGEABLE_CHARGE_IN_USE"):
        lo, hi = u_min if u_min is not None else uref, D("1.20") * uref
    elif supply == "BATTERY_OTHER":
        lo, hi = u_min if u_min is not None else uref, u_nom
    elif supply == "VEHICLE_12V":
        lo, hi = u_min if u_min is not None else uref, D("16")
    elif supply == "VEHICLE_24V":
        lo, hi = u_min if u_min is not None else uref, D("32")
    else:
        lo, hi = uref, uref

    out = [{"label": "Lower limit", "voltage": str(lo)},
           {"label": "Reference", "voltage": str(uref)}]
    if hi != uref:
        out.append({"label": "Upper limit", "voltage": str(hi)})
    return out