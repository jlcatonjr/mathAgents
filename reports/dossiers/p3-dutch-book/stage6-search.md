# P3 Stage 6 counterexample search (@counterexample-hunter)

2026-10-01. No candidates; nothing logged in `counterexamples.json`. Solver results are hints only (D6,
DD-16); the statements' truth rests on the Stage 5 kernel proofs.

- **Small instances by hand:** empty Ω (R2's hypothesis is contradictory; R1 holds vacuously with the empty
  book), q ∅ ≠ 0 (one bet on ∅ loses), q A < 0, q univ ≠ 1 and failed additivity each give an explicit
  sure-loss book; repeated events and zero stakes behave as expected.
- **converse_R2 (z3 5.1.0):** for |Ω| = 1, 2, 3, q free on every subset subject to the three axioms, every
  multiset of 1–3 events with free real stakes, net payoff < 0 in every state: unsat in all cases
  (9, 34 and 164 event tuples).
- **dutchBook_R1 (z3, bounded):** q violating some axiom with no Dutch book among ≤ 3 distinct events
  (encoded by Gordan's alternative, a state distribution per family): unsat for n = 1, 2, 3 (3, 14 and 92
  families), i.e. a Dutch book of ≤ 3 bets always exists, consistent with R1. (A bounded search cannot
  refute an existence claim.)
