#!/usr/bin/env bash
# Preferences tests (decision D32): the project and dossier preference files are checked; the problem
# card must agree with the settings in force; `kernel_as_judge = never` rejects waiver records; a
# dossier setting overrides the project default.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"  # sedi
subfirst() {  # subfirst FILE REGEX REPLACEMENT: replace the first match only (GNU sed's 0,/re/ form)
  python3 -c 'import re,sys; p,pat,rep=sys.argv[1:]; t=open(p).read(); open(p,"w").write(re.sub(pat, lambda m: rep, t, count=1, flags=re.M))' "$1" "$2" "$3"
}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
P="$ROOT/scripts/preferences.py"; V="$ROOT/scripts/validate_dossier.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT INT TERM
pass=0; failn=0
expect() {
  if [[ $RC -eq $2 ]] && grep -qF -- "$3" <<<"$OUT"; then echo "ok: $1"; pass=$((pass+1))
  else echo "FAIL: $1 (exit $RC)"; sed 's/^/    /' <<<"$OUT"; failn=$((failn+1)); fi
}
prun() { set +e; OUT="$(python3 "$P" --root "$TMP" "$@" 2>&1)"; RC=$?; set -e; }
vrun() { set +e; OUT="$(python3 "$V" --root "$TMP" "$@" 2>&1)"; RC=$?; set -e; }

# the real repository's files
set +e; OUT="$(python3 "$P" check 2>&1)"; RC=$?; set -e
expect "repository preferences are well formed" 0 "preferences: PASS"

# fixture: registries, charter, the real project defaults, one dossier with a brief
mkdir -p "$TMP/references/schemas" "$TMP/docs/charter" "$TMP/reports/dossiers/demo" "$TMP/reports/kernel" "$TMP/lean"
cp "$ROOT"/references/schemas/*.json "$TMP/references/schemas/"
cp "$ROOT/references/object-logics.json" "$ROOT/references/prover-engines.json" "$ROOT/references/axiom-allowlist.json" \
   "$ROOT/references/preferences.toml" "$TMP/references/"
cp "$(python3 -c 'import sys, pathlib; sys.path.insert(0, sys.argv[1]); import instance_root; print(instance_root.charter_path(pathlib.Path(sys.argv[2])))' "$ROOT/scripts" "$ROOT")" "$TMP/docs/charter/"
D="$TMP/reports/dossiers/demo"
printf '# Brief\n\n### R1. One\n\n### R2. Two\n\nG-AX-P9-1 and G-AX-P9-2 are candidates.\n' > "$D/interpretation.md"
prefs() {  # prefs [logic] [kernel_as_judge] [extra]
  cat > "$D/preferences.toml" <<EOF
schema_version = 1
slug = "demo"
[readings.selected]
choice = ["R1", "R2:variant"]
alternatives = []
decision = "D30"
[intake.object_logic]
choice = "${1:-classical-hol}"
alternatives = ["finite-probability"]
decision = "D31"
[intake.engines]
choice = ["lean-builtin", "z3"]
alternatives = [["lean-builtin"]]
decision = "D31"
[intake.domain]
choice = "research-math"
alternatives = []
decision = "D2"
[fidelity.kernel_as_judge]
choice = "${2:-never}"
alternatives = ["offer"]
decision = "D31"
[gax."P9-1"]
choice = "a"
alternatives = ["b"]
decision = "D31"
${3:-}
EOF
}
card() {  # card [logic] [engines] [reading]
  printf '# Problem card\n\n- **Source:** test\n- **Informal statement:** test\n- **Domain:** research-math\n- **Object logic:** %s\n- **Engine:** %s\n- **Reading:** %s\n' \
    "${1:-classical-hol}" "${2:-lean-builtin, z3}" "${3:-R1, R2:variant}" > "$D/problem-card.md"
}

prefs; prun check; expect "well-formed dossier preferences" 0 "PASS"
prefs "intuitionistic-x"; prun check; expect "object logic not in the registry" 1 "not an id in references/object-logics.json"
prefs; sedi 's/choice = \["R1", "R2:variant"\]/choice = ["R1", "R7"]/' "$D/preferences.toml"
prun check; expect "reading not in the brief" 1 "'R7' is not a reading"
prefs "" "sometimes"; prun check; expect "closed-vocabulary setting with an unknown value" 1 "'sometimes' is not one of"
prefs "" "never" '[gax."P9-9"]
choice = "x"
alternatives = []
decision = "D31"'
prun check; expect "G-AX choice for a candidate the brief lacks" 1 "G-AX-P9-9 is not a candidate"
prefs; sedi 's/alternatives = \["finite-probability"\]/alternatives = ["classical-hol"]/' "$D/preferences.toml"
prun check; expect "choice repeated among its alternatives" 1 "also listed among its alternatives"
prefs; sedi 's/decision = "D2"/decision = "D999"/' "$D/preferences.toml"
prun check; expect "decision that is not a charter row" 1 "D999"
prefs; sedi 's/slug = "demo"/slug = "other"/' "$D/preferences.toml"
prun check; expect "slug mismatch" 1 "does not match its directory"
prefs; printf '\n[intake.default_engines]\nchoice = ["lean-builtin"]\nalternatives = []\ndecision = "D6"\n' >> "$D/preferences.toml"
prun check; expect "project-only default in a dossier file" 1 "a project-only default in a dossier file"
cp "$TMP/references/preferences.toml" "$TMP/proj.bak"
printf '\n[gax."P9-1"]\nchoice = "a"\nalternatives = []\ndecision = "D31"\n' >> "$TMP/references/preferences.toml"
prefs; prun check; expect "dossier-only setting in the project file" 1 "a dossier-only setting in the project file"
cp "$TMP/proj.bak" "$TMP/references/preferences.toml"

# the settings in force, and their source
prefs; prun show demo
expect "a dossier setting overrides the project default" 0 '"never"'
grep -A1 '^fidelity.kernel_as_judge' <<<"$OUT" | grep -q 'enforced\] from reports/dossiers/demo/preferences.toml' \
  && { echo "ok: show names the dossier file as the source"; pass=$((pass+1)); } || { echo "FAIL: show source"; failn=$((failn+1)); }
grep -A1 '^sources.translation' <<<"$OUT" | grep -q 'advisory\] from references/preferences.toml' \
  && { echo "ok: an unset setting comes from the project file"; pass=$((pass+1)); } || { echo "FAIL: show default source"; failn=$((failn+1)); }

# the problem card must agree with the preferences
prefs; card; vrun demo; expect "card agreeing with the preferences" 0 "PASS"
card "classical-hol" "lean-builtin"; vrun demo; expect "card engines disagree with the preferences" 1 "disagrees with intake.engines"
card "classical-hol" "lean-builtin, z3" "R1"; vrun demo; expect "card readings disagree with the preferences" 1 "disagrees with readings.selected"
prefs "finite-probability"; card; vrun demo; expect "card logic disagrees after the preference changed" 1 "disagrees with intake.object_logic"

# kernel_as_judge = never rejects waiver records
prefs; card
printf '{"schema_version":1,"slug":"demo","records":[{"id":"AX-1","decl":"X.y","old_fingerprint":"1","new_fingerprint":"2","change":"other","description":"d","waiver":{"conversation":"c","date":"2026-10-01"}}]}\n' > "$D/gax.json"
vrun demo; expect "waiver record while kernel_as_judge = never" 1 "kernel_as_judge = 'never'"
prefs "" "offer"; vrun demo
grep -q "kernel_as_judge = 'never'" <<<"$OUT" && { echo "FAIL: waiver flagged under offer"; failn=$((failn+1)); } \
  || { echo "ok: the same waiver is not a preferences finding under 'offer'"; pass=$((pass+1)); }
rm "$D/gax.json"

# --- adversarial review round 1 ----------------------------------------------------------------
prefs; sedi 's/\[fidelity.kernel_as_judge\]/[fidelity.kernel_as_jugde]/' "$D/preferences.toml"
prun check; expect "misspelled setting name" 1 "an unknown setting (check its spelling)"
prefs; subfirst "$D/preferences.toml" '^choice = "never"' 'chioce = "never"'
prun check; expect "misspelled field name" 1 "must have exactly choice, alternatives and decision"
prefs; subfirst "$D/preferences.toml" '^slug = "demo"' $'slug = "demo"\nowner = "x"'
prun check; expect "unknown top-level key" 1 "unknown top-level key 'owner'"
prefs; subfirst "$D/preferences.toml" '^alternatives = \[\]' 'alternatives = ["R1"]'
prun check; expect "selected reading also listed as an alternative" 1 "also listed among its alternatives"
prun show nosuch; expect "show for an unknown dossier" 1 "no dossier 'nosuch'"

# kernel_as_judge = never also covers D26's in-session G-AX allowlist approvals
prefs; card
cp "$TMP/references/axiom-allowlist.json" "$TMP/allow.bak"
printf '{"note":"t","base_axioms":["propext","Classical.choice","Quot.sound"],"approved_axioms":["X.ax"],"approvals":[{"axiom":"X.ax","approver":"operator","date":"2026-10-01","reason":"r","dossier":"demo","conversation":"conv-7"}]}\n' > "$TMP/references/axiom-allowlist.json"
vrun demo; expect "in-session allowlist approval while kernel_as_judge = never" 1 "given by in-session directive"
cp "$TMP/allow.bak" "$TMP/references/axiom-allowlist.json"

# the fidelity record is bound to the problem card it was approved against
prefs; card
SHA="$(python3 "$P" --root "$TMP" digest demo)"
printf '{"schema_version":1,"slug":"demo","lean_namespace":"X","declarations":[{"decl":"X.y","statement_fingerprint":"1","status":"approved","approver":"o","date":"2026-10-01"}]}\n' > "$D/fidelity.json"
vrun demo; expect "approval without the intake hash" 1 "does not record intake_sha256"
printf '{"schema_version":1,"slug":"demo","lean_namespace":"X","intake_sha256":"%s","declarations":[{"decl":"X.y","statement_fingerprint":"1","status":"approved","approver":"o","date":"2026-10-01"}]}\n' "$SHA" > "$D/fidelity.json"
vrun demo; grep -q "intake_sha256\|different problem card" <<<"$OUT" \
  && { echo "FAIL: matching card hash flagged"; failn=$((failn+1)); } || { echo "ok: approval bound to the current card"; pass=$((pass+1)); }
card "classical-hol" "lean-builtin, z3" "R1, R2:variant"; printf '\n- **Note:** edited after approval\n' >> "$D/problem-card.md"
vrun demo; expect "card edited after approval lapses it" 1 "approved against a different problem card"
card; vrun demo; grep -q "different problem card" <<<"$OUT" && { echo "FAIL: restored card still lapsed"; failn=$((failn+1)); } \
  || { echo "ok: restoring the card restores the binding"; pass=$((pass+1)); }
sedi 's/choice = "a"/choice = "b"/; s/alternatives = \["b"\]/alternatives = ["a"]/' "$D/preferences.toml"
vrun demo; expect "an advisory G-AX answer changed after approval lapses it" 1 "different problem card or preferences"
rm "$D/fidelity.json"
prefs; printf '{"note":"t","base_axioms":["propext","Classical.choice","Quot.sound"],"approved_axioms":["X.ax"],"approvals":[{"axiom":"X.ax","who":"operator (in-session directive)","date":"2026-10-01","reason":"r","dossier":"demo"}]}\n' > "$TMP/references/axiom-allowlist.json"
set +e; OUT="$(cd "$TMP" && mkdir -p scripts && cp "$ROOT/scripts/axiom_allowlist.py" "$ROOT/scripts/validate_registries.py" "$ROOT/scripts/instance_root.py" scripts/ && python3 scripts/validate_registries.py 2>&1)"; RC=$?; set -e
expect "allowlist record with off-schema fields fails the registry" 1 "needs \`conversation\`"
cp "$TMP/allow.bak" "$TMP/references/axiom-allowlist.json"
sedi '/^\[fidelity.kernel_as_judge\]/,/^decision/d' "$TMP/references/preferences.toml"
prun check; expect "a required project setting deleted" 1 "a required project setting is missing"
cp "$ROOT/references/preferences.toml" "$TMP/references/preferences.toml"

# a project default never constrains a dossier that sets nothing
mkdir -p "$TMP/reports/dossiers/plain"
printf '# Problem card\n\n- **Source:** t\n- **Informal statement:** t\n- **Domain:** research-math\n- **Object logic:** classical-hol\n- **Engine:** lean-builtin, z3\n' > "$TMP/reports/dossiers/plain/problem-card.md"
echo "stmt" > "$TMP/reports/dossiers/plain/statement.md"
vrun plain; grep -q "disagrees with intake" <<<"$OUT" && { echo "FAIL: default acted as a requirement"; failn=$((failn+1)); } \
  || { echo "ok: intake defaults do not constrain a card"; pass=$((pass+1)); }
mv "$TMP/references/preferences.toml" "$TMP/proj.bak2"
vrun demo; expect "missing project preferences fails closed" 2 "references/preferences.toml is missing"
mv "$TMP/proj.bak2" "$TMP/references/preferences.toml"

# --- intake commands: readings, new, set --------------------------------------------------------
prun readings demo; expect "readings lists the brief's readings" 0 "R2"
mkdir -p "$TMP/reports/dossiers/fresh"; printf '# Brief\n\n### R1. Only\n\n### R2. Other\n' > "$TMP/reports/dossiers/fresh/interpretation.md"
prun new fresh --domain research-math --readings R1; expect "new writes preferences and a card skeleton" 0 "wrote reports/dossiers/fresh"
grep -q '^choice = \["R1"\]' "$TMP/reports/dossiers/fresh/preferences.toml" && grep -q 'Reading:\*\* R1' "$TMP/reports/dossiers/fresh/problem-card.md" \
  && { echo "ok: new records the chosen reading in both files"; pass=$((pass+1)); } || { echo "FAIL: new contents"; failn=$((failn+1)); }
prun new fresh --domain research-math; expect "new never overwrites" 1 "already exists"
prun set fresh readings.selected '["R2"]'; expect "set changes a choice" 0 'readings.selected = ["R2"]'
grep -A2 '^\[readings.selected\]' "$TMP/reports/dossiers/fresh/preferences.toml" | grep -q 'alternatives = \["R1"\]' \
  && { echo "ok: set on readings lists the other readings as alternatives"; pass=$((pass+1)); } || { echo "FAIL: set alternatives"; sed -n '/readings.selected/,+3p' "$TMP/reports/dossiers/fresh/preferences.toml"; failn=$((failn+1)); }
cp "$TMP/reports/dossiers/fresh/preferences.toml" "$TMP/fresh.bak"
prun set fresh intake.object_logic '"no-such-logic"'; expect "set rejects an invalid value" 1 "rejected, file restored"
cmp -s "$TMP/fresh.bak" "$TMP/reports/dossiers/fresh/preferences.toml" && { echo "ok: a rejected set restores the file"; pass=$((pass+1)); } \
  || { echo "FAIL: file not restored"; failn=$((failn+1)); }
prun set project fidelity.kernel_as_judge never; expect "set refuses an operator setting without a terminal" 1 "records an operator decision"
prun set project gax.P9-1 '"b"'; expect "set refuses a G-AX answer without a terminal" 1 "records an operator decision"
if command -v script >/dev/null; then  # the operator's path: an interactive terminal (`script` allocates a pty)
  CMD="python3 '$P' --root '$TMP' set project fidelity.kernel_as_judge never"
  set +e
  if script -qec true /dev/null >/dev/null 2>&1; then OUT="$(script -qec "$CMD" /dev/null 2>&1)"  # util-linux
  else OUT="$(script -q /dev/null sh -c "$CMD" 2>&1)"; fi  # BSD (macOS)
  RC=$?; set -e
  expect "set works on the project file from a terminal" 0 'fidelity.kernel_as_judge = "never" in project'
fi
prun set project no.such.key x; expect "set on an unknown key" 1 "no such setting"

echo "passed=$pass failed=$failn"
[[ $failn -eq 0 ]]
