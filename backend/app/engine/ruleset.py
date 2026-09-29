"""
Ruleset loader + integrity hash.

GOLDEN DESIGN RULE #2 (project.md §3.2): the rule set is DATA, not code.
- New OIML revision → new JSON file → code untouched.
- Every report stores ruleset_id + SHA-256 (audit/reproducibility).
"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

RULESETS_DIR = Path(__file__).resolve().parents[1] / "rulesets"


@lru_cache(maxsize=None)
def load_ruleset(ruleset_id: str = "oiml-r76-2006") -> dict:
    path = RULESETS_DIR / f"{ruleset_id}.json"
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    data["_id"] = ruleset_id
    data["_sha256"] = hashlib.sha256(raw).hexdigest()
    return data