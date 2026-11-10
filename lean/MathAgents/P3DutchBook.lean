import MathAgents.FiniteProbability

/-!
# P3: the finite Dutch book theorem

Primary source: de Finetti 1937, Chapitre I (French, open; charter D29). Converse statement of
record: Vineberg 2022 (survey, flagged). Object logic `finite-probability`: built on
`MathAgents.FiniteProbability`. See `reports/dossiers/p3-dutch-book/statement.md`.
-/

namespace MathAgents.P3DutchBook

open MathAgents.FiniteProbability

namespace Aux

theorem not_fap_cases {Ω : Type*} {q : Set Ω → ℝ} (hq : ¬ IsFinitelyAdditiveProb q) :
    (∃ A, q A < 0) ∨ q Set.univ ≠ 1 ∨
      ∃ A B, Disjoint A B ∧ q (A ∪ B) ≠ q A + q B := by
  by_contra h
  push Not at h
  exact hq ⟨h.1, h.2.1, h.2.2⟩

theorem isDutchBook_of_const {Ω : Type*} {q : Set Ω → ℝ} {book : List (Bet Ω)} {c : ℝ}
    (h : ∀ ω, netPayoff q book ω = c) (hc : c < 0) : IsDutchBook q book := by
  intro ω
  rw [h ω]
  exact hc

theorem book_neg {Ω : Type*} (q : Set Ω → ℝ) (A : Set Ω) (ω : Ω) :
    netPayoff q [⟨A, -1⟩] ω = q A - A.indicator (fun _ => (1 : ℝ)) ω := by
  rw [netPayoff_singleton]
  simp only [payoff]
  ring

theorem book_univ {Ω : Type*} (q : Set Ω → ℝ) (S : ℝ) (ω : Ω) :
    netPayoff q [⟨Set.univ, S⟩] ω = S * (1 - q Set.univ) := by
  rw [netPayoff_singleton]
  exact payoff_of_mem q ⟨Set.univ, S⟩ (Set.mem_univ ω)

theorem book_additivity {Ω : Type*} (q : Set Ω → ℝ) {A B : Set Ω} (hAB : Disjoint A B)
    (d : ℝ) (ω : Ω) :
    netPayoff q [⟨A ∪ B, d⟩, ⟨A, -d⟩, ⟨B, -d⟩] ω = -(d * (q (A ∪ B) - (q A + q B))) := by
  simp only [netPayoff_cons, netPayoff_nil, payoff, Set.indicator_union_of_disjoint hAB]
  ring

theorem sum_finset_singletons {Ω : Type*} {q : Set Ω → ℝ} (hq : IsFinitelyAdditiveProb q)
    (s : Finset Ω) : q ↑s = ∑ ω ∈ s, q {ω} := by
  classical
  induction s using Finset.induction_on with
  | empty => simp [hq.empty]
  | insert a s ha ih =>
    rw [Finset.coe_insert, Set.insert_eq,
      hq.union_of_disjoint _ _ (Set.disjoint_singleton_left.mpr (by simpa using ha)),
      Finset.sum_insert ha, ih]

theorem represent {Ω : Type*} [Fintype Ω] {q : Set Ω → ℝ} (hq : IsFinitelyAdditiveProb q)
    (A : Set Ω) : q A = pointMass (fun ω => q {ω}) A := by
  classical
  have hs : ((Finset.univ.filter (· ∈ A) : Finset Ω) : Set Ω) = A := by
    ext x; simp
  calc q A = q ↑(Finset.univ.filter (· ∈ A)) := by rw [hs]
    _ = ∑ ω ∈ Finset.univ.filter (· ∈ A), q {ω} := sum_finset_singletons hq _
    _ = ∑ ω, (↑(Finset.univ.filter (· ∈ A)) : Set Ω).indicator (fun ω => q {ω}) ω :=
        (Finset.sum_indicator_subset _ (Finset.subset_univ _)).symm
    _ = pointMass (fun ω => q {ω}) A := by rw [hs]; rfl

theorem weights_sum {Ω : Type*} [Fintype Ω] {q : Set Ω → ℝ} (hq : IsFinitelyAdditiveProb q) :
    ∑ ω, q {ω} = 1 := by
  have h := represent hq Set.univ
  rw [hq.univ_eq_one] at h
  simpa [pointMass] using h.symm

theorem weighted_neg {Ω : Type*} [Fintype Ω] {w f : Ω → ℝ} (hw : ∀ ω, 0 ≤ w ω)
    (hs : ∑ ω, w ω = 1) (hf : ∀ ω, f ω < 0) : ∑ ω, w ω * f ω < 0 := by
  obtain ⟨ω₀, h₀⟩ : ∃ ω, 0 < w ω := by
    by_contra h
    push Not at h
    have := Finset.sum_nonpos (s := Finset.univ) fun i _ => h i
    linarith
  calc ∑ ω, w ω * f ω < ∑ _ω : Ω, (0 : ℝ) :=
        Finset.sum_lt_sum (fun i _ => mul_nonpos_of_nonneg_of_nonpos (hw i) (hf i).le)
          ⟨ω₀, Finset.mem_univ _, mul_neg_of_pos_of_neg h₀ (hf ω₀)⟩
    _ = 0 := Finset.sum_const_zero

end Aux

/-- Reading R1 (forward): quotients that are not a finitely additive probability admit a
Dutch book. -/
theorem dutchBook_R1 {Ω : Type*} [Fintype Ω] (q : Set Ω → ℝ)
    (hq : ¬ IsFinitelyAdditiveProb q) :
    ∃ book : List (Bet Ω), IsDutchBook q book := by
  rcases Aux.not_fap_cases hq with ⟨A, hA⟩ | hU | ⟨A, B, hAB, hne⟩
  · refine ⟨[⟨A, -1⟩], fun ω => ?_⟩
    rw [Aux.book_neg]
    have := Set.indicator_nonneg (s := A) (f := fun _ => (1 : ℝ)) (fun _ _ => zero_le_one) ω
    linarith
  · refine ⟨[⟨Set.univ, q Set.univ - 1⟩],
      Aux.isDutchBook_of_const (c := -(q Set.univ - 1) ^ 2)
        (fun ω => by rw [Aux.book_univ]; ring) ?_⟩
    have := sq_pos_of_ne_zero (sub_ne_zero.mpr hU)
    linarith
  · refine ⟨[⟨A ∪ B, q (A ∪ B) - (q A + q B)⟩, ⟨A, -(q (A ∪ B) - (q A + q B))⟩,
        ⟨B, -(q (A ∪ B) - (q A + q B))⟩],
      Aux.isDutchBook_of_const (c := -(q (A ∪ B) - (q A + q B)) ^ 2)
        (fun ω => by rw [Aux.book_additivity q hAB]; ring) ?_⟩
    have := sq_pos_of_ne_zero (sub_ne_zero.mpr hne)
    linarith

/-- Reading R2 (the rough converse): finitely additive probability quotients admit no
Dutch book. -/
theorem converse_R2 {Ω : Type*} [Fintype Ω] (q : Set Ω → ℝ)
    (hq : IsFinitelyAdditiveProb q) :
    ¬ ∃ book : List (Bet Ω), IsDutchBook q book := by
  rintro ⟨b, hb⟩
  have hrep : q = pointMass (fun ω => q {ω}) := funext (Aux.represent hq)
  have hsum := Aux.weights_sum hq
  have hneg := Aux.weighted_neg (fun ω => hq.nonneg _) hsum hb
  have h0 := expected_netPayoff_pointMass hsum b
  rw [← hrep] at h0
  linarith

/-- Reading R3 (both directions, one formulation). -/
theorem dutchBook_R3 {Ω : Type*} [Fintype Ω] (q : Set Ω → ℝ) :
    (∃ book : List (Bet Ω), IsDutchBook q book) ↔ ¬ IsFinitelyAdditiveProb q := by
  exact ⟨fun ⟨b, h⟩ hq => converse_R2 q hq ⟨b, h⟩, dutchBook_R1 q⟩

end MathAgents.P3DutchBook
