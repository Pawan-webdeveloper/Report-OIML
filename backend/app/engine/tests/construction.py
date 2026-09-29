# app/engine/tests/construction.py
"""
FORM 16 — Construction & fitment: free text + photo. Verdict: PASSED if a
description is given (the reviewer will approve the details), otherwise PENDING.
"""
def evaluate_construction(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    desc = (obs.get("description") or "").strip()
    warnings = []
    if desc and not obs.get("has_photos"):
        warnings.append({"severity": "WARN", "code": "NO_PHOTOS",
                         "message": "Construction description hai par photos attached nahi"})
    return {"description_present": bool(desc)}, ("PASSED" if desc else "PENDING"), warnings