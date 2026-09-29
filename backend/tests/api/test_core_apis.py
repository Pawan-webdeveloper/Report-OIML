"""Core API tests: parties, instruments (Table 3 validation), equipment,
evaluations, the engine bridge (test-record save), attachments, RBAC."""
import uuid
from decimal import Decimal as D

from app.models import Equipment, Laboratory

WEIGHING_PASS = {
    "kind": "WEIGHING",
    "observations": {
        "zero": {"L": "0.02", "I": "0.02", "dL": "0.001"},
        "points": [
            {"L": "5", "up": {"I": "5.005", "dL": "0.0026"}},
            {"L": "12", "up": {"I": "12.005", "dL": "0.0036"}},
        ],
    },
}
WEIGHING_FAIL_12KG = {
    "kind": "WEIGHING",
    "observations": {
        "zero": {"L": "0.02", "I": "0.02", "dL": "0.001"},
        "points": [{"L": "12", "up": {"I": "12.01", "dL": "0.003"}}],
    },
}

INSTRUMENT_OK = {
    "type_designation": "PS-15K-API", "category": "Platform scale",
    "accuracy_class": "III", "min_capacity": "0.1", "unit": "kg",
    "power_supply_category": ["MAINS_AC"],
    "printer": "NOT_PRESENT_CONNECTABLE",
    "zero_devices": {"tracking": True},
    "tare_devices": {"subtractive": True},
    "ranges": [{"e": "0.005", "d": "0.005", "max": "15"}],
}
INSTRUMENT_BAD_N = {   # e = 1 g → n = 15000 > 10000 → Table 3 violation
    **INSTRUMENT_OK, "type_designation": "PS-BAD",
    "min_capacity": "0.02",
    "ranges": [{"e": "0.001", "d": "0.001", "max": "15"}],
}


class TestParties:
    def test_engineer_creates_party(self, client, make_user, auth_h):
        eng = make_user(username="pe", role="ENGINEER")
        r = client.post("/api/parties", headers=auth_h(eng),
                        json={"name": "Acme Scales", "kind": "MANUFACTURER"})
        assert r.status_code == 201
        assert r.json()["name"] == "Acme Scales"

    def test_viewer_cannot_create(self, client, make_user, auth_h):
        v = make_user(username="pv", role="VIEWER")
        assert client.post("/api/parties", headers=auth_h(v),
                           json={"name": "X"}).status_code == 403

    def test_list_requires_auth(self, client):
        assert client.get("/api/parties").status_code == 401


class TestInstruments:
    def test_create_valid_instrument(self, client, make_user, auth_h, db_session):
        eng = make_user(username="ie", role="ENGINEER")
        db_session.add(Laboratory(name="L1")); db_session.commit()
        r = client.post("/api/instruments", headers=auth_h(eng), json=INSTRUMENT_OK)
        assert r.status_code == 201
        body = r.json()
        assert body["ranges"][0]["e"] == "0.005"
        assert body["ranges"][0]["max_capacity"] == "15"
        # fetchable
        got = client.get(f"/api/instruments/{body['id']}", headers=auth_h(eng))
        assert got.status_code == 200

    def test_create_rejects_table3_violation(self, client, make_user, auth_h):
        eng = make_user(username="ie2", role="ENGINEER")
        r = client.post("/api/instruments", headers=auth_h(eng), json=INSTRUMENT_BAD_N)
        assert r.status_code == 400
        assert any(e["code"] == "T3_N" for e in r.json()["detail"]["errors"])

    def test_patch_revalidates(self, client, make_user, auth_h):
        eng = make_user(username="ie3", role="ENGINEER")
        inst = client.post("/api/instruments", headers=auth_h(eng),
                           json=INSTRUMENT_OK).json()
        bad = client.patch(f"/api/instruments/{inst['id']}", headers=auth_h(eng),
                           json={"ranges": [{"e": "0.001", "d": "0.001", "max": "15"}]})
        assert bad.status_code == 400

    def test_search_by_designation(self, client, make_user, auth_h):
        eng = make_user(username="ie4", role="ENGINEER")
        client.post("/api/instruments", headers=auth_h(eng), json=INSTRUMENT_OK)
        found = client.get("/api/instruments?q=PS-15K", headers=auth_h(eng))
        assert found.status_code == 200 and len(found.json()) == 1


class TestEquipment:
    def test_admin_creates_master(self, client, make_user, auth_h):
        admin = make_user(username="ea", role="ADMIN")
        r = client.post("/api/equipment", headers=auth_h(admin), json={
            "kind": "WEIGHT_SET", "name": "M1 Set", "serial_no": "M1-001",
            "accuracy_class_or_uncertainty": "M1"})
        assert r.status_code == 201

    def test_engineer_cannot_create_master(self, client, make_user, auth_h):
        eng = make_user(username="ee", role="ENGINEER")
        assert client.post("/api/equipment", headers=auth_h(eng),
                           json={"kind": "TIMER"}).status_code == 403

    def test_any_role_can_read(self, client, make_user, auth_h):
        v = make_user(username="ev", role="VIEWER")
        assert client.get("/api/equipment", headers=auth_h(v)).status_code == 200


class TestEngineBridge:
    def _setup(self, client, make_user, auth_h, db_session):
        eng = make_user(username="be", role="ENGINEER")
        db_session.add(Laboratory(name="L2")); db_session.commit()
        inst = client.post("/api/instruments", headers=auth_h(eng),
                           json=INSTRUMENT_OK).json()
        ev = client.post("/api/evaluations", headers=auth_h(eng),
                         json={"instrument_id": inst["id"]}).json()
        return eng, inst, ev

    def test_report_no_auto_generated(self, client, make_user, auth_h, db_session):
        eng, inst, ev = self._setup(client, make_user, auth_h, db_session)
        assert ev["report_no"].startswith("LM/NAWI/")
        assert ev["status"] == "DRAFT"

    def test_weighing_saved_with_verdict_and_status_transition(
            self, client, make_user, auth_h, db_session):
        eng, inst, ev = self._setup(client, make_user, auth_h, db_session)
        r = client.post(f"/api/evaluations/{ev['id']}/tests",
                        headers=auth_h(eng), json=WEIGHING_FAIL_12KG)
        assert r.status_code == 201
        body = r.json()
        assert body["verdict"] == "FAILED"                  # Ec = 8.0 > 7.5
        assert body["form_no"] == "1"
        assert D(body["computed"]["rows"][0]["up"]["Ec"]) == D("8.0")
        assert D(body["computed"]["rows"][0]["mpe"]) == D("7.5")  # 12 kg → grams, correct!

        detail = client.get(f"/api/evaluations/{ev['id']}", headers=auth_h(eng)).json()
        assert detail["status"] == "IN_PROGRESS"            # DRAFT auto-advanced

    def test_weighing_pass_case(self, client, make_user, auth_h, db_session):
        eng, inst, ev = self._setup(client, make_user, auth_h, db_session)
        r = client.post(f"/api/evaluations/{ev['id']}/tests",
                        headers=auth_h(eng), json=WEIGHING_PASS).json()
        assert r["verdict"] == "PASSED"

    def test_load_over_max_422(self, client, make_user, auth_h, db_session):
        eng, inst, ev = self._setup(client, make_user, auth_h, db_session)
        bad = {"kind": "WEIGHING",
               "observations": {"points": [{"L": "16",
                                            "up": {"I": "16", "dL": "0.002"}}]}}
        r = client.post(f"/api/evaluations/{ev['id']}/tests",
                        headers=auth_h(eng), json=bad)
        assert r.status_code == 422

    def test_unknown_kind_422(self, client, make_user, auth_h, db_session):
        eng, inst, ev = self._setup(client, make_user, auth_h, db_session)
        r = client.post(f"/api/evaluations/{ev['id']}/tests",
                        headers=auth_h(eng), json={"kind": "NOT_A_TEST",
                                                   "observations": {}})
        assert r.status_code == 422

    def test_unassigned_engineer_cannot_enter(self, client, make_user, auth_h,
                                              db_session):
        eng, inst, ev = self._setup(client, make_user, auth_h, db_session)
        other = make_user(username="other-eng", role="ENGINEER")
        r = client.post(f"/api/evaluations/{ev['id']}/tests",
                        headers=auth_h(other), json=WEIGHING_PASS)
        assert r.status_code == 403

    def test_viewer_and_reviewer_cannot_enter(self, client, make_user, auth_h,
                                              db_session):
        eng, inst, ev = self._setup(client, make_user, auth_h, db_session)
        assert client.post(f"/api/evaluations/{ev['id']}/tests",
                           headers=auth_h(make_user(username="rv", role="REVIEWER")),
                           json=WEIGHING_PASS).status_code == 403
        assert client.post(f"/api/evaluations/{ev['id']}/tests",
                           headers=auth_h(make_user(username="vw", role="VIEWER")),
                           json=WEIGHING_PASS).status_code == 403

    def test_required_tests_preview(self, client, make_user, auth_h, db_session):
        eng, inst, ev = self._setup(client, make_user, auth_h, db_session)
        r = client.get(f"/api/evaluations/{ev['id']}/required-tests",
                       headers=auth_h(eng)).json()
        assert "WEIGHING" in r["required"]
        assert r["outcome"] == "INCOMPLETE"


class TestAttachments:
    def _eval(self, client, make_user, auth_h, db_session):
        eng = make_user(username="ae", role="ENGINEER")
        db_session.add(Laboratory(name="L3")); db_session.commit()
        inst = client.post("/api/instruments", headers=auth_h(eng),
                           json=INSTRUMENT_OK).json()
        ev = client.post("/api/evaluations", headers=auth_h(eng),
                         json={"instrument_id": inst["id"]}).json()
        return eng, ev

    def test_upload_list_download(self, client, make_user, auth_h, db_session,
                                  upload_dir):
        eng, ev = self._eval(client, make_user, auth_h, db_session)
        r = client.post(f"/api/evaluations/{ev['id']}/attachments",
                        headers=auth_h(eng),
                        files={"file": ("nameplate.png", b"\x89PNG-fake", "image/png")},
                        data={"kind": "PHOTO", "caption": "Nameplate"})
        assert r.status_code == 201

        listed = client.get(f"/api/evaluations/{ev['id']}/attachments",
                            headers=auth_h(eng)).json()
        assert listed[0]["kind"] == "PHOTO" and listed[0]["sha256"]

        dl = client.get(f"/api/attachments/{listed[0]['id']}/download",
                        headers=auth_h(eng))
        assert dl.status_code == 200 and dl.content == b"\x89PNG-fake"

    def test_rejects_bad_type_and_kind(self, client, make_user, auth_h, db_session):
        eng, ev = self._eval(client, make_user, auth_h, db_session)
        r1 = client.post(f"/api/evaluations/{ev['id']}/attachments",
                         headers=auth_h(eng),
                         files={"file": ("x.exe", b"MZ", "application/x-msdownload")},
                         data={"kind": "PHOTO"})
        assert r1.status_code == 415
        r2 = client.post(f"/api/evaluations/{ev['id']}/attachments",
                         headers=auth_h(eng),
                         files={"file": ("x.png", b"x", "image/png")},
                         data={"kind": "VIRUS"})
        assert r2.status_code == 422

    def test_viewer_cannot_upload(self, client, make_user, auth_h, db_session):
        eng, ev = self._eval(client, make_user, auth_h, db_session)
        v = make_user(username="av", role="VIEWER")
        r = client.post(f"/api/evaluations/{ev['id']}/attachments", headers=auth_h(v),
                        files={"file": ("x.png", b"x", "image/png")},
                        data={"kind": "PHOTO"})
        assert r.status_code == 403

class TestLinkedEquipmentEndpoint:
    """GET /evaluations/{id}/equipment — linked master data for the workspace UI."""

    def _setup(self, client, make_user, auth_h, db_session):
        eng = make_user(username="le", role="ENGINEER")
        db_session.add(Laboratory(name="L-LE")); db_session.commit()
        inst = client.post("/api/instruments", headers=auth_h(eng),
                           json=INSTRUMENT_OK).json()
        ev = client.post("/api/evaluations", headers=auth_h(eng),
                         json={"instrument_id": inst["id"]}).json()
        eq = Equipment(kind="WEIGHT_SET", name="M1 Set", serial_no="M1-LE")
        db_session.add(eq); db_session.commit()
        return eng, ev, eq

    def test_empty_then_linked(self, client, make_user, auth_h, db_session):
        eng, ev, eq = self._setup(client, make_user, auth_h, db_session)

        r0 = client.get(f"/api/evaluations/{ev['id']}/equipment", headers=auth_h(eng))
        assert r0.status_code == 200 and r0.json() == []

        client.post(f"/api/evaluations/{ev['id']}/equipment", headers=auth_h(eng),
                    json={"equipment_id": str(eq.id)})
        r1 = client.get(f"/api/evaluations/{ev['id']}/equipment", headers=auth_h(eng))
        assert r1.status_code == 200
        rows = r1.json()
        assert len(rows) == 1 and rows[0]["serial_no"] == "M1-LE"

    def test_requires_auth(self, client, make_user, auth_h, db_session):
        _, ev, _ = self._setup(client, make_user, auth_h, db_session)
        assert client.get(f"/api/evaluations/{ev['id']}/equipment").status_code == 401

    def test_unknown_evaluation_404(self, client, make_user, auth_h):
        v = make_user(username="lv", role="VIEWER")
        assert client.get(f"/api/evaluations/{uuid.uuid4()}/equipment",
                          headers=auth_h(v)).status_code == 404
