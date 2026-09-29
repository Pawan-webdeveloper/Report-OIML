"""
Instrument (model) CRUD with OIML Table 3 validation on every write, and the
freeze rule: particulars cannot change once an APPROVED report uses them
(doc §4 data-layer rules — create a new revision instead).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user, require_roles
from ..models import Evaluation, Instrument, InstrumentRange, User
from ..schemas.instrument import InstrumentCreate, InstrumentOut, InstrumentUpdate
from ..services.audit_service import log_action
from ..services.evaluation_service import validate_new_instrument

router = APIRouter(prefix="/instruments", tags=["instruments"])
_editor = require_roles("ADMIN", "ENGINEER")


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _get_or_404(db: Session, instrument_id: uuid.UUID) -> Instrument:
    inst = db.get(Instrument, instrument_id)
    if inst is None:
        raise HTTPException(404, "Instrument not found")
    return inst


def _assert_not_frozen(db: Session, instrument_id: uuid.UUID) -> None:
    approved = db.scalar(
        select(func.count()).select_from(Evaluation)
        .where(Evaluation.instrument_id == instrument_id,
               Evaluation.status == "APPROVED"))
    if approved:
        raise HTTPException(409, "Instrument particulars are frozen: an APPROVED "
                                 "report uses this model. Create a new revision instead.")


@router.get("", response_model=list[InstrumentOut])
def list_instruments(q: str | None = None, db: Session = Depends(get_db),
                     _user: User = Depends(get_current_user)):
    stmt = select(Instrument).order_by(Instrument.created_at.desc())
    if q:
        stmt = stmt.where(Instrument.type_designation.ilike(f"%{q}%"))
    return db.scalars(stmt).all()


@router.post("", response_model=InstrumentOut, status_code=status.HTTP_201_CREATED)
def create_instrument(body: InstrumentCreate, request: Request,
                      db: Session = Depends(get_db), user: User = Depends(_editor)):
    inst = Instrument(**body.model_dump(exclude={"ranges"}), created_by=user.id)
    db.add(inst)
    db.flush()
    for i, r in enumerate(body.ranges, start=1):          # idx assigned by order
        db.add(InstrumentRange(instrument_id=inst.id, idx=i,
                               e=r.e, d=r.d, max_capacity=r.max))
    db.flush()
    validate_new_instrument(inst)                          # 400 on Table 3 violations

    log_action(db, user_id=user.id, action="INSTRUMENT_CREATED", entity="instrument",
               entity_id=str(inst.id),
               after={"type_designation": inst.type_designation}, ip=_ip(request))
    db.commit()
    db.refresh(inst)
    return inst


@router.get("/{instrument_id}", response_model=InstrumentOut)
def get_instrument(instrument_id: uuid.UUID, db: Session = Depends(get_db),
                   _user: User = Depends(get_current_user)):
    return _get_or_404(db, instrument_id)


@router.patch("/{instrument_id}", response_model=InstrumentOut)
def update_instrument(instrument_id: uuid.UUID, body: InstrumentUpdate,
                      request: Request, db: Session = Depends(get_db),
                      user: User = Depends(_editor)):
    inst = _get_or_404(db, instrument_id)
    _assert_not_frozen(db, inst.id)

    data = body.model_dump(exclude_unset=True, exclude={"ranges"})
    for field, value in data.items():
        setattr(inst, field, value)

    if body.ranges is not None:                            # full replacement
        inst.ranges.clear()                                # delete-orphan removes old rows
        db.flush()                                         # delete before re-insert (unique idx)
        for i, r in enumerate(body.ranges, start=1):
            inst.ranges.append(InstrumentRange(idx=i, e=r.e, d=r.d,
                                               max_capacity=r.max))
        db.flush()

    validate_new_instrument(inst)

    log_action(db, user_id=user.id, action="INSTRUMENT_UPDATED", entity="instrument",
               entity_id=str(inst.id), ip=_ip(request))
    db.commit()
    db.refresh(inst)
    return inst