"""The importable module (D35): harness manifest, CLI init/sync/export on an instance, the wheel, and the
append-only base comparison for an instance in a subdirectory of a git work tree. No Lean needed."""
from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mathagents import _harness_files, _scripts, cli, config  # noqa: E402
from api_fixtures import orchestrator  # noqa: E402

LAKEFILE = """name = "demo"
[[require]]
name = "mathlib"
git = "https://github.com/leanprover-community/mathlib4"
rev = "v4.34.1"
[[lean_lib]]
name = "Demo"
[[lean_lib]]
name = "DemoWIP"
"""


def mathagents(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(ROOT), "HOME": str(Path.home())}
    return subprocess.run([sys.executable, "-m", "mathagents.cli", *args], cwd=cwd, capture_output=True, text=True,
                          env=env)


@pytest.fixture
def instance(tmp_path):
    ws = tmp_path / "ws"
    (ws / "lean").mkdir(parents=True)  # placeholder so the instance can sit in a subdirectory
    orchestrator(ws / ".github" / "agents")
    r = mathagents("init", str(ws / "Projects" / "Demo"), "--agents-to", "../../.github/agents", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    r = mathagents("sync", "--write", cwd=ws / "Projects" / "Demo")  # init never exports agents (H2)
    assert r.returncode == 0, r.stdout + r.stderr
    return ws / "Projects" / "Demo"


def test_every_harness_file_exists_in_the_checkout():
    missing = [f for f in _harness_files.ALL if not (ROOT / f).is_file()]
    assert not missing


def test_every_gate_script_is_shipped():
    """A gate script the package runs or imports must be in the wheel."""
    shipped = {Path(f).name for f in _harness_files.GATE_SCRIPTS}
    assert set(_scripts.IN_PROCESS) <= shipped


def test_the_harness_digest_covers_exactly_the_shipped_gate_files():
    sys.path.insert(0, str(ROOT / "scripts"))
    import instance_root

    assert tuple(f"scripts/{f}" for f in instance_root.GATE_FILES) == _harness_files.GATE_SCRIPTS


def test_init_vendors_seeds_and_locks(instance):
    lock = json.loads((instance / cli.LOCK).read_text())
    for rel in _harness_files.VENDORED:
        assert (instance / rel).read_bytes() == (ROOT / rel).read_bytes()
        assert rel in lock["files"]
    allow = json.loads((instance / "references" / "axiom-allowlist.json").read_text())
    assert allow["approved_axioms"] == [] and allow["approvals"] == []
    assert "references/axiom-allowlist.json" not in lock["files"]  # instance-owned, never synced
    assert len([k for k in lock["files"] if k.endswith(".agent.md")]) == len(_harness_files.AGENTS)


def test_sync_is_idempotent_and_refuses_local_edits(instance):
    assert mathagents("sync", cwd=instance).returncode == 0
    vendored = instance / "references" / "object-logics.json"
    vendored.write_text(vendored.read_text() + "\n")
    r = mathagents("sync", "--write", cwd=instance)
    assert r.returncode == 1 and "conflict  references/object-logics.json" in r.stdout
    assert vendored.read_text().endswith("\n\n")  # not overwritten
    r = mathagents("sync", "--write", "--overwrite", "references/object-logics.json", cwd=instance)
    assert r.returncode == 0, r.stdout
    assert vendored.read_bytes() == (ROOT / "references" / "object-logics.json").read_bytes()


def test_sync_updates_an_unedited_file_the_harness_changed(instance):
    lock_path = instance / cli.LOCK
    target = instance / "docs" / "kernel-gate.md"
    target.write_text("older harness version\n")  # as if vendored by an older release
    lock = json.loads(lock_path.read_text())
    lock["files"]["docs/kernel-gate.md"] = cli.sha(target.read_bytes())
    lock_path.write_text(json.dumps(lock))
    r = mathagents("sync", "--write", cwd=instance)
    assert r.returncode == 0 and "update    docs/kernel-gate.md" in r.stdout
    assert target.read_bytes() == (ROOT / "docs" / "kernel-gate.md").read_bytes()


def test_agents_are_rewritten_for_the_instance(instance):
    (instance / "lean").mkdir()
    (instance / "lean" / "lakefile.toml").write_text(LAKEFILE)
    marker = instance / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# team = "baseAgent"', 'team = "baseAgent"'))
    assert mathagents("sync", "--write", cwd=instance).returncode == 0
    agents = instance.parent.parent / ".github" / "agents"
    for name in _harness_files.AGENTS:
        text = (agents / f"{name}.agent.md").read_text()
        assert text.startswith("---\n") and "<!-- mathagents-export: agent=" in text
        assert text.split("\n---\n", 1)[1].lstrip().startswith("<!-- mathagents-export")  # after the front matter
        assert "python3 scripts/" not in text and "bash scripts/" not in text
        assert "MathAgentsWIP" not in text and "MathAgents." not in text
        assert "— baseAgent" in text.splitlines()[1] or "name:" not in text.splitlines()[1]
    assert "DemoWIP" in (agents / "lean-prover.agent.md").read_text()
    # D41: the auditor runs G-KERNEL unrecorded; the recording run (check_proof_integrity) is the orchestrator's
    assert "mathagents run proof_integrity --no-report" in (agents / "axiom-auditor.agent.md").read_text()


def test_excluded_agents_are_not_exported(tmp_path):
    marker_dir = tmp_path / "inst"
    assert mathagents("init", str(marker_dir), "--agents-to", "agents", cwd=tmp_path).returncode == 0
    marker = marker_dir / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# exclude = ["lean-informalization"]', 'exclude = ["lean-informalization"]'))
    orchestrator(marker_dir / "agents")  # init does not export agents (H2); the team has an orchestrator (M2)
    (marker_dir / "agents" / "lean-informalization.agent.md").write_text("the consumer's own copy\n")
    assert mathagents("sync", "--write", cwd=marker_dir).returncode == 0
    assert (marker_dir / "agents" / "lean-informalization.agent.md").read_text() == "the consumer's own copy\n"
    lock = json.loads((marker_dir / cli.LOCK).read_text())
    assert "agents/lean-informalization.agent.md" not in lock["files"]


def test_gates_run_from_the_harness_against_the_instance(instance):
    for args in (("run", "validate_registries"), ("run", "preferences", "check"), ("run", "validate-dossier")):
        r = mathagents(*args, cwd=instance / "references")  # found by walking up to mathagents.toml
        assert r.returncode == 0, r.stdout + r.stderr
    assert mathagents("run", "no_such_gate", cwd=instance).returncode == 2


def test_a_root_that_is_not_an_instance_fails_instead_of_passing_on_nothing(tmp_path, instance):
    (tmp_path / "empty").mkdir()
    r = mathagents("run", "--root", str(tmp_path / "empty"), "validate_dossier", cwd=tmp_path)
    assert r.returncode == 2 and "neither a mathAgents checkout nor an instance" in r.stdout
    assert mathagents("run", "--root", str(instance), "validate_dossier", cwd=tmp_path).returncode == 0


def test_snapshot_refuses_a_tree_that_is_not_an_instance(tmp_path):
    """D28's clearance: a snapshot write into another tree is test-only; D35 adds only declared instances."""
    (tmp_path / "reports" / "dossiers").mkdir(parents=True)
    env = {"PATH": "/usr/bin:/bin", "MATHAGENTS_ROOT": str(tmp_path)}
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "snapshot_kernel.py"), "demo"], capture_output=True,
                       text=True, env=env)
    assert r.returncode == 2 and "not a mathAgents instance" in r.stdout


def test_init_refuses_an_existing_instance(instance):
    assert mathagents("init", str(instance), cwd=instance).returncode == 2


def test_doctor_reports_lakefile_rule_and_lock_drift(instance):
    r = mathagents("doctor", cwd=instance)
    assert r.returncode == 1 and "no lean/lakefile.toml" in r.stdout
    (instance / "lean").mkdir()
    (instance / "lean" / "lakefile.toml").write_text(LAKEFILE)
    (instance / "lean" / "lake-manifest.json").write_text("{}")
    assert mathagents("sync", "--write", cwd=instance).returncode == 0  # agents re-rendered for Demo/DemoWIP
    r = mathagents("doctor", cwd=instance)
    assert r.returncode == 0 and "libraries Demo, DemoWIP" in r.stdout, r.stdout
    (instance / "docs" / "kernel-gate.md").write_text("edited\n")
    r = mathagents("doctor", cwd=instance)
    assert r.returncode == 1 and "docs/kernel-gate.md: missing or edited" in r.stdout


def test_workspace_pointer_selects_the_instance(instance):
    ws = instance.parent.parent
    (ws / "mathagents.toml").write_text('[workspace]\ndefault = "Projects/Demo"\n')
    assert cli.find_root(start=ws / ".github") == instance.resolve()


def test_subdirectory_instance_gets_the_append_only_comparison(tmp_path):
    """D35: an instance below a work-tree root is compared with the base, not skipped."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_dossier as vd

    repo, inst = tmp_path / "repo", tmp_path / "repo" / "Projects" / "Demo"
    log = inst / "reports" / "dossiers" / "d1" / "counterexamples.json"
    log.parent.mkdir(parents=True)
    log.write_text('{"slug": "d1", "entries": []}')
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True)  # noqa: E731
    git("init", "-q")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base")
    git("add", ".")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "log")
    ref, problem = vd.resolve_base(inst.resolve(), "HEAD")
    assert ref == "HEAD" and problem is None
    assert vd.base_record_slugs(inst.resolve(), "HEAD") == ["d1"]
    assert vd.git_base_log(inst.resolve(), "d1", "HEAD") == ({"slug": "d1", "entries": []}, None)


def test_wheel_carries_the_harness(tmp_path):
    r = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "-q",
                        "-w", str(tmp_path), str(ROOT)], capture_output=True, text=True)
    if r.returncode != 0 and "No module named" in r.stderr:
        pytest.skip("setuptools or wheel unavailable: " + r.stderr[-200:])
    assert r.returncode == 0, r.stderr[-2000:]
    names = set(zipfile.ZipFile(next(tmp_path.glob("mathagents-*.whl"))).namelist())
    for rel in _harness_files.ALL:
        assert f"mathagents/_harness/{rel}" in names, rel
    assert "mathagents/cli.py" in names
    assert not any("/operator/" in n or n.startswith("scripts/") for n in names)


def test_switch_is_on_by_default_and_a_gitignored_env_turns_it_off(tmp_path, monkeypatch):
    monkeypatch.delenv(config.ENV_KEY, raising=False)
    repo = tmp_path / "repo"
    inst = repo / "Projects" / "P"
    inst.mkdir(parents=True)
    (repo / ".git").mkdir()  # the search stops at the work-tree root
    (tmp_path / ".env").write_text("MATHAGENTS_ENABLED=0\n")  # above the repository: never read
    assert config.switch(root=inst) == config.Switch(True, "default")
    (repo / ".env").write_text("SECRET_KEY=do-not-read\n# MATHAGENTS_ENABLED=0\nexport MATHAGENTS_ENABLED=\"off\"\n")
    sw = config.switch(root=inst)
    assert not sw.enabled and sw.source == str(repo / ".env") and sw.problem is None
    (repo / ".env").write_text("MATHAGENTS_ENABLED=sometimes\n")
    sw = config.switch(root=inst)
    assert not sw.enabled and "not one of" in sw.problem  # an unrecognised value fails closed
    monkeypatch.setenv(config.ENV_KEY, "1")  # the process environment overrides .env
    assert config.switch(root=inst) == config.Switch(True, "environment")


def test_a_switched_off_gate_exits_3_never_0(instance):
    (instance / ".env").write_text("MATHAGENTS_ENABLED=false\n")
    r = mathagents("run", "validate_dossier", "--require-fid", "demo", cwd=instance)
    assert r.returncode == config.DISABLED_EXIT and "did not run" in r.stdout
    assert mathagents("status", "--root", str(instance), cwd=instance).returncode == config.DISABLED_EXIT
    (instance / ".env").write_text("MATHAGENTS_ENABLED=true\n")
    assert mathagents("status", "--root", str(instance), cwd=instance).returncode == 0


def test_doctor_flags_an_env_that_is_not_gitignored(tmp_path):
    repo = tmp_path / "repo"
    assert mathagents("init", str(repo), cwd=tmp_path).returncode == 0
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".env").write_text("MATHAGENTS_ENABLED=1\n")
    assert "is not gitignored" in mathagents("doctor", cwd=repo).stdout
    (repo / ".gitignore").write_text(".env\n")
    assert "is not gitignored" not in mathagents("doctor", cwd=repo).stdout


def test_history_walk_sees_a_subdirectory_instance(tmp_path):
    """D35 + IA-01: the per-commit walk lists changes relative to the instance, so deleting a dossier's
    records in a later commit is caught, not passed vacuously, when the instance is a subdirectory."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_dossier as vd

    repo, inst = tmp_path / "repo", tmp_path / "repo" / "Projects" / "Demo"
    d = inst / "reports" / "dossiers" / "d1"
    d.mkdir(parents=True)
    git = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *a],  # noqa: E731
                                    capture_output=True, text=True, check=True)
    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "base")
    (d / "counterexamples.json").write_text('{"slug": "d1", "entries": []}')
    git("add", ".")
    git("commit", "-q", "-m", "log")
    (d / "counterexamples.json").unlink()
    git("add", "-A")
    git("commit", "-q", "-m", "delete the log")
    errs = vd.check_history(inst.resolve(), "HEAD~2")
    assert any("d1" in e and "without a retirement tombstone" in e for e in errs), errs


def test_namespace_setting_rewrites_declaration_names_not_library_names(instance):
    """v0.2.1: `[agents] namespace` drives `MathAgents.<Slug>`; the library names still come from the lakefile."""
    (instance / "lean").mkdir()
    (instance / "lean" / "lakefile.toml").write_text(LAKEFILE)
    (instance / "lean" / "Demo.lean").write_text("")
    marker = instance / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# namespace = "ZIT"', 'namespace = "ZIT"'))
    assert mathagents("sync", "--write", cwd=instance).returncode == 0
    text = (instance.parent.parent / ".github" / "agents" / "lean-prover.agent.md").read_text()
    assert "ZIT.<Slug>" in text and "MathAgents.<Slug>" not in text and "Demo.<Slug>" not in text
    assert "DemoWIP" in text and "MathAgentsWIP" not in text
    assert "declaration namespace ZIT" in text


def test_an_invalid_namespace_is_refused(instance):
    marker = instance / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# namespace = "ZIT"', 'namespace = "ZIT\\\\1 bad"'))
    r = mathagents("sync", "--write", cwd=instance)
    assert r.returncode != 0 and "not a Lean dotted identifier" in (r.stdout + r.stderr)


def test_init_never_exports_agents_and_records_settings(tmp_path):
    """H2: agents hold edit/execute grants, so `init` only records where they go; `sync --write` exports."""
    inst = tmp_path / "inst"
    r = mathagents("init", str(inst), "--agents-to", "agents", "--team", "baseAgent", "--exclude",
                   "lean-informalization", "interpretation-advisor", "--namespace", "ZIT", cwd=tmp_path)
    assert r.returncode == 0 and "not exported by init" in r.stdout
    assert not (inst / "agents").exists()
    assert not [k for k in json.loads((inst / cli.LOCK).read_text())["files"] if k.endswith(".agent.md")]
    orchestrator(inst / "agents")
    import tomllib
    cfg = tomllib.loads((inst / "mathagents.toml").read_text())["agents"]
    assert cfg == {"export_to": "agents", "team": "baseAgent", "namespace": "ZIT",
                   "exclude": ["lean-informalization", "interpretation-advisor"]}
    assert mathagents("sync", "--write", cwd=inst).returncode == 0
    assert len(list((inst / "agents").glob("*.agent.md"))) == len(_harness_files.AGENTS) - 2 + 1  # + orchestrator


def test_withdrawn_agents_are_untracked_not_deleted(instance):
    """H3: with export_to switched off, sync drops the agents' lock entries; their files stay."""
    marker = instance / "mathagents.toml"
    marker.write_text(marker.read_text().replace('export_to = "../../.github/agents"', '# export_to = "../../.github/agents"'))
    r = mathagents("sync", cwd=instance)
    assert r.returncode == 1 and r.stdout.count("untracked ") == len(_harness_files.AGENTS)
    assert mathagents("sync", "--write", cwd=instance).returncode == 0
    assert not [k for k in json.loads((instance / cli.LOCK).read_text())["files"] if k.endswith(".agent.md")]
    exported = [p for p in (instance.parent.parent / ".github" / "agents").glob("*.agent.md") if p.name != cli.ORCHESTRATOR]
    assert len(exported) == len(_harness_files.AGENTS)
    assert "agent.md: missing or edited" not in mathagents("doctor", cwd=instance).stdout


def test_status_reads_the_instance_env_like_run(instance):
    """H1: from the repository root, `status` and `run` resolve the same instance, so the same .env decides."""
    ws = instance.parent.parent
    (ws / "mathagents.toml").write_text('[workspace]\ndefault = "Projects/Demo"\n')
    (ws / ".git").mkdir()  # the .env search stops at the work-tree root
    (instance / ".env").write_text("MATHAGENTS_ENABLED=0\n")
    assert mathagents("status", cwd=ws).returncode == config.DISABLED_EXIT
    assert mathagents("run", "validate_registries", cwd=ws).returncode == config.DISABLED_EXIT


def test_a_one_off_export_elsewhere_keeps_the_configured_agents_tracked(instance, tmp_path):
    """`agents export --to OTHER --write` must not untrack the export_to agents (and sync must not untrack OTHER's)."""
    lock = lambda: json.loads((instance / cli.LOCK).read_text())["files"]  # noqa: E731
    before = {k for k in lock() if k.endswith(".agent.md")}
    other = tmp_path / "elsewhere"
    orchestrator(other)
    assert mathagents("agents", "export", "--to", str(other), "--write", cwd=instance).returncode == 0
    after = {k for k in lock() if k.endswith(".agent.md")}
    assert before <= after and len(after) == 2 * len(before)
    assert mathagents("sync", "--write", cwd=instance).returncode == 0
    assert {k for k in lock() if k.endswith(".agent.md")} == after


def test_status_on_a_root_that_is_not_an_instance_fails_like_run(tmp_path):
    (tmp_path / "nothing").mkdir()
    r = mathagents("status", "--root", str(tmp_path / "nothing"), cwd=tmp_path)
    assert r.returncode == 2 and "neither a mathAgents checkout nor an instance" in r.stdout


def test_init_validates_team_namespace_and_exclude(tmp_path):
    bad = [("--team", 'evil"\nname: x'), ("--namespace", "not a name"), ("--exclude", "no-such-agent")]
    for i, (flag, value) in enumerate(bad):
        r = mathagents("init", str(tmp_path / f"i{i}"), flag, value, cwd=tmp_path)
        assert r.returncode == 2 and not (tmp_path / f"i{i}" / "mathagents.toml").exists(), (flag, r.stdout)


def test_agents_are_never_exported_where_there_is_no_orchestrator(tmp_path):
    """M2: the orchestrator holds the team's write authority and dispatches every stage, so `sync` and `agents
    export` refuse a destination without one, before writing anything, and point at instantiating a team."""
    inst = tmp_path / "inst"
    assert mathagents("init", str(inst), "--agents-to", "agents", cwd=tmp_path).returncode == 0
    lock_before = (inst / cli.LOCK).read_bytes()
    for args in (("sync", "--write"), ("sync",), ("agents", "export", "--write"),
                 ("agents", "export", "--to", str(tmp_path / "bare"), "--write")):
        r = mathagents(*args, cwd=inst)
        assert r.returncode == 2 and "only under an orchestrator" in r.stdout and "agentteams" in r.stdout, args
    assert not (inst / "agents").exists() and not (tmp_path / "bare").exists()
    assert (inst / cli.LOCK).read_bytes() == lock_before


def test_doctor_flags_a_missing_orchestrator_and_warns_on_an_unfolded_roster(instance):
    agents = instance.parent.parent / ".github" / "agents"
    out = mathagents("doctor", cwd=instance).stdout
    assert "roster:   not yet in the orchestrator's agents: list" in out and "lean-prover" in out
    orchestrator(agents, roster=_harness_files.AGENTS)
    assert "roster:" not in mathagents("doctor", cwd=instance).stdout
    (agents / cli.ORCHESTRATOR).unlink()
    out = mathagents("doctor", cwd=instance).stdout
    assert f"no {cli.ORCHESTRATOR}" in out and "only under an orchestrator" in out


@pytest.mark.parametrize("make", ["bytes", "directory"])
def test_doctor_reports_an_unreadable_orchestrator(instance, make):
    """The roster check reads the orchestrator file; a read error is a doctor problem, never an empty roster."""
    path = instance.parent.parent / ".github" / "agents" / cli.ORCHESTRATOR
    path.unlink()
    if make == "bytes":
        path.write_bytes(b"---\nname: \xff\xfe\nagents:\n  - orchestrator\n---\n")
    else:
        path.mkdir()
        (path / "x").write_text("")
    r = mathagents("doctor", cwd=instance)
    if make == "bytes":
        assert r.returncode == 1 and "unreadable" in r.stdout, r.stdout
    else:  # a directory is no orchestrator file at all (M2)
        assert r.returncode == 1 and f"no {cli.ORCHESTRATOR}" in r.stdout, r.stdout


@pytest.mark.parametrize("bad", ['"lean-informalization"', '["no-such-agent"]', '[1]'])
def test_a_malformed_exclude_is_refused_not_ignored(tmp_path, bad):
    """`[agents] exclude` must be a list of pipeline-agent names: a string would split into characters and an
    unknown name would exclude nothing, both silently."""
    inst = tmp_path / "inst"
    assert mathagents("init", str(inst), "--agents-to", "agents", cwd=tmp_path).returncode == 0
    orchestrator(inst / "agents")
    marker = inst / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# exclude = ["lean-informalization"]', f"exclude = {bad}"))
    vendored = inst / "docs" / "kernel-gate.md"
    vendored.unlink()  # a refused sync must not restore it: the export is validated before anything is vendored
    lock_before = (inst / cli.LOCK).read_bytes()
    r = mathagents("sync", "--write", cwd=inst)
    assert r.returncode != 0 and "[agents] exclude" in r.stdout + r.stderr, r.stdout + r.stderr
    assert list((inst / "agents").glob("*.agent.md")) == [inst / "agents" / cli.ORCHESTRATOR]
    assert not vendored.exists() and (inst / cli.LOCK).read_bytes() == lock_before


def test_doctor_reports_a_bad_exclude_instead_of_aborting(instance):
    """`[agents] exclude` naming no pipeline agent is a doctor problem; doctor still runs its other checks."""
    marker = instance / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# exclude = ["lean-informalization"]', 'exclude = ["no-such-agent"]'))
    r = mathagents("doctor", cwd=instance)
    assert r.returncode == 1 and "[agents] exclude" in r.stdout and "doctor:" in r.stdout, r.stdout + r.stderr
