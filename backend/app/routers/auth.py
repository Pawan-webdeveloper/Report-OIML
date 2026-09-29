"""
Auth endpoints:
  POST /api/auth/login             → access token + httpOnly refresh cookie
  POST /api/auth/refresh           → new access token (rotates refresh cookie)
  POST /api/auth/logout            → clears refresh cookie
  GET  /api/auth/me                → current user profile
  POST /api/auth/change-password   → self-service password change

Security behaviours:
- Generic 'Invalid username or password' (never reveals which part failed).
- Account lockout: MAX_FAILED_LOGINS consecutive failures → locked for
  ACCOUNT_LOCK_MINUTES (423 Locked). Counter resets on lock and on success.
- Login success/failure, password change → audit_log rows.
- ALLOW_ANY_LOGIN=true (open demo): any credentials sign in and unknown
  usernames are auto-provisioned; set it to false to enforce the above.
"""
from __future__ import annotations

import re
import uuid
from datetime import timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import get_db
from ..core.deps import get_current_user
from ..core.security import (REFRESH, as_aware, create_access_token,
                             create_refresh_token, decode_token, hash_password,
                             utcnow, verify_password)
from ..models import User
from ..schemas.auth import (AccessTokenResponse, ChangePasswordRequest,
                            LoginRequest, TokenResponse, UserOut)
from ..services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

_COOKIE_PATH = f"{settings.API_PREFIX}/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,                     # not readable by JS (XSS mitigation)
        secure=settings.COOKIE_SECURE,     # set True behind HTTPS (prod)
        samesite="lax",                    # CSRF mitigation for top-level navigations
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        path=_COOKIE_PATH,                 # cookie only travels to /api/auth/*
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path=_COOKIE_PATH)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _guest_user(db: Session, username: str, password: str) -> User:
    """Open-demo mode: auto-provision an active ENGINEER for an unknown username."""
    raw = username.strip()
    clean = re.sub(r"[^A-Za-z0-9_.-]", "", raw)[:64] or f"user-{uuid.uuid4().hex[:8]}"
    if db.scalar(select(User).where(User.username == clean)):
        clean = f"{clean}-{uuid.uuid4().hex[:6]}"[:64]
    email = f"{clean}@demo.local"
    if db.scalar(select(User).where(User.email == email)):
        email = f"{clean}-{uuid.uuid4().hex[:6]}@demo.local"
    user = User(
        username=clean,
        full_name=raw[:255] or clean,
        email=email,
        password_hash=hash_password(password),
        role="ENGINEER",
        is_active=True,
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ------------------------------------------------------------------------ login
@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, response: Response,
          db: Session = Depends(get_db)):
    ip = _client_ip(request)
    demo = settings.ALLOW_ANY_LOGIN
    user = db.scalar(select(User).where(User.username == body.username))

    if user is None:
        if not demo:
            log_action(db, action="AUTH_LOGIN_FAILED", entity="user",
                       after={"username": body.username}, ip=ip)
            db.commit()
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
        user = _guest_user(db, body.username, body.password)

    if demo:
        # Open demo: any password is accepted, lockout counters are ignored.
        user.failed_logins = 0
        user.locked_until = None
        if not user.is_active:
            db.commit()
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
        db.commit()
    else:
        if as_aware(user.locked_until) and as_aware(user.locked_until) > utcnow():
            raise HTTPException(status.HTTP_423_LOCKED,
                                "Account temporarily locked — try again later")

        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")

        if not verify_password(user.password_hash, body.password):
            user.failed_logins += 1
            if user.failed_logins >= settings.MAX_FAILED_LOGINS:
                user.locked_until = utcnow() + timedelta(minutes=settings.ACCOUNT_LOCK_MINUTES)
                user.failed_logins = 0        # counter resets once the lock is applied
            log_action(db, action="AUTH_LOGIN_FAILED", user_id=user.id, entity="user",
                       entity_id=str(user.id), ip=ip)
            db.commit()
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

        user.failed_logins = 0
        user.locked_until = None
        db.commit()

    access = create_access_token(str(user.id), user.role)
    _set_refresh_cookie(response, create_refresh_token(str(user.id), user.role))
    log_action(db, action="AUTH_LOGIN", user_id=user.id, entity="user",
               entity_id=str(user.id), ip=ip)
    db.commit()

    out = UserOut.model_validate(user)
    if demo:
        out = out.model_copy(update={"must_change_password": False})
    return TokenResponse(access_token=access,
                         must_change_password=out.must_change_password,
                         user=out)


# ---------------------------------------------------------------------- refresh
@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token")
    try:
        payload = decode_token(token, expected_type=REFRESH)
    except jwt.InvalidTokenError:
        _clear_refresh_cookie(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    user = db.get(User, uuid.UUID(str(payload["sub"])))
    if user is None or not user.is_active:
        _clear_refresh_cookie(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    access = create_access_token(str(user.id), user.role)
    _set_refresh_cookie(response, create_refresh_token(str(user.id), user.role))  # rotation
    return AccessTokenResponse(access_token=access)


# ----------------------------------------------------------------------- logout
@router.post("/logout")
def logout(response: Response):
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


# -------------------------------------------------------------------------- me
@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


# -------------------------------------------------------------- change password
@router.post("/change-password")
def change_password(body: ChangePasswordRequest, request: Request,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(user.password_hash, body.current_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    if body.current_password == body.new_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "New password must be different from the current password")

    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    log_action(db, action="AUTH_PASSWORD_CHANGED", user_id=user.id, entity="user",
               entity_id=str(user.id), ip=_client_ip(request))
    db.commit()
    return {"message": "Password updated successfully"}