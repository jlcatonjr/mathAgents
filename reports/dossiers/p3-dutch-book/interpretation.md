# Interpretation Brief — P3 finite Dutch book

> **Commissioned by:** `@interpretation-advisor` · **Written by:** `@primary-producer` (completed by the orchestrator) · **Drafted:** 2026-10-01
> **Status:** advisory input to Stage 1 only. This brief is not a formal statement and not a fidelity decision, and it calls nothing proved. Selecting a reading is the human G-FID gate's decision.
> **Intake:** Stage 0 intake has not happened for P3. No object logic is declared, so every object-logic entry reads **intake pending**. Any divergence from the logic eventually declared goes back to intake.
> **Evidence base:** `references/phase1-evidence/group4.jsonl`, record `Vineberg2022` only. Every sentence with a parenthetical citation is a row in `interpretation.claims.csv`.
> **Guide drawn on:** `finite-probability-and-conditionals.methodology.guide.md` (status: provisional).

**Source framing.** The one named source is a Stanford Encyclopedia of Philosophy survey of Dutch Book arguments. The retrieved record is an excerpt, with elisions marked `[...]`, and it is not neutral: it takes positions on which readings of the argument remain defensible (section 5).

## 1. Claim and scope

The charter's pilot P3 asks for the finite Dutch Book theorem **in both directions**. The entry states the two directions as separate results.

The entry states the Dutch Book theorem as: "Given a set of betting quotients that fails to satisfy the probability axioms, there is a set of bets with those quotients that guarantees a net loss to one side" (Vineberg 2022).

It states the Converse Dutch Book theorem, "roughly stated", as: "For a set of betting quotients that obeys the probability axioms, there is no set of bets (with those quotients) that guarantees a sure loss (win) to one side" (Vineberg 2022).

The entry gives the basic axioms, for A in X, as non-negativity 0 ≤ pr(A), normalization (if A is a tautology then pr(A) = 1), and finite additivity (if A and B are incompatible then pr(A∨B) = pr(A) + pr(B)) (Vineberg 2022).

The conclusion of the basic argument, per the entry, is that the credences an agent attaches to the members of a set X of propositions, or sometimes statements or sentences, should satisfy the axioms of probability (Vineberg 2022).

**Scope, as the record leaves it** [editors' inference — unsourced]:

- The entry calls its statement of the converse rough, and gives no precise statement of either direction beyond the quoted sentences.
- The record does not state whether X is closed under the connectives that the axioms mention (tautologies, disjunctions of incompatible members).
- The payoff structure of a bet is given only through the pragmatic presentation quoted in section 2, because the entry's canonical form falls in an elided passage.

## 2. Readings

The readings are listed in the order in which the entry's retrieved passages present the material each one draws on. **That order is not a ranking and sets no default.** No reading is selected here: selection is G-FID's. No Mathlib declaration is named, and nothing has been checked against the pinned toolchain.

### R1. Forward direction only (incoherent quotients admit a Dutch Book)

- **Source support.** For each axiom, the entry says, the individual bets in the book are fair, having expected value zero when calculated with the agent's betting quotients, yet collectively produce a sure loss (Vineberg 2022).
- **Object logic:** intake pending. Candidates are `classical-hol`, or the registered (planned) `finite-probability`, with a real-valued quotient function [editors' inference — unsourced]. If normalization (2'') for necessary truths is chosen, a modal notion of necessity is needed (`modal-k`, planned); that divergence is **flagged to intake**.
- **Explicit hypotheses:** the quotients fail at least one of the axioms in section 1.
- **G-AX candidates:**
  - **G-AX-P3-1.** The canonical form of a bet and its payoff function. The entry assumes, with de Finetti, that a bet on a proposition H has a canonical form, but the canonical form itself falls in a passage elided from the retrieved record (Vineberg 2022).
  - **G-AX-P3-2.** Bet direction and stake sign. The pragmatic presentation assumes that an agent with degree of belief q in M finds a bet on or against M at the corresponding odds acceptable, which with stake S amounts to willingness to take either direction of a bet costing Sq that pays S if M and 0 otherwise (Vineberg 2022). Whether stakes may be negative, or both directions are separately available, must be fixed explicitly.
  - **G-AX-P3-3.** Which normalization axiom applies. The entry notes that Condition 2 is sometimes replaced by requiring pr(A) = 1 for every logical truth, or even for every necessary truth (Vineberg 2022).
  - **G-AX-P3-4.** The structure of X (closure under the connectives the axioms use), which the record does not state.
  - **G-AX-P3-7.** Whether X itself is finite, which the record does not state.
  - **G-AX-P3-8.** Which bets the agent accepts: fair only, or fair or favorable, as in Hájek's reformulation reported by the entry.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

### R2. Converse direction only (coherent quotients admit no Dutch Book)

- **Source support.** The entry reports that the Converse Dutch Book theorem was proven independently by Lehman (1955) and Kemeny (1955) (Vineberg 2022). Kemeny and Lehman, per the entry, restrict the allowable bets, for example to a finite number of bets, which seems to rule out the counterexamples, though it remains to be shown that avoiding book with such a restricted set suffices to justify the axioms (Vineberg 2022).
- **Object logic:** intake pending, as R1.
- **G-AX candidates:**
  - **G-AX-P3-5.** The restriction to finitely many bets is stated only as an example ("for example") of the Kemeny–Lehman restrictions; the full restriction must come from the primary texts.
  - **G-AX-P3-6.** The notion of sure loss. One response the entry reports restricts 'sure loss' to losses that do not depend on contingent facts, or to losses for which there is a mechanical formula for inflicting them (Vineberg 2022).
  - G-AX-P3-1 to G-AX-P3-4 also apply.
- **Counterexamples.** The entry also refers to "the sort of counterexample to the Converse Dutch Book theorem with which we began" and to "the need to strengthen the axioms" (Vineberg 2022). [editors' inference — unsourced] The rough converse as quoted may therefore be false without restrictions; see R4 and R5.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

### R3. Both directions as a biconditional

- **Source support.** Both the theorem and its converse are, per the entry, sensitive to the formulation of the axioms and to the understanding of 'bet', 'sure loss', and what it means for such a loss to be guaranteed (Vineberg 2022). The entry observes that the converse states that adhering to the axioms assures that one will not be susceptible to a sure loss, rather than the minimal claim that such vulnerability may be avoided (Vineberg 2022).
- **Reading** [editors' inference — unsourced]: the pilot's "both directions" combines R1 and R2 into one statement under a single, shared formulation of the axioms, bets and sure loss. The entry's sensitivity warning means the two directions may hold under different formulations, and the biconditional only under a common one.
- **G-AX candidates:** all of G-AX-P3-1 to G-AX-P3-9, which must be resolved **jointly** so that one formulation serves both directions.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

### R4. Converse with strengthened axioms

- **Source support.** The entry mentions "the need to strengthen the axioms" in connection with counterexamples to the converse (section R2); that strengthening is one way to remove them is [editors' inference — unsourced]. The strengthened axioms themselves fall outside the retrieved record.
- **Object logic:** intake pending; candidate `finite-probability` (planned) [editors' inference — unsourced].
- **G-AX candidates:** **G-AX-P3-9.** The strengthened axioms must be supplied from a primary source. G-AX-P3-1 to G-AX-P3-8 also apply.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

### R5. Converse with a restricted notion of sure loss

- **Source support.** One response the entry reports restricts 'sure loss' to losses that do not depend on contingent facts, or to losses for which there is a mechanical formula for inflicting them (Vineberg 2022).
- **Object logic:** intake pending; candidate `finite-probability` (planned) [editors' inference — unsourced].
- **G-AX candidates:** G-AX-P3-6 (which notion), plus G-AX-P3-1 to G-AX-P3-8.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

**Possibly unenumerated readings**, for `@adversarial` to audit:

- readings over sentences or statements rather than propositions, which the entry mentions as alternatives;
- countably additive or infinite-bet versions, which the record does not discuss;
- the diachronic conditionalization argument, which is listed under variants because it is a distinct result.

## 3. Variants and provenance

- The entry traces the argument for probabilism to Ramsey's "Truth and Probability", where the point was mentioned only in passing (Vineberg 2022).
- De Finetti, as the entry attributes it to his 1937 work, identified degrees of belief with betting quotients and called credences susceptible to a Dutch Book incoherent and those not susceptible coherent (Vineberg 2022).
- The entry reports a diachronic Dutch Book argument for conditionalization constructed by Lewis and first reported by Teller, and a converse theorem attributed to Skyrms (Vineberg 2022). It is a distinct, diachronic result and is not a reading of P3.
- The entry describes Hájek's "Czech Book Argument", which parallels the Dutch Book argument with the conclusion that one ought to violate the probability calculus, and reports Hájek's reformulation assuming that the agent should accept bets that are either fair or favorable (Vineberg 2022).
- **Priority.** The record says Lehman and Kemeny proved the converse independently; this brief makes no other priority claim.

## 4. Method lineage

The retrieved record presents no proof of either direction and no proof-system lineage, so none is supplied here.

## 5. Interpretive conflicts

- **Pragmatic reading.** The argument has often been presented as showing that credences violating the axioms are irrational because they can or do lead to bad consequences (Vineberg 2022).
- **Logical (consistency) reading.** A popular response, per the entry, holds that incoherence is not a pragmatic defect per se and that the Dutch Book is a dramatic device for illustrating a kind of logical defect, a reading Skyrms attributes to Ramsey (Vineberg 2022). Depragmatized versions seek to establish coherence as a consistency constraint without presupposing any definite connection between degrees of belief and preference (Vineberg 2022).
- **What incoherence costs.** It also states that the trouble with incoherence cannot be that it will lead to losses, but that it opens one up to sure losses in a way coherent beliefs do not, given an appropriate version of the converse theorem (Vineberg 2022).
- **The entry's own position.** The entry concludes that it remains defensible that the argument shows the axioms to be something like consistency constraints on partial belief, at least given some substantial decision-theoretic assumptions (Vineberg 2022).
- **Stakes** [editors' inference — unsourced]: these conflicts concern what the theorem *shows*, not only what it *states*. Whether any normative reading belongs in the formal target is a decision for G-FID, not for this brief.

## 6. Checklist for the Stage 1 fidelity check

These are inputs for `@proof-dossiers-expert` (standing in until `@fidelity-auditor` exists), not verdicts.

1. **Bet and payoff definition** (G-AX-P3-1, G-AX-P3-2) must be fixed from a primary source before any formal statement.
2. **Axiom formulation** (G-AX-P3-3): normalization for tautologies, logical truths, or necessary truths.
3. **Sure loss** (G-AX-P3-6): contingent-fact-independent, formula-based, or plain; one notion must serve both directions under R3.
4. **Finiteness** (G-AX-P3-5, G-AX-P3-7): finitely many bets, and whether X itself is finite.
5. **Trivially true** [editors' inference — unsourced]: if "guarantees a net loss" is defined so that every book loses, or the bet class is empty, the statement holds vacuously.
6. **False as stated:** the entry reports counterexamples to the rough converse (R2). Without the restrictions of R4 or R5, a formalized converse may be false, and the counterexample track (G-CX) applies.
7. **Primary statement:** a human must supply the statements from de Finetti 1937, Kemeny 1955, and Lehman 1955 with locations before Stage 1 (section 7).

## 7. Verification status

One primary work named for this result is de Finetti's 1937 paper (de Finetti 1937). Another is Kemeny's "Fair Bets and Inductive Probabilities", whose abstract opens with the question of what constitutes fairness in betting quotients (Kemeny 1955).

| Work (key) | Evidence layer | Use in this brief |
|---|---|---|
| Vineberg 2022 (`Vineberg2022`) | `group4.jsonl`, grounded; SEP excerpt retrieved 2026-10-01 UTC; `interpretation.claims.csv` validated PASS (25 claims) | every content claim |
| de Finetti 1937 (`deFinetti1937`) | `group3.jsonl`, no-abstract | **existence only; primary text not retrieved** |
| Kemeny 1955 (`Kemeny1955`) | `group3.jsonl`, grounded (CrossRef abstract only) | abstract cited once (P3C24); **the theorem statement itself was not retrieved** |
| Lehman 1955; Ramsey 1926; Hájek 2005, 2008; Skyrms 1987; Teller 1973; Lewis 1999; Christensen; Howson and Urbach; Hellman | named only inside the `Vineberg2022` record | not in the bibliography; named only as the entry's attributions |

No Mathlib or Lean declaration is named in this brief.

## References

de Finetti, Bruno. 1937. "La prévision : ses lois logiques, ses sources subjectives." *Annales de l'institut Henri Poincaré* 7. http://www.numdam.org/item/AIHP_1937__7_1_1_0/.

Kemeny, John G. 1955. "Fair Bets and Inductive Probabilities." *Journal of Symbolic Logic* 20: 263–73. https://doi.org/10.2307/2268222.

Vineberg, Susan. 2022. "Dutch Book Arguments." In *The Stanford Encyclopedia of Philosophy*, Fall 2022 ed., edited by Edward N. Zalta and Uri Nodelman. Metaphysics Research Lab, Stanford University. https://plato.stanford.edu/archives/fall2022/entries/dutch-book/.
