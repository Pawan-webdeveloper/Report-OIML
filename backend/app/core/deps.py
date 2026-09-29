"""
FastAPI dependencies: authentication + role-based access control.

Permission matrix (project.md §5.1) is enforced by wiring require_roles(...)
into each router — see routers/users.py for the ADMIN-only example.
Phase 5/9 will wire ENGINEER/REVIEWER/VIEWER guards onto
instruments / evaluations / workflow endpoints the same way.
"""
from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..models import User
from .db import get_db
from .security import ACCESS, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the Bearer access token → load an active user. 401 on any failure."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials, expected_type=ACCESS)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired",
                            headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token",
                            headers={"WWW-Authenticate": "Bearer"})

    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token subject")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def require_roles(*allowed: str):
    """Dependency factory — allow only the listed roles (403 otherwise)."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requires one of roles: {', '.join(sorted(allowed))}",
            )
        return user
    return checker


def assert_separation_of_duties(observer_id: uuid.UUID | None,
                                reviewer_id: uuid.UUID | None) -> None:
    """
    project.md §5.1: 'the approver cannot be the same person as the observer'.
    Used by the workflow endpoints (Phase 9) before approving an evaluation.
    """
    if observer_id and reviewer_id and observer_id == reviewer_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Separation of duties: the approver cannot be the same person as the observer",
        )