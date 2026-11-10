# P2 back-translation (Stage 1, @fidelity-auditor)

Independent back-translation of the three Stage 1 statements, dispatched by the orchestrator with the
declaration names only (DD-26). Advisory input to G-FID; it does not judge any statement faithful.
Persisted verbatim from the auditor's report, 2026-10-01. Fingerprints are from the G-KERNEL report of
that date and change with the Lean source.

**Independence:** partial. The in-file docstrings were visible alongside the code; the auditor wrote
the back-translation from the code, and opened the dossier files only afterwards.

## Common setting

α is a Boolean algebra (⊓ meet, ⊔ join, ᶜ complement, ⊤ top, `Disjoint a b` ⇔ a ⊓ b = ⊥).
`cond : α → α → α` is an arbitrary function (no properties). `P : α → ℝ`; `IsFinAddProb P`: 0 ≤ P ≤ 1,
P ⊤ = 1, and P(a ⊔ b) = P a + P b for disjoint a, b. `condProb P C A` = P(A ⊓ C) / P A; Lean's x/0 = 0
is never relied on, because every use is guarded (in `FactorizationAt`, 0 < P(A ⊓ B) forces P A > 0 by
monotonicity). On the trivial algebra (⊤ = ⊥) no finitely additive P exists, so all three theorems are
vacuously true there; harmless.

## `MathAgents.P2LewisTriviality.triviality_R2`

**Back-translation.** For every Boolean algebra α, every `cond`, every P with `IsFinAddProb P`, and all
A, C ∈ α: assume
(F1) if P(C⊓A) > 0 then P(C ⊓ cond A C)/P C = P(C⊓A⊓C)/P(C⊓A), i.e. Pr(A>C | C) = Pr(C | C∧A);
(F2) if P(Cᶜ⊓A) > 0 then P(Cᶜ ⊓ cond A C)/P Cᶜ = P(Cᶜ⊓A⊓C)/P(Cᶜ⊓A), i.e. Pr(A>C | ¬C) = Pr(C | ¬C∧A);
P(A⊓C) > 0 and P(A⊓Cᶜ) > 0. Then P(cond A C) = P C. All variables are bound outermost (one P);
Stalnaker's Hypothesis is not assumed.

**Drift.**
1. Only two Factorization instances, for one fixed P, versus the SEP's Factorization "for every
   probability function … for all sentences A and B": a narrowed hypothesis (weaker hypothesis, stronger
   theorem). G-AX-P2-12 (answered: one-fixed-Pr) and G-AX-P2-13 (open).
2. Conclusion P(cond A C) = P C matches the SEP's Pr(A>C) = Pr(C).
3. Non-vacuity (auditor's own check): `cond A C := C` satisfies F1 and F2 for every P, and positive
   P(A⊓C), P(A⊓Cᶜ) are achievable in a four-atom algebra.
4. Propositions are elements of a Boolean algebra, so `cond` respects logical equivalence; the SEP speaks
   of sentences. Hidden-hypothesis candidate (G-AX-P2-17).

**Matches reading:** R2.

## `MathAgents.P2LewisTriviality.triviality_R3_all`

**Back-translation.** For every α and every `cond`: suppose that for every P : α → ℝ with
`IsFinAddProb P` and all A, C with P A > 0, P(cond A C) = P(A⊓C)/P A. Then for every such P and all A, C
with P(A⊓C) > 0 and P(A⊓Cᶜ) > 0, P(cond A C) = P C. `cond` is fixed first; the hypothesis is ∀P; the
conclusion is ∀P ∀A ∀C; A ranges over all of α, conditionals included.

**Drift.**
1. The hypothesis is Stalnaker's Hypothesis only; Factorization, from which the SEP says Lewis derives
   the result, is not a hypothesis. It is derivable here (P(·|B) is again finitely additive), so dropping
   it makes the theorem stronger, not unfaithful. G-AX-P2-14.
2. "Every probability function" is read as every finitely additive α → ℝ on the one fixed α. G-AX-P2-7.
3. ∀ A C in `StalnakerHyp` matches "every conditional A>C, possibly complex". G-AX-P2-15.
4. Vacuity (unverified inference from Lewis's further result): on any α with three pairwise-disjoint
   non-⊥ elements the hypothesis is probably unsatisfiable, so the theorem has content only on algebras of
   at most four elements; `statement.md` discloses this. The conclusion is the SEP's Pr(A>C) = Pr(C), not
   "only trivial algebras admit such a cond".
5. Congruence of `cond`, as for R2.

**Matches reading:** R3:all.

## `MathAgents.P2LewisTriviality.triviality_R3_closed`

**Back-translation.** For every α, every `cond` and every set K of functions α → ℝ, assume every member
of K is finitely additive; for every P ∈ K and every B with P B > 0, X ↦ P(B⊓X)/P B is in K; every
P ∈ K satisfies Stalnaker's Hypothesis. Then for every P ∈ K and all A, C with P(A⊓C) > 0 and
P(A⊓Cᶜ) > 0, P(cond A C) = P C.

**Drift.**
1. Closure of K under conditioning is not stated by the source: an added hypothesis, and the one that
   defines this reading. G-AX-P2-6.
2. "Every probability function" relativized to a class K. G-AX-P2-7.
3. Degenerate classes: K = ∅ (disclosed), or K = {P} with P a 0/1 measure (closed, Stalnaker holds with
   `cond A C := C`, but the conclusion's antecedent can never hold); harmless.
4. Factorization dropped, as for R3:all (G-AX-P2-14); congruence of `cond` (G-AX-P2-17).
5. With K the set of all finitely additive P, this theorem implies R3:all.

**Matches reading:** R3:closed-under-conditioning.

## Other findings

- The problem card agrees with `preferences.toml` (readings, object logic, G-AX choices P2-1 to P2-5 and
  P2-12), and each encoding follows its answered choice.
- No coercions, ℕ/ℤ truncation, Finset/Fintype or decidability hazards in the three statements.
- A classical shallow encoding with the conditional uninterpreted is consistent with `classical-hol`.
