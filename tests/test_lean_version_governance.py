"""Lean-version governance as harness features (D38; baseAgent handoff LV1-LV11; docs/lean-version-governance.md).

The pin reader, G-KERNEL's toolchain check (with a `lean` shim, and with the real elan when two toolchains are
installed), the pin-consistency checks, the vendored rules and the agents that point to them, doctor's stale-version
scan, the bump command, pin stamps, the verified-toolchains register and the machine probe. No Lean build.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from mathagents import _harness_files, cli  # noqa: E402
import build_name_index  # noqa: E402
import dossier_structure  # noqa: E402
import lean_pin  # noqa: E402
import probe_machine  # noqa: E402
import validate_dossier  # noqa: E402

V32, V34 = "leanprover/lean4:v4.32.1", "leanprover/lean4:v4.34.1"
REV32, REV34 = "520045ab14e26149ee970e2e617ca04b09bde5d6", "d13f23b723b8a846827a245b89c10fc7d3f11612"


def lakefile(rev: str) -> str:
    return (f'name = "demo"\n[[require]]\nname = "mathlib"\ngit = "https://github.com/leanprover-community/mathlib4"\n'
            f'rev = "{rev}"\n[[lean_lib]]\nname = "Demo"\n[[lean_lib]]\nname = "DemoWIP"\n')


def lean_tree(root: Path, toolchain: str = V32, rev: str = REV32, lake_rev: str = "v4.32.1",
              input_rev: str = "v4.32.1", checkout: str | None = None) -> Path:
    lean = root / "lean"
    (lean / "Demo").mkdir(parents=True, exist_ok=True)
    (lean / "lean-toolchain").write_text(toolchain + "\n")
    (lean / "lakefile.toml").write_text(lakefile(lake_rev))
    (lean / "lake-manifest.json").write_text(json.dumps(
        {"version": "1.1.0", "packages": [{"name": "mathlib", "rev": rev, "inputRev": input_rev}]}))
    (lean / "Demo.lean").write_text("theorem t : True := trivial\n")
    (root / "references").mkdir(exist_ok=True)
    (root / "references" / "axiom-allowlist.json").write_text(json.dumps(
        {"base_axioms": ["propext", "Classical.choice", "Quot.sound"], "approved_axioms": [], "approvals": []}))
    if checkout is not None:
        (lean / ".lake" / "packages" / "mathlib").mkdir(parents=True)
        (lean / ".lake" / "packages" / "mathlib" / "lean-toolchain").write_text(checkout + "\n")
    return lean


def mathagents(*args: str, cwd: Path, **env: str) -> subprocess.CompletedProcess:
    e = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(ROOT), "HOME": str(Path.home()), **env}
    return subprocess.run([sys.executable, "-m", "mathagents.cli", *args], cwd=cwd, capture_output=True, text=True, env=e)


@pytest.fixture
def instance(tmp_path):
    ws = tmp_path / "ws"
    (ws / ".github" / "agents").mkdir(parents=True)
    (ws / ".github" / "agents" / cli.ORCHESTRATOR).write_text("---\nname: Orchestrator\nagents:\n  - orchestrator\n---\n")
    inst = ws / "Projects" / "Demo"
    r = mathagents("init", str(inst), "--agents-to", "../../.github/agents", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    lean_tree(inst, checkout=V32)
    r = mathagents("sync", "--write", cwd=inst)
    assert r.returncode == 0, r.stdout + r.stderr
    return inst


# --- the pin reader -------------------------------------------------------------------------------------

@pytest.mark.parametrize("text, want", [
    (V32, "4.32.1"), ("leanprover/lean4:v4.35.0-rc1", "4.35.0-rc1"),
    ("leanprover/lean4:nightly-2026-10-01", "nightly-2026-10-01"),
    ("Lean (version 4.32.1, arm64-apple-darwin24.6.0, commit f054605, Release)", "4.32.1"),
    ("Lean (version 4.35.0-rc1, x86_64-unknown-linux-gnu, commit 1, Release)", "4.35.0-rc1"),
    ("Lean (version 4.36.0-nightly-2026-10-01, x86_64, commit 1, Release)", "nightly-2026-10-01"),
    ("", None), (None, None), ("no version here", None)])
def test_release_parses_toolchains_and_lean_version_output(text, want):
    assert lean_pin.release(text) == want


def test_toolchain_mismatch_names_both_releases_and_never_passes_unreadable_output():
    wrong = lean_pin.toolchain_mismatch("Lean (version 4.32.1, x)", V34)
    assert "4.32.1" in wrong and "4.34.1" in wrong and "ELAN_TOOLCHAIN" in wrong
    assert lean_pin.toolchain_mismatch("Lean (version 4.34.1, x)", V34) is None
    assert lean_pin.toolchain_mismatch("", V34)  # an empty `lean --version` is a finding, not a skip
    assert lean_pin.toolchain_mismatch("Lean (version 4.35.0, x)", "leanprover/lean4:v4.35.0-rc1")
    assert lean_pin.toolchain_mismatch("Lean (version 4.36.0-nightly-2026-10-01, x)",
                                       "leanprover/lean4:nightly-2026-10-01") is None


def test_pin_findings_p2_mismatch_p4_mismatch_and_p4_missing(tmp_path):
    ok = lean_pin.read_pin(lean_tree(tmp_path / "ok", checkout=V32))
    assert lean_pin.pin_findings(ok) == ([], [])
    p2 = lean_pin.read_pin(lean_tree(tmp_path / "p2", lake_rev="v4.34.1", checkout=V32))
    assert any(f.startswith("P2:") and "v4.34.1" in f for f in lean_pin.pin_findings(p2)[0])
    p4 = lean_pin.read_pin(lean_tree(tmp_path / "p4", checkout=V34))
    assert lean_pin.pin_findings(p4) == ([], []) and lean_pin.checkout_finding(p4).startswith("P4:")
    assert lean_pin.checkout_finding(ok) is None
    missing = lean_pin.read_pin(lean_tree(tmp_path / "fresh"))
    findings, notices = lean_pin.pin_findings(missing)
    assert findings == [] and notices == [lean_pin.NOT_BUILT]  # a fresh clone: pin known, Mathlib not built
    assert lean_pin.checkout_finding(missing) is None
    broken = lean_tree(tmp_path / "broken")
    (broken / "lakefile.toml").write_text("name = \n")
    assert any("does not parse" in f for f in lean_pin.pin_findings(lean_pin.read_pin(broken))[0])


@pytest.mark.parametrize("text", ["{not json", "[]", '{"packages": [1]}'])
def test_an_unreadable_manifest_is_a_p3_finding_not_no_mathlib(tmp_path, text):
    lean = lean_tree(tmp_path / "m", checkout=V32)
    (lean / "lake-manifest.json").write_text(text)
    with pytest.raises(lean_pin.ManifestError):
        lean_pin.manifest_mathlib(lean)
    pin = lean_pin.read_pin(lean)
    assert pin["uses_mathlib"] and pin["manifest_error"]
    assert any(f.startswith("P3:") and "lake-manifest.json" in f for f in lean_pin.pin_findings(pin)[0])
    (lean / "lake-manifest.json").unlink()
    assert lean_pin.manifest_mathlib(lean) is None  # absent is not an error


def test_lean_pin_script_exit_codes(tmp_path):
    def run(root):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "lean_pin.py")], capture_output=True, text=True,
                              env={**os.environ, "MATHAGENTS_ROOT": str(root)})
    lean_tree(tmp_path / "a")
    assert run(tmp_path / "a").returncode == 0
    lean_tree(tmp_path / "b", input_rev="v4.34.1")
    assert run(tmp_path / "b").returncode == 1
    (tmp_path / "c").mkdir()
    assert run(tmp_path / "c").returncode == 2


# --- LV1: G-KERNEL checks the Lean that ran ---------------------------------------------------------------

def shim_bin(tmp: Path, version: str) -> Path:
    """A `lean` that reports ``version`` and a `lake` that records that it ran (and fails)."""
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    (bin_dir / "lean").write_text(f"#!/bin/sh\necho 'Lean (version {version}, shim, commit 0, Release)'\n")
    (bin_dir / "lake").write_text(f"#!/bin/sh\ntouch {tmp / 'lake-ran'}\nexit 1\n")
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    return bin_dir


def gkernel(tmp: Path, root: Path, bin_dir: Path, **env: str) -> subprocess.CompletedProcess:
    # HOME has no ~/.elan, so the gate's PATH prefix adds nothing and the shims answer
    e = {"PATH": f"{bin_dir}:{Path(sys.executable).parent}:/usr/bin:/bin", "HOME": str(tmp), "MATHAGENTS_ROOT": str(root),
         **env}
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "proof_integrity.py"), "--no-report"],
                          capture_output=True, text=True, env=e, cwd=root)


def test_gkernel_fails_without_building_when_another_lean_runs(tmp_path):
    root = tmp_path / "inst"
    lean_tree(root, toolchain=V34, rev=REV34, lake_rev="v4.34.1", input_rev="v4.34.1")
    r = gkernel(tmp_path, root, shim_bin(tmp_path, "4.32.1"))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "the Lean that ran is 4.32.1" in r.stdout and "pins 4.34.1" in r.stdout
    assert not (tmp_path / "lake-ran").exists()  # nothing was built under the wrong toolchain


def test_gkernel_builds_when_the_lean_that_runs_is_the_pin(tmp_path):
    root = tmp_path / "inst"
    lean_tree(root, toolchain=V34, rev=REV34, lake_rev="v4.34.1", input_rev="v4.34.1")
    r = gkernel(tmp_path, root, shim_bin(tmp_path, "4.34.1"))
    assert "toolchain:" not in r.stdout and (tmp_path / "lake-ran").exists()


def test_gkernel_reports_a_p2_mismatch(tmp_path):
    root = tmp_path / "inst"
    lean_tree(root, toolchain=V34, rev=REV34, lake_rev="v4.34.1", input_rev="v4.32.1")
    r = gkernel(tmp_path, root, shim_bin(tmp_path, "4.34.1"))
    assert r.returncode == 1 and "config: P2:" in r.stdout


def installed_toolchains() -> list[str]:
    d = Path.home() / ".elan" / "toolchains"
    return sorted(p.name.replace("---", ":").replace("--", "/") for p in d.iterdir()) if d.is_dir() else []


def test_gkernel_under_a_real_elan_override_fails_naming_both_versions():
    """The handoff's done-when: ELAN_TOOLCHAIN set to another installed release gives FAIL naming both."""
    pin = (ROOT / "lean" / "lean-toolchain").read_text().strip()
    other = next((t for t in installed_toolchains() if t.startswith("leanprover/lean4:v") and t != pin), None)
    if other is None or not shutil.which("elan", path=str(Path.home() / ".elan" / "bin")):
        pytest.skip("needs elan with a second installed Lean release")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "proof_integrity.py"), "--no-report"],
                       capture_output=True, text=True, cwd=ROOT / "lean",
                       env={**os.environ, "ELAN_TOOLCHAIN": other, "MATHAGENTS_ROOT": str(ROOT)}, timeout=120)
    assert r.returncode == 1, r.stdout + r.stderr
    assert lean_pin.release(other) in r.stdout and lean_pin.release(pin) in r.stdout
    assert "build, replay and envelope were not run" in r.stdout


def test_every_report_reader_refuses_a_report_from_another_lean(tmp_path):
    (tmp_path / "reports" / "kernel").mkdir(parents=True)
    report = tmp_path / "reports" / "kernel" / "latest.json"
    report.write_text(json.dumps({"verdict": "PASS", "toolchain_pin": V34,
                                  "lean_version": "Lean (version 4.32.1, x, commit 0, Release)"}))
    kernel, problem = validate_dossier.load_kernel(tmp_path, report)
    assert kernel is None and "another Lean" in problem
    report.write_text(json.dumps({"verdict": "PASS", "toolchain_pin": V34}))  # no lean_version: not a pass
    kernel, problem = validate_dossier.load_kernel(tmp_path, report)
    assert kernel is None and "lacks lean_version" in problem


def test_the_snapshot_check_refuses_a_run_under_another_lean(tmp_path):
    snap = tmp_path / "kernel-snapshot.json"
    snap.write_text(json.dumps({"verdict": "PASS", "commit": "abc", "source_sha256": "0", "dirty": False,
                                "lean_version": "Lean (version 4.32.1, x)", "toolchain_pin": V34, "declarations": [{}]}))
    errs: list[str] = []
    dossier_structure.check_snapshot("demo", snap, None, None, errs)
    assert any("another Lean" in e for e in errs)


# --- LV2: the name index and a Mathlib checkout built for another toolchain ------------------------------

def test_build_name_index_refuses_a_missing_or_mismatched_checkout(tmp_path):
    def run(root):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "build_name_index.py")], capture_output=True,
                              text=True, env={**os.environ, "MATHAGENTS_ROOT": str(root)})
    lean_tree(tmp_path / "fresh")
    r = run(tmp_path / "fresh")
    assert r.returncode == 1 and "Mathlib not built" in r.stdout
    lean_tree(tmp_path / "other", checkout=V34)
    r = run(tmp_path / "other")
    assert r.returncode == 1 and "P4:" in r.stdout


def test_load_index_refuses_a_checkout_built_for_another_toolchain(tmp_path):
    lean = lean_tree(tmp_path, checkout=V34)
    index = tmp_path / "name-index.txt"
    index.write_text(f"{build_name_index.header_for(lean)} count=1\nNat.add\n")
    names, problem = build_name_index.load_index(index, lean)
    assert names is None and "P4:" in problem
    (lean / ".lake" / "packages" / "mathlib" / "lean-toolchain").write_text(V32 + "\n")
    assert build_name_index.load_index(index, lean) == ({"Nat.add"}, None)


# --- LV3, LV11: the vendored rules and the agents that point to them ---------------------------------------

def agent_rules() -> dict[str, list[str]]:
    import re
    doc = (ROOT / "docs" / "lean-version-governance.md").read_text()
    rows = re.findall(r"^\| `@([\w-]+)` \| [^|]+ \| (R[\d, R]+) \|$", doc, re.M)
    return {a: [r.strip() for r in rules.split(",")] for a, rules in rows}


def test_a_fresh_instance_has_the_vendored_rules(instance):
    rel = "docs/lean-version-governance.md"
    assert rel in _harness_files.VENDORED
    assert (instance / rel).read_bytes() == (ROOT / rel).read_bytes()
    assert rel in json.loads((instance / cli.LOCK).read_text())["files"]


def test_every_exported_agent_points_to_the_rules_and_names_its_own(instance):
    table = agent_rules()
    names = cli.exported_names(cli.instance_config(instance))
    assert set(names) <= set(table), "every pipeline agent needs a row in the per-agent table"
    assert "mathagents run lean_pin" in (instance.parent.parent / ".github" / "agents" / "lean-prover.agent.md").read_text()
    for name in names:
        body = (instance.parent.parent / ".github" / "agents" / f"{name}.agent.md").read_text()
        assert "docs/lean-version-governance.md" in body, name
        assert "scripts/lean_pin.py" not in body, name  # any gate command was rewritten for the consumer
        for rule in table[name]:
            assert rule in body, (name, rule)


def test_lean_informalization_carries_the_lean_version_rule():
    body = (ROOT / ".github" / "agents" / "lean-informalization.agent.md").read_text()
    notes = body[body.index("## Project-Specific Notes"):]
    assert "docs/lean-version-governance.md" in notes and "toolchain_pin" in notes and "Stamp each narration" in notes


# --- LV5, LV6: doctor's stale-version scan ----------------------------------------------------------------

@pytest.mark.parametrize("release", ["4.32.1", "4.34.1"])
def test_shipped_text_names_no_version_but_the_pin_under_either_pin(release):
    """Every vendored doc and pipeline agent is clean under both pins (D8/D9 carry the harness-pin marker)."""
    files = [f for f in _harness_files.VENDORED if f.endswith(".md")] + list(_harness_files.AGENT_FILES)
    hits = {f: lean_pin.stale_versions((ROOT / f).read_text(), release) for f in files}
    assert not {f: h for f, h in hits.items() if h}


def test_stale_versions_honours_the_harness_pin_marker():
    text = "Pin Lean v4.34.1. <!-- harness-pin -->\nLean and Mathlib are pinned at v4.34.1; see .claude/skills\n"
    assert lean_pin.stale_versions(text, "4.32.1") == [(2, "v4.34.1")]
    assert lean_pin.stale_versions(text, "4.34.1") == []


def test_doctor_warns_on_stale_version_text_without_failing(instance):
    r = mathagents("doctor", cwd=instance)
    assert "version text" not in r.stdout, r.stdout
    agent = instance.parent.parent / ".github" / "agents" / "lean-prover.agent.md"
    agent.write_text(agent.read_text() + "\n- Lean and Mathlib are pinned at v4.34.1; see `.claude/skills`.\n")
    r = mathagents("doctor", cwd=instance)
    assert "lean-prover.agent.md" in r.stdout and "names v4.34.1, not the pin 4.32.1" in r.stdout
    assert "warning(s)" in r.stdout


def test_doctor_reports_pin_problems(instance):
    assert "pin:      v4.32.1: verified" in mathagents("doctor", cwd=instance).stdout
    (instance / "lean" / ".lake" / "packages" / "mathlib" / "lean-toolchain").write_text(V34)
    r = mathagents("doctor", cwd=instance)
    assert "warning: lean pin: P4:" in r.stdout  # a stale local build warns
    lean_tree(instance, lake_rev="v4.34.1")  # P2 != manifest inputRev: the pin is unknown
    r = mathagents("doctor", cwd=instance)
    assert r.returncode == 1 and "- lean pin: P2:" in r.stdout


def test_doctor_notes_a_mathlib_not_built_without_failing_on_it(instance):
    shutil.rmtree(instance / "lean" / ".lake")
    r = mathagents("doctor", cwd=instance)
    assert "Mathlib not built" in r.stdout and "lean pin:" not in r.stdout.split("note:")[0].split("pin:")[-1]


# --- LV7: the bump tools ship and run from the harness -----------------------------------------------------

def test_bump_tools_and_guide_are_shipped():
    for rel in _harness_files.BUMP_TOOLS + ("docs/lean-toolchain-upgrade.md",):
        assert rel in _harness_files.ALL and (ROOT / rel).is_file()


def test_bump_trial_defaults_to_the_instance_and_refuses_a_copy_inside_it(instance, tmp_path):
    subprocess.run(["git", "init", "-q", str(instance.parent.parent)], check=True)
    r = mathagents("bump", "trial", "--to", str(instance / "trial"), "--tag", "v4.34.1", cwd=instance)
    assert r.returncode == 2 and "outside the instance" in r.stdout
    r = mathagents("bump", "trial", "--to", str(instance.parent.parent / "elsewhere"), "--tag", "v4.34.1", cwd=instance)
    assert r.returncode == 2 and "outside the instance" in r.stdout  # the repository (workspace) is fenced too
    r = mathagents("bump", "trial", "--to", str(tmp_path / "a"), "--to", str(instance / "x"), "--tag", "v4.34.1",
                   cwd=instance)  # bump_trial.sh would use the last --to: a repeated option is refused
    assert r.returncode == 2 and "more than once" in r.stdout and not (instance / "x").exists()
    r = mathagents("bump", "trial", "--to", "trial", "--tag", "v4.34.1", cwd=instance / "lean")  # relative to cwd
    assert r.returncode == 2 and "outside the instance" in r.stdout
    (instance / "lean" / "lakefile.toml").unlink()  # the trial reaches bump_trial.sh with --from <instance>/lean
    r = mathagents("bump", "trial", "--to", str(tmp_path / "trial"), "--tag", "v4.34.1", cwd=instance)
    assert r.returncode == 2 and f"{instance / 'lean'} has no lakefile.toml" in r.stderr


def test_a_wheel_only_install_runs_the_bump_tools(tmp_path, instance):
    r = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "-q",
                        "-w", str(tmp_path / "w"), str(ROOT)], capture_output=True, text=True)
    if r.returncode != 0 and "No module named" in r.stderr:
        pytest.skip("setuptools or wheel unavailable")
    assert r.returncode == 0, r.stderr[-2000:]
    site = tmp_path / "site"
    zipfile.ZipFile(next((tmp_path / "w").glob("mathagents-*.whl"))).extractall(site)
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(site), "HOME": str(Path.home())}
    r = subprocess.run([sys.executable, "-m", "mathagents.cli", "bump", "statement-types", "--help"],
                       cwd=instance, capture_output=True, text=True, env=env)
    assert r.returncode == 0 and "dump" in r.stdout, r.stdout + r.stderr
    (instance / "lean" / "lakefile.toml").unlink()
    r = subprocess.run([sys.executable, "-m", "mathagents.cli", "bump", "trial", "--to", str(tmp_path / "t"),
                        "--tag", "v4.34.1"], cwd=instance, capture_output=True, text=True, env=env)
    assert r.returncode == 2 and "has no lakefile.toml" in r.stderr, r.stdout + r.stderr


def test_the_guide_lists_the_decision_and_gfid_gates_before_apply():
    guide = (ROOT / "docs" / "lean-toolchain-upgrade.md").read_text()
    decision, gfid, apply = (guide.index("Consumer decision gate"), guide.index("G-FID re-approval gate"),
                             guide.index("Apply the patch"))
    assert decision < gfid < apply and "--lean-dir" in guide


# --- LV8: pin stamps ---------------------------------------------------------------------------------------

def test_schemas_accept_pin_stamps():
    stamp = {"toolchain_pin": V32, "mathlib_rev": REV32}
    schemas = validate_dossier.load_schemas(ROOT)
    jsonschema.validate({"schema_version": 1, "slug": "d", "lean_namespace": "D", "declarations": [
        {"decl": "D.t", "statement_fingerprint": "1", "status": "approved", "approver": "J", "date": "2026-10-05",
         **stamp}]}, schemas["fid"])
    jsonschema.validate({"schema_version": 1, "slug": "d", "records": [
        {"id": "AX-1", "decl": "D.t", "old_fingerprint": "1", "new_fingerprint": "2", "change": "other",
         "description": "x", **stamp}]}, schemas["gax"])
    jsonschema.validate({"schema_version": 1, "slug": "d", "lean_namespace": "D", "counterexamples": [
        {"id": "CX-1", "decl": "D.t", "statement_fingerprint": "1", "method": "manual", "description": "x",
         **stamp}]}, schemas["cx"])


def test_validator_warns_on_a_fidelity_or_gax_stamp_from_an_earlier_pin_but_not_on_the_cx_log(tmp_path):
    lean_tree(tmp_path, toolchain=V34, rev=REV34, lake_rev="v4.34.1", input_rev="v4.34.1")
    d = tmp_path / "reports" / "dossiers" / "demo"
    d.mkdir(parents=True)
    old = {"toolchain_pin": V32, "mathlib_rev": REV32}
    (d / "fidelity.json").write_text(json.dumps({"declarations": [{"decl": "D.t", **old},
                                                                  {"decl": "D.u", "toolchain_pin": V34}]}))
    (d / "gax.json").write_text(json.dumps({"records": [{"id": "AX-1", "toolchain_pin": V32}]}))
    (d / "counterexamples.json").write_text(json.dumps({"counterexamples": [{"id": "CX-1", **old}]}))
    warns = validate_dossier.stamp_warnings(tmp_path, ["demo"])
    assert sum("D.t" in w for w in warns) == 2 and not any("D.u" in w for w in warns)
    assert any("AX-1" in w for w in warns) and not any("CX-1" in w for w in warns)


# --- LV9: the register of verified toolchains --------------------------------------------------------------

def test_the_register_is_shipped_and_names_its_evidence():
    entries = cli.verified_toolchains()
    assert _harness_files.VERIFIED_TOOLCHAINS in _harness_files.ALL
    assert {(e["toolchain"], e["mathlib_rev"]) for e in entries} >= {(V32, REV32), (V34, REV34)}
    assert all(e.get("evidence") and e.get("harness_version") and e.get("verified") for e in entries)


def test_pin_verification():
    pin = {"toolchain": V32, "mathlib_rev": REV32, "uses_mathlib": True}
    line, ok, _ = cli.pin_verification(pin)
    assert ok and line.startswith("v4.32.1: verified")
    assert not cli.pin_verification({**pin, "mathlib_rev": "0" * 40})[1]
    line, ok, _ = cli.pin_verification({**pin, "toolchain": "leanprover/lean4:v4.99.0"})
    assert not ok and "NOT verified" in line


def test_status_shows_the_pin_and_keeps_its_exit_code(instance):
    r = mathagents("status", cwd=instance)
    assert r.returncode == 0 and "pin v4.32.1: verified" in r.stdout
    r = mathagents("status", cwd=instance, MATHAGENTS_ENABLED="0")
    assert r.returncode == 3 and "pin v4.32.1: verified" in r.stdout


# --- LV10: the machine probe records the instance's Lean ---------------------------------------------------

def test_probe_never_runs_a_toolchain_that_is_not_installed(tmp_path, monkeypatch):
    lean_tree(tmp_path / "inst", toolchain="leanprover/lean4:v4.99.0")
    monkeypatch.setattr(probe_machine, "ROOT", tmp_path / "inst")
    monkeypatch.delenv("ELAN_TOOLCHAIN", raising=False)
    elan_bin = tmp_path / "elan" / "bin"
    elan_bin.mkdir(parents=True)
    got = probe_machine.lean_versions(elan_bin)
    assert got["lean_version"] is None and "not installed" in got["lean_version_source"]


def test_probe_runs_lean_in_the_instance_and_records_an_override(tmp_path, monkeypatch):
    lean_tree(tmp_path / "inst", toolchain=V34)
    monkeypatch.setattr(probe_machine, "ROOT", tmp_path / "inst")
    elan = tmp_path / "elan"
    (elan / "toolchains" / "leanprover--lean4---v4.32.1").mkdir(parents=True)
    (elan / "bin").mkdir()
    (elan / "bin" / "lean").write_text("#!/bin/sh\necho \"Lean (version 4.32.1, cwd $(pwd))\"\n")
    (elan / "bin" / "lean").chmod(0o755)
    monkeypatch.setenv("ELAN_TOOLCHAIN", V32)
    got = probe_machine.lean_versions(elan / "bin")
    assert "4.32.1" in got["lean_version"] and str((tmp_path / "inst" / "lean").resolve()) in got["lean_version"]
    assert got["elan_toolchain_override"] == V32 and "override" in got["lean_version_source"]


# --- D39: a returned Lean draft is scanned before it runs ----------------------------------------------------

def scan(text: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "scan_lean_draft.py")], input=text, text=True,
                          capture_output=True)


@pytest.mark.parametrize("line", ['#eval IO.println "x"', "run_cmd pure ()", "initialize x : Unit ← pure ()",
                                  "example : 2 = 2 := by decide +native", "@[extern \"f\"] opaque f : Nat",
                                  "unsafe def g : Nat := 0", "example : True := by run_tac pure ()",
                                  "example : True := by_elab pure ()", "@[command_elab evil] def e := 0",
                                  "@[term_elab foo] def t := 0", "@[tactic bar] def u := 0",
                                  "@[simproc] def s := 0", "@[init] def i := 0",
                                  "def f := IO.Process.run {cmd := \"x\"}", "def g := Lean.Elab.Command.liftCoreM",
                                  "import Lean.Elab"])
def test_scan_lean_draft_flags_code_that_runs_at_check_time(line):
    r = scan(f"theorem t : True := trivial\n{line}\n")
    assert r.returncode == 1 and ":2:" in r.stdout and "@security" in r.stdout, r.stdout


def test_scan_lean_draft_allows_open_markers_and_ignores_comments_and_strings():
    r = scan('-- #eval in a comment\n/- run_cmd -/\ntheorem s : 1 = 1 := sorry\ndef m : String := "#eval"\n'
             '@[simp] theorem t : 1 = 1 := rfl\n@[simp, norm_cast] theorem u : 2 = 2 := rfl\nimport Mathlib.Tactic\n')
    assert r.returncode == 0 and "clean" in r.stdout, r.stdout


def scan_args(*args: str, text: str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "scan_lean_draft.py"), *args], input=text or "",
                          text=True, capture_output=True, env=env)


DRAFTS = ("theorem t : True := trivial\n#eval IO.println \"x\"\nrun_cmd pure ()\n",  # findings
          "theorem s : 1 = 1 := sorry\n-- #eval in a comment\n")                      # clean


@pytest.mark.parametrize("draft,expected", zip(DRAFTS, (1, 0)))
def test_scan_lean_draft_reads_stdin_from_dash_exactly_as_from_a_file(tmp_path, draft, expected):
    """F1: `-` reads the draft from stdin, so a researcher scans it with no scratch file; the verdict, the
    findings and the exit code are those of the path mode (only the label differs)."""
    f = tmp_path / "Draft.lean"
    f.write_text(draft, encoding="utf-8")
    by_path, by_dash, by_none = scan_args(str(f)), scan_args("-", text=draft), scan_args(text=draft)
    assert by_path.returncode == by_dash.returncode == by_none.returncode
    assert by_dash.stdout == by_none.stdout == by_path.stdout.replace(str(f), "<stdin>")
    assert by_dash.returncode == expected, by_dash.stdout


def test_scan_lean_draft_path_mode_refusals_are_unchanged(tmp_path):
    missing = scan_args(str(tmp_path / "absent.lean"))
    assert missing.returncode == 2 and "cannot read the draft" in missing.stdout
    bad = tmp_path / "Bad.lean"
    bad.write_bytes(b"theorem t : True := trivial\n\xff\n")
    assert scan_args(str(bad)).returncode == 2
    assert scan_args("-", text=None).returncode == 0  # an empty draft has no finding
    twice = scan_args("-", "-", text=DRAFTS[1])
    assert twice.returncode == 2 and "only once" in twice.stdout


def test_scan_lean_draft_mixes_files_and_stdin(tmp_path):
    clean = tmp_path / "Clean.lean"
    clean.write_text(DRAFTS[1], encoding="utf-8")
    r = scan_args(str(clean), "-", text=DRAFTS[0])
    assert r.returncode == 1 and "<stdin>:2: `#eval`" in r.stdout and str(clean) not in r.stdout, r.stdout


def test_mathagents_run_passes_stdin_to_scan_lean_draft():
    """`mathagents run scan_lean_draft -` (the form the rendered agents use) hands the piped draft to the scan."""
    env = dict(os.environ, MATHAGENTS_ENABLED="1", PYTHONPATH=str(ROOT))
    for draft, rc in ((DRAFTS[0], 1), (DRAFTS[1], 0)):
        r = subprocess.run([sys.executable, "-m", "mathagents.cli", "run", "scan_lean_draft", "-"], input=draft,
                           text=True, capture_output=True, cwd=ROOT, env=env)
        assert r.returncode == rc, r.stdout + r.stderr
        assert ("<stdin>:2: `#eval`" in r.stdout) == (rc == 1)


def test_the_orchestrator_and_lean_prover_must_scan_drafts():
    orch = (ROOT / ".github" / "agents" / "orchestrator.agent.md").read_text()
    prover = (ROOT / ".github" / "agents" / "lean-prover.agent.md").read_text()
    assert "scripts/scan_lean_draft.py" in orch and "argument list" in orch and "resolve it" in orch
    assert "scripts/scan_lean_draft.py" in prover


def test_every_agent_that_pipes_drafts_to_lean_scans_them_first():
    for name in ("lean-prover", "statement-formalizer", "counterexample-hunter"):
        body = (ROOT / ".github" / "agents" / f"{name}.agent.md").read_text()
        assert "lake env lean --stdin" in body and "scripts/scan_lean_draft.py" in body, name


# --- validator grammars in the agent bodies, and the orchestrator's re-validation duties (2026-10-06 trial) ------

def _fenced(text: str) -> list[str]:
    import re
    return re.findall(r"```[a-z]*\n(.*?)```", text, re.S)


def test_logic_articulator_examples_agree_with_check_derivations(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import dossier_structure
    body = (ROOT / ".github" / "agents" / "logic-articulator.agent.md").read_text()
    assert "check_derivations" in body and "NODE_LEAN" in body
    good = next(b for b in _fenced(body) if "Nat.mul_zero" in b)
    bad = next(b for b in _fenced(body) if "Lean: none" in b)
    f = tmp_path / "derivations.md"
    f.write_text(good, encoding="utf-8")
    errs: list[str] = []
    dossier_structure.check_derivations("x", f, "classical-hol", errs)
    assert errs == []
    header = good.splitlines()[:3]
    expected = {"1.": "cites step 0, which does not exist", "4.": "cites step 14, which is not earlier",
                "5)": "step not in the '<n>. <formula>  [<rule or lemma>]' form", "6.": "step 6 names no rule or lemma"}
    for line in bad.splitlines():
        if line.startswith("## Node:"):
            continue
        num = int(line.split(".")[0].split(")")[0])
        fillers = [f"{i}. P{i}               [hyp]" for i in range(1, num)]  # earlier steps, never the bad one's number
        f.write_text("\n".join(header + fillers + [line]) + "\n", encoding="utf-8")
        errs = []
        dossier_structure.check_derivations("x", f, "classical-hol", errs)
        want = expected[line.split()[0]]
        assert len(errs) == 1 and want in errs[0], (line, errs)


def test_node_header_rule_matches_g_name():
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_lean_bindings as b
    inline = "## Node: A1   Lean: MathAgents.OddSum.sum_first_odds (inline step A1)"
    assert b.clean(b.NODE_LEAN.match(inline).group(1)) == "MathAgents.OddSum.sum_first_odds"
    assert b.clean(b.NODE_LEAN.match("## Node: A1   Lean: none").group(1)) == "none"
    for name in ("logic-articulator", "tactic-planner"):
        body = (ROOT / ".github" / "agents" / f"{name}.agent.md").read_text()
        assert "enclosing declaration" in body and "Lean: none" in body and "NODE_LEAN" in body, name


def test_orchestrator_card_grammar_examples_agree_with_check_card():
    sys.path.insert(0, str(ROOT / "scripts"))
    import dossier_structure as d
    logics, engines, domains = d.registry_ids(ROOT)
    right = d.card_fields("- **Domain:** competition\n  (elementary number theory)\n- **Object logic:** classical-hol\n"
                          "- **Engine:** lean-builtin\n")
    assert right["Domain"] in domains and right["Object logic"] in logics and right["Engine"] in engines
    wrong = {"Domain": "competition (elementary number theory)", "Object logic": "classical HOL (the default)",
             "Engine": "Lean"}
    assert wrong["Domain"] not in domains and wrong["Object logic"] not in logics and wrong["Engine"] not in engines
    for f in (".github/agents/orchestrator.agent.md", ".claude/agents/orchestrator.md"):
        text = (ROOT / f).read_text()
        for field, value in wrong.items():
            assert f"`- **{field}:** {value}`" in text, (f, field)
        assert "`- **Domain:** competition`" in text and "card_fields" in text and "check_card" in text, f


def test_orchestrator_supplies_run_context_and_revalidates_after_every_write():
    texts = {f: (ROOT / f).read_text() for f in (".github/agents/orchestrator.agent.md", ".claude/agents/orchestrator.md",
                                                 "brief.json", "docs/baseagent-integration-plan.md")}
    for f, text in texts.items():
        assert "mathagents status" in text and "lean_docs" in text, f
        assert "--require-fid <slug>" in text and "check_lean_bindings" in text and "next stage" in text, f
        assert "authoring agent" in text, f


def test_heredoc_form_scans_before_lean_and_guards_the_delimiter():
    """F1 (@security finding at the 2026-10-07T00:49Z UTC overwrite review; fixed in 9b1b89a): one quoted heredoc feeds the scan and, only on a clean scan, Lean; the delimiter
    is fresh per draft and checked against the draft, since a draft line equal to it would run as shell."""
    for name in ("lean-prover", "statement-formalizer", "counterexample-hunter"):
        body = (ROOT / ".github" / "agents" / f"{name}.agent.md").read_text()
        assert "draft | python3 scripts/scan_lean_draft.py - && (cd lean && draft | lake env lean --stdin)" in body, name
        assert "cat <<'MATHAGENTS_DRAFT_<6 random hex>'" in body, name  # a placeholder, never a literal to copy
        assert "no line of the draft equals the delimiter" in body and "MATHAGENTS_DRAFT_3f9c1a" not in body, name


def test_logic_articulator_states_step_ref_as_the_code_reads_it():
    """CA-036: only a one-digit run glued to a letter is skipped; `A12` cites step 2, and a lemma's name is not scanned."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import dossier_structure as d
    assert d.STEP_REF.findall("∧E1 A1") == [] and d.STEP_REF.findall("A12") == ["2"]
    assert d.STEP_REF.findall("s5") == ["5"] and d.STEP_REF.findall("step 5") == ["5"]
    body = (ROOT / ".github" / "agents" / "logic-articulator.agent.md").read_text()
    assert "`A12` and `x_12` cite step 2" in body and "a lemma or node name never counts" in body


def test_scan_lean_draft_help_prints_usage_instead_of_reading_a_file(tmp_path):
    for flag in ("--help", "-h"):
        r = scan_args(flag)
        assert r.returncode == 0 and "Usage:" in r.stdout and "cannot read" not in r.stdout, flag
    named = tmp_path / "--help"
    named.write_text("#eval 1\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "scan_lean_draft.py"), "./--help"], cwd=tmp_path,
                       text=True, capture_output=True)
    assert r.returncode == 1 and "`#eval`" in r.stdout, r.stdout


V025_REFUSALS = ("@[command_elab evil] def e := 0", "@[term_elab foo] def t := 0", "@[tactic bar] def u := 0",
                 "@[simproc] def s := 0", "@[dsimproc] def d := 0", "@[init] def i := 0", "@[env_linter] def l := 0",
                 "@[builtin_term_elab foo] def b := 0", "example : True := by run_tac pure ()",
                 "example : True := by_elab pure ()", "import Lean", "import Lean.Elab",
                 "def f := IO.Process.run {cmd := \"x\"}", "def g := IO.FS.writeFile \"a\" \"b\"",
                 "def h := Lean.Elab.Command.liftCoreM")


@pytest.mark.parametrize("line", V025_REFUSALS)
@pytest.mark.parametrize("mode", ("dash", "path"))
def test_v025_refusals_hold_in_stdin_and_path_mode(tmp_path, line, mode):
    """The PR #18 (v0.2.5) additions are refused on `-` exactly as on a path."""
    draft = f"theorem t : True := trivial\n{line}\n"
    if mode == "dash":
        r = scan_args("-", text=draft)
    else:
        f = tmp_path / "D.lean"
        f.write_text(draft, encoding="utf-8")
        r = scan_args(str(f))
    assert r.returncode == 1 and ":2:" in r.stdout, (mode, line, r.stdout)
