import uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from ._types import UUIDType


class Laboratory(Base):
    """Doc §4 — laboratories (that perform the testing, e.g. RRSL)."""

    __tablename__ = "laboratories"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    accreditation_no: Mapped[str | None] = mapped_column(String(64))   # NABL no.
    logo_path: Mapped[str | None] = mapped_column(String(512))
    contact: Mapped[str | None] = mapped_column(String(64))