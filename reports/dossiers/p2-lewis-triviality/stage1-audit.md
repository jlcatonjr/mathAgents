# P2 Stage 1 hidden-hypothesis audit (@adversarial)

Audit of the three Stage 1 statements and `statement.md`, 2026-10-01. Persisted from the auditor's
report. Proofs were checked on paper only; nothing was compiled for this audit.

**Recommendation: ready for G-FID once the editorial fixes are made** (they are now in `statement.md`).
No theorem statement needs revision.

## Provability (paper check)

- **R2.** Expansion gives P(X) = P(C⊓X) + P(Cᶜ⊓X) from finite additivity alone, and positivity makes
  P C, P Cᶜ > 0. hF₁ unfolds to P(C⊓(A>C))/P C = P(C⊓A⊓C)/P(C⊓A) = 1 and hF₂ to
  P(Cᶜ⊓(A>C))/P Cᶜ = 0; adding gives P(A>C) = P C. Helper lemmas: P ⊥ = 0, monotonicity, `inf_comm`.
- **R3:closed.** Condition P on C and on Cᶜ; both stay in K by closure; Stalnaker's Hypothesis at each
  conditioned function yields exactly F1 and F2; the R2 argument finishes.
- **R3:all.** R3:closed with K the set of all finitely additive P, which is closed under ratio
  conditioning (a lemma to prove, not to assume).
- R2 uses exactly the SEP's two displayed Factorization steps (instances (A:=C, B:=A) and (A:=¬C, B:=A));
  the order C∧A versus A∧C is immaterial; the provisos are discharged by the positivity hypotheses.
- Division by zero is never relied on: every `condProb` denominator is guarded.
- Satisfiability: R2's hypotheses hold non-trivially (`cond B C := C`, uniform P on `Set (Fin 4)`); on
  the trivial algebra no finitely additive P exists; on a non-trivial algebra an ultrafilter gives a
  two-valued P.

## Presuppositions challenged

1. **Is R3 still Lewis's theorem? (medium, fidelity)** Yes in substance, but the R3 proof must derive
   Factorization from Stalnaker's Hypothesis through closure under conditioning, which differs from the
   SEP's displayed derivation from Factorization. (The auditor recalls that this is Lewis's own first
   route, but that recollection is unverified; the primary is paywalled, D29, and it anchors no claim
   here.) Plan the Stage 2 lemma `stalnaker_closed_implies_factorization`.
2. **Near-vacuity of R3:all (low; Lewis's own point).** With all finitely additive P, any algebra with
   three pairwise disjoint non-zero elements carries a P violating Stalnaker's Hypothesis, so `hS` holds
   only on algebras of at most four elements. The conclusion Pr(A>C) = Pr(C) undersells "triviality".
3. **Congruence of `cond` (low).** On a Boolean quotient, A ≡ A′ forces A > C = A′ > C; unstated by the
   source; unused by the proof. New candidate G-AX-P2-17.
4. **Editorial:** `statement.md` §5 item 1 wording was backwards; §6 was stale. Fixed.
5. **Info:** the `P a ≤ 1` field of `IsFinAddProb` is redundant (it follows from the others); harmless.
6. Nothing the source states was dropped: both positivity conditions, both provisos, and "possibly
   complex" are present; Expansion is left for Stage 2 to prove (P2-4).

## G-AX candidates for the operator

P2-13 (two Factorization instances only), P2-14 (R3 assumes Stalnaker's Hypothesis only), P2-6 and
P2-7 (what closure means; which class "every Pr" ranges over), P2-15 (Stalnaker's Hypothesis over all A,
C), P2-16 (`cond` unconstrained), and new: P2-17 (congruence of `cond`; Pr respects logical equivalence)
and P2-18 (whether to add the corollary condProb P C A = P C under R3).
