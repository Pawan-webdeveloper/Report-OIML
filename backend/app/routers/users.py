"""
User administration — ADMIN only (project.md §5.1: 'Manage users...').

Guards implemented here:
- No self-deactivation (an admin cannot lock themselves out).
- Last-active-admin protection (cannot demote/deactivate the only admin).
- Unique username/email (409 on duplicates).
- Admin-set passwords force must_change_password=True on first login.
- Every mutation writes an audit_log row with before/after snapshots.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import require_roles
from ..core.security import hash_password
from ..models import User
from ..schemas.auth import UserCreate, UserOut, UserUpdate
from ..services.audit_service import log_action, user_snapshot

router = APIRouter(prefix="/users", tags=["users"])

_is_admin = require_roles("ADMIN")


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(_is_admin)):
    return db.scalars(select(User).order_by(User.username)).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, request: Request,
                db: Session = Depends(get_db), admin: User = Depends(_is_admin)):
    if db.scalar(select(User).where(User.username == body.username)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")

    user = User(username=body.username, full_name=body.full_name, email=body.email,
                password_hash=hash_password(body.password), role=body.role,
                must_change_password=True)
    db.add(user)
    db.flush()
    log_action(db, user_id=admin.id, action="USER_CREATED", entity="user",
               entity_id=str(user.id), after=user_snapshot(user), ip=_ip(request))
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db),
             _admin: User = Depends(_is_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: uuid.UUID, body: UserUpdate, request: Request,
                db: Session = Depends(get_db), admin: User = Depends(_is_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    before = user_snapshot(user)

    # Guard 1 — no self-deactivation
    if body.is_active is False and user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "You cannot deactivate your own account")

    # Guard 2 — last active admin cannot lose the ADMIN role
    if body.role is not None and body.role != user.role and user.role == "ADMIN":
        active_admins = db.scalar(
            select(func.count()).select_from(User)
            .where(User.role == "ADMIN", User.is_active.is_(True)))
        if active_admins is not None and active_admins <= 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Cannot demote the last active administrator")
        user.role = body.role
    elif body.role is not None:
        user.role = body.role

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.email is not None:
        dup = db.scalar(select(User).where(User.email == body.email, User.id != user.id))
        if dup:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")
        user.email = body.email
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.new_password is not None:
        user.password_hash = hash_password(body.new_password)
        user.must_change_password = True

    log_action(db, user_id=admin.id, action="USER_UPDATED", entity="user",
               entity_id=str(user.id), before=before,
               after=user_snapshot(user), ip=_ip(request))
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/unlock", response_model=UserOut)
def unlock_user(user_id: uuid.UUID, request: Request,
                db: Session = Depends(get_db), admin: User = Depends(_is_admin)):
    """Clear a brute-force lock before it expires (ADMIN action)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.failed_logins = 0
    user.locked_until = None
    log_action(db, user_id=admin.id, action="USER_UNLOCKED", entity="user",
               entity_id=str(user.id), ip=_ip(request))
    db.commit()
    db.refresh(user)
    return user