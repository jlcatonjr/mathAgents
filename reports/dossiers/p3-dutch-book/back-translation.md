# P3 back-translation (Stage 1, @fidelity-auditor)

Independent back-translation of the three Stage 1 statements, dispatched by the orchestrator with the
declaration names only (DD-26). Advisory input to G-FID; it does not judge any statement faithful.
Persisted from the auditor's report, 2026-10-01. Fingerprints are from the G-KERNEL report of that date.

**Independence:** yes, with a caveat: the Lean docstrings and the library's module header were visible,
but the back-translation was written from the code before any dossier file was opened.

## Shared back-translation (definitions unfolded)

Ω is any type with finitely many elements, possibly empty; q assigns a real number to every subset of Ω
(the events are the whole power set, so the only "tautology" is Ω itself).

- `IsFinitelyAdditiveProb q`: q(A) ≥ 0 for every A; q(Ω) = 1; q(A∪B) = q(A)+q(B) for disjoint A, B
  (these force q(∅) = 0).
- A bet is (A, S): any subset A, any real stake S (positive, negative or zero). The agent's payoff in
  state ω is S·(1_A(ω) − q(A)): the agent pays S·q(A) and receives S if A happens; S > 0 is buying,
  S < 0 selling, at the single price q(A).
- A book is any finite list of bets (repeated events, bets on ∅ or Ω, and zero stakes allowed); its net
  payoff is the sum.
- `IsDutchBook q book`: the agent's net payoff is strictly negative in every state.
- Edge cases: if Ω is empty then ∅ = Ω, no q satisfies the axioms, and every book (even the empty one)
  is trivially a Dutch book; if Ω is non-empty the empty book is not. A bet on ∅ pays −S·q(∅), so it
  alone is a Dutch book whenever q(∅) ≠ 0.

## `MathAgents.P3DutchBook.dutchBook_R1` (fingerprint 6372944151975572447)

**Back-translation.** For every finite Ω and every q: if q fails non-negativity, q(Ω) = 1, or pairwise
additivity on disjoint sets, then some finite book at prices q (any stakes) gives the agent a strictly
negative net payoff in every state. Order: ∀Ω ∀q, hypothesis, ∃book (the book may depend on q).

**Drift.**
1. Loss to the agent, versus Vineberg's "net loss to one side" and de Finetti's opponent's sure win
   (pp. 7–8). Immaterial here: flipping every stake's sign negates every payoff, which is available only
   because stakes may take either sign (P3-2).
2. `¬IsFinitelyAdditiveProb` fails one of three conditions on the whole power set; Vineberg's axioms are
   stated on a set X not necessarily closed under the connectives. Non-negativity must be exploited by a
   bet (selling at q(A) < 0); de Finetti never derives it from a betting argument. This matches Vineberg,
   not de Finetti.
3. Books may bet on any event; de Finetti's forward proof bets only on one complete class. Allowing more
   bets makes the existence claim easier to meet: a modelling choice (P3-13), not a hypothesis.
4. Logically equivalent propositions are the same set and so get the same quotient; the survey also
   speaks of sentences and statements. An unstated identification, covered only partly by P3-4.
5. Empty Ω: trivially true there; de Finetti's complete class assumes some state occurs (P3-15).

**G-AX candidates:** P3-11, P3-12, P3-13, P3-14, P3-15, P3-16 (and item 4).
**Matches reading:** R1.

## `MathAgents.P3DutchBook.converse_R2` (fingerprint 6943047732065357242)

**Back-translation.** For every finite Ω and every q that is a finitely additive probability on the power
set: every finite book leaves the agent a net payoff ≥ 0 in at least one state (which state may depend on
the book). If Ω is empty the hypothesis cannot hold.

**Drift.**
1. Only strict books are ruled out (loss in every state). Weak books, losing in some states and breaking
   even in the rest, are not ruled out; with states of probability 0 such books can exist against a
   probability, so the stronger converse would be false. This exclusion comes from P3-6, not from
   Vineberg's wording.
2. Finite Ω and finite books: Vineberg reports counterexamples to the rough converse; P3-5 and P3-7
   confine the statement to a finite setting, where the auditor found nothing matching them. The source
   does not license these restrictions; they are G-AX choices.
3. Books on any events: de Finetti proves sufficiency only for books on one partition (p. 8); this
   statement goes beyond his proof. Kemeny 1955 and Lehman 1955 were not consulted (paywalled, D29).
4. Sign: the same either-sign equivalence as for R1.

**G-AX candidates:** P3-10 (proof route only, not a hypothesis), P3-13, P3-14, P3-15; the restrictions
in items 1–2 are the recorded P3-5, P3-6 and P3-7.
**Matches reading:** R2, within the finite, strict-loss formulation.

## `MathAgents.P3DutchBook.dutchBook_R3` (fingerprint 6965868094698404562)

**Back-translation.** For every finite Ω and every q: a finite Dutch book exists against q exactly when q
is not a finitely additive probability. Logically R1 together with R2's contrapositive. If Ω is empty,
both sides are true.

**Drift.**
1. One shared formulation: bets, books, loss and the axioms are identical in R1 and R2, as R3 asks.
2. The definitions behind R3 are fixed by the recorded preferences (D31), not by a primary text stating
   both directions together over arbitrary books; de Finetti states both together only for a partition
   (pp. 7–8).

**G-AX candidates:** the union of those for R1 and R2.
**Matches reading:** R3.
