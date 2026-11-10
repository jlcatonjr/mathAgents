# P2 — Lewis's triviality result (Stage 8 assembly)

Result status: proved

All three statements were checked by the Lean kernel and approved by the operator at G-FID. None is
fidelity-waived. The frozen record is in `kernel-snapshot.json` (commit `e760f696`, clean tree). The
axiom envelope is `propext`, `Classical.choice` and `Quot.sound`, with no `sorry`, no added axioms and
no `native_decide`.

| Reading | Lean declaration | Approved at G-FID |
|---|---|---|
| R2 (Factorization instances ⇒ Pr(A>C) = Pr(C)) | `MathAgents.P2LewisTriviality.triviality_R2` | yes |
| R3:all (Stalnaker's Hypothesis for every finitely additive Pr) | `MathAgents.P2LewisTriviality.triviality_R3_all` | yes |
| R3:closed (Stalnaker's Hypothesis on a class closed under conditioning) | `MathAgents.P2LewisTriviality.triviality_R3_closed` | yes |

**Scope.** The statement of record is the SEP presentation, because Lewis 1976 was inaccessible (D29).
Fidelity to Lewis's own wording is not established. The auditors argue on paper, without a formal proof, that R3:all
has content only on small algebras (see `stage1-audit.md`). The G-AX choices are recorded in `preferences.toml`.

## Artifacts, by stage

- Stage 0: `problem-card.md`, `interpretation.md`, `preferences.toml`
- Stage 1: `statement.md`, `back-translation.md`, `stage1-audit.md`, `fidelity.json`
- Stage 2: `strategy.md`, `strategy-review.md`
- Stage 3: `derivations.md`
- Stage 4: `tactic-plan.md`
- Stage 6: `stage6-search.md` (no counterexamples found)
- Stage 7: `informalization.md`
- Stage 8: `kernel-snapshot.json`, this file
