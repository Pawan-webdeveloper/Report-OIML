"""Changeover-point method golden tests — R 76-2 explanatory notes [V]."""
import pytest

from app.engine.error import corrected, passes, point_error
from app.engine.units import dec


class TestPointError:
    def test_changeover_basic(self):
        # I = 5000 g display, d = 5 g, ΔL = 3.0 g
        # P = 5000 + 2.5 − 3.0 = 4999.5 → E = −0.5 g
        P, E = point_error(I="5000", L="5000", dL="3.0", step="5")
        assert P == dec("4999.5")
        assert E == dec("-0.5")

    def test_changeover_zero_dL(self):
        # ΔL = 0 → indication exactly at the step edge: P = I + ½d
        P, E = point_error(I="5000", L="5000", dL="0", step="5")
        assert P == dec("5002.5")
        assert E == dec("2.5")

    def test_direct_method(self):
        P, E = point_error(I="5000", L="5000", method="direct")
        assert P == dec("5000") and E == dec("0")

    def test_zero_row_e0(self):
        # E0 (non-automatic zero) [M]: I0=0, L0=0 → E0 = ½r − ΔL0
        _, E0 = point_error(I="0", L="0", dL="1.0", step="5")
        assert E0 == dec("1.5")


class TestCorrectedAndPass:
    def test_ec(self):
        assert corrected(dec("-0.5"), dec("1.5")) == dec("-2")

    def test_pass_boundary_is_pass(self):
        assert passes(dec("2.5"), dec("2.5")) is True    # equal → PASS
        assert passes(dec("2.6"), dec("2.5")) is False
        assert passes(dec("-2.5"), dec("2.5")) is True   # |Ec| is used