import pytest

from app.engine.catalogue import Features, applicable_tests, required_kinds
from app.engine.classification import build_instrument
from app.engine.context import EvaluationContext
from app.engine.evaluate import evaluate_test, overall_outcome


def _platform(**kw):
    return build_instrument("III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}])


def test_required_kinds_for_electronic_platform_scale(rs):
    feat = Features(has_tare=True, mains_ac=True)
    req = required_kinds(rs, _platform(), feat)
    assert {"WEIGHING", "TEMP_NOLOAD", "ECC_WEIGHTS", "REPEATABILITY", "ZERO_RETURN",
            "CREEP", "WARMUP", "VOLTAGE", "DAMP_HEAT", "SPAN_STABILITY",
            "CONSTRUCTION", "CHECKLIST", "DIST_DIPS"} <= set(req)
    assert "TARE" not in req            # applicable but not required
    assert "ENDURANCE" not in req       # applicable (15kg ≤ 100kg) but not required
    kinds = {e["kind"] for e in applicable_tests(rs, _platform(), feat)}
    assert {"TARE", "ENDURANCE", "DISC_DIGITAL"} <= kinds   # d=5g ≥ 5mg ✓


def test_non_electronic_excludes_annex_b(rs):
    inst = build_instrument("III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}])
    inst = type(inst)(**{**inst.__dict__, "is_electronic": False})
    kinds = {e["kind"] for e in applicable_tests(rs, inst, Features())}
    assert "VOLTAGE" not in kinds and "DIST_DIPS" not in kinds and "DAMP_HEAT" not in kinds


def test_dispatch_all_catalogue_kinds_resolve(rs):
    from app.engine.evaluate import _EVALUATORS
    from app.engine.ruleset import load_ruleset
    for entry in load_ruleset()["test_catalogue"]["entries"]:
        assert entry["kind"] in _EVALUATORS, f"missing evaluator: {entry['kind']}"


def test_dispatch_unknown_kind_raises(rs):
    with pytest.raises(ValueError):
        evaluate_test("NOT_A_TEST", rs, _platform(), EvaluationContext(), {})


def test_weighing_end_to_end_dispatch(rs):
    inst = _platform()
    ctx = EvaluationContext()
    obs = {"zero": {"L": "20", "I": "20", "dL": "1.0"},
           "points": [{"L": "12000", "up": {"I": "12010", "dL": "3.0"}}]}
    out = evaluate_test("WEIGHING", rs, inst, ctx, obs)
    assert out["verdict"] == "FAILED"          # Ec = 8.0 > 7.5
    assert any(w["code"] == "MPE_CHANGE_POINT_MISSING" for w in out["warnings"])


def test_overall_outcome():
    req = ["WEIGHING", "REPEATABILITY", "CREEP"]
    assert overall_outcome(req, {"WEIGHING": "PASSED", "REPEATABILITY": "PASSED",
                                 "CREEP": "PASSED"}) == "PASS"
    assert overall_outcome(req, {"WEIGHING": "PASSED", "REPEATABILITY": "FAILED",
                                 "CREEP": "PASSED"}) == "FAIL"
    assert overall_outcome(req, {"WEIGHING": "PASSED"}) == "INCOMPLETE"