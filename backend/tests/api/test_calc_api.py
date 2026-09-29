from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PAYLOAD = {
    "accuracy_class": "III",
    "min_capacity": "0.1",
    "unit": "kg",
    "ranges": [{"e": "0.005", "d": "0.005", "max": "15"}],
    "load": "12",
    "context": "INITIAL",
}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_mpe_endpoint_converts_unit_to_grams():
    # 12 kg = 12000 g = 2400 e → Class III band (2000, 10000] → 1.5e = 7.5 g
    r = client.post("/api/calc/mpe", json=PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert body["mpe"] == "7.5000"
    assert body["base_unit"] == "g"


def test_mpe_endpoint_in_service_doubles():
    r = client.post("/api/calc/mpe", json={**PAYLOAD, "context": "IN_SERVICE"})
    assert r.status_code == 200
    assert r.json()["mpe"] == "15.0000"


def test_mpe_endpoint_overload_422():
    r = client.post("/api/calc/mpe", json={**PAYLOAD, "load": "16"})
    assert r.status_code == 422


def test_mpe_endpoint_invalid_unit_422():
    r = client.post("/api/calc/mpe", json={**PAYLOAD, "unit": "lb"})
    assert r.status_code == 422


def test_mpe_endpoint_bad_class_422():
    r = client.post("/api/calc/mpe", json={**PAYLOAD, "accuracy_class": "X"})
    assert r.status_code == 422
