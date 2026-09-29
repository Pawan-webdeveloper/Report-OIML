import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from ._types import UUIDType


class Review(Base):
    """Doc §4 — reviewer decisions (RETURNED / APPROVED)."""
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("decision IN ('RETURNED','APPROVED')", name="ck_reviews_decision"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("evaluations.id", ondelete="CASCADE"))
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())


class ReportExport(Base):
    """Doc §4 — generated PDF/DOCX/JSON exports (+ version + integrity hash)."""
    __tablename__ = "report_exports"
    __table_args__ = (
        CheckConstraint("format IN ('PDF','DOCX','JSON')", name="ck_exports_format"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("evaluations.id", ondelete="CASCADE"))
    format: Mapped[str] = mapped_column(String(8), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    storage_path: Mapped[str | None] = mapped_column(String(512))
    sha256: Mapped[str | None] = mapped_column(String(64))
    signed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())