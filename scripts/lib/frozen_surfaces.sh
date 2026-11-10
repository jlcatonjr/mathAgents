# shellcheck shell=bash
# Surfaces the operator froze (D43; shared release policy §5: Codex stays frozen for 1.0 in a team with adopted
# agents; Goose, and the Goose-owned AGENTS.md, stay as rendered before M6). The list is brief.json "frozen_surfaces",
# the same key researchteam 1.0.1's update and autosync gate honour, so the gate and this repository's refresh can't
# disagree. MATHAGENTS_FROZEN_SURFACES (space-separated, e.g. "goose codex") may still be set, but only to the same
# set: a mismatch stops the run. A frozen surface keeps its committed files: a render must leave it byte-identical to
# HEAD. Source it from the repository root.
# Usage: source scripts/lib/frozen_surfaces.sh; is_frozen codex && ...
# Validated as researchteam 1.0.1 validates it (researchteam/_frozen.py load): an absent key or [] freezes nothing; a
# non-array value, an unknown surface id or a duplicate stops the run, so a value either reader would refuse is never
# read here as "nothing frozen".
_MATHAGENTS_FROZEN="$(python3 -I -c '
import json, sys
ids = ("copilot-vscode", "copilot-cli", "claude", "goose", "agents-md", "codex", "grok")
brief = json.load(open("brief.json"))
value = brief.get("frozen_surfaces", []) if isinstance(brief, dict) else []
if not isinstance(value, list):
    sys.exit(f"brief.json frozen_surfaces must be a JSON array, not {type(value).__name__}")
bad = [v for v in value if not isinstance(v, str) or v not in ids]
if bad or len(set(value)) != len(value):
    sys.exit("brief.json frozen_surfaces has unknown or duplicate id(s): %r; allowed: %s" % (value, ", ".join(ids)))
print(" ".join(sorted(value)))')" \
  || { echo "frozen_surfaces: cannot read a valid brief.json frozen_surfaces (see above)" >&2; exit 1; }
_env_raw="${MATHAGENTS_FROZEN_SURFACES:-}"
if [[ -n "${_env_raw//[[:space:]]/}" ]]; then
  _env_frozen="$(tr ' ' '\n' <<<"$MATHAGENTS_FROZEN_SURFACES" | { grep -v '^$' || true; } | sort | tr '\n' ' ')"
  [[ "${_env_frozen% }" == "$_MATHAGENTS_FROZEN" ]] || {
    echo "frozen_surfaces: MATHAGENTS_FROZEN_SURFACES ($MATHAGENTS_FROZEN_SURFACES) differs from brief.json frozen_surfaces ($_MATHAGENTS_FROZEN); stopping" >&2
    exit 1
  }
fi
is_frozen() { [[ " $_MATHAGENTS_FROZEN " == *" $1 "* ]]; }
