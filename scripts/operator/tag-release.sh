#!/usr/bin/env bash
# Sign, verify and push a mathagents release tag (SSH-signed, like agentteams' releases). Operator only, plain terminal.
# Revision 2 (2026-10-18): drafted by agentteams-f3 from agentteams' Phase T scripts, reviewed by mathAgents' @security.
# Revision 3 (2026-11-06): the pinned key is called the release key, which signs the 1.0 and 1.1 lines (policy §2).
# The fixed URL is unchanged: after runbook step 5 it names the public, fresh-history repository. New check: before
# anything is cloned, gh must show that jlcatonjr/mathAgents is the public, unarchived repository, so GitHub's rename
# redirect to the private one can't be followed.
# Revision 4 (2026-11-06, CA-154, operator decision "Drop python from the signer"): pyproject.toml's name and version are
# read with /usr/bin/awk instead of python3 + tomllib, so no interpreter (and no /opt/anaconda3) is used for signing.
# Usage: tag-release.sh <40-hex commit> <ssh-signing-key-path>
#
# Everything runs in a fresh clone of the fixed URL in a temporary directory, never in a working checkout, whose
# .git/config agents can write (gpg.ssh.program, core.sshCommand, url.*.insteadOf, hooks). Global and system git
# config are ignored too (include/includeIf, url.*.insteadOf, core.sshCommand): SSH login comes from ssh-agent and
# ~/.ssh/config, not git config. The tagger identity is passed explicitly. ssh-keygen is pinned by path.
# It refuses unless:
#   - <commit> is a 40-hex SHA and is the HEAD of an origin/release/* branch (sign right after the release merge);
#   - pyproject.toml there names "mathagents" ([project] table) and holds a release version that differs from the
#     version at the commit's first parent (so a later head can't be signed under the previous RC's version);
#   - the tag doesn't exist on origin;
#   - a successful Gates run on <commit> (a push run, or a workflow_dispatch run on that exact commit) passed its
#     `long-suites` job (charter D46: the long suites run before every release; a push to release/** forces them,
#     and dispatching Gates on release/* runs them on its head). Checked through `gh api`, fail-closed;
#   - the key's fingerprint is the pinned release key AND ~/.config/agentteams/allowed_signers lists it.
# The tag is verified (neutralised, stderr only, pinned fingerprint) before it is pushed.
# Operator notes (@security rev-2 PASS, Rule 12):
#   - The first rc1: create release/1.0 BEFORE the commit that bumps the version to 1.0.0rc1 (or at that bump commit
#     itself), so the signed commit's version differs from its first parent's; otherwise this script refuses.
#   - GIT_SSH_COMMAND and every other GIT_* variable are dropped. Put SSH options (IdentityAgent, a hardware key's
#     SecurityKeyProvider) in ~/.ssh/config. An -sk key may need SSH_SK_PROVIDER set for /usr/bin/ssh-keygen.
#   - git, ssh and gh are still found through PATH: run from a plain terminal with the default PATH. No python is used.
set -euo pipefail

URL="git@github.com:jlcatonjr/mathAgents.git"
COMMIT="${1:?usage: $0 <40-hex commit> <ssh-signing-key-path>}"
KEY="${2:?usage: $0 <40-hex commit> <ssh-signing-key-path>}"
SIGNERS="$HOME/.config/agentteams/allowed_signers"
RELEASE_FP="SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"  # the release key (policy §2; it signs the 1.0 and 1.1 lines)
SSH_KEYGEN=/usr/bin/ssh-keygen
TAGGER_NAME="${TAGGER_NAME:-jlcatonjr}"; TAGGER_EMAIL="${TAGGER_EMAIL:-}"
# No global/system git config, no GIT_* overrides from the environment (condition 1).
for v in ${!GIT_@}; do unset "$v"; done
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null

die() { echo "error: $*" >&2; exit 1; }
[[ -z "${CLAUDECODE:-}" && -z "${CLAUDE_CODE_ENTRYPOINT:-}" ]] || die "run this from a plain Terminal, not an agent session"
[[ "$COMMIT" =~ ^[0-9a-f]{40}$ ]] || die "<commit> must be the full 40-hex SHA of the release merge commit"
[[ -f "$KEY" ]] || die "signing key not found: $KEY"
[[ -f "$SIGNERS" ]] || die "$SIGNERS is missing: the operator installs it (agentteams SECURITY.md, Release signers)"
[[ -n "$TAGGER_EMAIL" ]] || die "set TAGGER_EMAIL to the tagger e-mail (the identity is passed explicitly, not read from git config)"

PUB="$KEY.pub"; [[ -f "$PUB" ]] || die "public key not found next to the signing key: $PUB"
[[ -x "$SSH_KEYGEN" ]] || die "$SSH_KEYGEN not found"
KEY_FP=$("$SSH_KEYGEN" -lf "$PUB" | awk '{print $2}')
[[ "$KEY_FP" == "$RELEASE_FP" ]] || die "this key ($KEY_FP) is not the release key ($RELEASE_FP)"
grep -v '^[[:space:]]*#' "$SIGNERS" | grep -qF "$(awk '{print $2}' "$PUB")" || die "$SIGNERS doesn't list this key"

# Before anything is cloned: the fixed name must reach the public repository, not the renamed private one.
command -v gh >/dev/null || die "gh is needed to check the repository and the long-suites run (D46)"
REPO_ID=$(gh api repos/jlcatonjr/mathAgents --jq '"\(.full_name) \(.visibility) \(.archived)"') || die "cannot read jlcatonjr/mathAgents through gh api"
[[ "$REPO_ID" == "jlcatonjr/mathAgents public false" ]] || die "jlcatonjr/mathAgents resolves to '$REPO_ID', not the public, unarchived repository (runbook step 5 comes first)"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
GITX=(git -C "$TMP/repo" -c core.hooksPath=/dev/null -c core.fsmonitor=false -c gpg.format=ssh
      -c gpg.ssh.program="$SSH_KEYGEN" -c gpg.ssh.allowedSignersFile="$SIGNERS"
      -c user.name="$TAGGER_NAME" -c user.email="$TAGGER_EMAIL")
git -c core.hooksPath=/dev/null -c core.fsmonitor=false clone -q --no-checkout "$URL" "$TMP/repo"
[[ "$(git -C "$TMP/repo" config --get remote.origin.url)" == "$URL" ]] || die "clone remote is not $URL"
"${GITX[@]}" fetch -q origin --tags
"${GITX[@]}" cat-file -e "$COMMIT^{commit}" 2>/dev/null || die "$COMMIT is not in $URL"

LINE=""
while read -r sha ref; do
  [[ "$sha" == "$COMMIT" ]] && { LINE="${ref#refs/remotes/origin/}"; break; }
done < <("${GITX[@]}" for-each-ref --format='%(objectname) %(refname)' 'refs/remotes/origin/release/*')
[[ -n "$LINE" ]] || die "$COMMIT is not the head of any origin/release/* branch (sign right after the release merge)"

project_field() {  # project_field <rev> <key>: [project].<key> from pyproject.toml at <rev>
  # No python (CA-154): the [project] table's first `<key> = "…"` line, read with /usr/bin/awk. Any other layout
  # prints nothing, and the name and version checks below then refuse.
  "${GITX[@]}" show "$1:pyproject.toml" | /usr/bin/awk -v k="$2" '/^\[/{inproj=($0=="[project]")} inproj && index($0, k " = \"")==1 {s=substr($0, length(k)+5); sub(/".*$/, "", s); print s; exit}'
}
[[ "$(project_field "$COMMIT" name)" == "mathagents" ]] || die "$COMMIT is not mathagents ([project].name)"
VERSION=$(project_field "$COMMIT" version)
PARENT_VERSION=$(project_field "$COMMIT^1" version 2>/dev/null || true)
[[ "$VERSION" != "$PARENT_VERSION" ]] || die "$COMMIT keeps its first parent's version $VERSION: bump the version for this RC (condition 3)"
[[ "$VERSION" =~ ^([0-9]+\.[0-9]+\.[0-9]+)(rc([0-9]+))?$ ]] || die "not a release version: $VERSION"
TAG="v${BASH_REMATCH[1]}${BASH_REMATCH[3]:+-rc.${BASH_REMATCH[3]}}"
"${GITX[@]}" ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1 && die "tag $TAG already exists on origin"

# D46: the long suites (G-KERNEL gate tests, G-AX Lean probes) must have passed on exactly this commit.
command -v gh >/dev/null || die "gh is needed to confirm the long-suites run on $COMMIT (D46)"
LONG_OK=""
# A push run, or a workflow_dispatch run on exactly this commit (D45 condition 4, third text: the public repository's
# push and pull_request events started no workflow on release day 2026-11-10). Either way the Gates workflow ran on
# $COMMIT itself, so D46's requirement is the same: the long suites passed on the commit that is signed.
for run in $(gh api "repos/jlcatonjr/mathAgents/actions/workflows/gates.yml/runs?head_sha=$COMMIT&status=success" \
               --jq '.workflow_runs[] | select(.head_sha == "'"$COMMIT"'" and (.event == "push" or .event == "workflow_dispatch")) | .id') ; do
  if gh api "repos/jlcatonjr/mathAgents/actions/runs/$run/jobs" \
       --jq '.jobs[] | select(.name == "long-suites" and .conclusion == "success") | .id' | grep -q .; then
    LONG_OK="$run"; break
  fi
done
[[ -n "$LONG_OK" ]] || die "no successful Gates run on $COMMIT passed long-suites; push release/* or dispatch Gates on it and wait (D46)"
echo "long-suites:  passed in Gates run $LONG_OK"

PREV=$("${GITX[@]}" describe --tags --abbrev=0 --match 'v[0-9]*' "$COMMIT^" 2>/dev/null || echo none)
echo "release:      $TAG  (version $VERSION, commit $COMMIT, line $LINE)"
echo "previous tag: $PREV (on this commit's history)"
echo "this key:     $KEY_FP"
read -r -p "Create, verify and push the signed tag $TAG? [y/N] " ok
[[ "$ok" == "y" ]] || die "aborted"

"${GITX[@]}" -c user.signingkey="$KEY" tag -s "$TAG" "$COMMIT" -m "mathagents $VERSION"
# Verify from stderr only (stdout carries the tag message, which the tagger controls), whole line, pinned fingerprint.
STATUS=$("${GITX[@]}" tag -v "$TAG" 2>&1 >/dev/null) || die "signature did not verify (the clone and its tag are discarded)"
ok=""
while IFS= read -r line; do [[ "$line" == 'Good "git" signature for '*" key $RELEASE_FP" ]] && ok=1; done <<<"$STATUS"
[[ -n "$ok" ]] || die "verified, but not by $RELEASE_FP (the clone and its tag are discarded)"
[[ "$("${GITX[@]}" rev-parse "$TAG^{commit}")" == "$COMMIT" ]] || die "$TAG does not peel to $COMMIT"

read -r -p "Push $TAG to origin? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "not pushed; the temporary clone and its tag are discarded"; exit 0; }
"${GITX[@]}" push origin "refs/tags/$TAG"
echo "pushed $TAG: tag object $("${GITX[@]}" rev-parse "$TAG"), peeled commit $COMMIT"
echo "Immutable: never move or delete it; fix forward (policy §2). Hand both SHAs to baseAgent (checklist step 9)."
