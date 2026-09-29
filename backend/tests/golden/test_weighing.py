"""Form 1 golden — changeover method, E0, pass/fail, multi-interval step handling."""
from decimal import Decimal as D

from app.engine.classification import build_instrument
from app.engine.context import EvaluationContext
from app.engine.tests.weighing import evaluate_weighing


def _platform():
    return build_instrument("III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}])


PASS_OBS = {
    "zero": {"L": "20", "I": "20", "dL": "1.0"},           # E0 = 20+2.5−1−20 = 1.5
    "points": [
        {"L": "5000",  "up": {"I": "5005", "dL": "2.6"}, "down": {"I": "5005", "dL": "3.1"}},
        {"L": "12000", "up": {"I": "12005", "dL": "3.6"}, "down": {"I": "12005", "dL": "4.1"}},
    ],
}


def test_golden_pass(rs):
    computed, verdict, warns = evaluate_weighing(rs, _platform(), EvaluationContext(), PASS_OBS)
    assert D(computed["E0"]) == D("1.5")
    row = computed["rows"][0]
    assert D(row["up"]["Ec"]) == D("3.4")            # P=5004.9 → E=4.9 → Ec=3.4 ≤ 5
    assert D(row["down"]["Ec"]) == D("2.9")            # P=5004.4 → E=4.4 → Ec=2.9 ≤ 5
    assert verdict == "PASSED" and not warns


def test_golden_fail_at_12kg(rs):
    obs = {"zero": PASS_OBS["zero"],
           "points": [{"L": "12000", "up": {"I": "12010", "dL": "3.0"}}]}
    computed, verdict, _ = evaluate_weighing(rs, _platform(), EvaluationContext(), obs)
    # P = 12010+2.5−3 = 12009.5 → E=9.5 → Ec=8.0 > mpe 7.5
    assert D(computed["rows"][0]["up"]["Ec"]) == D("8.0")
    assert verdict == "FAILED"


def test_missing_zero_row_defaults_E0_with_warning(rs):
    obs = {"points": [{"L": "5000", "up": {"I": "5000", "dL": "2.5"}}]}
    computed, verdict, warns = evaluate_weighing(rs, _platform(), EvaluationContext(), obs)
    assert computed["E0"] == "0"
    assert any(w["code"] == "ZERO_MISSING" for w in warns)
    assert verdict == "PASSED"


def test_multi_interval_uses_range_step(rs):
    inst = build_instrument("III", "20", "g",
                            [{"e": "1", "d": "1", "max": "2000"},
                             {"e": "2", "d": "2", "max": "5000"},
                             {"e": "10", "d": "10", "max": "15000"}])
    obs = {"zero": {"L": "0", "I": "0", "dL": "0.5"},       # step = e1 = 1 → E0 = 0
           "points": [{"L": "3000", "up": {"I": "3000", "dL": "1.0"}}]}  # step = e2 = 2
    computed, verdict, _ = evaluate_weighing(rs, inst, EvaluationContext(), obs)
    # P = 3000 + 1 − 1 = 3000 → E = 0 → Ec = 0; mpe(3000g) = 2 g
    assert D(computed["rows"][0]["up"]["Ec"]) == D("0")
    assert D(computed["rows"][0]["mpe"]) == D("2")
    assert verdict == "PASSED"


def test_empty_obs_pending(rs):
    _, verdict, _ = evaluate_weighing(rs, _platform(), EvaluationContext(), {"points": []})
    assert verdict == "PENDING"