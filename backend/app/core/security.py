"""
Password hashing (argon2) and JWT creation/verification.

Design notes (project.md §3.1 / §5):
- Passwords: argon2id via argon2-cffi.
- Access token:  short-lived (15 min), sent as `Authorization: Bearer <token>`.
- Refresh token: long-lived (7 days), httpOnly cookie scoped to /api/auth,
  ROTATED on every refresh. No server-side blacklist in this phase —
  short access window keeps the blast radius small (documented trade-off).
- Token payload carries: sub (user id), role, type (access|refresh),
  iat, exp, jti (unique id — ready for future revocation lists).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError, VerificationError

from .config import get_settings

settings = get_settings()

_ph = PasswordHasher()

ACCESS = "access"
REFRESH = "refresh"


# ------------------------------------------------------------------ time helpers
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_aware(dt: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes — treat them as UTC for comparisons."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


# ------------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        _ph.verify(password_hash, password)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ----------------------------------------------------------------------- JWT
def _create_token(user_id: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": uuid4().hex,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(user_id, role, ACCESS,
                         timedelta(minutes=settings.ACCESS_TOKEN_MINUTES))


def create_refresh_token(user_id: str, role: str) -> str:
    return _create_token(user_id, role, REFRESH,
                         timedelta(days=settings.REFRESH_TOKEN_DAYS))


def decode_token(token: str, expected_type: str = ACCESS) -> dict:
    """Verify signature + expiry + token type. Raises jwt.InvalidTokenError on failure."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected a {expected_type} token, got {payload.get('type')!r}")
    return payload