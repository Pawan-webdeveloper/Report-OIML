"""
Workflow state machine (doc §5.2) and the server-side submission gate.

    DRAFT → IN_PROGRESS → SUBMITTED → UNDER_REVIEW → APPROVED
                                            └→ RETURNED → IN_PROGRESS
    APPROVED → ARCHIVED

Submission gate (doc §5.2): every required test has a final verdict
(PASSED/FAILED/NOT_APPLICABLE), no ERROR-level validation warnings remain,
and test equipment has been recorded. `outcome` = FAIL if any required test
failed, else PASS (INCOMPLETE is impossible after the gate).

Approval stores approval_hash = SHA-256 over the canonical JSON of every
page's (kind, instance_no, observations, verdict) — reproducibility proof.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Evaluation, Review, TestRecord, User
from .audit_service import log_action
from .evaluation_service import outcome_preview


def _now():
    return datetime.now(timezone.utc)


def _ip_or_none(ip: str | None):
    return ip


# ------------------------------------------------------------------- submit
def submit_evaluation(db: Session, ev: Evaluation, user: User, ip: str | None) -> Evaluation:
    if ev.status not in ("DRAFT", "IN_PROGRESS"):
        raise HTTPException(409, f"Cannot submit from status {ev.status} "
                                 f"(expected DRAFT or IN_PROGRESS)")

    preview = outcome_preview(db, ev)
    required, verdicts = preview["required"], preview["verdicts"]

    missing = [k for k in required if k not in verdicts]
    pending = [k for k in required if verdicts.get(k) == "PENDING"]
    if missing or pending:
        raise HTTPException(400, detail={
            "message": "Submission gate: required tests are missing or still pending",
            "missing": missing, "pending": pending,
        })

    blocked = []
    for rec in ev.test_records:
        for w in (rec.warnings or []):
            if isinstance(w, dict) and w.get("severity") == "ERROR":
                blocked.append({"kind": rec.kind, "code": w.get("code"),
                                "message": w.get("message")})
    if blocked:
        raise HTTPException(400, detail={
            "message": "Submission gate: resolve ERROR-level validation issues first",
            "issues": blocked,
        })

    if not ev.equipment_links:
        raise HTTPException(400, "Submission gate: record the test equipment used "
                                 "(R 76-2 p.8 traceability) before submitting")

    ev.status = "SUBMITTED"
    ev.submitted_at = _now()
    ev.outcome = preview["outcome"]          # PASS or FAIL at this point

    log_action(db, user_id=user.id, action="EVALUATION_SUBMITTED", entity="evaluation",
               entity_id=str(ev.id), after={"status": ev.status, "outcome": ev.outcome},
               ip=ip)
    db.commit()
    db.refresh(ev)
    return ev


# -------------------------------------------------------------- review steps
def start_review(db: Session, ev: Evaluation, user: User, ip: str | None) -> Evaluation:
    if ev.status != "SUBMITTED":
        raise HTTPException(409, f"Cannot start review from status {ev.status}")
    ev.status = "UNDER_REVIEW"
    log_action(db, user_id=user.id, action="REVIEW_STARTED", entity="evaluation",
               entity_id=str(ev.id), ip=ip)
    db.commit()
    db.refresh(ev)
    return ev


def return_evaluation(db: Session, ev: Evaluation, user: User, comment: str,
                      ip: str | None) -> Evaluation:
    if ev.status != "UNDER_REVIEW":
        raise HTTPException(409, f"Cannot return from status {ev.status}")
    ev.status = "RETURNED"
    db.add(Review(evaluation_id=ev.id, reviewer_id=user.id,
                  decision="RETURNED", comment=comment))
    log_action(db, user_id=user.id, action="EVALUATION_RETURNED", entity="evaluation",
               entity_id=str(ev.id), after={"comment": comment}, ip=ip)
    db.commit()
    db.refresh(ev)
    return ev


def reopen_evaluation(db: Session, ev: Evaluation, user: User, ip: str | None) -> Evaluation:
    if ev.status != "RETURNED":
        raise HTTPException(409, f"Cannot reopen from status {ev.status}")
    ev.status = "IN_PROGRESS"
    log_action(db, user_id=user.id, action="EVALUATION_REOPENED", entity="evaluation",
               entity_id=str(ev.id), ip=ip)
    db.commit()
    db.refresh(ev)
    return ev


# ------------------------------------------------------------------ approve
def _canonical_hash(db: Session, ev: Evaluation) -> str:
    pages = [
        {"kind": r.kind, "instance_no": r.instance_no,
         "observations": r.observations, "verdict": r.verdict}
        for r in sorted(ev.test_records, key=lambda x: (x.kind, x.instance_no))
    ]
    payload = json.dumps(pages, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def approve_evaluation(db: Session, ev: Evaluation, reviewer: User,
                       ip: str | None) -> Evaluation:
    if ev.status != "UNDER_REVIEW":
        raise HTTPException(409, f"Cannot approve from status {ev.status}")

    # Separation of duties (doc §5.1): approver ≠ observer (or creator if unassigned)
    responsible = ev.observer_id or ev.created_by
    if responsible is not None and responsible == reviewer.id:
        raise HTTPException(403, "Separation of duties: the approver cannot be the "
                                 "same person as the observer")

    ev.status = "APPROVED"
    ev.approved_by = reviewer.id
    ev.approved_at = _now()
    ev.approval_hash = _canonical_hash(db, ev)
    db.add(Review(evaluation_id=ev.id, reviewer_id=reviewer.id, decision="APPROVED"))
    log_action(db, user_id=reviewer.id, action="EVALUATION_APPROVED", entity="evaluation",
               entity_id=str(ev.id), after={"outcome": ev.outcome,
                                            "approval_hash": ev.approval_hash}, ip=ip)
    db.commit()
    db.refresh(ev)
    return ev


def archive_evaluation(db: Session, ev: Evaluation, user: User, ip: str | None) -> Evaluation:
    if ev.status != "APPROVED":
        raise HTTPException(409, f"Cannot archive from status {ev.status}")
    ev.status = "ARCHIVED"
    log_action(db, user_id=user.id, action="EVALUATION_ARCHIVED", entity="evaluation",
               entity_id=str(ev.id), ip=ip)
    db.commit()
    db.refresh(ev)
    return ev