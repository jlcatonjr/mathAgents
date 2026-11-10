#!/bin/bash
# Operator-only signing helper, sourced by every new signing script (operator decision 2026-10-28: the root-owned
# signer only, no fallback). Long-lived; doc owner: docs/release-policy.md §7.
#   source scripts/operator/lib_signer.sh
#   signer_check                       # refuses unless the signer and its base Python are intact
#   preflight SPEC TEAMDIR REPO        # scripts/operator/check_decision_spec.py, run by the signer's Python
#   signer_run --sign-decision SPEC --output DIR   # agentteams, run as `python -I` (no PYTHON* from the caller)
# It reads no key and writes nothing. /opt/anaconda3 is not used for signing.
SIGNER_ROOT=/opt/agentteams-signer-v1.0.0   # fixed; never read from the environment
SIGNER_COMMIT=cc5b8c9ec4efdcb479939e0c1246a0ac11913259
SIGNER_TAG_FPR="SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"
SIGNER_SET=248ab89c3bd99ca609aa34823b574c5920d1e2accf2e3fd4efe9898d9a153a51
SIGNER_OWNER=root
SIGNER_FRAMEWORK=/Library/Frameworks/Python.framework/Versions/3.13   # the root-owned base interpreter
SIGNER_PYVERSION=3.13.16
SIGNER_PY=               # set only by signer_check; an inherited value is cleared here
SIGNER_CHECK_PARENTS=1   # tests reassign these after sourcing; nothing is read from the environment

_signer_die() { echo "lib_signer: STOP: $*" >&2; return 1; }

_owned_chain() {  # _owned_chain DIR: DIR and every parent owned by SIGNER_OWNER (or root), not writable by others
  local p="$1" o
  while [[ $SIGNER_CHECK_PARENTS == 1 ]]; do
    o="$(/usr/bin/stat -f '%Su' "$p")"
    [[ "$o" == "$SIGNER_OWNER" || "$o" == root ]] || { _signer_die "$p is not owned by $SIGNER_OWNER"; return 1; }
    [[ -z "$(/usr/bin/find "$p" -maxdepth 0 \( -perm -g+w -o -perm -o+w \) -print)" ]] || { _signer_die "$p is group- or world-writable"; return 1; }
    [[ "$p" == / ]] && break; p="$(/usr/bin/dirname "$p")"
  done
}

_owned_tree() {  # _owned_tree DIR: nothing under DIR (symlinks aside) is foreign-owned or writable by others
  [[ -z "$(/usr/bin/find "$1" \( \( ! -user "$SIGNER_OWNER" ! -user root \) -o -perm -g+w -o -perm -o+w \) ! -type l -print -quit)" ]] \
    || { _signer_die "something under $1 is not $SIGNER_OWNER-owned or is writable by others"; return 1; }
}

signer_check() {
  local p="$SIGNER_ROOT" py="$SIGNER_ROOT/bin/python" prov="$SIGNER_ROOT/PROVENANCE.json"
  [[ -d "$p" && -x "$py" && -f "$prov" ]] || { _signer_die "no signer at $SIGNER_ROOT (the operator provisions it once; docs/release-policy.md §7)"; return 1; }
  _owned_chain "$SIGNER_ROOT" || return 1
  _owned_tree "$SIGNER_ROOT" || return 1
  _owned_chain "$SIGNER_FRAMEWORK" || return 1
  _owned_tree "$SIGNER_FRAMEWORK" || return 1
  [[ -z "$(/usr/bin/find "$SIGNER_ROOT" -name '*.pth' -print -quit)" ]] || { _signer_die ".pth files under $SIGNER_ROOT"; return 1; }
  local out
  out="$(cd / && "$py" -I - "$prov" "$SIGNER_COMMIT" "$SIGNER_TAG_FPR" "$SIGNER_SET" "$SIGNER_FRAMEWORK" "$SIGNER_PYVERSION" <<'PY'
import hashlib, importlib.metadata as m, json, os, platform, sys
prov, commit, fpr, want, framework, pyversion = sys.argv[1:7]
p = json.load(open(prov))
problems = [k for k, v in (("commit", commit), ("tag_signer", fpr), ("package_set_sha256", want)) if p.get(k) != v]
if os.path.realpath(sys.base_prefix) != os.path.realpath(framework):
    problems.append(f"base interpreter {sys.base_prefix}")
if platform.python_version() != pyversion:
    problems.append(f"Python {platform.python_version()}")
s = "\n".join(sorted({d.metadata["Name"].lower().replace("_", "-") + "==" + d.version for d in m.distributions()}))
if hashlib.sha256((s + "\n").encode()).hexdigest() != want:
    problems.append("installed package set")
print("ok" if not problems else "mismatch: " + ", ".join(problems))
PY
)" || { _signer_die "could not run $py"; return 1; }
  [[ "$out" == ok ]] || { _signer_die "PROVENANCE.json or the installed packages differ ($out)"; return 1; }
  SIGNER_PY="$py"
}

signer_run() {  # agentteams under `python -I`: the caller's PYTHON* variables don't apply and cwd is not on sys.path
  [[ -n "${SIGNER_PY:-}" ]] || { _signer_die "call signer_check before signer_run"; return 1; }
  "$SIGNER_PY" -I "$SIGNER_ROOT/bin/agentteams" "$@"
}

preflight() {  # preflight SPEC TEAMDIR REPO
  [[ $# -eq 3 ]] || { _signer_die "usage: preflight SPEC TEAMDIR REPO"; return 1; }
  [[ -n "${SIGNER_PY:-}" ]] || { _signer_die "call signer_check before preflight"; return 1; }
  "$SIGNER_PY" -I "$3/scripts/operator/check_decision_spec.py" "$1" --team-dir "$2" --repo "$3"
}
