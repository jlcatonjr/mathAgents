#!/usr/bin/env bash
# Agent roster and tools-posture test (spec DD-24, DD-25; decision records D27, D34, D39).
# Part 1, the stage agents (D27): each must exist on all four surfaces, be listed in BESPOKE_AGENTS
# and the orchestrator rosters, and carry exactly its charter posture (as amended by D27 and D39) on the
# Copilot, Claude and Codex files: read-only agents get no write or command tools; only agents granted
# `execute` get Bash. Goose scoping is checked by tests/test_surfaces.py.
# Part 2, every agent (D34): no surface grants more than the canonical `tools:` list (see below).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
python3 - <<'PY'
import json, re, sys, tomllib
from pathlib import Path

STAGE_AGENTS = ["statement-formalizer", "fidelity-auditor", "proof-strategist", "logic-articulator",
                "tactic-planner", "lean-prover", "counterexample-hunter",            # D27
                "axiom-auditor", "engine-advisor", "lean-informalization"]           # D28
# Postures come from charter §5 (docs/charter/01-initiating-prompt.md), not from the agent files, so a
# drift in either is caught. Recorded amendments (decision D27) are listed here and must also appear in
# the D27 row of docs/charter/03-decisions.md.
AMENDMENTS = {"statement-formalizer": {"execute"}}
# D39 (2026-10-06): the pipeline agents are researchers; only the orchestrator writes. `edit` is revoked from
# every agent §5 gave it to here, and must be named in the D39 row of docs/charter/03-decisions.md.
REVOKED = {a: {"edit"} for a in ("statement-formalizer", "proof-strategist", "logic-articulator", "tactic-planner",
                                 "lean-prover")}
# D41 (2026-10-07, write-policy pilot): lean-informalization drops `edit` and returns change-proposals; recorded in
# the D41 row.
REVOKED_D41 = {"lean-informalization": {"edit"}}
# reading and searching are open to every agent; `agent` (hand-off) is still permitted by this check, but since the
# conformance commit and D39 no pipeline agent holds it: each returns to the orchestrator, which dispatches
BASE = {"read", "search", "agent"}
fails = []
def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)

charter = Path("docs/charter/01-initiating-prompt.md").read_text()
table = dict(re.findall(r"^\|\s*`@([a-z-]+)`\s*\|[^|]*\|\s*([^|]+?)\s*\|\s*$", charter, re.M))
def posture(words: str) -> set[str]:
    w = words.lower()
    if w.startswith("read-only"):
        return {"read", "search"}  # no hand-off either: a read-only agent must not delegate writes
    granted = set(BASE)
    if w.startswith("write"):
        granted.add("edit")
    if "bash" in w:
        granted.add("execute")
    return granted
# D45: the full charter stays in the archived private repository; the public tree carries the summary, whose rows
# are not edited after the fact. The grants themselves are checked below either way; only the cross-check that the
# full charter recorded each amendment needs the full charter.
FULL_CHARTER = Path("docs/charter/03-decisions.md")
POSTURE = {}
for name in STAGE_AGENTS:
    check(name in table, f"{name}: has a posture in charter §5")
    POSTURE[name] = ((posture(table.get(name, "")) | AMENDMENTS.get(name, set())) - REVOKED.get(name, set())
                     - REVOKED_D41.get(name, set()))
if FULL_CHARTER.is_file():
    d27 = next((l for l in FULL_CHARTER.read_text().splitlines() if l.startswith("| D27 |")), "")
    for name, extra in AMENDMENTS.items():
        check(name in d27 and all(f"`{t}`" in d27 for t in extra), f"{name}: amendment {sorted(extra)} recorded in D27")
    d39 = next((l for l in FULL_CHARTER.read_text().splitlines() if l.startswith("| D39 |")), "")
    for name, gone in REVOKED.items():
        check(f"`{name}`" in d39 and all(f"`{t}`" in d39 for t in gone), f"{name}: revocation {sorted(gone)} recorded in D39")
    d41 = next((l for l in FULL_CHARTER.read_text().splitlines() if l.startswith("| D41 |")), "")
    for name, gone in REVOKED_D41.items():
        check(f"`{name}`" in d41 and all(f"`{t}`" in d41 for t in gone), f"{name}: revocation {sorted(gone)} recorded in D41")
else:
    print("note: docs/charter/03-decisions.md is not in this tree (D45); the D27/D39/D41 record cross-check is skipped")

bespoke = re.search(r"^BESPOKE_AGENTS=\(([^)]*)\)", Path("scripts/refresh_agent_surfaces.sh").read_text(), re.M)
bespoke = set(bespoke.group(1).split()) if bespoke else set()
orch = Path(".github/agents/orchestrator.agent.md").read_text()
orch_text = orch.split("\n---", 1)[0]
goose_orch = Path(".goose/recipes/orchestrator.yaml").read_text()
# D41: under agentteams' write-policy pilot the render narrows every non-orchestrator agent on the pilot's
# surfaces to read and search, so there the Claude file holds neither write tools nor Bash.
_brief = json.loads(Path("brief.json").read_text())
PILOT_CLAUDE = _brief.get("write_policy") == "orchestrator-only" and "claude" in _brief.get("write_policy_frameworks", [])

for name, want in POSTURE.items():
    gh = Path(f".github/agents/{name}.agent.md")
    cl, gs, cx = Path(f".claude/agents/{name}.md"), Path(f".goose/recipes/{name}.yaml"), Path(f".codex/agents/{name}.toml")
    for p in (gh, cl, gs, cx):
        check(p.is_file(), f"{name}: {p} exists")
    if not gh.is_file():
        continue
    check(name in bespoke, f"{name}: listed in BESPOKE_AGENTS")
    check(re.search(rf"^\s*-\s*{re.escape(name)}\s*$", orch_text, re.M) is not None, f"{name}: in the Copilot orchestrator roster")
    check(f'"./{name}.yaml"' in goose_orch, f"{name}: a Goose orchestrator sub-recipe")
    m = re.search(r"^tools:\s*\[([^\]]*)\]", gh.read_text(), re.M)
    got = {t.strip().strip("'\"") for t in m.group(1).split(",")} if m else set()
    check(got <= want and (want - BASE) <= got and "read" in got,
          f"{name}: Copilot tools {sorted(got)} fit posture {sorted(want)} (privileged grants exact)")
    if cl.is_file():
        m = re.search(r"^tools:\s*(.*)$", cl.read_text(), re.M)
        ctools = {t.strip() for t in m.group(1).split(",")} if m else set()
        cwant = want - {"edit", "execute"} if PILOT_CLAUDE else want
        writes = bool(ctools & {"Edit", "Write", "NotebookEdit"})
        check(writes == ("edit" in cwant), f"{name}: Claude write tools {'present' if writes else 'absent'} matches posture")
        check(("Bash" in ctools) == ("execute" in cwant), f"{name}: Claude Bash {'present' if 'Bash' in ctools else 'absent'} matches posture")
    if cx.is_file():
        data = tomllib.loads(cx.read_text())
        if "edit" not in want:  # read-only and, since D39, command-running researchers: their commands never write
            check(data.get("sandbox_mode") == "read-only", f"{name}: Codex sandbox_mode read-only")

print(f"domain agents: {len(POSTURE)} agents, {len(fails)} failure(s): " + ("FAIL" if fails else "PASS"))
sys.exit(1 if fails else 0)
PY

# Every agent on every surface (IA-02; charter D34). A surface may never grant more than the
# canonical tools allow. Violations the agentteams projection still produces are listed in KNOWN, each
# tracked by the request to agentteams; the list only shrinks: a new violation fails, and a listed
# one that no longer occurs fails until it is removed here. Goose read-only and command-running
# recipes carry `developer` by accepted risk (D34) and are reported, not failed.
python3 - <<'PY'
import sys, tomllib
from pathlib import Path
sys.path.insert(0, "scripts/lib")
import agent_postures as ap

# The 12 Codex gaps once listed here were fixed by agentteams#100 (request
# 2026-10-03-agentteams-capability-postures.md) and removed on 2026-10-05.
KNOWN = {  # (surface, agent, violation) -> tracked by
}
# The Goose bridge-orchestrator entry (a bridge-generated orphan) was removed on 2026-11-09 with the
# copilot-vscode-to-goose bridge (CX-3).
# The Claude workstream-expert entry (a bridge-generated orphan with Task) was removed on 2026-10-27 with the
# copilot-vscode-to-claude bridge (native-projection Phase 1).
# The Claude team-builder entry (canonical tokens in its tools: line, D41) was fixed by agentteams#147 and
# removed on 2026-10-08 with the render at agentteams 2072362.
team = ap.canonical_team(Path("."))
import json
_brief = json.loads(Path("brief.json").read_text())
PILOT_CLAUDE = _brief.get("write_policy") == "orchestrator-only" and "claude" in _brief.get("write_policy_frameworks", [])
found, accepted = set(), []
surfaces = {"claude": (Path(".claude/agents"), "*.md"), "codex": (Path(".codex/agents"), "*.toml"),
            "goose": (Path(".goose/recipes"), "*.yaml")}
for surface, (d, pat) in surfaces.items():
    files = {p.stem: p for p in d.glob(pat)  # agent files only (YAML front matter / a recipe), not READMEs
             if p.suffix != ".md" or p.read_text(encoding="utf-8").startswith("---")}
    for slug in sorted(set(team) - set(files)):
        found.add((surface, slug, "missing"))
    for slug in sorted(set(files) - set(team)):
        found.add((surface, slug, "orphan (no canonical agent)"))
    for slug in sorted(set(team) & set(files)):
        tools, cls, f = team[slug], ap.posture(team[slug]), files[slug]
        if surface == "claude":
            have = ap.claude_tools(f)
            extra = None if have is None else have - ap.claude_allowed(tools)
            if extra and PILOT_CLAUDE:  # D41: the write-policy narrowing always keeps `read` (Claude: Read)
                extra = extra - {"Read"}
                # D43 (M6): exactly the runner tools brief.json's mcp_grants gives this agent, nothing more
                grant = (_brief.get("mcp_grants") or {}).get(slug) or {}
                extra = extra - {f"mcp__agentteams_runner__{t}" for t in grant.get("tools", [])}
            if have is None:
                found.add((surface, slug, "no tools: line (a Claude agent without one inherits every tool)"))
            elif extra:
                found.add((surface, slug, f"Claude tools beyond the canonical grant: {sorted(extra)}"))
        elif surface == "codex":
            mode = tomllib.loads(f.read_text(encoding="utf-8")).get("sandbox_mode")
            if mode == "danger-full-access":
                found.add((surface, slug, "sandbox_mode danger-full-access (no agent may run unsandboxed)"))
            elif cls == "RO" and mode != "read-only":
                found.add((surface, slug, "read-only role without sandbox_mode read-only"))
            elif cls == "RX" and mode is None:
                found.add((surface, slug, "command-running role without a sandbox_mode"))
        elif cls in ("RO", "RX") and "name: developer" in f.read_text(encoding="utf-8"):
            accepted.append(slug)
fails = 0
for v in sorted(found - set(KNOWN)):
    print(f"FAIL {v[0]} {v[1]}: {v[2]}"); fails += 1
for v in sorted(set(KNOWN) - found):
    print(f"FAIL {v[0]} {v[1]}: listed as known ({KNOWN[v]}) but no longer occurs; remove it from KNOWN"); fails += 1
for v in sorted(found & set(KNOWN)):
    print(f"known {v[0]} {v[1]}: {v[2]} (tracked: {KNOWN[v]})")
print(f"accepted risk (D34): {len(accepted)} Goose read-only/command-running recipes carry developer")
print(f"all agents: {len(team)} canonical agents, 3 surfaces, {len(found)} violation(s) "
      f"({len(found & set(KNOWN))} known), {fails} failure(s): " + ("FAIL" if fails else "PASS"))
sys.exit(1 if fails else 0)
PY
