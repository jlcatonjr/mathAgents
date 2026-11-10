#!/usr/bin/env bash
# Install Lean for mathAgents: elan (user-level, ~/.elan) and the toolchain pinned by
# lean/lean-toolchain, then (unless --no-build) the Mathlib build cache and a build of the library.
# Idempotent; re-run after pulling a toolchain bump. Needs curl and git; no sudo.
#   bash scripts/install_lean.sh [--no-build] [--check]
#     --no-build  install elan and the toolchain only (no Mathlib download, no lake build)
#     --check     report what is installed and exit (0 = toolchain ready, 1 = not); changes nothing
# Verify afterwards with: bash scripts/check_proof_integrity.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLCHAIN="$(tr -d '[:space:]' < "$ROOT/lean/lean-toolchain")"
BUILD=1; CHECK=0
for a in "$@"; do case "$a" in --no-build) BUILD=0 ;; --check) CHECK=1 ;; *) echo "unknown: $a" >&2; exit 2 ;; esac; done

# Pinned installer, verified by SHA-256 before execution (never piped into a shell).
# To bump: change ELAN_TAG, recompute the hash from the tagged file, review the diff.
ELAN_TAG="v4.2.4"
ELAN_SHA256="a620ff1641616222c8d37c54845492004bb84d6877cdbc944dd65c1aa685bf53"

if [[ $EUID -eq 0 ]]; then
  # Under sudo, ~/.elan/toolchains and lean/.lake end up root-owned and every later `lake` run as
  # the user fails with "permission denied".
  echo "[install_lean] do not run as root or with sudo; elan installs per user" >&2; exit 1
fi
for d in "$HOME/.elan" "$ROOT/lean/.lake"; do
  # whole tree: a later `sudo lake build` leaves root-owned files deep inside an otherwise user-owned .lake
  if [[ -e "$d" ]] && [[ -n "$(find "$d" ! -user "$(id -un)" -print -quit 2>/dev/null)" ]]; then
    echo "[install_lean] $d holds files owned by another user (a previous sudo run?); fix with:" >&2
    echo "  sudo chown -R $(id -un) \"$d\"" >&2; exit 1
  fi
done

export PATH="$HOME/.elan/bin:$PATH"

pin_resolves() {  # lean-toolchain selects the toolchain inside lean/; confirm it resolves to the pin
  local v; v="$(cd "$ROOT/lean" && lean --version 2>/dev/null)" || return 1
  echo "[install_lean] $v"
  [[ "$v" == *"${TOOLCHAIN##*:v}"* ]]
}

sha256_of() {  # sha256sum is absent on older macOS; shasum ships with it
  if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

if [[ $CHECK -eq 1 ]]; then
  if ! command -v elan >/dev/null; then echo "[install_lean] elan: not installed"; exit 1; fi
  echo "[install_lean] elan: $(elan --version)"
  toolchains="$(elan toolchain list)"  # captured: grep -q under pipefail can SIGPIPE elan
  if [[ "$toolchains" == *"$TOOLCHAIN"* ]] && pin_resolves; then
    echo "[install_lean] toolchain $TOOLCHAIN: installed"
  else
    echo "[install_lean] toolchain $TOOLCHAIN: missing, or lean in lean/ does not resolve to it (elan show)"; exit 1
  fi
  [[ -d "$ROOT/lean/.lake/packages/mathlib" ]] && echo "[install_lean] Mathlib: fetched" || echo "[install_lean] Mathlib: not fetched (run without --check)"
  exit 0
fi

for tool in curl git; do
  command -v "$tool" >/dev/null || { echo "[install_lean] $tool is required" >&2; exit 1; }
done

if ! command -v elan >/dev/null; then
  echo "[install_lean] installing elan $ELAN_TAG (user-level, ~/.elan) with $TOOLCHAIN"
  installer="$(mktemp)"; trap 'rm -f "$installer"' EXIT
  curl -sSfL "https://raw.githubusercontent.com/leanprover/elan/${ELAN_TAG}/elan-init.sh" -o "$installer"
  got="$(sha256_of "$installer")"
  if [[ "$got" != "$ELAN_SHA256" ]]; then
    echo "[install_lean] elan installer hash mismatch (got $got) — aborting" >&2; exit 1
  fi
  # elan-init adds ~/.elan/bin to your shell profile; open a new shell to pick it up.
  sh "$installer" -y --default-toolchain "$TOOLCHAIN"
fi
elan toolchain install "$TOOLCHAIN"

if ! pin_resolves; then
  echo "[install_lean] lean in lean/ does not report the pinned ${TOOLCHAIN} — check elan overrides (elan show)" >&2; exit 1
fi

if [[ $BUILD -eq 1 ]]; then
  echo "[install_lean] fetching Mathlib build cache (several GB on first run)"
  # The cache is an optimisation: on slow or flaky links it can fail mid-way, and `lake build`
  # then compiles only the Mathlib modules the library imports (minutes on a multi-core machine).
  (cd "$ROOT/lean" && lake exe cache get) || echo "[install_lean] warning: cache fetch failed; building required Mathlib modules from source"
  (cd "$ROOT/lean" && lake build)
fi
echo "[install_lean] done — verify with: bash scripts/check_proof_integrity.sh"
