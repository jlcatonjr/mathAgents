#!/bin/bash -p
# OPERATOR ONLY, plain terminal. Merge mathAgents' release PR into its release line at the reviewed head, check the
# merge commit in a fresh clone, then sign THAT commit with the repository's own reviewed signer, taken from the
# verified merge commit (never from a working checkout) and matching the sha256 the operator approved.
#   PR=<n> REL_HEAD=<40-hex> PREV_HEAD=<40-hex: the release line's head before the merge> \
#   LINE=release/1.1 EXPECT_VERSION=1.1.0 SIGNER_SHA256=<64-hex> TAGGER_EMAIL=<e-mail> KEY="$HOME/.ssh/<key>" \
#   /bin/bash -p "$HOME/githubrepositories/mathAgents/scripts/operator/release-merge-and-sign.sh"
# Derived 2026-11-06 from agentteams-f3's cleared derived-phase-t/release-merge-and-sign.sh (sha256 916edcf1…), which
# signed mathAgents v1.0.0 on 2026-10-19. Changes from it: mathAgents only (no REPO variable); the release line is the
# LINE variable (default release/1.1) instead of a fixed release/1.0, and EXPECT_VERSION defaults to 1.1.0. Every
# check is unchanged, except that the signer is given gh and no python (CA-154). SIGNER_SHA256 comes from the operator's own `shasum -a 256` of
# origin/<LINE>:scripts/operator/tag-release.sh, never from a session's output.
# Privileged mode only: -p ignores caller-exported functions (even `builtin`) and $BASH_ENV.
# Invoke as `/bin/bash -p <path>` or via the shebang, NEVER `bash <path>`. Only keywords are used in this guard.
if [[ $- == *p* ]]; then
set -euo pipefail
SCRIPT="$0"; # Invoke by ABSOLUTE path: bash 3.2 still honours CDPATH under -p.
HERE="$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")" && pwd -P)"; . "$HERE/lib_release.sh"
clean_reexec PR REL_HEAD PREV_HEAD LINE SIGNER_SHA256 TAGGER_NAME TAGGER_EMAIL KEY EXPECT_VERSION -- "$@"
neutralise
PR="${PR:?PR=<number>}"
REL_HEAD="${REL_HEAD:?}"; PREV_HEAD="${PREV_HEAD:?}"; SIGNER_SHA256="${SIGNER_SHA256:?}"; KEY="${KEY:?}"
LINE="${LINE:-release/1.1}"; EXPECT_VERSION="${EXPECT_VERSION:-1.1.0}"
[[ "$LINE" =~ ^release/[0-9]+\.[0-9]+$ ]] || die "LINE must be release/X.Y"
[[ "$REL_HEAD" =~ ^[0-9a-f]{40}$ && "$PREV_HEAD" =~ ^[0-9a-f]{40}$ ]] || die "REL_HEAD and PREV_HEAD must be 40-hex"
[[ "$SIGNER_SHA256" =~ ^[0-9a-f]{64}$ ]] || die "SIGNER_SHA256 must be 64-hex"
[[ "$PR" =~ ^[0-9]+$ ]] || die "PR must be a number"
tag_for_version "$EXPECT_VERSION" >/dev/null   # a release version only (X.Y.Z or X.Y.ZrcN)
[[ "$EXPECT_VERSION" == "${LINE#release/}".* ]] || die "version $EXPECT_VERSION is not on $LINE"
repo_info
TMP=$(/usr/bin/mktemp -d); trap 'rm -rf "$TMP"' EXIT

# The signer uses no python (CA-154; tag-release.sh revision 4). It needs gh for its repository and long-suites
# checks (D46), so it gets ONE private PATH entry holding a single symlink to the vetted gh: nothing else in gh's
# directory can shadow git, ssh or awk.
GHDIR="$TMP/signer-gh"; /bin/mkdir -m 700 "$GHDIR"; /bin/ln -s "$GH" "$GHDIR/gh"

# Before anything: the PR is into $LINE, its head is the reviewed one, $LINE is PREV_HEAD.
fresh_clone "$TMP/pre"
[[ "$("${GITX[@]}" rev-parse "origin/$LINE")" == "$PREV_HEAD" ]] || die "$LINE is not PREV_HEAD"
base=$("$GH" pr view "$PR" -R "$GH_REPO" --json baseRefName --jq .baseRefName)
[[ "$base" == "$LINE" ]] || die "#$PR targets $base, not $LINE"
head=$("$GH" pr view "$PR" -R "$GH_REPO" --json headRefOid --jq .headRefOid)
[[ "$head" == "$REL_HEAD" ]] || die "#$PR head is $head, not the reviewed $REL_HEAD"
"${GITX[@]}" fetch -q origin "$REL_HEAD" 2>/dev/null || "${GITX[@]}" fetch -q origin "pull/$PR/head"
v=$(version_at "$REL_HEAD"); [[ "$v" == "$EXPECT_VERSION" ]] || die "REL_HEAD is version $v, not $EXPECT_VERSION"
echo "ok: #$PR -> $LINE at $REL_HEAD, version $v"

printf '\n== CI on #%s\n' "$PR"
wait_for_green_ci "$PR"
yes_or_stop "Merge #$PR (mathAgents $v) into $LINE at ${REL_HEAD:0:10} with a regular merge?"
"$GH" pr merge "$PR" -R "$GH_REPO" --merge --match-head-commit "$REL_HEAD"
MERGE=$("$GH" pr view "$PR" -R "$GH_REPO" --json mergeCommit --jq .mergeCommit.oid)
[[ "$MERGE" =~ ^[0-9a-f]{40}$ ]] || die "cannot read #$PR's merge commit"

# The merge commit, checked in a fresh clone.
fresh_clone "$TMP/post"
[[ "$("${GITX[@]}" rev-list --parents -n 1 "$MERGE")" == "$MERGE $PREV_HEAD $REL_HEAD" ]] || die "merge $MERGE parents are not PREV_HEAD + REL_HEAD"
[[ "$("${GITX[@]}" rev-parse "origin/$LINE")" == "$MERGE" ]] || die "$LINE moved past the merge"
[[ "$(version_at "$MERGE")" == "$EXPECT_VERSION" ]] || die "$MERGE is not version $EXPECT_VERSION"
echo "ok: merge $MERGE = $PREV_HEAD + $REL_HEAD, version $EXPECT_VERSION"

# The signer, from the verified merge commit, pinned by sha256. The release PR may not change the signer: its blob at
# MERGE must equal the one already on $LINE (PREV_HEAD).
sp=scripts/operator/tag-release.sh
[[ "$("${GITX[@]}" rev-parse "$MERGE:$sp" 2>/dev/null)" == "$("${GITX[@]}" rev-parse "$PREV_HEAD:$sp" 2>/dev/null)" ]] \
  || die "the release PR changed $sp (or it is missing): sign only with the signer already on $LINE"
"${GITX[@]}" show "$MERGE:$sp" > "$TMP/tag-release.sh" || die "no $sp at $MERGE"
got=$(/usr/bin/shasum -a 256 "$TMP/tag-release.sh" | /usr/bin/awk '{print $1}')
[[ "$got" == "$SIGNER_SHA256" ]] || die "the signer at $MERGE has sha256 $got, not the approved $SIGNER_SHA256"
yes_or_stop "Sign mathAgents $EXPECT_VERSION at $MERGE with the approved signer?"
PATH="$GHDIR:/usr/bin:/bin:/usr/sbin:/sbin" /bin/bash -p "$TMP/tag-release.sh" "$MERGE" "$KEY" || die "the signer failed"

# Do not trust the signer's own report: fetch tags fresh and verify the result.
TAG=$(tag_for_version "$EXPECT_VERSION")
fresh_clone "$TMP/verify"
"${GITX[@]}" rev-parse -q --verify "refs/tags/$TAG" >/dev/null || die "$TAG is not on origin (the signer stopped or was not run with -p)"
verify_release_tag "$TAG"
[[ "$("${GITX[@]}" rev-parse "$TAG^{commit}")" == "$MERGE" ]] || die "$TAG does not peel to the merge commit $MERGE"
printf '\n%s verified: tag object %s, peeled %s\n' "$TAG" "$("${GITX[@]}" rev-parse "$TAG")" "$MERGE"
printf 'Hand both SHAs to the sessions that pin mathAgents, then run merge-forward.sh.\n'
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
