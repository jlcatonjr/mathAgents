#!/usr/bin/env bash
# G-BLUEPRINT tests (spec "Test to build" under G-BLUEPRINT; DD-42). A \leanok node bound to an open
# WIP stub, and a \lean{} name that does not exist, must each exit 1; a node bound to a proved
# declaration must pass; a missing blueprint, kernel report or index must fail.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
C="$ROOT/scripts/check_blueprint_consistency.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT INT TERM
pass=0; failn=0
mkdir -p "$TMP/references" "$TMP/reports/kernel" "$TMP/lean/MathAgents" "$TMP/lean/MathAgentsWIP" "$TMP/blueprint/src"
cp "$ROOT/references/axiom-allowlist.json" "$TMP/references/"
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
(tmp / "reports" / "kernel" / "name-index.txt").write_text(b.header_for(lean) + " count=1\nNat.succ_le_of_lt\n")
PY
bp() { printf '%s\n' "$1" > "$TMP/blueprint/src/content.tex"; }
run() { set +e; OUT="$(python3 "$C" --root "$TMP" "$@" 2>&1)"; RC=$?; set -e; }
expect() {
  if [[ $RC -eq $2 ]] && grep -qF -- "$3" <<<"$OUT"; then echo "ok: $1"; pass=$((pass+1))
  else echo "FAIL: $1 (exit $RC)"; sed 's/^/    /' <<<"$OUT"; failn=$((failn+1)); fi
}

# --- spec cases -----------------------------------------------------------------------------
bp '\begin{lemma}\label{l:stub}\lean{MathAgents.P.stub}\leanok
A stub.
\end{lemma}'
run; expect "\\leanok node bound to an open WIP stub" 1 "is 'open' in the kernel report"
bp '\begin{theorem}\label{t:ghost}\lean{MathAgents.P.ghost}
Ghost.
\end{theorem}'
run; expect "\\lean{} name that does not exist" 1 "resolves to no declaration"
bp '\begin{theorem}\label{t:main}\lean{MathAgents.P.main}\leanok
Main.
\end{theorem}
\begin{proof}\leanok
By [Mathlib] \lean{Nat.succ_le_of_lt}.
\end{proof}'
run; expect "\\leanok node bound to a proved declaration passes" 0 "PASS"

# --- edge cases -----------------------------------------------------------------------------
bp '\begin{lemma}\label{l:open}\lean{MathAgents.P.stub}
Formalized statement, proof open: no marker.
\end{lemma}'
run; expect "open declaration without \\leanok passes" 0 "PASS"
bp '\begin{lemma}\label{l:x}\leanok
No Lean name.
\end{lemma}'
run; expect "\\leanok with no \\lean{} name" 1 "names no declaration"
bp '\begin{lemma}\label{l:c}\lean{MathAgents.P.main}
% \leanok \lean{MathAgents.P.ghost}
\end{lemma}'
run; expect "markers in LaTeX comments are ignored" 0 "PASS"
bp '\begin{lemma}\label{l:m}\lean{MathAgents.P.main, MathAgents.P.stub}\leanok
Two names, one open.
\end{lemma}'
run; expect "\\leanok with one of two names open" 1 "MathAgents.P.stub is 'open'"

# --- adversarial review round 1 ----------------------------------------------------------------
bp '\begin{theorem}\label{t:x}\lean{MathAgents.P.stub}
X.
\end{theorem}
\begin{proof}\lean{Nat.succ_le_of_lt}\leanok
Proof marked done.
\end{proof}'
run; expect "proof \\leanok certifies its open theorem" 1 "MathAgents.P.stub is 'open'"
bp '\begin{lemma}\label{l:s}\lean {MathAgents.P.ghost}
Spaced.
\end{lemma}'
run; expect "\\lean {x} with a space" 1 "resolves to no declaration"
bp '\newcommand{\done}{\leanok}
\begin{lemma}\label{l:d}\lean{MathAgents.P.stub}\done
\end{lemma}'
run; expect "macro hiding \\leanok" 1 "a macro or environment definition mentions"
bp '\begin{main-thm}\label{t:h}\lean{MathAgents.P.stub}\leanok
Hyphenated environment.
\end{main-thm}'
run; expect "hyphenated environment name is parsed" 1 "MathAgents.P.stub is 'open'"
bp '\begin{lemma}\label{l:u}\lean{MathAgents.P.stub}
See \url{http://x/a%20b} \leanok
\end{lemma}'
run; expect "a percent sign inside \\url does not hide a marker" 1 "MathAgents.P.stub is 'open'"
bp 'Loose text \leanok outside any environment.'
run; expect "\\leanok outside any environment" 1 "outside any parsed environment"
bp '\begin{theorem}\label{t:p}\lean{MathAgents.P.stub}
T.
\end{theorem}
\begin{lemma}\label{l:q}\lean{Nat.succ_le_of_lt}
L.
\end{lemma}
\begin{proof}\proves{t:p}\leanok
Proves t:p.
\end{proof}'
run; expect "\\proves{label} binds the proof to that statement" 1 "MathAgents.P.stub is 'open'"
bp '\begin{proof}\proves{t:nowhere}\leanok
\end{proof}'
run; expect "\\proves an unknown label" 1 "names no labelled statement"
bp '\begin{theorem}\label{t:r}\lean{MathAgents.P.stub}
T.
\end{theorem}
\begin{remark}
An aside.
\end{remark}
\begin{proof}\lean{Nat.succ_le_of_lt}\leanok
\end{proof}'
run; expect "a remark between statement and proof does not detach the proof" 1 "MathAgents.P.stub is 'open'"
bp '\NewDocumentCommand{\done}{}
  {\leanok}
\begin{lemma}\lean{MathAgents.P.main}\end{lemma}'
run; expect "multi-line \\NewDocumentCommand hiding \\leanok" 1 "definition mentions"
printf '%s\n' '\newenvironment{done}{\leanok}{}' > "$TMP/blueprint/src/macros.sty"
bp '\begin{lemma}\lean{MathAgents.P.main}\end{lemma}'
run; expect "macro in a .sty file" 1 "macros.sty"
rm "$TMP/blueprint/src/macros.sty"
bp '\begin{theorem}\label{a}\lean{MathAgents.P.main}
A.
\end{theorem}
\begin{thm}\label{b}\lean{MathAgents.P.stub}
Custom node type.
\end{thm}
\begin{proof}\leanok
\end{proof}'
run; expect "a proof after a custom theorem environment binds to it" 1 "MathAgents.P.stub is 'open'"
bp '\begin{lemma}\lean{MathAgents.P.stub}\csname leanok\endcsname
\end{lemma}'
run; expect "\\csname leanok\\endcsname" 1 "other than as a literal"
bp '\begin{lemma}\label{d}\lean{MathAgents.P.main}
\end{lemma}
\begin{lemma}\label{d}\lean{MathAgents.P.main}
\end{lemma}'
run; expect "duplicate labels" 1 "defined more than once"
mkdir -p "$TMP/lean/blueprint/src"; printf '%s\n' '\begin{lemma}\label{l:lb}\lean{MathAgents.P.ghost}
\end{lemma}' > "$TMP/lean/blueprint/src/content.tex"
run; expect "lean/blueprint is the default location" 1 "lean/blueprint/src/content.tex"
rm -rf "$TMP/lean/blueprint"

# --- fails closed ---------------------------------------------------------------------------
run --blueprint "$TMP/no-such-blueprint"; expect "missing blueprint" 1 "no blueprint"
mv "$TMP/reports/kernel/latest.json" "$TMP/latest.bak"
run; expect "missing kernel report" 1 "no kernel report"
mv "$TMP/latest.bak" "$TMP/reports/kernel/latest.json"
rm "$TMP/reports/kernel/name-index.txt"
run; expect "missing name index" 1 "no name index"

echo "passed=$pass failed=$failn"
[[ $failn -eq 0 ]]
