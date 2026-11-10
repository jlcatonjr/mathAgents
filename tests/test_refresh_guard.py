"""scripts/refresh_agent_surfaces.sh must never run the overwrite render with an agentteams that drops user-editable
regions (D39 incident, CA-023/CA-031). Since agentteams P5a (f113f5d), --overwrite carries agents' Project-Specific
Notes and instruction files' Project-Specific Rules and refuses rather than drop one; the script checks for that
agentteams (scripts/lib/require_cli_flag.sh) before rendering, and never passes the --discard-user-regions opt-out."""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# A grant-mode Goose recipe as the write-policy pilot rendered it (agentteams v1.1.0-rc.15, the frozen .goose/recipes/
# security.yaml at 1751375). The live recipe no longer is one once Goose is unfrozen outside the switch (CX-3).
PILOT_SECURITY_RECIPE = ROOT / "tests/fixtures/goose-pilot-security.yaml"
SCRIPT = (ROOT / "scripts" / "refresh_agent_surfaces.sh").read_text()
HELPER = ROOT / "scripts" / "lib" / "require_cli_flag.sh"


def stub(tmp: Path, help_text: str, lines: int = 1) -> dict:
    """A PATH whose `agentteams` prints ``help_text`` padded to ``lines`` lines (a long help exercises SIGPIPE)."""
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    (bin_dir / "agentteams").write_text(f"#!/bin/sh\necho '{help_text}'\nseq {lines}\n")
    (bin_dir / "agentteams").chmod(0o755)
    return {**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin"}


def check(env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["/bin/bash", str(HELPER), "--discard-user-regions", "agentteams"], env=env, capture_output=True,
                          text=True)


def test_a_carrying_agentteams_passes_even_with_a_long_help(tmp_path):
    assert check(stub(tmp_path, "  --discard-user-regions  opt out", lines=200000)).returncode == 0


def test_an_agentteams_without_the_carry_is_refused(tmp_path):
    r = check(stub(tmp_path, "  --overwrite  re-render"))
    assert r.returncode == 1 and "does not list --discard-user-regions" in r.stderr


def test_a_missing_agentteams_is_reported_as_missing(tmp_path):
    r = check({**os.environ, "PATH": f"{tmp_path}:/usr/bin:/bin"})  # no agentteams on this PATH
    assert r.returncode == 127 and "not installed" in r.stderr


def test_the_refresh_checks_before_rendering_and_never_discards():
    check_at = SCRIPT.index("require_cli_flag.sh --discard-user-regions agentteams")
    assert check_at < SCRIPT.index("materialize --yes --adopt-orphans")
    calls = [ln for ln in SCRIPT.splitlines() if not ln.lstrip().startswith("#") and "--discard-user-regions" in ln]
    assert all("require_cli_flag.sh" in ln for ln in calls), calls


# --- the render runs reviewed agentteams code (scripts/lib/agentteams_provenance.py) ---------------------------

import json
import sys

PROVENANCE = ROOT / "scripts" / "lib" / "agentteams_provenance.py"


def g(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args], check=True,
                   capture_output=True)


def fake_agentteams(tmp: Path, install: str = "editable", layout: str = "flat", shebang: str = "direct",
                    git_repo: bool = True) -> tuple[Path, Path, dict]:
    """(repo, package dir, env): a fake agentteams source tree (flat or src/ layout, optionally a git checkout with
    origin/main), dist metadata recording how it was installed (PEP 610: editable, vcs or local snapshot), and a PATH
    whose `agentteams` launcher uses a direct, env-style or pip-trampoline shebang."""
    repo = tmp / "agentteams src"  # a space in the path, deliberately
    root = repo / "src" if layout == "src" else repo
    pkg = root / "agentteams"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    if git_repo:
        g(repo, "init", "-q", "-b", "main")
        g(repo, "add", ".")
        g(repo, "commit", "-qm", "init")
        g(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    site = tmp / "site dir"
    info = site / "agentteams-9.9.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: agentteams\nVersion: 9.9\n")
    direct = {"editable": {"url": repo.as_uri(), "dir_info": {"editable": True}},
              "vcs": {"url": "https://github.com/x/agentteams", "vcs_info": {"vcs": "git", "commit_id": "c" * 40}},
              "snapshot": {"url": repo.as_uri(), "dir_info": {}}}[install]
    (info / "direct_url.json").write_text(json.dumps(direct))
    pythonpath = f"{site}:{root}"
    if install != "editable":  # an installed copy lives in site-packages and is listed in the install's RECORD
        (site / "agentteams").mkdir()
        (site / "agentteams" / "__init__.py").write_text("")
        (info / "RECORD").write_text("agentteams/__init__.py,,\nagentteams-9.9.dist-info/METADATA,,\n")
        pythonpath = str(site)
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    py = sys.executable
    first = {"direct": f"#!{py}\n", "env": "#!/usr/bin/env python3\n",
             "trampoline": f"#!/bin/sh\n\'\'\'exec\' \"{py}\" \"$0\" \"$@\"\n\' \'\'\'\n"}[shebang]
    (bin_dir / "agentteams").write_text(first + "print('agentteams 9.9')\n")
    (bin_dir / "agentteams").chmod(0o755)
    path = f"{bin_dir}:{Path(py).parent}:/usr/bin:/bin"  # env-style shebangs resolve python3 from PATH
    return repo, pkg, {**os.environ, "PATH": path, "PYTHONPATH": pythonpath}


def provenance(env: dict, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run the check with the toolchain.lock in `cwd` (none unless a test passes a directory holding one); the
    repository's real lock is never consulted here (MATHAGENTS_TOOLCHAIN_LOCK)."""
    if cwd is None:
        cwd = Path(tempfile.mkdtemp())
    env = {**env, "MATHAGENTS_TOOLCHAIN_LOCK": str(cwd / "toolchain.lock")}
    return subprocess.run([sys.executable, str(PROVENANCE)], env=env, capture_output=True, text=True, cwd=cwd)


def lock_dir(tmp: Path, commit: str) -> Path:
    d = tmp / "instance"
    d.mkdir(exist_ok=True)
    (d / "toolchain.lock").write_text(f"# test lock\nresearchteam=x/researchteam@{'a' * 40}\nagentteams=x/agentteams@{commit}\n")
    return d


def test_a_vcs_install_must_be_the_locked_commit(tmp_path):
    *_, env = fake_agentteams(tmp_path, install="vcs", git_repo=False)
    r = provenance(env, lock_dir(tmp_path, "c" * 40))
    assert r.returncode == 0 and "matches toolchain.lock" in r.stdout, r.stdout + r.stderr
    (tmp_path / "other").mkdir()
    other = lock_dir(tmp_path / "other", "d" * 40)
    r = provenance(env, other)
    assert r.returncode == 1 and "toolchain.lock pins dddddddddddd" in r.stderr, r.stdout + r.stderr
    r = provenance({**env, "MATHAGENTS_ALLOW_UNLOCKED_AGENTTEAMS": "1"}, other)
    assert r.returncode == 0 and "WARNING" in r.stderr, r.stdout + r.stderr


def test_a_detached_release_checkout_at_the_lock_passes_even_off_main(tmp_path):
    """agentteams' consumer model: a detached checkout at the release tag (release/1.0 commits are not on main)."""
    repo, pkg, env = fake_agentteams(tmp_path)
    g(repo, "checkout", "-qb", "release/1.0")
    (pkg / "fix.py").write_text("backport = 1\n")
    g(repo, "add", ".")
    g(repo, "commit", "-qm", "backport")
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    g(repo, "checkout", "-q", "--detach", sha)
    r = provenance(env, lock_dir(tmp_path, sha))
    assert r.returncode == 0 and "matches toolchain.lock" in r.stdout, r.stdout + r.stderr
    assert provenance(env).returncode == 1  # without the lock the old rule holds: not on origin/main


def test_a_dirty_checkout_at_the_locked_commit_is_still_refused(tmp_path):
    repo, pkg, env = fake_agentteams(tmp_path)
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    lock = lock_dir(tmp_path, sha)
    assert provenance(env, lock).returncode == 0
    (pkg / "__init__.py").write_text("edited = True\n")
    r = provenance(env, lock)
    assert r.returncode == 1 and "__init__.py" in r.stderr, r.stdout + r.stderr
    (pkg / "__init__.py").write_text("")
    (pkg / "untracked.py").write_text("z = 3\n")
    r = provenance(env, lock)
    assert r.returncode == 1 and "untracked.py" in r.stderr, r.stdout + r.stderr


def test_the_lock_is_read_at_the_repository_root_not_the_working_directory():
    script = PROVENANCE.read_text()
    assert 'Path(__file__).resolve().parents[2] / "toolchain.lock"' in script
    assert 'Path("toolchain.lock")' not in script


def test_an_editable_checkout_on_main_but_not_the_locked_commit_is_refused(tmp_path):
    *_, env = fake_agentteams(tmp_path)
    r = provenance(env, lock_dir(tmp_path, "e" * 40))
    assert r.returncode == 1 and "toolchain.lock pins eeeeeeeeeeee" in r.stderr, r.stdout + r.stderr


def test_a_package_or_snapshot_cannot_satisfy_a_lock(tmp_path):
    *_, env = fake_agentteams(tmp_path, install="snapshot", git_repo=False)
    r = provenance({**env, "MATHAGENTS_ALLOW_AGENTTEAMS_SNAPSHOT": "1"}, lock_dir(tmp_path, "c" * 40))
    assert r.returncode == 1 and "cannot be shown" in r.stderr, r.stdout + r.stderr


def test_a_malformed_lock_is_refused(tmp_path):
    *_, env = fake_agentteams(tmp_path, install="vcs", git_repo=False)
    d = tmp_path / "bad"
    d.mkdir()
    (d / "toolchain.lock").write_text("agentteams=x/agentteams@main\n")
    r = provenance(env, d)
    assert r.returncode == 1 and "malformed agentteams line" in r.stderr, r.stdout + r.stderr


def test_an_editable_checkout_on_main_passes_and_is_named(tmp_path):
    *_, env = fake_agentteams(tmp_path)
    r = provenance(env)
    assert r.returncode == 0 and "editable checkout" in r.stdout and "branch main" in r.stdout, r.stdout + r.stderr


def test_an_unmerged_branch_is_refused(tmp_path):
    repo, pkg, env = fake_agentteams(tmp_path)
    g(repo, "checkout", "-qb", "someone-elses-branch")
    (pkg / "x.py").write_text("x = 1\n")
    g(repo, "add", ".")
    g(repo, "commit", "-qm", "wip")
    r = provenance(env)
    assert r.returncode == 1 and "not on origin/main" in r.stderr and "someone-elses-branch" in r.stderr


def test_edits_and_untracked_modules_are_refused_but_bytecode_is_not(tmp_path):
    _, pkg, env = fake_agentteams(tmp_path)
    (pkg / "__pycache__").mkdir()
    (pkg / "__pycache__" / "x.cpython-312.pyc").write_bytes(b"\0")
    assert provenance(env).returncode == 0
    (pkg / "new_module.py").write_text("y = 2\n")
    r = provenance(env)
    assert r.returncode == 1 and "new_module.py" in r.stderr
    (pkg / "new_module.py").unlink()
    (pkg / "__init__.py").write_text("edited = True\n")
    assert provenance(env).returncode == 1


def test_a_src_layout_is_checked_where_python_imports_it(tmp_path):
    _, pkg, env = fake_agentteams(tmp_path, layout="src")
    assert provenance(env).returncode == 0
    (pkg / "__init__.py").write_text("edited = True\n")
    assert provenance(env).returncode == 1


def test_env_and_pip_trampoline_shebangs_are_followed(tmp_path):
    for i, shebang in enumerate(("env", "trampoline")):
        *_, env = fake_agentteams(tmp_path / str(i), shebang=shebang)
        r = provenance(env)
        assert r.returncode == 0 and "editable checkout" in r.stdout, (shebang, r.stdout + r.stderr)


def test_a_failing_git_status_is_a_refusal_not_a_pass(tmp_path):
    repo, _, env = fake_agentteams(tmp_path)
    (repo / ".git" / "index").write_bytes(b"not an index")
    r = provenance(env)
    assert r.returncode == 1, r.stdout + r.stderr


def test_a_vcs_install_passes_and_names_its_commit(tmp_path):
    *_, env = fake_agentteams(tmp_path, install="vcs", git_repo=False)
    r = provenance(env)
    assert r.returncode == 0 and "VCS install" in r.stdout and "cccccccccccc" in r.stdout, r.stdout + r.stderr


def test_a_local_snapshot_is_refused_unless_accepted_knowingly(tmp_path):
    """A stale snapshot (researchteam/.venv at 5090eb0) is what dropped v0.2.6's adopted rows (CA-033)."""
    *_, env = fake_agentteams(tmp_path, install="snapshot", git_repo=False)
    r = provenance(env)
    assert r.returncode == 1 and "snapshot cannot be verified" in r.stderr, r.stdout + r.stderr
    r = provenance({**env, "MATHAGENTS_ALLOW_AGENTTEAMS_SNAPSHOT": "1"})
    assert r.returncode == 0 and "WARNING" in r.stderr, r.stdout + r.stderr


def test_an_install_inside_another_repo_is_not_judged_by_that_repo(tmp_path):
    """A venv inside an unrelated git repo on an unmerged branch (researchteam/.venv): a VCS install there passes."""
    outer = tmp_path / "outer"
    outer.mkdir()
    g(outer, "init", "-q", "-b", "feature")
    g(outer, "commit", "-q", "--allow-empty", "-m", "x")
    *_, env = fake_agentteams(outer, install="vcs", git_repo=False)
    assert provenance(env).returncode == 0


def test_the_refresh_checks_provenance_before_anything_runs():
    script = (ROOT / "scripts" / "refresh_agent_surfaces.sh").read_text()
    assert script.index("agentteams_provenance.py") < UPDATE_CMD.search(script).start()


def test_a_checkout_shadowing_a_verified_install_is_refused(tmp_path):
    """The VCS record says one thing; a checkout earlier on sys.path is what actually runs."""
    repo, _, env = fake_agentteams(tmp_path, install="vcs")
    env["PYTHONPATH"] = f"{repo}:{env['PYTHONPATH']}"
    r = provenance(env)
    assert r.returncode == 1 and "shadows" in r.stderr, r.stdout + r.stderr


def test_an_editable_record_pointing_elsewhere_is_refused(tmp_path):
    _, _, env = fake_agentteams(tmp_path)
    other = tmp_path / "elsewhere"
    (other / "agentteams").mkdir(parents=True)
    (other / "agentteams" / "__init__.py").write_text("")
    env["PYTHONPATH"] = env["PYTHONPATH"].split(":")[0] + f":{other}"  # the record's checkout is not what imports
    r = provenance(env)
    assert r.returncode == 1 and "outside the editable checkout" in r.stderr, r.stdout + r.stderr


def test_a_corrupt_install_record_is_a_clean_refusal(tmp_path):
    _, _, env = fake_agentteams(tmp_path)
    site = Path(env["PYTHONPATH"].split(":")[0])
    (site / "agentteams-9.9.dist-info" / "direct_url.json").write_text("{not json")
    r = provenance(env)
    assert r.returncode == 1 and "REFUSED" in r.stderr and "Traceback" not in r.stderr, r.stderr


def test_a_missing_agentteams_exits_127(tmp_path):
    r = provenance({**os.environ, "PATH": f"{tmp_path}:/usr/bin:/bin"})
    assert r.returncode == 127 and "not installed" in r.stderr


def test_an_unparseable_launcher_is_refused(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "agentteams").write_text("no shebang here\n")
    (bin_dir / "agentteams").chmod(0o755)
    r = provenance({**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin"})
    assert r.returncode == 1 and "shebang not understood" in r.stderr


# --- D41: agentteams applies the write policy to the bespoke agents (#174, 1.0.0rc9); step 3b checks Goose ---------

def _check_goose(tmp_path: Path, brief: dict, recipes: dict[str, str]) -> subprocess.CompletedProcess:
    import json
    import sys
    d = tmp_path / "recipes"
    d.mkdir(parents=True)
    for name, text in recipes.items():
        (d / f"{name}.yaml").write_text(text)
    (tmp_path / "brief.json").write_text(json.dumps(brief))
    return subprocess.run([sys.executable, str(ROOT / "scripts/lib/check_bespoke_goose.py"), str(d),
                           str(tmp_path / "brief.json"), *recipes], capture_output=True, text=True, cwd=ROOT)


PILOT_BRIEF = {"write_policy": "orchestrator-only", "write_policy_frameworks": ["claude", "goose"]}


def test_check_bespoke_goose_hands_back_when_the_pilot_is_off(tmp_path):
    for brief in ({}, {"write_policy": "orchestrator-only", "write_policy_frameworks": ["claude"]}):
        assert _check_goose(tmp_path / str(len(brief)), brief, {"x": ""}).returncode == 3


def test_check_bespoke_goose_passes_agentteams_grant_mode_and_refuses_the_legacy_shape(tmp_path):
    import pytest
    pytest.importorskip("agentteams.audit")
    granted = PILOT_SECURITY_RECIPE.read_text()  # a rendered read-only agent (grant mode)
    r = _check_goose(tmp_path / "a", PILOT_BRIEF, {"x": granted})
    assert r.returncode == 0, r.stderr
    legacy = granted.split("# agentteams-declared-tools:")[0] + (
        "extensions:\n  - type: builtin\n    name: developer\n    bundled: true\n    timeout: 300\n"
        "    available_tools: [tree]\n")
    r = _check_goose(tmp_path / "b", PILOT_BRIEF, {"x": legacy})
    assert r.returncode == 1 and "AR_GOOSE_MARKER_MISSING" in r.stderr, r.stderr


def test_check_bespoke_goose_usage_and_brief_shape(tmp_path):
    import sys
    r = subprocess.run([sys.executable, str(ROOT / "scripts/lib/check_bespoke_goose.py")], capture_output=True, text=True)
    assert r.returncode == 1 and r.stderr.startswith("Usage: check_bespoke_goose.py"), r.stderr
    r = _check_goose(tmp_path, {"write_policy": "orchestrator-only", "write_policy_frameworks": "goose"}, {"x": ""})
    assert r.returncode == 1 and "must be a list" in r.stderr


def test_check_bespoke_goose_refuses_a_missing_or_altered_readfs_server(tmp_path):
    import shutil
    import sys
    import pytest
    pytest.importorskip("agentteams.audit")
    granted = PILOT_SECURITY_RECIPE.read_text()
    (tmp_path / "recipes").mkdir()
    (tmp_path / "recipes/x.yaml").write_text(granted)
    (tmp_path / "brief.json").write_text(__import__("json").dumps(PILOT_BRIEF))
    cmd = [sys.executable, str(ROOT / "scripts/lib/check_bespoke_goose.py"), "recipes", "brief.json", "x"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path)  # no .agentteams/bin here
    assert r.returncode == 1 and "readfs server missing" in r.stderr, r.stderr
    server = tmp_path / ".agentteams/bin/goose-readfs-mcp.py"
    server.parent.mkdir(parents=True)
    shutil.copy(ROOT / ".agentteams/bin/goose-readfs-mcp.py", server)
    assert subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path).returncode == 0
    server.write_text(server.read_text() + "\n# altered\n")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 1 and "differs from the copy agentteams" in r.stderr, r.stderr


def test_refresh_refuses_an_agentteams_below_the_floor_before_rendering():
    script = (ROOT / "scripts/refresh_agent_surfaces.sh").read_text()
    assert "agentteams_too_old(agentteams_version())" in script
    assert script.index("agentteams_too_old") < script.index('step "1/4')


def test_refresh_passes_the_brief_to_interop_and_checks_goose_under_the_pilot():
    script = (ROOT / "scripts/refresh_agent_surfaces.sh").read_text()
    assert "bespoke_write_policy" not in script and not (ROOT / "scripts/lib/bespoke_write_policy.py").exists()
    for fw in ("claude", "goose"):
        line = next(l for l in script.splitlines() if f'--interop-from "$T/src" --framework {fw}' in l)
        assert "--description brief.json" in line, line
    assert 'check_bespoke_goose.py .goose/recipes brief.json' in script
    assert script.index("check_bespoke_goose.py") < script.index('scope-goose "$T/src" .goose/recipes')
    assert "if [[ $rc -eq 3 ]]" in script  # mathagents scopes Goose only when the pilot is off


def test_refresh_derives_in_canonical_shape_and_pins_the_runner_server():
    """M6: with mcp_grants, interop must write a project's .claude/agents (the runner installs beside it)."""
    script = (ROOT / "scripts/refresh_agent_surfaces.sh").read_text()
    for fw, out in (("claude", '"$T/proj/.claude/agents"'), ("goose", '"$T/proj/.goose/recipes"')):
        line = next(l for l in script.splitlines() if f'--interop-from "$T/src" --framework {fw}' in l)
        assert f"--output {out}" in line, line
    assert script.count("--overwrite --yes") >= 2
    assert "from agentteams.runner_mcp import SHA256" in script  # the copied server is checked against the pin
    assert "has mcp_grants but interop installed no agentteams_runner server" in script  # a missing server stops
    # Only named files come back from $T/proj: no directory copy, no glob, so interop's side files
    # (runtime-handoffs.json, the Goose team marker and control plane) can never reach the live tree.
    copies = [l.strip() for l in script.splitlines() if l.strip().startswith(("cp ", "mkdir -p \"$(dirname"))
              and "$T/proj" in l]
    assert copies and all(" -r" not in c and "*" not in c for c in copies), copies
    assert {c.split()[1] for c in copies if c.startswith("cp ")} <= {
        '"$T/proj/.claude/agents/$a.md"', '"$T/proj/.goose/recipes/$a.yaml"', '"$T/proj/$RUNNER_MCP"',
        '"$T/proj/$READFS"'}, copies
    # an unfrozen Goose's readfs server is installed only as agentteams pins it, and never replaces a local copy
    assert "from agentteams.frameworks.goose_tool_scoping import READFS_SHA256" in script
    assert 'installed $READFS differs from the one agentteams ships' in script


# researchteam-managed scripts (researchteam/_manifest.py FRAMEWORK_MANAGED_FILES): `researchteam update` overwrites
# them, so they can't carry the guard here; the fix for them is upstream (researchteam-f6, 2026-10-15).
# A command line that runs `researchteam update` (with --yes, or the refresh script's UPDATE_ARGS), not a comment.
UPDATE_CMD = re.compile(r'^\s*researchteam update (?:--yes\b|"\$\{UPDATE_ARGS\[@\]\}")', re.M)
RESEARCHTEAM_MANAGED = {"scripts/agentteams_autosync_gate.sh", "scripts/validate_agentteams_update.sh"}


def test_every_researchteam_update_is_bracketed_by_the_bespoke_guard():
    """researchteam's scholarly sync once replaced the canonical interpretation-advisor ("above-notes", researchteam
    90f497a; autosync f6be803, 2026-10-14). researchteam 1.0.0rc1 (#50) keeps it, so each mathAgents-owned script that
    runs the update snapshots before and verifies right after: a changed canonical source stops the run."""
    runners = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "scripts").rglob("*.sh")
                     if UPDATE_CMD.search(p.read_text()))
    owned = [r for r in runners if r not in RESEARCHTEAM_MANAGED]
    assert "scripts/refresh_agent_surfaces.sh" in owned
    for rel in owned:
        script = (ROOT / rel).read_text()
        update = UPDATE_CMD.search(script).start()
        assert script.rfind("guard_bespoke_canonical.sh snapshot", 0, update) >= 0, rel
        verify = script.find("guard_bespoke_canonical.sh verify", update)
        assert verify >= 0 and script.count("\n", update, verify) <= 2, rel  # verified right after the update
        assert "guard_bespoke_canonical.sh restore" not in script, rel  # never repaired silently


def test_bespoke_guard_snapshot_refuses_a_missing_canonical_file(tmp_path):
    guard = ["bash", str(ROOT / "scripts/lib/guard_bespoke_canonical.sh")]
    r = subprocess.run(guard + ["snapshot", str(tmp_path / "s2"), "missing"], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 1 and "missing" in r.stderr
    r = subprocess.run(guard + ["restore", str(tmp_path / "s2"), "missing"], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 2  # no restore mode: a changed source is fixed from git, never by the guard

def test_bespoke_guard_verify_fails_on_a_changed_canonical_file_and_changes_nothing(tmp_path):
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    (agents / "a.agent.md").write_text("bespoke\n")
    (agents / "b.agent.md").write_text("other\n")
    guard = ["bash", str(ROOT / "scripts/lib/guard_bespoke_canonical.sh")]
    snap = tmp_path / "snap"
    assert subprocess.run(guard + ["snapshot", str(snap), "a", "b"], cwd=tmp_path).returncode == 0
    assert subprocess.run(guard + ["verify", str(snap), "a", "b"], cwd=tmp_path).returncode == 0
    (agents / "a.agent.md").write_text("template\n")
    r = subprocess.run(guard + ["verify", str(snap), "a", "b"], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 1 and "a.agent.md" in r.stderr and "b.agent.md" not in r.stderr
    assert (agents / "a.agent.md").read_text() == "template\n"  # verify never restores


def test_refresh_reasserts_bespoke_agents_after_the_native_render():
    """researchteam #46 re-renders Claude natively under write_policy; a bespoke agent sharing a template's name
    (interpretation-advisor) must not come back as the template (M6 render, 2026-10-15)."""
    script = (ROOT / "scripts/refresh_agent_surfaces.sh").read_text()
    materialize = script.index("researchteam materialize --yes")
    reassert = script.index("re-asserting the bespoke")
    assert materialize < reassert < script.index('step "3b/4')
    assert '".claude/agents/$a.md"' in script[materialize:reassert]


def test_interpreter_of_follows_the_cli_launcher(tmp_path):
    """The refresh's Python steps run under the CLI's own interpreter, not whatever `python3` is first on PATH."""
    py = tmp_path / "py" / "python3"
    py.parent.mkdir()
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    cli = bindir / "agentteams"
    cli.write_text(f"#!{py}\nimport sys\n")
    cli.chmod(0o755)
    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}")
    r = subprocess.run(["python3", str(ROOT / "scripts/lib/agentteams_provenance.py"), "--interpreter-of", "agentteams"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0 and r.stdout.strip() == str(py)
    r = subprocess.run(["python3", str(ROOT / "scripts/lib/agentteams_provenance.py"), "--interpreter-of", "no-such-cli-x"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 127


def test_refresh_scripts_use_the_cli_interpreters():
    refresh = (ROOT / "scripts/refresh_agent_surfaces.sh").read_text()
    codex = (ROOT / "scripts/operator/refresh_codex_projection.sh").read_text()
    for line in (refresh + codex).splitlines():
        s = line.strip()
        assert not (s.startswith("python3 -c") or s.startswith("python3 -m mathagents")
                    or s.startswith("python3 scripts/lib/bespoke")), line
    assert '"$PY_RT" -c "from pathlib import Path; from researchteam' in codex


def test_the_rendered_surfaces_were_built_with_the_locked_agentteams():
    """toolchain.lock is the one record of the agentteams this checkout renders with (D43). Goose and Codex are
    frozen as last rendered before M6 (D43), so only the live surfaces are held to the lock until the 1.0 render."""
    import runpy
    want = runpy.run_path(str(PROVENANCE))["locked_commit"](ROOT / "toolchain.lock")  # the script's own parser
    assert want, "toolchain.lock names no agentteams commit"
    for surface in (".github/agents", ".claude/agents"):
        log = json.loads((ROOT / surface / "references" / "build-log.json").read_text())
        assert log["agentteams_source"].get("commit") == want, (surface, log["agentteams_source"])


def fake_researchteam(tmp: Path) -> tuple[Path, str, dict]:
    """(repo, HEAD sha, env): an editable researchteam git checkout with PEP 610 metadata on PYTHONPATH."""
    repo = tmp / "researchteam src"
    pkg = repo / "researchteam"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (repo / "README.md").write_text("repo-level file\n")
    g(repo, "init", "-q", "-b", "main")
    g(repo, "add", ".")
    g(repo, "commit", "-qm", "init")
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    site = tmp / "rt site"
    info = site / "researchteam-0.1.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: researchteam\nVersion: 0.1\n")
    (info / "direct_url.json").write_text(json.dumps({"url": repo.as_uri(), "dir_info": {"editable": True}}))
    return repo, sha, {**os.environ, "PYTHONPATH": f"{site}:{repo}"}


def researchteam_provenance(env: dict, lock: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PROVENANCE), "--inner-researchteam"], capture_output=True, text=True,
                          env={**env, "MATHAGENTS_TOOLCHAIN_LOCK": str(lock)})


def rt_lock(tmp: Path, commit: str) -> Path:
    lock = tmp / "toolchain.lock"
    lock.write_text(f"researchteam=x/researchteam@{commit}\nagentteams=x/agentteams@{'c' * 40}\n")
    return lock


def test_the_researchteam_that_renders_must_be_the_locked_commit(tmp_path):
    repo, sha, env = fake_researchteam(tmp_path)
    r = researchteam_provenance(env, rt_lock(tmp_path, sha))
    assert r.returncode == 0 and "matches toolchain.lock (researchteam" in r.stdout, r.stdout + r.stderr
    r = researchteam_provenance(env, rt_lock(tmp_path, "f" * 40))
    assert r.returncode == 1 and "toolchain.lock pins ffffffffffff" in r.stderr, r.stdout + r.stderr
    (repo / "README.md").write_text("edited repo file\n")  # outside the package: not judged
    assert researchteam_provenance(env, rt_lock(tmp_path, sha)).returncode == 0
    (repo / "researchteam" / "__init__.py").write_text("edited = True\n")
    r = researchteam_provenance(env, rt_lock(tmp_path, sha))
    assert r.returncode == 1 and "__init__.py" in r.stderr, r.stdout + r.stderr
    assert researchteam_provenance(env, tmp_path / "no-lock").returncode == 1  # dirty package still refused
    (repo / "researchteam" / "__init__.py").write_text("")
    assert researchteam_provenance(env, tmp_path / "no-lock").returncode == 0  # no lock: report only


def test_the_refresh_checks_researchteam_provenance_before_rendering():
    script = (ROOT / "scripts/refresh_agent_surfaces.sh").read_text()
    assert script.index("agentteams_provenance.py --researchteam") < script.index('step "1/4')


def test_frozen_surfaces_are_skipped_and_checked_against_head():
    """D43 / shared policy §5: researchteam update skips a frozen Codex itself (--no-codex, researchteam #64), and the
    refresh then checks .codex and .agents/skills against HEAD, never moving or deleting them; a frozen Goose is
    restored from git; and the render check accepts a frozen surface only when it is byte-identical to HEAD."""
    script = (ROOT / "scripts/refresh_agent_surfaces.sh").read_text()
    check = (ROOT / "scripts/check_render_consistency.sh").read_text()
    helper = (ROOT / "scripts/lib/frozen_surfaces.sh").read_text()
    assert "is_frozen()" in helper
    assert "source scripts/lib/frozen_surfaces.sh" in script and "MATHAGENTS_FROZEN_SURFACES:-" not in script
    assert "MATHAGENTS_FROZEN_SURFACES:-" not in check
    src = check.index('source "$ROOT/scripts/lib/frozen_surfaces.sh"')
    assert check.index('cd "$ROOT"') < src  # sourced after cd, so a frozen check can't silently become the live one
    # researchteam #64: update always skips Codex (--no-codex), which is then checked unchanged and never moved; an
    # unfrozen Codex is rendered once, in step 3a (CX-3)
    assert 'UPDATE_ARGS=(--yes --no-codex)' in script and 'researchteam update "${UPDATE_ARGS[@]}"' in script
    assert script.index('UPDATE_ARGS=(--yes --no-codex)') < script.index('researchteam update "${UPDATE_ARGS[@]}"')
    assert script.index('require_unfreeze_toolchain.sh') < script.index('researchteam update "${UPDATE_ARGS[@]}"')
    assert script.index('step "3a/4') < script.index('bash scripts/lib/project_bespoke_codex.sh')
    unchanged = script.index('git diff --quiet HEAD -- .codex .agents/skills')
    assert script.index('researchteam update "${UPDATE_ARGS[@]}"') < unchanged < script.index('step "2/4')
    assert 'mv .codex' not in script and 'rm -rf .codex' not in script
    assert script.index('git checkout HEAD -- .goose AGENTS.md') < script.index('step "4/4')
    # the gate's consumption mark in Goose's decisions log survives the frozen restore (found by agentteams-f3, 2026-10-18)
    save, back = script.index('cp "$GLOG" "$T/goose-decisions.log.csv"'), script.index('cp "$T/goose-decisions.log.csv" "$GLOG"')
    assert save < script.index('git checkout HEAD -- .goose AGENTS.md') < back
    assert 'if is_frozen codex; then\n  echo "[refresh] Codex is frozen (brief.json frozen_surfaces): step 3a skipped"' in script
    assert "git diff --quiet HEAD -- .codex .agents/skills" in check


def test_frozen_surfaces_come_from_the_brief_and_an_env_override_must_agree(tmp_path):
    """researchteam 1.0.1 honours brief.json "frozen_surfaces"; the refresh reads the same key, so the managed gate and
    the refresh can't disagree. MATHAGENTS_FROZEN_SURFACES may name the same set (any order); a different set stops."""
    brief = json.loads((ROOT / "brief.json").read_text())
    assert brief["frozen_surfaces"] == []  # CX-3 (operator ruling 2026-11-09): Codex and Goose unfrozen for 1.1.0
    assert "codex" in brief["write_policy_frameworks"]  # Codex unfrozen only under orchestrator-only
    assert "goose" not in brief["write_policy_frameworks"]  # agentteams refuses the switch on Goose (UNENFORCED)
    (tmp_path / "brief.json").write_text(json.dumps({"frozen_surfaces": ["goose", "codex"]}))
    helper = ROOT / "scripts/lib/frozen_surfaces.sh"
    probe = f'source "{helper}"; for s in codex goose claude; do is_frozen "$s" && echo "$s frozen" || echo "$s live"; done'

    def run(env_value):
        env = {k: v for k, v in os.environ.items() if k != "MATHAGENTS_FROZEN_SURFACES"}
        if env_value is not None:
            env["MATHAGENTS_FROZEN_SURFACES"] = env_value
        return subprocess.run(["bash", "-c", probe], cwd=tmp_path, env=env, capture_output=True, text=True)

    for value in (None, "codex goose", "goose codex"):
        out = run(value)
        assert out.returncode == 0, out.stderr
        assert out.stdout.split("\n")[:3] == ["codex frozen", "goose frozen", "claude live"], (value, out.stdout)
    mismatch = run("codex")
    assert mismatch.returncode != 0 and "differs from brief.json frozen_surfaces" in mismatch.stderr
    assert run("   ").returncode == 0  # a blank override is no override


@pytest.mark.parametrize("brief, frozen", [({}, ""), ({"frozen_surfaces": []}, ""), ({"frozen_surfaces": ["goose", "codex"]}, "codex goose")])
def test_frozen_surfaces_absent_or_empty_freezes_nothing(tmp_path, brief, frozen):
    """As in researchteam 1.0.1 (researchteam/_frozen.py load): an absent key or [] freezes nothing."""
    (tmp_path / "brief.json").write_text(json.dumps(brief))
    probe = f'source "{ROOT / "scripts/lib/frozen_surfaces.sh"}"; echo "[$_MATHAGENTS_FROZEN]"'
    env = {k: v for k, v in os.environ.items() if k != "MATHAGENTS_FROZEN_SURFACES"}
    out = subprocess.run(["bash", "-c", probe], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.strip() == f"[{frozen}]", out.stderr


@pytest.mark.parametrize("value", ["codex", {"codex": True}, ["codex", "codx"], ["codex", "codex"], [1]])
def test_frozen_surfaces_refuses_what_researchteam_refuses(tmp_path, value):
    """A non-array, an unknown id or a duplicate stops the run (as researchteam refuses it), never 'nothing frozen'."""
    (tmp_path / "brief.json").write_text(json.dumps({"frozen_surfaces": value}))
    probe = f'source "{ROOT / "scripts/lib/frozen_surfaces.sh"}"; echo sourced'
    env = {k: v for k, v in os.environ.items() if k != "MATHAGENTS_FROZEN_SURFACES"}
    out = subprocess.run(["bash", "-c", probe], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert out.returncode != 0 and "sourced" not in out.stdout
    assert "cannot read a valid brief.json frozen_surfaces" in out.stderr


def test_bespoke_codex_import_reads_the_refresh_scripts_bespoke_list():
    """scripts/lib/project_bespoke_codex.sh parses BESPOKE_AGENTS from refresh_agent_surfaces.sh with sed; the parse must
    give the same 11 agents the refresh uses, each canonical in .github/agents (CX-3)."""
    out = subprocess.run(["bash", "-c", "sed -n 's/^BESPOKE_AGENTS=(\\(.*\\))$/\\1/p' scripts/refresh_agent_surfaces.sh"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert len(out) == 11 and len(set(out)) == 11, out
    assert all((ROOT / ".github/agents" / f"{a}.agent.md").is_file() for a in out)
    text = (ROOT / "scripts/lib/project_bespoke_codex.sh").read_text()
    assert "agentteams_provenance.py" in text and 'at --interop-from "$SRC" --framework codex --output .codex/agents' in text
    assert '--description brief.json' in text and 'sandbox_mode = "read-only"' in text


@pytest.mark.parametrize("surface", ["codex", "goose"])
def test_an_unfrozen_surface_needs_agentteams_v1_1_0_and_its_signed_unfreeze_row(tmp_path, surface):
    """CX-3: require_unfreeze_toolchain.sh refuses below an agentteams v1.1.0 release tag, and without an Ed25519-signed
    unfreeze-<surface> row; with both, it passes (researchteam still verifies the row through agentteams' gate)."""
    import shutil as _sh
    (tmp_path / "scripts/lib").mkdir(parents=True)
    _sh.copy(ROOT / "scripts/lib/require_unfreeze_toolchain.sh", tmp_path / "scripts/lib/")
    log = tmp_path / ".github/agents/references/security-decisions.log.csv"
    log.parent.mkdir(parents=True)
    log.write_text("timestamp,action_reviewed,verdict,sig_scheme,signature\r\n")
    run = lambda: subprocess.run(["bash", "scripts/lib/require_unfreeze_toolchain.sh", surface], cwd=tmp_path,
                                 capture_output=True, text=True)
    for tag in ("v1.1.0-rc.17", "v1.0.1"):
        (tmp_path / "toolchain.lock").write_text(f"agentteams=jlcatonjr/agentteams@{'0' * 40}\nagentteams.tag={tag}\n")
        r = run(); assert r.returncode != 0 and "v1.1.0 or later release tag" in r.stdout + r.stderr, tag
    (tmp_path / "toolchain.lock").write_text(f"agentteams=jlcatonjr/agentteams@{'0' * 40}\nagentteams.tag=v1.1.0\n")
    r = run(); assert r.returncode != 0 and f"no operator Ed25519-signed unfreeze-{surface} row" in r.stdout + r.stderr
    with log.open("a") as f:
        f.write(f"2026-11-09,unfreeze-{surface},PASS,ed25519,c2ln\r\n")
    assert run().returncode == 0


def _codex_tree(root: Path, stamp: str, body: str = "x") -> None:
    import json
    (root / ".codex/agents/references").mkdir(parents=True)
    (root / ".agents/skills/s").mkdir(parents=True)
    (root / ".codex/agents/security.toml").write_text(f"a = 1\nGenerated at: `{stamp}`\nbody = \"{body}\"\n")
    (root / ".codex/agents/references/build-log.json").write_text(json.dumps(
        {"archetypes": ["a"], "generated_at": stamp, "file_hashes": {"x": stamp}, "files_written": [stamp]}))
    (root / ".codex/agents/references/memory-index.json").write_text(json.dumps({"built_at": stamp}))
    (root / ".agents/skills/s/SKILL.md").write_text("skill\n")


def test_the_native_codex_freshness_compare_ignores_run_provenance_only(tmp_path):
    """CX-3: a native Codex render stamps run provenance (Generated at, generated_at, per-run build-log records, the
    memory index); compare_codex_tree.py ignores exactly that, and still reports a content change or a missing file."""
    import sys
    fresh, committed = tmp_path / "fresh", tmp_path / "committed"
    _codex_tree(fresh, "2026-11-09T23:30:13Z")
    _codex_tree(committed, "2026-10-10T22:02:36Z")
    cmp = lambda: subprocess.run([sys.executable, str(ROOT / "scripts/lib/compare_codex_tree.py"), str(fresh),
                                  str(committed)], capture_output=True, text=True)
    assert cmp().returncode == 0, cmp().stdout
    (fresh / ".codex/agents/security.toml").write_text('a = 1\nGenerated at: `2026-11-09T23:30:13Z`\nbody = "y"\n')
    r = cmp(); assert r.returncode == 1 and "differs beyond run provenance: .codex/agents/security.toml" in r.stdout
    _codex_tree(fresh2 := tmp_path / "fresh2", "2026-11-09T23:30:13Z")
    (fresh2 / ".agents/skills/s/SKILL.md").unlink()
    fresh = fresh2
    r = cmp(); assert r.returncode == 1 and "only in the committed tree: .agents/skills/s/SKILL.md" in r.stdout
    check = (ROOT / "scripts/check_render_consistency.sh").read_text()
    native = check.index("-f .agentteams/bin/codex-role-gate.py")
    assert native < check.index("_refresh_codex(Path('.'), dry_run=False)") < check.index("project_bespoke_codex.sh")
    assert check.index("project_bespoke_codex.sh") < check.index("compare_codex_tree.py")
    assert "--exclude .git " in check  # the copy never carries the worktree's git pointer
