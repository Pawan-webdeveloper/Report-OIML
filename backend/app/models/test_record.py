import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String,
    Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base
from ._types import JSONType, UUIDType


class TestRecord(Base):
    """
    Doc §4 — ONE PAGE of R 76-2 = one row (identified by kind + instance_no).

    GOLDEN RULE #3: observations stay RAW/immutable (enforced by the Phase 5
    service layer after SUBMITTED), computed values stored separately (recomputable).
    """
    __tablename__ = "test_records"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "kind", "instance_no", name="uq_test_records_page"),
        CheckConstraint("verdict IN ('PASSED','FAILED','NOT_APPLICABLE','PENDING')",
                        name="ck_tr_verdict"),
        Index("ix_test_records_eval_kind", "evaluation_id", "kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)

    kind: Mapped[str] = mapped_column(String(32), nullable=False)   # WEIGHING, ECC_WEIGHTS, ...
    form_no: Mapped[str | None] = mapped_column(String(8))          # '1', '3.1', '12.4a'
    instance_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    condition_label: Mapped[str | None] = mapped_column(String(64))  # 'Initial 20 C', 'High 40 C'
    test_date: Mapped[date | None] = mapped_column(Date)
    observer_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))

    # { "start": {temp, rh, time, pressure}, "max": {...}, "end": {...} }
    environment: Mapped[dict | None] = mapped_column(JSONType)

    observations: Mapped[dict] = mapped_column(JSONType, nullable=False)  # RAW
    computed: Mapped[dict | None] = mapped_column(JSONType)               # engine output cache
    verdict: Mapped[str | None] = mapped_column(String(16))
    warnings: Mapped[list | None] = mapped_column(JSONType)               # plausibility warnings
    remarks: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    evaluation: Mapped["Evaluation"] = relationship(back_populates="test_records")
