"""Open-demo mode (ALLOW_ANY_LOGIN=true): any username/password signs in.

The autouse fixture in conftest forces strict mode for every other test;
these tests explicitly flip it back on via the `any_login` fixture.
"""
import pytest

from app.core.config import get_settings


@pytest.fixture()
def any_login():
    s = get_settings()
    previous = s.ALLOW_ANY_LOGIN
    s.ALLOW_ANY_LOGIN = True
    yield s
    s.ALLOW_ANY_LOGIN = previous


def _login(client, username, password="whatever1"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


class TestAnyLogin:
    def test_unknown_username_is_provisioned_and_returns_token(self, client, any_login):
        r = _login(client, "rahul")
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"]
        assert body["user"]["username"] == "rahul"
        assert body["must_change_password"] is False
        assert "nawi_refresh" in r.cookies

    def test_wrong_password_for_existing_user_accepted(self, client, make_user, any_login):
        make_user(username="eng", role="ENGINEER")
        r = _login(client, "eng", "totally-wrong")
        assert r.status_code == 200
        assert r.json()["user"]["username"] == "eng"
        assert r.json()["user"]["role"] == "ENGINEER"

    def test_provisioned_user_can_call_protected_apis(self, client, any_login):
        token = _login(client, "guest1").json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/auth/me", headers=h)
        assert me.status_code == 200
        assert me.json()["username"] == "guest1"
        assert me.json()["role"] == "ENGINEER"

        assert client.get("/api/dashboard/kpis", headers=h).status_code == 200

    def test_forced_password_change_is_bypassed(self, client, make_user, any_login):
        make_user(username="cp", role="ENGINEER", must_change=True)
        assert _login(client, "cp", "OldPass1").json()["must_change_password"] is False

    def test_odd_username_is_sanitised(self, client, any_login):
        r = _login(client, "dark knight!")
        assert r.status_code == 200
        assert r.json()["user"]["username"] == "darkknight"

    def test_collision_gets_unique_username(self, client, any_login):
        first = _login(client, "sam", "x").json()["user"]
        second = _login(client, "sam x", "x").json()["user"]  # sanitises to "sam"
        assert first["username"] == "sam"
        assert second["username"] != first["username"]

    def test_inactive_account_still_rejected(self, client, make_user, db_session, any_login):
        u = make_user(username="off", role="VIEWER")
        u.is_active = False
        db_session.commit()
        assert _login(client, "off").status_code == 403

    def test_strict_mode_restored_after_fixture(self):
        assert get_settings().ALLOW_ANY_LOGIN is False
