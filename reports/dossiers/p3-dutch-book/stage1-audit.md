# P3 Stage 1 hidden-hypothesis audit (@adversarial)

Audit of the three Stage 1 statements and `statement.md`, 2026-10-01. Persisted from the auditor's
report. Proofs were sketched on paper; nothing was compiled for this audit.

**Recommendation: ready for G-FID.** All three statements are true and provable as stated; the wording
fixes it asked for are now in `statement.md`. R2 is not a G-CX target in this formulation.

## Provability (paper sketches)

- **R1 (forward).** By contradiction, one field of `IsFinitelyAdditiveProb` fails, and each failure gives
  a book of at most three bets: q A < 0 → [⟨A, −1⟩] (payoff q A − 1_A ≤ q A < 0); q univ ≠ 1 →
  [⟨univ, −sign(1 − q univ)⟩] (constant payoff −|1 − q univ|); additivity fails for disjoint A, B with
  d = q(A∪B) − qA − qB ≠ 0 → [⟨A∪B, s⟩, ⟨A, −s⟩, ⟨B, −s⟩], s = sign d (net payoff −|d|). Needs neither
  finiteness nor `Nonempty Ω`; does need either-sign stakes (P3-2).
- **R2 (converse).** (1) On finite Ω, q = pointMass (ω ↦ q{ω}), by Finset induction. (2) w ω := q{ω}
  has ∑w = 1 and w ≥ 0. (3) `expected_netPayoff_pointMass` gives ∑ w·net = 0. (4) If net < 0 in every
  state, every term is ≤ 0 and some w ω > 0, so the sum is < 0: contradiction. Non-negativity is
  essential at (4) (w = (2, −1), net = (−1, −2) has weighted sum 0); such a q is not a probability, and
  R1 books it.
- **R3** is R1 together with R2's contrapositive.
- **Empty Ω:** the hypothesis of R2 is contradictory (univ = ∅ forces q ∅ = 0 and q ∅ = 1).
- **De Finetti p. 8:** his Σ pₕGₕ = 0 is `expected_netPayoff_pointMass` restricted to one partition; R2
  widens it to arbitrary books through the representation lemma, which his p. 10 asserts. His
  sufficiency sentence uses pₕ ≥ 0 without stating it; the `nonneg` field supplies it. His forward
  (determinant) argument yields only partition normalization; R1 also covers non-negativity and pairwise
  additivity, beyond his text but true.

## Findings

1. **Medium (documentation): strictness is load-bearing (P3-6).** Under weak sure loss, R2 is false:
   Ω = {a, b}, q{a} = 1, q{b} = 0, the book [⟨{b}, −1⟩] pays 0 at a and −1 at b. R3 holds only under the
   strict notion.
2. **Medium (text):** R2 was described as a possible G-CX target; in this formulation it is a theorem.
   Fixed in `statement.md` and the preferences comment. (Charter D30's original wording is kept as
   history.)
3. **Low:** P3-10 (point-mass representation) is a provable lemma on finite Ω, not a G-AX candidate.
   Reclassified.
4. **Low:** sign convention (P3-14): under either-sign stakes, `payoff_neg_stake` makes "sure loss to the
   agent" and "sure win to the agent" interchangeable, so "to one side" is captured. Optionally add a
   library lemma (∃ loss-book ↔ ∃ win-book).
5. **Low:** the three axiom fields are independent for |Ω| ≥ 2 (q ≡ 0; q ≡ 1; signed weights summing to
   1); for |Ω| = 1 `nonneg` follows from the others. Normalization on `Set.univ` renders "tautology"
   extensionally.
6. **Low:** empty Ω (P3-15): consistent but degenerate; `[Nonempty Ω]` is optional.
7. **Low:** additivity form (P3-12): on a total q, partition normalization is equivalent to binary
   additivity plus q univ = 1; neither implies non-negativity, so `nonneg` stays separate.

No dropped hypotheses. Totality of q (P3-16) narrows the setting relative to de Finetti's arbitrary class
of events and is consistent with P3-4.

## For the operator

Confirm P3-6 strict (required for R2 and R3) and P3-2 either-sign (required for R1); decide P3-15
(`Nonempty Ω`, cosmetic). The other candidates (P3-11 to P3-16) are recorded in `statement.md`.
