"""
Validation layer — two jobs:
1. validate_instrument(): Table 3 classification checks [V] + d-form check [V 4.2.2.1]
2. check_weighing_observations(): plausibility warnings (doc §8.1)

Severity: "ERROR" (data/entry wrong — blocks submit) | "WARN" (suspicious — goes into report)
"""
from decimal import Decimal as D

from .units import dec


# ---------------------------------------------------------------- instrument

def _table3_row(rs: dict, cls: str, e: D) -> dict | None:
    rows = rs["classification_table3"][cls]
    if isinstance(rows, dict):
        rows = [rows]
    for row in rows:
        lo = dec(row["e_min_g"])
        hi = row["e_max_g"]
        if e >= lo and (hi is None or e <= dec(hi)):
            return row
    return None


def _interval_form_mantissa(d: D) -> int:
    """Extracts the mantissa from d.normalize() digits (5000→5, 0.005→5, 2.5→25)."""
    t = d.normalize().as_tuple()
    return int("".join(map(str, t.digits))) if t.digits else 0


def validate_instrument(rs: dict, inst) -> tuple[list[dict], list[dict]]:
    """Table 3 [V]: e-band per range, n=Max/e limits; Min ≥ min_in_e × e1."""
    errors: list[dict] = []
    warns: list[dict] = []

    if not inst.ranges:
        errors.append({"severity": "ERROR", "code": "T3_NO_RANGE",
                       "message": "Instrument needs at least one range (3.1)"})
        return errors, warns

    e1 = inst.ranges[0].e
    prev = None
    for i, r in enumerate(inst.ranges, start=1):
        if prev is not None and r.e <= prev:
            errors.append({"severity": "ERROR", "code": "T3_E_ORDER",
                           "message": f"Range {i}: e_{i} ({r.e} g) pichhle e se bada hona chahiye (3.3)"})
        prev = r.e

        row = _table3_row(rs, inst.cls, r.e)
        if row is None:
            errors.append({"severity": "ERROR", "code": "T3_E_BAND",
                           "message": f"Range {i}: e = {r.e} g class {inst.cls} ke liye Table 3 band me nahi hai"})
            continue

        n = r.max / r.e
        n_min, n_max = dec(row["n_min"]), row["n_max"]
        if n < n_min or (n_max is not None and n > dec(n_max)):
            errors.append({"severity": "ERROR", "code": "T3_N",
                           "message": f"Range {i}: n = Max/e = {n}, allowed "
                                      f"{row['n_min']}–{n_max or '∞'} (Table 3, class {inst.cls})"})

    row1 = _table3_row(rs, inst.cls, e1)
    if row1 is not None and inst.min_cap < dec(row1["min_in_e"]) * e1:
        errors.append({"severity": "ERROR", "code": "T3_MIN",
                       "message": f"Min ({inst.min_cap} g) < {row1['min_in_e']} × e1 "
                                  f"({dec(row1['min_in_e']) * e1} g) — Table 3 violation"})

    for i, r in enumerate(inst.ranges, start=1):
        if _interval_form_mantissa(r.d) not in (1, 2, 5):
            warns.append({"severity": "WARN", "code": "D_FORM",
                          "message": f"Range {i}: d = {r.d} g (1, 2 ya 5) × 10^k form me nahi hai "
                                     f"[checklist 4.2.2.1]"})
    return errors, warns


# --------------------------------------------------------------- observations

def check_weighing_observations(rs: dict, inst, ctx, obs: dict) -> list[dict]:
    """Weighing-family plausibility (doc §8.1). Masses expected in BASE GRAMS."""
    warns: list[dict] = []
    points = obs.get("points") or []

    for p in points:
        if p.get("L") in (None, ""):
            continue
        L = dec(p["L"])

        if L > inst.max + inst.tare_plus:
            warns.append({"severity": "ERROR", "code": "L_GT_MAX",
                          "message": f"Load {L} g > Max + T+ = {inst.max + inst.tare_plus} g"})
            continue
        if L < inst.min_cap:
            warns.append({"severity": "WARN", "code": "L_LT_MIN",
                          "message": f"Load {L} g Min ({inst.min_cap} g) se neeche hai"})

        # multi-interval: do not take the exact load at a scale-interval change point (take ~5e below)
        if inst.is_multi_interval:
            for r in inst.ranges[:-1]:
                if L == r.max:
                    warns.append({"severity": "WARN", "code": "L_AT_INTERVAL_CHANGE",
                                  "message": f"Load {L} g exactly scale-interval change point "
                                             f"(Max_{r.idx}) par hai — ~5 e neeche use karo"})

        r_now = inst.range_for_load(L) if L <= inst.max else inst.ranges[-1]
        for dirn in ("up", "down"):
            entry = p.get(dirn) or {}
            if entry.get("I") in (None, ""):
                continue
            I = dec(entry["I"])
            if abs(I - L) > D(11) * r_now.e:
                warns.append({"severity": "WARN", "code": "I_TOO_FAR",
                              "message": f"{dirn}@{L} g: indication {I} g load se "
                                         f"11 e se zyada door — typo ho sakta hai"})
            if entry.get("dL") not in (None, ""):
                dv = dec(entry["dL"])
                st = ctx.resolution or r_now.d
                if dv < 0 or dv >= st:
                    warns.append({"severity": "WARN", "code": "DL_RANGE",
                                  "message": f"{dirn}@{L} g: ΔL = {dv} g — 0 ≤ ΔL < step "
                                             f"({st} g) hona chahiye (changeover method)"})

    loads = [dec(p["L"]) for p in points if p.get("L") not in (None, "")]
    n_min = 10 if obs.get("initial_intrinsic") else 5      # A.4.4 initial [M/C]
    if loads and len(loads) < n_min:
        warns.append({"severity": "WARN", "code": "TOO_FEW_LOADS",
                      "message": f"Sirf {len(loads)} loads — kam se kam {n_min} chahiye"})

    if loads and inst.is_multi_interval is False:
        if min(loads) > inst.min_cap:
            warns.append({"severity": "WARN", "code": "MIN_NOT_COVERED",
                          "message": f"Min ({inst.min_cap} g) test me cover nahi hua"})
        if max(loads) < inst.max and not obs.get("blanking_at_max"):
            warns.append({"severity": "WARN", "code": "MAX_NOT_COVERED",
                          "message": f"Max ({inst.max} g) test me cover nahi hua"})

    # Are MPE change points covered? (doc §7.4 point 3)
    for b in rs["mpe_bands"][inst.cls]:
        if b["up_to"]:
            x = dec(b["up_to"]) * inst.ranges[0].e
            if inst.min_cap < x <= inst.max and x not in loads:
                warns.append({"severity": "WARN", "code": "MPE_CHANGE_POINT_MISSING",
                              "message": f"MPE change point {x} g ({b['up_to']} e) "
                                         f"test loads me nahi hai"})

    # Humidity (temperature tests) — P108 [M]
    env = obs.get("environment") or {}
    for phase in ("start", "max", "end"):
        block = env.get(phase) or {}
        if block.get("temp") is not None and block.get("rh") is not None:
            ah = absolute_humidity(dec(str(block["temp"])), dec(str(block["rh"])))
            if ah is not None and ah > dec(rs["constants"]["absolute_humidity_limit_g_m3"]["value"]):
                warns.append({"severity": "WARN", "code": "HUMIDITY_HIGH",
                              "message": f"{phase}: absolute humidity {ah} g/m³ > 20 g/m³ "
                                         f"limit [P108]"})
    return warns


def absolute_humidity(temp_c: D, rh_pct: D) -> D | None:
    """
    Magnus formula (doc §6.7, NMI P108 [M]):
        es(T) = 6.112 × exp(17.62 T / (243.12 + T))   [hPa]
        AH    = es × RH × 2.1674 / (273.15 + T)        [g/m³]
    Warning-only calculation — float-free, uses Decimal exp().
    """
    if temp_c <= D("-243.12"):
        return None
    es = D("6.112") * (D("17.62") * temp_c / (D("243.12") + temp_c)).exp()
    return es * rh_pct * D("2.1674") / (D("273.15") + temp_c)