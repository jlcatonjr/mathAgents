# P3 Stage 4 tactic plan: finite Dutch book

> **Superseded (Stage 8, 2026-10-01):** this is the historical Stage 4 record. The statements are now proved
> in the kernel and live in `lean/MathAgents/P3DutchBook.lean`; see `README.md` and `kernel-snapshot.json`.
>
> **Author:** `@tactic-planner` · 2026-10-01 · Inputs: `derivations.md`, `strategy.md` (CLEARED in `strategy-review.md`), `lean/MathAgentsWIP/P3DutchBook.lean`, `lean/MathAgents/FiniteProbability.lean`.
> These are advisory sketches. Nothing here is proved; each node's status is set only by G-KERNEL, and the Lean prover may depart from a plan when it fails.

Conventions. `FP.` abbreviates `MathAgents.FiniteProbability.` and `Aux.` abbreviates `MathAgents.P3DutchBook.Aux.` in prose; every `Lemmas:` line uses fully-qualified names.
Lemma locations: Mathlib paths are relative to `lean/.lake/packages/mathlib/`; core names were found in the pinned toolchain sources (`~/.elan/toolchains/leanprover--lean4---v4.34.1/src/lean/`, written `core:`); library names are in `lean/MathAgents/FiniteProbability.lean` (and in the G-KERNEL report).
`sum_*` and `indicator_*` names are `to_additive` forms: the located note names the multiplicative source declaration. All names were also checked against `reports/kernel/name-index.txt`.
Planned Aux lemmas (the `Aux.*` node headers below) do not exist yet, so they appear only in node headers and Plan prose, never on `Lemmas:` lines.
Statement shape assumed for the Aux lemmas: the signatures in `strategy.md` §2, with `{Ω : Type*} [Fintype Ω]` where a sum occurs and no extra instance arguments (use `classical` inside proofs).
Avoided names: `Set.setOf_mem_eq` is a deprecated alias at the pinned Mathlib (since 2026-07-09); use `Set.ofPred_mem_eq`. Bare `not_forall` is not a declaration; use `Classical.not_forall`.

## Node: Aux.not_fap_cases   Lean: MathAgents.P3DutchBook.Aux.not_fap_cases
Derivation steps: derivations.md, node Aux.not_fap_cases, lines 1–23
Plan:
  1. `by_contra h`                                   -- RAA, step 22 (classical; admitted by the declared logic)
  2. `push_neg at h`                                 -- steps 6–8, 12–13, 17–19: h becomes `(∀ A, 0 ≤ q A) ∧ q Set.univ = 1 ∧ ∀ A B, Disjoint A B → q (A ∪ B) = q A + q B`
  3. `exact hq ⟨h.1, h.2.1, h.2.2⟩`                  -- step 20 (anonymous constructor of the structure `FP.IsFinitelyAdditiveProb`, defined in lean/MathAgents/FiniteProbability.lean; its auto-generated `.mk` is not listed in the G-KERNEL report, so it is kept off the Lemmas line) then ¬E, step 21
Lemmas: not_or (located: core: Init/PropLemmas.lean) | not_exists (located: core: Init/PropLemmas.lean) | not_lt (located: Mathlib/Order/Defs/LinearOrder.lean) | not_and_not_right (located: Mathlib/Basic/Logic/Basic.lean) | Classical.not_not (located: core: Init/Classical.lean)
Engine hints: lean-builtin
Fallbacks: if `push_neg` leaves `¬(… ≠ …)` or an `∧ ¬` shape, use `simp only [not_or, not_exists, not_lt, not_and_not_right, Classical.not_not] at h`; or `refine Classical.byContradiction fun h => hq ⟨fun A => ?_, ?_, fun A B hAB => ?_⟩` and close each field with `by_contra` + `exact h (Or.inl ⟨A, by linarith⟩)` etc.

## Node: Aux.isDutchBook_of_const   Lean: MathAgents.P3DutchBook.Aux.isDutchBook_of_const
Derivation steps: derivations.md, node Aux.isDutchBook_of_const, lines 1–6
Plan:
  1. `intro ω`                                       -- ∀I, step 5 (`IsDutchBook` is a def whose body is a ∀; `intro` unfolds it)
  2. `rw [h ω]; exact hc`                            -- =E, steps 3–4
Lemmas: MathAgents.FiniteProbability.IsDutchBook (located: lean/MathAgents/FiniteProbability.lean)
Engine hints: lean-builtin
Fallbacks: `fun ω => (h ω).symm ▸ hc`; or `unfold IsDutchBook; intro ω; simpa [h ω] using hc`; or `intro ω; linarith [h ω]`.

## Node: Aux.book_neg   Lean: MathAgents.P3DutchBook.Aux.book_neg
Derivation steps: derivations.md, node Aux.book_neg, lines 1–5
Plan:
  1. `intro ω` (if the statement is ∀-quantified)    -- ∀I, step 5
  2. `rw [netPayoff_singleton]`                      -- step 1
  3. `simp only [payoff]`                            -- def payoff, step 2
  4. `ring`                                          -- step 3
Lemmas: MathAgents.FiniteProbability.netPayoff_singleton (located: lean/MathAgents/FiniteProbability.lean) | MathAgents.FiniteProbability.payoff (located: lean/MathAgents/FiniteProbability.lean)
Engine hints: lean-builtin
Fallbacks: `simp [payoff]; ring`; or `rw [netPayoff_singleton, payoff_neg_stake]` then `simp [payoff]` (the library lemma `FP.payoff_neg_stake` turns the −1 stake into a negation).

## Node: Aux.book_univ   Lean: MathAgents.P3DutchBook.Aux.book_univ
Derivation steps: derivations.md, node Aux.book_univ, lines 1–5
Plan:
  1. `intro ω`                                       -- ∀I, step 5
  2. `rw [netPayoff_singleton, payoff_of_mem _ _ (Set.mem_univ ω)]`   -- steps 1–4 (the bet's event reduces to `Set.univ` by `rfl`)
Lemmas: MathAgents.FiniteProbability.netPayoff_singleton (located: lean/MathAgents/FiniteProbability.lean) | MathAgents.FiniteProbability.payoff_of_mem (located: lean/MathAgents/FiniteProbability.lean) | Set.mem_univ (located: Mathlib/Data/Set/Operations.lean)
Engine hints: lean-builtin
Fallbacks: if `rw` fails on the structure projection, `simp [payoff, Set.indicator_of_mem (Set.mem_univ ω)]`; or `simp [payoff]` alone (simp knows `Set.indicator_univ`).

## Node: Aux.book_additivity   Lean: MathAgents.P3DutchBook.Aux.book_additivity
Derivation steps: derivations.md, node Aux.book_additivity, lines 1–11
Plan:
  1. `intro ω`                                       -- ∀I, step 10 (hAB : Disjoint A B in context, step 1)
  2. `simp only [netPayoff_cons, netPayoff_nil, payoff, Set.indicator_union_of_disjoint hAB]`   -- steps 2–8
  3. `ring`                                          -- step 9
Lemmas: MathAgents.FiniteProbability.netPayoff_cons (located: lean/MathAgents/FiniteProbability.lean) | MathAgents.FiniteProbability.netPayoff_nil (located: lean/MathAgents/FiniteProbability.lean) | MathAgents.FiniteProbability.payoff (located: lean/MathAgents/FiniteProbability.lean) | Set.indicator_union_of_disjoint (located: Mathlib/Algebra/Group/Indicator.lean, to_additive of Set.mulIndicator_union_of_disjoint)
Engine hints: lean-builtin
Fallbacks: `Set.indicator_union_of_disjoint` returns a lambda, so if `simp only` leaves a beta-redex add `beta_reduce` or use `simp`; else `by_cases hA : ω ∈ A <;> by_cases hB : ω ∈ B <;> simp [payoff, hA, hB] <;> ring` (the case ω ∈ A ∧ ω ∈ B is excluded by `Set.disjoint_left.mp hAB hA hB`).

## Node: Aux.sum_finset_singletons   Lean: MathAgents.P3DutchBook.Aux.sum_finset_singletons
Derivation steps: derivations.md, node Aux.sum_finset_singletons, lines 1–17
Plan:
  1. `classical`                                     -- DecidableEq Ω for `insert` and `Finset.sum_insert` (strategy risk on instance mismatch)
  2. `induction s using Finset.induction_on with`    -- step 16
  3. `| empty => simp [hq.empty]`                    -- base case, steps 2–5 (`Finset.coe_empty`, `Finset.sum_empty`, `FP.IsFinitelyAdditiveProb.empty`)
  4. `| insert a s ha ih =>`                         -- steps 6–7
       `rw [Finset.coe_insert, Set.insert_eq, hq.union_of_disjoint _ _ (Set.disjoint_singleton_left.mpr (Finset.mem_coe.not.mpr ha)), Finset.sum_insert ha, ih]`   -- steps 8–14
Lemmas: Finset.induction_on (located: Mathlib/Data/Finset/Insert.lean) | Finset.coe_empty (located: Mathlib/Data/Finset/Empty.lean) | Finset.sum_empty (located: Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean, to_additive of Finset.prod_empty) | Finset.coe_insert (located: Mathlib/Data/Finset/Insert.lean) | Set.insert_eq (located: Mathlib/Data/Set/Insert.lean) | Finset.mem_coe (located: Mathlib/Data/Finset/Defs.lean) | Set.disjoint_singleton_left (located: Mathlib/Data/Set/Insert.lean) | Finset.sum_insert (located: Mathlib/Algebra/BigOperators/Group/Finset/Basic.lean, to_additive of Finset.prod_insert) | MathAgents.FiniteProbability.IsFinitelyAdditiveProb.empty (located: lean/MathAgents/FiniteProbability.lean) | MathAgents.FiniteProbability.IsFinitelyAdditiveProb.union_of_disjoint (located: lean/MathAgents/FiniteProbability.lean)
Engine hints: lean-builtin
Fallbacks: if the case names differ at the pinned Mathlib, use `| @insert a s ha ih` or `refine Finset.induction_on s ?_ ?_`; if `Finset.mem_coe.not.mpr` does not elaborate, use `(by simpa using ha)`; if `rw` fails on the coercion, `simp only [Finset.coe_insert, Set.insert_eq]` first, then `rw`.

## Node: Aux.represent   Lean: MathAgents.P3DutchBook.Aux.represent
Derivation steps: derivations.md, node Aux.represent, lines 1–12
Plan:
  1. `classical`
  2. `set s := Finset.univ.filter (· ∈ A)` and `have hs : (↑s : Set Ω) = A := by rw [Finset.coe_filter_univ, Set.ofPred_mem_eq]`   -- steps 2–4
  3. `calc q A = q ↑s := by rw [hs]`
     `_ = ∑ ω ∈ s, q {ω} := Aux.sum_finset_singletons hq s`   -- step 5 (planned Aux lemma)
     `_ = ∑ ω, (↑s : Set Ω).indicator (fun ω => q {ω}) ω := (Finset.sum_indicator_subset _ (Finset.subset_univ s)).symm`   -- steps 6–7, used right to left
     `_ = pointMass (fun ω => q {ω}) A := by rw [hs]; rfl`   -- steps 8–10 (def pointMass)
Lemmas: Finset.coe_filter_univ (located: Mathlib/Data/Finset/BooleanAlgebra.lean) | Set.ofPred_mem_eq (located: Mathlib/Data/Set/Operations.lean) | Finset.sum_indicator_subset (located: Mathlib/Algebra/BigOperators/Group/Finset/Indicator.lean, to_additive of Finset.prod_mulIndicator_subset) | Finset.subset_univ (located: Mathlib/Data/Fintype/Defs.lean) | MathAgents.FiniteProbability.pointMass (located: lean/MathAgents/FiniteProbability.lean)
Engine hints: lean-builtin
Fallbacks: prove `hs` by `ext x; simp` (`Finset.mem_coe`, `Finset.mem_filter`, `Finset.mem_univ`); replace the last calc step by `simp only [pointMass, hs]`; if `Finset.coe_filter_univ`'s `DecidablePred` instance mismatches the `classical` one, use `ext x; simp` or `convert` with `Finset.filter_congr_decidable`.

## Node: Aux.weights_sum   Lean: MathAgents.P3DutchBook.Aux.weights_sum
Derivation steps: derivations.md, node Aux.weights_sum, lines 1–7
Plan:
  1. `have h := Aux.represent hq Set.univ`          -- step 2 (planned Aux lemma)
  2. `rw [hq.univ_eq_one, pointMass, Set.indicator_univ] at h`   -- steps 3–5
  3. `exact h.symm`                                  -- step 6
Lemmas: MathAgents.FiniteProbability.IsFinitelyAdditiveProb.univ_eq_one (located: lean/MathAgents/FiniteProbability.lean) | MathAgents.FiniteProbability.pointMass (located: lean/MathAgents/FiniteProbability.lean) | Set.indicator_univ (located: Mathlib/Algebra/Notation/Indicator.lean, to_additive of Set.mulIndicator_univ)
Engine hints: lean-builtin
Fallbacks: `simpa [pointMass, hq.univ_eq_one] using (Aux.represent hq Set.univ).symm`; if `rw [pointMass]` fails (noncomputable def), use `unfold pointMass at h` or `simp only [pointMass] at h`.

## Node: Aux.weighted_neg   Lean: MathAgents.P3DutchBook.Aux.weighted_neg
Derivation steps: derivations.md, node Aux.weighted_neg, lines 1–18
Plan:
  1. `obtain ⟨ω₀, h₀⟩ : ∃ ω, 0 < w ω := by`
       `by_contra h; push_neg at h`                 -- steps 4, 8–11 (classical, `Classical.not_forall`, `not_le`)
       `have := Finset.sum_nonpos (s := Finset.univ) fun i _ => h i`   -- step 5
       `linarith`                                    -- steps 6–7
  2. `calc ∑ ω, w ω * f ω < ∑ ω, (0 : ℝ) := Finset.sum_lt_sum (fun i _ => mul_nonpos_of_nonneg_of_nonpos (hw i) (hf i).le) ⟨ω₀, Finset.mem_univ _, mul_neg_of_pos_of_neg h₀ (hf ω₀)⟩`   -- steps 12–15
     `_ = 0 := Finset.sum_const_zero`             -- steps 16–17
Lemmas: Classical.not_forall (located: core: Init/Classical.lean) | not_le (located: Mathlib/Order/Defs/LinearOrder.lean) | Finset.sum_nonpos (located: Mathlib/Algebra/Order/BigOperators/Group/Finset.lean, to_additive of Finset.prod_le_one) | Finset.sum_lt_sum (located: Mathlib/Algebra/Order/BigOperators/Group/Finset.lean, to_additive of Finset.prod_lt_prod) | Finset.mem_univ (located: Mathlib/Data/Fintype/Defs.lean) | mul_nonpos_of_nonneg_of_nonpos (located: Mathlib/Algebra/Order/GroupWithZero/Basic.lean) | mul_neg_of_pos_of_neg (located: Mathlib/Algebra/Order/GroupWithZero/Basic.lean) | LT.lt.le (located: Mathlib/Order/Basic.lean, alias of le_of_lt) | Finset.sum_const_zero (located: Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean, to_additive of Finset.prod_const_one)
Engine hints: lean-builtin | z3 (hint only: the linear step 6–7 is a one-line LRA check; the kernel must re-check)
Fallbacks: if `push_neg` is unavailable in this form, `simp only [Classical.not_forall, not_exists, not_lt] at h` (shape `¬ ∃ ω, 0 < w ω` becomes `∀ ω, w ω ≤ 0`); for step 2, `Finset.sum_lt_sum_of_nonempty` needs every term strictly negative, which fails when some `w ω = 0`, so do not substitute it; if `calc` elaboration is slow, `have := Finset.sum_lt_sum …; simpa using this`.

## Node: dutchBook_R1   Lean: MathAgents.P3DutchBook.dutchBook_R1
Derivation steps: derivations.md, node dutchBook_R1, lines 1–34
Plan:
  1. `rcases Aux.not_fap_cases hq with ⟨A, hA⟩ | hU | ⟨A, B, hAB, hne⟩`   -- step 2, ∨E step 33 (planned Aux lemma)
  2. Case (a): `refine ⟨[⟨A, -1⟩], fun ω => ?_⟩; rw [Aux.book_neg]; have := Set.indicator_nonneg (s := A) (fun _ _ => zero_le_one) ω; linarith`   -- steps 3–10
  3. Case (b): `refine ⟨[⟨Set.univ, q Set.univ - 1⟩], Aux.isDutchBook_of_const (c := -(q Set.univ - 1) ^ 2) (fun ω => by rw [Aux.book_univ]; ring) ?_⟩; have := sq_pos_of_ne_zero (sub_ne_zero.mpr hU); linarith`   -- steps 11–19
  4. Case (c): `set d := q (A ∪ B) - (q A + q B) with hd; refine ⟨[⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩], Aux.isDutchBook_of_const (c := -d ^ 2) (fun ω => by rw [Aux.book_additivity hAB]; ring) ?_⟩; have := sq_pos_of_ne_zero (sub_ne_zero.mpr hne); linarith`   -- steps 20–32
Lemmas: Set.indicator_nonneg (located: Mathlib/Algebra/Order/Group/Indicator.lean, to_additive of Set.one_le_mulIndicator) | zero_le_one (located: Mathlib/Algebra/Order/ZeroLEOne.lean) | sub_ne_zero (located: Mathlib/Algebra/Group/Basic.lean, to_additive of div_ne_one) | sq_pos_of_ne_zero (located: Mathlib/Algebra/Order/Ring/Basic.lean, alias from sq_pos_iff) | neg_lt_zero (located: Mathlib/Algebra/Order/Group/Unbundled/Basic.lean, to_additive of inv_lt_one')
Engine hints: lean-builtin | z3 (hint only for the sign arguments; the kernel decides)
Fallbacks: replace `have := sq_pos_of_ne_zero …; linarith` with `nlinarith [sq_nonneg (q Set.univ - 1), sq_pos_of_ne_zero (sub_ne_zero.mpr hU)]` or `exact neg_lt_zero.mpr (by positivity)`; if `set d` interferes with the `rw [Aux.book_additivity hAB]` pattern, use plain `let`-free terms (write `q (A ∪ B) - (q A + q B)` inline); in case (a), `have := Set.indicator_nonneg …` may need `(f := fun _ => (1 : ℝ))` explicit.

## Node: converse_R2   Lean: MathAgents.P3DutchBook.converse_R2
Derivation steps: derivations.md, node converse_R2, lines 1–16
Plan:
  1. `rintro ⟨b, hb⟩`                                -- steps 6–8
  2. `have hrep : q = pointMass (fun ω => q {ω}) := funext (Aux.represent hq)`   -- steps 2–3 (planned Aux lemma)
  3. `have hsum := Aux.weights_sum hq`               -- step 4
  4. `have hneg := Aux.weighted_neg (fun ω => hq.nonneg _) hsum hb`   -- steps 5, 10 (stated against q; no rewrite needed)
  5. `have h0 := expected_netPayoff_pointMass hsum b; rw [← hrep] at h0`   -- steps 9, 11 (rewrite `pointMass w` back to `q`, avoiding rewriting q inside w)
  6. `linarith`                                      -- steps 12–14
Lemmas: funext (located: core: Init/Prelude.lean) | MathAgents.FiniteProbability.expected_netPayoff_pointMass (located: lean/MathAgents/FiniteProbability.lean) | MathAgents.FiniteProbability.IsFinitelyAdditiveProb.nonneg (located: lean/MathAgents/FiniteProbability.lean) | MathAgents.FiniteProbability.pointMass (located: lean/MathAgents/FiniteProbability.lean) | lt_irrefl (located: Mathlib/Order/Defs/PartialOrder.lean)
Engine hints: lean-builtin
Fallbacks: if `rw [← hrep] at h0` fails (motive or pattern), `simp only [← hrep] at h0` or `conv at h0 => rw [← hrep]`; or keep `pointMass w` and instead `rw [hrep] at hb` before calling `Aux.weighted_neg`, then `exact lt_irrefl _ (h0 ▸ hneg)`.

## Node: dutchBook_R3   Lean: MathAgents.P3DutchBook.dutchBook_R3
Derivation steps: derivations.md, node dutchBook_R3, lines 1–8
Plan:
  1. `constructor`                                   -- ↔I, step 8
  2. `· rintro ⟨b, hb⟩ hq; exact converse_R2 q hq ⟨b, hb⟩`   -- steps 1–6
  3. `· exact dutchBook_R1 q`                        -- step 7
Lemmas: Iff.intro (located: core: Init/Core.lean, structure Iff constructor) | MathAgents.P3DutchBook.converse_R2 (located then: lean/MathAgentsWIP/P3DutchBook.lean; now lean/MathAgents/P3DutchBook.lean) | MathAgents.P3DutchBook.dutchBook_R1 (located then: lean/MathAgentsWIP/P3DutchBook.lean; now lean/MathAgents/P3DutchBook.lean)
Engine hints: lean-builtin
Fallbacks: term mode `⟨fun ⟨b, h⟩ hq => converse_R2 q hq ⟨b, h⟩, dutchBook_R1 q⟩`.
