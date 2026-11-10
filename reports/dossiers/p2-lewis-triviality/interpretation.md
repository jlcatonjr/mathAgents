# Interpretation Brief — P2 Lewis triviality

> **Commissioned by:** `@interpretation-advisor` · **Written by:** `@primary-producer` · **Drafted:** 2026-10-01
> **Status:** advisory input to Stage 1 only. This brief is not a formal statement and not a fidelity decision, and it calls nothing proved. Selecting a reading is the human G-FID gate's decision.
> **Intake:** Stage 0 intake has not happened for P2. No object logic is declared, so every object-logic entry below reads **intake pending** and names the logic the reading would need. Any divergence from the logic eventually declared goes back to intake.
> **Evidence base:** `references/phase1-evidence/group4.jsonl`, record `Egre2026` only. Every sentence with a parenthetical citation is a row in `interpretation.claims.csv`.
> **Guide drawn on:** `finite-probability-and-conditionals.methodology.guide.md` (status: provisional). Anything taken from it is provisional here too.

**Source framing.** The one named source is a Stanford Encyclopedia of Philosophy survey of the logic of conditionals. The retrieved record is an excerpt, with elisions marked `[...]`, so material between the excerpts is outside this brief. That includes the further variants the entry says Lewis states. The entry is not treated as neutral: it is written from inside the logic-of-conditionals literature and takes positions, for example on why Stalnaker's Hypothesis should fail (section 5).

## 1. Claim and scope

The statement of record is the Triviality Theorem (Lewis) as given in the Stanford Encyclopedia of Philosophy entry "The Logic of Conditionals", which introduces it as a result Lewis derives from Factorization and which "basically expresses that the probability of the conditional collapses to the unconditional probability of its consequent" (Egré and Rott 2026).

> **Triviality Theorem (Lewis)**, verbatim with LaTeX as served: "If \(A\) is probabilistically compatible with both \(C\) and \(\neg C\), that is, if \(\Pr(A\wedge C)>0\) and \(\Pr(A\wedge \neg C)>0\), then \(\Pr(A>C)=\Pr(C)\)."

In plain notation, the theorem says that if Pr(A∧C) > 0 and Pr(A∧¬C) > 0, then Pr(A>C) = Pr(C) (Egré and Rott 2026).

**Location.** The retrieved record has no section headings. The theorem follows the entry's statements of Stalnaker's Hypothesis and the Factorization Hypothesis, and the entry later refers to "Lewis's trivialization (see section 5.2)" (Egré and Rott 2026). [editors' inference — unsourced] That reference suggests, but does not establish, that the theorem sits in section 5.2.

**Hypotheses as the entry states them** (verbatim, LaTeX as served):

> (Stalnaker's Hypothesis) "For every probability function \(\Pr\) and for every conditional \(A>C\), possibly complex: \(\Pr(A>C)=\Pr(C\mkern2mu|\mkern2muA)\), provided that \(\Pr(A)>0\)."
>
> (Factorization Hypothesis) "For every probability function \(\Pr\) and for all sentences \(A\) and \(B\) such that \(\Pr(A\wedge B)>0\): \[\Pr(B >C\mid A)=\Pr(C\mid A\wedge B).\]"

Both hypotheses are stated for every probability function: Stalnaker's Hypothesis for every conditional, possibly complex, under the proviso Pr(A) > 0, and Factorization for all sentences A and B with Pr(A∧B) > 0 (Egré and Rott 2026).

**Proof as displayed.** The entry gives the proof in four displayed lines, labelling the first "(Expansion)" and the second and third "(by Factorization)", which yield Pr(A>C | C) = Pr(C | A∧C) = 1 and Pr(A>C | ¬C) = Pr(C | A∧¬C) = 0 (Egré and Rott 2026).

**Scope, as the record leaves it** [editors' inference — unsourced]:

- The displayed proof cites Expansion and Factorization at its labelled steps and does not cite Stalnaker's Hypothesis at any step.
- The hypotheses quantify over every probability function, while the theorem itself speaks of a single Pr, and the record does not say how the two quantifiers relate.
- The record states neither the probability axioms, nor the definition of conditional probability, nor the domain of Pr, nor any finiteness condition for Lewis's theorem.

## 2. Readings

The readings are listed in the order in which the entry's retrieved passages present the material each one draws on. **That order is not a ranking and sets no default.** No reading is selected here: selection is G-FID's. For each reading the brief gives:

- the object logic it would need (intake pending);
- the hypotheses the entry states, quoted;
- a **G-AX candidate** for every hypothesis the reading needs that the entry does not state;
- a Lean/Mathlib note, which is **UNVERIFIED**.

No Mathlib declaration is named anywhere in this brief, and nothing has been checked against the pinned toolchain.

### R1. Simple-conditional reading (Adams's Thesis)

- **Source support.** Adams's central assumption, as the entry states it, is that for every conditional sentence A>C in which A and C are Boolean sentences, and for every probability function, the probability of the conditional equals the corresponding conditional probability, provided Pr(A) > 0 (Egré and Rott 2026). The entry states that the main limit of Adams's logic is that it does not account for embeddings of conditionals, listing negated conditionals, disjunctions of conditionals, and right-nested and left-nested conditionals (Egré and Rott 2026). It also states that Stalnaker's Thesis is consistent for simple conditionals but fails for conditionals of arbitrary complexity (Egré and Rott 2026).
- **Object logic:** intake pending. The reading needs a language whose conditionals take only Boolean antecedents and consequents, with Pr on conditionals fixed by definition. Whether that is a definitional extension inside `classical-hol` is for intake to decide [editors' inference — unsourced].
- **Explicit hypotheses:** A and C Boolean; Pr(A) > 0.
- **G-AX candidates:** G-AX-P2-1 to G-AX-P2-3 apply. [editors' inference — unsourced] Because Factorization and the proof's second and third lines take the probability of a conditional conditional on a further sentence, this reading may leave the theorem's hypotheses inexpressible rather than true or false. See checklist item 6.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

### R2. Factorization-as-hypothesis reading (one fixed probability function)

- **Source support.** The entry says that Lewis assumes the Factorization Hypothesis, a label it attributes to Fitelson 2015, and that from Factorization Lewis derives the result (Egré and Rott 2026).
- **Reading** [editors' inference — unsourced]: one fixed probability function Pr on a language that contains A>C is assumed to satisfy the instances of Factorization the proof uses and the two positivity conditions. The conclusion is Pr(A>C) = Pr(C) for that Pr.
- **Object logic:** intake pending. The candidates are `classical-hol`, with > as an uninterpreted binary operation on an algebra of sentences or events, or the registered (planned) `stalnaker-conditional` [editors' inference — unsourced].
- **Explicit hypotheses:** Pr(A∧C) > 0 and Pr(A∧¬C) > 0, plus the Factorization proviso Pr(A∧B) > 0 (section 1).
- **G-AX candidates:**
  - **G-AX-P2-1.** The probability axioms Pr satisfies are not stated in the record.
  - **G-AX-P2-2.** The definition of conditional probability, as a ratio or as a primitive, is not stated. The record writes Pr(C | A) with the proviso Pr(A) > 0 but gives no definition.
  - **G-AX-P2-3.** The domain: Pr and conditioning must apply to sentences containing > (for example Pr(A>C | C)), but the record does not specify the language.
  - **G-AX-P2-4.** Expansion is used at the first proof step but not stated.
  - **G-AX-P2-12.** The entry states Factorization "for every probability function", while this reading assumes it of one fixed Pr. Narrowing the quantifier is a change to the stated hypothesis.
  - **G-AX-P2-5.** If Factorization were encoded as an axiom, not as a hypothesis of the theorem statement, it would be an axiom beyond the kernel defaults. It would then need G-AX approval, and `references/axiom-allowlist.json` is currently empty.
- **Lean/Mathlib (UNVERIFIED):** not assessed. No declaration is named.

### R3. Universal reading (Stalnaker's Hypothesis over a class of probability functions)

- **Source support.** The entry reports that Lewis (1976) shows that under rather uncontroversial assumptions on the probability of nested conditionals the thesis leads to triviality (Egré and Rott 2026).
- **Reading** [editors' inference — unsourced]: the hypotheses hold for every member of a class of probability functions on a fixed language, and the theorem is asserted of each member. If that class were closed under conditioning, Factorization would follow from Stalnaker's Hypothesis applied to Pr(· | A); the record does not state such closure. That inference may not anchor any dossier claim.
- **Object logic:** intake pending. Quantifying over probability functions on a language plausibly fits `classical-hol` [editors' inference — unsourced].
- **Explicit hypotheses:** Stalnaker's Hypothesis and its proviso, as quoted in section 1.
- **G-AX candidates:**
  - **G-AX-P2-6.** Closure of the class under conditioning.
  - **G-AX-P2-7.** Which class "every probability function" ranges over: all functions on the language, or a restricted class.
  - G-AX-P2-1 to G-AX-P2-3 also apply.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

### R4. Import-Export reading

- **Source support.** The entry states that, given Stalnaker's Hypothesis, the Factorization Hypothesis is equivalent to the Law of Import-Export, Pr(A>(B>C)) = Pr((A∧B)>C) (Egré and Rott 2026).
- **Reading** [editors' inference — unsourced]: Stalnaker's Hypothesis together with Import-Export stands in for Factorization as the hypothesis set. The stated equivalence is the entry's claim and has not been checked here.
- **Object logic:** intake pending. The language must contain right-nested conditionals. The candidates are `classical-hol` with > as an uninterpreted operation, or the registered (planned) `stalnaker-conditional` [editors' inference — unsourced].
- **G-AX candidates:**
  - **G-AX-P2-8.** As quoted, the Law of Import-Export carries no positivity proviso, unlike Stalnaker's Hypothesis and Factorization. Whether a proviso is intended is not stated.
  - G-AX-P2-1 to G-AX-P2-3 also apply.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

### R5. Preservation reading (Bradley)

- **Source support.** The entry reports that Bradley (2000) shows that a Preservation Condition inspired by Belief Revision theory also leads to triviality, the condition being that for every probability function and all sentences A and C, if Pr(A) > 0 and Pr(C) = 0, then Pr(A>C) = 0 (Egré and Rott 2026). The entry calls the condition weaker than Stalnaker's Thesis, so that it extends triviality to an even wider class of conditionals (Egré and Rott 2026).
- **Object logic:** intake pending. The candidates are the same as for R2: `classical-hol` with > as an uninterpreted operation, or the registered (planned) `stalnaker-conditional` [editors' inference — unsourced].
- **G-AX candidates:**
  - **G-AX-P2-9.** [editors' inference — unsourced] The record states the Preservation Condition but not the triviality conclusion Bradley derives from it, so this reading has no quotable conclusion. Bradley 2000 is not in `reports/references/bibliography.bib`, so a human must supply its statement.
  - G-AX-P2-1 to G-AX-P2-3 also apply.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

### R6. Finite possible-worlds reading (propositions, imaging)

- **Source support.** The entry reports that Hájek (1989) showed there are more distinct conditional probability values than distinct unconditional probability values for any finite set of possible worlds that has at least three worlds with non-zero probability (Egré and Rott 2026). It states that the conditional probability of C given A is not in general equal to the probability of any possible world proposition (Egré and Rott 2026). The entry also reports that Lewis (1976) identifies a revision rule he calls imaging and shows that the probability of Stalnaker's conditional is the probability of the consequent under imaging by the antecedent (Egré and Rott 2026). Imaging, per the entry, shifts the weight of non-A worlds non-uniformly to the A-worlds depending on the selection function (Egré and Rott 2026).
- **Object logic:** intake pending. Stalnaker's selection-function semantics is a conditional logic, registered as **planned** (`stalnaker-conditional`) in `references/object-logics.json`; choosing it over `classical-hol` is **flagged to intake**. The `finite-probability` logic (planned) is a candidate only if finiteness (G-AX-P2-10) is adopted. Another option is a finite classical model in which propositions are sets of worlds, inside `classical-hol` [editors' inference — unsourced].
- **G-AX candidates:**
  - **G-AX-P2-10.** [editors' inference — unsourced] Finiteness of the set of worlds is stated for Hájek's result, not for Lewis's theorem.
  - **G-AX-P2-11.** The properties of the selection function are not stated in the record.
  - G-AX-P2-1 to G-AX-P2-3 also apply.
- **Note.** This reading formalizes related results: Hájek's count and Lewis's imaging result. Whether either counts as "Lewis's triviality" is for G-FID to decide.
- **Lean/Mathlib (UNVERIFIED):** not assessed.

**Possibly unenumerated readings**, for `@adversarial` to audit:

- combinations of R2 to R5 with R6's finite semantics;
- readings drawn from Lewis's own further variants, which are absent from the record;
- the non-probabilistic Gärdenfors analogue, which is listed under variants because it is a distinct theorem;
- [editors' inference — unsourced] "triviality" read as a conclusion about the whole class: every probability function satisfying Stalnaker's Hypothesis is trivial;
- [editors' inference — unsourced] the theorem combined with Stalnaker's Hypothesis, which would yield Pr(C | A) = Pr(C) under the theorem's positivity conditions;
- [editors' inference — unsourced] conditional probability taken as primitive (Popper-style), which changes what the positivity provisos mean.

The last three need human-supplied sources before they can be enumerated as readings.

## 3. Variants and provenance

- Stalnaker's Hypothesis is named for Stalnaker, who formulates it in his 1970 article (per Egré and Rott 2026).
- Lewis (1976) is the work the entry credits with showing that the thesis leads to triviality (per Egré and Rott 2026).
- The label "Factorization Hypothesis" is attributed to Fitelson 2015 (per Egré and Rott 2026).
- Lewis himself states further variants, and several generalizations have been proposed since by Hájek and Hall, Bradley, Milne, and Fitelson (per Egré and Rott 2026). The record does not reproduce Lewis's variants, so a human must supply them from the primary text.
- Bradley's Preservation Condition, which is weaker than Stalnaker's Thesis, also leads to triviality (per Egré and Rott 2026).
- Lewis showed that the probability of Stalnaker's conditional is the probability of the consequent under imaging by the antecedent (per Egré and Rott 2026).
- Gärdenfors noticed that coupling the Ramsey test with the AGM theory of belief revision leads to a trivialization in many respects similar to Lewis's (per Egré and Rott 2026).
- Gärdenfors's theorem, as the entry states it, says that a belief revision model satisfying the AGM postulates (*4) and (*5) and Gärdenfors's Ramsey Test is trivial in the sense that it contains no belief set logically compatible with three pairwise inconsistent sentences A, B and C (per Egré and Rott 2026). Its object logic would be AGM belief revision, which is **not yet registered**; it is listed here as a variant, not a reading.
- **Priority.** The record makes no "first proved" claim about Lewis's theorem, and this brief makes none. Any ordering of these variants by logical strength, beyond the entry's own statement that Bradley's condition is weaker than Stalnaker's Thesis, would be [editors' inference — unsourced] and is not made here.

## 4. Method lineage

The entry presents the method only at the level of the displayed proof: Lewis derives the result from Factorization, and the proof's first line is labelled Expansion (per Egré and Rott 2026). The entry contrasts imaging with conditioning, which kills off the non-A worlds and spreads their mass uniformly over the A-worlds (per Egré and Rott 2026). The record states no proof-system lineage, such as natural deduction or a sequent calculus, for this result, and none is supplied here.

## 5. Interpretive conflicts

- **Truth conditions.** The entry reports that Adams's scepticism about truth conditions for conditionals is shared by Gibbard (1980) and Edgington (1995) and was further fueled by Lewis's (1976) triviality results (Egré and Rott 2026).
- **Definition or empirical claim.** The entry says Adams's Thesis has two sides: from the inner standpoint of Adams' logic of conditionals it may be viewed as a definition, and from the outer standpoint of ordinary English it makes an empirical claim about the assertability of simple conditionals (Egré and Rott 2026). It holds that Adams's Thesis remains coherent for simple conditionals qua definition, whereas, as an empirical thesis, Stalnaker's Hypothesis states a substantive identity between quantities defined separately, and "we now see better why it should fail" (Egré and Rott 2026). Whether Adams' Thesis holds as a matter of empirical fact, even for simple conditionals, is described as still debated (Egré and Rott 2026).
- **What the result exposes.** Lewis's triviality results, in the entry's words, "expose a mismatch" between the conditional probability Pr(C | A) and the probability of the conditional Pr(A>C) (Egré and Rott 2026).
- **Restrictor view.** In a passage separated by an elision from the Hájek result, the entry describes a result as compatible with the idea that if-clauses fundamentally act as restrictors of overt or covert operators, reports that Égré and Cozic (2011) use the result to vindicate that view, and reports that Charlow (2016) argues that the restrictor view is not in itself immune to triviality (Egré and Rott 2026). Which result the passage means cannot be identified from the record.
- **Belief-revision analogue.** Gärdenfors interpreted his theorem basically as a conflict between (*4) or the Preservation Principle on the one hand and the Ramsey Test on the other, reactions were mixed, and no consensus has emerged so far (per Egré and Rott 2026).
- **Stakes** [editors' inference — unsourced]:
  - Under R1 the theorem's nested probabilities may fall outside the language.
  - Under R2 to R5 the result constrains any conditional that satisfies the stated hypotheses.
  - Under R6 the conditional's probability is an imaging probability, not a conditional probability.
  - Each side's commitment is sourced only through the entry's report. The primary texts (Adams, Stalnaker, Gibbard, Edgington, Charlow, Gärdenfors) have not been retrieved.

## 6. Checklist for the Stage 1 fidelity check

These are inputs for `@proof-dossiers-expert` (standing in until `@fidelity-auditor` exists), not verdicts.

1. **Compare the back-translation against the quoted hypotheses:** Pr(A∧C) > 0 and Pr(A∧¬C) > 0; Factorization with its proviso Pr(A∧B) > 0; Stalnaker's Hypothesis with its proviso Pr(A) > 0. Each must appear, or its absence must be justified by the selected reading.
2. **Quantifier scope:** is Pr a single function (R2) or a member of a class quantified over (R3)? The back-translation must make the choice explicit.
3. **Domain of Pr:** does it include nested conditionals (G-AX-P2-3)? Without them, Pr(A>C | C) is not well formed.
4. **Conditional probability:** ratio or primitive (G-AX-P2-2)? This determines the meaning of the positivity provisos.
5. **Trivially true** [editors' inference — unsourced]: if the formal hypotheses are jointly unsatisfiable except in degenerate models, the statement holds vacuously. Also, if Factorization enters as a global axiom (G-AX-P2-5), the conclusion follows in a few lines. Neither situation is fidelity to the source.
6. **Ill-formed or false** [editors' inference — unsourced]: under R1 the statement may be ill-typed. If the positivity conditions are dropped, the conditional probabilities in the proof are undefined or take conventional values, and the conclusion may change.
7. **G-AX candidates to resolve before Stage 1:** G-AX-P2-1 to G-AX-P2-12.
8. **Primary statement:** a human must supply Lewis's own statement, with its location, from the primary text and compare it with the entry's version before the Stage 1 statement is drafted (section 7).

## 7. Verification status

The primary work is David Lewis's article "Probabilities of Conditionals and Conditional Probabilities" in The Philosophical Review (Lewis 1976).

| Work (key) | Evidence layer | `@reference-manager` (existence) | `@technical-validator` (ledger) | Use in this brief |
|---|---|---|---|---|
| Egré and Rott 2026 (`Egre2026`) | `group4.jsonl`, status grounded; SEP page excerpt, retrieved 2026-10-01 | listed in `phase1-source-inventory.csv` and `bibliography.bib`; confirmation pending | `interpretation.claims.csv` validated: `validate_claim_ledger.py` PASS (35 claims), 2026-10-01 UTC | every content claim |
| Lewis 1976 (`Lewis1976`) | `group3.jsonl`, status no-abstract | listed in inventory as verified via Crossref DOI; confirmation pending | existence row only | **existence only; primary text not retrieved.** A human must supply the primary statement and its location before Stage 1. |
| Stalnaker 1970; Fitelson 2015; Bradley 2000; Hájek 1989; Hájek and Hall 1994; Milne 2003; Gibbard 1980; Edgington 1995; Égré and Cozic 2011; Charlow 2016; Gärdenfors 1986 and 1988 | named only inside the `Egre2026` record | not in `bibliography.bib`; existence unverified | not ledgered as keys | named only as the entry's attributions |
| Guide `finite-probability-and-conditionals.methodology.guide.md` | drawn from `group4.jsonl` | n/a | n/a | status: provisional |

No Mathlib or Lean declaration is named in this brief, so there is nothing for the declaration ledger to check.

## References

Egré, Paul, and Hans Rott. 2026. "The Logic of Conditionals." In *The Stanford Encyclopedia of Philosophy*, Summer 2026 ed., edited by Edward N. Zalta and Uri Nodelman. Metaphysics Research Lab, Stanford University. https://plato.stanford.edu/archives/sum2026/entries/logic-conditionals/.

Lewis, David. 1976. "Probabilities of Conditionals and Conditional Probabilities." *The Philosophical Review* 85: 297. https://doi.org/10.2307/2184045.
