"""
Phase 1 'proof of life' endpoint: open /docs, calculate MPE live.
Proper auth-protected routers will come in Phase 5; this is a demo/utility.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..engine.classification import build_instrument
from ..engine.mpe import mpe
from ..engine.ruleset import load_ruleset
from ..engine.units import to_base

router = APIRouter(prefix="/calc", tags=["engine"])


class MpeRequest(BaseModel):
    accuracy_class: str                 # 'I' | 'II' | 'III' | 'IIII'
    min_capacity: str                   # e.g. "0.1"
    unit: str = "kg"                    # kg | g | mg | t | ct
    ranges: list[dict]                  # [{"e": "0.005", "d": "0.005", "max": "15"}]
    load: str                           # e.g. "12"
    context: str = "INITIAL"            # INITIAL | IN_SERVICE


@router.post("/mpe")
def calc_mpe(req: MpeRequest):
    try:
        inst = build_instrument(
            req.accuracy_class, req.min_capacity, req.unit, req.ranges
        )
        load_g = to_base(req.load, req.unit)
        value = mpe(load_ruleset(), inst, load_g, req.context)
        return {"mpe": str(value), "base_unit": "g", "context": req.context}
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))