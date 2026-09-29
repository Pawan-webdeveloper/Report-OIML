"""Test equipment master (R 76-2 p.8). Create: ADMIN (doc §5.1). Read: all."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user, require_roles
from ..models import Equipment, User
from ..schemas.equipment import EquipmentCreate, EquipmentOut
from ..services.audit_service import log_action

router = APIRouter(prefix="/equipment", tags=["equipment"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[EquipmentOut])
def list_equipment(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.scalars(select(Equipment).order_by(Equipment.kind, Equipment.name)).all()


@router.post("", response_model=EquipmentOut, status_code=status.HTTP_201_CREATED)
def create_equipment(body: EquipmentCreate, request: Request,
                     db: Session = Depends(get_db),
                     user: User = Depends(require_roles("ADMIN"))):
    item = Equipment(**body.model_dump())
    db.add(item)
    db.flush()
    log_action(db, user_id=user.id, action="EQUIPMENT_CREATED", entity="equipment",
               entity_id=str(item.id), after={"name": item.name}, ip=_ip(request))
    db.commit()
    db.refresh(item)
    return item


@router.get("/{equipment_id}", response_model=EquipmentOut)
def get_equipment(equipment_id: uuid.UUID, db: Session = Depends(get_db),
                  _user: User = Depends(get_current_user)):
    item = db.get(Equipment, equipment_id)
    if item is None:
        raise HTTPException(404, "Equipment not found")
    return item