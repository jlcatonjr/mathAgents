# P2 Lewis triviality: informalization (Stage 7)

> **Produced by:** `@lean-informalization` · 2026-10-01
> **Target reader:** working mathematicians and philosophers of science familiar with probability on Boolean algebras and with the probabilities-of-conditionals literature. Statement-level narration only; no proof internals.
> **Source of truth:** `lean/MathAgents/P2LewisTriviality.lean`, namespace `MathAgents.P2LewisTriviality`. Statuses and axioms are from the G-KERNEL report `reports/kernel/latest.json` (verdict PASS, checked 2026-10-01T22:34:15Z, commit `6fdbd26`, `dirty: false`), frozen in `kernel-snapshot.json`.
> **Statement of record (D29, flagged):** the SEP version of Lewis's Triviality Theorem in Egré and Rott 2026, as quoted in `problem-card.md` and `statement.md` §0. Lewis 1976 is paywalled and was not consulted.

## 1. Setting and notation

Throughout, `α` is an arbitrary type carrying a Boolean algebra structure (Mathlib's `BooleanAlgebra`): its elements are the propositions, with `⊓` read as conjunction, `⊔` as disjunction, `ᶜ` as negation, `⊤` as the tautology, and `Disjoint a b` meaning `a ⊓ b = ⊥`. The conditional `>` is a function `cond : α → α → α`, with `cond A C` read as `A > C`. No property of `cond` is assumed; because its values lie in `α`, conditionals may be nested and conditioned on. The module header attributes this choice to the object logic `classical-hol` and G-AX-P2-3 ("the conditional `>` is an uninterpreted binary operation `cond` on a Boolean algebra `α`, which is therefore closed under it"; module docstring of `P2LewisTriviality.lean`).

Because propositions are algebra elements rather than sentences, `cond` and any `P` automatically respect logical equivalence. The source does not state this; the operator accepted it (G-AX-P2-17, `boolean-algebra`), and the proofs do not need it beyond the algebra's own laws.

## 2. Definitions

**Finitely additive probability.** For `P : α → ℝ`, `IsFinAddProb P` holds when `0 ≤ P a` for every `a`, `P a ≤ 1` for every `a`, `P ⊤ = 1`, and `P (a ⊔ b) = P a + P b` whenever `a` and `b` are disjoint. No σ-additivity and no finiteness of `α` are assumed. [Lean: MathAgents.P2LewisTriviality.IsFinAddProb | proved]
Docstring: "G-AX-P2-1: `P` is a finitely additive probability function on the Boolean algebra `α`."

**Conditional probability.** `condProb P C A` is the ratio `P (A ⊓ C) / P A`, read `Pr(C | A)`. In Lean `x / 0 = 0`, but every use in the statements below is guarded by a positivity hypothesis. [Lean: MathAgents.P2LewisTriviality.condProb | proved]
Docstring: "G-AX-P2-2: `condProb P C A` is `Pr(C | A) = Pr(A ∧ C) / Pr(A)`; used only when `Pr(A) > 0`."

**One instance of Factorization.** `FactorizationAt cond P A B C` is the implication: if `0 < P (A ⊓ B)`, then `condProb P (cond B C) A = condProb P C (A ⊓ B)`, that is, `Pr(B > C | A) = Pr(C | A ∧ B)`. [Lean: MathAgents.P2LewisTriviality.FactorizationAt | proved]
Docstring: "One instance of the Factorization Hypothesis, with its proviso."

**Stalnaker's Hypothesis for one function.** `StalnakerHyp cond P` says: for all `A, C ∈ α` with `0 < P A`, `P (cond A C) = condProb P C A`. Both `A` and `C` range over all of `α`, conditionals included (G-AX-P2-15, `all-A-C`, reading the SEP's "every conditional A>C, possibly complex"). [Lean: MathAgents.P2LewisTriviality.StalnakerHyp | proved]

**Closure under conditioning.** For a set `K` of functions `α → ℝ`, `ClosedUnderConditioning K` says: for every `P ∈ K` and every `B` with `0 < P B`, the function `X ↦ condProb P X B` belongs to `K` (G-AX-P2-6, `conditioning-on-positive-events`). [Lean: MathAgents.P2LewisTriviality.ClosedUnderConditioning | proved]

(The kernel report lists these definitions with status `proved` and the axiom set below; for a definition this just means it elaborates and depends on no `sorry`.)

## 3. Main results

All three theorems are universally quantified over the type `α`, its Boolean algebra structure, and `cond`.

### 3.1 Reading R2: Factorization as a hypothesis on one fixed probability function

**Theorem.** Let `P : α → ℝ` satisfy `IsFinAddProb P`, and let `A, C ∈ α`. Assume
(F₁) the Factorization instance `FactorizationAt cond P C A C`, i.e. if `0 < P (C ⊓ A)` then `Pr(A > C | C) = Pr(C | C ∧ A)`;
(F₂) the Factorization instance `FactorizationAt cond P Cᶜ A C`, i.e. if `0 < P (Cᶜ ⊓ A)` then `Pr(A > C | ¬C) = Pr(C | ¬C ∧ A)`;
and `0 < P (A ⊓ C)` and `0 < P (A ⊓ Cᶜ)`. Then `P (cond A C) = P C`. [Lean: MathAgents.P2LewisTriviality.triviality_R2 | proved]

Only these two instances of Factorization are assumed, and only for the one `P` in the statement (G-AX-P2-12 `one-fixed-Pr`; G-AX-P2-13 `two-instances`). Per `statement.md` §2, these are the two instances used in the SEP's displayed proof. This is a weaker hypothesis than the SEP's Factorization "for every probability function … for all sentences A and B", so the theorem is stronger than the corresponding statement with the full schema. Stalnaker's Hypothesis is not assumed.

### 3.2 Reading R3:all: Stalnaker's Hypothesis for every probability function

**Theorem.** Suppose that every `P : α → ℝ` with `IsFinAddProb P` satisfies `StalnakerHyp cond P`. Then for every `P` with `IsFinAddProb P` and all `A, C ∈ α` with `0 < P (A ⊓ C)` and `0 < P (A ⊓ Cᶜ)`, `P (cond A C) = P C`. [Lean: MathAgents.P2LewisTriviality.triviality_R3_all | proved]
Docstring: "Reading R3:all: Stalnaker's Hypothesis holds for every finitely additive `Pr` on `α`."

"Every probability function" ranges over the finitely additive functions on the one fixed algebra `α` with the one fixed `cond`; algebras are not varied (G-AX-P2-7, `fixed-algebra`). The hypothesis is Stalnaker's Hypothesis alone; Factorization is not assumed but derived (G-AX-P2-14, `stalnaker-only`), so the hypothesis set differs from the SEP's displayed derivation from Factorization.

**Near-vacuity.** The Stage 1 audits (`statement.md` §5 notes; `stage1-audit.md` item 2; `back-translation.md`, R3:all drift item 4) report that on any algebra with three pairwise disjoint non-zero elements some finitely additive `P` violates Stalnaker's Hypothesis, so the hypothesis of this theorem can hold only on very small algebras (at most four elements). This argument is the auditors', on paper, and is **not** formalized here; the back-translation calls it an "unverified inference". If it is right, R3:all is true but nearly vacuous, and its conclusion `Pr(A>C) = Pr(C)` understates the triviality phenomenon. The corollary `condProb P C A = P C` was not formalized (G-AX-P2-18, `not-now`).

### 3.3 Reading R3:closed-under-conditioning

**Theorem.** Let `K` be a set of functions `α → ℝ` such that every member satisfies `IsFinAddProb`, `K` satisfies `ClosedUnderConditioning`, and every `P ∈ K` satisfies `StalnakerHyp cond P`. Then for every `P ∈ K` and all `A, C ∈ α` with `0 < P (A ⊓ C)` and `0 < P (A ⊓ Cᶜ)`, `P (cond A C) = P C`. [Lean: MathAgents.P2LewisTriviality.triviality_R3_closed | proved]
Docstring: "Reading R3:closed-under-conditioning: Stalnaker's Hypothesis holds for every member of a class of probability functions closed under conditioning."

Closure under conditioning is not stated by the source; it is the added hypothesis that defines this reading. Degenerate classes satisfy the hypotheses harmlessly (e.g. `K = ∅`, for which the theorem says nothing; `statement.md` §4, `back-translation.md`). Factorization is again derived, not assumed (G-AX-P2-14).

## 4. Auxiliary lemmas (namespace `Aux`, no docstrings)

These carry no author exposition; they are narrated from their statements only. Each assumes `IsFinAddProb P` unless noted.

- `P ⊥ = 0`. [Lean: MathAgents.P2LewisTriviality.Aux.prob_bot | proved]
- Monotonicity: `a ≤ b` implies `P a ≤ P b`. [Lean: MathAgents.P2LewisTriviality.Aux.prob_mono | proved]
- Expansion (law of total probability; G-AX-P2-4 `prove`): `P X = P (C ⊓ X) + P (Cᶜ ⊓ X)` for all `C, X`. [Lean: MathAgents.P2LewisTriviality.Aux.expansion | proved]
- `0 < P (a ⊓ b)` implies `0 < P a` and `0 < P b`. [Lean: MathAgents.P2LewisTriviality.Aux.pos_of_inf_pos | proved]
- Without assuming `IsFinAddProb`, only `P (C ⊓ A) ≠ 0`: `condProb P C (C ⊓ A) = 1`. [Lean: MathAgents.P2LewisTriviality.Aux.condProb_inf_self | proved]
- `condProb P C (Cᶜ ⊓ A) = 0` for all `C, A`. [Lean: MathAgents.P2LewisTriviality.Aux.condProb_compl_inf | proved]
- Conditioning preserves finite additivity: if `IsFinAddProb P` and `0 < P B`, then `IsFinAddProb (X ↦ condProb P X B)`. [Lean: MathAgents.P2LewisTriviality.Aux.condProb_isFinAddProb | proved]
- Stalnaker's Hypothesis for a conditioned function yields Factorization: if `0 < P A` and `StalnakerHyp cond (X ↦ condProb P X A)`, then `FactorizationAt cond P A B C` for all `B, C`. This lemma assumes no `IsFinAddProb P`. [Lean: MathAgents.P2LewisTriviality.Aux.stalnaker_closed_implies_factorization | proved]

## 5. Foundational envelope (G4)

- **Status.** All 16 declarations of `MathAgents.P2LewisTriviality` (5 definitions, 3 main theorems, 8 `Aux` lemmas) have status `proved` in `reports/kernel/latest.json`; the report lists no findings and no open markers.
- **Axioms.** Every one depends on exactly `propext`, `Classical.choice`, `Quot.sound`, Lean's standard classical axioms. No `sorry`, no project `axiom`, no `native_decide`. Factorization and Stalnaker's Hypothesis enter only as theorem hypotheses (G-AX-P2-5 `hypothesis`), never as axioms.
- **Kernel report provenance.** The report was taken on a clean tree at commit `6fdbd26`; the dossier's `kernel-snapshot.json` (Stage 8 assembly) is the binding record.
- **Fidelity.** No kernel-as-judge waiver applies (`preferences.toml` `fidelity.kernel_as_judge = "never"`); the statements went through the operator's G-FID review.

## 6. What the formal results do not establish

- **Fidelity to Lewis 1976.** The statement of record is the SEP's (Egré and Rott 2026). Whether these theorems match Lewis's own wording, hypotheses or proof route is open (D29) until a primary copy is consulted.
- **Fidelity in general.** The kernel checks that each Lean statement is proved, not that it is the right formalization of the informal text; that judgment rests on the G-FID review and the Stage 1 audits, which are advisory.
- **Non-vacuity of R3.** The near-vacuity of R3:all, and the satisfiability of the R2 hypotheses in a non-degenerate model (the audits give `cond A C := C` on a four-atom algebra as an example), are paper arguments in the dossier. Neither is a Lean theorem here.
- **No triviality corollary.** No formal statement says that the algebra, or the class of probability functions, must be trivial; the "class is trivial" corollary is not formalized (G-AX-P2-18).
- **Other readings.** Readings R1, R4, R5 and R6 (`preferences.toml` `readings.selected` alternatives) are not formalized, nor is a semantics for `>` (G-AX-P2-16, `unconstrained`: no Stalnaker selection-function properties).
- **Countable additivity, sentences.** Results are about finitely additive functions on a Boolean algebra (G-AX-P2-1), not probability measures on σ-algebras or probability over a syntactic language of sentences (G-AX-P2-17).

## References

Egré, Paul, and Hans Rott. 2026. "The Logic of Conditionals." In *The Stanford Encyclopedia of Philosophy*, Summer 2026 ed., edited by Edward N. Zalta and Uri Nodelman. Metaphysics Research Lab, Stanford University. https://plato.stanford.edu/archives/sum2026/entries/logic-conditionals/.

Lewis, David. 1976. "Probabilities of Conditionals and Conditional Probabilities." *The Philosophical Review* 85: 297. https://doi.org/10.2307/2184045. (Not consulted; paywalled, D29.)
