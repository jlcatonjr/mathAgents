# G-KERNEL — the proof-integrity gate

`bash scripts/check_proof_integrity.sh` (implemented in `scripts/proof_integrity.py`) decides,
**per declaration**, whether a Lean result may be called **proved**.

## Exit codes

- **0**: the library verdict is PASS (no findings).
- **1**: FAIL, with at least one finding. A tool that fails to run is also recorded as a finding
  and exits 1: `lake build`, `leanchecker`, or the axiom audit.
- **2**: FAIL, the gate itself raised an unexpected error. Any previous report is deleted at the start of every run, so a crash can never leave a stale PASS behind.

Every non-zero exit is a failure.

## Two libraries

The library names come from the `lean_lib` entries in `lean/lakefile.toml`, which is the single
source of truth. The gate fails closed unless it finds exactly one proved library and one library
whose name ends in `WIP`.

| Library | Purpose | `sorry` / `admit` / `stop` |
|---|---|---|
| `lean/MathAgents` | The proved library. Dossiers cite only declarations here. | Forbidden (finding) |
| `lean/MathAgentsWIP` | Open work: theorem stubs from pipeline Stage 1 (`:= sorry`) and partial proofs | Tolerated as *open markers*, listed in the report |

In `MathAgentsWIP`, every other check stays fatal: metaprogramming, unapproved axioms,
`native_decide`, config, and kernel replay. `MathAgents` may never import `MathAgentsWIP`, so an
open result cannot leak into a proved one. When a WIP result is finished, it moves into
`MathAgents`.

## Per-declaration status

Every theorem, def, opaque, structure and inductive type in either library (private ones included;
type rows from mathagents 0.2.1) is reported with one status:

- **`proved`**:
  - it lives in `MathAgents`, or in a WIP module that has no findings;
  - its axioms ⊆ `{propext, Classical.choice, Quot.sound}` plus G-AX approvals;
  - and its module has no source or replay finding.
- **`open`**: it lives in `MathAgentsWIP`, and the only axiom beyond the envelope is `sorryAx`.
- **`failed`**: anything else.

An open stub therefore does not change the status of any proved theorem. A result may be called
proved only when its declaration's status is `proved`. The library verdict (the exit code) is
PASS only when there are no findings at all.

## Layers

| # | Layer | Catches |
|---|---|---|
| 0 | Toolchain | The Lean that runs in `lean/` (`lean --version`) is not the release `lean-toolchain` pins, e.g. under an `ELAN_TOOLCHAIN` override. Layers 3-5 are then skipped, so nothing is built under the wrong toolchain (`docs/lean-version-governance.md`, R5) |
| 1 | Config scan | Kernel-weakening options (`debug.*`, `skipKernelTC`) in `lakefile.*` / `lean-toolchain`; the lakefile's Mathlib `rev` differing from the manifest's `inputRev` (P2); after a successful build, a `.lake` Mathlib checkout built for another toolchain (P4) |
| 2 | Source scan (comment- and string-aware) | `sorry`, `admit`, `stop` (outside WIP), `native_decide`, `+native`, `unsafe`, `implemented_by`, `extern`; metaprogramming commands (`run_cmd`, `#eval`, `elab`, `initialize`, …); `axiom` declarations not approved by fully-qualified name; `MathAgents` importing `MathAgentsWIP` |
| 3 | `lake build` | Elaboration or kernel errors; ``declaration uses `sorry` `` outside WIP (both the older and the Lean 4.34 wording) |
| 4 | `leanchecker` replay | Declarations added to the environment without a kernel check |
| 5 | Axiom envelope | Any dependency beyond the envelope. `sorryAx` (outside WIP), `Lean.ofReduceBool`, `Lean.trustCompiler`, and the auxiliary axioms that `native_decide` mints in Lean 4.34 (`<decl>._native.native_decide.ax_*`) always fail. The audit must also cover at least as many theorems as the source declares. |

The envelope alone is blind to declarations added without a kernel check: such a declaration can
"prove" `False` with no axioms. That is why layers 2 and 4 exist, and they are tested against
exactly that probe.

## Tests

`scripts/tests/test_mathagents_gates.sh` seeds defects into a throwaway copy of the project. It
requires **every** relevant layer to report each one, matched by finding text, so a regression in
one layer cannot hide behind another. Covered cases:

- **Must PASS:** a clean probe; comments and strings that mention forbidden tokens.
- **Single-layer or multi-layer rejections:**
  - `sorry`: source, build and envelope
  - `stop`, `admit`, `native_decide`, `+native`, an unapproved `axiom`: source and envelope
  - private theorems: envelope
  - `#eval`: source
  - an unchecked `False` declaration: source and kernel replay
  - a kernel-weakening lakefile option: config
- **WIP behaviour:**
  - an open stub is reported as `open` while proved theorems stay `proved`;
  - metaprogramming and unapproved axioms are still rejected in WIP;
  - a proved-library import of WIP is rejected.
- **Registry:** an unsourced capability claim is rejected.

`unsafe`, `implemented_by` and `extern` are covered only by the source-scan token list. They do
not yet have a dedicated probe.

## Report

`reports/kernel/latest.json` is per-run and gitignored; dossiers snapshot their own copy. It
records:
- the verdict, findings and open markers;
- provenance: the commit, a dirty flag for `lean/`, a SHA-256 of the sources (with the toolchain,
  lakefile and manifest), the version string of the Lean binary that ran (which must name the release
  in `toolchain_pin`: every consumer of the report refuses one where they disagree), and the axiom allowlist
  used (`allowlist`: its path and SHA-256). Consumers reject a report made with any allowlist other
  than the committed `references/axiom-allowlist.json`;
- for each declaration: its status, the axioms it depends on, and a `statement_fingerprint`: a hash
  of its type combined with the type and, for definitions, the body of every project constant the
  statement reaches (DD-34);
- for each theorem of type `¬ X` (or `X → False`): a `negates_fingerprint`, the hash of `X`. G-CX
  uses it to bind a counterexample witness, written `theorem cx_<n> : ¬ (type_of% @<target>)`, to
  exactly its target (for a target revised since logging, the logged statement is written out in
  full instead of `type_of%`);
- for each declaration: `statement_uses`, the project constants its type reaches, followed through
  project definition bodies. G-FID rejects an approved statement that reaches an `Aux.` or `CX.`
  helper: those namespaces are exempt from fidelity coverage and editable by the prover.

## What the gate does not establish

A `proved` status means the kernel accepted the proof. It does **not** mean the formal statement
says what was intended. That is the G-FID human gate. A G-FID approval is recorded against the
declaration's `statement_fingerprint`. If the statement changes, the fingerprint changes and the
approval lapses.

Because the fingerprint also covers the project definitions a statement reaches (DD-34), editing
such a definition lapses the approval too. **Limits:** fingerprints stop at the Mathlib boundary (a
Mathlib bump leaves approvals standing); a `partial def` is opaque to the kernel, so editing its body
changes nothing; and the hashes detect change, not adversarial collisions.

## Axiom approvals (G-AX)

`references/axiom-allowlist.json` is the single home of the envelope (DD-38): `base_axioms` (Lean's
three standard axioms; a widened base is refused) and `approved_axioms` by fully-qualified name, each
needing a complete record (`axiom`, `approver`, `date`, `reason`, `dossier`). G-KERNEL and
`scripts/validate_registries.py` load it through `scripts/axiom_allowlist.py`, so both reject a
missing or incomplete record. Adding an approval is a human decision, never an agent's, with
one exception: when the operator explicitly extends the kernel-as-judge override to G-AX within a
session (D26, spec DD-30), the agent records each approval with the operator as approver.
