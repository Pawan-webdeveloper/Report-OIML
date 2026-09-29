"""Dashboard KPIs, audit RBAC + filters, ruleset inspector."""
import pytest

from app.engine.ruleset import load_ruleset
from app.models import (AuditLog, Evaluation, Instrument, InstrumentRange,
                        Laboratory, TestRecord)


@pytest.fixture()
def dash_env(client, make_user, auth_h, db_session):
    engineer = make_user(username="dash-eng", role="ENGINEER")
    reviewer = make_user(username="dash-rev", role="REVIEWER")
    admin = make_user(username="dash-adm", role="ADMIN")
    db_session.add(Laboratory(name="Dash Lab"))
    db_session.commit()
    lab = db_session.query(Laboratory).first()

    inst = Instrument(type_designation="PS-DASH", accuracy_class="III",
                      indication_type="SELF", display_kind="DIGITAL",
                      range_kind="SINGLE", min_capacity="0.1", unit="kg")
    db_session.add(inst)
    db_session.flush()
    db_session.add(InstrumentRange(instrument_id=inst.id, idx=1,
                                   e="0.005", d="0.005", max_capacity="15"))

    rs = load_ruleset()
    specs = [("DRAFT", None), ("IN_PROGRESS", None), ("SUBMITTED", "PASS"),
             ("APPROVED", "PASS"), ("APPROVED", "FAIL")]
    evals = []
    for i, (status, outcome) in enumerate(specs, 1):
        ev = Evaluation(report_no=f"LM/NAWI/2026/10{i:02d}", instrument_id=inst.id,
                        laboratory_id=lab.id, ruleset_id=rs["_id"],
                        ruleset_sha256=rs["_sha256"], purpose="TYPE_APPROVAL",
                        status=status, outcome=outcome, created_by=engineer.id)
        db_session.add(ev)
        evals.append(ev)
    db_session.flush()

    db_session.add(TestRecord(evaluation_id=evals[2].id, kind="WEIGHING",
                              observations={}, verdict="FAILED"))
    db_session.add(TestRecord(evaluation_id=evals[2].id, kind="CREEP",
                              observations={}, verdict="PASSED"))
    db_session.add(TestRecord(evaluation_id=evals[4].id, kind="REPEATABILITY",
                              observations={}, verdict="FAILED"))
    db_session.add(AuditLog(action="EVALUATION_CREATED", entity="evaluation",
                            user_id=engineer.id))
    db_session.commit()
    return engineer, reviewer, admin


class TestDashboard:
    def test_kpis_shape_and_counts(self, client, make_user, auth_h, dash_env):
        engineer, _, _ = dash_env
        r = client.get("/api/dashboard/kpis", headers=auth_h(engineer))
        assert r.status_code == 200
        k = r.json()
        assert k["totals"]["evaluations"] == 5
        assert k["totals"]["instruments"] == 1
        assert k["totals"]["users"] >= 3
        assert k["status_counts"]["APPROVED"] == 2
        assert k["outcome_counts"]["FAIL"] == 1
        assert k["outcome_counts"]["NOT_SET"] == 2
        assert len(k["trend"]) == 6
        assert all("month" in t and "count" in t for t in k["trend"])
        fails = {f["kind"]: f["count"] for f in k["failures"]}
        assert fails.get("WEIGHING") == 1 and fails.get("REPEATABILITY") == 1

    def test_kpis_requires_auth(self, client):
        assert client.get("/api/dashboard/kpis").status_code == 401


class TestAuditRbac:
    def test_engineer_forbidden(self, client, make_user, auth_h, dash_env):
        engineer, _, _ = dash_env
        assert client.get("/api/audit", headers=auth_h(engineer)).status_code == 403

    def test_reviewer_and_admin_can_read(self, client, make_user, auth_h, dash_env):
        _, reviewer, admin = dash_env
        assert client.get("/api/audit", headers=auth_h(reviewer)).status_code == 200
        r = client.get("/api/audit", headers=auth_h(admin))
        assert r.status_code == 200
        assert any(row["action"] == "EVALUATION_CREATED" for row in r.json())

    def test_action_filter(self, client, make_user, auth_h, dash_env):
        _, _, admin = dash_env
        rows = client.get("/api/audit", headers=auth_h(admin),
                          params={"action": "EVALUATION"}).json()
        assert rows and all("EVALUATION" in r["action"] for r in rows)
        empty = client.get("/api/audit", headers=auth_h(admin),
                           params={"action": "NO_SUCH_ACTION"}).json()
        assert empty == []


class TestRulesets:
    def test_list_contains_seeded_ruleset(self, client, make_user, auth_h, dash_env):
        engineer, _, _ = dash_env
        rows = client.get("/api/rulesets", headers=auth_h(engineer)).json()
        assert any(r["id"] == "oiml-r76-2006" for r in rows)
        assert all(len(r["sha256"]) == 64 for r in rows)

    def test_detail_exposes_document(self, client, make_user, auth_h, dash_env):
        engineer, _, _ = dash_env
        d = client.get("/api/rulesets/oiml-r76-2006",
                       headers=auth_h(engineer)).json()
        assert d["document"]["mpe_bands"]["III"][0]["mult"] == "0.5"
        assert d["document"]["test_catalogue"]["entries"]

    def test_unknown_ruleset_404(self, client, make_user, auth_h, dash_env):
        engineer, _, _ = dash_env
        assert client.get("/api/rulesets/nope-123",
                          headers=auth_h(engineer)).status_code == 404

    def test_requires_auth(self, client):
        assert client.get("/api/rulesets").status_code == 401