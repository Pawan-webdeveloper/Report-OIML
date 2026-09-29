# app/engine/tests/checklist.py
"""
FORM 17 — Checklist (17.1–17.4) [V]. Pass: no item FAILED.
obs = {"items": [{"code": "7.1.1", "state": "PASSED|FAILED|NOT_APPLICABLE",
                  "device_state": "EXISTENT|NON_EXISTENT", "remarks": ""}]}
"""
def evaluate_checklist(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    items = obs.get("items") or []
    failed = [i.get("code") for i in items if i.get("state") == "FAILED"]
    warnings = []
    if failed:
        warnings.append({"severity": "WARN", "code": "CHECKLIST_FAILED",
                         "message": f"Failed checklist items: {', '.join(failed)}"})
    verdict = "FAILED" if failed else ("PASSED" if items else "PENDING")
    return {"count": len(items), "failed_items": failed}, verdict, warnings