#!/usr/bin/env bash
# Keep the committed Codex team marker when a re-projection changed nothing but its timestamp.
# agentteams (d31d4a0) rewrites .codex/agents/references/build-log.json on every projection with a
# fresh `generated_at`; until agentteams PR #98 makes an unchanged rewrite byte-identical, this
# restores the committed file so a no-op render leaves no git diff. Any other field change is kept.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
M=.codex/agents/references/build-log.json
git ls-files --error-unmatch "$M" >/dev/null 2>&1 || exit 0   # not committed yet: nothing to restore
git diff --quiet -- "$M" && exit 0
if python3 - "$M" <<'PY'
import json, subprocess, sys
path = sys.argv[1]
old = json.loads(subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout)
new = json.loads(open(path, encoding="utf-8").read())
old.pop("generated_at", None)
new.pop("generated_at", None)
sys.exit(0 if old == new else 1)
PY
then
  git checkout -- "$M"
  echo "[codex-marker] only generated_at changed; committed marker kept"
fi
