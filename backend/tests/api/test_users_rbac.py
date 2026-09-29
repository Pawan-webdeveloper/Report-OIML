"""RBAC matrix + admin guard tests (project.md §5.1)."""
import uuid

import pytest
from fastapi import HTTPException

from app.core.deps import assert_separation_of_duties


def _payload(username: str, role: str = "ENGINEER") -> dict:
    return {"username": username, "full_name": username.title(),
            "email": f"{username}@test.in", "password": "Starter1", "role": role}


class TestRbacMatrix:
    def test_admin_can_create_user(self, client, make_user, auth_h):
        admin = make_user(username="root", role="ADMIN")
        r = client.post("/api/users", headers=auth_h(admin), json=_payload("neweng"))
        assert r.status_code == 201
        body = r.json()
        assert body["role"] == "ENGINEER"
        assert body["must_change_password"] is True    # admin-set password forces change

    def test_engineer_cannot_create_user(self, client, make_user, auth_h):
        eng = make_user(username="e1", role="ENGINEER")
        r = client.post("/api/users", headers=auth_h(eng), json=_payload("nope"))
        assert r.status_code == 403

    def test_reviewer_cannot_create_user(self, client, make_user, auth_h):
        rev = make_user(username="r1", role="REVIEWER")
        assert client.post("/api/users", headers=auth_h(rev),
                           json=_payload("nope2")).status_code == 403

    def test_viewer_cannot_list_users(self, client, make_user, auth_h):
        v = make_user(username="v1", role="VIEWER")
        assert client.get("/api/users", headers=auth_h(v)).status_code == 403

    def test_anonymous_gets_401(self, client):
        assert client.get("/api/users").status_code == 401

    def test_viewer_can_still_use_me(self, client, make_user, auth_h):
        v = make_user(username="v2", role="VIEWER")
        assert client.get("/api/auth/me", headers=auth_h(v)).status_code == 200


class TestAdminGuards:
    def test_duplicate_username_409(self, client, make_user, auth_h):
        admin = make_user(username="adm", role="ADMIN")
        make_user(username="taken", role="VIEWER")
        assert client.post("/api/users", headers=auth_h(admin),
                           json=_payload("taken")).status_code == 409

    def test_duplicate_email_409(self, client, make_user, auth_h):
        admin = make_user(username="adm2", role="ADMIN")
        make_user(username="occ", role="VIEWER")
        body = _payload("other")
        body["email"] = "occ@test.in"
        assert client.post("/api/users", headers=auth_h(admin),
                           json=body).status_code == 409

    def test_cannot_deactivate_self(self, client, make_user, auth_h):
        admin = make_user(username="selfy", role="ADMIN")
        r = client.patch(f"/api/users/{admin.id}", headers=auth_h(admin),
                         json={"is_active": False})
        assert r.status_code == 400

    def test_cannot_demote_last_admin(self, client, make_user, auth_h):
        admin = make_user(username="last", role="ADMIN")
        r = client.patch(f"/api/users/{admin.id}", headers=auth_h(admin),
                         json={"role": "VIEWER"})
        assert r.status_code == 400

    def test_can_demote_when_second_admin_exists(self, client, make_user, auth_h, db_session):
        from app.models import User
        a1 = make_user(username="a1", role="ADMIN")
        a2 = make_user(username="a2", role="ADMIN")
        r = client.patch(f"/api/users/{a2.id}", headers=auth_h(a1),
                         json={"role": "VIEWER"})
        assert r.status_code == 200
        assert db_session.get(User, a2.id).role == "VIEWER"

    def test_admin_reset_password_forces_change(self, client, make_user, auth_h):
        admin = make_user(username="adm3", role="ADMIN")
        u = make_user(username="forgot", role="VIEWER")
        r = client.patch(f"/api/users/{u.id}", headers=auth_h(admin),
                         json={"new_password": "ResetPass1"})
        assert r.status_code == 200
        assert r.json()["must_change_password"] is True

    def test_unlock_clears_lock(self, client, make_user, auth_h, db_session):
        from datetime import timedelta

        from app.core.security import utcnow
        admin = make_user(username="adm4", role="ADMIN")
        u = make_user(username="stuck", role="VIEWER")
        u.locked_until = utcnow() + timedelta(minutes=10)
        db_session.commit()

        r = client.post(f"/api/users/{u.id}/unlock", headers=auth_h(admin))
        assert r.status_code == 200
        assert r.json().get("locked_until") is None or r.json()  # field not exposed; verify via login
        login = client.post("/api/auth/login",
                            json={"username": "stuck", "password": "Passw0rd1"})
        assert login.status_code == 200

    def test_get_missing_user_404(self, client, make_user, auth_h):
        admin = make_user(username="adm5", role="ADMIN")
        r = client.get(f"/api/users/{uuid.uuid4()}", headers=auth_h(admin))
        assert r.status_code == 404


class TestSeparationOfDuties:
    def test_different_ids_ok(self):
        a, b = uuid.uuid4(), uuid.uuid4()
        assert_separation_of_duties(a, b)          # no exception

    def test_same_ids_rejected(self):
        a = uuid.uuid4()
        with pytest.raises(HTTPException) as ei:
            assert_separation_of_duties(a, a)
        assert ei.value.status_code == 403

    def test_none_observer_ok(self):
        assert_separation_of_duties(None, uuid.uuid4())