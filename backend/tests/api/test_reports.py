"""Reporting: model JSON, print HTML, DOCX export, PDF fallback, RBAC, versions."""
import uuid

from app.models import Equipment, Evaluation, Laboratory, TestRecord
from app.services.evaluation_service import outcome_preview

INSTRUMENT_OK = {
    "type_designation": "PS-15K-RPT", "category": "Platform scale",
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


def _prep(client, make_user, auth_h, db_session, tag: str):
    engineer = make_user(username=f"{tag}-eng", role="ENGINEER")
    reviewer = make_user(username=f"{tag}-rev", role="REVIEWER")
    viewer = make_user(username=f"{tag}-view", role="VIEWER")
    db_session.add(Laboratory(name=f"Lab {tag}", address="Metrology Bhawan"))
    db_session.commit()
    inst = client.post("/api/instruments", headers=auth_h(engineer),
                       json=INSTRUMENT_OK).json()
    ev = client.post("/api/evaluations", headers=auth_h(engineer),
                     json={"instrument_id": inst["id"],
                           "observer_id": str(engineer.id)}).json()
    r = client.post(f"/api/evaluations/{ev['id']}/tests",
                    headers=auth_h(engineer), json=WEIGHING_PASS)
    assert r.status_code == 201
    eq = Equipment(kind="WEIGHT_SET", name="M1 Set", serial_no="M1-RPT")
    db_session.add(eq)
    db_session.commit()
    client.post(f"/api/evaluations/{ev['id']}/equipment",
                headers=auth_h(engineer), json={"equipment_id": str(eq.id)})
    # fill remaining required tests directly
    db_ev = db_session.get(Evaluation, uuid.UUID(ev["id"]))
    for kind in outcome_preview(db_session, db_ev)["required"]:
        if not db_session.query(TestRecord).filter_by(
                evaluation_id=db_ev.id, kind=kind).first():
            db_session.add(TestRecord(evaluation_id=db_ev.id, kind=kind,
                                      observations={}, verdict="PASSED"))
    db_session.commit()
    return engineer, reviewer, viewer, ev


def test_report_model_json(client, make_user, auth_h, db_session):
    engineer, _, _, ev = _prep(client, make_user, auth_h, db_session, "rm")
    r = client.get(f"/api/evaluations/{ev['id']}/report", headers=auth_h(engineer))
    assert r.status_code == 200
    m = r.json()
    assert m["report_no"] == ev["report_no"]
    assert m["instrument"]["accuracy_class"] == "III"
    assert m["ranges"][0][4] == "3000"                    # n = 15 / 0.005
    assert any(p["verdict"] == "PASSED" for p in m["pages"])
    assert m["outcome"] in ("PASS", "INCOMPLETE")
    assert m["conformity"], "required kinds present"


def test_print_html(client, make_user, auth_h, db_session):
    engineer, _, _, ev = _prep(client, make_user, auth_h, db_session, "ph")
    r = client.get(f"/api/evaluations/{ev['id']}/report/print",
                   headers=auth_h(engineer))
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    body = r.text
    assert ev["report_no"] in body
    assert "TYPE EVALUATION REPORT" in body
    assert "Form 1" in body                                # weighing page rendered
    assert "window.print" in body                          # toolbar present


def test_docx_export_versions_and_download(client, make_user, auth_h, db_session):
    engineer, _, _, ev = _prep(client, make_user, auth_h, db_session, "dx")
    url = f"/api/evaluations/{ev['id']}/report"

    r1 = client.post(f"{url}/export", headers=auth_h(engineer),
                     json={"format": "DOCX"})
    assert r1.status_code == 200
    assert r1.json()["version"] == 1
    r2 = client.post(f"{url}/export", headers=auth_h(engineer),
                     json={"format": "DOCX"})
    assert r2.json()["version"] == 2                       # per-format versioning

    dl = client.get(f"{url}/exports/{r1.json()['id']}/download",
                    headers=auth_h(engineer))
    assert dl.status_code == 200
    assert dl.content[:2] == b"PK"                         # valid .docx (zip)
    assert "content-disposition" in dl.headers

    history = client.get(f"{url}/exports", headers=auth_h(engineer)).json()
    assert len(history) == 2
    assert all(len(h["sha256"]) == 64 for h in history)


def test_pdf_export_with_fallback(client, make_user, auth_h, db_session):
    engineer, _, _, ev = _prep(client, make_user, auth_h, db_session, "pf")
    r = client.post(f"/api/evaluations/{ev['id']}/report/export",
                    headers=auth_h(engineer), json={"format": "PDF"})
    # WeasyPrint is optional: 200 when installed, 503 with guidance when not.
    assert r.status_code in (200, 503)
    if r.status_code == 503:
        assert "WeasyPrint" in r.json()["detail"]


def test_viewer_rbac_on_export(client, make_user, auth_h, db_session):
    engineer, reviewer, viewer, ev = _prep(client, make_user, auth_h, db_session, "vr")
    url = f"/api/evaluations/{ev['id']}/report"
    h_view = auth_h(viewer)

    # not approved → viewer blocked
    assert client.post(f"{url}/export", headers=h_view,
                       json={"format": "DOCX"}).status_code == 403
    # viewer can still VIEW the report
    assert client.get(f"{url}", headers=h_view).status_code == 200

    # approve: engineer submits, reviewer reviews + approves
    assert client.post(f"/api/evaluations/{ev['id']}/submit",
                       headers=auth_h(engineer)).status_code == 200
    assert client.post(f"/api/evaluations/{ev['id']}/start-review",
                       headers=auth_h(reviewer)).status_code == 200
    assert client.post(f"/api/evaluations/{ev['id']}/approve",
                       headers=auth_h(reviewer)).status_code == 200

    # now viewer CAN export
    r = client.post(f"{url}/export", headers=h_view, json={"format": "DOCX"})
    assert r.status_code == 200
    # and the model carries the approval block
    m = client.get(f"{url}", headers=h_view).json()
    assert m["approver"] and len(m["approval_hash"]) == 64
    assert m["qr"] is not None                             # QR generated when approved


def test_exports_require_auth(client, make_user, auth_h, db_session):
    _, _, _, ev = _prep(client, make_user, auth_h, db_session, "an")
    assert client.get(f"/api/evaluations/{ev['id']}/report/print").status_code == 401
    assert client.post(f"/api/evaluations/{ev['id']}/report/export",
                       json={"format": "DOCX"}).status_code == 401