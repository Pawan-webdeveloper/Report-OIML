"""
Attachments: photos / sketches / documents tied to an evaluation (optionally
to one test page). Files stored on disk under UPLOAD_DIR with a SHA-256
integrity hash (doc §4 attachments table; feeds the report in Phase 8).

RBAC (doc §5.1): upload — ADMIN/ENGINEER/REVIEWER; download — any role;
delete — ADMIN/ENGINEER while the evaluation is editable.
"""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Request,
                     UploadFile, status)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import get_db
from ..core.deps import get_current_user, require_roles
from ..models import Attachment, Evaluation, User
from ..schemas.evaluation import Message
from ..services.audit_service import log_action
from ..services.evaluation_service import EDITABLE_STATUSES

router = APIRouter(tags=["attachments"])
settings = get_settings()

MAX_BYTES = 10 * 1024 * 1024          # 10 MB
ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "application/pdf", "text/plain", "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
ALLOWED_KINDS = {"PHOTO", "SKETCH", "DOCUMENT", "CERTIFICATE", "RAW_DATA"}


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _eval_or_404(db: Session, evaluation_id: uuid.UUID) -> Evaluation:
    ev = db.get(Evaluation, evaluation_id)
    if ev is None:
        raise HTTPException(404, "Evaluation not found")
    return ev


@router.post("/evaluations/{evaluation_id}/attachments",
             response_model=Message, status_code=status.HTTP_201_CREATED)
async def upload_attachment(evaluation_id: uuid.UUID, request: Request,
                            file: UploadFile = File(...),
                            kind: str = Form(...),
                            caption: str | None = Form(default=None),
                            test_record_id: uuid.UUID | None = Form(default=None),
                            db: Session = Depends(get_db),
                            user: User = Depends(require_roles("ADMIN", "ENGINEER", "REVIEWER"))):
    ev = _eval_or_404(db, evaluation_id)
    if ev.status == "ARCHIVED":
        raise HTTPException(409, "Cannot attach files to an archived evaluation")
    if kind not in ALLOWED_KINDS:
        raise HTTPException(422, f"kind must be one of {sorted(ALLOWED_KINDS)}")
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(415, f"Unsupported file type: {file.content_type}")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File exceeds the 10 MB limit")
    if not data:
        raise HTTPException(422, "Empty file")

    dest_dir = Path(settings.UPLOAD_DIR) / "evaluations" / str(ev.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload.bin").suffix[:10]
    dest = dest_dir / f"{uuid.uuid4().hex}{suffix}"
    dest.write_bytes(data)

    att = Attachment(
        evaluation_id=ev.id,
        test_record_id=test_record_id,
        kind=kind,
        file_name=file.filename,
        mime=file.content_type,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        storage_path=str(dest),
        caption=caption,
        uploaded_by=user.id,
    )
    db.add(att)
    db.flush()
    log_action(db, user_id=user.id, action="ATTACHMENT_UPLOADED", entity="attachment",
               entity_id=str(att.id),
               after={"kind": kind, "sha256": att.sha256, "size": len(data)},
               ip=_ip(request))
    db.commit()
    return Message(message=f"Attachment stored (sha256={att.sha256[:12]}…)")


@router.get("/evaluations/{evaluation_id}/attachments")
def list_attachments(evaluation_id: uuid.UUID, db: Session = Depends(get_db),
                     _user: User = Depends(get_current_user)):
    ev = _eval_or_404(db, evaluation_id)
    rows = db.scalars(select(Attachment)
                      .where(Attachment.evaluation_id == ev.id)
                      .order_by(Attachment.uploaded_at)).all()
    return [{
        "id": str(a.id), "kind": a.kind, "file_name": a.file_name, "mime": a.mime,
        "size_bytes": a.size_bytes, "sha256": a.sha256, "caption": a.caption,
        "test_record_id": str(a.test_record_id) if a.test_record_id else None,
    } for a in rows]


@router.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: uuid.UUID, db: Session = Depends(get_db),
                        _user: User = Depends(get_current_user)):
    att = db.get(Attachment, attachment_id)
    if att is None or att.storage_path is None or not Path(att.storage_path).exists():
        raise HTTPException(404, "Attachment not found")
    return FileResponse(att.storage_path, media_type=att.mime or "application/octet-stream",
                        filename=att.file_name or "attachment")


@router.delete("/attachments/{attachment_id}", response_model=Message)
def delete_attachment(attachment_id: uuid.UUID, request: Request,
                      db: Session = Depends(get_db),
                      user: User = Depends(require_roles("ADMIN", "ENGINEER"))):
    att = db.get(Attachment, attachment_id)
    if att is None:
        raise HTTPException(404, "Attachment not found")
    ev = db.get(Evaluation, att.evaluation_id)
    if ev is not None and ev.status not in EDITABLE_STATUSES:
        raise HTTPException(409, f"Cannot delete attachments while the evaluation is {ev.status}")
    if att.storage_path and Path(att.storage_path).exists():
        Path(att.storage_path).unlink()
    log_action(db, user_id=user.id, action="ATTACHMENT_DELETED", entity="attachment",
               entity_id=str(att.id), ip=_ip(request))
    db.delete(att)
    db.commit()
    return Message(message="Attachment deleted")