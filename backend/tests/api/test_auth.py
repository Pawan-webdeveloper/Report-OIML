"""End-to-end auth flow tests: login, lockout, refresh, logout, me, change password."""
from datetime import timedelta

import pytest

from app.core.security import create_access_token, utcnow

PASSWORD = "Passw0rd1"


def _login(client, username, password=PASSWORD):
    return client.post("/api/auth/login", json={"username": username, "password": password})


class TestLogin:
    def test_success_returns_token_cookie_and_user(self, client, make_user):
        make_user(username="eng", role="ENGINEER")
        r = _login(client, "eng")
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"]
        assert body["user"]["role"] == "ENGINEER"
        assert body["must_change_password"] is False
        assert "nawi_refresh" in r.cookies

    def test_wrong_password_401(self, client, make_user):
        make_user(username="u1", role="VIEWER")
        assert _login(client, "u1", "nope").status_code == 401

    def test_unknown_username_401_generic_message(self, client):
        r = _login(client, "ghost")
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid username or password"

    def test_lockout_after_five_failures(self, client, make_user):
        make_user(username="locky", role="ENGINEER")
        for _ in range(5):
            assert _login(client, "locky", "wrong").status_code == 401
        # locked — even the CORRECT password is now rejected
        r = _login(client, "locky")
        assert r.status_code == 423

    def test_lock_expires(self, client, make_user, db_session):
        u = make_user(username="oldlock", role="VIEWER")
        u.locked_until = utcnow() - timedelta(minutes=1)   # lock in the past
        db_session.commit()
        assert _login(client, "oldlock").status_code == 200

    def test_disabled_account_403(self, client, make_user, db_session):
        u = make_user(username="off", role="VIEWER")
        u.is_active = False
        db_session.commit()
        assert _login(client, "off").status_code == 403


class TestMe:
    def test_requires_token(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_with_token(self, client, make_user, auth_h):
        u = make_user(username="me1", role="ENGINEER")
        r = client.get("/api/auth/me", headers=auth_h(u))
        assert r.status_code == 200
        assert r.json()["username"] == "me1"

    def test_refresh_token_rejected_as_access(self, client, make_user, auth_h):
        u = make_user(username="x1", role="VIEWER")
        from app.core.security import create_refresh_token
        bad = {"Authorization": f"Bearer {create_refresh_token(str(u.id), u.role)}"}
        assert client.get("/api/auth/me", headers=bad).status_code == 401

    def test_inactive_user_token_rejected(self, client, make_user, auth_h, db_session):
        u = make_user(username="dead", role="VIEWER")
        h = auth_h(u)
        u.is_active = False
        db_session.commit()
        assert client.get("/api/auth/me", headers=h).status_code == 401


class TestRefreshLogout:
    def test_refresh_flow_returns_new_access(self, client, make_user):
        make_user(username="rf", role="VIEWER")
        first = _login(client, "rf").json()["access_token"]

        r = client.post("/api/auth/refresh")
        assert r.status_code == 200
        assert r.json()["access_token"]
        assert r.json()["access_token"] != first        # rotation happened

        me = client.get("/api/auth/me",
                        headers={"Authorization": f"Bearer {r.json()['access_token']}"})
        assert me.status_code == 200

    def test_refresh_without_cookie_401(self, client):
        assert client.post("/api/auth/refresh").status_code == 401

    def test_refresh_rejects_access_token_in_cookie(self, client, make_user):
        u = make_user(username="ra", role="VIEWER")
        client.cookies.set("nawi_refresh", create_access_token(str(u.id), u.role))
        assert client.post("/api/auth/refresh").status_code == 401

    def test_logout_then_refresh_fails(self, client, make_user):
        make_user(username="lo", role="VIEWER")
        _login(client, "lo")
        assert client.post("/api/auth/logout").status_code == 200
        assert client.post("/api/auth/refresh").status_code == 401


class TestChangePassword:
    def test_full_flow(self, client, make_user):
        make_user(username="cp", role="ENGINEER", password="OldPass1", must_change=True)
        login = _login(client, "cp", "OldPass1")
        assert login.json()["must_change_password"] is True
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        r = client.post("/api/auth/change-password", headers=h,
                        json={"current_password": "OldPass1", "new_password": "NewPass99"})
        assert r.status_code == 200

        assert _login(client, "cp", "OldPass1").status_code == 401      # old dead
        again = _login(client, "cp", "NewPass99")
        assert again.status_code == 200
        assert again.json()["must_change_password"] is False            # flag cleared

    def test_wrong_current_password(self, client, make_user, auth_h):
        u = make_user(username="cw", role="VIEWER")
        r = client.post("/api/auth/change-password", headers=auth_h(u),
                        json={"current_password": "nope", "new_password": "NewPass99"})
        assert r.status_code == 400

    def test_same_password_rejected(self, client, make_user, auth_h):
        u = make_user(username="same", role="VIEWER")
        r = client.post("/api/auth/change-password", headers=auth_h(u),
                        json={"current_password": PASSWORD, "new_password": PASSWORD})
        assert r.status_code == 400

    def test_policy_requires_letter_and_digit(self, client, make_user, auth_h):
        u = make_user(username="pol", role="VIEWER")
        r = client.post("/api/auth/change-password", headers=auth_h(u),
                        json={"current_password": PASSWORD, "new_password": "nodigitshere"})
        assert r.status_code == 422

    def test_requires_auth(self, client):
        r = client.post("/api/auth/change-password",
                        json={"current_password": "a", "new_password": "b"})
        assert r.status_code == 401


class TestAudit:
    def test_login_success_and_failure_logged(self, client, make_user, db_session):
        from sqlalchemy import select

        from app.models import AuditLog
        make_user(username="aud", role="VIEWER")
        _login(client, "aud", "wrong")           # failure
        _login(client, "aud")                    # success

        actions = db_session.scalars(
            select(AuditLog.action).where(AuditLog.action.like("AUTH_%"))).all()
        assert actions.count("AUTH_LOGIN_FAILED") == 1
        assert actions.count("AUTH_LOGIN") == 1