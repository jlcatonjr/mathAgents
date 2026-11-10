#!/usr/bin/env bash
# Bootstrap a machine for mathAgents: elan + pinned Lean, Mathlib cache, conda env, probe.
# Idempotent; safe to re-run after pulling a toolchain bump.
#   bash scripts/bootstrap_env.sh [--no-conda] [--engines]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WITH_CONDA=1; WITH_ENGINES=0
for a in "$@"; do case "$a" in --no-conda) WITH_CONDA=0 ;; --engines) WITH_ENGINES=1 ;; *) echo "unknown: $a" >&2; exit 2 ;; esac; done
if [[ $WITH_ENGINES -eq 1 && $WITH_CONDA -eq 0 ]]; then echo "--engines installs into the conda env; it cannot be combined with --no-conda" >&2; exit 2; fi

# Lean (elan, the pinned toolchain, Mathlib cache, library build) lives in one script.
bash "$ROOT/scripts/install_lean.sh"
export PATH="$HOME/.elan/bin:$PATH"

if [[ $WITH_CONDA -eq 1 ]]; then
  if command -v conda >/dev/null; then
    if conda env list | grep -qE '^mathagents\s'; then conda env update -f "$ROOT/environment.yml" --prune
    else conda env create -f "$ROOT/environment.yml"; fi
    [[ $WITH_ENGINES -eq 1 ]] && conda run -n mathagents pip install -r "$ROOT/requirements-engines.txt"
  else
    echo "[bootstrap] conda not found — install Miniforge, or install environment.yml's packages manually" >&2
  fi
fi

# TeX packages for the PDF blueprint are system-level; report, don't install.
kpsewhich biblatex-chicago.sty >/dev/null 2>&1 || echo "[bootstrap] note: biblatex-chicago not found (needed for the PDF blueprint; e.g. tlmgr install biblatex-chicago)"

# Probe inside the shared env when it exists, so Python-module engines are detected correctly.
if command -v conda >/dev/null && conda env list | grep -qE '^mathagents\s'; then
  conda run -n mathagents python "$ROOT/scripts/probe_machine.py"
else
  python3 "$ROOT/scripts/probe_machine.py"
fi
echo "[bootstrap] done — verify with: bash scripts/check_proof_integrity.sh"
