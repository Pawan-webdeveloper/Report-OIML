"""Audit trail viewer — ADMIN and REVIEWER only (doc §5.1)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import require_roles
from ..models import AuditLog, User
from ..schemas.admin import AuditOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditOut])
def list_audit(
    action: str | None = None,
    entity: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("ADMIN", "REVIEWER")),
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
    if entity:
        stmt = stmt.where(AuditLog.entity.ilike(f"%{entity}%"))
    stmt = stmt.order_by(AuditLog.id.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()