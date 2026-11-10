# Shared helpers for mathAgents' operator release scripts (release-merge-and-sign.sh, merge-forward.sh).
# Sourced, never run. Every caller runs in privileged mode (/bin/bash -p; see its guard).
# Derived 2026-11-06 from agentteams-f3's cleared derived-phase-t/_derived_common.sh (sha256 39cef2b1…, agentteams
# tmp/by-week/2026-W42/f3-drafts/phase-t-hashes.sha256), which mathAgents ran in Phase T for v1.0.0 (2026-10-19).
# Changes from it: mathAgents only (repo_info takes no argument, and checks that the fixed name reaches the public,
# unarchived repository); the re-exec marker is _MA_RELEASE_CLEAN; the comments say "release line" rather than
# release/1.0. The other checks are unchanged.

# --- environment: refuse agent sessions, then re-exec once with an allowlisted environment -----------------------
# Usage, at the top of a script, before anything else:  . "<dir>/lib_release.sh"; clean_reexec VAR1 VAR2 -- "$@"
clean_reexec() {
  # Speed bump only: an agent could unset these. The real control is that only the operator runs these scripts.
  [[ -z "${CLAUDECODE:-}" && -z "${CLAUDE_CODE_ENTRYPOINT:-}" ]] || { echo "error: run this from a plain terminal, not an agent session" >&2; exit 1; }
  local keep=() names=() v n ok=1
  while [[ $# -gt 0 && "$1" != "--" ]]; do names+=("$1"); [[ -n "${!1:-}" ]] && keep+=("$1=${!1}"); shift; done
  [[ "${1:-}" == "--" ]] && shift
  # The marker is never trusted by itself: the environment must hold only the allowlist.
  # Nothing external runs under the caller's PATH: a wrong PATH fails the check at once.
  [[ "${PATH:-}" == /usr/bin:/bin:/usr/sbin:/sbin ]] || ok=""
  if [[ -n "$ok" ]]; then
    [[ -z "$(declare -F | /usr/bin/grep -vxE 'declare -f (clean_reexec|neutralise|die|yes_or_stop|repo_info|fresh_clone|verify_release_tag|version_at|tag_for_version|wait_for_green_ci)')" ]] || ok=""
    while IFS= read -r n; do
      case " HOME TERM PATH SSH_AUTH_SOCK _MA_RELEASE_CLEAN PWD SHLVL OLDPWD _ ${names[*]} " in *" $n "*) ;; *) ok="" ;; esac
    done < <(compgen -e)
  fi
  [[ -n "$ok" ]] && return 0
  [[ "${_MA_RELEASE_CLEAN:-}" != 1 ]] || { echo "error: environment not clean after the env -i re-exec; stopping" >&2; exit 1; }
  exec /usr/bin/env -i _MA_RELEASE_CLEAN=1 HOME="$HOME" TERM="${TERM:-dumb}" PATH=/usr/bin:/bin:/usr/sbin:/sbin \
    ${SSH_AUTH_SOCK:+SSH_AUTH_SOCK="$SSH_AUTH_SOCK"} ${keep[@]+"${keep[@]}"} /bin/bash -p "$SCRIPT" "$@"
}
neutralise() {
  for v in ${!GIT_@} ${!GH_@}; do unset "$v"; done
  unset GITHUB_TOKEN DEVELOPER_DIR TOOLCHAINS SDKROOT
  export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PATH=/usr/bin:/bin:/usr/sbin:/sbin
  GIT=/usr/bin/git; SSH_KEYGEN=/usr/bin/ssh-keygen; GH=""
  for c in /opt/homebrew/bin/gh /usr/local/bin/gh; do [[ -x "$c" ]] && { GH="$c"; break; }; done
  [[ -n "$GH" ]] || die "gh not found at /opt/homebrew/bin/gh or /usr/local/bin/gh"
  SIGNERS="$HOME/.config/agentteams/allowed_signers"
  [[ -f "$SIGNERS" ]] || die "no $SIGNERS"
}
die() { echo "error: $*" >&2; exit 1; }
yes_or_stop() { local ok; read -r -p "$1 [y/N] " ok; [[ "$ok" == "y" ]] || { echo "stopped: $1 not confirmed"; exit 0; }; }

# --- the repository ----------------------------------------------------------------------------------------------
# repo_info: sets URL GH_REPO PKG VERSION_KIND, after neutralise (it needs $GH). The URL is fixed and is the same one tag-release.sh clones. After
# runbook step 5 it names the public, fresh-history repository (the private one is renamed mathAgents-private).
repo_info() {
  URL="git@github.com:jlcatonjr/mathAgents.git"; GH_REPO="github.com/jlcatonjr/mathAgents"; PKG=mathagents; VERSION_KIND=pyproject
  # The fixed name must reach the public, unarchived repository, not the renamed private one through GitHub's rename
  # redirect (which git and gh both follow): run nothing until runbook step 5 is complete.
  local id; id=$("$GH" api repos/jlcatonjr/mathAgents --jq '"\(.full_name) \(.visibility) \(.archived)"') \
    || die "cannot read jlcatonjr/mathAgents through gh api"
  [[ "$id" == "jlcatonjr/mathAgents public false" ]] \
    || die "jlcatonjr/mathAgents resolves to '$id', not the public, unarchived repository (runbook step 5 comes first)"
}
# fresh_clone <dir>: clone $URL with every config source neutralised; sets GITX for that clone.
fresh_clone() {
  GITX=("$GIT" -C "$1" -c core.hooksPath=/dev/null -c core.fsmonitor=false -c gpg.ssh.program="$SSH_KEYGEN"
        -c gpg.ssh.allowedSignersFile="$SIGNERS" -c credential.helper=
        -c "credential.https://github.com.helper=!'$GH' auth git-credential")
  "$GIT" -c core.hooksPath=/dev/null -c core.fsmonitor=false -c credential.helper= \
    -c "credential.https://github.com.helper=!'$GH' auth git-credential" clone -q --no-checkout "$URL" "$1" \
    || die "cannot clone $URL"
  [[ "$("$GIT" -C "$1" config --get remote.origin.url)" == "$URL" ]] || die "clone remote is not $URL"
  "${GITX[@]}" fetch -q origin --tags
}
# The release key, pinned (docs/release-policy.md §2; the same key signs the 1.0 and 1.1 lines).
RELEASE_FPS=("SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM")
verify_release_tag() {  # stderr only, whole line, pinned fingerprint, annotated, and the object's own name is <tag>
  local tag="$1" status line fp ok=""
  [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$ ]] || die "not a release tag name: $tag"
  status=$("${GITX[@]}" tag -v "$tag" 2>&1 >/dev/null) || die "$tag does not verify against $SIGNERS"
  while IFS= read -r line; do for fp in "${RELEASE_FPS[@]}"; do [[ "$line" == 'Good "git" signature for '*" key $fp" ]] && ok=1; done; done <<<"$status"
  [[ -n "$ok" ]] || die "$tag is not signed by a release key"
  [[ "$("${GITX[@]}" cat-file -t "$tag")" == tag ]] || die "$tag is not annotated"
  # The signed object must name itself <tag>: an rc's signed object re-published as the final tag would otherwise pass.
  [[ "$("${GITX[@]}" cat-file -p "$tag" | /usr/bin/sed -n 's/^tag //p' | /usr/bin/head -1)" == "$tag" ]] \
    || die "the tag object behind $tag names a different tag (a re-published object)"
}
tag_for_version() {  # 1.1.0 -> v1.1.0 ; 1.1.0rc1 -> v1.1.0-rc.1
  [[ "$1" =~ ^([0-9]+\.[0-9]+\.[0-9]+)(rc([0-9]+))?$ ]] || die "unexpected version $1"
  echo "v${BASH_REMATCH[1]}${BASH_REMATCH[3]:+-rc.${BASH_REMATCH[3]}}"
}
# wait_for_green_ci <pr> [long]: wait (up to 10 min) until GitHub has registered at least one check, then watch, then
# re-check every check. `gh pr checks` reports "no checks reported" (non-zero) in the seconds after a PR opens or
# its head moves, which is not a CI result (the registration race seen in the operator's run on 2026-10-19).
# Fallback (D45 condition 4, third text): when no check registers because the repository's pull_request events start
# no workflow, a Gates run dispatched on the PR's exact head commit stands in. It must be complete and successful with
# every job green (long-suites green, not skipped, when the second argument is "long"), and the PR must contain its
# base's head (up to date). The run is dispatched by the session; this function only reads it.
wait_for_green_ci() {
  local pr="$1" want="${2:-}" n=0 i head base run jobs behind
  for i in $(/usr/bin/seq 1 40); do
    n=$("$GH" pr view "$pr" -R "$GH_REPO" --json statusCheckRollup --jq '.statusCheckRollup | length' 2>/dev/null || echo 0)
    [[ "$n" =~ ^[0-9]+$ && "$n" -gt 0 ]] && break
    /bin/sleep 15
  done
  if [[ "$n" =~ ^[0-9]+$ && "$n" -gt 0 ]]; then
    "$GH" pr checks "$pr" -R "$GH_REPO" --watch --interval 30 || die "CI on #$pr is not green"
    /bin/sleep 20   # --watch can return once early checks finish; every check on the head must be complete and green
    "$GH" pr checks "$pr" -R "$GH_REPO" >/dev/null || die "CI on #$pr is not green on re-check (pending or failed checks)"
    return 0
  fi
  head=$("$GH" pr view "$pr" -R "$GH_REPO" --json headRefOid --jq .headRefOid)
  base=$("$GH" pr view "$pr" -R "$GH_REPO" --json baseRefName --jq .baseRefName)
  [[ "$head" =~ ^[0-9a-f]{40}$ ]] || die "cannot read #$pr's head commit"
  [[ "$base" =~ ^(main|dev|release/[0-9]+\.[0-9]+)$ ]] || die "#$pr targets $base, not main, dev or release/X.Y"
  # (gh api takes OWNER/REPO, not the host-qualified GH_REPO that -R takes)
  behind=$("$GH" api "repos/jlcatonjr/mathAgents/compare/$base...$head" --jq .behind_by) || die "cannot compare #$pr with $base"
  [[ "$behind" == 0 ]] || die "#$pr is $behind commit(s) behind $base: update it, then dispatch Gates on its head"
  echo "no PR checks registered on #$pr; looking for a Gates run dispatched on its head ${head:0:10}"
  run=""
  for i in $(/usr/bin/seq 1 480); do   # up to 4 hours: the long suites take about two
    run=$("$GH" api "repos/jlcatonjr/mathAgents/actions/workflows/gates.yml/runs?head_sha=$head" \
            --jq '[.workflow_runs[] | select(.head_sha == "'"$head"'")] | sort_by(.created_at) | last | "\(.id) \(.status) \(.conclusion)"') \
      || die "cannot list Gates runs for #$pr's head"
    [[ "$i" == 20 && "$run" == "null null null" ]] && die "no Gates run on #$pr's head $head after 10 minutes: dispatch one (gh workflow run gates.yml --ref <branch>)"
    case "$run" in
      *" completed "*|*" completed") break ;;
    esac
    /bin/sleep 30
  done
  [[ "$run" =~ ^[0-9]+\ completed\ success$ ]] || die "no successful Gates run on #$pr's head $head (latest: ${run:-none})"
  run="${run%% *}"
  jobs=$("$GH" api "repos/jlcatonjr/mathAgents/actions/runs/$run/jobs" --jq '[.jobs[] | "\(.name)=\(.conclusion)"] | join(" ")') \
    || die "cannot read the jobs of run $run"
  echo "Gates run $run on ${head:0:10}: $jobs"
  case " $jobs " in *" gates=success "*) ;; *) die "gates did not pass in run $run" ;; esac
  if [[ "$want" == long ]]; then
    case " $jobs " in *" long-suites=success "*) ;; *) die "long-suites did not pass (green, not skipped) in run $run" ;; esac
  fi
  for i in $jobs; do
    case "${i#*=}" in success|skipped) ;; *) die "job ${i%%=*} is ${i#*=} in run $run" ;; esac
  done
  # The head and the base must not have moved while the run was awaited.
  [[ "$("$GH" pr view "$pr" -R "$GH_REPO" --json headRefOid --jq .headRefOid)" == "$head" ]] || die "#$pr's head moved past $head"
  behind=$("$GH" api "repos/jlcatonjr/mathAgents/compare/$base...$head" --jq .behind_by) || die "cannot compare #$pr with $base"
  [[ "$behind" == 0 ]] || die "$base moved while waiting: #$pr is $behind commit(s) behind"
}
# version_at <rev>: the package version at <rev>
version_at() {
  case "$VERSION_KIND" in
    # No python: macOS /usr/bin/python3 is 3.9 (no tomllib). The [project] table's first `version = "…"` line, only.
    pyproject) "${GITX[@]}" show "$1:pyproject.toml" | awk '/^\[/{inproj=($0=="[project]")} inproj && /^version = "/{sub(/^version = "/,""); sub(/"$/,""); print; exit}' ;;
    *) die "no static version for $VERSION_KIND" ;;
  esac
}
