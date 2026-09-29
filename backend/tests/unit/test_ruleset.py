import hashlib

import pytest

from app.engine.ruleset import RULESETS_DIR, load_ruleset


def test_loads_default_ruleset():
    rs = load_ruleset()
    assert rs["_id"] == "oiml-r76-2006"
    assert len(rs["_sha256"]) == 64


def test_sha256_matches_file():
    rs = load_ruleset()
    raw = (RULESETS_DIR / "oiml-r76-2006.json").read_bytes()
    assert rs["_sha256"] == hashlib.sha256(raw).hexdigest()


def test_mpe_bands_present_for_all_classes():
    rs = load_ruleset()
    for cls in ("I", "II", "III", "IIII"):
        assert cls in rs["mpe_bands"], f"missing mpe_bands for class {cls}"


def test_every_constant_has_clause():
    rs = load_ruleset()
    missing = [
        name
        for name, entry in rs["constants"].items()
        if not entry.get("clause")
    ]
    assert not missing, f"constants without clause: {missing}"


def test_unknown_ruleset_raises():
    with pytest.raises(FileNotFoundError):
        load_ruleset("does-not-exist")
