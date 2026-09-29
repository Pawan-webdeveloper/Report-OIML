"""
Report endpoints: model JSON, print-ready HTML, and versioned PDF/DOCX exports.

RBAC (doc §5.1): export — ADMIN/ENGINEER/REVIEWER anytime, VIEWER only once the
evaluation is APPROVED/ARCHIVED. Every export is stored in report_exports with
version + SHA-256 of the file bytes.
"""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import get_db
from ..core.deps import get_current_user
from ..models import Evaluation, ReportExport, User
from ..reporting.docx import build_docx
from ..reporting.pdf import render_pdf
from ..reporting.render import render_html
from ..reporting.report_model import build_report_model
from ..services.audit_service import log_action

router = APIRouter(prefix="/evaluations/{evaluation_id}/report", tags=["reports"])
settings = get_settings()


def _ev_or_404(db: Session, evaluation_id: uuid.UUID) -> Evaluation:
    ev = db.get(Evaluation, evaluation_id)
    if ev is None:
        raise HTTPException(404, "Evaluation not found")
    return ev


def _can_export(user: User, ev: Evaluation) -> bool:
    if user.role in ("ADMIN", "ENGINEER", "REVIEWER"):
        return True
    return user.role == "VIEWER" and ev.status in ("APPROVED", "ARCHIVED")


@router.get("")
def get_report(evaluation_id: uuid.UUID, db: Session = Depends(get_db),
               _user: User = Depends(get_current_user)):
    """Full report model as JSON (used for previews and future renderers)."""
    return build_report_model(db, _ev_or_404(db, evaluation_id))


@router.get("/print", response_class=HTMLResponse)
def print_report(evaluation_id: uuid.UUID, db: Session = Depends(get_db),
                 _user: User = Depends(get_current_user)):
    """Print-ready R 76-2 HTML — open in a tab, use the toolbar or Ctrl+P."""
    ev = _ev_or_404(db, evaluation_id)
    return HTMLResponse(render_html(build_report_model(db, ev)))


class ExportRequest(BaseModel):
    format: Literal["PDF", "DOCX"]


@router.post("/export")
def export_report(evaluation_id: uuid.UUID, body: ExportRequest, request: Request,
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = _ev_or_404(db, evaluation_id)
    if not _can_export(user, ev):
        raise HTTPException(403, "Export is allowed for ADMIN/ENGINEER/REVIEWER; "
                                 "VIEWER may export approved reports only")

    model = build_report_model(db, ev)
    html = render_html(model)

    if body.format == "PDF":
        data = render_pdf(html)
        if data is None:
            raise HTTPException(
                503,
                "PDF engine (WeasyPrint) is not installed on the server. "
                "Use Preview → 'Print / Save as PDF', or install WeasyPrint "
                "in the deployment container.",
            )
        mime = "application/pdf"
        ext = "pdf"
    else:
        data = build_docx(model)
        mime = ("application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document")
        ext = "docx"

    current = db.scalar(select(func.max(ReportExport.version))
                        .where(ReportExport.evaluation_id == ev.id,
                               ReportExport.format == body.format))
    version = (current or 0) + 1

    dest_dir = Path(settings.UPLOAD_DIR) / "reports" / str(ev.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"report_{ev.report_no.replace('/', '-')}_{body.format.lower()}_v{version}.{ext}"
    dest.write_bytes(data)

    row = ReportExport(
        evaluation_id=ev.id, format=body.format, version=version,
        storage_path=str(dest), sha256=hashlib.sha256(data).hexdigest(),
        created_by=user.id,
    )
    db.add(row)
    log_action(db, user_id=user.id, action="REPORT_EXPORTED", entity="evaluation",
               entity_id=str(ev.id),
               after={"format": body.format, "version": version,
                      "sha256": row.sha256[:16]},
               ip=request.client.host if request.client else None)
    db.commit()
    db.refresh(row)

    return {"id": str(row.id), "format": row.format, "version": row.version,
            "sha256": row.sha256, "size_bytes": len(data),
            "download_url": f"/api/evaluations/{ev.id}/report/exports/{row.id}/download"}


@router.get("/exports")
def list_exports(evaluation_id: uuid.UUID, db: Session = Depends(get_db),
                 _user: User = Depends(get_current_user)):
    ev = _ev_or_404(db, evaluation_id)
    rows = db.scalars(select(ReportExport)
                      .where(ReportExport.evaluation_id == ev.id)
                      .order_by(ReportExport.created_at.desc())).all()
    return [{"id": str(r.id), "format": r.format, "version": r.version,
             "sha256": r.sha256, "signed": r.signed,
             "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/exports/{export_id}/download")
def download_export(evaluation_id: uuid.UUID, export_id: uuid.UUID,
                    db: Session = Depends(get_db),
                    _user: User = Depends(get_current_user)):
    _ev_or_404(db, evaluation_id)
    row = db.get(ReportExport, export_id)
    if row is None or row.evaluation_id != evaluation_id or not row.storage_path \
            or not Path(row.storage_path).exists():
        raise HTTPException(404, "Export not found")
    safe_no = _safe_report_no(db, evaluation_id)
    filename = f"{safe_no}_{row.format.lower()}_v{row.version}.{row.format.lower()}"
    return FileResponse(row.storage_path, media_type=(
        "application/pdf" if row.format == "PDF" else
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        filename=filename)


def _safe_report_no(db: Session, evaluation_id: uuid.UUID) -> str:
    ev = db.get(Evaluation, evaluation_id)
    return (ev.report_no if ev else "report").replace("/", "-")