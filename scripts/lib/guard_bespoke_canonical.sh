#!/usr/bin/env bash
# Keep the bespoke agents' canonical .github sources across `researchteam update`.
#
# The bespoke agents are canonical in .github/agents (decision records D24, D27, D28). researchteam's scholarly
# layer-2 sync manages .github/agents/interpretation-advisor.agent.md with its "above-notes" strategy (researchteam
# 90f497a): upstream owns everything above "## Project-Specific Notes", so an update replaces our retargeted agent
# with researchteam's (it reached main that way in the 2026-10-14 autosync, f6be803). researchteam 1.0.0rc1 (#50)
# keeps a customised file, so every script that runs `researchteam update` now brackets it with snapshot + verify:
# a changed canonical source stops the run (a researchteam regression) instead of being repaired silently.
#
# Usage:
#   guard_bespoke_canonical.sh snapshot DIR AGENT...   copy .github/agents/<AGENT>.agent.md into DIR (all must exist)
#   guard_bespoke_canonical.sh verify   DIR AGENT...   fail, naming each file the update changed; changes nothing
# Exit: 0 = done (verify: unchanged); 1 = a source is missing, a copy failed, or (verify) a file changed; 2 = usage.
set -euo pipefail
die() { echo "[guard-bespoke] ERROR: $*" >&2; exit 1; }
[[ $# -ge 3 ]] || { echo "usage: $0 snapshot|verify DIR AGENT..." >&2; exit 2; }
mode="$1" dir="$2"; shift 2
case "$mode" in
  snapshot)
    mkdir -p "$dir"
    for a in "$@"; do
      [[ -f ".github/agents/$a.agent.md" ]] || die "canonical bespoke agent missing: .github/agents/$a.agent.md"
      cp ".github/agents/$a.agent.md" "$dir/" || die "cannot snapshot $a"
    done ;;
  verify)
    changed=0
    for a in "$@"; do
      [[ -f "$dir/$a.agent.md" ]] || die "no snapshot of $a in $dir"
      if ! cmp -s "$dir/$a.agent.md" ".github/agents/$a.agent.md"; then
        echo "[guard-bespoke] ERROR: researchteam update changed the canonical bespoke .github/agents/$a.agent.md" >&2
        changed=1
      fi
    done
    [[ $changed -eq 0 ]] || die "researchteam update changed bespoke canonical sources (it should keep them, researchteam #50); the files are tracked: git checkout HEAD -- .github/agents/<agent>.agent.md" ;;
  *) echo "usage: $0 snapshot|verify DIR AGENT..." >&2; exit 2 ;;
esac
