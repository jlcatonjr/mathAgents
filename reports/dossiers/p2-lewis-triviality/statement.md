# Stage 1 statement — P2 Lewis triviality

> **Superseded (Stage 8, 2026-10-01):** this is the historical Stage 1 record. The statements are now proved
> in the kernel and live in `lean/MathAgents/P2LewisTriviality.lean`; see `README.md` and `kernel-snapshot.json`.
>
> **Drafted by:** `@statement-formalizer` · 2026-10-01 · **Status:** draft for the human G-FID review. Nothing here is claimed correct, faithful or proved; every Lean body is `sorry`.
> **Lean stub:** `lean/MathAgentsWIP/P2LewisTriviality.lean`, namespace `MathAgents.P2LewisTriviality`.
> **Statement of record (D29):** the SEP version, per Egré and Rott 2026. Lewis 1976 is paywalled; fidelity to Lewis's own wording stays an open item.
> **Readings formalized (D30, `readings.selected`):** R2, R3:all, R3:closed-under-conditioning.

## 0. Source text (verbatim, per Egré and Rott 2026)

> **Triviality Theorem (Lewis):** "If \(A\) is probabilistically compatible with both \(C\) and \(\neg C\), that is, if \(\Pr(A\wedge C)>0\) and \(\Pr(A\wedge \neg C)>0\), then \(\Pr(A>C)=\Pr(C)\)."
>
> **Stalnaker's Hypothesis:** "For every probability function \(\Pr\) and for every conditional \(A>C\), possibly complex: \(\Pr(A>C)=\Pr(C\mkern2mu|\mkern2muA)\), provided that \(\Pr(A)>0\)."
>
> **Factorization Hypothesis:** "For every probability function \(\Pr\) and for all sentences \(A\) and \(B\) such that \(\Pr(A\wedge B)>0\): \[\Pr(B >C\mid A)=\Pr(C\mid A\wedge B).\]"

(Egré and Rott 2026; quoted as served in `interpretation.md` §1.)

## 1. Common setting and definitions

Throughout, the following are fixed and universally quantified at the outermost level of every theorem:

- `α : Type*` with `[BooleanAlgebra α]` — the propositions; `⊓` = ∧, `⊔` = ∨, `ᶜ` = ¬, `⊤` = tautology.
- `cond : α → α → α` — the conditional `>`; `cond A C` is `A > C`. Uninterpreted: no property of `cond` is assumed. Because its codomain is `α`, the algebra is closed under `>` (nested and conditioned conditionals are well formed).

Definitions (all in `MathAgents.P2LewisTriviality`):

- `IsFinAddProb P` for `P : α → ℝ`: (∀a, 0 ≤ P a) ∧ (∀a, P a ≤ 1) ∧ P ⊤ = 1 ∧ (∀ a b, Disjoint a b → P(a ⊔ b) = P a + P b).
- `condProb P C A := P(A ⊓ C) / P A` — Pr(C | A) as a ratio.
- `FactorizationAt cond P A B C :≡ 0 < P(A ⊓ B) → condProb P (cond B C) A = condProb P C (A ⊓ B)` — one instance of Factorization with its proviso.
- `StalnakerHyp cond P :≡ ∀ A C : α, 0 < P A → P(cond A C) = condProb P C A`.
- `ClosedUnderConditioning K :≡ ∀ P ∈ K, ∀ B : α, 0 < P B → (X ↦ condProb P X B) ∈ K`, for `K : Set (α → ℝ)`.

## 2. Theorems

### `triviality_R2` (reading R2: one fixed Pr, Factorization as hypothesis)

For all α (Boolean algebra), cond : α → α → α, P : α → ℝ, A C : α:

if IsFinAddProb P,
and (F₁) 0 < P(C ⊓ A) → Pr(A > C | C) = Pr(C | C ⊓ A)  [Factorization with A:=C, B:=A],
and (F₂) 0 < P(Cᶜ ⊓ A) → Pr(A > C | Cᶜ) = Pr(C | Cᶜ ⊓ A)  [Factorization with A:=¬C, B:=A],
and 0 < P(A ⊓ C) and 0 < P(A ⊓ Cᶜ),
then P(A > C) = P(C).

```lean
theorem triviality_R2 (cond : α → α → α) (P : α → ℝ) (hP : IsFinAddProb P) (A C : α)
    (hF₁ : FactorizationAt cond P C A C) (hF₂ : FactorizationAt cond P Cᶜ A C)
    (hAC : 0 < P (A ⊓ C)) (hAnC : 0 < P (A ⊓ Cᶜ)) :
    P (cond A C) = P C
```

Only the two Factorization instances the SEP's displayed proof uses (its lines 2–3) are assumed, of the one P (G-AX-P2-12, `one-fixed-Pr`). Assuming full Factorization for that P would be a stronger hypothesis and a weaker theorem; it is implied by this one.

### `triviality_R3_all` (reading R3: Stalnaker's Hypothesis for every probability function)

For all α, cond: if ∀ P : α → ℝ, IsFinAddProb P → StalnakerHyp cond P, then
∀ P : α → ℝ, IsFinAddProb P → ∀ A C : α, 0 < P(A ⊓ C) → 0 < P(A ⊓ Cᶜ) → P(A > C) = P(C).

```lean
theorem triviality_R3_all (cond : α → α → α)
    (hS : ∀ P : α → ℝ, IsFinAddProb P → StalnakerHyp cond P) :
    ∀ P : α → ℝ, IsFinAddProb P → ∀ A C : α,
      0 < P (A ⊓ C) → 0 < P (A ⊓ Cᶜ) → P (cond A C) = P C
```

### `triviality_R3_closed` (reading R3 over a class closed under conditioning)

For all α, cond, K : Set (α → ℝ): if every member of K is IsFinAddProb, K is ClosedUnderConditioning, and StalnakerHyp cond P for every P ∈ K, then
∀ P ∈ K, ∀ A C : α, 0 < P(A ⊓ C) → 0 < P(A ⊓ Cᶜ) → P(A > C) = P(C).

```lean
theorem triviality_R3_closed (cond : α → α → α) (K : Set (α → ℝ))
    (hK : ∀ P ∈ K, IsFinAddProb P) (hclosed : ClosedUnderConditioning K)
    (hS : ∀ P ∈ K, StalnakerHyp cond P) :
    ∀ P ∈ K, ∀ A C : α,
      0 < P (A ⊓ C) → 0 < P (A ⊓ Cᶜ) → P (cond A C) = P C
```

Both R3 theorems take Stalnaker's Hypothesis, not Factorization, as their hypothesis: R3 in `interpretation.md` §2 lists Stalnaker's Hypothesis as its explicit hypothesis and treats closure under conditioning as what would yield Factorization. Adding Factorization would weaken them (see G-AX candidates).

## 3. Preference → encoding map

| Preference (`preferences.toml`) | Choice | Encoding |
|---|---|---|
| `intake.object_logic` (D31) | classical-hol | shallow Lean statement; `cond` an uninterpreted function `α → α → α`, no axioms |
| `gax.P2-1` | finitely-additive | `IsFinAddProb`: nonneg, ≤ 1, P ⊤ = 1, additive on `Disjoint` pairs; no σ-algebra, no finiteness |
| `gax.P2-2` | ratio | `condProb P C A = P(A ⊓ C)/P A`; every occurrence is guarded by a positivity premise |
| `gax.P2-3` | algebra-closed-under-conditional | `cond`'s codomain is `α`, so `A > C`, `Pr(A > C | C)` are well typed |
| `gax.P2-4` | prove | Expansion appears nowhere in the statements; it is left to Stage 2 |
| `gax.P2-5` | hypothesis | Factorization enters R2 only as hypotheses `hF₁`, `hF₂`; no `axiom` |
| `gax.P2-12` | one-fixed-Pr | R2 fixes one `P`; Factorization assumed of that `P` only |
| `readings.selected` (D30) | R2, R3:all, R3:closed | one theorem each |
| `sources.primary_unavailable` (D29) | survey-statement-flagged | all quotations are the SEP's |

## 4. Formalization hazards (checklist)

- **Division by zero.** In ℝ, `x / 0 = 0`. The statements never rely on it: `StalnakerHyp` requires `0 < P A`; `FactorizationAt` requires `0 < P(A ⊓ B)`, which forces `0 < P A` and `0 < P(A ⊓ B)` for both denominators (`P A ≥ P(A ⊓ B)` follows from IsFinAddProb); `ClosedUnderConditioning` requires `0 < P B`.
- **Coercions.** None: all probabilities are real-valued; no ℕ/ℤ/ℚ appears.
- **Finset vs Set, Fintype, decidability.** None used; α is arbitrary (possibly infinite). `K` is a `Set`.
- **Quantifier order.** R2: A, C, P are fixed outermost, hypotheses are about that P. R3: the hypothesis quantifies over all P (or all P ∈ K) and so does the conclusion; the conclusion's P is chosen after `cond` (and K) is fixed, as in the SEP ("for every probability function").
- **Classical choice.** Object logic is classical-hol; no issue.
- **`P ≤ 1` field** is redundant given the others; included because P2-1 lists it. Harmless.
- **Vacuity (checklist item 5).** The R3 hypotheses (Stalnaker's Hypothesis for every P, or for a class closed under conditioning) may be satisfiable only on algebras/classes where the conclusion holds trivially — that is the content of Lewis's result, not a defect, but the reviewer should know the R3 theorems are of this form. `K = ∅` satisfies R3:closed's hypotheses (the theorem is then vacuous for that K). Whether R2's hypotheses are jointly satisfiable in a non-degenerate model has NOT been checked here.
- **¬C** is the Boolean complement `Cᶜ`; `A ∧ ¬C` is `A ⊓ Cᶜ`. Factorization instances are written in the schema's own order (`C ⊓ A`), while the SEP's proof writes `A ∧ C`; equal in a Boolean algebra.
- **Positivity order.** The theorem's provisos are `0 < P(A ⊓ C)`, `0 < P(A ⊓ Cᶜ)`, the SEP's `Pr(A∧C)>0`, `Pr(A∧¬C)>0`.

## 5. G-AX candidates

Already answered in `preferences.toml`: P2-1 (finitely-additive), P2-2 (ratio), P2-3 (closed algebra), P2-4 (prove), P2-5 (hypothesis), P2-12 (one-fixed-Pr). New or residual candidates from this draft:

1. **G-AX-P2-13 (R2 instance restriction).** R2 assumes only the two Factorization instances used in the SEP's displayed proof, not the full schema even for the fixed P. As a hypothesis this is weaker than the source's universal Factorization, so the theorem is stronger; flag for G-FID.
2. **G-AX-P2-14 (R3 hypothesis choice).** R3 theorems assume Stalnaker's Hypothesis alone; the SEP derives the theorem from Factorization. Alternative: assume both. Not stated by the source which R3 intends.
3. **G-AX-P2-7 (residual).** "every probability function" is encoded as every finitely additive `α → ℝ` on the fixed algebra α with fixed `cond` (R3:all). The class is not varied over algebras.
4. **G-AX-P2-6 (residual).** Closure under conditioning is encoded as: conditioning on any B with P B > 0 stays in K. The source does not state closure (R3:closed is the reading that assumes it).
5. **G-AX-P2-15 (Stalnaker's Hypothesis over complex A).** `StalnakerHyp` quantifies over all A, C ∈ α, including conditionals ("possibly complex"); the quantification over A as well as C is a reading of "every conditional A>C".
6. **G-AX-P2-16 (no constraints on `cond`).** The conditional is wholly uninterpreted (no Stalnaker selection-function properties, no `cond A C ≤ ...`). The source states none for this theorem; recorded so G-FID sees it.
7. **G-AX-P2-17 (congruence; raised by both Stage 1 audits).** Propositions are elements of a Boolean (Lindenbaum) algebra, so `cond` automatically respects logical equivalence (A ≡ A′ gives A > C = A′ > C), and Pr does too. The source speaks of sentences and does not state this. No proof step uses it.
8. **G-AX-P2-18 (optional corollary).** Under R3 one could also state the "class is trivial" corollary, condProb P C A = P C. Not formalized; the operator may add it as a further theorem.

**Notes for the G-FID review (from the Stage 1 audits).**
- *R3 and Factorization.* Both R3 theorems assume Stalnaker's Hypothesis only; the proof must derive the two Factorization instances from it through closure under conditioning (planned Stage 2 lemma `stalnaker_closed_implies_factorization`). The theorem is the SEP's conclusion under a different hypothesis set than the SEP's displayed derivation.
- *Near-vacuity of R3:all.* On any algebra with three pairwise disjoint non-zero elements, some finitely additive P violates Stalnaker's Hypothesis, so `hS` can hold only on algebras of at most four elements. R3:all is true but nearly vacuous; this is the substance of Lewis's triviality, and the stated conclusion Pr(A>C) = Pr(C) undersells it (see P2-18).
- *Satisfiability.* R2's hypotheses are jointly satisfiable (e.g. `cond A C := C` with positive Pr(A∧C), Pr(A∧¬C) in a four-atom algebra); on the trivial algebra no finitely additive P exists, so the theorems are vacuous there, harmlessly.

## 6. Open items

- The problem card exists and agrees with `preferences.toml`. The `@adversarial` hidden-hypothesis audit and the independent back-translation have run (`stage1-audit.md`, `back-translation.md`): no theorem needs revision; the candidates above go to the operator.
- G-AX-P2-13 to P2-18 were answered by the operator after this draft and are recorded in `preferences.toml` `[gax]` (D33).
- Fidelity to Lewis 1976's own wording is open (D29).

## References

Egré, Paul, and Hans Rott. 2026. "The Logic of Conditionals." In *The Stanford Encyclopedia of Philosophy*, Summer 2026 ed., edited by Edward N. Zalta and Uri Nodelman. Metaphysics Research Lab, Stanford University. https://plato.stanford.edu/archives/sum2026/entries/logic-conditionals/.

Lewis, David. 1976. "Probabilities of Conditionals and Conditional Probabilities." *The Philosophical Review* 85: 297. https://doi.org/10.2307/2184045.
