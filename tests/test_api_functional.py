"""Functional tests of the mathagents API on a throwaway copy of the checkout."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api_fixtures import ROOT, copy_checkout  # noqa: E402

from mathagents import bindings, blueprint, counterexamples, dossiers, fidelity, gates, kernel, preferences, registries, snapshot  # noqa: E402
from mathagents.errors import KernelReportError, RecordError  # noqa: E402
from mathagents.results import GateResult  # noqa: E402

P2, P3, P4 = "p2-lewis-triviality", "p3-dutch-book", "p4-thirty-divides-n5-minus-n"


@pytest.fixture()
def root(tmp_path: Path, monkeypatch) -> Path:
    problem = kernel.kernel_report_problem(root=ROOT)
    assert problem is None, f"these tests need a fresh PASS kernel report (bash scripts/check_proof_integrity.sh): {problem}"
    monkeypatch.setenv("MATHAGENTS_TEST", "1")  # writes go into the throwaway copy
    return copy_checkout(tmp_path / "checkout")


def test_list_and_status(root):
    assert dossiers.list_dossiers(root=root) == [P2, P3, P4]
    s = dossiers.dossier_status(root=root, slug=P3)
    assert s.lean_namespace == "MathAgents.P3DutchBook" and s.has_kernel_snapshot
    assert {1, 2, 3, 4, 7, 8} <= set(s.stages_with_artifacts)
    assert any(lab.file == "README.md" and lab.value == "proved" for lab in s.result_labels)


def test_constants_mirror_the_gate_scripts():
    from mathagents import _scripts

    produced = {s.number: s.artifacts for s in dossiers.STAGES}
    for n, arts in _scripts.gate("dossier_structure").STAGE_ARTIFACTS.items():
        assert produced[n] == tuple(arts)
    assert [s.number for s in dossiers.STAGES] == list(range(9))
    assert counterexamples.METHODS == tuple(_scripts.gate("log_counterexample").METHODS)


def test_root_that_is_not_an_instance_is_refused(tmp_path):
    (tmp_path / "reports").mkdir()
    with pytest.raises(FileNotFoundError, match="neither a mathAgents checkout nor an instance"):
        dossiers.list_dossiers(root=tmp_path)


def test_instance_runs_the_harness_scripts_not_its_own(root):
    f = root / "scripts" / "validate_registries.py"  # an instance's own copy is never run
    f.write_text("raise SystemExit('instance code ran')\n")
    assert registries.validate_registries(root=root).success


def test_malformed_and_foreign_records_raise(root):
    d = root / "reports" / "dossiers" / P2
    (d / "fidelity.json").write_text("{not json")
    with pytest.raises(RecordError):
        fidelity.read_fidelity_record(root=root, slug=P2)
    rec = json.loads((ROOT / "reports" / "dossiers" / P3 / "fidelity.json").read_text())
    (d / "fidelity.json").write_text(json.dumps(rec))  # P3's record in P2's directory
    with pytest.raises(RecordError, match="does not match"):
        fidelity.read_fidelity_record(root=root, slug=P2)
    (d / "kernel-snapshot.json").write_text("[]")
    with pytest.raises(RecordError):
        snapshot.read_kernel_snapshot(root=root, slug=P2)


def test_validate_and_require_stage_pass(root):
    res = dossiers.validate_dossiers(root=root)
    assert isinstance(res, GateResult) and res.success, res.errors
    assert res.checked == [P2, P3, P4]
    assert dossiers.require_stage(root=root, slug=P2, stage=8).success
    assert fidelity.require_fidelity(root=root, slug=P3).success


def _cli(root, *args):
    import subprocess

    return subprocess.run([sys.executable, str(root / "scripts" / "validate_dossier.py"), "--root", str(root), *args],
                          capture_output=True, text=True)


def test_api_agrees_with_cli_on_pass_and_fail(root):
    ok = _cli(root)
    api = dossiers.validate_dossiers(root=root)
    assert ok.returncode == 0 and api.success
    p = root / "reports" / "dossiers" / P3 / "fidelity.json"
    rec = json.loads(p.read_text())
    rec["declarations"][0]["approver"] = ""  # a schema-invalid approval
    p.write_text(json.dumps(rec))
    bad, api = _cli(root, P3), dossiers.validate_dossiers(root=root, slugs=[P3])
    assert bad.returncode == 1 and not api.success
    assert [ln[5:] for ln in bad.stdout.splitlines() if ln.startswith("FAIL ")] == api.errors


def test_single_string_is_not_a_slug_list(root):
    with pytest.raises(TypeError):
        dossiers.validate_dossiers(root=root, slugs=P3)
    with pytest.raises(TypeError):
        bindings.check_lean_bindings(root=root, slugs=P3)


def test_snapshot_into_another_tree_needs_the_test_flag(root, monkeypatch):
    monkeypatch.delenv("MATHAGENTS_TEST")
    with pytest.raises(PermissionError):
        snapshot.snapshot_kernel(root=root, slug=P2)
    assert snapshot.snapshot_kernel(root=root, slug=P2, dry_run=True).success


def test_tampered_approval_lapses_and_fails(root):
    p = root / "reports" / "dossiers" / P3 / "fidelity.json"
    rec = json.loads(p.read_text())
    rec["declarations"][0]["statement_fingerprint"] = "1"
    p.write_text(json.dumps(rec))
    cov = fidelity.fidelity_coverage(root=root, slug=P3)
    assert rec["declarations"][0]["decl"] in cov.lapsed
    assert not dossiers.validate_dossiers(root=root, slugs=[P3]).success


def test_changed_intake_is_detected(root):
    card = root / "reports" / "dossiers" / P2 / "problem-card.md"
    card.write_text(card.read_text() + "\n")
    assert fidelity.fidelity_coverage(root=root, slug=P2).intake_current is False
    assert preferences.intake_digest(root=root, slug=P2) != preferences.intake_digest(root=ROOT, slug=P2)


def test_stale_kernel_report_is_refused(root):
    f = root / "lean" / "MathAgents" / "P3DutchBook.lean"
    f.write_text(f.read_text() + "\n-- edit\n")
    assert kernel.kernel_report_problem(root=root)
    with pytest.raises(KernelReportError):
        kernel.load_kernel_report(root=root)
    assert not kernel.load_kernel_report(root=root, require_fresh=False).verdict == ""
    assert not dossiers.validate_dossiers(root=root).success


def test_kernel_report_and_namespace(root):
    rep = kernel.load_kernel_report(root=root)
    assert rep.status("MathAgents.P2LewisTriviality.triviality_R2") == "proved"
    claims = kernel.declarations_in_namespace(root=root, namespace="MathAgents.P2LewisTriviality", include_helpers=False)
    assert len(claims) == 8 and not any(".Aux." in d.name for d in claims)


def test_invalid_input_raises(root):
    with pytest.raises(ValueError):
        dossiers.dossier_status(root=root, slug="Bad_Slug")
    with pytest.raises(FileNotFoundError):
        dossiers.dossier_status(root=root, slug="no-such-dossier")
    with pytest.raises(FileNotFoundError):
        dossiers.list_dossiers(root=root / "reports")
    with pytest.raises(ValueError):
        dossiers.validate_dossiers(root=root, require_stages={P2: 9})


def test_counterexample_log_dry_run_then_write(root):
    kw = dict(root=root, slug=P3, decl="MathAgents.P3DutchBook.converse_R2", method="manual", description="probe")
    dry = counterexamples.log_counterexample(**kw, dry_run=True)
    assert dry.success and dry.notices and not (root / "reports" / "dossiers" / P3 / "counterexamples.json").exists()
    real = counterexamples.log_counterexample(**kw)
    assert real.success and "CX-1" in real.message
    log = counterexamples.read_counterexample_log(root=root, slug=P3)
    e = log.entry("CX-1")
    assert e["statement_fingerprint"] == kernel.load_kernel_report(root=root).declarations[kw["decl"]].statement_fingerprint
    assert "verdict" not in e
    bad = counterexamples.log_counterexample(**{**kw, "decl": "MathAgents.Nope"})
    assert not bad.success and "not in the kernel report" in bad.errors[0]
    with pytest.raises(ValueError):
        counterexamples.log_counterexample(**{**kw, "method": "guess"})
    w = counterexamples.record_lean_witness(root=root, slug=P3, cx_id="CX-1", witness_decl=kw["decl"])
    assert not w.success  # a proved theorem does not negate itself


def test_invalid_record_raises(root):
    (root / "reports" / "dossiers" / P2 / "gax.json").write_text(json.dumps({"schema_version": 1, "slug": P2, "records": []}))
    from mathagents.axioms import read_gax_record

    with pytest.raises(RecordError):
        read_gax_record(root=root, slug=P2)


def test_snapshot_dry_run_and_refusals(root):
    snap = root / "reports" / "dossiers" / P2 / "kernel-snapshot.json"
    before = snap.read_bytes()
    res = snapshot.snapshot_kernel(root=root, slug=P2, dry_run=True)
    assert res.success and res.declaration_count == 16 and snap.read_bytes() == before
    assert snapshot.read_kernel_snapshot(root=root, slug=P2).lean_namespace == "MathAgents.P2LewisTriviality"
    (root / "reports" / "dossiers" / P2 / "fidelity.json").unlink()
    assert not snapshot.snapshot_kernel(root=root, slug=P2).success


def test_preferences_set_and_create(root):
    eff = preferences.effective_preferences(root=root, slug=P3)
    assert eff["readings.selected"].enforcement == "enforced"
    pf = root / "reports" / "dossiers" / P3 / "preferences.toml"
    before = pf.read_text()
    dry = preferences.set_preference(root=root, target=P3, key="readings.selected", value=["R1"], dry_run=True)
    assert dry.success and pf.read_text() == before
    real = preferences.set_preference(root=root, target=P3, key="readings.selected", value=["R1"])
    assert real.success and preferences.effective_preferences(root=root, slug=P3)["readings.selected"].choice == ["R1"]
    bad = preferences.set_preference(root=root, target="project", key="sources.translation", value="bogus")
    assert not bad.success and "restored" in bad.errors[0]
    made = preferences.create_dossier(root=root, slug="p9-new", domain="philosophy-of-science", dry_run=True)
    assert made.success and not (root / "reports" / "dossiers" / "p9-new").exists()
    made = preferences.create_dossier(root=root, slug="p9-new", domain="philosophy-of-science")
    assert made.success and len(made.written) == 2
    again = preferences.create_dossier(root=root, slug="p9-new", domain="philosophy-of-science")
    assert not again.success


def test_bindings_and_blueprint(root):
    scan = bindings.list_lean_bindings(root=root, slug=P3)
    assert not scan.errors and any(b.kind == "narration" and b.status == "proved" for b in scan.bindings)
    if (root / "reports" / "kernel" / "name-index.txt").exists():
        assert bindings.check_lean_bindings(root=root, assembled_only=True).success
    res = blueprint.check_blueprint(root=root)
    assert res.success and res.notices


def test_run_gates(root):
    rep = gates.run_gates(root=root)
    assert list(rep.results) == list(gates.GATES)
    if (root / "reports" / "kernel" / "name-index.txt").exists():
        assert rep.success, rep.errors
    f = root / "lean" / "MathAgents" / "P3DutchBook.lean"
    f.write_text(f.read_text() + "\n-- edit\n")
    stale = gates.run_gates(root=root)
    assert not stale.success and "G-KERNEL" in stale.failed
