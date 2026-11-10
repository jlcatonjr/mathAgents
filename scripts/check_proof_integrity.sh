#!/usr/bin/env bash
# G-KERNEL — thin wrapper; the gate lives in scripts/proof_integrity.py (see its docstring).
exec python3 "$(dirname "${BASH_SOURCE[0]}")/proof_integrity.py" "$@"
