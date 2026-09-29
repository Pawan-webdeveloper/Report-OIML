"""
Error formulas — R 76-2 explanatory notes [V].

"""
from decimal import Decimal as D

from .units import dec


def point_error(I, L, dL=None, step=None, method: str = "changeover") -> tuple[D, D]:
    """
    Returns (P, E) for one observation point. Values in base unit (g).

    method='changeover' → P = I + ½·step − ΔL   (step normally = d)
    method='direct'     → P = I                 (only d ≤ 0.2 e allowed [C])
    """
    I, L = dec(I), dec(L)
    if method == "direct":
        P = I
    elif method == "changeover":
        P = I + dec(step) / 2 - dec(dL)
    else:
        raise ValueError(f"Unknown method {method!r}")
    return P, P - L


def corrected(E, E0) -> D:
    """Ec = E − E0 (zero-error correction) [V]."""
    return dec(E) - dec(E0)


def passes(Ec, mpe_value) -> bool:
    """|Ec| ≤ |mpe| → PASS (R 76-1 3.5 [V]). Boundary equality is also PASS."""
    return abs(dec(Ec)) <= abs(dec(mpe_value))