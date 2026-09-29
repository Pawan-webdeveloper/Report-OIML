"""
Shared schema helpers.

DecimalStr: accepts "0.005", 0.005, or 5 and normalizes to the STRING "0.005".
Strings are what the ExactNumeric column and the engine expect (Golden Rule #4:
no floats cross the boundary as numbers — they arrive as exact text).
"""
from typing import Annotated, Any

from pydantic import BeforeValidator


def _to_dec_str(v: Any) -> str:
    if v is None or v == "":
        raise ValueError("numeric value required")
    return str(v)


DecimalStr = Annotated[str, BeforeValidator(_to_dec_str)]