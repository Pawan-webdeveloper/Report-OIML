"""Parties + Instruments + ranges (R 76-2 'General information concerning the type')."""
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .common import DecimalStr

AccuracyClass = Literal["I", "II", "III", "IIII"]
Unit = Literal["kg", "g", "mg", "t", "ct"]


# ------------------------------------------------------------------ parties
class PartyCreate(BaseModel):
    kind: Literal["MANUFACTURER", "APPLICANT", "AGENT"] = "MANUFACTURER"
    name: str = Field(min_length=1, max_length=255)
    address: str | None = None
    gstin: str | None = Field(default=None, max_length=32)
    contact: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=255)


class PartyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = None
    gstin: str | None = None
    contact: str | None = None
    email: str | None = None


class PartyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    name: str
    address: str | None = None
    gstin: str | None = None
    contact: str | None = None
    email: str | None = None


# --------------------------------------------------------------- instruments
class RangeIn(BaseModel):
    """One weighing range. `max` shadows the builtin inside this schema only."""
    e: DecimalStr
    d: DecimalStr
    max: DecimalStr


class RangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idx: int
    e: Decimal
    d: Decimal
    max_capacity: Decimal          # DB column is `max`; ORM attr is max_capacity


class InstrumentCreate(BaseModel):
    application_no: str | None = Field(default=None, max_length=64)
    type_designation: str = Field(min_length=1, max_length=128)
    manufacturer_id: UUID | None = None
    applicant_id: UUID | None = None
    category: str | None = Field(default=None, max_length=128)

    accuracy_class: AccuracyClass
    indication_type: Literal["SELF", "SEMI_SELF", "NON_SELF"] = "SELF"
    display_kind: Literal["DIGITAL", "ANALOG"] | None = "DIGITAL"
    range_kind: Literal["SINGLE", "MULTI_INTERVAL", "MULTIPLE_RANGE"] = "SINGLE"

    min_capacity: DecimalStr
    unit: Unit = "kg"
    tare_plus: DecimalStr = "0"
    tare_minus: DecimalStr = "0"
    max_safe_load: DecimalStr | None = None

    temp_min_c: DecimalStr = "-10"
    temp_max_c: DecimalStr = "40"
    power_supply_category: list[str] = Field(default_factory=list)
    zero_devices: dict | None = None
    tare_devices: dict | None = None
    printer: Literal["BUILT_IN", "CONNECTED",
                     "NOT_PRESENT_CONNECTABLE", "NO_CONNECTION"] | None = None
    direct_sales_to_public: bool = False
    level_indicator: bool | None = None
    software_version: str | None = None
    submitted_identification_no: str | None = None
    remarks: str | None = None

    ranges: list[RangeIn] = Field(min_length=1)


class InstrumentUpdate(BaseModel):
    type_designation: str | None = Field(default=None, min_length=1, max_length=128)
    category: str | None = None
    remarks: str | None = None
    temp_min_c: DecimalStr | None = None
    temp_max_c: DecimalStr | None = None
    ranges: list[RangeIn] | None = None       # if given, full replacement


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_no: str | None = None
    type_designation: str
    manufacturer_id: UUID | None = None
    applicant_id: UUID | None = None
    category: str | None = None
    accuracy_class: str
    indication_type: str
    display_kind: str | None = None
    range_kind: str
    min_capacity: Decimal
    unit: str
    tare_plus: Decimal | None = None
    tare_minus: Decimal | None = None
    temp_min_c: Decimal | None = None
    temp_max_c: Decimal | None = None
    power_supply_category: list[str] | None = None
    zero_devices: dict | None = None
    tare_devices: dict | None = None
    printer: str | None = None
    direct_sales_to_public: bool = False
    remarks: str | None = None
    created_at: datetime
    ranges: list[RangeOut] = Field(default_factory=list)