import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String,
    Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base
from ._types import ExactNumeric, JSONType, UUIDType


class Instrument(Base):
    """
    Doc §4 — instruments. R 76-2 p.6 'General information concerning the type'.
    NUMERIC columns are ExactNumeric (Decimal discipline).
    """
    __tablename__ = "instruments"
    __table_args__ = (
        CheckConstraint("accuracy_class IN ('I','II','III','IIII')", name="ck_instruments_class"),
        CheckConstraint("indication_type IN ('SELF','SEMI_SELF','NON_SELF')", name="ck_instruments_ind"),
        CheckConstraint("range_kind IN ('SINGLE','MULTI_INTERVAL','MULTIPLE_RANGE')", name="ck_instruments_rk"),
        CheckConstraint("printer IN ('BUILT_IN','CONNECTED','NOT_PRESENT_CONNECTABLE','NO_CONNECTION')",
                        name="ck_instruments_printer"),
        Index("ix_instruments_type_designation", "type_designation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    application_no: Mapped[str | None] = mapped_column(String(64))
    type_designation: Mapped[str] = mapped_column(String(128), nullable=False)

    manufacturer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("parties.id"))
    applicant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("parties.id"))

    category: Mapped[str | None] = mapped_column(String(128))       # platform/weighbridge/retail
    is_module: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    module_error_fraction_pi: Mapped[Decimal | None] = mapped_column(ExactNumeric)

    accuracy_class: Mapped[str] = mapped_column(String(8), nullable=False)
    indication_type: Mapped[str] = mapped_column(String(16), nullable=False, default="SELF")
    display_kind: Mapped[str | None] = mapped_column(String(16))    # DIGITAL | ANALOG
    range_kind: Mapped[str] = mapped_column(String(24), nullable=False, default="SINGLE")

    min_capacity: Mapped[Decimal] = mapped_column(ExactNumeric, nullable=False)   # Min
    unit: Mapped[str] = mapped_column(String(4), nullable=False, default="kg")    # kg/g/mg/t/ct
    tare_plus: Mapped[Decimal] = mapped_column(ExactNumeric, default=Decimal("0"))   # T = +
    tare_minus: Mapped[Decimal] = mapped_column(ExactNumeric, default=Decimal("0"))  # T = -
    max_safe_load: Mapped[Decimal | None] = mapped_column(ExactNumeric)              # Lim

    # Power supply (R 76-2 p.7)
    u_nom: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    u_min: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    u_max: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    frequency_hz: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    battery_u_nom: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    power_supply_category: Mapped[list[str]] = mapped_column(JSONType, default=list)

    # Zero / tare devices (R 76-2 p.7 checkboxes)
    zero_devices: Mapped[dict | None] = mapped_column(JSONType)
    initial_zero_range_pct: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    zero_setting_range_pct: Mapped[Decimal | None] = mapped_column(ExactNumeric)
    tare_devices: Mapped[dict | None] = mapped_column(JSONType)

    # Environment (3.9.2): default -10..+40 C
    temp_min_c: Mapped[Decimal] = mapped_column(ExactNumeric, default=Decimal("-10"))
    temp_max_c: Mapped[Decimal] = mapped_column(ExactNumeric, default=Decimal("40"))
    temp_range_is_special: Mapped[bool] = mapped_column(Boolean, default=False)

    # Tilting (3.9.1)
    direct_sales_to_public: Mapped[bool] = mapped_column(Boolean, default=False)
    level_indicator: Mapped[bool | None] = mapped_column(Boolean)
    auto_tilt_sensor: Mapped[bool | None] = mapped_column(Boolean)
    limiting_tilt: Mapped[Decimal | None] = mapped_column(ExactNumeric)

    printer: Mapped[str | None] = mapped_column(String(32))
    software_version: Mapped[str | None] = mapped_column(String(64))
    software_checksum: Mapped[str | None] = mapped_column(String(128))

    # Modules (Annex C-F)
    load_cell: Mapped[dict | None] = mapped_column(JSONType)
    interfaces: Mapped[dict | None] = mapped_column(JSONType)
    connected_equipment: Mapped[dict | None] = mapped_column(JSONType)

    submitted_identification_no: Mapped[str | None] = mapped_column(String(128))
    remarks: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    ranges: Mapped[list["InstrumentRange"]] = relationship(
        back_populates="instrument", cascade="all, delete-orphan",
        order_by="InstrumentRange.idx",
    )


class InstrumentRange(Base):
    """Doc §4 — one row per weighing range (R 76-2: e1, Max1, d1, n1...)."""

    __tablename__ = "instrument_ranges"
    __table_args__ = (
        UniqueConstraint("instrument_id", "idx", name="uq_instrument_ranges"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)          # 1, 2, 3
    e: Mapped[Decimal] = mapped_column(ExactNumeric, nullable=False)
    d: Mapped[Decimal] = mapped_column(ExactNumeric, nullable=False)
    # DB column is 'max' per doc, Python attr is 'max_capacity'
    max_capacity: Mapped[Decimal] = mapped_column("max", ExactNumeric, nullable=False)

    instrument: Mapped[Instrument] = relationship(back_populates="ranges")