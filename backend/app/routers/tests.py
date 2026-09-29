"""
Test-record endpoints: save one R 76-2 page (observations in → engine →
computed/verdict/warnings persisted) and list the pages of an evaluation.

RBAC (doc §5.1): observations are entered by the assigned ENGINEER only;
read access for all authenticated roles.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user, require_roles
from ..models import Evaluation, TestRecord, User
from ..schemas.evaluation import TestRecordCreate, TestRecordOut
from ..services.audit_service import log_action
from ..services.evaluation_service import can_enter_observations, save_test_record

router = APIRouter(prefix="/evaluations/{evaluation_id}/tests", tags=["test-records"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _eval_or_404(db: Session, evaluation_id: uuid.UUID) -> Evaluation:
    ev = db.get(Evaluation, evaluation_id)
    if ev is None:
        raise HTTPException(404, "Evaluation not found")
    return ev


@router.get("", response_model=list[TestRecordOut])
def list_test_records(evaluation_id: uuid.UUID, db: Session = Depends(get_db),
                      _user: User = Depends(get_current_user)):
    ev = _eval_or_404(db, evaluation_id)
    return db.scalars(
        select(TestRecord)
        .where(TestRecord.evaluation_id == ev.id)
        .order_by(TestRecord.kind, TestRecord.instance_no)
    ).all()


@router.post("", response_model=TestRecordOut, status_code=status.HTTP_201_CREATED)
def save_test(evaluation_id: uuid.UUID, body: TestRecordCreate, request: Request,
              db: Session = Depends(get_db),
              user: User = Depends(require_roles("ENGINEER"))):
    ev = _eval_or_404(db, evaluation_id)
    if not can_enter_observations(user, ev):
        raise HTTPException(403, "Only the assigned engineer may enter observations "
                                 "for this evaluation")

    row = save_test_record(
        db, ev, user,
        kind=body.kind, instance_no=body.instance_no,
        observations=body.observations, condition_label=body.condition_label,
        test_date=body.test_date, environment=body.environment, remarks=body.remarks,
    )
    log_action(db, user_id=user.id, action="TEST_RECORD_SAVED", entity="test_record",
               entity_id=str(row.id),
               after={"kind": row.kind, "instance_no": row.instance_no,
                      "verdict": row.verdict}, ip=_ip(request))
    db.commit()
    db.refresh(row)
    return row