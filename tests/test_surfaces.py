"""Grant-scoped projection of the pipeline agents onto the claude, goose and codex surfaces
(mathagents/_surfaces.py, `[agents] surfaces`). The CLI tests drive a stand-in agentteams that writes the
interop layouts agentteams 1.0.0rc8 writes (including its over-granting Goose extensions); the `test_real_*`
tests run only when MATHAGENTS_TEST_AGENTTEAMS names an agentteams executable (its interop needs live security
intel, so it is opt-in), and the Goose check also needs `goose` on PATH. No Lean needed."""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mathagents import _harness_files, _learned as learned, _surfaces as surfaces, cli  # noqa: E402
from api_fixtures import orchestrator  # noqa: E402

FAKE_AGENTTEAMS = r"""
import ast, re, sys
from pathlib import Path
a = sys.argv[1:]
if a == ["--version"]:
    print("agentteams 1.0.0rc9 (fake)"); sys.exit(0)
src, fw, out = Path(a[a.index("--interop-from") + 1]), a[a.index("--framework") + 1], Path(a[a.index("--output") + 1])
CLAUDE = {"read": ["Read"], "search": ["Grep", "Glob"], "edit": ["Edit", "Write"], "execute": ["Bash"], "agent": ["Task"]}
for f in sorted(src.glob("*.agent.md")):
    name = f.name.removesuffix(".agent.md")
    front, body = f.read_text().split("\n---\n", 1)
    tools = ast.literal_eval(re.search(r"^tools: (\[.*\])$", front, re.M).group(1))
    if fw == "claude":
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{name}.md").write_text(f"---\nname: {name}\ntools: {', '.join(t for k in tools for t in CLAUDE[k])}\n---\n{body}")
    elif fw == "goose":
        out.mkdir(parents=True, exist_ok=True)
        ins = "".join("  " + l if l.strip() else "\n" for l in body.splitlines(True))
        (out / f"{name}.yaml").write_text(f'version: "1.0.0"\ntitle: "{name}"\ndescription: "d"\ninstructions: |\n{ins}\n'
            "extensions:\n  - type: builtin\n    name: developer\n    bundled: true\n    timeout: 300\n"
            "  - type: platform\n    name: summon\n")
    elif fw == "codex":  # agentteams #319: only into a project's native .codex/agents, with a brief
        proj = out.parent.parent
        native = [".codex/agents/references/build-log.json", ".agentteams/bin/codex-role-gate.py", ".codex/hooks.json",
                  ".codex/confined-run.example.sh"]
        if out.parts[-2:] != (".codex", "agents") or "--description" not in a or \
                not all((proj / n).is_file() for n in native):
            print("codex import under write_policy: no native Codex team", file=sys.stderr); sys.exit(1)
        d = out
        mode = "workspace-write" if "edit" in tools else "read-only"
        (d / f"{name}.toml").write_text(f'# header\n\nname = "{name}"\ndescription = "d"\nsandbox_mode = "{mode}"\n'
                                        f"developer_instructions = '''\n{body}'''\n")
    else:
        sys.exit(2)
"""
SURFACE_DIRS = {s: d for s, (d, _, _) in surfaces.SURFACES.items()}


NATIVE_CODEX = (".codex/agents/references/build-log.json", ".agentteams/bin/codex-role-gate.py", ".codex/hooks.json",
                ".codex/confined-run.example.sh")


def native_codex(ws: Path) -> None:
    """Stand in for the instance's native Codex team (agentteams renders it under the switch; #319's gate)."""
    for rel in NATIVE_CODEX:
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text("{}\n" if rel.endswith(".json") else "# native\n")
    (ws / "brief.json").write_text(json.dumps({"write_policy": "orchestrator-only",
                                               "write_policy_frameworks": ["claude", "codex"]}))


def mathagents(*args: str, cwd: Path, agentteams: str | None = None,
               codex_capable: bool | None = True) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(ROOT), "HOME": str(Path.home())}
    if agentteams:
        env["MATHAGENTS_AGENTTEAMS"] = agentteams
    if agentteams and codex_capable is not None and Path(agentteams).parent.is_dir():
        probe = Path(agentteams).parent / ("probe-yes" if codex_capable else "probe-no")
        probe.write_text(f"#!/bin/sh\necho {'yes' if codex_capable else 'no'}\n")
        probe.chmod(0o755)
        env["MATHAGENTS_AGENTTEAMS_PYTHON"] = str(probe)
    return subprocess.run([sys.executable, "-m", "mathagents.cli", *args], cwd=cwd, capture_output=True, text=True,
                          env=env)


@pytest.fixture
def fake(tmp_path) -> str:
    script = tmp_path / "agentteams"
    script.write_text(f"#!{sys.executable}\n{FAKE_AGENTTEAMS}")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return str(script)


def make_instance(tmp_path: Path, surfaces_line: str, agentteams: str) -> Path:
    ws = tmp_path / "ws"
    (ws / "lean").mkdir(parents=True)
    orchestrator(ws / ".github" / "agents")  # the team has an orchestrator: agents are never exported without one (M2)
    native_codex(ws)
    inst = ws / "Projects" / "Demo"
    assert mathagents("init", str(inst), "--agents-to", "../../.github/agents", cwd=tmp_path).returncode == 0
    marker = inst / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# surfaces = ["claude", "goose", "codex"]', surfaces_line))
    r = mathagents("sync", "--write", cwd=inst, agentteams=agentteams)
    assert r.returncode == 0, r.stdout + r.stderr
    return inst


@pytest.fixture
def instance(tmp_path, fake):
    return make_instance(tmp_path, 'surfaces = ["claude", "goose", "codex"]', fake)


def surface_file(instance: Path, surface: str, name: str) -> Path:
    return surfaces.surface_path(instance.parent.parent, surface, name)


# --- the Goose map (Goose 1.37.0 tool names) ----------------------------------------------------------------

def scoped(tools):
    return surfaces.goose_extensions(tools)


def test_a_read_only_agent_gets_no_shell_no_writes_and_no_summon():
    ext = scoped(["read", "search"])
    assert "available_tools: [tree]" in ext and f"name: analyze\n    available_tools: [{surfaces.ANALYZE_OFF}]" in ext
    assert "summon" not in ext  # load and delegate both need `agent`
    assert "shell" not in ext and "write" not in ext and "delegate" not in ext


def test_edit_without_execute_gets_no_shell():
    ext = scoped(["read", "search", "edit", "agent"])
    assert "available_tools: [write, edit, tree]" in ext and "shell" not in ext
    assert "name: summon\n    available_tools: [delegate, load]" in ext


def test_the_full_grant():
    assert "available_tools: [write, edit, shell, tree]" in scoped(["read", "search", "edit", "execute", "agent"])


@pytest.mark.parametrize("tools", [["read", "web"], ["edit"], []])
def test_an_unmappable_tool_set_is_refused(tools):
    with pytest.raises(surfaces.SurfaceError):
        scoped(tools)


def test_every_pipeline_agent_has_a_scopable_tool_set():
    for name in _harness_files.AGENTS:
        tools = surfaces.declared_tools((ROOT / ".github" / "agents" / f"{name}.agent.md").read_text())
        ext = scoped(tools)
        assert ("shell" in ext) == ("execute" in tools) and ("delegate" in ext) == ("agent" in tools), name
        assert ("write, edit" in ext) == ("edit" in tools), name


GOOSE_RECIPE = ('version: "1.0.0"\ntitle: "t"\ndescription: "d"\ninstructions: |\n  body\n\n  more\n'
                "extensions:\n  - type: builtin\n    name: developer\n  - type: platform\n    name: summon\n")


def test_scope_goose_replaces_only_extensions():
    out = surfaces.scope_goose(GOOSE_RECIPE, ["read", "agent"])
    assert out.startswith(GOOSE_RECIPE.split("extensions:")[0])
    assert out.endswith("    available_tools: [delegate, load]\n") and "shell" not in out


@pytest.mark.parametrize("extra", ["settings:\n  max_turns: 5\n", "retry:\n  checks:\n    - type: shell\n",
                                   "sub_recipes:\n  - name: x\n", "mcp_servers: {}\n", "instructions: |\n  again\n",
                                   '"retry":\n  checks: []\n', "<<: *defaults\n", "? sub_recipes\n: []\n",
                                   "{retry: {}}\n", "---\n", "\tretry: {}\n"])
def test_scope_goose_refuses_any_other_top_level_key(extra):
    with pytest.raises(surfaces.SurfaceError):
        surfaces.scope_goose(GOOSE_RECIPE + extra, ["read"])


def test_claude_over_grants_are_refused():
    with pytest.raises(surfaces.SurfaceError):
        surfaces.check_claude("---\nname: x\ntools: Read, Grep, Bash\n---\n", ["read", "search"])
    with pytest.raises(surfaces.SurfaceError):
        surfaces.check_claude("---\nname: x\n---\n", ["read"])  # no tools: inherits everything
    surfaces.check_claude("---\nname: x\ndescription: d\ntools: Read, Grep, Glob\n---\n", ["read", "search"])


@pytest.mark.parametrize("extra", ["permissionMode: bypassPermissions", "mcpServers: [x]", "hooks: {}",
                                   "model: opus", "tools: Read, Bash"])
def test_a_claude_projection_with_any_other_or_a_repeated_key_is_refused(extra):
    with pytest.raises(surfaces.SurfaceError):
        surfaces.check_claude(f"---\nname: x\ntools: Read, Grep, Glob\n{extra}\n---\n", ["read", "search"])


CODEX = "name = \"x\"\ndescription = \"d\"\nsandbox_mode = \"{mode}\"\ndeveloper_instructions = '''\nbody\n'''\n"


def test_codex_is_checked_against_agentteams_rule_never_rewritten():
    """G4 (0.2.8): agentteams' sandbox_mode_for, workspace-write exactly when the agent declares edit."""
    ro, ww = CODEX.format(mode="read-only"), CODEX.format(mode="workspace-write")
    for tools in (["read"], ["read", "search"], ["read", "search", "execute"], ["read", "search", "agent"]):
        assert surfaces.check_codex(ro, tools) is None
        with pytest.raises(surfaces.SurfaceError, match="agentteams' rule"):
            surfaces.check_codex(ww, tools)
    for tools in (["read", "edit"], ["read", "search", "edit", "execute"]):
        assert surfaces.check_codex(ww, tools) is None
        with pytest.raises(surfaces.SurfaceError, match="agentteams' rule"):
            surfaces.check_codex(ro, tools)
    with pytest.raises(surfaces.SurfaceError):
        surfaces.check_codex(CODEX.format(mode="danger-full-access"), ["read", "edit", "execute"])
    assert not hasattr(surfaces, "scope_codex") and not hasattr(surfaces, "NARROWED")


@pytest.mark.parametrize("version,ok", [("1.0.0rc9 (vcs-pin 9928a3a640b5)", True), ("1.0.0-rc.9", True),
                                        ("1.0.0", True), ("1.0.1rc1", True), ("1.0.0rc8", False),
                                        ("0.9.9", False), ("0.0.0-fake", False), ("unknown", False)])
def test_the_minimum_agentteams_version(version, ok):
    assert (surfaces.agentteams_too_old(version) is None) == ok, version


def test_sync_and_doctor_refuse_an_agentteams_older_than_the_minimum(instance, fake):
    old = Path(fake)
    old.write_text(old.read_text().replace("1.0.0rc9 (fake)", "1.0.0rc8"))
    r = mathagents("sync", "--write", cwd=instance, agentteams=fake)
    assert r.returncode != 0 and "older than 1.0.0rc9" in r.stdout + r.stderr and "no agent" in r.stdout + r.stderr
    r = mathagents("doctor", cwd=instance, agentteams=fake)
    assert r.returncode != 0 and "older than 1.0.0rc9" in r.stdout + r.stderr


# --- the researcher posture (D39): only the orchestrator writes ----------------------------------------------

# the nine pipeline agents: every exported agent but the two D39 leaves as they were
PIPELINE = tuple(a for a in _harness_files.AGENTS if a not in ("interpretation-advisor", "lean-informalization"))
EXECUTE = {"statement-formalizer", "lean-prover", "counterexample-hunter", "axiom-auditor"}


def test_the_pipeline_agents_hold_no_edit_and_keep_execute_where_held():
    for name in PIPELINE:
        assert name in _harness_files.AGENTS
        tools = surfaces.declared_tools((ROOT / ".github" / "agents" / f"{name}.agent.md").read_text())
        assert "edit" not in tools and "agent" not in tools, (name, tools)
        assert set(tools) == {"read", "search"} | ({"execute"} if name in EXECUTE else set()), (name, tools)


def test_the_pipeline_agents_project_without_a_write_tool_on_every_surface(instance, fake):
    for name in PIPELINE:
        claude = surface_file(instance, "claude", name).read_text()
        ctools = set(re.search(r"^tools: (.*)$", claude, re.M).group(1).split(", "))
        assert not ctools & {"Edit", "Write", "NotebookEdit", "Task"}, (name, ctools)
        assert ("Bash" in ctools) == (name in EXECUTE), (name, ctools)
        ext = surface_file(instance, "goose", name).read_text().split("\nextensions:\n")[1]
        granted = {t for line in re.findall(r"available_tools: \[(.*)\]", ext) for t in line.split(", ")}
        # `analyze` is listed only to switch it off (surfaces.ANALYZE_OFF)
        assert granted == {"tree", surfaces.ANALYZE_OFF} | ({"shell"} if name in EXECUTE else set()), (name, granted)
        assert "summon" not in ext, name
        assert 'sandbox_mode = "read-only"' in surface_file(instance, "codex", name).read_text(), name


@pytest.mark.parametrize("extra", ['approval_policy = "never"\n', "[mcp_servers.x]\ncommand = \"sh\"\n",
                                   'sandbox_mode = "read-only"\n', "not toml ===\n"])
def test_a_codex_projection_with_any_other_key_or_bad_toml_is_refused(extra):
    with pytest.raises(surfaces.SurfaceError):
        surfaces.check_codex(CODEX.format(mode="read-only") + extra, ["read"])


# --- the CLI ------------------------------------------------------------------------------------------------

def test_sync_writes_and_locks_every_surface(instance, fake):
    lock = json.loads((instance / "mathagents.lock.json").read_text())
    for name in _harness_files.AGENTS:
        for surface, directory in SURFACE_DIRS.items():
            f = surface_file(instance, surface, name)
            assert f.is_file() and os.path.relpath(f, instance) in lock["files"], (surface, name)
    assert lock["surfaces"] == {"surfaces": ["claude", "goose", "codex"], "agentteams": "1.0.0rc9 (fake)",
                                "goose_tool_map": surfaces.GOOSE_MAP_VERSION}
    recipe = surface_file(instance, "goose", "fidelity-auditor").read_text().split("\nextensions:\n")[1]
    assert "available_tools: [tree]" in recipe and "delegate" not in recipe and "shell" not in recipe
    assert "mathagents run" in surface_file(instance, "claude", "axiom-auditor").read_text()  # the rendered body
    r = mathagents("sync", cwd=instance, agentteams=fake)
    assert r.returncode == 0, r.stdout
    # D41: lean-informalization holds no edit, so Codex renders it read-only with nothing to narrow
    assert 'sandbox_mode = "read-only"' in surface_file(instance, "codex", "lean-informalization").read_text()
    assert 'sandbox_mode = "read-only"' in surface_file(instance, "codex", "lean-prover").read_text()  # D39


def test_a_retired_codex_opt_in_is_reported_and_ignored(instance, fake):
    """[agents] codex_workspace_write was retired in 0.2.8 (G4): a config that still sets it syncs, with a notice,
    and the Codex projection is unchanged (every pipeline agent stays read-only)."""
    marker = instance / "mathagents.toml"
    text = marker.read_text()
    assert 'surfaces = ["claude", "goose", "codex"]\n' in text
    marker.write_text(text.replace('surfaces = ["claude", "goose", "codex"]\n',
                                   'surfaces = ["claude", "goose", "codex"]\ncodex_workspace_write = []\n'))
    before = surface_file(instance, "codex", "lean-prover").read_bytes()
    r = mathagents("sync", "--write", cwd=instance, agentteams=fake)
    assert r.returncode == 0 and "codex_workspace_write is retired" in r.stdout, r.stdout + r.stderr
    assert surface_file(instance, "codex", "lean-prover").read_bytes() == before


@pytest.mark.parametrize("surface", ["goose", "claude", "codex"])
def test_the_learned_block_rule_covers_every_surface(instance, fake, surface):
    f = surface_file(instance, surface, "lean-prover")
    text = f.read_text()
    p = learned.parse(text, surfaces.SURFACES[surface][2])
    block = "".join(p.indent + line for line in f"{learned.BEGIN_MARKER}\n- a note\n{learned.END_MARKER}\n"
                    .splitlines(True))
    f.write_text(text[: p.insert_at] + "\n" + block + text[p.insert_at:])
    assert mathagents("sync", "--write", cwd=instance, agentteams=fake).returncode == 0
    assert "- a note" in f.read_text()
    f.write_text(f.read_text().replace("lean", "Lean", 1))  # an edit outside the block
    r = mathagents("sync", cwd=instance, agentteams=fake)
    assert r.returncode == 1 and f"conflict  {os.path.relpath(f, instance)}" in r.stdout
    assert f"{os.path.relpath(f, instance)}: missing or edited" in mathagents("doctor", cwd=instance).stdout


def test_a_widened_goose_recipe_reads_as_an_edit(instance, fake):
    f = surface_file(instance, "goose", "fidelity-auditor")
    f.write_text(f.read_text().replace("available_tools: [tree]", "available_tools: [tree, shell]"))
    assert mathagents("sync", cwd=instance, agentteams=fake).returncode == 1


def test_dropping_a_surface_untracks_it(instance, fake):
    marker = instance / "mathagents.toml"
    marker.write_text(marker.read_text().replace('surfaces = ["claude", "goose", "codex"]', 'surfaces = ["claude"]'))
    r = mathagents("sync", "--write", cwd=instance, agentteams=fake)
    assert r.returncode == 0 and "untracked ../../.goose/recipes/lean-prover.yaml" in r.stdout, r.stdout
    lock = json.loads((instance / "mathagents.lock.json").read_text())
    assert not any(k.endswith((".yaml", ".toml")) for k in lock["files"]) and lock["surfaces"]["surfaces"] == ["claude"]
    assert surface_file(instance, "goose", "lean-prover").is_file()  # the consumer's file now; never deleted


def test_a_failing_agentteams_writes_nothing(tmp_path, fake):
    inst = make_instance(tmp_path, 'surfaces = ["claude"]', fake)
    marker = inst / "mathagents.toml"
    marker.write_text(marker.read_text().replace('surfaces = ["claude"]', 'surfaces = ["claude", "goose"]'))
    before = sorted(p for p in (inst.parent.parent).rglob("*") if p.is_file())
    r = mathagents("sync", "--write", cwd=inst, agentteams="/nonexistent/agentteams")
    assert r.returncode != 0 and "no agent or surface file was written" in r.stdout + r.stderr
    assert sorted(p for p in (inst.parent.parent).rglob("*") if p.is_file()) == before


def test_no_surface_file_is_written_without_an_orchestrator(tmp_path, fake):
    """M2 with surfaces on: the refusal comes before any agent or surface file is written."""
    ws = tmp_path / "ws"
    (ws / "lean").mkdir(parents=True)
    inst = ws / "Projects" / "Demo"
    assert mathagents("init", str(inst), "--agents-to", "../../.github/agents", cwd=tmp_path).returncode == 0
    marker = inst / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# surfaces = ["claude", "goose", "codex"]',
                                                 'surfaces = ["claude", "goose", "codex"]'))
    r = mathagents("sync", "--write", cwd=inst, agentteams=fake)
    assert r.returncode == 2 and "only under an orchestrator" in r.stdout, r.stdout
    for d in [".github/agents", *SURFACE_DIRS.values()]:
        assert not (ws / d).exists(), d


def test_surfaces_need_a_github_agents_export(tmp_path, fake):
    inst = tmp_path / "inst"
    assert mathagents("init", str(inst), "--agents-to", "agents", cwd=tmp_path).returncode == 0
    marker = inst / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# surfaces = ["claude", "goose", "codex"]', 'surfaces = ["goose"]'))
    (inst / "agents").mkdir()  # an orchestrator is present (M2), so the refusal is about the surfaces
    (inst / "agents" / cli.ORCHESTRATOR).write_text("---\nname: Orchestrator\n---\n")
    r = mathagents("sync", "--write", cwd=inst, agentteams=fake)
    assert r.returncode != 0 and ".github/agents" in r.stdout + r.stderr


# --- the real toolchain (skipped when absent) ---------------------------------------------------------------

def real_agentteams() -> str | None:
    return os.environ.get("MATHAGENTS_TEST_AGENTTEAMS")


@pytest.mark.skipif(not real_agentteams(), reason="set MATHAGENTS_TEST_AGENTTEAMS to run against a real agentteams")
def test_real_agentteams_projection_is_scoped(tmp_path):
    """agentteams >= 1.0.0rc12: Goose recipes come in grant mode (agentteams_readfs, checked never wider than the
    agent's tools); the codex surface is frozen (the next test)."""
    inst = make_instance(tmp_path, 'surfaces = ["claude", "goose"]', real_agentteams())
    recipe = surface_file(inst, "goose", "fidelity-auditor").read_text().split("\nextensions:\n")[1]
    assert 'name: "agentteams_readfs"' in recipe and "name: developer" not in recipe and "summon" not in recipe
    assert "available_tools: [read_file, list_dir, find, grep, stat]" in recipe
    assert "tools: Read, Grep, Glob\n" in surface_file(inst, "claude", "fidelity-auditor").read_text()
    for name in PIPELINE:  # the researcher posture survives the real projection (D39)
        claude = surface_file(inst, "claude", name).read_text()
        assert not re.search(r"^tools: .*\b(Edit|Write)\b", claude, re.M), name
        ext = surface_file(inst, "goose", name).read_text().split("\nextensions:\n")[1]
        assert "write" not in ext and "summon" not in ext and "edit" not in ext, name
    assert mathagents("sync", cwd=inst, agentteams=real_agentteams()).returncode == 0  # deterministic


@pytest.mark.skipif(not real_agentteams(), reason="set MATHAGENTS_TEST_AGENTTEAMS to run against a real agentteams")
def test_real_agentteams_refuses_codex_without_its_capability_or_a_native_team(tmp_path):
    ws = tmp_path / "ws"
    (ws / "lean").mkdir(parents=True)
    orchestrator(ws / ".github" / "agents")
    inst = ws / "Projects" / "Demo"
    assert mathagents("init", str(inst), "--agents-to", "../../.github/agents", cwd=tmp_path).returncode == 0
    marker = inst / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# surfaces = ["claude", "goose", "codex"]', 'surfaces = ["codex"]'))
    r = mathagents("sync", "--write", cwd=inst, agentteams=real_agentteams(), codex_capable=None)
    # agentteams before #319 (1.1.0rc17) lacks the capability; from #319 on, an instance with no native Codex team is
    # refused before agentteams runs. Either way nothing is written.
    assert r.returncode != 0 and ("cannot import into Codex under write_policy" in r.stdout + r.stderr
                                  or "native Codex team" in r.stdout + r.stderr), r.stdout + r.stderr
    assert not (ws / ".codex").exists()  # nothing written


def test_the_pinned_goose_readfs_server_matches_agentteams():
    """Guard for the internal agentteams accessors the Goose projection uses (no public one before agentteams 1.1):
    an agentteams bump that moves the pin or the accessor fails here, not at a consumer's sync."""
    pytest.importorskip("agentteams")
    from agentteams.frameworks.goose_tool_scoping import READFS_SCRIPT, READFS_SHA256
    assert (READFS_SHA256, READFS_SCRIPT) == (surfaces.READFS_SHA256, surfaces.READFS_SCRIPT)
    assert surfaces._pinned_readfs()


def test_a_grant_mode_recipe_is_checked_never_wider():
    ok = surfaces._READFS_BLOCK
    dev = "  - type: builtin\n    name: developer\n    bundled: true\n    timeout: 300\n    available_tools: [shell, tree]\n"
    off = "  - type: platform\n    name: analyze\n    available_tools: [__none__]\n"
    load = "  - type: platform\n    name: summon\n    available_tools: [load]\n"
    surfaces.check_goose_grant(_with_extensions("extensions:\n" + ok), ["read", "search"])
    surfaces.check_goose_grant(_with_extensions("extensions:\n" + dev + off + ok), ["read", "search", "execute"])
    surfaces.check_goose_grant(_with_extensions("extensions:\n" + load + ok), ["read", "search", "agent"])
    for bad, tools in [(dev + off + ok, ["read", "search"]),                        # shell beyond read/search
                       ("", ["read", "search"]),                                     # no readfs entry
                       (ok + ok, ["read", "search"]),                                 # two readfs entries
                       (ok.replace("[read_file, list_dir, find, grep, stat]", "[read_file, write_file]"), ["read"]),
                       (ok.replace('"."', '"/"'), ["read", "search"]),                # readfs rooted elsewhere
                       ("  - type: stdio\n    name: operator_db\n    available_tools: [q]\n" + ok, ["read"])]:
        with pytest.raises(surfaces.SurfaceError, match="refused"):
            surfaces.check_goose_grant(_with_extensions("extensions:\n" + bad), tools)


@pytest.mark.skipif(not (real_agentteams() and shutil.which("goose")), reason="needs MATHAGENTS_TEST_AGENTTEAMS and goose")
def test_real_scoped_recipes_validate_with_goose(tmp_path):
    inst = make_instance(tmp_path, 'surfaces = ["goose"]', real_agentteams())
    for name in _harness_files.AGENTS:
        r = subprocess.run(["goose", "recipe", "validate", str(surface_file(inst, "goose", name))],
                           capture_output=True, text=True)
        assert r.returncode == 0, (name, r.stdout + r.stderr)


def test_the_checkout_refresh_scopes_its_own_recipes(tmp_path):
    recipes = tmp_path / "recipes"
    recipes.mkdir()
    (recipes / "engine-advisor.yaml").write_text('version: "1.0.0"\ntitle: "t"\ndescription: "d"\ninstructions: |\n'
                                                 "  body\nextensions:\n  - type: builtin\n    name: developer\n")
    assert surfaces.main(["scope-goose", str(ROOT / ".github" / "agents"), str(recipes), "engine-advisor"]) == 0
    assert "available_tools: [tree]" in (recipes / "engine-advisor.yaml").read_text()
    assert "summon" not in (recipes / "engine-advisor.yaml").read_text()  # never added: narrowing only
    assert not list(recipes.glob(".*"))  # no temporary file left behind
    assert surfaces.main(["scope-goose", str(ROOT / ".github" / "agents"), str(recipes), "no-such-agent"]) == 1


PILOT = json.loads((ROOT / "brief.json").read_text()).get("write_policy") == "orchestrator-only"
_BRIEF = json.loads((ROOT / "brief.json").read_text())
# Goose's bespoke recipes are agentteams grant-mode recipes only while Goose is covered by the switch or frozen as the
# pilot rendered them; an unfrozen Goose outside the switch (CX-3, UNENFORCED) is mathagents-scoped (refresh step 3b).
GOOSE_GRANT_MODE = PILOT and ("goose" in (_BRIEF.get("write_policy_frameworks") or ["goose"])
                              or "goose" in (_BRIEF.get("frozen_surfaces") or []))


def test_the_checkout_refresh_only_narrows_the_bespoke_agents():
    """Step 3b of scripts/refresh_agent_surfaces.sh. Under the pilot (D42) agentteams renders the bespoke recipes in
    grant mode and the step checks them with agentteams' own audit; with the pilot off, mathagents' scoping never
    grants an extension the checkout's recipe lacked (Goose adds `analyze` next to `developer` itself)."""
    if PILOT and not GOOSE_GRANT_MODE:
        # unfrozen and UNENFORCED (CX-3): step 3b runs check_bespoke_goose.py, which defers to mathagents' scoping, and
        # the scoping is a fixed point of the committed recipes (it never grants an extension a re-render would drop)
        pytest.importorskip("agentteams.audit")
        r = subprocess.run([sys.executable, str(ROOT / "scripts/lib/check_bespoke_goose.py"), str(ROOT / ".goose/recipes"),
                            str(ROOT / "brief.json"), *_harness_files.AGENTS], capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 3 and "the pilot is off for goose" in r.stdout, r.stdout + r.stderr  # step 3b's defer code
        for name in _harness_files.AGENTS:
            recipe = (ROOT / ".goose" / "recipes" / f"{name}.yaml").read_text()
            tools = surfaces.declared_tools((ROOT / ".github" / "agents" / f"{name}.agent.md").read_text())
            assert surfaces.scope_goose(recipe, tools) == recipe, name
        return
    if PILOT:
        pytest.importorskip("agentteams.audit")
        brief = ROOT / "brief.json"
        frameworks = json.loads(brief.read_text()).get("write_policy_frameworks")
        if frameworks and "goose" not in frameworks:
            # The switch covers Claude only (agentteams #204 refuses goose under it), and Jim froze the Goose
            # recipes as the pilot rendered them (2026-10-15). Hold the frozen recipes to the grant-mode audit, so
            # nothing widens while they are frozen.
            frozen = json.loads(brief.read_text())
            frozen["write_policy_frameworks"] = [*frameworks, "goose"]
            brief = Path(tempfile.mkdtemp()) / "brief.json"
            brief.write_text(json.dumps(frozen))
        r = subprocess.run([sys.executable, str(ROOT / "scripts/lib/check_bespoke_goose.py"), str(ROOT / ".goose/recipes"),
                            str(brief), *_harness_files.AGENTS], capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout + r.stderr
        return
    for name in _harness_files.AGENTS:
        recipe = (ROOT / ".goose" / "recipes" / f"{name}.yaml").read_text()
        tools = surfaces.declared_tools((ROOT / ".github" / "agents" / f"{name}.agent.md").read_text())
        before = set(re.findall(r"^    name: (\w+)$", recipe.split("\nextensions:\n")[1], re.M)) | {"analyze"}
        after = set(re.findall(r"^    name: (\w+)$", surfaces.scope_goose(recipe, tools), re.M))
        assert after <= before, (name, after - before)


@pytest.mark.parametrize("line", ["tools: [read, search", "tools: ['read', 3]", "tools: read"])
def test_an_unreadable_tools_list_is_a_surface_error(line):
    with pytest.raises(surfaces.SurfaceError):
        surfaces.declared_tools(f"---\nname: x\n{line}\n---\n")


def test_analyze_is_switched_off_by_a_name_no_tool_has_never_by_an_empty_list():
    """Goose 1.37 adds `analyze` beside `developer` unless the recipe lists it, reads an empty available_tools as
    "no restriction" (agentteams spike A1), and `analyze` reaches outside the workspace (B1). A non-matching name
    is the only off switch (A2). Pin the exact text so it is never "simplified" to `[]`."""
    for tools in (["read"], ["read", "search"], ["read", "search", "edit"], ["read", "search", "execute"],
                  ["read", "search", "edit", "execute", "agent"]):
        ext = scoped(tools)
        assert surfaces.ANALYZE_OFF == "__none__"  # never `[]` (spike A1)
        assert f"  - type: platform\n    name: analyze\n    available_tools: [{surfaces.ANALYZE_OFF}]\n" in ext, tools
        assert "available_tools: []" not in ext and "available_tools: [analyze" not in ext, tools


def test_a_tool_set_that_cannot_read_is_refused():
    with pytest.raises(surfaces.SurfaceError, match="without read or search"):
        surfaces.goose_extensions(["edit", "execute"])



def _with_extensions(section: str) -> str:
    """fidelity-auditor's recipe with its extensions section replaced (independent of where the key sits)."""
    recipe = (ROOT / ".goose" / "recipes" / "fidelity-auditor.yaml").read_text()
    kept = [(k, v) for k, v in surfaces._sections(recipe) if k != "extensions"]
    return "".join(v if v.endswith("\n") else v + "\n" for _, v in kept) + section


READFS = '  - type: stdio\n    name: agentteams_readfs\n    cmd: python3\n    available_tools: [read_file]\n'


@pytest.mark.parametrize("section", [
    "extensions:\n  - type: stdio\n    name: operator_db\n    cmd: db-mcp\n    available_tools: [query]\n",
    "extensions:\n" + READFS,
    "extensions:\n  - type: stdio\n    cmd: unnamed-mcp\n",
    # a nested name: is not the entry's own
    "extensions:\n  - type: stdio\n    cmd: x\n    envs:\n      name: developer\n",
    "extensions:\n    - type: stdio\n      name: operator_db\n",                  # four-space items
])
def test_an_extension_mathagents_does_not_grant_is_refused_not_dropped(section):
    with pytest.raises(surfaces.SurfaceError, match="refused rather than dropped"):
        surfaces.scope_goose(_with_extensions(section), ["read", "search"])


def test_column_0_extension_items_are_refused_by_the_top_level_guard():
    with pytest.raises(surfaces.SurfaceError, match="unreadable top-level recipe line"):
        surfaces.scope_goose(_with_extensions("extensions:\n- type: stdio\n  name: operator_db\n"), ["read", "search"])


@pytest.mark.parametrize("section", [
    "extensions: []\n", "extensions:\n", "extensions:\n  # nothing here\n",
    "extensions:\n  - type: builtin\n    name: developer\n    bundled: true\n",
])
def test_an_empty_or_builtin_extensions_section_still_scopes(section):
    assert "available_tools: [tree]" in surfaces.scope_goose(_with_extensions(section), ["read", "search"])


def test_every_committed_bespoke_recipe_still_scopes():
    """With the pilot off the checkout's recipes are mathagents-scoped and must rescope. Under the pilot they are
    agentteams' grant-mode recipes (D42), which mathagents' consumer scoping refuses rather than drops (agentteams_readfs
    is not in its map); test_the_checkout_refresh_only_narrows_the_bespoke_agents checks them instead."""
    for name in _harness_files.AGENTS:
        recipe = (ROOT / ".goose" / "recipes" / f"{name}.yaml").read_text()
        tools = surfaces.declared_tools((ROOT / ".github" / "agents" / f"{name}.agent.md").read_text())
        if GOOSE_GRANT_MODE:
            assert "agentteams_readfs" in recipe and "# agentteams-declared-tools:" in recipe, name
            with pytest.raises(surfaces.SurfaceError, match="agentteams_readfs"):
                surfaces.scope_goose(recipe, tools)
        else:
            surfaces.scope_goose(recipe, tools)


def test_codex_is_refused_without_agentteams_codex_interop(tmp_path, fake):
    """No #319 capability (the probe says no): sync refuses the codex surface and writes nothing."""
    ws = tmp_path / "ws"
    (ws / "lean").mkdir(parents=True)
    orchestrator(ws / ".github" / "agents")
    native_codex(ws)
    inst = ws / "Projects" / "Demo"
    assert mathagents("init", str(inst), "--agents-to", "../../.github/agents", cwd=tmp_path).returncode == 0
    marker = inst / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# surfaces = ["claude", "goose", "codex"]', 'surfaces = ["codex"]'))
    r = mathagents("sync", "--write", cwd=inst, agentteams=fake, codex_capable=False)
    assert r.returncode != 0 and "cannot import into Codex under write_policy" in r.stdout + r.stderr
    assert not list((ws / ".codex" / "agents").glob("*.toml"))


def test_codex_is_refused_without_the_instance_native_codex_team(tmp_path, fake):
    """#319 accepts codex only into a native team: with its gate files missing, nothing is written."""
    ws = tmp_path / "ws"
    (ws / "lean").mkdir(parents=True)
    orchestrator(ws / ".github" / "agents")
    native_codex(ws)
    (ws / ".codex" / "hooks.json").unlink()
    inst = ws / "Projects" / "Demo"
    assert mathagents("init", str(inst), "--agents-to", "../../.github/agents", cwd=tmp_path).returncode == 0
    marker = inst / "mathagents.toml"
    marker.write_text(marker.read_text().replace('# surfaces = ["claude", "goose", "codex"]', 'surfaces = ["codex"]'))
    r = mathagents("sync", "--write", cwd=inst, agentteams=fake)
    assert r.returncode != 0 and "native Codex team" in r.stdout + r.stderr and ".codex/hooks.json" in r.stdout + r.stderr
    assert not list((ws / ".codex" / "agents").glob("*.toml"))


@pytest.mark.parametrize("older,newer", [("1.1.0.dev0", "1.1.0rc12"), ("1.1.0rc12", "1.1.0rc17 (vcs-pin 8d0a4bc989f5)"),
                                         ("1.1.0rc17", "1.1.0"), ("1.0.0", "1.1.0.dev0")])
def test_version_key_orders_dev_builds_and_vcs_pins(older, newer):
    assert surfaces.version_key(older) < surfaces.version_key(newer)
    assert surfaces.agentteams_too_old("1.1.0.dev0") is None
