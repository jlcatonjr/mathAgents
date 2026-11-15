#!/usr/bin/env bash
# Install the tmp/ private-paths guard (scripts/hooks/private-paths-guard.sh) into this checkout's pre-commit hook.
# The block goes directly after the shebang, so it runs before agentteams' fenced blocks (the last of which ends
# with `exit`). Idempotent: an existing MATHAGENTS:private-paths-guard block is replaced, not duplicated.
# Re-run after `agentteams --install-git-hooks` (or scripts/refresh_agent_surfaces.sh) if that rewrites the hook.
#   bash scripts/install_private_paths_guard.sh
set -euo pipefail
ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
HOOK="$(git -C "$ROOT" rev-parse --git-path hooks/pre-commit)"
case "$HOOK" in /*) ;; *) HOOK="$ROOT/$HOOK";; esac
BEGIN='# >>> MATHAGENTS:private-paths-guard >>>'
END='# <<< MATHAGENTS:private-paths-guard <<<'
BLOCK="$BEGIN
# Installed by scripts/install_private_paths_guard.sh. BLOCKING: refuses staged paths under tmp/.
_ma_root=\"\$(git rev-parse --show-toplevel 2>/dev/null)\"
if [ -n \"\$_ma_root\" ] && [ -f \"\$_ma_root/scripts/hooks/private-paths-guard.sh\" ]; then
    sh \"\$_ma_root/scripts/hooks/private-paths-guard.sh\" || exit 1
else
    echo \"mathAgents: WARNING: scripts/hooks/private-paths-guard.sh not found; tmp/ files are NOT being checked\" >&2
fi
$END"
mkdir -p "$(dirname "$HOOK")"
[ -f "$HOOK" ] || printf '#!/bin/sh\n' > "$HOOK"
python3 - "$HOOK" "$BEGIN" "$END" "$BLOCK" <<'EOF'
import re, sys
path, begin, end, block = sys.argv[1:]
s = open(path).read()
s = re.sub(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", "", s, flags=re.S)
lines = s.split("\n", 1)
if lines[0].startswith("#!"):
    s = lines[0] + "\n" + block + "\n" + (lines[1] if len(lines) > 1 else "")
else:
    s = "#!/bin/sh\n" + block + "\n" + s
open(path, "w").write(s)
EOF
chmod +x "$HOOK"
echo "installed private-paths guard in $HOOK"
