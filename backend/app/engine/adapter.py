"""
API BOUNDARY ADAPTER — brings JSON observations into engine format (base grams, strings).

GOLDEN RULE #4: no float ever enters the engine. But JSON parsing turns numbers
into floats. This adapter converts numbers to STRINGs at the API edge (Python's
str(float) gives the shortest repr — fine for practical precision), then
converts them to grams via to_base. Everything EXCEPT mass fields stays
unchanged (temp, rh, voltage, t_min etc. remain as-is).
"""
from .units import to_base

# Fields with these names are MASS values in instrument units → convert to grams
MASS_FIELDS = frozenset({
    "L", "L0", "I", "I0", "I1", "I2", "dL", "dL0",
    "test_load", "load", "printed", "min_display", "max_display",
    "reference_I", "disturbed_I",
    "I_level", "dL_level", "I_tilted", "dL_tilted",
})


def to_base_obs(obj, unit: str):
    """Recursively converts mass fields to base grams (str)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in MASS_FIELDS and isinstance(v, (int, float, str)) and not isinstance(v, bool):
                if v in ("", None):
                    out[k] = v
                else:
                    out[k] = str(to_base(v, unit))
            else:
                out[k] = to_base_obs(v, unit)
        return out
    if isinstance(obj, list):
        return [to_base_obs(x, unit) for x in obj]
    return obj