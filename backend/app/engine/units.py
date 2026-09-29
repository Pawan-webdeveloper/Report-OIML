"""
Arithmetic foundation of the engine.

GOLDEN DESIGN RULE #4 (project.md §3.2):
    Only Decimal in the engine. Float must NEVER enter it.
    Values from API/JSON always arrive as STRINGS.

Boundary example this rule protects against:
    On Table 6, 500 e is EXACTLY a boundary. With floats, binary drift can
    produce '500.000000001 e' → wrong band → wrong PASS/FAIL.
    With Decimal the boundary is deterministic.
"""
from decimal import ROUND_HALF_UP, Decimal as D, getcontext

# 34 significant digits — far more margin than any weighing scale needs
getcontext().prec = 34

# Engine base unit = GRAM. The API layer converts values to the base unit
# before passing them to the engine (doc §4: instruments.unit column — conversion is standardized here).
UNIT_TO_GRAM = {
    "mg": D("0.001"),
    "g": D(1),
    "kg": D(1000),
    "t": D("1000000"),
    "ct": D("0.2"),  # carat — gem scales
}


def dec(x) -> D:
    """int/str/Decimal → Decimal. Explicitly rejects float."""
    if isinstance(x, D):
        return x
    if isinstance(x, float):
        raise TypeError(
            "float engine mein allowed nahi hai (boundary bugs). "
            "String pass karo: dec('2.5') — dec(2.5) nahi."
        )
    return D(str(x))


def to_base(value, unit: str) -> D:
    """Convert any supported mass unit to the base unit (gram)."""
    try:
        return dec(value) * UNIT_TO_GRAM[unit]
    except KeyError:
        raise ValueError(f"Unknown unit {unit!r}; allowed: {sorted(UNIT_TO_GRAM)}")


def q(value: D, quantum: D) -> D:
    """Round value to the nearest multiple of quantum (half-up)."""
    value, quantum = dec(value), dec(quantum)
    return (value / quantum).to_integral_value(rounding=ROUND_HALF_UP) * quantum