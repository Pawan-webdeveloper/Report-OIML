from decimal import Decimal as D

import pytest

from app.engine.units import UNIT_TO_GRAM, dec, q, to_base


def test_dec_accepts_int_str_decimal():
    assert dec(5) == D(5)
    assert dec("2.5") == D("2.5")
    assert dec(D("1.1")) == D("1.1")


def test_dec_rejects_float():
    with pytest.raises(TypeError, match="float"):
        dec(2.5)


def test_to_base_converts_all_units():
    assert to_base("1", "kg") == D(1000)
    assert to_base("2.5", "g") == D("2.5")
    assert to_base("1", "mg") == D("0.001")
    assert to_base("1", "t") == D(1000000)
    assert to_base("1", "ct") == D("0.2")


def test_to_base_unknown_unit():
    with pytest.raises(ValueError, match="Unknown unit"):
        to_base("1", "lb")


def test_round_half_up():
    assert q(D("0.0026"), D("0.005")) == D("0.005")
    assert q(D("0.0024"), D("0.005")) == D("0")
    assert q(D("2.5"), D("1")) == D(3)


def test_base_unit_is_gram():
    assert UNIT_TO_GRAM["g"] == D(1)
