"""scripts/lean_docs.py: the documentation matching the instance's pinned Lean and Mathlib. No network."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "lean_docs.py"
sys.path.insert(0, str(ROOT / "scripts"))
import lean_docs  # noqa: E402

REF = "https://lean-lang.org/doc/reference/"


def instance(tmp: Path, toolchain: str | None, mathlib_rev: str | None = None) -> Path:
    lean = tmp / "lean"
    lean.mkdir(parents=True)
    if toolchain is not None:
        (lean / "lean-toolchain").write_text(toolchain)
    packages = [{"name": "mathlib", "rev": mathlib_rev, "inputRev": "v4.32.1"}] if mathlib_rev else []
    (lean / "lake-manifest.json").write_text(json.dumps({"version": "1.1.0", "packages": packages}))
    return tmp


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "MATHAGENTS_ROOT": str(root)}
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)


def test_the_version_comes_from_the_toolchain_pin(tmp_path):
    assert lean_docs.lean_version(instance(tmp_path / "a", "leanprover/lean4:v4.32.1\n") / "lean") == "4.32.1"
    assert lean_docs.lean_version(instance(tmp_path / "b", "leanprover/lean4:v4.35.0-rc1") / "lean") == "4.35.0-rc1"
    assert lean_docs.lean_version(instance(tmp_path / "c", None) / "lean") is None


def test_reference_candidates_are_the_exact_release_then_the_minor_edition():
    assert lean_docs.reference_candidates("4.34.1") == [f"{REF}4.34.1/", f"{REF}4.34.0/"]
    assert lean_docs.reference_candidates("4.34.0") == [f"{REF}4.34.0/"]
    assert lean_docs.reference_candidates("4.35.0-rc1") == [f"{REF}4.35.0-rc1/", f"{REF}4.35.0/"]


def test_mathlib_resolves_to_the_pinned_rev_never_to_master_docs(tmp_path):
    root = instance(tmp_path, "leanprover/lean4:v4.32.1", mathlib_rev="520045ab")
    pin = lean_docs.mathlib_pin(root / "lean")
    assert pin["rev"] == "520045ab" and pin["source"].endswith("/tree/520045ab")
    assert pin["online_docs_pinned"] is False and pin["local_source"] == "lean/.lake/packages/mathlib"


def test_offline_json_lists_candidates_and_does_not_claim_a_resolved_reference(tmp_path):
    out = run(instance(tmp_path, "leanprover/lean4:v4.32.1", mathlib_rev="520045ab"), "--json")
    assert out.returncode == 0, out.stderr
    info = json.loads(out.stdout)
    assert info["lean"]["version"] == "4.32.1" and info["lean"]["probed"] is False
    assert info["lean"]["reference"] is None and info["lean"]["reference_candidates"][0] == f"{REF}4.32.1/"
    assert info["lean"]["release_notes"] == f"{REF}4.32.0/releases/v4.32.0/"
    assert "latest" not in out.stdout


def test_no_mathlib_dependency_is_reported_not_invented(tmp_path):
    out = run(instance(tmp_path, "leanprover/lean4:v4.32.1"))
    assert out.returncode == 0 and "Mathlib: not a dependency" in out.stdout


def test_a_missing_toolchain_exits_2(tmp_path):
    assert run(instance(tmp_path, None)).returncode == 2


def test_the_release_notes_use_the_minor_edition_even_when_the_exact_release_resolves(tmp_path, monkeypatch):
    monkeypatch.setattr(lean_docs, "resolves", lambda url: True)  # the exact 4.32.1 manual "resolves"
    info = lean_docs.resolve(instance(tmp_path, "leanprover/lean4:v4.32.1"), online=True)
    assert info["lean"]["reference"] == f"{REF}4.32.1/"
    assert info["lean"]["release_notes"] == f"{REF}4.32.0/releases/v4.32.0/"


def test_a_mathlib_entry_without_a_rev_is_an_error_not_a_none_link(tmp_path):
    root = instance(tmp_path, "leanprover/lean4:v4.32.1")
    (root / "lean" / "lake-manifest.json").write_text(json.dumps({"packages": [{"name": "mathlib"}]}))
    out = run(root)
    assert out.returncode != 0 and "no rev" in out.stderr + out.stdout


def test_a_corrupt_manifest_is_an_error_not_an_absent_mathlib(tmp_path):
    root = instance(tmp_path, "leanprover/lean4:v4.32.1")
    (root / "lean" / "lake-manifest.json").write_text("{not json")
    out = run(root)
    assert out.returncode != 0 and "unreadable" in out.stderr + out.stdout and "not a dependency" not in out.stdout


@pytest.mark.parametrize("text", ['[]', '{"packages": "x"}', '{"packages": [1]}'])
def test_a_manifest_that_is_not_a_lake_manifest_is_an_error(tmp_path, text):
    root = instance(tmp_path, "leanprover/lean4:v4.32.1")
    (root / "lean" / "lake-manifest.json").write_text(text)
    out = run(root)
    assert out.returncode == 1 and "not a Lake manifest" in out.stderr, out.stderr
