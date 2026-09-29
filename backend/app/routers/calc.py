"""
Live engine endpoint. FIX: the load is now converted from the instrument UNIT to BASE GRAMS.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..engine.classification import build_instrument
from ..engine.mpe import mpe
from ..engine.ruleset import load_ruleset
from ..engine.units import to_base

router = APIRouter(prefix="/calc", tags=["engine"])


class MpeRequest(BaseModel):
    accuracy_class: str
    min_capacity: str
    unit: str = "kg"
    ranges: list[dict]
    load: str
    context: str = "INITIAL"


@router.post("/mpe")
def calc_mpe(req: MpeRequest):
    try:
        inst = build_instrument(req.accuracy_class, req.min_capacity, req.unit, req.ranges)
        load_g = to_base(req.load, req.unit)          # ← FIX: 12 kg → 12000 g
        value = mpe(load_ruleset(), inst, load_g, req.context)
        return {"mpe": str(value), "base_unit": "g", "context": req.context}
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))