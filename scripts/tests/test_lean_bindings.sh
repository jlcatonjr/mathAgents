#!/usr/bin/env bash
# G-NAME tests (spec "Test to build" under G-NAME; DD-17, DD-18). A dossier citing an invented name,
# and one citing an open declaration as proved, must exit 1; plus index, tactic-plan and Stage 8 cases.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"  # sedi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
C="$ROOT/scripts/check_lean_bindings.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT INT TERM
pass=0; failn=0
mkdir -p "$TMP/references/schemas" "$TMP/reports/kernel" "$TMP/reports/dossiers" "$TMP/lean/MathAgents" "$TMP/lean/MathAgentsWIP"
cp "$ROOT"/references/schemas/*.json "$TMP/references/schemas/"
cp "$ROOT/references/object-logics.json" "$ROOT/references/prover-engines.json" "$ROOT/references/axiom-allowlist.json" "$TMP/references/"
printf '[[lean_lib]]\nname = "MathAgents"\n[[lean_lib]]\nname = "MathAgentsWIP"\n' > "$TMP/lean/lakefile.toml"
echo "leanprover/lean4:v4.34.1" > "$TMP/lean/lean-toolchain"; echo '{"version": "fixture"}' > "$TMP/lean/lake-manifest.json"
echo "theorem thm : True := trivial" > "$TMP/lean/MathAgents/P.lean"; echo "" > "$TMP/lean/MathAgents.lean"; echo "" > "$TMP/lean/MathAgentsWIP.lean"
python3 - "$ROOT" "$TMP" <<'PY'
import hashlib, json, sys
from pathlib import Path
root, tmp = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(root / "scripts")); import proof_integrity as g, build_name_index as b
lean = tmp / "lean"
report = {"verdict": "PASS", "toolchain_pin": "leanprover/lean4:v4.34.1", "lean_version": "Lean (version 4.34.1, fixture)", "source_sha256": g.source_digest(lean, g.libraries(lean)[0]),
          "allowlist": {"path": "references/axiom-allowlist.json",
                        "sha256": hashlib.sha256((tmp / "references" / "axiom-allowlist.json").read_bytes()).hexdigest()},
          "declarations": [
            {"decl": "MathAgents.P.main", "status": "proved", "statement_fingerprint": "1", "statement_uses": [], "axioms": []},
            {"decl": "MathAgents.P.stub", "status": "open", "statement_fingerprint": "2", "statement_uses": [], "axioms": ["sorryAx"]}]}
(tmp / "reports" / "kernel" / "latest.json").write_text(json.dumps(report))
(tmp / "reports" / "kernel" / "name-index.txt").write_text(b.header_for(lean) + " count=2\nNat.succ_le_of_lt\nFinset.sum_comm\n")
PY
d() { local dir="$TMP/reports/dossiers/$1"; rm -rf "$dir"; mkdir -p "$dir"; printf '%s\n' "$3" > "$dir/$2"; }
run() { set +e; OUT="$(python3 "$C" --root "$TMP" "$@" 2>&1)"; RC=$?; set -e; }
expect() {
  if [[ $RC -eq $2 ]] && grep -qF -- "$3" <<<"$OUT"; then echo "ok: $1"; pass=$((pass+1))
  else echo "FAIL: $1 (exit $RC)"; sed 's/^/    /' <<<"$OUT"; failn=$((failn+1)); fi
}

# --- spec cases -----------------------------------------------------------------------------
d invented informalization.md "By [Lean: Nat.totally_made_up] every n is small."
run invented; expect "binding to an invented name" 1 "resolves to no declaration"
d openproved informalization.md "The main step is proved [Lean: MathAgents.P.stub]."
run openproved; expect "open declaration narrated as proved" 1 "says 'open' (DD-18)"

# --- resolution -----------------------------------------------------------------------------
d good informalization.md "We have proved [Lean: MathAgents.P.main], using [Lean: Nat.succ_le_of_lt, Finset.sum_comm]."
run good; expect "project and Mathlib names resolve" 0 "PASS"
d openok informalization.md "This statement is not proved yet [Lean: MathAgents.P.stub | open]; it remains open."
run openok; expect "'not proved' is not a proved claim" 0 "PASS"
d planok tactic-plan.md "Lemmas: Nat.succ_le_of_lt (located: Mathlib/Order/Basic.lean) | Finset.sum_comm (located: x)"
run planok; expect "tactic-plan lemmas located in the index pass" 0 "PASS"
d planbad tactic-plan.md "Lemmas: Nat.made_up_lemma (located: nowhere)"
run planbad; expect "tactic-plan lemma that does not exist" 1 "Nat.made_up_lemma resolves to no declaration"
d planunv tactic-plan.md "Lemmas: Finset.sum_comm (UNVERIFIED)"
run planunv; expect "UNVERIFIED tactic-plan lemma" 1 "is marked UNVERIFIED"
d nobind informalization.md "Prose with no bindings."
run nobind; expect "no bindings, nothing to check" 0 "PASS"

# --- adversarial review round 1 ----------------------------------------------------------------
d emph tactic-plan.md "**Lemmas:** Fake.nonexistent | Nat.succ_le_of_lt"
run emph; expect "fake lemma before a real one, behind markdown emphasis" 1 "Fake.nonexistent resolves to no declaration"
d unparse tactic-plan.md "Lemmas: [x](link) | Nat.succ_le_of_lt"
run unparse; expect "lemma item that does not parse" 1 "cannot parse tactic-plan lemma"
d multiline tactic-plan.md "Lemmas:
- Fake.lemma"
run multiline; expect "Lemmas list on following lines" 1 "must be on its own line"
d node tactic-plan.md "## Node: main   Lean: MathAgents.P.ghost
Lemmas: Nat.succ_le_of_lt"
run node; expect "node header naming a missing declaration" 1 "MathAgents.P.ghost resolves to no declaration"
d lower informalization.md "As [lean: Nat.ghost_lemma] shows."
run lower; expect "lower-case binding" 1 "Nat.ghost_lemma resolves to no declaration"
d split informalization.md "As [Lean:
Nat.ghost_split] shows."
run split; expect "binding split across lines" 1 "Nat.ghost_split resolves to no declaration"
d unterm informalization.md "As [Lean: Nat.succ_le_of_lt shows, unterminated."
run unterm; expect "unterminated binding" 1 "unterminated binding"
d estab informalization.md "The main step is established [Lean: MathAgents.P.stub]."
run estab; expect "non-proved declaration narrated without its status" 1 "bind it with its status"
d nextline informalization.md "We bind [Lean: MathAgents.P.stub] here.
It is proved."
run nextline; expect "proved claim on the next line of the same paragraph" 1 "narration calls MathAgents.P.stub proved"
d stated informalization.md "The step [Lean: MathAgents.P.stub | open] remains open."
run stated; expect "non-proved declaration with its status stated" 0 "PASS"
d openset informalization.md "[Lean: MathAgents.P.stub] shows every open set is measurable; hence it holds."
run openset; expect "'open set' does not count as a status" 1 "bind it with its status"
d mismatch informalization.md "As [Lean: MathAgents.P.main | open] states."
run mismatch; expect "status tag that contradicts the kernel" 1 "tags MathAgents.P.main as 'open'"
d badtag informalization.md "As [Lean: MathAgents.P.stub | nearly] states."
run badtag; expect "unknown status tag" 1 "unknown status 'nearly'"
d provedtag informalization.md "We have [Lean: MathAgents.P.main | proved]."
run provedtag; expect "matching proved tag passes" 0 "PASS"
d uscore informalization.md "See [Lean: Nat.succ_le_of_lt_]."
run uscore; expect "a trailing underscore is part of the name" 1 "Nat.succ_le_of_lt_ resolves to no declaration"
d twonames tactic-plan.md "Lemmas: Nat.succ_le_of_lt and Nat.fake (located: x)"
run twonames; expect "lemma item with two names" 1 "cannot parse tactic-plan lemma"
d h3node derivations.md "### Node: x   Lean: MathAgents.P.ghost"
run h3node; expect "### Node: header is resolved" 1 "MathAgents.P.ghost resolves to no declaration"
d falseref informalization.md "As [Lean: MathAgents.P.stub | refuted] shows."
run falseref; expect "'refuted' tag without a G-CX refuted label" 1 "has no G-CX"
d trueref informalization.md "Result status: refuted (MathAgents.P.stub)

As [Lean: MathAgents.P.stub | refuted] shows."
run trueref; expect "'refuted' tag backed by the refuted label" 0 "PASS"
run nosuchslug; expect "named slug that does not exist" 1 "dossier directory not found"
cp "$TMP/reports/kernel/name-index.txt" "$TMP/idx.bak"
sedi '1s/count=2/count=3/' "$TMP/reports/kernel/name-index.txt"
run good; expect "index whose count does not match" 1 "count does not match"
cp "$TMP/idx.bak" "$TMP/reports/kernel/name-index.txt"
sedi '1s/count=2/count=3/' "$TMP/reports/kernel/name-index.txt"; echo "MathAgents.P.ghost" >> "$TMP/reports/kernel/name-index.txt"
run good; expect "index listing a project name" 1 "lists project declarations"
cp "$TMP/idx.bak" "$TMP/reports/kernel/name-index.txt"

# --- --assembled-only (CI): only dossiers at Stage 7+ are scanned --------------------------------
d midway informalization.md "x"; rm "$TMP/reports/dossiers/midway/informalization.md"; echo "## Node: x   Lean: MathAgents.P.Aux.notyet" > "$TMP/reports/dossiers/midway/derivations.md"
set +e; OUT="$(python3 "$C" --root "$TMP" --assembled-only 2>&1)"; RC=$?; set -e
grep -q "midway" <<<"$OUT" && { echo "FAIL: --assembled-only scanned a mid-pipeline dossier"; failn=$((failn+1)); } || { echo "ok: --assembled-only skips mid-pipeline dossiers"; pass=$((pass+1)); }
echo "n" > "$TMP/reports/dossiers/midway/informalization.md"
set +e; OUT="$(python3 "$C" --root "$TMP" --assembled-only 2>&1)"; RC=$?; set -e
expect "--assembled-only scans an assembled dossier" 1 "MathAgents.P.Aux.notyet resolves to no declaration"
rm -rf "$TMP/reports/dossiers/midway"

# --- the index fails closed -----------------------------------------------------------------
mv "$TMP/reports/kernel/name-index.txt" "$TMP/name-index.bak"
run good; expect "missing index" 1 "no name index"
mv "$TMP/name-index.bak" "$TMP/reports/kernel/name-index.txt"
echo '{"version": "bumped"}' > "$TMP/lean/lake-manifest.json"
run good; expect "index stale after a manifest change" 1 "stale"
echo '{"version": "fixture"}' > "$TMP/lean/lake-manifest.json"
run good; expect "index valid again for its manifest" 0 "PASS"
run "../x"; expect "invalid slug" 2 "invalid slug"

echo "passed=$pass failed=$failn"
[[ $failn -eq 0 ]]
