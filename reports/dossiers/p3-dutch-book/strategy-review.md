# P3 Stage 2 strategy review (@adversarial, DD-9)

Review of `strategy.md`, 2026-10-01, persisted from the reviewer's report.

- **Case split and books (algebra checked):** `not_fap_cases` recovers exactly the three fields (nonneg,
  univ_eq_one, union_of_disjoint); books (a) [⟨A,−1⟩] pays q A − 1_A ≤ q A < 0; (b) [⟨univ,d⟩] pays
  d(1 − q univ) = −d²; (c) the additivity book pays −d² for disjoint A, B. q ∅ ≠ 0 is caught by (c) with
  A = B = ∅; |Ω| = 1 needs nothing special.
- **Low:** §1(b) says (b) "covers an empty Ω"; any case works there (every book is trivially a Dutch book
  on an empty Ω). Wording only.
- **Low:** `Set.setOf_mem_eq` is deprecated at the pinned Mathlib; use the replacement name.
- **Low:** R2 needs `funext` to turn the per-event `represent` into q = pointMass w before rewriting.
- **Info:** use `Finset.sum_indicator_subset` right to left, with `coe_filter_univ`.
- **Representation route sound;** `weighted_neg` needs no `Nonempty` (∑ w = 1 forces a positive weight);
  not circular (R3 uses only R1 and R2). No new hypotheses, no change to an approved statement.
- **Names spot-checked:** present (`prod_le_one`, `prod_lt_prod`, `prod_mulIndicator_subset`,
  `mulIndicator_union_of_disjoint`, `mulIndicator_of_notMem`, `Finset.coe_filter_univ`, `Finset.coe_insert`,
  `Set.insert_eq`, `Set.disjoint_singleton_left`, …); primed forms deprecated and avoided.

Verdict: CLEARED
Strategy sha256: 52f9c8762431f2978c0d087544ad2ec41356b6c8d2c50b128394be747a849187
