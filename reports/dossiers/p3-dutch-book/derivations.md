# P3 Stage 3 derivations: finite Dutch book

> **Superseded (Stage 8, 2026-10-01):** this is the historical Stage 3 record. The statements are now proved
> in the kernel and live in `lean/MathAgents/P3DutchBook.lean`; see `README.md` and `kernel-snapshot.json`.
>
> **Author:** `@logic-articulator` · 2026-10-01 · Inputs: `strategy.md` (CLEARED in `strategy-review.md`), `statement.md`, `problem-card.md`, `lean/MathAgentsWIP/P3DutchBook.lean`, `lean/MathAgents/FiniteProbability.lean`.
> Nothing here is proved; each node's status is set only by G-KERNEL.

Conventions. Calculus: natural deduction, Gentzen–Prawitz NK (classical), because `finite-probability` is a classical theory (`references/object-logics.json`, family `classical`). Classical rules (RAA, ¬¬E, `not_forall`) are admitted by the declared logic and are flagged where they are used.
Rule names: ∧I, ∧E, ∨I, ∨E, →I, →E, ¬I, ¬E, ∀I, ∀E, ∃I, ∃E, ↔I, RAA, ¬¬E, =E (substitution of equals), `def <Name>` (unfolding a definition of `MathAgents.FiniteProbability`).
Decision-procedure steps over ordered fields are named `ring` (commutative-ring normalisation) and `linarith` (linear arithmetic); they introduce no hypothesis.
`FP.` abbreviates `MathAgents.FiniteProbability.` and `Aux.` abbreviates `MathAgents.P3DutchBook.Aux.`. Mathlib and core names were located in the pinned toolchain (`lean/.lake/packages/mathlib`, Lean v4.34.1); `sum_*` and `indicator_*` names are the `to_additive` forms of the located `prod_*` and `mulIndicator_*` declarations, and `sub_ne_zero` is the additive form of `div_ne_one`.
Abbreviations: P := ∃ A, q A < 0; Q := q univ ≠ 1; R := ∃ A B, Disjoint A B ∧ q (A ∪ B) ≠ q A + q B; 1_A ω := A.indicator (fun _ => 1) ω; w := fun ω => q {ω}.

## Node: Aux.not_fap_cases   Lean: MathAgents.P3DutchBook.Aux.not_fap_cases
Calculus: natural deduction (NK)
Object logic: finite-probability

1. ¬ IsFinitelyAdditiveProb q   [hyp]
2. ¬ (P ∨ Q ∨ R)   [hyp]
3. ∃ A, q A < 0   [hyp]
4. P ∨ Q ∨ R   [∨I 3]
5. ⊥   [¬E 2, 4]
6. ¬ ∃ A, q A < 0   [¬I 3, 5]
7. ∀ A, ¬ (q A < 0)   [lemma not_exists 6]
8. ∀ A, 0 ≤ q A   [lemma not_lt 7]
9. q univ ≠ 1   [hyp]
10. P ∨ Q ∨ R   [∨I 9]
11. ⊥   [¬E 2, 10]
12. ¬¬ (q univ = 1)   [¬I 9, 11]
13. q univ = 1   [¬¬E 12]
14. ∃ A B, Disjoint A B ∧ q (A ∪ B) ≠ q A + q B   [hyp]
15. P ∨ Q ∨ R   [∨I 14]
16. ⊥   [¬E 2, 15]
17. ¬ ∃ A B, Disjoint A B ∧ q (A ∪ B) ≠ q A + q B   [¬I 14, 16]
18. ∀ A B, ¬ (Disjoint A B ∧ ¬ (q (A ∪ B) = q A + q B))   [lemma not_exists 17]
19. ∀ A B, Disjoint A B → q (A ∪ B) = q A + q B   [lemma not_and_not_right 18]
20. IsFinitelyAdditiveProb q   [lemma FP.IsFinitelyAdditiveProb.mk 8, 13, 19]
21. ⊥   [¬E 1, 20]
22. P ∨ Q ∨ R   [RAA 2, 21]
23. ¬ IsFinitelyAdditiveProb q → P ∨ Q ∨ R   [→I 1, 22]

## Node: Aux.isDutchBook_of_const   Lean: MathAgents.P3DutchBook.Aux.isDutchBook_of_const
Calculus: natural deduction (NK)
Object logic: finite-probability

1. ∀ ω, netPayoff q book ω = c   [hyp]
2. c < 0   [hyp]
3. netPayoff q book ω = c   [∀E 1]
4. netPayoff q book ω < 0   [=E 3, 2]
5. ∀ ω, netPayoff q book ω < 0   [∀I 4]
6. IsDutchBook q book   [def IsDutchBook 5]

## Node: Aux.book_neg   Lean: MathAgents.P3DutchBook.Aux.book_neg
Calculus: natural deduction (NK)
Object logic: finite-probability

1. netPayoff q [⟨A, -1⟩] ω = payoff q ⟨A, -1⟩ ω   [lemma FP.netPayoff_singleton]
2. payoff q ⟨A, -1⟩ ω = -1 * (1_A ω - q A)   [def payoff]
3. -1 * (1_A ω - q A) = q A - 1_A ω   [ring]
4. netPayoff q [⟨A, -1⟩] ω = q A - 1_A ω   [=E 1, 2, 3]
5. ∀ ω, netPayoff q [⟨A, -1⟩] ω = q A - 1_A ω   [∀I 4]

## Node: Aux.book_univ   Lean: MathAgents.P3DutchBook.Aux.book_univ
Calculus: natural deduction (NK)
Object logic: finite-probability

1. ω ∈ Set.univ   [lemma Set.mem_univ]
2. netPayoff q [⟨univ, d⟩] ω = payoff q ⟨univ, d⟩ ω   [lemma FP.netPayoff_singleton]
3. payoff q ⟨univ, d⟩ ω = d * (1 - q univ)   [lemma FP.payoff_of_mem 1]
4. netPayoff q [⟨univ, d⟩] ω = d * (1 - q univ)   [=E 2, 3]
5. ∀ ω, netPayoff q [⟨univ, d⟩] ω = d * (1 - q univ)   [∀I 4]

## Node: Aux.book_additivity   Lean: MathAgents.P3DutchBook.Aux.book_additivity
Calculus: natural deduction (NK)
Object logic: finite-probability

1. Disjoint A B   [hyp]
2. netPayoff q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩] ω = payoff q ⟨A ∪ B, d⟩ ω + (payoff q ⟨A, -d⟩ ω + (payoff q ⟨B, -d⟩ ω + netPayoff q [] ω))   [lemma FP.netPayoff_cons]
3. netPayoff q [] ω = 0   [lemma FP.netPayoff_nil]
4. 1_(A ∪ B) ω = 1_A ω + 1_B ω   [lemma Set.indicator_union_of_disjoint 1]
5. payoff q ⟨A ∪ B, d⟩ ω = d * (1_(A ∪ B) ω - q (A ∪ B))   [def payoff]
6. payoff q ⟨A, -d⟩ ω = -d * (1_A ω - q A)   [def payoff]
7. payoff q ⟨B, -d⟩ ω = -d * (1_B ω - q B)   [def payoff]
8. netPayoff q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩] ω = d * (1_A ω + 1_B ω - q (A ∪ B)) - d * (1_A ω - q A) - d * (1_B ω - q B)   [=E 2, 3, 4, 5, 6, 7]
9. netPayoff q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩] ω = -d * (q (A ∪ B) - q A - q B)   [ring 8]
10. ∀ ω, netPayoff q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩] ω = -d * (q (A ∪ B) - q A - q B)   [∀I 9]
11. Disjoint A B → ∀ ω, netPayoff q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩] ω = -d * (q (A ∪ B) - q A - q B)   [→I 1, 10]

## Node: Aux.sum_finset_singletons   Lean: MathAgents.P3DutchBook.Aux.sum_finset_singletons
Calculus: natural deduction (NK)
Object logic: finite-probability

1. IsFinitelyAdditiveProb q   [hyp]
2. ((∅ : Finset Ω) : Set Ω) = ∅   [lemma Finset.coe_empty]
3. q ∅ = 0   [lemma FP.IsFinitelyAdditiveProb.empty 1]
4. ∑ ω ∈ ∅, q {ω} = 0   [lemma Finset.sum_empty]
5. q ↑(∅ : Finset Ω) = ∑ ω ∈ ∅, q {ω}   [=E 2, 3, 4]
6. a ∉ s   [hyp]
7. q ↑s = ∑ ω ∈ s, q {ω}   [hyp]
8. ↑(insert a s) = insert a ↑s   [lemma Finset.coe_insert]
9. ↑(insert a s) = {a} ∪ ↑s   [lemma Set.insert_eq 8]
10. a ∉ (↑s : Set Ω)   [lemma Finset.mem_coe 6]
11. Disjoint {a} ↑s   [lemma Set.disjoint_singleton_left 10]
12. q ({a} ∪ ↑s) = q {a} + q ↑s   [lemma FP.IsFinitelyAdditiveProb.union_of_disjoint 1, 11]
13. ∑ ω ∈ insert a s, q {ω} = q {a} + ∑ ω ∈ s, q {ω}   [lemma Finset.sum_insert 6]
14. q ↑(insert a s) = ∑ ω ∈ insert a s, q {ω}   [=E 9, 12, 7, 13]
15. a ∉ s → (q ↑s = ∑ ω ∈ s, q {ω}) → q ↑(insert a s) = ∑ ω ∈ insert a s, q {ω}   [→I 6, 7, 14]
16. ∀ s : Finset Ω, q ↑s = ∑ ω ∈ s, q {ω}   [lemma Finset.induction_on 5, 15]
17. IsFinitelyAdditiveProb q → ∀ s : Finset Ω, q ↑s = ∑ ω ∈ s, q {ω}   [→I 1, 16]

## Node: Aux.represent   Lean: MathAgents.P3DutchBook.Aux.represent
Calculus: natural deduction (NK)
Object logic: finite-probability

1. IsFinitelyAdditiveProb q   [hyp]
2. ↑(univ.filter (· ∈ A)) = {x | x ∈ A}   [lemma Finset.coe_filter_univ]
3. {x | x ∈ A} = A   [lemma Set.ofPred_mem_eq]
4. ↑(univ.filter (· ∈ A)) = A   [=E 2, 3]
5. q A = ∑ ω ∈ univ.filter (· ∈ A), q {ω}   [lemma Aux.sum_finset_singletons 1, 4]
6. univ.filter (· ∈ A) ⊆ univ   [lemma Finset.subset_univ]
7. ∑ ω, (↑(univ.filter (· ∈ A))).indicator w ω = ∑ ω ∈ univ.filter (· ∈ A), w ω   [lemma Finset.sum_indicator_subset 6]
8. ∑ ω, A.indicator w ω = ∑ ω ∈ univ.filter (· ∈ A), q {ω}   [=E 7, 4]
9. pointMass w A = ∑ ω, A.indicator w ω   [def pointMass]
10. q A = pointMass w A   [=E 5, 8, 9]
11. ∀ A, q A = pointMass w A   [∀I 10]
12. IsFinitelyAdditiveProb q → ∀ A, q A = pointMass w A   [→I 1, 11]

## Node: Aux.weights_sum   Lean: MathAgents.P3DutchBook.Aux.weights_sum
Calculus: natural deduction (NK)
Object logic: finite-probability

1. IsFinitelyAdditiveProb q   [hyp]
2. q univ = pointMass w univ   [lemma Aux.represent 1]
3. pointMass w univ = ∑ ω, univ.indicator w ω   [def pointMass]
4. univ.indicator w = w   [lemma Set.indicator_univ]
5. q univ = 1   [lemma FP.IsFinitelyAdditiveProb.univ_eq_one 1]
6. ∑ ω, q {ω} = 1   [=E 2, 3, 4, 5]
7. IsFinitelyAdditiveProb q → ∑ ω, q {ω} = 1   [→I 1, 6]

## Node: Aux.weighted_neg   Lean: MathAgents.P3DutchBook.Aux.weighted_neg
Calculus: natural deduction (NK)
Object logic: finite-probability

1. ∀ ω, 0 ≤ w ω   [hyp]
2. ∑ ω, w ω = 1   [hyp]
3. ∀ ω, f ω < 0   [hyp]
4. ∀ ω, w ω ≤ 0   [hyp]
5. ∑ ω, w ω ≤ 0   [lemma Finset.sum_nonpos 4]
6. 1 ≤ 0   [=E 2, 5]
7. ⊥   [linarith 6]
8. ¬ ∀ ω, w ω ≤ 0   [¬I 4, 7]
9. ∃ ω₀, ¬ (w ω₀ ≤ 0)   [lemma Classical.not_forall 8]
10. ¬ (w ω₀ ≤ 0)   [hyp]
11. 0 < w ω₀   [lemma not_le 10]
12. w ω₀ * f ω₀ < 0   [lemma mul_neg_of_pos_of_neg 11, 3]
13. ∀ ω ∈ univ, w ω * f ω ≤ 0   [lemma mul_nonpos_of_nonneg_of_nonpos 1, 3]
14. ∃ ω ∈ univ, w ω * f ω < 0   [∃I 12]
15. ∑ ω, w ω * f ω < ∑ ω, (0 : ℝ)   [lemma Finset.sum_lt_sum 13, 14]
16. ∑ ω, (0 : ℝ) = 0   [lemma Finset.sum_const_zero]
17. ∑ ω, w ω * f ω < 0   [=E 15, 16]
18. ∑ ω, w ω * f ω < 0   [∃E 9, 10, 17]

## Node: dutchBook_R1   Lean: MathAgents.P3DutchBook.dutchBook_R1
Calculus: natural deduction (NK)
Object logic: finite-probability

1. ¬ IsFinitelyAdditiveProb q   [hyp]
2. P ∨ Q ∨ R   [lemma Aux.not_fap_cases 1]
3. ∃ A, q A < 0   [hyp]
4. q A < 0   [hyp]
5. ∀ ω, netPayoff q [⟨A, -1⟩] ω = q A - 1_A ω   [lemma Aux.book_neg]
6. ∀ ω, 0 ≤ 1_A ω   [lemma Set.indicator_nonneg]
7. ∀ ω, netPayoff q [⟨A, -1⟩] ω < 0   [linarith 4, 5, 6]
8. IsDutchBook q [⟨A, -1⟩]   [def IsDutchBook 7]
9. ∃ book, IsDutchBook q book   [∃I 8]
10. ∃ book, IsDutchBook q book   [∃E 3, 4, 9]
11. q univ ≠ 1   [hyp]
12. q univ - 1 ≠ 0   [lemma sub_ne_zero 11]
13. ∀ ω, netPayoff q [⟨univ, q univ - 1⟩] ω = (q univ - 1) * (1 - q univ)   [lemma Aux.book_univ]
14. (q univ - 1) * (1 - q univ) = -(q univ - 1) ^ 2   [ring]
15. 0 < (q univ - 1) ^ 2   [lemma sq_pos_of_ne_zero 12]
16. -(q univ - 1) ^ 2 < 0   [lemma neg_lt_zero 15]
17. ∀ ω, netPayoff q [⟨univ, q univ - 1⟩] ω = -(q univ - 1) ^ 2   [=E 13, 14]
18. IsDutchBook q [⟨univ, q univ - 1⟩]   [lemma Aux.isDutchBook_of_const 17, 16]
19. ∃ book, IsDutchBook q book   [∃I 18]
20. ∃ A B, Disjoint A B ∧ q (A ∪ B) ≠ q A + q B   [hyp]
21. Disjoint A B ∧ q (A ∪ B) ≠ q A + q B   [hyp]
22. Disjoint A B   [∧E 21]
23. q (A ∪ B) ≠ q A + q B   [∧E 21]
24. q (A ∪ B) - (q A + q B) ≠ 0   [lemma sub_ne_zero 23]
25. ∀ ω, netPayoff q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩] ω = -d * (q (A ∪ B) - q A - q B), with d := q (A ∪ B) - (q A + q B)   [lemma Aux.book_additivity 22]
26. -d * (q (A ∪ B) - q A - q B) = -d ^ 2   [ring]
27. ∀ ω, netPayoff q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩] ω = -d ^ 2   [=E 25, 26]
28. 0 < d ^ 2   [lemma sq_pos_of_ne_zero 24]
29. -d ^ 2 < 0   [lemma neg_lt_zero 28]
30. IsDutchBook q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩]   [lemma Aux.isDutchBook_of_const 27, 29]
31. ∃ book, IsDutchBook q book   [∃I 30]
32. ∃ book, IsDutchBook q book   [∃E 20, 21, 31]
33. ∃ book, IsDutchBook q book   [∨E 2, 3, 10, 11, 19, 20, 32]
34. ¬ IsFinitelyAdditiveProb q → ∃ book, IsDutchBook q book   [→I 1, 33]

## Node: converse_R2   Lean: MathAgents.P3DutchBook.converse_R2
Calculus: natural deduction (NK)
Object logic: finite-probability

1. IsFinitelyAdditiveProb q   [hyp]
2. ∀ A, q A = pointMass w A   [lemma Aux.represent 1]
3. q = pointMass w   [lemma funext 2]
4. ∑ ω, w ω = 1   [lemma Aux.weights_sum 1]
5. ∀ ω, 0 ≤ w ω   [lemma FP.IsFinitelyAdditiveProb.nonneg 1]
6. ∃ book, IsDutchBook q book   [hyp]
7. IsDutchBook q b   [hyp]
8. ∀ ω, netPayoff q b ω < 0   [def IsDutchBook 7]
9. ∀ ω, netPayoff (pointMass w) b ω < 0   [=E 3, 8]
10. ∑ ω, w ω * netPayoff (pointMass w) b ω < 0   [lemma Aux.weighted_neg 5, 4, 9]
11. ∑ ω, w ω * netPayoff (pointMass w) b ω = 0   [lemma FP.expected_netPayoff_pointMass 4]
12. (0 : ℝ) < 0   [=E 11, 10]
13. ⊥   [lemma lt_irrefl 12]
14. ⊥   [∃E 6, 7, 13]
15. ¬ ∃ book, IsDutchBook q book   [¬I 6, 14]
16. IsFinitelyAdditiveProb q → ¬ ∃ book, IsDutchBook q book   [→I 1, 15]

## Node: dutchBook_R3   Lean: MathAgents.P3DutchBook.dutchBook_R3
Calculus: natural deduction (NK)
Object logic: finite-probability

1. ∃ book, IsDutchBook q book   [hyp]
2. IsFinitelyAdditiveProb q   [hyp]
3. ¬ ∃ book, IsDutchBook q book   [lemma MathAgents.P3DutchBook.converse_R2 2]
4. ⊥   [¬E 3, 1]
5. ¬ IsFinitelyAdditiveProb q   [¬I 2, 4]
6. (∃ book, IsDutchBook q book) → ¬ IsFinitelyAdditiveProb q   [→I 1, 5]
7. ¬ IsFinitelyAdditiveProb q → ∃ book, IsDutchBook q book   [lemma MathAgents.P3DutchBook.dutchBook_R1]
8. (∃ book, IsDutchBook q book) ↔ ¬ IsFinitelyAdditiveProb q   [↔I 6, 7]
