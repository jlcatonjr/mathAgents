import Mathlib

/-!
# Finite probability (object logic `finite-probability`, charter D31)

A classical theory of probability on a finite state space, built as the foundation for the
P3 finite Dutch book pilot.

## Design

* **Events are `Set Ω`** over a finite state type `Ω` (`[Fintype Ω]`). `Set Ω` is a complete
  Boolean algebra, so `∪`, `ᶜ`, `\`, `⊆`, `univ`, `∅` are available with Mathlib's lattice
  lemmas and no decidability side conditions. Membership tests in sums and payoffs are expressed
  through `Set.indicator`, which is noncomputable but needs no `DecidablePred` instance; this keeps
  every statement free of instance arguments that would otherwise have to be threaded through
  (and made to agree) in each lemma. `payoff_eq_ite` recovers the `if ω ∈ A then 1 else 0` form.
  `Finset Ω` was rejected because it forces `DecidableEq Ω` and decidable predicates into every
  event-level statement for no gain in a purely propositional (non-computational) theory.
* **Probability** is a predicate `IsFinitelyAdditiveProb pr` on `pr : Set Ω → ℝ`
  (non-negativity, normalization, finite additivity on disjoint pairs).
* **Point-mass probabilities** `pointMass w A = ∑ ω, A.indicator w ω` for a weighting
  `w ≥ 0`, `∑ w = 1`; these are finitely additive probabilities (`pointMass_isFinitelyAdditiveProb`).
* **Bets and books**: a `Bet` is an event with a real stake of either sign; a book is a
  `List (Bet Ω)`; `IsDutchBook q book` means sure loss for the agent holding quotients `q`.

## D31 G-AX choices encoded (reports/dossiers/p3-dutch-book/preferences.toml, `gax`)

1. Bet on `A` at quotient `q` with stake `S` pays `S · (1_A − q)` (`payoff`).
2. Stakes of either sign (`Bet.stake : ℝ`); `payoff_neg_stake` shows the sign flip is the
   counter-party's side of the same fair bet.
3. Normalization `pr ⊤ = 1` for the tautology (`pr Set.univ = 1`).
4. `X` = finite Boolean algebra: events are subsets of a finite state type `Ω`.
5. Finitely many bets: a book is a finite `List`.
6. Sure loss = net payoff strictly negative in every state (`IsDutchBook`).
7. Fair bets: the quotient is both buying and selling price (one `q` for both stake signs);
   at coherent point-mass quotients every bet and every book has expectation `0`
   (`expected_payoff_pointMass`, `expected_netPayoff_pointMass`).

The Dutch book theorems themselves are deliberately not stated here.
-/

namespace MathAgents.FiniteProbability

open Finset

variable {Ω : Type*}

/-! ## Finitely additive probabilities -/

/-- `pr` is a finitely additive probability on the events (subsets) of `Ω`. -/
structure IsFinitelyAdditiveProb (pr : Set Ω → ℝ) : Prop where
  nonneg : ∀ A, 0 ≤ pr A
  univ_eq_one : pr Set.univ = 1
  union_of_disjoint : ∀ A B, Disjoint A B → pr (A ∪ B) = pr A + pr B

namespace IsFinitelyAdditiveProb

variable {pr : Set Ω → ℝ} (h : IsFinitelyAdditiveProb pr)
include h

theorem empty : pr ∅ = 0 := by
  have := h.union_of_disjoint ∅ ∅ (disjoint_bot_left)
  simp only [Set.union_empty] at this
  linarith

theorem compl (A : Set Ω) : pr Aᶜ = 1 - pr A := by
  have := h.union_of_disjoint A Aᶜ disjoint_compl_right
  rw [Set.union_compl_self, h.univ_eq_one] at this
  linarith

theorem diff_of_subset {A B : Set Ω} (hAB : A ⊆ B) : pr (B \ A) = pr B - pr A := by
  have := h.union_of_disjoint A (B \ A) Set.disjoint_sdiff_right
  rw [Set.union_sdiff_cancel hAB] at this
  linarith

theorem mono {A B : Set Ω} (hAB : A ⊆ B) : pr A ≤ pr B := by
  have := h.diff_of_subset hAB
  have := h.nonneg (B \ A)
  linarith

theorem le_one (A : Set Ω) : pr A ≤ 1 := by
  have := h.mono (Set.subset_univ A)
  rwa [h.univ_eq_one] at this

theorem union_add_inter (A B : Set Ω) : pr (A ∪ B) + pr (A ∩ B) = pr A + pr B := by
  have h1 : pr (A ∪ B) = pr A + pr (B \ A) := by
    rw [← h.union_of_disjoint A (B \ A) Set.disjoint_sdiff_right, Set.union_sdiff_self]
  have h2 : pr B = pr (B \ A) + pr (A ∩ B) := by
    rw [← h.union_of_disjoint (B \ A) (A ∩ B) ?_]
    · congr 1; ext x; by_cases hx : x ∈ A <;> simp [hx]
    · rw [Set.disjoint_left]; intro x hx hx'; exact hx.2 hx'.1
  linarith

end IsFinitelyAdditiveProb

/-! ## Point-mass probabilities -/

/-- The event function induced by a weighting `w` of the states: `pointMass w A = ∑_{ω ∈ A} w ω`. -/
noncomputable def pointMass [Fintype Ω] (w : Ω → ℝ) (A : Set Ω) : ℝ :=
  ∑ ω, A.indicator w ω

theorem pointMass_isFinitelyAdditiveProb [Fintype Ω] {w : Ω → ℝ}
    (hw : ∀ ω, 0 ≤ w ω) (hsum : ∑ ω, w ω = 1) :
    IsFinitelyAdditiveProb (pointMass w) where
  nonneg A := Finset.sum_nonneg fun ω _ => Set.indicator_nonneg (fun ω _ => hw ω) ω
  univ_eq_one := by simp [pointMass, hsum]
  union_of_disjoint A B hAB := by
    simp only [pointMass, Set.indicator_union_of_disjoint hAB, Finset.sum_add_distrib]

/-! ## Bets, books, payoffs -/

/-- A bet on the event `event` with real `stake` (either sign). -/
structure Bet (Ω : Type*) where
  event : Set Ω
  stake : ℝ

/-- Payoff in state `ω` of bet `b` at betting quotients `q`: `S · (1_A(ω) − q A)`. -/
noncomputable def payoff (q : Set Ω → ℝ) (b : Bet Ω) (ω : Ω) : ℝ :=
  b.stake * (b.event.indicator (fun _ => (1 : ℝ)) ω - q b.event)

theorem payoff_eq_ite (q : Set Ω → ℝ) (b : Bet Ω) (ω : Ω) [Decidable (ω ∈ b.event)] :
    payoff q b ω = b.stake * ((if ω ∈ b.event then 1 else 0) - q b.event) := by
  simp [payoff, Set.indicator_apply]

theorem payoff_of_mem (q : Set Ω → ℝ) (b : Bet Ω) {ω : Ω} (hω : ω ∈ b.event) :
    payoff q b ω = b.stake * (1 - q b.event) := by
  simp [payoff, hω]

theorem payoff_of_not_mem (q : Set Ω → ℝ) (b : Bet Ω) {ω : Ω} (hω : ω ∉ b.event) :
    payoff q b ω = -(b.stake * q b.event) := by
  simp [payoff, hω]

/-- Reversing the sign of the stake is taking the other side of the same fair bet. -/
theorem payoff_neg_stake (q : Set Ω → ℝ) (A : Set Ω) (S : ℝ) (ω : Ω) :
    payoff q ⟨A, -S⟩ ω = -payoff q ⟨A, S⟩ ω := by
  simp [payoff]

theorem payoff_add_stake (q : Set Ω → ℝ) (A : Set Ω) (S T : ℝ) (ω : Ω) :
    payoff q ⟨A, S + T⟩ ω = payoff q ⟨A, S⟩ ω + payoff q ⟨A, T⟩ ω := by
  simp only [payoff]; ring

/-- Net payoff in state `ω` of a (finite) book of bets at quotients `q`. -/
noncomputable def netPayoff (q : Set Ω → ℝ) (book : List (Bet Ω)) (ω : Ω) : ℝ :=
  (book.map fun b => payoff q b ω).sum

@[simp] theorem netPayoff_nil (q : Set Ω → ℝ) (ω : Ω) : netPayoff q [] ω = 0 := rfl

@[simp] theorem netPayoff_cons (q : Set Ω → ℝ) (b : Bet Ω) (book : List (Bet Ω)) (ω : Ω) :
    netPayoff q (b :: book) ω = payoff q b ω + netPayoff q book ω := by
  simp [netPayoff]

@[simp] theorem netPayoff_append (q : Set Ω → ℝ) (b₁ b₂ : List (Bet Ω)) (ω : Ω) :
    netPayoff q (b₁ ++ b₂) ω = netPayoff q b₁ ω + netPayoff q b₂ ω := by
  simp [netPayoff]

theorem netPayoff_singleton (q : Set Ω → ℝ) (b : Bet Ω) (ω : Ω) :
    netPayoff q [b] ω = payoff q b ω := by
  simp

/-- A Dutch book against the quotients `q`: the book yields a sure loss (strictly negative
net payoff in every state) to the agent holding `q`. -/
def IsDutchBook (q : Set Ω → ℝ) (book : List (Bet Ω)) : Prop :=
  ∀ ω, netPayoff q book ω < 0

theorem not_isDutchBook_nil [Nonempty Ω] (q : Set Ω → ℝ) : ¬ IsDutchBook q [] := by
  intro h
  obtain ⟨ω⟩ := ‹Nonempty Ω›
  simpa using h ω

/-! ## Expected payoff at coherent point-mass quotients -/

/-- Key lemma for the converse direction: if the quotients are the point-mass probability of a
weighting `w` with total mass `1`, every bet has `w`-expected payoff `0`. -/
theorem expected_payoff_pointMass [Fintype Ω] {w : Ω → ℝ} (hsum : ∑ ω, w ω = 1) (b : Bet Ω) :
    ∑ ω, w ω * payoff (pointMass w) b ω = 0 := by
  have key : ∀ ω, w ω * payoff (pointMass w) b ω
      = b.stake * (b.event.indicator w ω - w ω * pointMass w b.event) := by
    intro ω
    by_cases hω : ω ∈ b.event <;> simp [payoff, hω] <;> ring
  simp only [key, ← Finset.mul_sum, Finset.sum_sub_distrib, ← Finset.sum_mul, hsum]
  simp [pointMass]

/-- Every finite book has `w`-expected net payoff `0` at the point-mass quotients of `w`. -/
theorem expected_netPayoff_pointMass [Fintype Ω] {w : Ω → ℝ} (hsum : ∑ ω, w ω = 1)
    (book : List (Bet Ω)) :
    ∑ ω, w ω * netPayoff (pointMass w) book ω = 0 := by
  induction book with
  | nil => simp
  | cons b book ih =>
    simp only [netPayoff_cons, mul_add, Finset.sum_add_distrib, ih,
      expected_payoff_pointMass hsum, add_zero]

end MathAgents.FiniteProbability
