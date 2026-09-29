"""Response models for the admin/management routers."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    at: datetime
    action: str
    entity: str | None = None
    entity_id: str | None = None
    user_id: UUID | None = None
    ip: str | None = None


class RulesetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None = None
    effective_from: date | None = None
    sha256: str
    is_active: bool


class RulesetDetail(RulesetOut):
    document: dict