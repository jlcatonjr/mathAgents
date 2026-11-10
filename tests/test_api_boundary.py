"""The DD-29 boundary: the API never writes a human approval, G-AX record, allowlist entry or verdict."""
from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api_fixtures import ROOT, copy_checkout  # noqa: E402

from mathagents import _scripts, counterexamples, kernel, preferences, snapshot  # noqa: E402

PKG = ROOT / "mathagents"
FORBIDDEN_NAME = re.compile(r"(?i)approv|verdict|waive|allowlist_(add|write|set)|record_(fid|gax)")
PROTECTED = ("fidelity", "gax", "allowlist")
# every script the API reaches: imported in-process, or run as a subprocess
SUBPROCESS = ("proof_integrity.py", "build_name_index.py", "probe_machine.py", "validate_registries.py",
              "validate_evidence.py", "validate_claim_ledger.py")
WRITE_CALLS = {"write_text", "write_bytes", "unlink", "rename", "replace", "write_atomic", "dump", "open", "mkstemp"}


def _public_functions():
    for f in sorted(PKG.glob("*.py")):
        if f.stem.startswith("_"):
            continue
        mod = importlib.import_module(f"mathagents.{f.stem}")
        for name in getattr(mod, "__all__", []):
            obj = getattr(mod, name)
            if inspect.isfunction(obj):
                yield f.stem, name, obj


def _writes(path: Path) -> list[str]:
    """The source of every write-like call in a file (a lint; the behavioural test below is the proof)."""
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if name in WRITE_CALLS:
                out.append(ast.unparse(node))
    return out


def test_no_public_function_offers_a_human_decision():
    bad = [f"{m}.{n}" for m, n, _ in _public_functions() if FORBIDDEN_NAME.search(n)]
    assert not bad, bad


def test_the_scan_sees_the_writes_it_must_check():
    """Guard against a vacuous scan: the reached scripts do write files."""
    found = [src for f in _scripts.IN_PROCESS for src in _writes(ROOT / "scripts" / f)]
    assert any("write_atomic" in s for s in found) and any("write_text" in s for s in found)


def test_no_reached_code_writes_a_protected_record():
    files = sorted(PKG.glob("*.py")) + [ROOT / "scripts" / f for f in (*_scripts.IN_PROCESS, *SUBPROCESS)]
    bad = []
    for f in files:
        for src in _writes(f):
            if any(p in src.lower() for p in PROTECTED):
                bad.append(f"{f.name}: {src}")
    assert not bad, bad


def test_operator_only_settings_are_refused():
    for key in ("gax.P3-6", "fidelity.kernel_as_judge"):
        with pytest.raises(ValueError, match="operator decision"):
            preferences.set_preference(target="p3-dutch-book", key=key, value="x", dry_run=True)


def test_every_writer_succeeds_and_leaves_protected_records_untouched(tmp_path, monkeypatch):
    problem = kernel.kernel_report_problem(root=ROOT)
    assert problem is None, f"needs a fresh PASS kernel report: {problem}"
    monkeypatch.setenv("MATHAGENTS_TEST", "1")
    root = copy_checkout(tmp_path / "c")
    files = [p for p in (root / "reports" / "dossiers").rglob("*") if p.stem in ("fidelity", "gax")] + [
        root / "references" / "axiom-allowlist.json"]
    digest = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    slug, decl = "p3-dutch-book", "MathAgents.P3DutchBook.converse_R2"
    assert counterexamples.log_counterexample(root=root, slug=slug, decl=decl, method="manual", description="x").success
    witness = counterexamples.record_lean_witness(root=root, slug=slug, cx_id="CX-1", witness_decl=decl)
    assert not witness.success and "does not negate" in witness.errors[0]  # refused: reaches the check, writes nothing
    assert snapshot.snapshot_kernel(root=root, slug=slug).success
    assert preferences.set_preference(root=root, target=slug, key="readings.selected", value=["R1"]).success
    assert preferences.create_dossier(root=root, slug="p9-x", domain="philosophy-of-science").success
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files} == digest
    log = counterexamples.read_counterexample_log(root=root, slug=slug)
    assert [e["id"] for e in log.entries] == ["CX-1"] and all("verdict" not in e for e in log.entries)
