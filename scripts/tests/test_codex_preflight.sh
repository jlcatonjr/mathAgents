#!/usr/bin/env bash
# Codex preflight test (IA-02, operator decision D-c): static posture checks, request dedupe,
# --no-write, and the live sentinel probe, on fixture trees. Portable (no GNU-only sed).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PF="$ROOT/scripts/codex_preflight.py"
T="$(mktemp -d)"; trap 'chmod -R u+w "$T"; rm -rf "$T"' EXIT
fails=0
check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }

fixture() {  # fixture DIR RO_SANDBOX(read-only|none)
  local d="$1"; mkdir -p "$d/.github/agents" "$d/.codex/agents"
  printf -- "---\ntools: ['read', 'search']\n---\n" > "$d/.github/agents/auditor.agent.md"
  printf -- "---\ntools: ['read', 'edit', 'execute']\n---\n" > "$d/.github/agents/writer.agent.md"
  printf -- "---\ntools: ['read', 'search', 'execute']\n---\n" > "$d/.github/agents/runner.agent.md"
  printf 'name = "runner"\nsandbox_mode = "read-only"\ndeveloper_instructions = %s\n' "'x'" > "$d/.codex/agents/runner.toml"
  { echo 'name = "auditor"'; [[ "$2" == read-only ]] && echo 'sandbox_mode = "read-only"'; echo "developer_instructions = 'x'"; } > "$d/.codex/agents/auditor.toml"
  printf 'name = "writer"\ndeveloper_instructions = %s\n' "'x'" > "$d/.codex/agents/writer.toml"
}
REQ="references/agentteams-feedback"
nreq() { find "$1/$REQ" -name '*-agentteams-codex-preflight-*.md' 2>/dev/null | wc -l | tr -d ' '; }

fixture "$T/clean" read-only
set +e; out="$(python3 "$PF" --root "$T/clean")"; rc=$?; set -e
check "clean tree: exit 0" '[[ $rc -eq 0 && "$out" == *"no findings"* ]]'

fixture "$T/ro" none
set +e; out="$(python3 "$PF" --root "$T/ro")"; rc=$?; set -e
check "RO agent without read-only sandbox: exit 1, HIGH finding" '[[ $rc -eq 1 && "$out" == *"HIGH"*"auditor"* ]]'
check "  one request file written" '[[ "$(nreq "$T/ro")" == 1 ]]'
check "  request carries a fingerprint" 'grep -q "^- fingerprint: \`[0-9a-f]\{12\}\`" "$T/ro/$REQ"/*.md'
set +e; out="$(python3 "$PF" --root "$T/ro")"; rc=$?; set -e
check "rerun: already reported, no second file" '[[ $rc -eq 1 && "$out" == *"already reported"* && "$(nreq "$T/ro")" == 1 ]]'

fixture "$T/nw" none
set +e; out="$(python3 "$PF" --root "$T/nw" --no-write)"; rc=$?; set -e
check "--no-write: prints the request, writes nothing" '[[ $rc -eq 1 && "$out" == *"# Request to agentteams"* && "$(nreq "$T/nw")" == 0 ]]'

fixture "$T/orphan" read-only
printf 'name = "ghost"\ndeveloper_instructions = %s\n' "'x'" > "$T/orphan/.codex/agents/ghost.toml"
rm "$T/orphan/.codex/agents/writer.toml"
set +e; out="$(python3 "$PF" --root "$T/orphan" --no-write)"; rc=$?; set -e
check "roster drift: orphan and missing agent reported" '[[ $rc -eq 1 && "$out" == *"ghost"*"orphan"* && "$out" == *"writer"*"no Codex agent"* ]]'

fixture "$T/live" read-only
set +e; out="$(python3 "$PF" --root "$T/live" --live --agent runner --no-write)"; rc=$?; set -e
check "live, read-only sandbox_mode but writable: ceiling finding" '[[ $rc -eq 1 && "$out" == *"ceiling"* && "$out" == *"repository writable"* ]]'
check "  sentinel removed" '[[ -z "$(find "$T/live" -maxdepth 1 -name ".codex-preflight-*")" ]]'
set +e; out="$(python3 "$PF" --root "$T/live" --live --agent writer --no-write)"; rc=$?; set -e
check "live, W agent writable: no finding" '[[ $rc -eq 0 ]]'
set +e; out="$(python3 "$PF" --root "$T/live" --live --agent auditor --no-write 2>&1)"; rc=$?; set -e
check "live as a read-only role: refused (C-3), exit 2" '[[ $rc -eq 2 && "$out" == *"C-3"* ]]'

fixture "$T/rx" read-only
rm "$T/rx/.codex/agents/runner.toml"; printf 'name = "runner"\ndeveloper_instructions = %s\n' "'x'" > "$T/rx/.codex/agents/runner.toml"
set +e; out="$(python3 "$PF" --root "$T/rx" --no-write)"; rc=$?; set -e
check "RX agent without a sandbox_mode: MEDIUM finding" '[[ $rc -eq 1 && "$out" == *"MEDIUM"*"runner"* ]]'

fixture "$T/fwd" none
mkdir -p "$T/fwd/.github/agents/references/cross-orchestrator-requests"
python3 "$PF" --root "$T/fwd" >/dev/null || true
mv "$T/fwd/$REQ"/*.md "$T/fwd/.github/agents/references/cross-orchestrator-requests/"
set +e; out="$(python3 "$PF" --root "$T/fwd")"; rc=$?; set -e
check "forwarded request still counts as reported" '[[ $rc -eq 1 && "$out" == *"already reported"* && "$(nreq "$T/fwd")" == 0 ]]'

if [[ $EUID -ne 0 ]]; then
fixture "$T/blocked" read-only
chmod a-w "$T/blocked"
set +e; out="$(python3 "$PF" --root "$T/blocked" --live --agent runner)"; rc=$?; set -e
chmod u+w "$T/blocked"
check "live, read-only filesystem: no ceiling finding" '[[ $rc -eq 0 && "$out" == *"not writable"* ]]'
fi

set +e; python3 "$PF" --root "$T/live" --live >/dev/null 2>&1; rc=$?; set -e
check "--live without --agent: usage error" '[[ $rc -eq 2 ]]'
set +e; python3 "$PF" --root "$T" >/dev/null 2>&1; rc=$?; set -e
check "no team directories: exit 2" '[[ $rc -eq 2 ]]'

echo "codex preflight: $fails failure(s): $([[ $fails -eq 0 ]] && echo PASS || echo FAIL)"
exit $(( fails > 0 ))
