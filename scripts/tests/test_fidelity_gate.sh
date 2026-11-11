#!/usr/bin/env bash
# G-FID gate tests (spec "Test to build" + adversarial-audit cases). Builds throwaway dossiers, a
# minimal Lean tree, and a kernel report whose source hash matches that tree. Every seeded defect
# must exit 1 with the expected finding; valid records must exit 0.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="$ROOT/scripts/validate_dossier.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT INT TERM
pass=0; failn=0
mkdir -p "$TMP/references/schemas" "$TMP/reports/kernel" "$TMP/lean/MathAgents" "$TMP/lean/MathAgentsWIP"
cp "$ROOT/references/schemas/fidelity-record.schema.json" "$ROOT/references/schemas/counterexample-log.schema.json" "$ROOT/references/schemas/gax-record.schema.json" "$TMP/references/schemas/"
cp "$ROOT/references/schemas/prover-engines.schema.json" "$TMP/references/schemas/"
cp "$ROOT/references/object-logics.json" "$ROOT/references/prover-engines.json" "$TMP/references/"
cp "$ROOT/references/axiom-allowlist.json" "$ROOT/references/preferences.toml" "$TMP/references/"
mkdir -p "$TMP/docs/charter" && cp "$(python3 -c 'import sys, pathlib; sys.path.insert(0, sys.argv[1]); import instance_root; print(instance_root.charter_path(pathlib.Path(sys.argv[2])))' "$ROOT/scripts" "$ROOT")" "$TMP/docs/charter/"
printf '[[lean_lib]]\nname = "MathAgents"\n[[lean_lib]]\nname = "MathAgentsWIP"\n' > "$TMP/lean/lakefile.toml"
echo "theorem thm : True := trivial" > "$TMP/lean/MathAgents/Pilot.lean"
echo "import MathAgents.Pilot" > "$TMP/lean/MathAgents.lean"
echo "" > "$TMP/lean/MathAgentsWIP.lean"

write_report() {  # write_report <verdict> [extra-decl-json] [thm-statement_uses-json]
  local sha; sha="$(python3 -c "import sys; sys.path.insert(0,'$ROOT/scripts'); import proof_integrity as g; from pathlib import Path; p=Path('$TMP/lean'); print(g.source_digest(p, g.libraries(p)[0]))")"
  cat > "$TMP/reports/kernel/latest.json" <<EOF
{"verdict": "$1", "toolchain_pin": "leanprover/lean4:v4.34.1", "lean_version": "Lean (version 4.34.1, fixture)", "source_sha256": "$sha", "declarations": [
 {"decl": "MathAgents.Pilot.thm", "status": "proved", "statement_fingerprint": "111", "statement_uses": ${3:-[]}, "axioms": ["propext"]},
 {"decl": "MathAgentsWIP.Stub.stub", "status": "open", "statement_fingerprint": "222", "statement_uses": [], "axioms": ["sorryAx"]}${2:-}]}
EOF
  python3 - "$TMP" <<'PYSTAMP'
import hashlib, json, sys
from pathlib import Path
r = Path(sys.argv[1]); p = r / "reports" / "kernel" / "latest.json"; d = json.loads(p.read_text())
d["allowlist"] = {"path": "references/axiom-allowlist.json", "sha256": hashlib.sha256((r / "references" / "axiom-allowlist.json").read_bytes()).hexdigest()}
p.write_text(json.dumps(d))
PYSTAMP
}
write_report PASS
dossier() {  # dossier <slug> <fidelity-json-or-empty> [status-text]
  local d="$TMP/reports/dossiers/$1"; rm -rf "$d"; mkdir -p "$d"
  [[ -n "$2" ]] && printf '%s\n' "$2" > "$d/fidelity.json"
  printf '# Dossier\n\n%s\n' "${3:-}" > "$d/README.md"
  printf '# Problem card\n\n- **Source:** test\n- **Informal statement:** test\n- **Domain:** research-math\n- **Object logic:** classical-hol\n- **Engine:** lean-builtin\n' > "$d/problem-card.md"
}
run() { set +e; OUT="$(python3 "$V" --root "$TMP" "$@" 2>&1)"; RC=$?; set -e; }
expect() {  # expect <label> <rc> <substr>
  if [[ $RC -eq $2 ]] && grep -qF -- "$3" <<<"$OUT"; then echo "ok: $1"; pass=$((pass+1))
  else echo "FAIL: $1 (exit $RC)"; sed 's/^/    /' <<<"$OUT"; failn=$((failn+1)); fi
}
APPROVED=',"approver":"operator","date":"2026-10-01"'
WAIVER=',"waiver":{"conversation":"conv-1","date":"2026-10-01"}'
REC() {  # REC <slug> <status> <fingerprint> [extra-fields] [namespace]
  printf '{"schema_version":1,"slug":"%s","lean_namespace":"%s","declarations":[{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"%s","status":"%s"%s}]}' "$1" "${5:-MathAgents.Pilot}" "$3" "$2" "${4:-}"
}

# --- spec cases -----------------------------------------------------------------------------
dossier ok "$(REC ok approved 111 "$APPROVED")" "**Result status:** proved"
run --require-fid ok; expect "matching approved record passes" 0 "PASS"
dossier fp "$(REC fp approved 999 "$APPROVED")"
run --require-fid fp; expect "fingerprint differs from kernel report" 1 "approval lapsed"
dossier noapp "$(REC noapp approved 111 ',"date":"2026-10-01"')"
run --require-fid noapp; expect "approval without approver" 1 "lacks approver or date"
dossier wplain "$(REC wplain waived 111 "$WAIVER")" "**Result status:** proved"
run wplain; expect "fidelity-waived result labelled plain proved" 1 "must be 'proved, fidelity-waived'"
dossier wnoconv "$(REC wnoconv waived 111)"
run --require-fid wnoconv; expect "waiver names no conversation" 1 "names no waiving conversation"

# --- waiver scope (D5/D26: that conversation only) ------------------------------------------
dossier wok "$(REC wok waived 111 "$WAIVER")" "Result status: proved, fidelity-waived"
run --require-fid wok --conversation conv-1; expect "waiver in its own conversation passes" 0 "PASS"
run --require-fid wok --conversation conv-2; expect "waiver reused in another conversation" 1 "applies only to conversation"
run --require-fid wok; expect "waiver without --conversation" 1 "applies only to conversation"
run wok; expect "waived label persists in scan mode" 0 "PASS"

# --- missing / invalid inputs ---------------------------------------------------------------
dossier norec ""
run --require-fid norec; expect "missing fidelity record" 1 "no fidelity record"
dossier bad '{"schema_version":1,"slug":"bad","lean_namespace":"X","declarations":[{"decl":"X","statement_fingerprint":"abc","status":"approved"}]}'
run --require-fid bad; expect "schema-invalid record" 1 "fidelity.json invalid"
dossier nons "$(printf '{"schema_version":1,"slug":"nons","declarations":[{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"111","status":"approved","approver":"o","date":"2026-10-01"}]}')"
run --require-fid nons; expect "record without lean_namespace" 1 "fidelity.json invalid"
dossier dup "$(printf '{"schema_version":1,"slug":"dup","lean_namespace":"MathAgents.Pilot","declarations":[{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"111","status":"approved","approver":"o","date":"2026-10-01"},{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"111","status":"approved","approver":"o","date":"2026-10-01"}]}')"
run --require-fid dup; expect "duplicate declaration entries" 1 "duplicate entry"

# --- kernel report freshness ----------------------------------------------------------------
dossier fresh "$(REC fresh approved 111 "$APPROVED")"
mv "$TMP/reports/kernel/latest.json" "$TMP/latest.bak"
run --require-fid fresh; expect "missing kernel report" 1 "no kernel report"
mv "$TMP/latest.bak" "$TMP/reports/kernel/latest.json"
write_report FAIL
run --require-fid fresh; expect "kernel report verdict FAIL" 1 "not PASS"
write_report PASS
echo "-- edited" >> "$TMP/lean/MathAgents/Pilot.lean"
run --require-fid fresh; expect "stale report after a source edit" 1 "stale kernel report"
write_report PASS

# --- coverage (no partial approval) ---------------------------------------------------------
write_report PASS ', {"decl": "MathAgents.Pilot.thm2", "status": "proved", "statement_fingerprint": "333", "axioms": []}'
dossier partial "$(REC partial approved 111 "$APPROVED")"
run --require-fid partial; expect "second declaration in namespace unapproved" 1 "has no fidelity entry"
write_report PASS

# --- label detection ------------------------------------------------------------------------
dossier lh "" "## Result status: proved"
run lh; expect "label in a heading without record" 1 "without a fidelity record"
dossier lb "" "- Result status: proved"
run lb; expect "label in a bullet without record" 1 "without a fidelity record"
dossier lt "" "| Result status | proved |"
run lt; expect "label in a table row without record" 1 "without a fidelity record"
dossier lr "" "Result: proved"
run lr; expect "'Result:' variant without record" 1 "without a fidelity record"
dossier ln ""
mkdir -p "$TMP/reports/dossiers/ln/notes"; echo "Status: proved" > "$TMP/reports/dossiers/ln/notes/summary.txt"
run ln; expect "label in a nested .txt file" 1 "without a fidelity record"
dossier lnc "$(REC lnc waived 111 "$WAIVER")" "Result status: proved,fidelity-waived"
run lnc; expect "non-canonical 'proved,fidelity-waived'" 1 "non-canonical result label"
dossier lprose "" "This brief calls nothing proved, and its **Status:** is advisory."
run lprose; expect "prose mentioning 'proved' is not a label" 0 "PASS"
dossier lopen "$(printf '{"schema_version":1,"slug":"lopen","lean_namespace":"MathAgentsWIP.Stub","declarations":[{"decl":"MathAgentsWIP.Stub.stub","statement_fingerprint":"222","status":"approved","approver":"o","date":"2026-10-01"}]}')" "Result status: proved"
run lopen; expect "proved label on a kernel-open declaration" 1 "cannot be labelled"

# --- audit round 2 -------------------------------------------------------------------------
dossier dep "$(REC dep approved 111 "$APPROVED")"
echo '{"version": 1}' > "$TMP/lean/lake-manifest.json"
run --require-fid dep; expect "stale report after a dependency (manifest) change" 1 "stale kernel report"
write_report PASS
dossier nsdecl "$(REC nsdecl approved 111 "$APPROVED" "MathAgents.Pilot.thm")"
run --require-fid nsdecl; expect "namespace narrowed to a declaration" 1 "is itself a declaration"
dossier nsout "$(REC nsout approved 111 "$APPROVED" "MathAgents.Other")"
run --require-fid nsout; expect "entry outside its namespace" 1 "outside lean_namespace"
dossier lproven "" "Status: proven"
run lproven; expect "'proven' label is blocked" 1 "non-canonical result label"
dossier lfully "" "Result status = fully proved"
run lfully; expect "'fully proved' with '=' separator is blocked" 1 "non-canonical result label"
dossier lclause "" "**Status:** advisory input only. It calls nothing proved."
run lclause; expect "label value stops at the clause end" 0 "PASS"

# --- helper and witness sub-namespaces are exempt from coverage ---------------------------------
write_report PASS ', {"decl": "MathAgents.Pilot.Aux.helper", "status": "open", "statement_fingerprint": "41", "axioms": ["sorryAx"]}, {"decl": "MathAgents.Pilot.CX.cx_1", "status": "proved", "statement_fingerprint": "42", "axioms": []}'
dossier aux "$(REC aux approved 111 "$APPROVED")"
run --require-fid aux; expect "Aux helper and CX witness need no fidelity entry" 0 "PASS"
write_report PASS ', {"decl": "MathAgents.Pilot.Auxiliary", "status": "proved", "statement_fingerprint": "43", "axioms": []}'
dossier auxname "$(REC auxname approved 111 "$APPROVED")"
run --require-fid auxname; expect "a name merely starting with Aux is still covered" 1 "has no fidelity entry"
write_report PASS

# --- approved statements must not reach Aux/CX helpers (stage-agent review round 2) -------------
write_report PASS "" '["MathAgents.Pilot.Aux.bound", "MathAgents.Pilot.P"]'
dossier usesaux "$(REC usesaux approved 111 "$APPROVED")"
run --require-fid usesaux; expect "approved statement reaching an Aux definition" 1 "depends on helper declaration(s) MathAgents.Pilot.Aux.bound"
write_report PASS "" '["MathAgents.Pilot.P", "MathAgents.Pilot.Auxiliary"]'
run --require-fid usesaux; expect "top-level definitions are fine" 0 "PASS"
python3 - "$TMP/reports/kernel/latest.json" <<'PY2'
import json, sys
p = sys.argv[1]; r = json.load(open(p)); r["declarations"][0].pop("statement_uses"); json.dump(r, open(p, "w"))
PY2
run --require-fid usesaux; expect "report without statement_uses fails closed" 1 "lacks statement_uses"
write_report PASS

echo "passed=$pass failed=$failn"
[[ $failn -eq 0 ]]
