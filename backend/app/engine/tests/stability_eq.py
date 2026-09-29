"""
FORM 7 — Stability of equilibrium (A.4.12) [V]. Applies where printing/storage/
zero-setting/tare-balancing exists. All three blocks are optional — only the
ones provided are evaluated.

print_store [V]: printed value within ≤ 1 e of the display readings (5 s);
                 warning even if spread > 1 e (only 2 adjacent values allowed).
zero_setting / tare_balancing [V]: 5 trials, |E0| ≤ 0.25 e each
                 (if auto-zero is in operation, L0 = 10 e appears in the zero row [M]).
"""
from decimal import Decimal as D

from ..error import point_error
from ..units import dec


def evaluate_stability_eq(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    e = inst.smallest_e()
    step = ctx.resolution or inst.ranges[0].d
    zero_acc = dec(rs["constants"]["zero_setting_accuracy_e"]["value"])   # 0.25
    warnings, ok, any_obs = [], True, False
    computed: dict = {}

    # --- printing / storage ---
    ps_rows = []
    for t in obs.get("print_store") or []:
        printed, mn, mx = dec(t["printed"]), dec(t["min_display"]), dec(t["max_display"])
        dev = max(abs(printed - mn), abs(printed - mx))
        ok_i = dev <= e
        if mx - mn > e:
            warnings.append({"severity": "WARN", "code": "STAB_SPREAD",
                             "message": f"Display spread {mx - mn} g > 1 e — "
                                        f"sirf 2 adjacent values allowed [A.4.12]"})
        ok &= ok_i
        any_obs = True
        ps_rows.append({"printed": str(printed), "min": str(mn), "max": str(mx),
                        "deviation": str(dev), "limit": str(e), "pass": ok_i})
    if ps_rows:
        computed["print_store"] = ps_rows

    # --- zero-setting / tare-balancing (same criterion 0.25 e) ---
    for block_name in ("zero_setting", "tare_balancing"):
        rows = []
        for t in obs.get(block_name) or []:
            _, E0 = point_error(t.get("I", "0"), t.get("L", "0"), t.get("dL", "0"), step)
            ok_i = abs(E0) <= zero_acc * e
            ok &= ok_i
            any_obs = True
            rows.append({"E0": str(E0), "limit": str(zero_acc * e), "pass": ok_i})
        if rows:
            computed[block_name] = rows

    if not any_obs:
        return computed, "PENDING", warnings
    return computed, ("PASSED" if ok else "FAILED"), warnings