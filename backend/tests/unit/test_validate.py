"""Table 3 classification checks + d-form + weighing plausibility."""
from decimal import Decimal as D

from app.engine.classification import build_instrument
from app.engine.context import EvaluationContext
from app.engine.validate import check_weighing_observations, validate_instrument


def _platform():
    return build_instrument("III", "0.1", "kg",
                            [{"e": "0.005", "d": "0.005", "max": "15"}])


class TestInstrumentValidation:
    def test_valid_platform_scale_no_errors(self, rs):
        errors, warns = validate_instrument(rs, _platform())
        assert errors == []
        assert warns == []

    def test_n_too_big(self, rs):
        inst = build_instrument("III", "20", "g",
                                [{"e": "0.5", "d": "0.5", "max": "10000"}])  # n=20000
        errors, _ = validate_instrument(rs, inst)
        assert any(e["code"] == "T3_N" for e in errors)

    def test_min_below_limit(self, rs):
        inst = build_instrument("III", "50", "g",
                                [{"e": "5", "d": "5", "max": "15000"}])  # Min<20e=100
        errors, _ = validate_instrument(rs, inst)
        assert any(e["code"] == "T3_MIN" for e in errors)

    def test_e_outside_any_band(self, rs):
        inst = build_instrument("III", "20", "g",
                                [{"e": "3", "d": "3", "max": "15000"}])  # e=3g: no band matches
        errors, _ = validate_instrument(rs, inst)
        assert any(e["code"] == "T3_E_BAND" for e in errors)

    def test_multi_interval_e_must_increase(self, rs):
        inst = build_instrument("III", "20", "g",
                                [{"e": "2", "d": "2", "max": "5000"},
                                 {"e": "1", "d": "1", "max": "15000"}])
        errors, _ = validate_instrument(rs, inst)
        assert any(e["code"] == "T3_E_ORDER" for e in errors)

    def test_d_form_warning(self, rs):
        inst = build_instrument("III", "0.1", "kg",
                                [{"e": "0.005", "d": "0.003", "max": "15"}])  # d=3g
        _, warns = validate_instrument(rs, inst)
        assert any(w["code"] == "D_FORM" for w in warns)


class TestWeighingObservations:
    def test_load_over_max_is_error(self, rs):
        warns = check_weighing_observations(
            rs, _platform(), EvaluationContext(),
            {"points": [{"L": "16000", "up": {"I": "16000", "dL": "2.5"}}]})
        assert any(w["code"] == "L_GT_MAX" and w["severity"] == "ERROR" for w in warns)

    def test_dl_out_of_range_warns(self, rs):
        warns = check_weighing_observations(
            rs, _platform(), EvaluationContext(),
            {"points": [{"L": "5000", "up": {"I": "5000", "dL": "7"}}]})
        assert any(w["code"] == "DL_RANGE" for w in warns)

    def test_indication_typo_warns(self, rs):
        warns = check_weighing_observations(
            rs, _platform(), EvaluationContext(),
            {"points": [{"L": "5000", "up": {"I": "5200", "dL": "2.5"}}]})
        assert any(w["code"] == "I_TOO_FAR" for w in warns)

    def test_mpe_change_points_and_count(self, rs):
        warns = check_weighing_observations(
            rs, _platform(), EvaluationContext(),
            {"points": [{"L": "5000", "up": {"I": "5000", "dL": "2.5"}}]})
        codes = {w["code"] for w in warns}
        assert "TOO_FEW_LOADS" in codes
        assert "MPE_CHANGE_POINT_MISSING" in codes

    def test_clean_full_loads_no_warnings(self, rs):
        loads = ["100", "1300", "2500", "6250", "10000", "15000"]
        obs = {"points": [{"L": L, "up": {"I": L, "dL": "2.5"}} for L in loads]}
        warns = check_weighing_observations(rs, _platform(), EvaluationContext(), obs)
        codes = {w["code"] for w in warns}
        assert not (codes & {"L_GT_MAX", "DL_RANGE", "I_TOO_FAR",
                             "MPE_CHANGE_POINT_MISSING", "TOO_FEW_LOADS"})