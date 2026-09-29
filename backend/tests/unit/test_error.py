from decimal import Decimal as D

from app.engine.error import corrected, passes, point_error


def test_point_error_changeover():
    # P = I + step/2 − ΔL ; E = P − L
    P, E = point_error("100.0", "100.05", dL="0", step="0.005")
    assert P == D("100.0025")
    assert E == D("-0.0475")


def test_point_error_direct():
    P, E = point_error("50", "50.1", method="direct")
    assert P == D(50)
    assert E == D("-0.1")


def test_corrected_zero_error():
    assert corrected("0.02", "0.01") == D("0.01")
    assert corrected("-0.01", "0.02") == D("-0.03")


def test_passes_boundary_is_pass():
    assert passes(D("0.5"), D("0.5")) is True
    assert passes(D("-0.5"), D("0.5")) is True
    assert passes(D("0.4"), D("0.5")) is True


def test_passes_fail():
    assert passes(D("0.6"), D("0.5")) is False
    assert passes(D("-0.6"), D("0.5")) is False
