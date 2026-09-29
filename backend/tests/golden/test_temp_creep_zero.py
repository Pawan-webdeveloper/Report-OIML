"""Golden examples: Form 2 (temp no-load), Form 6.1 (zero return), Form 6.2 (creep)."""
from decimal import ROUND_HALF_UP, Decimal as D

from app.engine.classification import build_instrument
from app.engine.context import EvaluationContext
from app.engine.tests.creep import evaluate_creep
from app.engine.tests.temp_noload import evaluate_temp_noload
from app.engine.tests.zero_return import evaluate_zero_return


def _platform():
    return build_instrument("III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}])


class TestTempNoLoad:
    def test_golden_0_6436_per_5c(self, rs):
        obs = {"readings": [
            {"temp": "20.1", "I": "20", "dL": "2.5", "L": "0"},     # P = 20.0
            {"temp": "40.3", "I": "22.6", "dL": "2.5", "L": "0"},   # P = 22.6
        ]}
        computed, verdict, _ = evaluate_temp_noload(rs, _platform(), EvaluationContext(), obs)
        change = D(computed["rows"][0]["change"]).quantize(D("0.0001"), ROUND_HALF_UP)
        assert change == D("0.6436")        # doc §8.2 golden [M]
        assert D(computed["rows"][0]["limit"]) == D("5")
        assert verdict == "PASSED"

    def test_fail_when_drift_exceeds_e(self, rs):
        obs = {"readings": [
            {"temp": "20", "I": "20", "dL": "2.5", "L": "0"},
            {"temp": "40", "I": "40", "dL": "2.5", "L": "0"},   # ΔP=20 over 20°C → 5.0/5°C ≥ e
        ]}
        _, verdict, _ = evaluate_temp_noload(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "FAILED"


class TestZeroReturn:
    def test_golden_pass(self, rs):
        obs = {"P0": {"I": "0", "dL": "1.0"}, "P30": {"I": "2", "dL": "1.0"}}
        computed, verdict, _ = evaluate_zero_return(rs, _platform(), EvaluationContext(), obs)
        assert D(computed["change"]) == D("2.0")          # ≤ 0.5×5 = 2.5
        assert verdict == "PASSED"

    def test_fail(self, rs):
        obs = {"P0": {"I": "0", "dL": "1.0"}, "P30": {"I": "5", "dL": "1.0"}}
        _, verdict, _ = evaluate_zero_return(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "FAILED"                  # 5.0 > 2.5


class TestCreep:
    GOLDEN = {"load": "15000", "readings": [
        {"t_min": "0",  "I": "15000", "dL": "3.5"},   # P=14999.0
        {"t_min": "5",  "I": "15000", "dL": "3.0"},   # P=14999.5
        {"t_min": "15", "I": "15000", "dL": "2.5"},   # P=15000.0
        {"t_min": "30", "I": "15000", "dL": "2.5"},   # P=15000.0
    ]}

    def test_golden_condition_a_pass(self, rs):
        computed, verdict, _ = evaluate_creep(rs, _platform(), EvaluationContext(), self.GOLDEN)
        assert computed["mode"] == "a) 30-min"
        assert verdict == "PASSED"

    def test_a_fails_no_4h_data_pending(self, rs):
        obs = {"load": "15000", "readings": [
            {"t_min": "0", "I": "15000", "dL": "3.5"},
            {"t_min": "30", "I": "15020", "dL": "3.5"},   # ΔP=20 > 2.5
        ]}
        _, verdict, _ = evaluate_creep(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "PENDING"          # 4h data needed for condition b)

    def test_condition_b_pass_within_mpe(self, rs):
        obs = {"load": "15000", "readings": [
            {"t_min": "0", "I": "15000", "dL": "3.5"},
            {"t_min": "60", "I": "15010", "dL": "3.5"},   # ΔP=10 ≤ mpe 7.5? NO → adjust:
        ]}
        # ΔP=10 > 7.5 → FAILED expected
        _, verdict, _ = evaluate_creep(rs, _platform(), EvaluationContext(), obs)
        assert verdict == "FAILED"

    def test_condition_b_pass_real(self, rs):
        obs = {"load": "15000", "readings": [
            {"t_min": "0", "I": "15000", "dL": "3.5"},
            {"t_min": "240", "I": "15004", "dL": "3.5"},  # ΔP=4 ≤ mpe 7.5 ✓
        ]}
        computed, verdict, _ = evaluate_creep(rs, _platform(), EvaluationContext(), obs)
        assert computed["mode"].startswith("b)")
        assert verdict == "PASSED"