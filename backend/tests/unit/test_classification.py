from decimal import Decimal as D

import pytest

from app.engine.classification import Instrument, Range, build_instrument
from app.engine.ruleset import load_ruleset

RS = load_ruleset()


def single_range() -> Instrument:
    return build_instrument(
        "III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}]
    )


def multi_interval() -> Instrument:
    return build_instrument(
        "III",
        "0",
        "g",
        [
            {"e": "1", "d": "1", "max": "2000"},
            {"e": "2", "d": "2", "max": "5000"},
            {"e": "10", "d": "10", "max": "15000"},
        ],
    )


def test_build_single_range_values_in_grams():
    inst = single_range()
    r = inst.ranges[0]
    assert r.e == D("5.000")
    assert r.max == D("15000.000")
    assert r.min == D("100.000")
    assert inst.max == D("15000.000")


def test_build_multi_interval_lower_bounds():
    inst = multi_interval()
    assert [r.idx for r in inst.ranges] == [1, 2, 3]
    assert inst.ranges[0].min == D(0)
    assert inst.ranges[1].min == D(2000)
    assert inst.ranges[2].min == D(5000)
    assert inst.is_multi_interval is True
    assert inst.smallest_e() == D(1)


def test_range_for_load_picks_partial_range():
    inst = multi_interval()
    assert inst.range_for_load(D(1500)).idx == 1
    assert inst.range_for_load(D(2000)).idx == 1
    assert inst.range_for_load(D(2001)).idx == 2
    assert inst.range_for_load(D(15000)).idx == 3


def test_range_for_load_overload_raises():
    with pytest.raises(ValueError, match="Max"):
        single_range().range_for_load(D(16000))
