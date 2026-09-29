"""
Instrument model — engine-facing immutable representation.

"""
from dataclasses import dataclass
from decimal import Decimal as D

from .units import dec, to_base


@dataclass(frozen=True)
class Range:
    idx: int   # 1, 2, 3 ...
    e: D       # verification scale interval (base unit: g)
    d: D       # actual scale interval (base unit: g)
    max: D     # Max_i (base unit: g)
    min: D     # lower bound of this partial range (base unit: g)


@dataclass(frozen=True)
class Instrument:
    cls: str                      # 'I' | 'II' | 'III' | 'IIII'
    ranges: tuple[Range, ...]
    min_cap: D                    # instrument Min (g)
    tare_plus: D = D(0)           # T = + (g)
    is_electronic: bool = True
    is_digital: bool = True

    @property
    def max(self) -> D:
        return self.ranges[-1].max

    @property
    def is_multi_interval(self) -> bool:
        return len(self.ranges) > 1

    def smallest_e(self) -> D:
        return self.ranges[0].e

    def range_for_load(self, load) -> Range:
        """The partial range the load falls into (R 76-1 3.3 [V])."""
        m = dec(load)
        for r in self.ranges:
            if m <= r.max:
                return r
        raise ValueError(
            f"Load {m} g > Max {self.max} g — pehle validate.py mein pakda jayega"
        )


def build_instrument(
    accuracy_class: str, min_capacity, unit: str, ranges: list[dict]
) -> Instrument:
    """
    API-shaped dict → engine Instrument (all values in base unit = g).

    ranges example (kg scale, e = d = 5 g):
        [{"e": "0.005", "d": "0.005", "max": "15"}]

    Multi-interval example (g):
        [{"e": "1", "d": "1", "max": "2000"},
         {"e": "2", "d": "2", "max": "5000"},
         {"e": "10", "d": "10", "max": "15000"}]
    """
    base_min = to_base(min_capacity, unit)
    conv = [
        (to_base(r["e"], unit), to_base(r["d"], unit), to_base(r["max"], unit))
        for r in ranges
    ]
    built = []
    for i, (e_i, d_i, max_i) in enumerate(conv):
        lower = base_min if i == 0 else conv[i - 1][2]  # Min_i = Max_(i-1) [V]
        built.append(Range(idx=i + 1, e=e_i, d=d_i, max=max_i, min=lower))
    return Instrument(cls=accuracy_class, ranges=tuple(built), min_cap=base_min)