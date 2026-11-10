#!/usr/bin/env bash
# SUPERSEDED: signing was paused on 2026-09-30 (D21) and has since resumed. The current path is
# scripts/refresh_agent_surfaces.sh under an operator-signed `overwrite` row minted with the root-owned
# signer (scripts/operator/lib_signer.sh; docs/release-policy.md section 7). Kept for its history only.
# OPERATOR-ONLY: sign one `overwrite` clearance per agent surface, then re-render all three
# surfaces (Copilot via `researchteam materialize`; Claude Code and Goose via agentteams
# native renders). Run it from a plain terminal, never from inside an agent session.
#
#   bash scripts/operator/signed_render_all.sh "why this render is being cleared"
#
# The signing key is read with a hidden prompt (or taken from AGENTTEAMS_DECISION_SIGNING_KEY if
# already set). It lives only in this process and is never written to disk or shell history.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
SURFACES=(".github/agents" ".claude/agents" ".goose/recipes")

die() { echo "[signed-render] ERROR: $*" >&2; exit 1; }
step() { echo; echo "[signed-render] === $* ==="; }

# --- preflight ---------------------------------------------------------------------------------
[[ $# -eq 1 && -n "${1// }" ]] || die "usage: $0 \"<conditions: what was reviewed and why>\""
CONDITIONS="$1"

# The key must never enter an agent's environment (docs/researchteam-framework.md).
for v in CLAUDECODE CLAUDE_CODE_SESSION_ID GOOSE_SESSION_ID GOOSE_TERMINAL; do
  [[ -z "${!v:-}" ]] || die "agent session detected (\$$v is set). Run this from a plain terminal."
done

command -v researchteam >/dev/null || die "researchteam CLI not found"
command -v agentteams >/dev/null || die "agentteams CLI not found"
[[ -f scripts/sign_security_decision.py ]] || die "scripts/sign_security_decision.py missing (run: researchteam update)"
python -c "import agentteams" 2>/dev/null || die "agentteams is not importable by 'python'"
for s in "${SURFACES[@]}"; do
  [[ -f "$s/references/security-decisions.log.csv" ]] || die "missing decisions log in $s"
done

if [[ -z "${AGENTTEAMS_DECISION_SIGNING_KEY:-}" ]]; then
  read -rsp "[signed-render] Signing key (input hidden): " AGENTTEAMS_DECISION_SIGNING_KEY; echo
  [[ -n "$AGENTTEAMS_DECISION_SIGNING_KEY" ]] || die "empty key"
fi
export AGENTTEAMS_DECISION_SIGNING_KEY
DESC="$(mktemp --suffix=.json)"
trap 'unset AGENTTEAMS_DECISION_SIGNING_KEY; rm -f "$DESC"' EXIT

# --- 1. one signed clearance per surface --------------------------------------------------------
step "1/4 signing overwrite clearances"
for s in "${SURFACES[@]}"; do
  python scripts/sign_security_decision.py --action overwrite --conditions "$CONDITIONS" \
    --log "$s/references/security-decisions.log.csv" || die "signing failed for $s"
done

# --- 2. Copilot surface (roster reconciled from _build-description.json) -----------------------
step "2/4 researchteam materialize (Copilot)"
researchteam materialize --yes || die "materialize failed"

# --- 3/4. native Claude Code and Goose surfaces ------------------------------------------------
python - "$DESC" <<'PY'
import json, sys
b = json.load(open("brief.json")); b.pop("layer2_profile", None)  # researchteam-only key
json.dump(b, open(sys.argv[1], "w"))
PY
step "3/4 agentteams native render (Claude Code)"
agentteams --description "$DESC" --framework claude --project . --update --overwrite --materialize-native --yes \
  || die "claude render failed"
step "4/4 agentteams native render (Goose)"
agentteams --description "$DESC" --framework goose --project . --update --overwrite --materialize-native --yes \
  || die "goose render failed"

echo
echo "[signed-render] DONE. All three surfaces rendered. Nothing is committed; hand back to the"
echo "[signed-render] orchestrator for verification (rosters, stale references, gates) before commit."
