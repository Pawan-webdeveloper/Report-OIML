"""Test equipment master (R 76-2 p.8)."""
from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .common import DecimalStr

EquipmentKind = Literal[
    "WEIGHT_SET", "THERMOMETER", "HYGROMETER", "BAROMETER", "CHAMBER",
    "ESD_GUN", "BURST_GEN", "SURGE_GEN", "EM_FIELD", "RF_CONDUCTED",
    "VOLTAGE_SOURCE", "TIMER", "OTHER",
]


class EquipmentCreate(BaseModel):
    kind: EquipmentKind
    name: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=128)
    serial_no: str | None = Field(default=None, max_length=128)
    accuracy_class_or_uncertainty: str | None = Field(default=None, max_length=64)
    cert_no: str | None = Field(default=None, max_length=64)
    calibrated_on: date | None = None
    valid_until: date | None = None
    weight_nominal: DecimalStr | None = None
    weight_error: DecimalStr | None = None
    weight_uncertainty: DecimalStr | None = None


class EquipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    name: str | None = None
    model: str | None = None
    serial_no: str | None = None
    accuracy_class_or_uncertainty: str | None = None
    cert_no: str | None = None
    calibrated_on: date | None = None
    valid_until: date | None = None
    weight_nominal: Decimal | None = None
    weight_error: Decimal | None = None
    weight_uncertainty: Decimal | None = None