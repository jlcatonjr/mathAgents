# P3 — Dutch book theorem and its converse, finite case (Stage 8 assembly)

Result status: proved

All three statements were checked by the Lean kernel and approved by the operator at G-FID. None is
fidelity-waived. The frozen record is in `kernel-snapshot.json` (commit `e760f696`, clean tree). The
axiom envelope is `propext`, `Classical.choice` and `Quot.sound`, with no `sorry`, no added axioms and
no `native_decide`.

| Reading | Lean declaration | Approved at G-FID |
|---|---|---|
| R1 (not a finitely additive probability ⇒ a Dutch book exists) | `MathAgents.P3DutchBook.dutchBook_R1` | yes |
| R2 (finitely additive probability ⇒ no Dutch book) | `MathAgents.P3DutchBook.converse_R2` | yes |
| R3 (a Dutch book exists ⇔ not a finitely additive probability) | `MathAgents.P3DutchBook.dutchBook_R3` | yes |

**Scope.** The setting is finite Ω, finite books, stakes of either sign, and strict sure loss (P3-6).
R2 is false under weak sure loss. R4 and R5 are deferred. Kemeny 1955 and Lehman 1955 were not
consulted (D29). `dutchBook_R1` carries `[Fintype Ω]` although its proof does not use it; the
approved statement is kept as is. The supporting library `MathAgents.FiniteProbability` sits outside this dossier's namespace, so it is not
in the snapshot; its declarations are proved in the G-KERNEL report at the same commit. The G-AX choices are recorded in `preferences.toml`.

## Artifacts, by stage

- Stage 0: `problem-card.md`, `interpretation.md`, `preferences.toml`, `sources/`
- Stage 1: `statement.md`, `back-translation.md`, `stage1-audit.md`, `fidelity.json`
- Stage 2: `strategy.md`, `strategy-review.md`
- Stage 3: `derivations.md`
- Stage 4: `tactic-plan.md`
- Stage 6: `stage6-search.md` (no counterexamples found)
- Stage 7: `informalization.md`
- Stage 8: `kernel-snapshot.json`, this file
