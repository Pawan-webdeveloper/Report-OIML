"""
Dashboard analytics (any authenticated role):
- totals (evaluations / instruments / users / test pages)
- status & outcome counts
- 6-month creation trend (bucketed in Python → SQLite/PG portable)
- failure analysis: FAILED verdicts grouped by test kind
"""
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models import Evaluation, Instrument, TestRecord, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis")
def kpis(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    evaluations = db.scalars(select(Evaluation)).all()

    status_counts = Counter(e.status for e in evaluations)
    outcome_counts = Counter(e.outcome or "NOT_SET" for e in evaluations)

    # last 6 month labels (including empty months, for a stable chart axis)
    now = datetime.now(timezone.utc)
    y, m = now.year, now.month
    months: list[str] = []
    for _ in range(6):
        months.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    months.reverse()

    trend_counter = Counter(
        e.created_at.strftime("%Y-%m") for e in evaluations if e.created_at
    )
    trend = [{"month": mth, "count": trend_counter.get(mth, 0)} for mth in months]

    fail_rows = db.execute(
        select(TestRecord.kind, func.count())
        .where(TestRecord.verdict == "FAILED")
        .group_by(TestRecord.kind)
        .order_by(func.count().desc())
    ).all()

    return {
        "totals": {
            "evaluations": len(evaluations),
            "instruments": db.scalar(select(func.count()).select_from(Instrument)) or 0,
            "users": db.scalar(select(func.count()).select_from(User)) or 0,
            "test_records": db.scalar(select(func.count()).select_from(TestRecord)) or 0,
        },
        "status_counts": dict(status_counts),
        "outcome_counts": dict(outcome_counts),
        "trend": trend,
        "failures": [{"kind": kind, "count": count} for kind, count in fail_rows],
    }