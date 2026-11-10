import Mathlib.Order.BooleanAlgebra.Basic
import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith

/-!
# P2: Lewis's triviality theorem

Statement of record: the SEP version (Egré and Rott 2026), per charter D29.
Object logic `classical-hol`: the conditional `>` is an uninterpreted binary operation `cond` on a
Boolean algebra `α`, which is therefore closed under it (G-AX-P2-3). See
`reports/dossiers/p2-lewis-triviality/statement.md`.
-/

namespace MathAgents.P2LewisTriviality

variable {α : Type*} [BooleanAlgebra α]

/-- G-AX-P2-1: `P` is a finitely additive probability function on the Boolean algebra `α`. -/
def IsFinAddProb (P : α → ℝ) : Prop :=
  (∀ a, 0 ≤ P a) ∧ (∀ a, P a ≤ 1) ∧ P ⊤ = 1 ∧
    ∀ a b, Disjoint a b → P (a ⊔ b) = P a + P b

/-- G-AX-P2-2: `condProb P C A` is `Pr(C | A) = Pr(A ∧ C) / Pr(A)`; used only when `Pr(A) > 0`. -/
noncomputable def condProb (P : α → ℝ) (C A : α) : ℝ :=
  P (A ⊓ C) / P A

/-- One instance of the Factorization Hypothesis, with its proviso:
`Pr(A ∧ B) > 0 → Pr(B > C | A) = Pr(C | A ∧ B)`. -/
def FactorizationAt (cond : α → α → α) (P : α → ℝ) (A B C : α) : Prop :=
  0 < P (A ⊓ B) → condProb P (cond B C) A = condProb P C (A ⊓ B)

/-- Stalnaker's Hypothesis for one `P`: for every conditional `A > C`, possibly complex,
`Pr(A > C) = Pr(C | A)` provided `Pr(A) > 0`. -/
def StalnakerHyp (cond : α → α → α) (P : α → ℝ) : Prop :=
  ∀ A C : α, 0 < P A → P (cond A C) = condProb P C A

/-- A class `K` of functions is closed under conditioning: conditioning a member on any `B` of
positive probability yields a member. -/
def ClosedUnderConditioning (K : Set (α → ℝ)) : Prop :=
  ∀ P ∈ K, ∀ B : α, 0 < P B → (fun X => condProb P X B) ∈ K

namespace Aux

theorem prob_bot {P : α → ℝ} (hP : IsFinAddProb P) : P ⊥ = 0 := by
  obtain ⟨-, -, -, hadd⟩ := hP
  have h := hadd ⊥ ⊥ disjoint_bot_left
  rw [sup_idem] at h
  linarith

theorem prob_mono {P : α → ℝ} (hP : IsFinAddProb P) : ∀ a b : α, a ≤ b → P a ≤ P b := by
  intro a b hab
  obtain ⟨hnn, -, -, hadd⟩ := hP
  have h := hadd a (b \ a) disjoint_sdiff_self_right
  rw [sup_sdiff_cancel_right hab] at h
  linarith [hnn (b \ a)]

theorem expansion {P : α → ℝ} (hP : IsFinAddProb P) : ∀ C X : α, P X = P (C ⊓ X) + P (Cᶜ ⊓ X) := by
  intro C X
  obtain ⟨-, -, -, hadd⟩ := hP
  have h := hadd (X ⊓ C) (X ⊓ Cᶜ) (Disjoint.mono inf_le_right inf_le_right disjoint_compl_right)
  rw [sup_inf_inf_compl, inf_comm X C, inf_comm X Cᶜ] at h
  exact h

theorem pos_of_inf_pos {P : α → ℝ} (hP : IsFinAddProb P) :
    ∀ a b : α, 0 < P (a ⊓ b) → 0 < P a ∧ 0 < P b := by
  intro a b h
  exact ⟨lt_of_lt_of_le h (prob_mono hP _ _ inf_le_left),
    lt_of_lt_of_le h (prob_mono hP _ _ inf_le_right)⟩

theorem condProb_inf_self {P : α → ℝ} {C A : α} (h : P (C ⊓ A) ≠ 0) :
    condProb P C (C ⊓ A) = 1 := by
  have e : C ⊓ A ⊓ C = C ⊓ A := by rw [inf_right_comm, inf_idem]
  unfold condProb
  rw [e]
  exact div_self h

theorem condProb_compl_inf {P : α → ℝ} (hP : IsFinAddProb P) (C A : α) :
    condProb P C (Cᶜ ⊓ A) = 0 := by
  have e : Cᶜ ⊓ A ⊓ C = ⊥ := by rw [inf_right_comm, compl_inf_self, bot_inf_eq]
  unfold condProb
  rw [e, prob_bot hP, zero_div]

theorem stalnaker_closed_implies_factorization {cond : α → α → α} {P : α → ℝ} {A : α}
    (hA : 0 < P A) (hS : StalnakerHyp cond (fun X => condProb P X A)) :
    ∀ B C, FactorizationAt cond P A B C := by
  intro B C hAB
  have hB : 0 < condProb P B A := div_pos hAB hA
  have h := hS B C hB
  simp only at h
  rw [h]
  unfold condProb
  rw [div_div_div_cancel_right₀ (ne_of_gt hA), inf_assoc]

theorem condProb_isFinAddProb {P : α → ℝ} {B : α} (hP : IsFinAddProb P) (hB : 0 < P B) :
    IsFinAddProb (fun X => condProb P X B) := by
  obtain ⟨hnn, -, -, hadd⟩ := id hP
  refine ⟨fun x => div_nonneg (hnn _) (le_of_lt hB),
    fun x => div_le_one_of_le₀ (prob_mono hP _ _ inf_le_left) (le_of_lt hB), ?_, fun x y hxy => ?_⟩
  · show P (B ⊓ ⊤) / P B = 1
    rw [inf_top_eq, div_self (ne_of_gt hB)]
  · show P (B ⊓ (x ⊔ y)) / P B = P (B ⊓ x) / P B + P (B ⊓ y) / P B
    rw [inf_sup_left, hadd _ _ (Disjoint.mono inf_le_right inf_le_right hxy), add_div]

end Aux

/-- Reading R2: one fixed `Pr` satisfying the two Factorization instances the proof uses. -/
theorem triviality_R2 (cond : α → α → α) (P : α → ℝ) (hP : IsFinAddProb P) (A C : α)
    (hF₁ : FactorizationAt cond P C A C) (hF₂ : FactorizationAt cond P Cᶜ A C)
    (hAC : 0 < P (A ⊓ C)) (hAnC : 0 < P (A ⊓ Cᶜ)) :
    P (cond A C) = P C := by
  have hCA : 0 < P (C ⊓ A) := by rwa [inf_comm]
  have hCcA : 0 < P (Cᶜ ⊓ A) := by rwa [inf_comm]
  have hPC := (Aux.pos_of_inf_pos hP C A hCA).1
  have hPCc := (Aux.pos_of_inf_pos hP Cᶜ A hCcA).1
  have h1 := hF₁ hCA
  rw [Aux.condProb_inf_self (ne_of_gt hCA)] at h1
  unfold condProb at h1
  rw [div_eq_one_iff_eq (ne_of_gt hPC)] at h1
  have h2 := hF₂ hCcA
  rw [Aux.condProb_compl_inf hP] at h2
  unfold condProb at h2
  have h2' : P (Cᶜ ⊓ cond A C) = 0 := by
    rcases div_eq_zero_iff.mp h2 with h | h
    · exact h
    · exact absurd h (ne_of_gt hPCc)
  rw [Aux.expansion hP C (cond A C), h1, h2', add_zero]

/-- Reading R3:all: Stalnaker's Hypothesis holds for every finitely additive `Pr` on `α`. -/
theorem triviality_R3_all (cond : α → α → α)
    (hS : ∀ P : α → ℝ, IsFinAddProb P → StalnakerHyp cond P) :
    ∀ P : α → ℝ, IsFinAddProb P → ∀ A C : α,
      0 < P (A ⊓ C) → 0 < P (A ⊓ Cᶜ) → P (cond A C) = P C := by
  intro P hP A C hAC hAnC
  have hPC := (Aux.pos_of_inf_pos hP C A (by rwa [inf_comm])).1
  have hPCc := (Aux.pos_of_inf_pos hP Cᶜ A (by rwa [inf_comm])).1
  have F1 := Aux.stalnaker_closed_implies_factorization hPC
    (hS _ (Aux.condProb_isFinAddProb hP hPC)) A C
  have F2 := Aux.stalnaker_closed_implies_factorization hPCc
    (hS _ (Aux.condProb_isFinAddProb hP hPCc)) A C
  exact triviality_R2 cond P hP A C F1 F2 hAC hAnC

/-- Reading R3:closed-under-conditioning: Stalnaker's Hypothesis holds for every member of a
class of probability functions closed under conditioning. -/
theorem triviality_R3_closed (cond : α → α → α) (K : Set (α → ℝ))
    (hK : ∀ P ∈ K, IsFinAddProb P) (hclosed : ClosedUnderConditioning K)
    (hS : ∀ P ∈ K, StalnakerHyp cond P) :
    ∀ P ∈ K, ∀ A C : α,
      0 < P (A ⊓ C) → 0 < P (A ⊓ Cᶜ) → P (cond A C) = P C := by
  intro P hPK A C hAC hAnC
  have hP := hK P hPK
  have hPC := (Aux.pos_of_inf_pos hP C A (by rwa [inf_comm])).1
  have hPCc := (Aux.pos_of_inf_pos hP Cᶜ A (by rwa [inf_comm])).1
  have F1 := Aux.stalnaker_closed_implies_factorization hPC (hS _ (hclosed P hPK C hPC)) A C
  have F2 := Aux.stalnaker_closed_implies_factorization hPCc (hS _ (hclosed P hPK Cᶜ hPCc)) A C
  exact triviality_R2 cond P hP A C F1 F2 hAC hAnC

end MathAgents.P2LewisTriviality
