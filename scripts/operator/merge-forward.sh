#!/bin/bash -p
# OPERATOR ONLY, plain terminal. After a mathAgents tag: merge the session-prepared merge-forward PR (the release line
# -> main; after a final X.Y.0 tag it may also move main to the next .dev0) at its reviewed head, regular merge, after
# checking in a fresh clone that the PR's head merges the verified tag and nothing else.
#   PR=<n> MF_HEAD=<40-hex> TAG=v1.1.0 NEXT_DEV=1.2.0.dev0 \
#   /bin/bash -p "$HOME/githubrepositories/mathAgents/scripts/operator/merge-forward.sh"
# NEXT_DEV is optional: when set, the script warns unless main's version at the PR head equals it.
# Derived 2026-11-06 from agentteams-f3's cleared derived-phase-t/merge-forward.sh (sha256 94750b70…), which
# mathAgents ran after v1.0.0 on 2026-10-19. Changes from it: mathAgents only (no REPO variable); the fixed
# "v1.0.0 -> 1.1.0.dev0" warning is the optional NEXT_DEV variable. Every check is unchanged.
# Privileged mode only: -p ignores caller-exported functions (even `builtin`) and $BASH_ENV.
# Invoke as `/bin/bash -p <path>` or via the shebang, NEVER `bash <path>`. Only keywords are used in this guard.
if [[ $- == *p* ]]; then
set -euo pipefail
SCRIPT="$0"; # Invoke by ABSOLUTE path: bash 3.2 still honours CDPATH under -p.
HERE="$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")" && pwd -P)"; . "$HERE/lib_release.sh"
clean_reexec PR MF_HEAD TAG NEXT_DEV -- "$@"
neutralise
PR="${PR:?}"; MF_HEAD="${MF_HEAD:?}"; TAG="${TAG:?TAG=vX.Y.Z}"; NEXT_DEV="${NEXT_DEV:-}"
[[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$ ]] || die "not a release tag name: $TAG"
[[ "$MF_HEAD" =~ ^[0-9a-f]{40}$ && "$PR" =~ ^[0-9]+$ ]] || die "PR must be a number and MF_HEAD 40-hex"
[[ -z "$NEXT_DEV" || "$NEXT_DEV" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.dev0$ ]] || die "NEXT_DEV must be X.Y.Z.dev0"
repo_info
TMP=$(/usr/bin/mktemp -d); trap 'rm -rf "$TMP"' EXIT
fresh_clone "$TMP/repo"
verify_release_tag "$TAG"
V=$("${GITX[@]}" rev-parse "$TAG^{commit}")
base=$("$GH" pr view "$PR" -R "$GH_REPO" --json baseRefName --jq .baseRefName); [[ "$base" == main ]] || die "#$PR targets $base, not main"
head=$("$GH" pr view "$PR" -R "$GH_REPO" --json headRefOid --jq .headRefOid); [[ "$head" == "$MF_HEAD" ]] || die "#$PR head is $head, not $MF_HEAD"
"${GITX[@]}" fetch -q origin "pull/$PR/head"
"${GITX[@]}" merge-base --is-ancestor "$V" "$MF_HEAD" || die "$MF_HEAD does not contain $TAG ($V)"
"${GITX[@]}" merge-base --is-ancestor origin/main "$MF_HEAD" || die "$MF_HEAD is not based on current main"
# For the operator's review, in full: every file the PR changes on main, and every non-merge commit it brings that is
# neither on main nor in the tag (expected: only the main -> next-dev version commit, if any).
echo "== files the PR changes on main (full):"; "${GITX[@]}" --no-pager diff --stat=200 origin/main "$MF_HEAD"
echo "== non-merge commits in the PR beyond main and $TAG:"; "${GITX[@]}" --no-pager log --oneline --no-merges "$MF_HEAD" ^origin/main "^$V"
if [[ -n "$NEXT_DEV" ]]; then
  nv=$(version_at "$MF_HEAD" 2>/dev/null || echo "?"); [[ "$nv" == "$NEXT_DEV" ]] || echo "WARNING: main's version at the PR head is $nv, not $NEXT_DEV"
fi
wait_for_green_ci "$PR"
yes_or_stop "Merge #$PR (merge-forward after $TAG) at ${MF_HEAD:0:10} with a regular merge?"
"$GH" pr merge "$PR" -R "$GH_REPO" --merge --match-head-commit "$MF_HEAD"
echo "done. Sessions: re-sync your checkouts with git pull --ff-only; check git status for untracked residue."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
