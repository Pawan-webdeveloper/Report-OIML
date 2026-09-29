"""
Per-kind renderers: engine `computed` dicts → generic blocks the template draws.

Block shapes:
  {"type": "kv",    "title": str, "items": [[label, value], ...]}
  {"type": "table", "title": str, "columns": [str, ...], "rows": [[cell, ...], ...]}
  {"type": "note",  "text": str}
  {"type": "json",  "data": dict}

All gram values are converted to the instrument's DECLARED unit for display.
"""
from typing import Any

from ..engine.units import UNIT_TO_GRAM, dec

# Weighing-family kinds share the same computed shape (engine dispatcher maps them)
WEIGHING_FAMILY = {"WEIGHING", "TARE", "VOLTAGE", "DAMP_HEAT"}


def f(grams: Any, unit: str) -> str:
    """Grams (string from the engine) → display string in the declared unit."""
    if grams in (None, ""):
        return "—"
    try:
        return str(dec(grams) / UNIT_TO_GRAM[unit])
    except Exception:
        return str(grams)


def pflag(b: Any) -> str:
    return "—" if b is None else ("PASS" if b else "FAIL")


def _kv(title: str, items: list[tuple[str, Any]]) -> dict:
    return {"type": "kv", "title": title,
            "items": [[k, (v if v not in (None, "") else "—")] for k, v in items]}


def _table(title: str, columns: list[str], rows: list[list[Any]]) -> dict:
    return {"type": "table", "title": title, "columns": columns, "rows": rows}


def _weighing_blocks(computed: dict, unit: str) -> list[dict]:
    blocks: list[dict] = []
    if "E0" in computed:
        blocks.append(_kv("Zero error", [("E₀ (error at/near zero)", f(computed["E0"], unit) + " " + unit)]))
    rows = []
    for r in computed.get("rows", []):
        up, dn = r.get("up"), r.get("down")
        row_pass = None
        if up or dn:
            results = [d["pass"] for d in (up, dn) if d]
            row_pass = all(results)
        rows.append([
            f(r.get("L"), unit),
            f(up.get("P"), unit) if up else "—",
            f(up.get("Ec"), unit) if up else "—",
            f(dn.get("P"), unit) if dn else "—",
            f(dn.get("Ec"), unit) if dn else "—",
            f(r.get("mpe"), unit),
            pflag(row_pass),
        ])
    if rows:
        blocks.append(_table(
            "Observations",
            [f"Load ({unit})", f"P ↑ ({unit})", f"Ec ↑ ({unit})",
             f"P ↓ ({unit})", f"Ec ↓ ({unit})", f"|MPE| ({unit})", "Result"],
            rows))
    return blocks


def blocks_for_kind(kind: str, computed: dict, unit: str) -> list[dict]:
    if not computed:
        return [{"type": "note", "text": "No computed data recorded."}]

    if kind in WEIGHING_FAMILY:
        return _weighing_blocks(computed, unit)

    if kind in ("ECC_WEIGHTS", "ECC_ROLLING"):
        blocks = [_kv("Test setup", [
            ("Test load", f(computed.get("test_load"), unit) + " " + unit),
            ("Default ⅓(Max+T₊)", f(computed.get("expected_load_default_1_3"), unit) + " " + unit),
            ("E₀", f(computed.get("E0"), unit) + " " + unit),
            ("|MPE| at test load", f(computed.get("mpe"), unit) + " " + unit),
        ])]
        rows = [[loc.get("location"), f(loc.get("P"), unit), f(loc.get("Ec"), unit),
                 f(loc.get("mpe"), unit), pflag(loc.get("pass"))]
                for loc in computed.get("rows", [])]
        if rows:
            blocks.append(_table("Locations", ["Position", f"P ({unit})",
                                               f"Ec ({unit})", f"|MPE| ({unit})", "Result"], rows))
        return blocks

    if kind == "REPEATABILITY":
        rows = [[f(s.get("L"), unit), s.get("n"), f(s.get("Pmin"), unit),
                 f(s.get("Pmax"), unit), f(s.get("spread"), unit),
                 f(s.get("mpe"), unit), pflag(s.get("all_within_mpe")),
                 pflag(s.get("spread_ok")), pflag(s.get("pass"))]
                for s in computed.get("series", [])]
        return [_table("Series",
                       [f"Load ({unit})", "n", f"Pmin ({unit})", f"Pmax ({unit})",
                        f"Spread ({unit})", f"|MPE| ({unit})", "All within MPE",
                        "Spread ≤ MPE", "Result"], rows)]

    if kind == "TEMP_NOLOAD":
        rows = [[r.get("T1"), r.get("T2"), f(r.get("dP"), unit), r.get("dT"),
                 f(r.get("change"), unit), f(r.get("limit"), unit), pflag(r.get("pass"))]
                for r in computed.get("rows", [])]
        return [_table("Zero drift between temperatures",
                       ["T₁ (°C)", "T₂ (°C)", f"ΔP ({unit})", "ΔT (°C)",
                        f"Change / 5 °C ({unit})", f"Limit ({unit})", "Result"], rows)]

    if kind == "ZERO_RETURN":
        items = [("P₀ (before load)", f(computed.get("P0"), unit) + " " + unit),
                 ("P₃₀ (after load removed)", f(computed.get("P30"), unit) + " " + unit),
                 ("Change", f(computed.get("change"), unit) + " " + unit),
                 ("Limit", f(computed.get("limit"), unit) + " " + unit),
                 ("Result", pflag(computed.get("pass")))]
        blocks = [_kv("Zero return (30 min load)", items)]
        mr = computed.get("multiple_range")
        if mr:
            blocks.append(_kv("Multiple-range check (5 min unloaded, lowest range)", [
                ("P₃₅", f(mr.get("P35"), unit) + " " + unit),
                ("Change", f(mr.get("change"), unit) + " " + unit),
                ("Limit (e₁)", f(mr.get("limit"), unit) + " " + unit),
                ("Result", pflag(mr.get("pass"))),
            ]))
        return blocks

    if kind == "CREEP":
        blocks = [_kv("Creep", [
            ("Load", f(computed.get("load"), unit) + " " + unit),
            ("Mode", computed.get("mode")),
        ])]
        rows = [[r.get("t_min"), f(r.get("P"), unit), f(r.get("dP"), unit)]
                for r in computed.get("rows", [])]
        if rows:
            blocks.append(_table("Readings", ["t (min)", f"P ({unit})", f"ΔP ({unit})"], rows))
        return blocks

    if kind == "STABILITY_EQ":
        blocks: list[dict] = []
        ps = computed.get("print_store") or []
        if ps:
            blocks.append(_table("Printing / storage trials",
                                 ["Printed value", "Min display", "Max display",
                                  "Deviation", "Limit (e)", "Result"],
                                 [[f(t.get("printed"), unit), f(t.get("min"), unit),
                                   f(t.get("max"), unit), f(t.get("deviation"), unit),
                                   t.get("limit"), pflag(t.get("pass"))] for t in ps]))
        for name, label in (("zero_setting", "Zero-setting trials"),
                            ("tare_balancing", "Tare-balancing trials")):
            tr = computed.get(name) or []
            if tr:
                blocks.append(_table(label, ["E₀", "Limit (e)", "Result"],
                                     [[f(t.get("E0"), unit), t.get("limit"),
                                       pflag(t.get("pass"))] for t in tr]))
        return blocks or [{"type": "note", "text": "No trials recorded."}]

    if kind == "TILTING":
        blocks: list[dict] = []
        if computed.get("note"):
            blocks.append({"type": "note", "text": computed["note"]})
        nl = computed.get("no_load")
        if nl:
            if nl.get("note"):
                blocks.append({"type": "note", "text": nl["note"]})
            else:
                blocks.append(_kv("No-load, tilted", [
                    ("Change", f(nl.get("change"), unit) + " " + unit),
                    ("Limit", f(nl.get("limit"), unit) + " " + unit),
                    ("Result", pflag(nl.get("pass"))),
                ]))
        if computed.get("loaded"):
            blocks += _weighing_blocks(computed["loaded"], unit)
        return blocks or [{"type": "note", "text": "No data recorded."}]

    if kind == "WARMUP":
        rows = [[r.get("t_min"), f(r.get("L"), unit), f(r.get("Ec"), unit),
                 f(r.get("mpe"), unit), pflag(r.get("pass"))]
                for r in computed.get("rows", [])]
        blocks = [_kv("Warm-up", [("E₀", f(computed.get("E0"), unit) + " " + unit)])]
        if rows:
            blocks.append(_table("Readings before declared warm-up",
                                 ["t (min)", f"Load ({unit})", f"Ec ({unit})",
                                  f"|MPE| ({unit})", "Result"], rows))
        return blocks

    if kind.startswith("DIST_"):
        rows = [[r.get("load"), f(r.get("fault"), unit), f(r.get("e"), unit),
                 r.get("significant"), r.get("detected"), r.get("acted_upon"),
                 pflag(r.get("pass")), r.get("remarks") or ""]
                for r in computed.get("rows", [])]
        return [_table("Disturbance trials",
                       ["Load", "Fault", "e", "Significant", "Detected",
                        "Acted upon", "Result", "Remarks"], rows)]

    if kind == "SPAN_STABILITY":
        rows = [[c.get("label"), f(c.get("E"), unit), f(c.get("E_initial"), unit),
                 f(c.get("variation"), unit), f(c.get("limit"), unit), pflag(c.get("pass"))]
                for c in computed.get("rows", [])]
        blocks = [_kv("Span stability", [("Initial error E", f(computed.get("E_initial"), unit) + " " + unit)])]
        if rows:
            blocks.append(_table("Checks", ["Check", f"E ({unit})", f"E initial ({unit})",
                                            f"Variation ({unit})", f"Limit ({unit})", "Result"], rows))
        return blocks

    if kind == "ENDURANCE":
        blocks = [_kv("Endurance", [("Cycles applied", computed.get("cycles") or "—")])]
        blocks += _weighing_blocks(computed, unit)
        return blocks

    if kind == "CHECKLIST":
        failed = computed.get("failed_items") or []
        text = (f"{computed.get('count', 0)} items recorded; failed: {', '.join(failed)}"
                if failed else f"{computed.get('count', 0)} items recorded, none failed.")
        return [{"type": "note", "text": text}]

    if kind == "CONSTRUCTION":
        return [{"type": "note", "text": "Construction & fitment recorded; see photographs annex."}]

    return [{"type": "json", "data": computed}]