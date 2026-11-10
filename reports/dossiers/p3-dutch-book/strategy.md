# P3 Stage 2 strategy: finite Dutch book

> **Author:** `@proof-strategist` · 2026-10-01 · Precondition: `validate_dossier.py --require-stage p3-dutch-book 2` passes.
> Statements under proof: `lean/MathAgentsWIP/P3DutchBook.lean` (approved, unchanged). Library: `MathAgents.FiniteProbability` (`FP.` below).
> Nothing here is proved; the status of each lemma is set only by G-KERNEL. There is no blueprint because leanblueprint is not installed, so the dependency list in §3 takes its place.

## 1. Methods

- **`dutchBook_R1`: construction by cases.** `Aux.not_fap_cases` turns `¬IsFinitelyAdditiveProb q` into three cases. Each case gets an explicit book with a constant net payoff `c < 0`:
  - (a) `q A < 0`: the book is `[⟨A, -1⟩]`, and its payoff `q A − 1_A ω ≤ q A < 0` (`FP.payoff_of_mem` / `payoff_of_not_mem`).
  - (b) `q univ ≠ 1`: with `d := q univ − 1`, the book is `[⟨univ, d⟩]`, and its payoff is `d·(1 − q univ) = −d² < 0`. Every ω lies in `univ`. This case also covers an empty Ω.
  - (c) A and B are disjoint, and `d := q(A∪B) − q A − q B ≠ 0`: the book is `[⟨A∪B, d⟩, ⟨A, −d⟩, ⟨B, −d⟩]`. `Set.indicator_union_of_disjoint` gives the net payoff `−d²`.

  Neither `Nonempty Ω` nor finiteness is needed.
- **`converse_R2`: contradiction through representation.** Set `w ω := q {ω}`. Then `q = FP.pointMass w` (Aux.represent). It follows that `∑ w = 1` and `w ≥ 0`. `FP.expected_netPayoff_pointMass` gives `∑ w·net = 0`, so `IsDutchBook` would give `∑ w·net < 0` (Aux.weighted_neg).
- **`dutchBook_R3`:** `⟨fun ⟨b,h⟩ hq => converse_R2 q hq ⟨b,h⟩, dutchBook_R1 q⟩`.

## 2. Lemma plan (`MathAgents.P3DutchBook.Aux`, in order)

1. `not_fap_cases (hq : ¬IsFinitelyAdditiveProb q) : (∃ A, q A < 0) ∨ q Set.univ ≠ 1 ∨ ∃ A B, Disjoint A B ∧ q (A ∪ B) ≠ q A + q B`. Status: **new** (trivial). Proof: `by_contra h; push_neg at h; exact hq ⟨h.1, h.2.1, h.2.2⟩`. The structure is built with its anonymous constructor and is never destructured.
2. `isDutchBook_of_const (h : ∀ ω, netPayoff q book ω = c) (hc : c < 0) : IsDutchBook q book`. Status: **new** (trivial).
3. `book_neg`, `book_univ`, `book_additivity`: one lemma per case, each giving a closed form for `netPayoff`. Status: **new**. They use `FP.netPayoff_cons/nil`, `FP.payoff_of_mem/not_mem`, `Set.indicator_union_of_disjoint` (**known**), `Set.indicator_apply`, and `ring`/`nlinarith` (`sq_pos_of_ne_zero` / `pow_pos`).
4. `sum_finset_singletons (hq : IsFAP q) (s : Finset Ω) : q ↑s = ∑ ω ∈ s, q {ω}`. Status: **standard**. Proof: `classical`; `Finset.induction_on` (**known**, needs `DecidableEq`); `Finset.coe_insert`, `Set.insert_eq`, `Set.disjoint_singleton_left`, `hq.union_of_disjoint`, `Finset.sum_insert`, base case `hq.empty`.
5. `represent (hq : IsFAP q) (A) : q A = pointMass (fun ω => q {ω}) A`. Status: **standard**. Proof: `classical`; take `s := univ.filter (· ∈ A)`; `Finset.coe_filter_univ` (**known**) with `Set.setOf_mem_eq`; then lemma 4; then `Finset.sum_indicator_subset` (**known**, additive form of `prod_mulIndicator_subset`) with `s ⊆ univ`. This route avoids `Set.toFinset`.
6. `weights_sum (hq) : ∑ ω, q {ω} = 1`: apply lemma 5 at `univ` and `hq.univ_eq_one`. Status: **new**.
7. `weighted_neg (hw : ∀ ω, 0 ≤ w ω) (hs : ∑ w = 1) (hf : ∀ ω, f ω < 0) : ∑ ω, w ω * f ω < 0`. Status: **standard**. Proof: get some ω₀ with `0 < w ω₀` by `by_contra` on `∀ ω, w ω ≤ 0` with `Finset.sum_nonpos` (additive `prod_le_one`, **known**), then `Finset.sum_lt_sum` (**known**) against `0`, `mul_nonpos_of_nonneg_of_nonpos` and `mul_neg_of_pos_of_neg` (**known**).

## 3. Dependencies

- R1 uses lemmas 1, 2 and 3.
- R2 uses lemmas 4, 5, 6 and 7, `FP.expected_netPayoff_pointMass`, and `hq.nonneg`.
- R3 uses R1 and R2.

## 4. Risks

- `Set.indicator` with `fun _ => 1`: `simp` may need `Set.indicator_of_mem` / `Set.indicator_of_notMem` (check whether the name is `notMem` or `not_mem` at the pinned Mathlib).
- Instance mismatch: the `DecidableEq` that `classical` supplies against the one in `Finset.sum_insert` / `coe_filter_univ`. Use `classical` at the top of the proof and never add instance arguments to the Aux statements.
- `Finset.sum_lt_sum` takes membership-bounded hypotheses (`∀ i ∈ s`).
- `List.sum`: avoid unfolding it. Use the `netPayoff_cons` simp lemmas.
- Mathlib deprecations as of 2026-09 (`prod_le_one'` and others) mean every cited name must be checked at the pinned version.

## 5. Loop-back

No statement looks false. On empty Ω, R1 holds vacuously, and R2's hypothesis is contradictory, which lemma 6 or `hq.empty` together with `univ = ∅` exposes. That agrees with the Stage 1 audit. No loop-back is needed.
