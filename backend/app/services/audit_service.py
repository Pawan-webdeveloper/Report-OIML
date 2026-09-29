"""Audit helpers — write audit_log rows (project §4: every write inserts a row)."""
import uuid

from sqlalchemy.orm import Session

from ..models import AuditLog, User


def log_action(db: Session, *, action: str, user_id: uuid.UUID | None = None,
               entity: str | None = None, entity_id: str | None = None,
               before: dict | None = None, after: dict | None = None,
               ip: str | None = None) -> AuditLog:
    """Add one audit_log row; the caller owns the transaction (commit/rollback)."""
    entry = AuditLog(user_id=user_id, action=action, entity=entity,
                     entity_id=entity_id, before=before, after=after, ip=ip)
    db.add(entry)
    return entry


def user_snapshot(user: User) -> dict:
    """Safe user fields for before/after audit snapshots (never the password hash)."""
    return {
        "id": str(user.id),
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "must_change_password": user.must_change_password,
        "failed_logins": user.failed_logins,
        "locked_until": user.locked_until.isoformat() if user.locked_until else None,
    }
