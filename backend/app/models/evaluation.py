import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base
from ._types import ExactNumeric, JSONType, UUIDType


class Evaluation(Base):
    """Doc §4 — one test campaign = one Type Evaluation Report."""
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint("purpose IN ('TYPE_APPROVAL','VERIFICATION')", name="ck_eval_purpose"),
        CheckConstraint("mpe_context IN ('INITIAL','IN_SERVICE')", name="ck_eval_ctx"),
        CheckConstraint("status IN ('DRAFT','IN_PROGRESS','SUBMITTED','UNDER_REVIEW',"
                        "'RETURNED','APPROVED','ARCHIVED')", name="ck_eval_status"),
        CheckConstraint("outcome IN ('PASS','FAIL','INCOMPLETE')", name="ck_eval_outcome"),
        CheckConstraint("auto_zero_status IN ('NON_EXISTENT','NOT_IN_OPERATION',"
                        "'OUT_OF_WORKING_RANGE','IN_OPERATION')", name="ck_eval_azs"),
        Index("ix_evaluations_status_outcome", "status", "outcome"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    report_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("instruments.id"), nullable=False)
    laboratory_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("laboratories.id"), nullable=False)
    range_index: Mapped[int | None] = mapped_column(Integer)   # for MULTIPLE_RANGE

    ruleset_id: Mapped[str] = mapped_column(String(64), nullable=False,
                                            default="oiml-r76-2006")
    ruleset_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    purpose: Mapped[str] = mapped_column(String(16), nullable=False, default="TYPE_APPROVAL")
    mpe_context: Mapped[str] = mapped_column(String(16), nullable=False, default="INITIAL")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    outcome: Mapped[str | None] = mapped_column(String(16))

    evaluation_period_from: Mapped[date | None] = mapped_column(Date)
    evaluation_period_to: Mapped[date | None] = mapped_column(Date)
    observer_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    resolution_during_test: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    auto_zero_status: Mapped[str | None] = mapped_column(String(24))
    initial_zero_gt_20pct: Mapped[bool | None] = mapped_column(Boolean)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_hash: Mapped[str | None] = mapped_column(String(64))

    instrument: Mapped["Instrument"] = relationship()
    laboratory: Mapped["Laboratory"] = relationship()
    test_records: Mapped[list["TestRecord"]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan",
        order_by="TestRecord.instance_no")
    equipment_links: Mapped[list["EvaluationEquipment"]] = relationship(
        cascade="all, delete-orphan")


class Equipment(Base):
    """Doc §4 — test equipment (R 76-2 p.8) — with traceability."""
    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint("kind IN ('WEIGHT_SET','THERMOMETER','HYGROMETER','BAROMETER',"
                        "'CHAMBER','ESD_GUN','BURST_GEN','SURGE_GEN','EM_FIELD',"
                        "'RF_CONDUCTED','VOLTAGE_SOURCE','TIMER','OTHER')",
                        name="ck_equipment_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    model: Mapped[str | None] = mapped_column(String(128))
    serial_no: Mapped[str | None] = mapped_column(String(128))
    accuracy_class_or_uncertainty: Mapped[str | None] = mapped_column(String(64))  # 'M1', 'U=0.5 mg'
    cert_no: Mapped[str | None] = mapped_column(String(64))
    calibrated_on: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    # Weights (the 1/3-MPE check of 3.7.1 will use these in Phase 3)
    weight_nominal: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    weight_error: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    weight_uncertainty: Mapped[Decimal | None] = mapped_column(ExactNumeric)


class EvaluationEquipment(Base):
    """Doc §4 — association: evaluation ↔ equipment."""
    __tablename__ = "evaluation_equipment"

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("evaluations.id", ondelete="CASCADE"), primary_key=True)
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True)

    equipment: Mapped["Equipment"] = relationship()


class ChecklistResult(Base):
    """Doc §4 — R 76-2 test 17 checklist (item-wise)."""
    __tablename__ = "checklist_results"
    __table_args__ = (
        CheckConstraint("state IN ('PASSED','FAILED','NOT_APPLICABLE')", name="ck_cl_state"),
        CheckConstraint("device_state IN ('EXISTENT','NON_EXISTENT')", name="ck_cl_device"),
    )

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("evaluations.id", ondelete="CASCADE"), primary_key=True)
    item_code: Mapped[str] = mapped_column(String(16), primary_key=True)  # '7.1.1', '4.5.2'
    state: Mapped[str | None] = mapped_column(String(16))
    device_state: Mapped[str | None] = mapped_column(String(16))
    remarks: Mapped[str | None] = mapped_column(Text)