"""Golden: eccentricity, discrimination (digital/analog/nonself), sensitivity, stability."""
from app.engine.classification import build_instrument
from app.engine.context import EvaluationContext
from app.engine.tests.discrimination import (evaluate_disc_analog, evaluate_disc_digital,
                                             evaluate_disc_nonself, evaluate_sensitivity)
from app.engine.tests.eccentricity import evaluate_eccentricity
from app.engine.tests.stability_eq import evaluate_stability_eq


def _platform():
    return build_instrument("III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}])


class TestEccentricity:
    def test_pass_all_locations(self, rs):
        obs = {"test_load": "5000", "zero": {"L": "0", "I": "0", "dL": "1.0"},
               "locations": [{"location": i, "I": "5004", "dL": "1.6"} for i in range(1, 6)]}
        computed, verdict, _ = evaluate_eccentricity(rs, _platform(), EvaluationContext(), obs)
        assert computed["expected_load_default_1_3"] == "5000"   # (15000+0)/3
        assert all(r["pass"] for r in computed["rows"])
        assert verdict == "PASSED"

    def test_fail_one_location(self, rs):
        obs = {"test_load": "5000", "zero": {"L": "0", "I": "0", "dL": "1.0"},
               "locations": [{"location": 1, "I": "5004", "dL": "1.6"},
                             {"location": 2, "I": "5010", "dL": "1.6"}]}  # Ec=9.4 > 5
        _, verdict, _ = evaluate_eccentricity(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "FAILED"


class TestDiscrimination:
    def test_digital_pass_and_boundary(self, rs):
        obs = {"loads": [{"L": "100", "I1": "100", "I2": "107"},     # 7 ≥ 5 ✓
                         {"L": "15000", "I1": "15000", "I2": "15005"}]}  # 5 ≥ 5 ✓ boundary
        _, verdict, _ = evaluate_disc_digital(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "PASSED"

    def test_digital_fail(self, rs):
        obs = {"loads": [{"L": "100", "I1": "100", "I2": "103"}]}    # 3 < 5
        _, verdict, _ = evaluate_disc_digital(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "FAILED"

    def test_analog_0_7_mpe(self, rs):
        obs = {"loads": [{"L": "5000", "I1": "1.0", "I2": "4.0"}]}   # change 3 ≥ 0.7×5=3.5? NO
        _, verdict, _ = evaluate_disc_analog(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "FAILED"
        obs["loads"][0]["I2"] = "4.5"                                # 3.5 ≥ 3.5 ✓
        _, verdict, _ = evaluate_disc_analog(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "PASSED"

    def test_nonself_boolean(self, rs):
        obs = {"loads": [{"L": "5000", "visible_change": True}]}
        _, verdict, _ = evaluate_disc_nonself(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "PASSED"


class TestSensitivity:
    def test_class_III_max_le_30kg_needs_2mm(self, rs):
        inst = _platform()   # Max 15 kg ≤ 30 kg → 2 mm
        ok_obs = {"loads": [{"L": "5000", "displacement_mm": "2.0"}]}
        computed, verdict, _ = evaluate_sensitivity(rs, inst, EvaluationContext(), ok_obs)
        assert computed["required_mm"] == "2" and verdict == "PASSED"
        bad = {"loads": [{"L": "5000", "displacement_mm": "1.5"}]}
        _, verdict, _ = evaluate_sensitivity(rs, inst, EvaluationContext(), bad)
        assert verdict == "FAILED"


class TestStabilityEq:
    def test_print_store_pass_and_spread_warning(self, rs):
        obs = {"print_store": [{"printed": "7500", "min_display": "7499.9", "max_display": "7500.4"}]}
        computed, verdict, warns = evaluate_stability_eq(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "PASSED"
        assert not warns
        obs2 = {"print_store": [{"printed": "7500", "min_display": "7498", "max_display": "7504"}]}  # spread 6 > 1 e
        _, verdict, warns = evaluate_stability_eq(rs, _platform(), EvaluationContext(), obs2)
        assert any(w["code"] == "STAB_SPREAD" for w in warns)

    def test_zero_setting_0_25e(self, rs):
        obs = {"zero_setting": [{"I": "0", "L": "50", "dL": "1.0"}]}   # E0=0+2.5−1−50=−48.5 → |E0|>1.25
        _, verdict, _ = evaluate_stability_eq(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "FAILED"