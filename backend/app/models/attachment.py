import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from ._types import UUIDType


class Attachment(Base):
    """Doc §4 — photos / sketches / documents (optional inclusion in report)."""
    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint("kind IN ('PHOTO','SKETCH','DOCUMENT','CERTIFICATE','RAW_DATA')",
                        name="ck_attachments_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("evaluations.id", ondelete="CASCADE"))
    test_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("test_records.id", ondelete="CASCADE"))

    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255))
    mime: Mapped[str | None] = mapped_column(String(64))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    sha256: Mapped[str | None] = mapped_column(String(64))
    storage_path: Mapped[str | None] = mapped_column(String(512))
    caption: Mapped[str | None] = mapped_column(String(255))
    include_in_report: Mapped[bool] = mapped_column(Boolean, default=True)

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())