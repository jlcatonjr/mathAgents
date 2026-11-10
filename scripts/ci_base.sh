#!/usr/bin/env bash
# Print the commit CI compares against (IA-01): a pull request's base; otherwise the newest commit
# with a successful Gates run on main that is an ancestor of HEAD. With no such commit, or no access
# to the runs API, the root commit (slower, never weaker), with a workflow warning on stderr.
#   EVENT=<github.event_name> PR_BASE=<sha> REPO=<owner/name> GH_TOKEN=<token> bash scripts/ci_base.sh
set -uo pipefail
if [ "${EVENT:-}" = pull_request ]; then
  printf '%s\n' "${PR_BASE:?pull_request event without PR_BASE}"
  exit 0
fi
for sha in $(gh api "repos/${REPO:?}/actions/workflows/gates.yml/runs?branch=main&status=success&per_page=50" \
    --jq '.workflow_runs[].head_sha' 2>/dev/null); do
  if git merge-base --is-ancestor "$sha" HEAD 2>/dev/null; then printf '%s\n' "$sha"; exit 0; fi
done
root="$(git rev-list --max-parents=0 HEAD | tail -n 1)"
echo "::warning::no successful Gates run found (or the runs API failed); walking every commit from the root $root" >&2
printf '%s\n' "$root"
