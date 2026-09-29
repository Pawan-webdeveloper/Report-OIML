# app/models/ruleset.py
from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from ._types import JSONType


class Ruleset(Base):
    """Doc §4 — versioned rule sets (GOLDEN RULE #2: rules = data, not code)."""
    __tablename__ = "rulesets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # 'oiml-r76-2006'
    title: Mapped[str | None] = mapped_column(String(255))
    effective_from: Mapped[date | None] = mapped_column(Date)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    document: Mapped[dict] = mapped_column(JSONType, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)