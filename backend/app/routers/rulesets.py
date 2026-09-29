"""
Rule set inspector. Read-only for any authenticated user — rules are DATA
(Golden Rule #2), so showing them is safe and demonstrable.

Source of truth: the `rulesets` table (seeded with the document JSON).
Fallback: the packaged JSON file, so the page works even before seeding.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import get_db
from ..core.deps import get_current_user
from ..engine.ruleset import load_ruleset
from ..models import Ruleset, User
from ..schemas.admin import RulesetDetail, RulesetOut

router = APIRouter(prefix="/rulesets", tags=["rulesets"])
settings = get_settings()


def _from_file(ruleset_id: str) -> RulesetDetail | None:
    try:
        doc = load_ruleset(ruleset_id)
    except FileNotFoundError:
        return None
    return RulesetDetail(
        id=ruleset_id,
        title=doc.get("title"),
        effective_from=None,
        sha256=doc["_sha256"],
        is_active=True,
        document={k: v for k, v in doc.items() if not k.startswith("_")},
    )


@router.get("", response_model=list[RulesetOut])
def list_rulesets(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    rows = db.scalars(select(Ruleset).order_by(Ruleset.id)).all()
    if rows:
        return rows
    fallback = _from_file(settings.RULESET_ID)
    return [fallback] if fallback else []


@router.get("/{ruleset_id}", response_model=RulesetDetail)
def get_ruleset(ruleset_id: str, db: Session = Depends(get_db),
                _user: User = Depends(get_current_user)):
    row = db.get(Ruleset, ruleset_id)
    if row is not None:
        return RulesetDetail(
            id=row.id, title=row.title, effective_from=row.effective_from,
            sha256=row.sha256, is_active=row.is_active, document=row.document,
        )
    detail = _from_file(ruleset_id)
    if detail is None:
        raise HTTPException(404, "Ruleset not found")
    return detail