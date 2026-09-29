"""
Test catalogue applicability (doc §6.8) — the instrument + features decide
which tests apply and which are required.
"""
from dataclasses import dataclass
from decimal import Decimal as D

from .units import dec


@dataclass
class Features:
    """Application-level flags of the instrument (built from the DB instruments row)."""
    non_self: bool = False
    has_tare: bool = False
    has_printer_or_storage: bool = False
    has_zero_setting: bool = False
    mains_ac: bool = False
    vehicle_powered: bool = False
    liable_to_tilt: bool = False
    rolling_load: bool = False
    direct_sales: bool = False


def _applies(cond: dict, inst, feat: Features) -> bool:
    if not cond:
        return True
    if "classes" in cond:
        return inst.cls in cond["classes"]
    if "electronic" in cond and not inst.is_electronic:
        return False
    if "digital" in cond and not inst.is_digital:
        return False
    if "analog" in cond and inst.is_digital:
        return False
    if "non_self" in cond and not feat.non_self:
        return False
    if "d_ge_5mg" in cond and inst.ranges[0].d < dec("0.005"):   # 3.8.2.2 [V]
        return False
    if "has_tare" in cond and not feat.has_tare:
        return False
    if "print_store_zero_tare" in cond and not (
            feat.has_printer_or_storage or feat.has_zero_setting or feat.has_tare):
        return False
    if "liable_to_tilt" in cond and not feat.liable_to_tilt:
        return False
    if "mains_ac" in cond and not feat.mains_ac:
        return False
    if "vehicle_powered" in cond and not feat.vehicle_powered:
        return False
    if "rolling_load" in cond and not feat.rolling_load:
        return False
    if "max_le_100kg" in cond and inst.max > dec("100000"):      # 100 kg [V 3.9.4.3]
        return False
    return True


def applicable_tests(rs: dict, inst, feat: Features) -> list[dict]:
    return [e for e in rs["test_catalogue"]["entries"] if _applies(e.get("applies_if") or {}, inst, feat)]


def required_kinds(rs: dict, inst, feat: Features) -> list[str]:
    return [e["kind"] for e in applicable_tests(rs, inst, feat) if e.get("required")]


def find_entry(rs: dict, kind: str) -> dict | None:
    return next((e for e in rs["test_catalogue"]["entries"] if e["kind"] == kind), None)