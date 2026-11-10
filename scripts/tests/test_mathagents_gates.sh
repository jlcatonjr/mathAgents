#!/usr/bin/env bash
# Gate tests. Each seeded defect must be reported by EVERY layer that should see it (matched by
# finding text, so one layer cannot mask a broken other), with exit code 1 (a finding) rather
# than 2 (a gate error). A clean probe must PASS. Runs on a throwaway copy of the Lean project
# that shares only .lake/packages (read-mostly dependency builds); probe build products stay in
# the copy's own .lake/build and are removed with it.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT INT TERM
pass=0; failn=0
ok() { echo "ok: $1"; pass=$((pass+1)); }
bad() { echo "FAIL: $1"; failn=$((failn+1)); }

mk_project() {
  rm -rf "$TMP/lean"; mkdir -p "$TMP/lean/.lake"
  cp -r "$ROOT/lean/MathAgents" "$ROOT/lean/MathAgents.lean" "$ROOT/lean/MathAgentsWIP" "$ROOT/lean/MathAgentsWIP.lean" "$ROOT/lean/lakefile.toml" \
        "$ROOT/lean/lean-toolchain" "$ROOT/lean/lake-manifest.json" "$TMP/lean/"
  ln -s "$ROOT/lean/.lake/packages" "$TMP/lean/.lake/packages"
  printf '%s\n' "$@" > "$TMP/lean/MathAgents/GateProbe.lean"
  echo "import MathAgents.GateProbe" >> "$TMP/lean/MathAgents.lean"
}
# mk_wip LINE... : clean proved library plus a probe module as the ONLY module of MathAgentsWIP, so the
# per-declaration counts do not depend on the open stubs the real WIP library carries.
mk_wip() {
  mk_project "theorem probe_ok : True := trivial"
  rm -rf "$TMP/lean/MathAgentsWIP"; mkdir -p "$TMP/lean/MathAgentsWIP"
  printf '%s\n' "$@" > "$TMP/lean/MathAgentsWIP/GateProbe.lean"
  printf '%s\n' "-- Root of the open-work library (gate-test probe only)." "import MathAgentsWIP.GateProbe" > "$TMP/lean/MathAgentsWIP.lean"
}
gate() { set +e; python3 "$ROOT/scripts/proof_integrity.py" --lean-dir "$TMP/lean" --no-report >"$TMP/out.log" 2>&1; rc=$?; set -e; }

# expect_findings LABEL PATTERN... : gate must exit 1 and report every PATTERN.
expect_findings() {
  local label="$1"; shift; gate
  if [[ $rc -ne 1 ]]; then bad "$label (exit $rc, expected 1)"; sed 's/^/    /' "$TMP/out.log" | tail -5; return; fi
  local p; for p in "$@"; do
    if ! grep -qE -- "$p" "$TMP/out.log"; then bad "$label (missing finding /$p/)"; sed 's/^/    /' "$TMP/out.log" | tail -8; return; fi
  done
  ok "$label"
}

mk_project "import Mathlib.Tactic.NormNum" "theorem probe_clean : 2 + 2 = 4 := by norm_num"
gate; if [[ $rc -eq 0 ]]; then ok "clean probe passes"; else bad "clean probe (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -8; fi

mk_project "theorem probe_sorry : 1 = 2 := by sorry"
expect_findings "sorry: source + build + envelope" "forbidden \`sorry\`" "build: a declaration uses sorry" "probe_sorry depends on .*sorryAx"

mk_project "theorem probe_stop : 1 = 2 := by" "  stop" "  rfl"
expect_findings "stop: source + envelope" "forbidden \`stop\`" "probe_stop depends on .*sorryAx"

mk_project "axiom probe_ax : False" "theorem probe_use : 1 = 2 := probe_ax.elim"
expect_findings "axiom: source + envelope" "unapproved axiom \`probe_ax\`" "probe_use depends on .*probe_ax"

mk_project "theorem probe_nd : 2 + 2 = 4 := by native_decide"
expect_findings "native_decide: source + envelope" "forbidden \`native_decide\`" "probe_nd depends on .*(Lean.ofReduceBool|_native)"

mk_project "private theorem probe_priv : 1 = 2 := by sorry"
expect_findings "private theorem is audited" "probe_priv depends on .*sorryAx"

mk_project "open Lean Elab Command in" "#eval (pure () : CommandElabM Unit)"
expect_findings "metaprogramming command rejected" "forbidden \`#eval\`"

# Kernel bypass: a metaprogram adds `theorem probe_bad : False` without a kernel check. The
# axiom envelope is blind to this (probe_uses_bad "does not depend on any axioms"), so the
# source scan AND the leanchecker replay must each reject it.
mk_project "import Lean" "open Lean Elab Command in" "run_cmd liftCoreM do" \
  "  let decl := Declaration.thmDecl { name := \`probe_bad, levelParams := [], type := mkConst \`\`False, value := mkConst \`\`True.intro }" \
  "  match (← getEnv).addDeclCore 0 0 decl none false with" \
  "  | Except.ok env' => setEnv env'" \
  "  | Except.error _ => throwError \"addDeclCore failed\"" \
  "theorem probe_uses_bad : False := probe_bad"
expect_findings "unchecked declaration: source + kernel replay" "forbidden \`run_cmd\`" "replay: leanchecker rejected MathAgents.GateProbe"

mk_project "theorem probe_admit : 1 = 2 := by admit"
expect_findings "admit: source + envelope" "forbidden \`admit\`" "probe_admit depends on .*sorryAx"

mk_project "theorem probe_native : 2 + 2 = 4 := by decide +native"
expect_findings "+native: source + envelope" "forbidden \`\+native\`" "probe_native depends on"

mk_project "theorem probe_cfg : True := trivial"
echo 'moreLeanArgs = ["-Ddebug.skipKernelTC=true"]' >> "$TMP/lean/lakefile.toml"
expect_findings "config: kernel-weakening option" "config: kernel-weakening option in lakefile.toml"

# --- MathAgentsWIP: open stubs are tolerated and reported per declaration --------------------
mk_wip "theorem probe_stub : 1 = 2 := by sorry"
gate
if [[ $rc -eq 0 ]] && grep -q "proved=[1-9][0-9]* open=1 failed=0" "$TMP/out.log"; then ok "WIP stub is open; proved theorems stay proved"
else bad "WIP stub (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -6; fi

mk_wip "open Lean Elab Command in" "#eval (pure () : CommandElabM Unit)"
expect_findings "WIP still rejects metaprogramming" "forbidden \`#eval\`"

mk_wip "axiom probe_wip_ax : False" "theorem probe_wip : 1 = 2 := probe_wip_ax.elim"
expect_findings "WIP still rejects unapproved axioms" "unapproved axiom \`probe_wip_ax\`" "probe_wip depends on .*probe_wip_ax"

mk_wip "theorem probe_stub2 : 1 = 2 := by sorry"
printf '%s\n' "import MathAgentsWIP.GateProbe" "theorem probe_leak : True := trivial" > "$TMP/lean/MathAgents/GateProbe.lean"
expect_findings "proved library may not import WIP" "proved library imports MathAgentsWIP"

mk_wip "theorem probe_stub3 : 1 = 2 := by sorry"
printf '%s\n' "import Mathlib.Tactic.NormNum MathAgentsWIP.GateProbe" "theorem probe_leak2 : True := trivial" > "$TMP/lean/MathAgents/GateProbe.lean"
expect_findings "multi-module import of WIP is caught" "proved library imports MathAgentsWIP"

mk_project "-- a comment mentioning sorry and native_decide" "theorem probe_doc : True := trivial -- \"sorry\""
gate; if [[ $rc -eq 0 ]]; then ok "comments/strings are not false positives"; else bad "comment false positive (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi

# --- Registry validator: capability claim without a source -------------------------------
mkdir -p "$TMP/reg/references/schemas" "$TMP/reg/scripts"
cp "$ROOT"/references/schemas/*.json "$TMP/reg/references/schemas/"
cp "$ROOT"/references/object-logics.json "$ROOT"/references/axiom-allowlist.json "$TMP/reg/references/"
cp "$ROOT/scripts/validate_registries.py" "$ROOT/scripts/axiom_allowlist.py" "$ROOT/scripts/instance_root.py" "$TMP/reg/scripts/"
python3 - "$ROOT/references/prover-engines.json" "$TMP/reg/references/prover-engines.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); z3 = next(e for e in d["engines"] if e["id"] == "z3")
z3["strengths"] = ["unsourced claim"]; z3["sources"] = []
json.dump(d, open(sys.argv[2], "w"))
PY
set +e; python3 "$TMP/reg/scripts/validate_registries.py" >"$TMP/out.log" 2>&1; rc=$?; set -e
if [[ $rc -eq 1 ]] && grep -q "z3: capability claim" "$TMP/out.log"; then ok "registry rejects unsourced claim"; else bad "registry unsourced claim (exit $rc)"; fi

python3 - "$ROOT/references/object-logics.json" "$TMP/reg/references/object-logics.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); d["logics"].append({"id": "probe-shallow-modal", "name": "probe", "family": "modal",
  "proof_systems": [], "semantics": [], "embedding": "shallow", "lean_module": None, "status": "planned",
  "pilot": None, "cross_checks": [], "sources": []})
json.dump(d, open(sys.argv[2], "w"))
PY
cp "$ROOT/references/prover-engines.json" "$TMP/reg/references/prover-engines.json"
set +e; python3 "$TMP/reg/scripts/validate_registries.py" >"$TMP/out.log" 2>&1; rc=$?; set -e
if [[ $rc -eq 1 ]] && grep -q "must use a deep embedding" "$TMP/out.log"; then ok "registry rejects shallow non-classical logic (D4/C3)"; else bad "shallow non-classical logic accepted (exit $rc)"; fi

# Local path dependencies are neither gated nor hashed, so the config scan forbids them.
mk_project "theorem probe_ok : True := trivial"
printf '\n[[require]]\nname = "localdep"\npath = "../localdep"\n' >> "$TMP/lean/lakefile.toml"
expect_findings "local path dependency rejected" "config: local path dependency .localdep. in lakefile.toml"

# G-CX witness binding (DD-59): a theorem of type `¬ X` reports negates_fingerprint = hash of X, so a
# witness written `¬ (type_of% @target)` binds to its target and an unrelated negation does not.
mk_wip "theorem conj : ∀ n : Nat, n * n ≠ 4 := sorry" \
  "theorem cx_1 : ¬ (type_of% @conj) := fun h => h 2 (by decide)" \
  "theorem other : ¬ (1 = 2) := by decide" \
  "def Aux.bound : Nat := 4" "def P (n : Nat) : Prop := n * n ≠ Aux.bound" "theorem main : ∀ n : Nat, P n := sorry"
set +e; python3 "$ROOT/scripts/proof_integrity.py" --lean-dir "$TMP/lean" --report "$TMP/report.json" >"$TMP/out.log" 2>&1; rc=$?; set -e
if [[ $rc -eq 0 ]] && python3 - "$TMP/report.json" <<'PY2'
import json, sys
d = {x["decl"]: x for x in json.load(open(sys.argv[1]))["declarations"]}
conj, cx, other = d["conj"], d["cx_1"], d["other"]
assert cx["negates_fingerprint"] == conj["statement_fingerprint"], (cx, conj)
assert other["negates_fingerprint"] != conj["statement_fingerprint"]
assert "negates_fingerprint" not in conj
assert d["main"]["statement_uses"] == ["Aux.bound", "P"], d["main"]["statement_uses"]  # through P's body
assert conj["statement_uses"] == []
PY2
then ok "witness negates_fingerprint binds; statement_uses follows definition bodies"; else bad "witness negates_fingerprint / statement_uses (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi

# Type rows (v0.2.1): structures and inductive types are audited, so prose can bind `[Lean: S]`; a type
# row's fingerprint covers its fields, so changing a field changes it.
type_fp() {  # type_fp FIELD_TYPE : kind and fingerprint of structure S, kind of inductive T
  mk_wip "structure S where" "  x : $1" "inductive T where | a | b" "theorem uses_s (s : S) : s = s := rfl"
  python3 "$ROOT/scripts/proof_integrity.py" --lean-dir "$TMP/lean" --report "$TMP/report.json" >"$TMP/out.log" 2>&1 || return 1
  python3 -c 'import json,sys; d={x["decl"]: x for x in json.load(open(sys.argv[1]))["declarations"]}; print(d["S"]["kind"], d["T"]["kind"], d["S"]["statement_fingerprint"], d["S"]["status"], "S" in d["uses_s"]["statement_uses"])' "$TMP/report.json"
}
set +e; t1="$(type_fp Nat)"; t2="$(type_fp Int)"; set -e
if [[ $t1 == "structure inductive "* && $t1 == *" proved True" && ${t1#* * } != "${t2#* * }" ]]; then
  ok "structure/inductive rows audited; a field change moves the structure's fingerprint"
else bad "type rows (got '$t1' / '$t2')"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi

# DD-34: a statement's fingerprint covers the bodies of the project definitions it reaches, so
# editing such a definition lapses its approval; an unrelated statement keeps its fingerprint.
fp_of() {  # fp_of BOUND : fingerprints of `main` and `plain` with `def bound : Nat := BOUND`
  mk_wip "def bound : Nat := $1" "def P (n : Nat) : Prop := n * n ≠ bound" \
    "theorem main : ∀ n : Nat, P n := sorry" "theorem plain : ∀ n : Nat, n + 0 = n := sorry"
  python3 "$ROOT/scripts/proof_integrity.py" --lean-dir "$TMP/lean" --report "$TMP/fp.json" >/dev/null 2>&1 || return 1
  python3 -c "import json,sys; d={x['decl']:x['statement_fingerprint'] for x in json.load(open('$TMP/fp.json'))['declarations']}; print(d['main'], d['plain'])"
}
if a="$(fp_of 4)" && b="$(fp_of 5)" && [[ "${a% *}" != "${b% *}" && "${a#* }" == "${b#* }" ]]; then
  ok "DD-34: editing a used definition changes the fingerprint; unrelated statements keep theirs"
else bad "DD-34 transitive fingerprint (main/plain: '$a' vs '$b')"; fi

# Compiler-generated matchers (from an anonymous-constructor pattern) get no row of their own; the
# theorem that uses one still carries its axioms.
mk_wip "theorem uses_match : (∃ n : Nat, n = n) → True := fun ⟨_, _⟩ => trivial"
set +e; python3 "$ROOT/scripts/proof_integrity.py" --lean-dir "$TMP/lean" --report "$TMP/match.json" >"$TMP/out.log" 2>&1; rc=$?; set -e
if [[ $rc -eq 0 ]] && python3 -c "import json,sys; d=[x['decl'] for x in json.load(open('$TMP/match.json'))['declarations']]; sys.exit(0 if 'uses_match' in d and not any('match_' in x for x in d) else 1)"; then
  ok "matchers are not audited as declarations"; else bad "matcher rows in the report (exit $rc)"; sed 's/^/    /' "$TMP/out.log" | tail -5; fi

echo "passed=$pass failed=$failn"
[[ $failn -eq 0 ]]
