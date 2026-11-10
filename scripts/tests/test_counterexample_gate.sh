#!/usr/bin/env bash
# G-CX gate tests (spec "Test to build" + edge cases; DD-16, DD-39, DD-59). Builds throwaway
# dossiers, a minimal Lean tree, and a kernel report whose source hash matches that tree. Every
# seeded defect must exit 1 with the expected finding; valid logs must exit 0.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="$ROOT/scripts/validate_dossier.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT INT TERM
pass=0; failn=0
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"  # sedi
mkdir -p "$TMP/references/schemas" "$TMP/reports/kernel" "$TMP/lean/MathAgents" "$TMP/lean/MathAgentsWIP"
cp "$ROOT/references/schemas/fidelity-record.schema.json" "$ROOT/references/schemas/counterexample-log.schema.json" "$ROOT/references/schemas/gax-record.schema.json" "$TMP/references/schemas/"
cp "$ROOT/references/schemas/prover-engines.schema.json" "$TMP/references/schemas/"
cp "$ROOT/references/object-logics.json" "$ROOT/references/prover-engines.json" "$TMP/references/"
cp "$ROOT/references/axiom-allowlist.json" "$ROOT/references/preferences.toml" "$TMP/references/"
mkdir -p "$TMP/docs/charter" && cp "$ROOT/docs/charter/03-decisions.md" "$TMP/docs/charter/"
printf '[[lean_lib]]\nname = "MathAgents"\n[[lean_lib]]\nname = "MathAgentsWIP"\n' > "$TMP/lean/lakefile.toml"
echo "theorem thm : True := trivial" > "$TMP/lean/MathAgents/Pilot.lean"
echo "import MathAgents.Pilot" > "$TMP/lean/MathAgents.lean"
echo "" > "$TMP/lean/MathAgentsWIP.lean"

# Kernel declarations: Pilot.conj is the open conjecture (fp CONJ_FP); Pilot.witness is a proved
# negation on a finite instance; Pilot.thm is a proved theorem; Pilot.open_w is an open stub.
CONJ_FP=500
write_report() {  # write_report [conj-fingerprint] [conj-status]
  local sha; sha="$(python3 -c "import sys; sys.path.insert(0,'$ROOT/scripts'); import proof_integrity as g; from pathlib import Path; p=Path('$TMP/lean'); print(g.source_digest(p, g.libraries(p)[0]))")"
  cat > "$TMP/reports/kernel/latest.json" <<EOF
{"verdict": "PASS", "toolchain_pin": "leanprover/lean4:v4.34.1", "lean_version": "Lean (version 4.34.1, fixture)", "source_sha256": "$sha", "declarations": [
 {"decl": "Pilot.conj", "status": "${2:-open}", "statement_fingerprint": "${1:-$CONJ_FP}", "axioms": ["sorryAx"]},
 {"decl": "Pilot.witness", "status": "proved", "statement_fingerprint": "600", "negates_fingerprint": "$CONJ_FP", "axioms": []},
 {"decl": "Pilot.CX.unrelated", "status": "proved", "statement_fingerprint": "650", "negates_fingerprint": "12", "axioms": []},
 {"decl": "Pilot.thm", "status": "proved", "statement_fingerprint": "111", "axioms": []},
 {"decl": "Pilot.open_w", "status": "open", "statement_fingerprint": "700", "axioms": ["sorryAx"]}]}
EOF
  python3 - "$TMP" <<'PYSTAMP'
import hashlib, json, sys
from pathlib import Path
r = Path(sys.argv[1]); p = r / "reports" / "kernel" / "latest.json"; d = json.loads(p.read_text())
d["allowlist"] = {"path": "references/axiom-allowlist.json", "sha256": hashlib.sha256((r / "references" / "axiom-allowlist.json").read_bytes()).hexdigest()}
p.write_text(json.dumps(d))
PYSTAMP
}
write_report
dossier() {  # dossier <slug> <counterexamples-json-or-empty> [status-text] [fidelity-json]
  local d="$TMP/reports/dossiers/$1"; rm -rf "$d"; mkdir -p "$d"
  [[ -n "$2" ]] && printf '%s\n' "$2" > "$d/counterexamples.json"
  [[ -n "${4:-}" ]] && printf '%s\n' "$4" > "$d/fidelity.json"
  printf '# Dossier\n\n%s\n' "${3:-}" > "$d/README.md"
  printf '# Problem card\n\n- **Source:** test\n- **Informal statement:** test\n- **Domain:** research-math\n- **Object logic:** classical-hol\n- **Engine:** lean-builtin\n' > "$d/problem-card.md"
}
run() { set +e; OUT="$(python3 "$V" --root "$TMP" "$@" 2>&1)"; RC=$?; set -e; }
expect() {  # expect <label> <rc> <substr>
  if [[ $RC -eq $2 ]] && grep -qF -- "$3" <<<"$OUT"; then echo "ok: $1"; pass=$((pass+1))
  else echo "FAIL: $1 (exit $RC)"; sed 's/^/    /' <<<"$OUT"; failn=$((failn+1)); fi
}
HUMAN='"approver":"operator","date":"2026-10-01"'
WAIVE='"waiver":{"conversation":"conv-1","date":"2026-10-01"}'
# CX <slug> <entry-json> [namespace]
CX() { printf '{"schema_version":1,"slug":"%s","lean_namespace":"%s","counterexamples":[%s]}' "$1" "${3:-Pilot}" "$2"; }
# E <logged-fp> <method> [verdict-json] [extra-fields]
E() { printf '{"id":"CX-1","decl":"Pilot.conj","statement_fingerprint":"%s","method":"%s","description":"n=2 instance"%s%s}' \
  "$1" "$2" "${4:-}" "${3:+,\"verdict\":$3}"; }
V_REF="{\"decision\":\"refutes\",\"statement_fingerprint\":\"$CONJ_FP\",$HUMAN}"
WIT=',"lean_witness":"Pilot.witness"'

# --- spec cases -----------------------------------------------------------------------------
dossier ok "$(CX ok "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "Result status: refuted (Pilot.conj)"
run ok; expect "current human refutes verdict passes" 0 "PASS"
dossier noverdict "$(CX noverdict "$(E $CONJ_FP decide)")" "Result status: refuted (Pilot.conj)"
run noverdict; expect "refuted label with no verdict" 1 "without a current human G-CX 'refutes' verdict"
dossier stale "$(CX stale "$(E $CONJ_FP decide "{\"decision\":\"refutes\",\"statement_fingerprint\":\"499\",$HUMAN}" "$WIT")")" "Result status: refuted (Pilot.conj)"
run stale; expect "verdict fingerprint stale" 1 "verdict stale"

# --- labels and records ---------------------------------------------------------------------
dossier nolog "" "Result status: refuted (Pilot.conj)"
run nolog; expect "refuted label without any log" 1 "without a current human G-CX 'refutes' verdict"
dossier disproved "$(CX disproved "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "**Status:** disproved"
run disproved; expect "'disproved' is non-canonical" 1 "non-canonical result label"
dossier refby "$(CX refby "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "| Result status | refuted by CX-1 |"
run refby; expect "'refuted by ...' is non-canonical" 1 "non-canonical result label"
dossier prose "" "Nothing here is refuted yet, and the **Status:** is open."
run prose; expect "prose mentioning 'refuted' is not a label" 0 "PASS"
dossier pending "$(CX pending "$(E $CONJ_FP smt)")" "Result status: open"
run pending; expect "logged candidate without verdict, unrevised, unlabelled" 0 "PASS"
dossier spur "$(CX spur "$(E $CONJ_FP decide "{\"decision\":\"spurious\",\"statement_fingerprint\":\"$CONJ_FP\",$HUMAN}")")" "Result status: refuted (Pilot.conj)"
run spur; expect "refuted label on a spurious verdict" 1 "without a current human G-CX 'refutes' verdict"
dossier noappr "$(CX noappr "$(E $CONJ_FP decide "{\"decision\":\"refutes\",\"statement_fingerprint\":\"$CONJ_FP\"}" "$WIT")")"
run noappr; expect "verdict without approver or waiver" 1 "lacks approver and date"
dossier both "$(CX both "$(E $CONJ_FP decide "{\"decision\":\"refutes\",\"statement_fingerprint\":\"$CONJ_FP\",$HUMAN,$WAIVE}" "$WIT")")"
run both; expect "verdict with approval and waiver" 1 "both an approval and a waiver"
dossier bad '{"schema_version":1,"slug":"bad","lean_namespace":"Pilot","counterexamples":[{"id":"1","decl":"Pilot.conj","statement_fingerprint":"500","method":"guess","description":"x"}]}'
run bad; expect "schema-invalid log" 1 "counterexamples.json invalid"
dossier dupid "$(CX dupid "$(E $CONJ_FP decide),$(E $CONJ_FP smt)")"
run dupid; expect "duplicate counterexample ids" 1 "duplicate counterexample id CX-1"
dossier nsout "$(CX nsout "$(E $CONJ_FP decide)" Other)"
run nsout; expect "target outside lean_namespace" 1 "outside lean_namespace"
dossier nsdecl "$(CX nsdecl "$(E $CONJ_FP decide)" Pilot.conj)"
run nsdecl; expect "namespace narrowed to a declaration" 1 "is itself a declaration"

# --- solver output and witnesses (DD-16) -----------------------------------------------------
dossier smtnow "$(CX smtnow "$(E $CONJ_FP smt "$V_REF")")" "Result status: refuted (Pilot.conj)"
run smtnow; expect "smt refutation without a Lean witness" 1 "counts only once a kernel-proved lean_witness"
dossier smtw "$(CX smtw "$(E $CONJ_FP smt "$V_REF" "$WIT")")" "Result status: refuted (Pilot.conj)"
run smtw; expect "smt refutation with a proved witness passes" 0 "PASS"
dossier wopen "$(CX wopen "$(E $CONJ_FP atp "$V_REF" ',"lean_witness":"Pilot.open_w"')")" "Result status: refuted (Pilot.conj)"
run wopen; expect "witness open in the kernel report" 1 "not proved"
dossier wmiss "$(CX wmiss "$(E $CONJ_FP decide "$V_REF" ',"lean_witness":"Pilot.nope"')")"
run wmiss; expect "witness absent from the kernel report" 1 "absent from the kernel report"

# --- waivers (D26, DD-59) -------------------------------------------------------------------
V_WAIVE="{\"decision\":\"refutes\",\"statement_fingerprint\":\"$CONJ_FP\",$WAIVE}"
dossier wv "$(CX wv "$(E $CONJ_FP decide "$V_WAIVE" "$WIT")")" "Result status: refuted, verdict-waived (Pilot.conj)"
run wv; expect "waived refutation with a proved witness passes" 0 "PASS"
dossier wvplain "$(CX wvplain "$(E $CONJ_FP decide "$V_WAIVE" "$WIT")")" "Result status: refuted (Pilot.conj)"
run wvplain; expect "waived refutation labelled plain refuted" 1 "label must be 'refuted, verdict-waived'"
dossier wvnow "$(CX wvnow "$(E $CONJ_FP small-model "$V_WAIVE")")" "Result status: refuted, verdict-waived (Pilot.conj)"
run wvnow; expect "waived refutation without a witness" 1 "needs a kernel-proved lean_witness"
dossier wvlab "$(CX wvlab "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "Result status: refuted, verdict-waived (Pilot.conj)"
run wvlab; expect "'verdict-waived' label with only a human verdict" 1 "without a current waived 'refutes' verdict"

# --- revision after a counterexample --------------------------------------------------------
write_report 501
dossier rev "$(CX rev "$(E $CONJ_FP decide)")"
run rev; expect "statement revised with no verdict" 1 "revised after this counterexample was logged"
dossier revok "$(CX revok "$(E $CONJ_FP decide "{\"decision\":\"revise\",\"statement_fingerprint\":\"501\",$HUMAN}")")"
run revok; expect "revision with a current revise verdict passes" 0 "PASS"
dossier revstale "$(CX revstale "$(E $CONJ_FP decide "{\"decision\":\"revise\",\"statement_fingerprint\":\"502\",$HUMAN}")")"
run revstale; expect "revise verdict on a different fingerprint" 1 "verdict stale"
dossier revspur "$(CX revspur "$(E $CONJ_FP decide "{\"decision\":\"spurious\",\"statement_fingerprint\":\"501\",$HUMAN}")")"
run revspur; expect "revision under a non-revise verdict" 1 "not 'revise'"
write_report
dossier revnone "$(CX revnone "$(E $CONJ_FP decide "{\"decision\":\"revise\",\"statement_fingerprint\":\"$CONJ_FP\",$HUMAN}")")"
run revnone; expect "revise verdict but statement unchanged" 1 "is unchanged"
dossier gone "$(CX gone '{"id":"CX-1","decl":"Pilot.removed","statement_fingerprint":"5","method":"decide","description":"x"}')"
run gone; expect "target removed after a logged counterexample" 1 "absent from the kernel report"

# --- contradictions -------------------------------------------------------------------------
write_report "" proved
dossier provedref "$(CX provedref "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "Result status: refuted (Pilot.conj)"
run provedref; expect "refutes verdict on a kernel-proved target" 1 "proved in the kernel report yet"
write_report
dossier twolab "$(CX twolab "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "Result status: refuted (Pilot.conj)

Status: proved"
run twolab; expect "proved and refuted labels together" 1 "both a proved and a refuted"

# --- audit round 1 --------------------------------------------------------------------------
dossier unbound "$(CX unbound "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "Result status: refuted"
run unbound; expect "refuted label naming no declaration" 1 "non-canonical result label"
dossier other "$(CX other "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "Result status: refuted (Pilot.thm)"
run other; expect "label bound to a target the verdict does not cover" 1 "verdict on Pilot.thm"
dossier jlab "" ""
echo '{"status": "refuted"}' > "$TMP/reports/dossiers/jlab/summary.json"
run jlab; expect "JSON-quoted label key" 1 "non-canonical result label"
dossier ylab "" "result_status: refuted"
run ylab; expect "underscore label key" 1 "non-canonical result label"
dossier jfid "" ""
echo '{"status":"proved"}' > "$TMP/reports/dossiers/jfid/summary.json"
run jfid; expect "JSON-quoted proved label (G-FID)" 1 "without a fidelity record"
dossier vfalse "" "Status: false"
run vfalse; expect "'Status: false'" 1 "non-canonical result label"
dossier vout "" "Outcome: refuted (Pilot.conj)"
run vout; expect "'Outcome:' key" 1 "without a current human G-CX 'refutes' verdict"
dossier vconc "" "**Verdict:** not a theorem"
run vconc; expect "'not a theorem' value" 1 "non-canonical result label"
dossier vcx "" "Verdict: counterexample found"
run vcx; expect "'counterexample found' value" 1 "non-canonical result label"
dossier vsemi "" "Status: open; refuted by CX-1"
run vsemi; expect "refutation after a semicolon" 1 "non-canonical result label"
dossier descr "$(CX descr "$(E $CONJ_FP smt "" ',"engine":"z3"')" | sed 's/n=2 instance/status: refuted by z3/')"
run descr; expect "label-like text inside the log is not a label" 0 "PASS"
dossier dnow "$(CX dnow "$(E $CONJ_FP decide "$V_REF")")"
run dnow; expect "decide refutation without a witness" 1 "counts only once a kernel-proved lean_witness"
dossier mnow "$(CX mnow "$(E $CONJ_FP manual "$V_REF")")" "Result status: refuted (Pilot.conj)"
run mnow; expect "manual refutation under a human verdict needs no witness" 0 "PASS"
write_report 501
dossier wrev "$(CX wrev "$(E $CONJ_FP smt "{\"decision\":\"revise\",\"statement_fingerprint\":\"501\",$WAIVE}")")"
run wrev; expect "waived revise without a witness" 1 "needs a kernel-proved lean_witness"
write_report
FIDREC='{"schema_version":1,"slug":"nsdiff","lean_namespace":"Pilot.Main","declarations":[{"decl":"Pilot.Main.t","statement_fingerprint":"1","status":"approved","approver":"o","date":"2026-10-01"}]}'
dossier nsdiff "$(CX nsdiff "$(E $CONJ_FP decide)")" "" "$FIDREC"
run nsdiff; expect "fidelity and counterexample namespaces differ" 1 "a dossier has one namespace"

# --- append-only log (git base) -------------------------------------------------------------
G="$TMP/git"; mkdir -p "$G"; cp -r "$TMP/references" "$TMP/lean" "$TMP/reports" "$TMP/docs" "$G/"; rm -rf "$G/reports/dossiers"
git -C "$G" init -q; git -C "$G" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
mkdir -p "$G/reports/dossiers/ap"; cp "$TMP/reports/dossiers/ok/problem-card.md" "$G/reports/dossiers/ap/"; printf '%s\n' "$(CX ap "$(E $CONJ_FP decide)")" > "$G/reports/dossiers/ap/counterexamples.json"
git -C "$G" add -A; git -C "$G" -c user.email=t@t -c user.name=t commit -q -m log
grun() { set +e; OUT="$(python3 "$V" --root "$G" "$@" 2>&1)"; RC=$?; set -e; }
grun ap --base HEAD; expect "unchanged committed log passes" 0 "PASS"
sedi 's/"statement_fingerprint":"500"/"statement_fingerprint":"501"/' "$G/reports/dossiers/ap/counterexamples.json"
grun ap --base HEAD; expect "logged fingerprint rewritten (laundered revision)" 1 "statement_fingerprint changed"
sedi 's/"Pilot.conj"/"Pilot.thm"/; s/"501"/"500"/' "$G/reports/dossiers/ap/counterexamples.json"
grun ap --base HEAD; expect "target re-pointed" 1 "decl changed"
printf '%s\n' "$(CX ap "$(E $CONJ_FP decide | sed 's/CX-1/CX-2/')")" > "$G/reports/dossiers/ap/counterexamples.json"
grun ap --base HEAD; expect "entry removed" 1 "CX-1 was removed"
rm "$G/reports/dossiers/ap/counterexamples.json"
grun ap --base HEAD; expect "log deleted" 1 "was deleted"
git -C "$G" checkout -q -- reports
grun ap --base nope; expect "unknown --base fails closed" 1 "not a commit"
run ok --base HEAD; expect "--base outside a git work tree fails closed" 1 "is not in a git work tree"
# a git that cannot run (macOS xcrun shim under a sandbox exits 71) is not "no work tree": fail closed (M6-F4)
mkdir -p "$TMP/brokengit"; printf '#!/bin/sh\necho "git: error: cannot exec git" >&2\nexit 71\n' > "$TMP/brokengit/git"
chmod +x "$TMP/brokengit/git"
set +e; OUT="$(PATH="$TMP/brokengit:$PATH" python3 "$V" --root "$G" ap 2>&1)"; RC=$?; set -e
expect "git that cannot run fails closed" 2 "git rev-parse failed (exit 71)"
grun; expect "no origin/HEAD and no --base fails closed" 1 "no origin/HEAD"
# default base = merge base with upstream: an edit already committed locally is still caught
git clone -q "$G" "$TMP/clone"; C="$TMP/clone"
cp "$TMP/reports/kernel/latest.json" "$C/reports/kernel/" 2>/dev/null || { mkdir -p "$C/reports/kernel"; cp "$TMP/reports/kernel/latest.json" "$C/reports/kernel/"; }
crun() { set +e; OUT="$(python3 "$V" --root "$C" "$@" 2>&1)"; RC=$?; set -e; }
crun; expect "clone at its upstream passes" 0 "PASS"
sedi 's/"statement_fingerprint":"500"/"statement_fingerprint":"501"/' "$C/reports/dossiers/ap/counterexamples.json"
git -C "$C" -c user.email=t@t -c user.name=t commit -qam launder
crun; expect "committed laundering caught against the upstream merge base" 1 "statement_fingerprint changed"
git -C "$C" reset -q --hard HEAD~1; git -C "$C" mv reports/dossiers/ap reports/dossiers/ap2
git -C "$C" -c user.email=t@t -c user.name=t commit -qm rename
crun; expect "dossier with a log renamed away" 1 "ap: dossier directory not found"
# a pushed feature branch: its own upstream contains the edit, but the default branch does not
git -C "$C" reset -q --hard HEAD~1; git -C "$C" checkout -q -b feature
sedi 's/"statement_fingerprint":"500"/"statement_fingerprint":"501"/' "$C/reports/dossiers/ap/counterexamples.json"
git -C "$C" -c user.email=t@t -c user.name=t commit -qam launder; git -C "$C" push -q -u origin feature 2>/dev/null
crun; expect "laundering pushed on a feature branch caught against origin/HEAD" 1 "statement_fingerprint changed"
# an entry committed locally but not yet on the default branch is protected through HEAD
git -C "$C" reset -q --hard HEAD~1
printf '%s\n' "$(CX ap "$(E $CONJ_FP decide),$(E $CONJ_FP smt | sed 's/CX-1/CX-2/')")" > "$C/reports/dossiers/ap/counterexamples.json"
git -C "$C" -c user.email=t@t -c user.name=t commit -qam "log CX-2 locally"
printf '%s\n' "$(CX ap "$(E $CONJ_FP decide)")" > "$C/reports/dossiers/ap/counterexamples.json"
crun; expect "locally committed entry removed (caught via HEAD)" 1 "CX-2 was removed"

# --- per-commit history (IA-01): a change made in an intermediate commit and undone later is
# caught, though the base and the tip agree (a cancelled CI run leaves such a commit unverified)
H="$TMP/hist"; mkdir -p "$H"; cp -r "$G/references" "$G/lean" "$G/docs" "$H/"; mkdir -p "$H/reports/kernel"
cp "$TMP/reports/kernel/latest.json" "$H/reports/kernel/"
git -C "$H" init -q; hc() { git -C "$H" add -A; git -C "$H" -c user.email=t@t -c user.name=t commit -qm "$1"; }
mkdir -p "$H/reports/dossiers/ap"; cp "$TMP/reports/dossiers/ok/problem-card.md" "$H/reports/dossiers/ap/"
LOG1="$(CX ap "$(E $CONJ_FP decide)")"
printf '%s\n' "$LOG1" > "$H/reports/dossiers/ap/counterexamples.json"; hc A; A="$(git -C "$H" rev-parse HEAD)"
hrun() { set +e; OUT="$(python3 "$V" --root "$H" --base "$A" "$@" 2>&1)"; RC=$?; set -e; }
hrun ap; expect "history: untouched log passes" 0 "PASS"
printf '%s\n' "$(CX ap "")" > "$H/reports/dossiers/ap/counterexamples.json"; hc "B: drop CX-1"
printf '%s\n' "$LOG1" > "$H/reports/dossiers/ap/counterexamples.json"; hc "C: restore CX-1"
hrun ap; expect "history: entry removed in one commit and restored in the next" 1 "history"
expect "  ... names the removal" 1 "CX-1 was removed"
git -C "$H" reset -q --hard "$A"
sedi 's/"statement_fingerprint":"500"/"statement_fingerprint":"501"/' "$H/reports/dossiers/ap/counterexamples.json"; hc "B: launder"
printf '%s\n' "$LOG1" > "$H/reports/dossiers/ap/counterexamples.json"; hc "C: restore"
hrun ap; expect "history: logged fingerprint changed and restored" 1 "history"
expect "  ... names the immutable field" 1 "statement_fingerprint changed"
git -C "$H" reset -q --hard "$A"
git -C "$H" rm -rq reports/dossiers/ap; hc "B: delete dossier"
git -C "$H" checkout -q "$A" -- reports/dossiers/ap; hc "C: restore dossier"
hrun; expect "history: dossier deleted and restored" 1 "history"
expect "  ... names the deletion" 1 "deleted"
git -C "$H" reset -q --hard "$A"
hrun ap --no-history; expect "--no-history keeps the snapshot comparison only" 0 "PASS"
# a rename hides nothing: the old dossier's records count as deleted in that commit
git -C "$H" mv reports/dossiers/ap reports/dossiers/ap2; hc "B: rename"
git -C "$H" mv reports/dossiers/ap2 reports/dossiers/ap; hc "C: rename back"
hrun; expect "history: dossier renamed away and back" 1 "ap: gate records deleted"
git -C "$H" reset -q --hard "$A"
# a deletion with a valid human tombstone passes
git -C "$H" rm -rq reports/dossiers/ap; mkdir -p "$H/reports/dossiers"
printf '{"slug":"ap","approver":"operator","date":"2026-10-03","reason":"test","declarations":[]}\n' > "$H/reports/dossiers/ap.retired.json"; hc "B: retire"
hrun; expect "history: retired with a tombstone passes" 0 "PASS"
git -C "$H" reset -q --hard "$A"
# a merge resolution may not drop what the other side logged
git -C "$H" checkout -qb side
printf '%s\n' "$(CX ap "$(E $CONJ_FP decide),$(E $CONJ_FP smt | sed 's/CX-1/CX-2/')")" > "$H/reports/dossiers/ap/counterexamples.json"; hc "S: log CX-2"
git -C "$H" checkout -q -; echo "note" >> "$H/reports/dossiers/ap/problem-card.md"; hc "M: unrelated"
git -C "$H" -c user.email=t@t -c user.name=t merge -q --no-commit --no-ff side  # no conflict: the sides touch different files
printf '%s\n' "$LOG1" > "$H/reports/dossiers/ap/counterexamples.json"; hc "X: merge dropping CX-2"
hrun ap; expect "history: merge resolution drops the other side's entry" 1 "CX-2 was removed"
git -C "$H" reset -q --hard "$A"; git -C "$H" branch -qD side
# an approved statement changed in one commit and restored in the next needs a G-AX record
FIDA='{"schema_version":1,"slug":"ap","lean_namespace":"Pilot","declarations":[{"decl":"Pilot.thm","statement_fingerprint":"111","status":"approved","approver":"o","date":"2026-10-01"}]}'
printf '%s\n' "$FIDA" > "$H/reports/dossiers/ap/fidelity.json"; hc "A2: approval"; A2="$(git -C "$H" rev-parse HEAD)"
sedi 's/"111"/"112"/' "$H/reports/dossiers/ap/fidelity.json"; hc "B: approval moved"
printf '%s\n' "$FIDA" > "$H/reports/dossiers/ap/fidelity.json"; hc "C: restored"
set +e; OUT="$(python3 "$V" --root "$H" --base "$A2" ap 2>&1)"; RC=$?; set -e
expect "history: approved fingerprint changed without a G-AX record" 1 "was approved with fingerprint 111"
git -C "$H" reset -q --hard "$A"

# --- audit round 2: structural labels, vocabulary scope, waived spurious, long lines -----------
dossier tcol "" "| Declaration | Status |
|---|---|
| Pilot.conj | refuted |"
run tcol; expect "label in a key-headed table column" 1 "non-canonical result label 'refuted'"
dossier tcolok "$(CX tcolok "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "| Declaration | **Result status** |
|:--|:--|
| Pilot.conj | refuted (Pilot.conj) |"
run tcolok; expect "canonical label in a table column passes" 0 "PASS"
dossier tfid "" "| Declaration | Status |
| --- | --- |
| Pilot.thm | proved |"
run tfid; expect "proved in a table column (G-FID)" 1 "without a fidelity record"
dossier hlab "" "## Status

refuted (Pilot.conj)"
run hlab; expect "label under a key heading" 1 "without a current human G-CX 'refutes' verdict"
dossier hprose "" "## Conclusion

The converse is false without positivity."
run hprose; expect "'false' under a loose key heading is prose" 0 "PASS"
dossier jbool "" ""
echo '{"label": false, "status": "draft"}' > "$TMP/reports/dossiers/jbool/meta.json"
run jbool; expect "unquoted JSON boolean is not a label" 0 "PASS"
dossier cprose "" "**Conclusion:** the converse is false without positivity."
run cprose; expect "'false' after a loose key is prose" 0 "PASS"
dossier sfalse "" "Status: false"
run sfalse; expect "'false' after a status key is a label" 1 "non-canonical result label"
write_report "" proved
dossier wspur "$(CX wspur "$(E $CONJ_FP smt "{\"decision\":\"spurious\",\"statement_fingerprint\":\"$CONJ_FP\",$WAIVE}")")"
run wspur; expect "waived spurious with the target kernel-proved passes" 0 "PASS"
write_report
dossier wspuro "$(CX wspuro "$(E $CONJ_FP smt "{\"decision\":\"spurious\",\"statement_fingerprint\":\"$CONJ_FP\",$WAIVE}")")"
run wspuro; expect "waived spurious with the target open" 1 "needs Pilot.conj proved"
dossier longl "" "$(python3 -c "print('status:' * 20000)")"
SECONDS=0; run longl; [[ $SECONDS -lt 10 ]] && expect "pathological line stays fast" 0 "PASS" || { echo "FAIL: pathological line took ${SECONDS}s"; failn=$((failn+1)); }

# --- audit round 3 --------------------------------------------------------------------------
dossier kcol "" "| Declaration | Kernel status |
|-|-|
| Pilot.conj | refuted |"
run kcol; expect "'Kernel status' column with a |-| rule" 1 "non-canonical result label 'refuted'"
dossier hof "" "## Status of Pilot.conj

refuted (Pilot.conj)"
run hof; expect "'Status of <decl>' heading" 1 "without a current human G-CX 'refutes' verdict"
dossier esc "" "| Declaration | Status |
|---|---|
| Pilot.conj \\| alt | refuted |"
run esc; expect "escaped pipe does not shift columns" 1 "non-canonical result label 'refuted'"
dossier ofalse "" "Outcome: false"
run ofalse; expect "'Outcome: false'" 1 "non-canonical result label"
dossier onat "" "Conclusion: not a theorem"
run onat; expect "'Conclusion: not a theorem'" 1 "non-canonical result label"
dossier ybool "" ""
printf 'status: false\n' > "$TMP/reports/dossiers/ybool/meta.yaml"
run ybool; expect "unquoted 'status: false' in YAML stays a label" 1 "non-canonical result label"

# --- stage-agent review: witness binding (DD-59) ------------------------------------------------
dossier unrel "$(CX unrel "$(E $CONJ_FP decide "$V_REF" ',"lean_witness":"Pilot.CX.unrelated"')")" "Result status: refuted (Pilot.conj)"
run unrel; expect "proved witness that negates a different statement" 1 "does not negate the logged statement"
dossier nonneg "$(CX nonneg "$(E $CONJ_FP decide "$V_REF" ',"lean_witness":"Pilot.thm"')")" "Result status: refuted (Pilot.conj)"
run nonneg; expect "proved witness that is no negation at all" 1 "does not negate the logged statement"
write_report 501
dossier revw "$(CX revw "$(E $CONJ_FP smt "{\"decision\":\"revise\",\"statement_fingerprint\":\"501\",$WAIVE}" "$WIT")")"
run revw; expect "waived revise with a witness negating the logged statement" 0 "PASS"
write_report

# --- log_counterexample.py --------------------------------------------------------------------
L="$ROOT/scripts/log_counterexample.py"
lrun() { set +e; OUT="$(python3 "$L" --root "$TMP" "$@" 2>&1)"; RC=$?; set -e; }
dossier lg "" ""
lrun add lg --decl Pilot.conj --method smt --description "n=2"; expect "add without fidelity record or --namespace refused" 1 "pass --namespace"
lrun add lg --decl Pilot.conj --method smt --description "n=2" --namespace Pilot --engine z3; expect "add creates the log" 0 "logged CX-1"
lrun add lg --decl Pilot.conj --method decide --description "n=2 by decide"; expect "add appends the next id" 0 "logged CX-2"
grep -q '"statement_fingerprint": "500"' "$TMP/reports/dossiers/lg/counterexamples.json" && grep -q '"schema_version": 1' "$TMP/reports/dossiers/lg/counterexamples.json" \
  && { echo "ok: logged fingerprint comes from the kernel report"; pass=$((pass+1)); } || { echo "FAIL: logged fingerprint/schema fields"; failn=$((failn+1)); }
lrun add lg --decl Pilot.nope --method smt --description x; expect "add on a target absent from the kernel refused" 1 "not in the kernel report"
lrun witness lg CX-2 Pilot.CX.unrelated; expect "witness negating another statement refused" 1 "does not negate"
lrun witness lg CX-2 Pilot.open_w; expect "unproved witness refused" 1 "not proved"
lrun witness lg CX-2 Pilot.witness; expect "bound witness recorded" 0 "recorded lean_witness Pilot.witness"
lrun witness lg CX-2 Pilot.witness; expect "witness not overwritten" 1 "already records"
run lg; expect "logger output passes the validator" 0 "PASS"

# --- kernel report freshness ----------------------------------------------------------------
dossier fresh "$(CX fresh "$(E $CONJ_FP decide "$V_REF" "$WIT")")" "Result status: refuted (Pilot.conj)"
echo "-- edited" >> "$TMP/lean/MathAgents/Pilot.lean"
run fresh; expect "stale kernel report" 1 "stale kernel report"

echo "passed=$pass failed=$failn"
[[ $failn -eq 0 ]]
