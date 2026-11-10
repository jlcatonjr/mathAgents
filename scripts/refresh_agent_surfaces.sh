#!/usr/bin/env bash
# Full, repeatable refresh of every agent surface from brief.json via researchteam + agentteams.
#   1. researchteam update              layer-2 framework sync, plus a layer-1 merge (non-destructive)
#   2. bespoke agents                   derive claude/goose forms of each BESPOKE agent (no agentteams
#                                       template) from its canonical .github/agents file (agentteams interop,
#                                       with --description brief.json: agentteams #174 applies the write
#                                       policy, D41, to the imported agents when the brief enables it)
#   3. researchteam materialize --adopt-orphans --no-codex
#                                       overwrite re-render of copilot-vscode, claude and goose, with
#                                       bespoke agents adopted into every roster; agentteams (P5a+, checked
#                                       before the render) carries the Project-Specific Notes and Rules; then
#                                       Codex agents and skills are re-projected from the rendered sources
#   3b. goose grant check               under the pilot, agentteams renders the bespoke recipes in grant mode
#                                       (agentteams_readfs); they are checked with agentteams' own audit
#                                       (scripts/lib/check_bespoke_goose.py). With the pilot off for goose,
#                                       each recipe is scoped to its tools: instead (python3 -m
#                                       mathagents._surfaces scope-goose; narrowing only)
#   4. consistency check                scripts/check_render_consistency.sh (fails closed)
#
# Step 3 needs an operator-signed (Ed25519) `overwrite` row in each rendered surface's decisions log: the gate
# refuses an unsigned one. The operator signs it with the root-owned signer (scripts/operator/lib_signer.sh;
# docs/release-policy.md section 7) before the run; this script never writes clearances.
#
#   bash scripts/refresh_agent_surfaces.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
# Bespoke agents: canonical in .github/agents, no agentteams template (decision records D24, D27, D28).
BESPOKE_AGENTS=(interpretation-advisor statement-formalizer fidelity-auditor proof-strategist logic-articulator tactic-planner lean-prover counterexample-hunter axiom-auditor engine-advisor lean-informalization)
die()  { echo "[refresh] ERROR: $*" >&2; exit 1; }
step() { echo "[refresh] === $* ==="; }

bash scripts/lib/require_cli_flag.sh --adopt-orphans researchteam materialize \
  || die "researchteam CLI missing or predates consolidated materialize; reinstall researchteam"

# A render must run reviewed agentteams code, not whatever branch a shared editable checkout holds right now.
python3 scripts/lib/agentteams_provenance.py || die "agentteams provenance check failed (see above)"
python3 scripts/lib/agentteams_provenance.py --researchteam || die "researchteam provenance check failed (see above)"
# Python steps import agentteams and researchteam, so they run under those CLIs' own interpreters: the `python3`
# first on PATH may be another environment without them (the first P5 run stopped at step 3a on exactly that).
PY_AT="$(python3 scripts/lib/agentteams_provenance.py --interpreter-of agentteams)" || die "cannot find agentteams' interpreter"
PY_RT="$(python3 scripts/lib/agentteams_provenance.py --interpreter-of researchteam)" || die "cannot find researchteam's interpreter"

# Step 2 relies on agentteams #174 (--description on --interop-from): refuse an agentteams older than mathagents'
# floor (MIN_AGENTTEAMS in mathagents/_surfaces.py) here, rather than fail later with an unclear derivation error.
"$PY_AT" -c 'import sys; from mathagents._surfaces import agentteams_too_old, agentteams_version
p = agentteams_too_old(agentteams_version()); print(p or "", file=sys.stderr); sys.exit(1 if p else 0)' \
  || die "agentteams is older than mathagents supports (see above)"

T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
# researchteam update never touches Codex here: --no-codex (researchteam #64) skips its Codex step, so .codex and
# .agents/skills must still equal HEAD afterwards. Codex is rendered once, in step 3a, when it is not frozen (CX-3: a
# native render under orchestrator-only, then the bespoke agents imported into it; agentteams #319), so a
# write-protected .codex can't fail step 1 halfway.
source scripts/lib/frozen_surfaces.sh
UPDATE_ARGS=(--yes --no-codex)
is_frozen codex && echo "[refresh] Codex is frozen (brief.json frozen_surfaces): left unchanged" \
  || echo "[refresh] Codex: rendered in step 3a, not by researchteam update"
# CX-3 (operator ruling 2026-11-09): an unfrozen Codex or Goose needs agentteams v1.1.0 or later (#319) and the
# operator's Ed25519-signed unfreeze-<surface> row, which researchteam itself verifies; fail early and clearly.
for s in codex goose; do
  is_frozen "$s" && continue
  bash scripts/lib/require_unfreeze_toolchain.sh "$s" || die "unfreeze-$s: toolchain or signed row missing (see above)"
done
# researchteam update must keep the canonical bespoke agents (researchteam #50); verified, never repaired here.
bash scripts/lib/guard_bespoke_canonical.sh snapshot "$T/canonical" "${BESPOKE_AGENTS[@]}"

# Native projection, no thin bridges (operator decision 2026-10-27; native-projection Phase 1): a surface that is not
# frozen must be rendered natively by agentteams, never by a copilot-vscode bridge. Fail closed, before and after the
# render, on a bridge directory, a bridge-generated agent (researchteam's own bridge_outputs: the `bridge:` front-matter
# key) or an AGENTTEAMS-BRIDGE fence for that surface. Frozen surfaces keep theirs until they are unfrozen (Phase 2).
bridge_guard() {
  "$PY_RT" - "$1" <<'PY' || die "bridge guard ($1): a non-frozen surface is bridged (see above); retire the bridge, don't adopt it"
import re, subprocess, sys
from pathlib import Path
from researchteam._drift import bridge_frameworks, bridge_outputs
frozen = set(subprocess.run(["bash", "-c", "source scripts/lib/frozen_surfaces.sh && echo $_MATHAGENTS_FROZEN"],
                            capture_output=True, text=True, check=True).stdout.split())
root, bad = Path("."), []
for fw in ("claude", "goose"):
    if fw in frozen:
        continue
    if fw in bridge_frameworks(root):
        bad.append(f"references/bridges/copilot-vscode-to-{fw}/ exists")
    bad += [f"{p}: bridge-generated agent" for p in bridge_outputs(root, fw)]
    base = root / (".claude" if fw == "claude" else ".goose")
    for f in sorted(base.rglob("*")) if base.is_dir() else []:
        if f.is_file() and f.suffix in (".md", ".yaml", ".json"):
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                sys.exit(f"bridge guard: cannot read {f} ({exc}); failing closed")
            if re.search(r"<!-- AGENTTEAMS-BRIDGE:BEGIN", text):
                bad.append(f"{f}: AGENTTEAMS-BRIDGE fence")
for b in bad:
    print(f"[refresh] bridge guard: {b}", file=sys.stderr)
sys.exit(1 if bad else 0)
PY
  echo "[refresh] bridge guard ($1): no bridge on a non-frozen surface"
}
bridge_guard before

step "1/4 researchteam update (sync + merge)"
researchteam update "${UPDATE_ARGS[@]}" >/dev/null || die "researchteam update failed"
bash scripts/lib/guard_bespoke_canonical.sh verify "$T/canonical" "${BESPOKE_AGENTS[@]}"
if true; then  # step 1 always runs --no-codex
  git diff --quiet HEAD -- .codex .agents/skills && [[ -z "$(git status --porcelain -- .codex .agents/skills)" ]] \
    || die "researchteam update --no-codex changed the frozen Codex surface (.codex, .agents/skills)"
fi

step "2/4 derive bespoke agents for claude/goose: ${BESPOKE_AGENTS[*]}"
mkdir -p "$T/src"
for a in "${BESPOKE_AGENTS[@]}"; do
  [[ -f ".github/agents/$a.agent.md" ]] || die "canonical bespoke agent missing: .github/agents/$a.agent.md"
  cp ".github/agents/$a.agent.md" "$T/src/"
done
# With --description, agentteams (#174, 1.0.0rc9+) carries the brief's write policy into the imported agents: under
# the pilot (D41; Claude only since D43) their Claude forms are narrowed to read/search and carry the Return Proposals
# section, or the agentteams_runner grant for the agents in mcp_grants; Goose renders off the switch (agentteams
# refuses orchestrator-only on Goose: GOOSE_SWITCH_REFUSED), grant-scoped in step 3b (UNENFORCED, CX-3).
# With the pilot off the brief changes nothing (agentteams pins that byte for byte).
# Derive into $T/proj in the canonical shape: with mcp_grants (M6) agentteams installs the agentteams_runner server
# next to the agents directory and refuses any --output that is not a project's .claude/agents or .goose/recipes.
# A fresh $T holds no agents, so --overwrite (required under the switch) can't replace anything of ours. Only the
# 11 bespoke files and the runner server are copied back; interop's side files (runtime-handoffs.json, Goose team
# marker and control plane) stay in $T, since the native render owns the live ones.
agentteams --interop-from "$T/src" --framework claude --output "$T/proj/.claude/agents" --description brief.json \
  --overwrite --yes >/dev/null || die "claude derivation failed"
# agentteams rc.12 (#210) has Goose interop read through agentteams_readfs and refuses unless the pinned server is at
# the output project's scripts/. Give the temp project the copy agentteams ships (package data), never a local one.
mkdir -p "$T/proj/scripts"
"$PY_AT" -c 'import agentteams, pathlib, shutil, sys
shutil.copyfile(pathlib.Path(agentteams.__file__).parent / "data" / "goose-readfs-mcp.py", sys.argv[1])' \
  "$T/proj/scripts/goose-readfs-mcp.py" || die "cannot stage agentteams' goose-readfs-mcp.py for the Goose derivation"
agentteams --interop-from "$T/src" --framework goose  --output "$T/proj/.goose/recipes" --description brief.json \
  --overwrite --yes >/dev/null || die "goose derivation failed"
for a in "${BESPOKE_AGENTS[@]}"; do  # all-or-nothing: check every derived file before replacing any live one
  [[ -f "$T/proj/.claude/agents/$a.md" && -f "$T/proj/.goose/recipes/$a.yaml" ]] || die "interop did not derive $a"
done
for a in "${BESPOKE_AGENTS[@]}"; do
  cp "$T/proj/.claude/agents/$a.md"   ".claude/agents/$a.md"
  cp "$T/proj/.goose/recipes/$a.yaml" ".goose/recipes/$a.yaml"
done
# An unfrozen Goose runs the bespoke recipes as derived, and they launch the pinned readfs server at scripts/ (agentteams
# rc.12+, #210): install the copy agentteams ships (staged above, from its package data), never a local edit.
if ! is_frozen goose; then
  READFS=scripts/goose-readfs-mcp.py
  "$PY_AT" -c 'import hashlib, sys; from agentteams.frameworks.goose_tool_scoping import READFS_SHA256
sys.exit(0 if hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest() == READFS_SHA256 else 1)' "$T/proj/$READFS" \
    || die "the staged goose-readfs server does not match agentteams' pinned READFS_SHA256"
  if [[ -f "$READFS" ]]; then
    cmp -s "$T/proj/$READFS" "$READFS" || die "installed $READFS differs from the one agentteams ships: " \
      "remove it under a C-5 row if it is a stale pin, never edit it"
  else
    cp "$T/proj/$READFS" "$READFS"; echo "[refresh] installed agentteams' pinned $READFS"
  fi
fi
RUNNER_MCP=.agentteams/bin/agentteams-runner-mcp.py
if "$PY_AT" -c 'import json, sys; sys.exit(0 if json.load(open("brief.json")).get("mcp_grants") else 1)'; then
  [[ -f "$T/proj/$RUNNER_MCP" ]] || die "brief.json has mcp_grants but interop installed no agentteams_runner server"
  "$PY_AT" -c 'import hashlib, sys; from agentteams.runner_mcp import SHA256
sys.exit(0 if hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest() == SHA256 else 1)' "$T/proj/$RUNNER_MCP" \
    || die "agentteams_runner server does not match agentteams' pinned sha256"
  if [[ -f "$RUNNER_MCP" ]]; then
    cmp -s "$T/proj/$RUNNER_MCP" "$RUNNER_MCP" || die "installed $RUNNER_MCP differs from the one agentteams ships: " \
      "an agentteams upgrade changed the server; stop the runner, remove $RUNNER_MCP, re-run, then restart the runner"
  else
    mkdir -p "$(dirname "$RUNNER_MCP")"; cp "$T/proj/$RUNNER_MCP" "$RUNNER_MCP"
  fi
fi

# Once agentteams recognises .codex as a team (interop team marker, agentteams d31d4a0), the Claude
# sandbox block write-denies .codex for in-session Bash. Then Codex is projected by the operator,
# outside the session: scripts/operator/refresh_codex_projection.sh.
codex_writable=1
if [[ -d .codex/agents ]] && ! ( : > .codex/agents/.write-probe ) 2>/dev/null; then codex_writable=0; fi
rm -f .codex/agents/.write-probe 2>/dev/null || true
# The overwrite render must keep every agent's Project-Specific Notes and every instruction file's Project-Specific
# Rules. agentteams carries both on --overwrite since P5a (agentteams f113f5d), and refuses rather than drop one; an
# older agentteams drops them (D39's render erased the orchestrator's duties, CA-023/CA-031). Refuse to render with
# an agentteams that lacks the carry (its marker is the --discard-user-regions opt-out, which this script never passes).
bash scripts/lib/require_cli_flag.sh --discard-user-regions agentteams \
  || die "agentteams missing or predates P5a (f113f5d): its --overwrite would drop Project-Specific Notes/Rules; update it"
step "3/4 researchteam materialize --adopt-orphans --no-codex (copilot, claude, goose)"
researchteam materialize --yes --adopt-orphans --no-codex >/dev/null || die "materialize failed (missing overwrite clearance row?)"
# Under write_policy researchteam re-renders the covered Claude team natively (researchteam #46). The bespoke forms
# derived in step 2 are authoritative, so put back any the native render changed (a template sharing a bespoke
# agent's name, such as interpretation-advisor, would otherwise win).
for a in "${BESPOKE_AGENTS[@]}"; do
  for pair in ".claude/agents/$a.md" ".goose/recipes/$a.yaml"; do
    if ! cmp -s "$T/proj/$pair" "$pair"; then
      echo "[refresh] re-asserting the bespoke $pair over the native render"; cp "$T/proj/$pair" "$pair"
    fi
  done
done
if is_frozen codex; then
  echo "[refresh] Codex is frozen (brief.json frozen_surfaces): step 3a skipped"
elif [[ $codex_writable -eq 1 ]]; then
  step "3a/4 project Codex from the rendered .github/agents"
  "$PY_RT" -c "from pathlib import Path; from researchteam._update_cmd import _refresh_codex; _refresh_codex(Path('.'), dry_run=False)" \
    || die "Codex projection failed"
  # The native render (write_policy covering codex) holds only agentteams' templates; the bespoke pipeline agents are
  # imported into it under the switch (CX-3; agentteams #319).
  bash scripts/lib/project_bespoke_codex.sh || die "bespoke Codex import failed"
  bash scripts/lib/restore_codex_marker.sh
else
  echo "[refresh] NOTE: .codex is write-protected in this session. Run, outside the agent session:"
  echo "[refresh]       bash scripts/operator/refresh_codex_projection.sh"
fi

step "3b/4 check (pilot) or scope (pilot off) the bespoke agents' Goose recipes"
# A surface the operator froze (D43: Goose until the 1.0 render) keeps its committed files; the caller restores them
# after this run, so checking or scoping the render's discarded output would only fail on agentteams' newer shape
# (rc.12 recipes read through agentteams_readfs, which mathagents' scoper refuses rather than drops).
if is_frozen goose; then
  echo "[refresh] Goose is frozen (brief.json frozen_surfaces): step 3b skipped; .goose is restored from git below"
  rc=0
else
  rc=0; "$PY_AT" scripts/lib/check_bespoke_goose.py .goose/recipes brief.json "${BESPOKE_AGENTS[@]}" || rc=$?
fi
if [[ $rc -eq 3 ]]; then
  "$PY_AT" -m mathagents._surfaces scope-goose "$T/src" .goose/recipes "${BESPOKE_AGENTS[@]}" \
    || die "goose scoping failed (no recipe was changed)"
elif [[ $rc -ne 0 ]]; then
  die "the bespoke Goose recipes fail agentteams' grant/write-policy audit (see above)"
fi
if ! is_frozen goose; then  # every Goose recipe's stdio server must exist (rc.17 moved readfs to scripts/)
  "$PY_AT" - <<'PY' || die "a Goose recipe launches a server file that is not in the repository (see above)"
import re, sys
from pathlib import Path
bad = []
for r in sorted(Path(".goose/recipes").glob("*.yaml")):
    for path in re.findall(r'^\s*-\s*"((?:scripts|\.agentteams/bin)/[^"]+\.py)"\s*$', r.read_text(encoding="utf-8"), re.M):
        if not Path(path).is_file():
            bad.append(f"{r}: {path}")
for b in bad:
    print(f"[refresh] goose server missing: {b}", file=sys.stderr)
sys.exit(1 if bad else 0)
PY
fi

if is_frozen goose; then  # put the committed recipes back (tracked files only); new untracked render output stops the run
  # AGENTS.md is Goose-owned (Goose reads it with .goosehints), so it is frozen with Goose (and serves Codex too)
  # the security gate marks a used single-use clearance in each surface's decisions log, Goose's too: keep that write
  GLOG=.goose/recipes/references/security-decisions.log.csv
  cp "$GLOG" "$T/goose-decisions.log.csv" || die "could not save the Goose decisions log"
  git checkout HEAD -- .goose AGENTS.md || die "could not restore the frozen .goose and AGENTS.md from git"
  cp "$T/goose-decisions.log.csv" "$GLOG" || die "could not put back the Goose decisions log"
  [[ -z "$(git status --porcelain -- .goose AGENTS.md ":!$GLOG")" ]] || die "frozen .goose/AGENTS.md still differs from HEAD (untracked render output?)"
  echo "[refresh] frozen Goose restored from git"
fi
step "4/4 consistency check"
bash scripts/check_render_consistency.sh
bridge_guard after
