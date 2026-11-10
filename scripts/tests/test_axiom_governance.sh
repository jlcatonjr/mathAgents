#!/usr/bin/env bash
# G-AX governance tests (spec "Tests to build" under G-AX; DD-36, DD-37). Covers both halves of the
# gate: the axiom allowlist (G-KERNEL + registry validator, on real Lean probes) and changes to
# approved statements (the dossier validator's G-AX module, against a git base).
#   bash scripts/tests/test_axiom_governance.sh [--part validator|lean]
# --part validator runs the registry and dossier-validator checks (seconds; the `gates` job, every run); --part lean
# runs the G-KERNEL checks on real Lean probes (the `long-suites` job, charter D46). No flag runs both.
set -euo pipefail
PART=all
case "${1:-}" in
  "") ;;
  --part) PART="${2:?--part needs validator or lean}"; [[ $PART == validator || $PART == lean ]] || { echo "unknown part: $PART" >&2; exit 2; } ;;
  *) echo "usage: $0 [--part validator|lean]" >&2; exit 2 ;;
esac
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT INT TERM
pass=0; failn=0
ok() { echo "ok: $1"; pass=$((pass+1)); }
bad() { echo "FAIL: $1"; failn=$((failn+1)); }

# Shared by both parts (the Lean half uses allowlist and REC too).
allowlist() {  # allowlist FILE APPROVED-JSON-ARRAY APPROVALS-JSON-ARRAY
  printf '{"note": "test", "base_axioms": ["propext", "Classical.choice", "Quot.sound"], "approved_axioms": %s, "approvals": %s}\n' "$2" "$3" > "$1"
}
REC='{"axiom": "%s", "approver": "operator", "date": "2026-10-01", "reason": "test", "dossier": "p0", "conversation": null}'

if [[ $PART != lean ]]; then
# --- allowlist: registry validator ---------------------------------------------------------------
mkdir -p "$TMP/reg/references/schemas" "$TMP/reg/scripts"
cp "$ROOT"/references/schemas/*.json "$TMP/reg/references/schemas/"
cp "$ROOT"/references/object-logics.json "$ROOT"/references/prover-engines.json "$TMP/reg/references/"
cp "$ROOT/scripts/validate_registries.py" "$ROOT/scripts/axiom_allowlist.py" "$ROOT/scripts/instance_root.py" "$TMP/reg/scripts/"
mkdir -p "$TMP/reg/reports/dossiers/p0"   # approval records must name a real dossier
reg() { set +e; python3 "$TMP/reg/scripts/validate_registries.py" >"$TMP/out.log" 2>&1; rc=$?; set -e; }

allowlist "$TMP/reg/references/axiom-allowlist.json" '["Probe.ax"]' '[{"axiom": "Probe.ax", "approver": "operator"}]'
reg; if [[ $rc -eq 1 ]] && grep -q "Probe.ax: approval record missing date, reason, dossier" "$TMP/out.log"; then
  ok "registry rejects an incomplete approval record"; else bad "incomplete approval record (exit $rc)"; sed 's/^/    /' "$TMP/out.log"; fi
allowlist "$TMP/reg/references/axiom-allowlist.json" '["Probe.ax"]' '[]'
reg; if [[ $rc -eq 1 ]] && grep -q "Probe.ax is approved without an approval record" "$TMP/out.log"; then
  ok "registry rejects an approved axiom with no record"; else bad "approved axiom without record, registry (exit $rc)"; fi
allowlist "$TMP/reg/references/axiom-allowlist.json" '["Probe.ax"]' "[$(printf "$REC" Probe.ax)]"
reg; if [[ $rc -eq 0 ]]; then ok "registry accepts a complete record"; else bad "complete record rejected (exit $rc)"; sed 's/^/    /' "$TMP/out.log"; fi
printf '{"note": "t", "base_axioms": ["propext", "Classical.choice", "Quot.sound", "sorryAx"], "approved_axioms": [], "approvals": []}\n' > "$TMP/reg/references/axiom-allowlist.json"
reg; if [[ $rc -eq 1 ]] && grep -q "base_axioms widens the envelope with sorryAx" "$TMP/out.log"; then
  ok "a widened base envelope is refused (DD-38)"; else bad "widened base envelope (exit $rc)"; sed 's/^/    /' "$TMP/out.log"; fi

allowlist "$TMP/reg/references/axiom-allowlist.json" '["Probe.ax"]' "[$(printf "$REC" Probe.ax | sed 's/"p0"/"p9"/')]"
reg; if [[ $rc -eq 1 ]] && grep -q "names dossier 'p9', which is not" "$TMP/out.log"; then
  ok "registry rejects an approval naming a dossier that does not exist"; else bad "unknown dossier in approval (exit $rc)"; sed 's/^/    /' "$TMP/out.log"; fi

fi

if [[ $PART != validator ]]; then
# --- allowlist: G-KERNEL on real Lean probes -----------------------------------------------------
mk_project() {  # mk_project LINE... : the real library plus a probe module in MathAgents
  rm -rf "$TMP/lean"; mkdir -p "$TMP/lean/.lake"
  cp -r "$ROOT/lean/MathAgents" "$ROOT/lean/MathAgents.lean" "$ROOT/lean/MathAgentsWIP" "$ROOT/lean/MathAgentsWIP.lean" \
        "$ROOT/lean/lakefile.toml" "$ROOT/lean/lean-toolchain" "$ROOT/lean/lake-manifest.json" "$TMP/lean/"
  ln -s "$ROOT/lean/.lake/packages" "$TMP/lean/.lake/packages"
  printf '%s\n' "$@" > "$TMP/lean/MathAgents/AxProbe.lean"
  echo "import MathAgents.AxProbe" >> "$TMP/lean/MathAgents.lean"
}
gate() {  # gate ALLOWLIST-FILE
  set +e; python3 "$ROOT/scripts/proof_integrity.py" --lean-dir "$TMP/lean" --no-report --allowlist "$1" >"$TMP/out.log" 2>&1; rc=$?; set -e
}
A="$TMP/allow.json"
NS_PROBE=("namespace Probe" "axiom ax : 1 = 1" "theorem uses : 1 = 1 := ax" "end Probe")

mk_project "${NS_PROBE[@]}"
allowlist "$A" '["Probe.ax"]' '[]'
gate "$A"; if [[ $rc -eq 1 ]] && grep -q "allowlist: Probe.ax is approved without an approval record" "$TMP/out.log"; then
  ok "G-KERNEL rejects an approved axiom with no record"; else bad "approved axiom without record, G-KERNEL (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi
allowlist "$A" '["Probe.ax"]' "[$(printf "$REC" Probe.ax)]"
gate "$A"; if [[ $rc -eq 0 ]]; then ok "namespaced axiom approved by its fully-qualified name passes"; else bad "namespaced approved axiom (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi
allowlist "$A" '["ax"]' "[$(printf "$REC" ax)]"
gate "$A"; if [[ $rc -eq 1 ]] && grep -q "unapproved axiom \`Probe.ax\`" "$TMP/out.log" && grep -q "uses depends on .*Probe.ax" "$TMP/out.log"; then
  ok "approving the short name does not approve a namespaced axiom"; else bad "short-name approval of namespaced axiom (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi

mk_project "namespace Probe" "axiom _root_.rootAx : 2 = 2" "theorem usesRoot : 2 = 2 := rootAx" "end Probe"
allowlist "$A" '["rootAx"]' "[$(printf "$REC" rootAx)]"
gate "$A"; if [[ $rc -eq 0 ]]; then ok "_root_ axiom approved by its root name passes"; else bad "_root_ approved axiom (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi
allowlist "$A" '["Probe.rootAx"]' "[$(printf "$REC" Probe.rootAx)]"
gate "$A"; if [[ $rc -eq 1 ]] && grep -q "unapproved axiom \`rootAx\`" "$TMP/out.log"; then
  ok "a namespaced approval does not cover a _root_ axiom"; else bad "_root_ axiom under namespaced approval (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi

fi

if [[ $PART != lean ]]; then
# --- approved statement changes: the dossier validator's G-AX module -----------------------------
G="$TMP/repo"; mkdir -p "$G/references/schemas" "$G/reports/kernel" "$G/lean/MathAgents" "$G/lean/MathAgentsWIP" "$G/reports/dossiers/ax"
cp "$ROOT"/references/schemas/*.json "$G/references/schemas/"
cp "$ROOT"/references/object-logics.json "$ROOT"/references/prover-engines.json "$G/references/"
cp "$ROOT/references/axiom-allowlist.json" "$ROOT/references/preferences.toml" "$G/references/"
mkdir -p "$G/docs/charter" && cp "$ROOT/docs/charter/03-decisions.md" "$G/docs/charter/"
printf '# Problem card\n\n- **Source:** test\n- **Informal statement:** test\n- **Domain:** research-math\n- **Object logic:** classical-hol\n- **Engine:** lean-builtin\n' > "$G/reports/dossiers/ax/problem-card.md"
printf '[[lean_lib]]\nname = "MathAgents"\n[[lean_lib]]\nname = "MathAgentsWIP"\n' > "$G/lean/lakefile.toml"
echo "theorem t : True := trivial" > "$G/lean/MathAgents/P.lean"; echo "" > "$G/lean/MathAgents.lean"; echo "" > "$G/lean/MathAgentsWIP.lean"
report() {  # report FINGERPRINT : kernel report for MathAgents.Ax.main with that fingerprint
  local sha; sha="$(python3 -c "import sys; sys.path.insert(0,'$ROOT/scripts'); import proof_integrity as g; from pathlib import Path; p=Path('$G/lean'); print(g.source_digest(p, g.libraries(p)[0]))")"
  printf '{"verdict":"PASS","toolchain_pin":"leanprover/lean4:v4.34.1","lean_version":"Lean (version 4.34.1, fixture)","source_sha256":"%s","declarations":[{"decl":"MathAgents.Ax.main","status":"proved","statement_fingerprint":"%s","statement_uses":[],"axioms":[]}]}\n' "$sha" "$1" > "$G/reports/kernel/latest.json"
  python3 - "$G" <<'PYSTAMP'
import hashlib, json, sys
from pathlib import Path
r = Path(sys.argv[1]); p = r / "reports" / "kernel" / "latest.json"; d = json.loads(p.read_text())
d["allowlist"] = {"path": "references/axiom-allowlist.json", "sha256": hashlib.sha256((r / "references" / "axiom-allowlist.json").read_bytes()).hexdigest()}
p.write_text(json.dumps(d))
PYSTAMP
}
fid() {  # fid FINGERPRINT
  printf '{"schema_version":1,"slug":"ax","lean_namespace":"MathAgents.Ax","declarations":[{"decl":"MathAgents.Ax.main","statement_fingerprint":"%s","status":"approved","approver":"operator","date":"2026-10-01"}]}\n' "$1" > "$G/reports/dossiers/ax/fidelity.json"
}
GAXREC='{"id":"AX-1","decl":"MathAgents.Ax.main","old_fingerprint":"100","new_fingerprint":"200","change":"added-hypothesis","description":"adds 0 < n"%s}'
gaxfile() { printf '{"schema_version":1,"slug":"ax","records":[%s]}\n' "$(printf "$GAXREC" "$1")" > "$G/reports/dossiers/ax/gax.json"; }
dv() { set +e; OUT="$(python3 "$ROOT/scripts/validate_dossier.py" --root "$G" --base HEAD "$@" 2>&1)"; RC=$?; set -e; }
expect() { if [[ $RC -eq $2 ]] && grep -qF -- "$3" <<<"$OUT"; then ok "$1"; else bad "$1 (exit $RC)"; sed 's/^/    /' <<<"$OUT"; fi; }

report 100; fid 100; printf '# Dossier\n' > "$G/reports/dossiers/ax/README.md"
git -C "$G" init -q; git -C "$G" add -A; git -C "$G" -c user.email=t@t -c user.name=t commit -qm base
dv ax; expect "approved statement unchanged passes" 0 "PASS"
report 200; fid 200
dv ax; expect "fingerprint change on an approved statement without a G-AX record" 1 "needs a G-AX record in gax.json naming old_fingerprint 100 and new_fingerprint 200"
gaxfile ',"approver":"operator","date":"2026-10-02"'
dv ax; expect "fingerprint change with a G-AX record passes" 0 "PASS"
gaxfile ''
dv ax; expect "G-AX record without approver or waiver" 1 "record lacks approver and date"
gaxfile ',"waiver":{"conversation":"conv-1","date":"2026-10-02"}'
printf '# Dossier\n\nResult status: proved\n' > "$G/reports/dossiers/ax/README.md"
dv ax; expect "waived G-AX change with a plain proved label" 1 "a G-AX change was waived"
printf '# Dossier\n' > "$G/reports/dossiers/ax/README.md"
rm "$G/reports/dossiers/ax/fidelity.json"
dv ax; expect "approved declaration dropped from the fidelity record" 1 "absent from the fidelity record"
fid 200; gaxfile ',"approver":"operator","date":"2026-10-02"'
git -C "$G" add -A; git -C "$G" -c user.email=t@t -c user.name=t commit -qm "re-approve with G-AX"
rm "$G/reports/dossiers/ax/gax.json"
dv ax; expect "G-AX record removed (append-only)" 1 "gax.json is append-only"

# --- review round 1: waiver scope, dossier deletion ----------------------------------------------
cp "$G/reports/dossiers/ax/gax.json" "$TMP/gax.bak" 2>/dev/null || true
git -C "$G" checkout -q -- reports
printf '{"schema_version":1,"slug":"ax","records":[%s,%s]}\n' "$(printf "$GAXREC" ',"approver":"operator","date":"2026-10-02"')" \
  '{"id":"AX-2","decl":"MathAgents.Ax.main","old_fingerprint":"200","new_fingerprint":"300","change":"weakened","description":"drops a case","waiver":{"conversation":"conv-9","date":"2026-10-03"}}' > "$G/reports/dossiers/ax/gax.json"
report 300; fid 300
dv --require-fid ax; expect "new G-AX waiver outside its conversation" 1 "waiver applies only to conversation 'conv-9'"
dv --require-fid ax --conversation conv-9; expect "new G-AX waiver in its own conversation" 0 "PASS"
git -C "$G" checkout -q -- reports; report 200
rm -rf "$G/reports/dossiers/ax"
dv; expect "deleting a dossier that holds gate records" 1 "ax: dossier directory not found"
printf '{"slug":"ax","approver":"operator","date":"2026-10-03","reason":"superseded"}\n' > "$G/reports/dossiers/ax.retired.json"
dv; expect "a tombstone that omits an approved declaration does not count" 1 "ax: dossier directory not found"
printf '{"slug":"ax","approver":"operator","date":"2026-10-03","reason":"superseded","declarations":["MathAgents.Ax.main"]}\n' > "$G/reports/dossiers/ax.retired.json"
dv; expect "a tombstone listing every approved declaration retires the dossier" 0 "PASS"
fi

echo "passed=$pass failed=$failn"
[[ $failn -eq 0 ]]
