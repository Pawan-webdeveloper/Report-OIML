from decimal import Decimal as D

from app.engine.classification import build_instrument
from app.engine.suggest_loads import suggest_loads


def test_platform_scale_includes_change_points_and_max(rs):
    inst = build_instrument("III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}])
    loads = suggest_loads(rs, inst, n_min=10)
    values = {D(str(x)) for x in loads}
    assert {D("100"), D("2500"), D("10000"), D("15000")} <= values   # Min, 500e, 2000e, Max
    assert len(loads) >= 10


def test_blanking_at_max(rs):
    inst = build_instrument("III", "0.1", "kg", [{"e": "0.005", "d": "0.005", "max": "15"}])
    loads = suggest_loads(rs, inst, blanking_at_max=True)
    assert D(str(loads[-1])) == D("14975")                # Max − 5e


def test_multi_interval_stays_5e_below_changes(rs):
    inst = build_instrument("III", "20", "g",
                            [{"e": "1", "d": "1", "max": "2000"},
                             {"e": "2", "d": "2", "max": "5000"},
                             {"e": "10", "d": "10", "max": "15000"}])
    values = {str(x) for x in suggest_loads(rs, inst)}
    assert {"500", "2000", "4000", "15000"} <= values         # MPE change points
    assert "1995" in values and "4990" in values              # 5e below Max1 / Max2