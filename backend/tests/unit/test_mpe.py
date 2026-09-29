from decimal import Decimal as D

import pytest

from app.engine.classification import build_instrument
from app.engine.mpe import band_multiplier, mpe
from app.engine.ruleset import load_ruleset

RS = load_ruleset()


def inst() -> build_instrument:
    return build_instrument(
        "III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}]
    )


def test_band_multiplier_500e_boundary_inclusive():
    # Class III: 0 ≤ m ≤ 500 e → 0.5 (boundary inclusive)
    assert band_multiplier(RS, "III", D(500)) == D("0.5")
    assert band_multiplier(RS, "III", D(500.2)) == D("1")


def test_mpe_below_500e():
    # 1000 g = 200 e ≤ 500 e → 0.5 × 5 g = 2.5 g
    assert mpe(RS, inst(), "1000") == D("2.5000")


def test_mpe_500e_exact_boundary():
    # 2500 g = 500 e exactly → still 0.5 band → 2.5 g
    assert mpe(RS, inst(), "2500") == D("2.5000")


def test_mpe_just_past_boundary():
    # 2501 g = 500.2 e → next band (1e) → 5 g
    assert mpe(RS, inst(), "2501") == D("5.0000")


def test_mpe_in_service_doubles():
    assert mpe(RS, inst(), "1000", "IN_SERVICE") == D("5.0000")
    assert mpe(RS, inst(), "1000", "INITIAL") == D("2.5000")


def test_mpe_negative_load_raises():
    with pytest.raises(ValueError, match="negative"):
        mpe(RS, inst(), "-1")


def test_mpe_overload_raises():
    with pytest.raises(ValueError):
        mpe(RS, inst(), "16000")
