#!/usr/bin/env bash
# Dossier-structure gate tests (spec "Test to build" under Dossier structure; DD-1, DD-19, DD-43).
# The spec's four cases (no problem card; a derivation step naming no rule; no strategy review; a
# kernel snapshot whose fingerprint differs from the fidelity record) must exit 1, plus edge cases.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
V="$ROOT/scripts/validate_dossier.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT INT TERM
pass=0; failn=0
mkdir -p "$TMP/references/schemas" "$TMP/reports/kernel" "$TMP/lean/MathAgents" "$TMP/lean/MathAgentsWIP"
cp "$ROOT"/references/schemas/*.json "$TMP/references/schemas/"
cp "$ROOT/references/object-logics.json" "$ROOT/references/prover-engines.json" "$TMP/references/"
cp "$ROOT/references/axiom-allowlist.json" "$ROOT/references/preferences.toml" "$TMP/references/"
mkdir -p "$TMP/docs/charter" && cp "$(python3 -c 'import sys, pathlib; sys.path.insert(0, sys.argv[1]); import instance_root; print(instance_root.charter_path(pathlib.Path(sys.argv[2])))' "$ROOT/scripts" "$ROOT")" "$TMP/docs/charter/"
printf '[[lean_lib]]\nname = "MathAgents"\n[[lean_lib]]\nname = "MathAgentsWIP"\n' > "$TMP/lean/lakefile.toml"
echo "theorem thm : True := trivial" > "$TMP/lean/MathAgents/Pilot.lean"; echo "" > "$TMP/lean/MathAgents.lean"; echo "" > "$TMP/lean/MathAgentsWIP.lean"
echo "leanprover/lean4:v4.34.1" > "$TMP/lean/lean-toolchain"; echo '{"version": "fixture"}' > "$TMP/lean/lake-manifest.json"
python3 -c "import sys; sys.path.insert(0,'$ROOT/scripts'); import build_name_index as b; from pathlib import Path; print(b.header_for(Path('$TMP/lean')) + ' count=1'); print('Nat.succ_le_of_lt')" > "$TMP/reports/kernel/name-index.txt"
SHA="$(python3 -c "import sys; sys.path.insert(0,'$ROOT/scripts'); import proof_integrity as g; from pathlib import Path; p=Path('$TMP/lean'); print(g.source_digest(p, g.libraries(p)[0]))")"
write_report() {  # write_report [thm-status] [dirty]
  printf '{"gate":"G-KERNEL","verdict":"PASS","source_sha256":"%s","commit":"abc123","lean_version":"Lean 4.34.1","toolchain_pin":"leanprover/lean4:v4.34.1","dirty":%s,"declarations":[{"decl":"MathAgents.Pilot.thm","status":"%s","statement_fingerprint":"111","statement_uses":[],"axioms":[]}]}\n' \
    "$SHA" "${2:-false}" "${1:-proved}" > "$TMP/reports/kernel/latest.json"
  python3 - "$TMP" <<'PYSTAMP'
import hashlib, json, sys
from pathlib import Path
r = Path(sys.argv[1]); p = r / "reports" / "kernel" / "latest.json"; d = json.loads(p.read_text())
d["allowlist"] = {"path": "references/axiom-allowlist.json", "sha256": hashlib.sha256((r / "references" / "axiom-allowlist.json").read_bytes()).hexdigest()}
p.write_text(json.dumps(d))
PYSTAMP
}
write_report
FID='{"schema_version":1,"slug":"%s","lean_namespace":"MathAgents.Pilot","declarations":[{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"111","status":"approved","approver":"operator","date":"2026-10-01"}]}'
CARD='# Problem card

- **Source:** Lewis 1976, p. 300 (quoted below)
- **Informal statement:** a quoted statement
- **Domain:** philosophy-of-science
- **Object logic:** classical-hol
- **Engine:** lean-builtin
'
DERIV='## Node: main   Lean: MathAgents.Pilot.thm
Calculus: natural deduction (NK)
Object logic: classical-hol

1. A        [hyp]
2. A → B    [lemma MathAgents.Pilot.thm]
3. B        [→E 1, 2]
'
d() { echo "$TMP/reports/dossiers/$1"; }
dossier() {  # dossier SLUG FILE=CONTENT ...  (CONTENT 'FID' expands to the fidelity record)
  local dir; dir="$(d "$1")"; rm -rf "$dir"; mkdir -p "$dir"; local slug="$1"; shift
  local kv; for kv in "$@"; do
    local f="${kv%%=*}" c="${kv#*=}"
    [[ "$c" == FID ]] && c="$(printf "$FID" "$slug")"
    printf '%s\n' "$c" > "$dir/$f"
  done
}
run() { set +e; OUT="$(python3 "$V" --root "$TMP" "$@" 2>&1)"; RC=$?; set -e; }
expect() {  # expect <label> <rc> <substr>
  if [[ $RC -eq $2 ]] && grep -qF -- "$3" <<<"$OUT"; then echo "ok: $1"; pass=$((pass+1))
  else echo "FAIL: $1 (exit $RC)"; sed 's/^/    /' <<<"$OUT"; failn=$((failn+1)); fi
}
S1=("problem-card.md=$CARD" "statement.md=stmt" "fidelity.json=FID" "back-translation.md=bt")
STRAT_SHA="$(printf 's\n' | sha256sum | cut -d' ' -f1)"   # strategy.md is written as "s"
REVIEW="Verdict: CLEARED
Strategy sha256: $STRAT_SHA"

# --- spec cases -----------------------------------------------------------------------------
dossier nocard "statement.md=stmt" "fidelity.json=FID"
run nocard; expect "Stage 1 artifacts without a problem card" 1 "no problem card"
dossier norule "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/\[→E 1, 2\]/}"
run norule; expect "derivation step naming no rule" 1 "step 3 names no rule or lemma"
dossier noreview "${S1[@]}" "strategy.md=s"
run noreview; expect "strategy without its adversarial review" 1 "has no strategy-review.md"
dossier snapfp "${S1[@]}" 'kernel-snapshot.json={"verdict":"PASS","commit":"c","source_sha256":"s","lean_version":"v","declarations":[{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"999"}]}'
run snapfp; expect "kernel snapshot fingerprint differs from the fidelity record" 1 "differs from the fidelity record's 111"

# --- intake and the problem card ------------------------------------------------------------
dossier pre "interpretation.md=### R1. A reading" "README.md=x"
run pre; expect "pre-intake dossier (brief only) passes" 0 "PASS"
run --require-stage pre 1; expect "dispatching Stage 1 on a pre-intake dossier" 1 "no problem card"
dossier full "${S1[@]}"
run full; expect "complete Stage 1 dossier passes" 0 "PASS"
dossier nofield "problem-card.md=${CARD/- \*\*Engine:\*\* lean-builtin/}" "statement.md=s"
run nofield; expect "card without an engine" 1 "lacks 'Engine'"
dossier badlogic "problem-card.md=${CARD/classical-hol/intuitionistic-x}" "statement.md=s"
run badlogic; expect "object logic not in the registry" 1 "is not an id in references/object-logics.json"
dossier planned "problem-card.md=${CARD/classical-hol/modal-k}" "statement.md=s"
run planned; expect "planned object logic" 1 "registered as planned"
dossier badeng "problem-card.md=${CARD/lean-builtin/hal9000}" "statement.md=s"
run badeng; expect "engine not in the registry" 1 "is not an id in references/prover-engines.json"
dossier baddom "problem-card.md=${CARD/philosophy-of-science/poetry}" "statement.md=s"
run baddom; expect "domain outside D2" 1 "domain 'poetry'"
dossier noread "problem-card.md=$CARD" "interpretation.md=### R1. A reading" "statement.md=s"
run noread; expect "brief exists but the card names no reading" 1 "must name the"
dossier badread "problem-card.md=$CARD- **Reading:** R7" "interpretation.md=### R1. A reading" "statement.md=s"
run badread; expect "reading not in the brief" 1 "reading 'R7' is not a reading"
dossier goodread "problem-card.md=$CARD- **Reading:** R1" "interpretation.md=### R1. A reading" "statement.md=s"
run goodread; expect "card naming a reading of the brief passes" 0 "PASS"

# --- derivations ----------------------------------------------------------------------------
dossier dok "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=$DERIV"
run dok; expect "well-formed derivations pass" 0 "PASS"
dossier dq "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/lemma MathAgents.Pilot.thm/lemma ? — name not located}"
run dq; expect "unlocated lemma is not a named step" 1 "step 2 names no rule or lemma"
dossier dfwd "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/→E 1, 2/→E 1, 3}"
run dfwd; expect "step citing a later step" 1 "cites step 3, which is not earlier"
dossier dcalc "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/Calculus: natural deduction (NK)/}"
run dcalc; expect "node without its calculus" 1 "does not state its Calculus"
dossier dlog "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/Object logic: classical-hol/Object logic: modal-k}"
run dlog; expect "derivation logic differs from the card" 1 "differs from the problem card's 'classical-hol'"
dossier dnostrat "${S1[@]}" "derivations.md=$DERIV"
run dnostrat; expect "derivations without a strategy" 1 "without a Stage 2 strategy.md"
dossier tnod "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "tactic-plan.md=t"
run tnod; expect "tactic plan without derivations" 1 "without Stage 3 derivations.md"

# --- stage dispatch preconditions -----------------------------------------------------------
dossier st "${S1[@]}"
run --require-stage st 3; expect "dispatching Stage 3 without Stage 2 artifacts" 1 "needs strategy.md (stage 2)"
dossier st2 "problem-card.md=$CARD" "statement.md=s" "back-translation.md=b"
run --require-stage st2 2; expect "dispatching Stage 2 implies G-FID" 1 "no fidelity record"
dossier st5 "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=$DERIV" "tactic-plan.md=t"
run --require-stage st5 5; expect "complete dossier may dispatch Stage 5" 0 "PASS"
write_report open
run --require-stage st5 7; expect "Stage 7 needs every approved declaration proved" 1 "needs MathAgents.Pilot.thm proved"
write_report

# --- kernel snapshot (DD-19) ----------------------------------------------------------------
dossier snap "${S1[@]}"
set +e; OUT="$(MATHAGENTS_TEST=1 python3 "$ROOT/scripts/snapshot_kernel.py" --root "$TMP" snap 2>&1)"; RC=$?; set -e
expect "snapshot_kernel.py writes a snapshot" 0 "wrote 1 declaration(s) for snap at commit abc123"
run snap; expect "written snapshot is consistent with the fidelity record" 0 "PASS"
run --require-stage snap 8; expect "Stage 8 with snapshot but no Stage 2-7 artifacts" 1 "needs strategy.md (stage 2)"
FULL=("${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=$DERIV" "tactic-plan.md=t" "informalization.md=n")
dossier snap2 "${FULL[@]}"
run --require-stage snap2 8; expect "Stage 8 dispatch does not need the snapshot it produces" 0 "PASS"
write_report proved true
set +e; OUT="$(MATHAGENTS_TEST=1 python3 "$ROOT/scripts/snapshot_kernel.py" --root "$TMP" snap2 2>&1)"; RC=$?; set -e
expect "snapshot refused from a dirty tree" 1 "dirty lean/ tree"
write_report
dossier snapbad "${S1[@]}" 'kernel-snapshot.json={"verdict":"FAIL","commit":"c","source_sha256":"s","lean_version":"v","declarations":[{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"111"}]}'
run snapbad; expect "snapshot of a failed run" 1 "not PASS"

# --- adversarial review round 1 (DD-34/43/G-AX) ----------------------------------------------
dossier empty "${S1[@]}" "strategy.md=" "strategy-review.md=$REVIEW"
run empty; expect "empty artifact" 1 "strategy.md is empty"
dossier blocked "${S1[@]}" "strategy.md=s" "strategy-review.md=Verdict: BLOCKED — circular"
run --require-stage blocked 3; expect "a BLOCKED strategy review blocks Stage 3" 1 "needs strategy-review.md with 'Verdict: CLEARED'"
dossier noverd "${S1[@]}" "strategy.md=s" "strategy-review.md=looks fine"
run noverd; expect "review without a verdict line" 1 "states no 'Verdict: CLEARED'"
dossier paren "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/3. B        \[→E 1, 2\]/3) B}"
run paren; expect "step in another numbering form" 1 "step not in the"
dossier prenode "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=1. X  [hyp]
$DERIV"
run prenode; expect "numbered step before any node" 1 "outside any '## Node:' section"
dossier nosteps "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=## Node: a
Calculus: ND
Object logic: classical-hol"
run nosteps; expect "node with no steps" 1 "has no steps"
dossier ghost "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/→E 1, 2/→E 1, 0}"
run ghost; expect "citing a step that does not exist" 1 "cites step 0, which does not exist"
dossier sref "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/→E 1, 2/→E s1, s5}"
run sref; expect "'s5'-style forward reference" 1 "cites step 5, which is not earlier"
dossier fenced "problem-card.md=\`\`\`
- **Source:** x
- **Informal statement:** x
- **Domain:** research-math
- **Object logic:** classical-hol
- **Engine:** lean-builtin
\`\`\`" "statement.md=s"
run fenced; expect "card fields inside a code fence do not count" 1 "lacks 'Source'"
dossier dupf "problem-card.md=$CARD- **Engine:** z3" "statement.md=s"
run dupf; expect "card field stated twice" 1 "states 'Engine' more than once"
dossier colon "problem-card.md=${CARD//:\*\*/**:}" "statement.md=s"
run colon; expect "'**Field**: value' form is parsed" 0 "PASS"
dossier forge "${S1[@]}" 'kernel-snapshot.json={"verdict":"PASS","commit":"x","source_sha256":"y","lean_version":"z","dirty":false,"declarations":[{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"111","status":"proved","axioms":["sorryAx"]}]}'
run forge; expect "forged snapshot disagrees with the current report" 1 "axioms of MathAgents.Pilot.thm differs from the current kernel report"
dossier dirty "${S1[@]}" 'kernel-snapshot.json={"verdict":"PASS","commit":"x","source_sha256":"y","lean_version":"z","declarations":[{"decl":"MathAgents.Pilot.thm","statement_fingerprint":"111","status":"proved","axioms":[]}]}'
run dirty; expect "snapshot not marked clean" 1 "not taken from a clean"
python3 - "$TMP" <<'PY2'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "reports" / "kernel" / "latest.json"; d = json.loads(p.read_text())
d["declarations"].append(dict(d["declarations"][0])); p.write_text(json.dumps(d))
PY2
dossier dupk "${S1[@]}"
run dupk; expect "kernel report with a duplicated name" 1 "more than once"
write_report
dossier ref7 "${FULL[@]}" "README.md=Result status: refuted (MathAgents.Pilot.thm)"
write_report open
run --require-stage ref7 7; expect "Stage 7 on a refuted statement is not blocked by the structure check" 1 "without a current human G-CX 'refutes' verdict"
grep -q "needs MathAgents.Pilot.thm proved" <<<"$OUT" && { echo "FAIL: refuted target still required proved"; failn=$((failn+1)); } || { echo "ok: refuted target exempt from 'proved'"; pass=$((pass+1)); }
write_report

# --- adversarial review round 2 ----------------------------------------------------------------
dossier rounds "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW
Round 2 found a circularity.
Verdict: BLOCKED"
run --require-stage rounds 3; expect "a later BLOCKED round overrides an earlier CLEARED" 1 "needs strategy-review.md with 'Verdict: CLEARED'"
dossier stale "${S1[@]}" "strategy.md=s (edited after review)" "strategy-review.md=$REVIEW"
run --require-stage stale 3; expect "strategy edited after its review" 1 "does not match the current strategy.md"
dossier hidden "${S1[@]}" "strategy.md=s" "strategy-review.md=<!-- Verdict: CLEARED -->
Strategy sha256: $STRAT_SHA"
run hidden; expect "a verdict inside an HTML comment does not count" 1 "states no 'Verdict: CLEARED'"
dossier glued "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=${DERIV/→E 1, 2/MP(1,5)}"
run glued; expect "forward reference glued to the rule name" 1 "cites step 5, which is not earlier"
dossier boldstep "${S1[@]}" "strategy.md=s" "strategy-review.md=$REVIEW" "derivations.md=$DERIV**4.** C"
run boldstep; expect "bold-numbered step is not in the canonical form" 1 "step not in the"

# --- D32: a `never` dossier may not depend on an axiom approved in session for another dossier --------
dossier nev "${S1[@]}" "preferences.toml=schema_version = 1
slug = \"nev\"
[fidelity.kernel_as_judge]
choice = \"never\"
alternatives = [\"offer\"]
decision = \"D31\""
mkdir -p "$TMP/reports/dossiers/other"; cp "$TMP/references/axiom-allowlist.json" "$TMP/allow.keep"
python3 - "$TMP" <<'PY2'
import hashlib, json, sys
from pathlib import Path
t = Path(sys.argv[1])
allow = {"note": "t", "base_axioms": ["propext", "Classical.choice", "Quot.sound"], "approved_axioms": ["X.ax"],
         "approvals": [{"axiom": "X.ax", "approver": "operator", "date": "2026-10-01", "reason": "r",
                        "dossier": "other", "conversation": "conv-3"}]}
(t / "references" / "axiom-allowlist.json").write_text(json.dumps(allow))
r = t / "reports" / "kernel" / "latest.json"; d = json.loads(r.read_text())
d["declarations"][0]["axioms"] = ["X.ax"]
d["allowlist"]["sha256"] = hashlib.sha256((t / "references" / "axiom-allowlist.json").read_bytes()).hexdigest()
r.write_text(json.dumps(d))
PY2
ISHA="$(python3 -c "import sys; sys.path.insert(0,'$ROOT/scripts'); import dossier_structure as ds; from pathlib import Path; print(ds.intake_digest(Path('$TMP/reports/dossiers/nev')))")"
python3 - "$TMP/reports/dossiers/nev/fidelity.json" "$ISHA" <<'PY2'
import json, sys
p = sys.argv[1]; d = json.load(open(p)); d["intake_sha256"] = sys.argv[2]; json.dump(d, open(p, "w"))
PY2
run nev; expect "a never dossier depending on another dossier's in-session axiom" 1 "approved by in-session directive"
cp "$TMP/allow.keep" "$TMP/references/axiom-allowlist.json"; rm -rf "$TMP/reports/dossiers/other" "$TMP/reports/dossiers/nev"; write_report

# --- security conditions (2026-10-01 review) --------------------------------------------------
dossier sec "${S1[@]}"
python3 - "$TMP" <<'PY2'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "reports" / "kernel" / "latest.json"; d = json.loads(p.read_text()); d["allowlist"]["sha256"] = "0" * 64; p.write_text(json.dumps(d))
PY2
run --require-fid sec; expect "report produced with another allowlist is rejected" 1 "not produced with the committed"
write_report
run "../etc"; expect "invalid slug is refused" 2 "invalid slug"
set +e; OUT="$(python3 "$ROOT/scripts/snapshot_kernel.py" --root "$TMP" sec 2>&1)"; RC=$?; set -e
expect "snapshot --root outside the test suite is refused" 2 "--root is for the test suite"
set +e; OUT="$(cd "$TMP" && git init -q 2>/dev/null; python3 "$V" --root "$TMP" --base=--output=/tmp/x sec 2>&1)"; RC=$?; set -e
expect "a --base that looks like a git option fails closed" 1 "not a commit"
set +e; OUT="$(python3 "$ROOT/scripts/proof_integrity.py" --lean-dir "$TMP/lean" --allowlist "$TMP/references/axiom-allowlist.json" 2>&1)"; RC=$?; set -e
expect "non-default allowlist may not write the authoritative report" 2 "may not write the authoritative report"

# a kernel snapshot's declaration statuses are kernel records, not result labels
set +e; OUT="$(cd "$ROOT/scripts" && python3 -c "
import sys, validate_dossier as vd
from pathlib import Path
d = Path(sys.argv[1]); d.mkdir(parents=True, exist_ok=True)
(d / 'kernel-snapshot.json').write_text('{\"declarations\": [{\"decl\": \"X.y\", \"status\": \"proved\"}]}')
print('labels:', vd.result_labels(d))" "$TMP/labels-only" 2>&1)"; RC=$?; set -e
expect "kernel-snapshot.json statuses are not result labels" 0 "labels: []"

echo "passed=$pass failed=$failn"
[[ $failn -eq 0 ]]
