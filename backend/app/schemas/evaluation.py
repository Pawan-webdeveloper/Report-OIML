"""Evaluations, test records (one per R 76-2 page) and workflow bodies."""
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCreate(BaseModel):
    instrument_id: UUID
    laboratory_id: UUID | None = None      # None → the single seeded laboratory
    purpose: Literal["TYPE_APPROVAL", "VERIFICATION"] = "TYPE_APPROVAL"
    mpe_context: Literal["INITIAL", "IN_SERVICE"] = "INITIAL"
    range_index: int | None = None         # MULTIPLE_RANGE instruments only
    observer_id: UUID | None = None        # the ENGINEER who will enter observations


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_no: str
    instrument_id: UUID
    laboratory_id: UUID
    range_index: int | None = None
    ruleset_id: str
    purpose: str
    mpe_context: str
    status: str
    outcome: str | None = None
    observer_id: UUID | None = None
    created_at: datetime
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    approval_hash: str | None = None


class TestRecordCreate(BaseModel):
    kind: str                              # catalogue kind, e.g. WEIGHING
    instance_no: int = Field(default=1, ge=1)
    condition_label: str | None = Field(default=None, max_length=64)
    test_date: date | None = None
    environment: dict | None = None        # {"start": {...}, "max": {...}, "end": {...}}
    observations: dict[str, Any]           # RAW — masses in the instrument's unit
    remarks: str | None = None


class TestRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_id: UUID
    kind: str
    form_no: str | None = None
    instance_no: int
    condition_label: str | None = None
    test_date: date | None = None
    environment: dict | None = None
    observations: dict
    computed: dict | None = None
    verdict: str | None = None
    warnings: list | None = None
    remarks: str | None = None


class EquipmentLinkBody(BaseModel):
    equipment_id: UUID


class ReturnBody(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)


class Message(BaseModel):
    message: str