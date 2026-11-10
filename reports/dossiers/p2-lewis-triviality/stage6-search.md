# P2 Stage 6 counterexample search (@counterexample-hunter)

2026-10-01. No candidates; nothing logged in `counterexamples.json`. Solver results are hints only (D6,
DD-16); the statements' truth rests on the Stage 5 kernel proofs.

- **triviality_R2 by hand:** F1 reduces to P(C ⊓ X) = P C and F2 to P(Cᶜ ⊓ X) = 0 for X = cond A C (both
  denominators positive), so additivity gives P X = P C; the argument order in `FactorizationAt` matches.
- **triviality_R2 (z3 5.1.0):** the 16-element algebra of subsets of 4 atoms, P by non-negative atom weights
  summing to 1 (zero weights cover smaller and degenerate algebras), X = cond A C a free element (so the
  conditional table is arbitrary); all 4096 triples (A, C, X) with F1, F2 (denominators cleared), the two
  positivity hypotheses and P X ≠ P C: unsat.
