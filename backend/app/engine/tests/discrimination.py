"""
FORM 4 — Discrimination (A.4.8) & Sensitivity (A.4.9) [V].

4.1.1 Digital [V]: extra load 1.4 d → I2 − I1 ≥ d (unambiguous change)
4.1.2 Analog:      extra |mpe| → displacement ≥ 0.7 × |mpe|
4.1.3 Non-self:    extra 0.4|mpe| → visible displacement (boolean)
4.2  Sensitivity:  extra |mpe| → ≥ 1 mm (I, II); 2 mm (III/IIII Max ≤ 30 kg);
                   5 mm (III/IIII Max > 30 kg)
"""
from decimal import Decimal as D

from ..mpe import mpe
from ..units import dec


def evaluate_disc_digital(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    factor = dec(rs["constants"]["discrimination_extra_load_d"]["value"])   # 1.4
    rows, ok, any_obs = [], True, False
    for item in obs.get("loads") or []:
        L = dec(item["L"])
        r = inst.range_for_load(L)
        change = dec(item["I2"]) - dec(item["I1"])
        ok_i = change >= r.d
        ok &= ok_i
        any_obs = True
        rows.append({"L": str(L), "extra_required": str(factor * r.d),
                     "change": str(change), "d": str(r.d), "pass": ok_i})
    if not any_obs:
        return {"rows": rows}, "PENDING", []
    return {"rows": rows}, ("PASSED" if ok else "FAILED"), []


def evaluate_disc_analog(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    frac = dec(rs["constants"]["disc_analog_fraction_of_mpe"]["value"])     # 0.7
    rows, ok, any_obs = [], True, False
    for item in obs.get("loads") or []:
        L = dec(item["L"])
        m = mpe(rs, inst, L, ctx.mpe_context)
        change = dec(item["I2"]) - dec(item["I1"])
        ok_i = change >= frac * m
        ok &= ok_i
        any_obs = True
        rows.append({"L": str(L), "extra_required": str(m),
                     "min_change": str(frac * m), "change": str(change), "pass": ok_i})
    if not any_obs:
        return {"rows": rows}, "PENDING", []
    return {"rows": rows}, ("PASSED" if ok else "FAILED"), []


def evaluate_disc_nonself(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    frac = dec(rs["constants"]["disc_nonself_fraction_of_mpe"]["value"])    # 0.4
    rows, ok, any_obs = [], True, False
    for item in obs.get("loads") or []:
        L = dec(item["L"])
        m = mpe(rs, inst, L, ctx.mpe_context)
        ok_i = bool(item.get("visible_change"))
        ok &= ok_i
        any_obs = True
        rows.append({"L": str(L), "extra_required": str(frac * m), "pass": ok_i})
    if not any_obs:
        return {"rows": rows}, "PENDING", []
    return {"rows": rows}, ("PASSED" if ok else "FAILED"), []


def evaluate_sensitivity(rs, inst, ctx, obs) -> tuple[dict, str, list]:
    c = rs["constants"]["sensitivity_displacement_mm"]
    if inst.cls in ("I", "II"):
        need = dec(c["value"])                               # 1 mm
    else:
        need = dec(c["class_III_IIII_max_le_30kg"] if inst.max <= dec("300000")
                   else c["class_III_IIII_max_gt_30kg"])     # 2 mm / 5 mm
    rows, ok, any_obs = [], True, False
    for item in obs.get("loads") or []:
        L = dec(item["L"])
        m = mpe(rs, inst, L, ctx.mpe_context)
        disp = dec(item["displacement_mm"])
        ok_i = disp >= need
        ok &= ok_i
        any_obs = True
        rows.append({"L": str(L), "extra_required": str(m),
                     "need_mm": str(need), "got_mm": str(disp), "pass": ok_i})
    if not any_obs:
        return {"rows": rows}, "PENDING", []
    return {"rows": rows, "required_mm": str(need)}, ("PASSED" if ok else "FAILED"), []