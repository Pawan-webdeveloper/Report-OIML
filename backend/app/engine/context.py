"""
EvaluationContext — gives the engine evaluation-level settings (immutable).
Will be built from the Evaluation row in Phase 5.
"""
from dataclasses import dataclass
from decimal import Decimal as D


@dataclass(frozen=True)
class EvaluationContext:
    mpe_context: str = "INITIAL"            # INITIAL | IN_SERVICE  (3.5.2)
    resolution: D | None = None             # resolution during test (smaller than e)
    auto_zero_status: str = "NON_EXISTENT"  # NON_EXISTENT | NOT_IN_OPERATION |
                                            # OUT_OF_WORKING_RANGE | IN_OPERATION