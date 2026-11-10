#!/usr/bin/env bash
# OPERATOR SCRIPT — run outside the agent session.
# Re-projects the Codex surface (.codex/agents and .agents/skills) from the canonical Copilot team and
# the Claude skills, using researchteam's own Codex step (interop with --overwrite, stale-agent prune,
# team-marker check). It is needed once agentteams recognises .codex as a team: the Claude sandbox
# block then write-denies .codex for in-session Bash, so scripts/refresh_agent_surfaces.sh renders
# every other surface and asks you to run this.
#
#   bash scripts/operator/refresh_codex_projection.sh
#
# Afterwards: review `git diff -- .codex .agents`, then commit (the agent session can commit it).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
# Run under researchteam's own interpreter: the `python3` first on PATH may be another environment without it.
PY_RT="$(python3 scripts/lib/agentteams_provenance.py --interpreter-of researchteam)" || { echo "[codex] cannot find researchteam's interpreter" >&2; exit 1; }
"$PY_RT" -c "from pathlib import Path; from researchteam._update_cmd import _refresh_codex; _refresh_codex(Path('.'), dry_run=False)"
bash scripts/lib/project_bespoke_codex.sh   # the bespoke pipeline agents, into the native team (CX-3; agentteams #319)
bash scripts/lib/restore_codex_marker.sh
bash scripts/check_render_consistency.sh
echo "[codex] done. Review: git diff --stat -- .codex .agents"
