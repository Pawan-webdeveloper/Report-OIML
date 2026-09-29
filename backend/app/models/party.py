import uuid

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from ._types import UUIDType


class Party(Base):
    """Doc §4 — parties (manufacturer / applicant / agent)."""

    __tablename__ = "parties"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('MANUFACTURER','APPLICANT','AGENT')", name="ck_parties_kind"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="MANUFACTURER")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    gstin: Mapped[str | None] = mapped_column(String(32))
    contact: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))