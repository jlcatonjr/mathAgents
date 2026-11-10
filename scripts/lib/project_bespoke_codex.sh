#!/usr/bin/env bash
# Import the bespoke pipeline agents into the native Codex team (CX-3; agentteams #319, 1.1.0rc17+).
#   bash scripts/lib/project_bespoke_codex.sh
# Under write_policy "orchestrator-only" covering codex, agentteams accepts codex as an interop target only into the
# project's native .codex/agents, rendered under the switch first (researchteam's _refresh_codex): its build-log, the
# role gate (.agentteams/bin/codex-role-gate.py), .codex/hooks.json and the launcher. The imported agents come out
# read-only; the role gate denies every spawned agent's writes. The bespoke list is the one in
# scripts/refresh_agent_surfaces.sh (BESPOKE_AGENTS), canonical in .github/agents.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
die() { echo "[codex-bespoke] ERROR: $*" >&2; exit 1; }
read -r -a BESPOKE <<< "$(sed -n 's/^BESPOKE_AGENTS=(\(.*\))$/\1/p' scripts/refresh_agent_surfaces.sh)"
[[ ${#BESPOKE[@]} -gt 0 ]] || die "cannot read BESPOKE_AGENTS from scripts/refresh_agent_surfaces.sh"
for f in .codex/agents/references/build-log.json .agentteams/bin/codex-role-gate.py .codex/hooks.json \
         .codex/confined-run.example.sh; do
  [[ -f "$f" && ! -L "$f" ]] || die "no native Codex team under the switch ($f missing); render it first"
done
# Run the reviewed agentteams (toolchain.lock), through its own interpreter, never a bare `agentteams` on PATH.
python3 scripts/lib/agentteams_provenance.py || die "agentteams provenance check failed (see above)"
PY_AT="$(python3 scripts/lib/agentteams_provenance.py --interpreter-of agentteams)" || die "cannot find agentteams' interpreter"
at() { "$PY_AT" -I -c 'import sys, build_team; sys.argv[0] = "agentteams"; sys.exit(build_team.main())' "$@"; }
SRC="$(mktemp -d)"; trap 'rm -rf "$SRC"' EXIT
for a in "${BESPOKE[@]}"; do
  [[ -f ".github/agents/$a.agent.md" ]] || die "canonical bespoke agent missing: .github/agents/$a.agent.md"
  cp ".github/agents/$a.agent.md" "$SRC/"
done
at --interop-from "$SRC" --framework codex --output .codex/agents --description brief.json --overwrite --yes \
  >/dev/null || die "agentteams refused the Codex import (see above)"
for a in "${BESPOKE[@]}"; do
  grep -q '^sandbox_mode = "read-only"$' ".codex/agents/$a.toml" || die ".codex/agents/$a.toml is not read-only"
done
echo "[codex-bespoke] imported ${#BESPOKE[@]} bespoke agent(s) into the native Codex team, read-only"
