"""Manufacturer / applicant / agent master. Write: ADMIN+ENGINEER. Read: all."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user, require_roles
from ..models import Party, User
from ..schemas.evaluation import Message
from ..schemas.instrument import PartyCreate, PartyOut, PartyUpdate
from ..services.audit_service import log_action

router = APIRouter(prefix="/parties", tags=["parties"])
_editor = require_roles("ADMIN", "ENGINEER")


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[PartyOut])
def list_parties(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.scalars(select(Party).order_by(Party.name)).all()


@router.post("", response_model=PartyOut, status_code=status.HTTP_201_CREATED)
def create_party(body: PartyCreate, request: Request, db: Session = Depends(get_db),
                 user: User = Depends(_editor)):
    party = Party(**body.model_dump())
    db.add(party)
    db.flush()
    log_action(db, user_id=user.id, action="PARTY_CREATED", entity="party",
               entity_id=str(party.id), after={"name": party.name}, ip=_ip(request))
    db.commit()
    db.refresh(party)
    return party


@router.get("/{party_id}", response_model=PartyOut)
def get_party(party_id: uuid.UUID, db: Session = Depends(get_db),
              _user: User = Depends(get_current_user)):
    party = db.get(Party, party_id)
    if party is None:
        raise HTTPException(404, "Party not found")
    return party


@router.patch("/{party_id}", response_model=PartyOut)
def update_party(party_id: uuid.UUID, body: PartyUpdate, request: Request,
                 db: Session = Depends(get_db), user: User = Depends(_editor)):
    party = db.get(Party, party_id)
    if party is None:
        raise HTTPException(404, "Party not found")
    before = {"name": party.name, "address": party.address}
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(party, field, value)
    log_action(db, user_id=user.id, action="PARTY_UPDATED", entity="party",
               entity_id=str(party.id), before=before,
               after={"name": party.name, "address": party.address}, ip=_ip(request))
    db.commit()
    db.refresh(party)
    return party