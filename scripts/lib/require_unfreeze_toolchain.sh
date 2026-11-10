#!/usr/bin/env bash
# CX-3: refuse to render an unfrozen surface (codex or goose) below agentteams v1.1.0 or without the operator's
# signed unfreeze-<surface> row in .github/agents/references/security-decisions.log.csv. A fast, readable early
# stop; researchteam itself still verifies the row through agentteams' gate (signature, relaxing class).
#   bash scripts/lib/require_unfreeze_toolchain.sh codex|goose
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
s="${1:?surface}"
python3 - "$s" <<'PY'
import csv, re, sys
s = sys.argv[1]
tag = next((l.split("=", 1)[1].strip() for l in open("toolchain.lock") if l.startswith("agentteams.tag=")), "")
m = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)(-rc\.\d+)?", tag)
if not m or m.group(4) or tuple(map(int, m.group(1, 2, 3))) < (1, 1, 0):
    sys.exit(f"[refresh] unfreeze-{s}: toolchain.lock pins agentteams {tag or '(no tag)'}; an unfrozen {s} needs a "
             "verified agentteams v1.1.0 or later release tag (CX-3, docs/release-policy.md section 5)")
rows = [r for r in csv.DictReader(open(".github/agents/references/security-decisions.log.csv", newline=""))
        if r.get("action_reviewed") == f"unfreeze-{s}"]
if not rows or (rows[-1].get("sig_scheme") or "").lower() != "ed25519" or not (rows[-1].get("signature") or "").strip():
    sys.exit(f"[refresh] unfreeze-{s}: no operator Ed25519-signed unfreeze-{s} row "
             "(docs/release/unfreeze-" + s + ".decision-spec.json)")
PY
