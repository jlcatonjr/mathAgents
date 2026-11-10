"""The pilot register (references/pilots.json, D11/D44) and its check in scripts/validate_registries.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

pytest.importorskip("jsonschema")
import validate_registries as vr  # noqa: E402


def _root(tmp_path: Path, pilots, logics_pilots=None) -> Path:
    (tmp_path / "references").mkdir()
    for slug in ("p2-lewis-triviality", "p3-dutch-book", "p4-thirty-divides-n5-minus-n"):
        (tmp_path / "reports" / "dossiers" / slug).mkdir(parents=True)
    logics = json.loads((ROOT / "references" / "object-logics.json").read_text())
    if logics_pilots is not None:
        for e in logics["logics"]:
            e["pilot"] = logics_pilots.get(e["id"])
    (tmp_path / "references" / "object-logics.json").write_text(json.dumps(logics))
    if pilots is not None:
        (tmp_path / "references" / "pilots.json").write_text(json.dumps({"schema_version": 1, "pilots": pilots}))
    return tmp_path


def _real():
    return json.loads((ROOT / "references" / "pilots.json").read_text())["pilots"]


def test_the_repository_register_is_valid():
    assert vr.check_pilots(ROOT) == []


def test_the_m6_dossier_is_pilot_p6_and_d11_p4_is_modal():
    by_id = {p["id"]: p for p in _real()}
    assert by_id["P6"]["dossier"] == "p4-thirty-divides-n5-minus-n"
    assert by_id["P4"]["dossier"] is None and "Modal" in by_id["P4"]["title"]


def test_an_instance_without_a_register_is_not_checked(tmp_path):
    assert vr.check_pilots(_root(tmp_path, None)) == []


@pytest.mark.parametrize("mutate, expected", [
    (lambda ps: ps + [dict(ps[0])], "duplicate pilot ids"),
    (lambda ps: [dict(p, id="X1") if p["id"] == "P1" else p for p in ps], "not of the form P<n>"),
    (lambda ps: [dict(p, dossier="no-such-dossier") if p["id"] == "P2" else p for p in ps], "is not a reports/dossiers"),
    (lambda ps: [dict(p, dossier="p2-lewis-triviality") if p["id"] == "P6" else p for p in ps], "more than one pilot"),
])
def test_register_defects_are_reported(tmp_path, mutate, expected):
    problems = vr.check_pilots(_root(tmp_path, mutate(_real())))
    assert any(expected in p for p in problems), problems


def test_an_object_logic_pilot_must_be_registered(tmp_path):
    root = _root(tmp_path, [p for p in _real() if p["id"] != "P4"])
    assert any("modal-k" in p and "'P4'" in p for p in vr.check_pilots(root))
