"""
Evaluation lifecycle endpoints (one evaluation = one Type Evaluation Report):
create with auto report number, list/detail, required-tests preview,
equipment linking, and all workflow transitions.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user, require_roles
from ..engine.ruleset import load_ruleset
from ..models import Equipment, Evaluation, EvaluationEquipment, Instrument, Laboratory, User
from ..schemas.evaluation import (EquipmentLinkBody, EvaluationCreate, EvaluationOut,
                                  Message, ReturnBody)
from ..schemas.equipment import EquipmentOut
from ..services import workflow_service
from ..services.audit_service import log_action
from ..services.evaluation_service import next_report_no, outcome_preview

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _get_or_404(db: Session, evaluation_id: uuid.UUID) -> Evaluation:
    ev = db.get(Evaluation, evaluation_id)
    if ev is None:
        raise HTTPException(404, "Evaluation not found")
    return ev


@router.get("", response_model=list[EvaluationOut])
def list_evaluations(status_filter: str | None = None,
                     instrument_id: uuid.UUID | None = None,
                     db: Session = Depends(get_db),
                     _user: User = Depends(get_current_user)):
    stmt = select(Evaluation).order_by(Evaluation.created_at.desc())
    if status_filter:
        stmt = stmt.where(Evaluation.status == status_filter.upper())
    if instrument_id:
        stmt = stmt.where(Evaluation.instrument_id == instrument_id)
    return db.scalars(stmt).all()


@router.post("", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
def create_evaluation(body: EvaluationCreate, request: Request,
                      db: Session = Depends(get_db),
                      user: User = Depends(require_roles("ADMIN", "ENGINEER"))):
    inst = db.get(Instrument, body.instrument_id)
    if inst is None:
        raise HTTPException(404, "Instrument not found")

    if body.laboratory_id is not None:
        lab = db.get(Laboratory, body.laboratory_id)
        if lab is None:
            raise HTTPException(404, "Laboratory not found")
    else:
        lab = db.scalar(select(Laboratory).limit(1))
        if lab is None:
            raise HTTPException(400, "No laboratory exists — create one first")

    ev = Evaluation(
        report_no=next_report_no(db),
        instrument_id=body.instrument_id,
        laboratory_id=lab.id,
        range_index=body.range_index,
        ruleset_id="oiml-r76-2006",
        ruleset_sha256=load_ruleset()["_sha256"],
        purpose=body.purpose,
        mpe_context=body.mpe_context,
        observer_id=body.observer_id,
        created_by=user.id,
    )
    db.add(ev)
    db.flush()
    log_action(db, user_id=user.id, action="EVALUATION_CREATED", entity="evaluation",
               entity_id=str(ev.id), after={"report_no": ev.report_no}, ip=_ip(request))
    db.commit()
    db.refresh(ev)
    return ev


@router.get("/{evaluation_id}", response_model=EvaluationOut)
def get_evaluation(evaluation_id: uuid.UUID, db: Session = Depends(get_db),
                   _user: User = Depends(get_current_user)):
    return _get_or_404(db, evaluation_id)


@router.get("/{evaluation_id}/required-tests")
def required_tests(evaluation_id: uuid.UUID, db: Session = Depends(get_db),
                   _user: User = Depends(get_current_user)):
    """Live preview for the UI: required kinds, current verdicts, overall outcome."""
    ev = _get_or_404(db, evaluation_id)
    return outcome_preview(db, ev)


@router.post("/{evaluation_id}/equipment", response_model=Message)
def link_equipment(evaluation_id: uuid.UUID, body: EquipmentLinkBody,
                   request: Request, db: Session = Depends(get_db),
                   user: User = Depends(require_roles("ADMIN", "ENGINEER"))):
    ev = _get_or_404(db, evaluation_id)
    if ev.status not in ("DRAFT", "IN_PROGRESS", "RETURNED"):
        raise HTTPException(409, "Equipment can only be linked while the evaluation is editable")
    item = db.get(Equipment, body.equipment_id)
    if item is None:
        raise HTTPException(404, "Equipment not found")
    exists = db.get(EvaluationEquipment, (ev.id, item.id))
    if exists is None:
        db.add(EvaluationEquipment(evaluation_id=ev.id, equipment_id=item.id))
        log_action(db, user_id=user.id, action="EQUIPMENT_LINKED", entity="evaluation",
                   entity_id=str(ev.id), after={"equipment": str(item.id)}, ip=_ip(request))
        db.commit()
    return Message(message="Equipment linked")


@router.get("/{evaluation_id}/equipment", response_model=list[EquipmentOut])
def list_linked_equipment(evaluation_id: uuid.UUID, db: Session = Depends(get_db),
                          _user: User = Depends(get_current_user)):
    """Equipment linked to this evaluation (used by the workspace UI)."""
    ev = _get_or_404(db, evaluation_id)
    rows = db.scalars(
        select(Equipment)
        .join(EvaluationEquipment, EvaluationEquipment.equipment_id == Equipment.id)
        .where(EvaluationEquipment.evaluation_id == ev.id)
        .order_by(Equipment.kind, Equipment.name)
    ).all()
    return rows


# ------------------------------------------------------------------ workflow
@router.post("/{evaluation_id}/submit", response_model=EvaluationOut)
def submit(evaluation_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
           user: User = Depends(require_roles("ENGINEER"))):
    ev = _get_or_404(db, evaluation_id)
    return workflow_service.submit_evaluation(db, ev, user, _ip(request))


@router.post("/{evaluation_id}/start-review", response_model=EvaluationOut)
def start_review(evaluation_id: uuid.UUID, request: Request,
                 db: Session = Depends(get_db),
                 user: User = Depends(require_roles("REVIEWER"))):
    ev = _get_or_404(db, evaluation_id)
    return workflow_service.start_review(db, ev, user, _ip(request))


@router.post("/{evaluation_id}/return", response_model=EvaluationOut)
def return_evaluation(evaluation_id: uuid.UUID, body: ReturnBody, request: Request,
                      db: Session = Depends(get_db),
                      user: User = Depends(require_roles("REVIEWER"))):
    ev = _get_or_404(db, evaluation_id)
    return workflow_service.return_evaluation(db, ev, user, body.comment, _ip(request))


@router.post("/{evaluation_id}/approve", response_model=EvaluationOut)
def approve(evaluation_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
            user: User = Depends(require_roles("REVIEWER"))):
    ev = _get_or_404(db, evaluation_id)
    return workflow_service.approve_evaluation(db, ev, user, _ip(request))


@router.post("/{evaluation_id}/reopen", response_model=EvaluationOut)
def reopen(evaluation_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
           user: User = Depends(require_roles("ENGINEER"))):
    ev = _get_or_404(db, evaluation_id)
    return workflow_service.reopen_evaluation(db, ev, user, _ip(request))


@router.post("/{evaluation_id}/archive", response_model=EvaluationOut)
def archive(evaluation_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
            user: User = Depends(require_roles("ADMIN"))):
    ev = _get_or_404(db, evaluation_id)
    return workflow_service.archive_evaluation(db, ev, user, _ip(request))