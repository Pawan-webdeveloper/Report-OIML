"""Workflow state machine + submission gate + separation of duties + freeze."""
import uuid

from app.models import Equipment, Evaluation, Laboratory, TestRecord
from app.services.evaluation_service import outcome_preview

INSTRUMENT_OK = {
    "type_designation": "PS-15K-WF", "category": "Platform scale",
    "accuracy_class": "III", "min_capacity": "0.1", "unit": "kg",
    "power_supply_category": ["MAINS_AC"],
    "printer": "NOT_PRESENT_CONNECTABLE",
    "zero_devices": {"tracking": True}, "tare_devices": {"subtractive": True},
    "ranges": [{"e": "0.005", "d": "0.005", "max": "15"}],
}
WEIGHING_PASS = {
    "kind": "WEIGHING",
    "observations": {
        "zero": {"L": "0.02", "I": "0.02", "dL": "0.001"},
        "points": [{"L": "5", "up": {"I": "5.005", "dL": "0.0026"}},
                   {"L": "12", "up": {"I": "12.005", "dL": "0.0036"}}],
    },
}


class Workspace:
    """Helper: engineer + reviewer + instrument + evaluation, ready to drive."""

    def __init__(self, client, make_user, auth_h, db_session, tag):
        self.client, self.auth_h, self.db = client, auth_h, db_session
        self.engineer = make_user(username=f"{tag}-eng", role="ENGINEER")
        self.reviewer = make_user(username=f"{tag}-rev", role="REVIEWER")
        self.reviewer2 = make_user(username=f"{tag}-rev2", role="REVIEWER")
        db_session.add(Laboratory(name=f"L-{tag}"))
        db_session.commit()
        inst = client.post("/api/instruments", headers=auth_h(self.engineer),
                           json=INSTRUMENT_OK).json()
        # observer = engineer → assigned; reviewer2 is a DIFFERENT person for approval
        self.ev = client.post(
            "/api/evaluations", headers=auth_h(self.engineer),
            json={"instrument_id": inst["id"], "observer_id": str(self.engineer.id)},
        ).json()

    def save(self, payload, as_engineer=True):
        user = self.engineer if as_engineer else self.reviewer
        return self.client.post(f"/api/evaluations/{self.ev['id']}/tests",
                                headers=self.auth_h(user), json=payload)

    def fill_required(self, failed_kind: str | None = None):
        """Insert every still-missing required kind directly (verdict PASSED)."""
        preview = outcome_preview(self.db, self.db.get(Evaluation, uuid.UUID(self.ev["id"])))
        for kind in preview["required"]:
            exists = self.db.query(TestRecord).filter_by(
                evaluation_id=uuid.UUID(self.ev["id"]), kind=kind).first()
            if exists:
                continue
            self.db.add(TestRecord(
                evaluation_id=uuid.UUID(self.ev["id"]), kind=kind,
                observations={}, verdict="FAILED" if kind == failed_kind else "PASSED"))
        self.db.commit()

    def link_equipment(self):
        eq = Equipment(kind="WEIGHT_SET", name="M1 Set", serial_no="M1-WF")
        self.db.add(eq); self.db.commit()
        r = self.client.post(f"/api/evaluations/{self.ev['id']}/equipment",
                             headers=self.auth_h(self.engineer),
                             json={"equipment_id": str(eq.id)})
        assert r.status_code == 200


def test_submit_blocked_then_passes(client, make_user, auth_h, db_session):
    ws = Workspace(client, make_user, auth_h, db_session, "w1")

    # 1. nothing entered → gate lists missing tests
    r = ws.client.post(f"/api/evaluations/{ws.ev['id']}/submit", headers=auth_h(ws.engineer))
    assert r.status_code == 400
    assert "WEIGHING" in r.json()["detail"]["missing"]

    # 2. weighing saved but everything else missing + no equipment
    assert ws.save(WEIGHING_PASS).status_code == 201
    r = ws.client.post(f"/api/evaluations/{ws.ev['id']}/submit", headers=auth_h(ws.engineer))
    assert r.status_code == 400

    # 3. equipment linked, others still missing
    ws.link_equipment()
    r = ws.client.post(f"/api/evaluations/{ws.ev['id']}/submit", headers=auth_h(ws.engineer))
    assert r.status_code == 400
    assert "missing" in r.json()["detail"]

    # 4. all required verdicts present → submit OK
    ws.fill_required()
    r = ws.client.post(f"/api/evaluations/{ws.ev['id']}/submit", headers=auth_h(ws.engineer))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "SUBMITTED" and body["outcome"] == "PASS"

    # 5. observations now read-only
    assert ws.save(WEIGHING_PASS).status_code == 409


def test_review_cycle_with_return_and_reopen(client, make_user, auth_h, db_session):
    ws = Workspace(client, make_user, auth_h, db_session, "w2")
    ws.save(WEIGHING_PASS)
    ws.link_equipment()
    ws.fill_required()
    ev_id = ws.ev["id"]
    h_eng, h_rev = auth_h(ws.engineer), auth_h(ws.reviewer)

    assert ws.client.post(f"/api/evaluations/{ev_id}/submit", headers=h_eng).status_code == 200
    assert ws.client.post(f"/api/evaluations/{ev_id}/start-review", headers=h_rev).status_code == 200

    # reviewer returns with a comment → engineer reopens
    r = ws.client.post(f"/api/evaluations/{ev_id}/return", headers=h_rev,
                       json={"comment": "Recheck eccentricity location 3"})
    assert r.status_code == 200 and r.json()["status"] == "RETURNED"

    assert ws.client.post(f"/api/evaluations/{ev_id}/reopen", headers=h_eng).status_code == 200
    detail = ws.client.get(f"/api/evaluations/{ev_id}", headers=h_eng).json()
    assert detail["status"] == "IN_PROGRESS"


def test_approval_separation_of_duties_and_hash(client, make_user, auth_h, db_session):
    ws = Workspace(client, make_user, auth_h, db_session, "w3")
    ws.save(WEIGHING_PASS)
    ws.link_equipment()
    ws.fill_required()
    ev_id = ws.ev["id"]
    h_eng = auth_h(ws.engineer)

    ws.client.post(f"/api/evaluations/{ev_id}/submit", headers=h_eng)
    ws.client.post(f"/api/evaluations/{ev_id}/start-review", headers=auth_h(ws.reviewer))

    # the OBSERVER (engineer) cannot approve even with a reviewer token minted
    # for them — SoD triggers first because role guard blocks ENGINEER at /approve
    assert ws.client.post(f"/api/evaluations/{ev_id}/approve",
                          headers=h_eng).status_code == 403

    # a reviewer who IS the observer/creator → 403 SoD (craft: approve as reviewer2? No —
    # make reviewer2 the creator scenario via a second evaluation below)
    r = ws.client.post(f"/api/evaluations/{ev_id}/approve", headers=auth_h(ws.reviewer))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "APPROVED"
    assert len(body["approval_hash"]) == 64          # SHA-256 hex


def test_sod_blocks_observer_reviewer(client, make_user, auth_h, db_session):
    """Reviewer who is the evaluation's observer → 403 even with REVIEWER role."""
    ws = Workspace(client, make_user, auth_h, db_session, "w4")
    # re-assign observer to reviewer2 via direct DB (engineer created it, but we
    # simulate the doc's scenario: observer == approver attempt)
    ev = db_session.get(Evaluation, uuid.UUID(ws.ev["id"]))
    ev.observer_id = ws.reviewer2.id
    db_session.commit()

    ws.save(WEIGHING_PASS)                            # creator (engineer) still saves? No—
    # ^ creator==engineer so can_enter_observations allows (created_by match) ✓
    ws.link_equipment()
    ws.fill_required()
    ev_id = ws.ev["id"]

    ws.client.post(f"/api/evaluations/{ev_id}/submit", headers=auth_h(ws.engineer))
    ws.client.post(f"/api/evaluations/{ev_id}/start-review", headers=auth_h(ws.reviewer))

    r = ws.client.post(f"/api/evaluations/{ev_id}/approve", headers=auth_h(ws.reviewer2))
    assert r.status_code == 403                       # SoD: approver == observer


def test_failed_outcome_flows_through(client, make_user, auth_h, db_session):
    ws = Workspace(client, make_user, auth_h, db_session, "w5")
    ws.save(WEIGHING_PASS)
    ws.link_equipment()
    ws.fill_required(failed_kind="REPEATABILITY")     # one required test FAILED
    ev_id = ws.ev["id"]

    r = ws.client.post(f"/api/evaluations/{ev_id}/submit", headers=auth_h(ws.engineer))
    assert r.status_code == 200
    assert r.json()["outcome"] == "FAIL"              # submitted WITH a FAIL outcome


def test_instrument_frozen_after_approval(client, make_user, auth_h, db_session):
    ws = Workspace(client, make_user, auth_h, db_session, "w6")
    ws.save(WEIGHING_PASS)
    ws.link_equipment()
    ws.fill_required()
    ev_id = ws.ev["id"]
    inst_id = ws.client.get(f"/api/evaluations/{ev_id}",
                            headers=auth_h(ws.engineer)).json()["instrument_id"]

    ws.client.post(f"/api/evaluations/{ev_id}/submit", headers=auth_h(ws.engineer))
    ws.client.post(f"/api/evaluations/{ev_id}/start-review", headers=auth_h(ws.reviewer))
    ws.client.post(f"/api/evaluations/{ev_id}/approve", headers=auth_h(ws.reviewer))

    r = ws.client.patch(f"/api/instruments/{inst_id}", headers=auth_h(ws.engineer),
                        json={"remarks": "try to edit"})
    assert r.status_code == 409                       # frozen — create a new revision


def test_archive_admin_only(client, make_user, auth_h, db_session):
    ws = Workspace(client, make_user, auth_h, db_session, "w7")
    ws.save(WEIGHING_PASS)
    ws.link_equipment()
    ws.fill_required()
    ev_id = ws.ev["id"]
    ws.client.post(f"/api/evaluations/{ev_id}/submit", headers=auth_h(ws.engineer))
    ws.client.post(f"/api/evaluations/{ev_id}/start-review", headers=auth_h(ws.reviewer))
    ws.client.post(f"/api/evaluations/{ev_id}/approve", headers=auth_h(ws.reviewer))

    assert ws.client.post(f"/api/evaluations/{ev_id}/archive",
                          headers=auth_h(ws.engineer)).status_code == 403
    assert ws.client.post(f"/api/evaluations/{ev_id}/archive",
                          headers=auth_h(make_user(username="w7a", role="ADMIN"))
                          ).status_code == 200