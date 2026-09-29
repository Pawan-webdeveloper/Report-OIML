"""
API test fixtures: isolated in-memory DB wired into the app via
dependency_overrides + helpers to mint users and auth headers.
"""
import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app

_ph = PasswordHasher()
DEFAULT_PASSWORD = "Passw0rd1"


@pytest.fixture(autouse=True)
def _strict_login():
    """Auth tests assert real credential checking → force ALLOW_ANY_LOGIN off.

    The open-demo bypass has its own tests in tests/api/test_any_login.py.
    """
    from app.core.config import get_settings

    s = get_settings()
    previous = s.ALLOW_ANY_LOGIN
    s.ALLOW_ANY_LOGIN = False
    yield
    s.ALLOW_ANY_LOGIN = previous


@pytest.fixture()
def db_session():
    eng = create_engine("sqlite://",
                        connect_args={"check_same_thread": False},
                        poolclass=StaticPool)

    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(eng)
    TestingSession = sessionmaker(bind=eng, autoflush=False,
                                  autocommit=False, expire_on_commit=False)
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    """Factory: make_user(username=..., role=..., password=DEFAULT_PASSWORD)."""
    counter = {"n": 0}

    def _make(username: str | None = None, role: str = "VIEWER",
              password: str = DEFAULT_PASSWORD, must_change: bool = False):
        counter["n"] += 1
        username = username or f"user{counter['n']}"
        u = db_session.merge(__import__("app.models", fromlist=["User"]).User(
            username=username, full_name=username.title(),
            email=f"{username}@test.in", password_hash=_ph.hash(password),
            role=role, must_change_password=must_change))
        db_session.commit()
        db_session.refresh(u)
        return u

    return _make


@pytest.fixture()
def auth_h():
    """Mint an Authorization header for a user without going through login."""
    def _h(user):
        from app.core.security import create_access_token
        return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}
    return _h

# add at the bottom of tests/api/conftest.py
import pytest


@pytest.fixture()
def upload_dir(tmp_path, monkeypatch):
    """Redirect attachment storage to a temp dir for the test session."""
    from app.core.config import get_settings
    s = get_settings()
    monkeypatch.setattr(s, "UPLOAD_DIR", str(tmp_path))
    return tmp_path