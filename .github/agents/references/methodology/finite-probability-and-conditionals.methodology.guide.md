<!-- AGENTTEAMS:BEGIN content v=1 -->
# Finite probability and conditionals — Interpretive Methodology Guide

> **Purpose:** Guide the interpretation of results about probability functions on finite
> algebras of propositions and the probability of conditionals: methodological commitments,
> provenance, and shaping conflicts. Serves the pilots P2 (Lewis triviality) and P3 (finite
> Dutch book).
> **Applies to:** `reports/dossiers/p2-lewis-triviality/`, `reports/dossiers/p3-dutch-book/`, and
> any later dossier that declares a probabilistic or conditional object logic.
> **Relationship:** Reasoning reference, **NOT authoritative**; one interpretation among
> several. Not a citation database.
> **Authority Position:** Complements `orchestrator.agent.md`; does not supersede.
> **Commissioned by:** `@interpretation-advisor` · **Authored by:** `@content-enricher` (role
> performed by the orchestrator) · **Maintenance owner:** `@agent-updater`
> **Audited by:** `@reference-manager` (existence) + `@technical-validator` (claim ledger)
> + `@adversarial` (selection) + `@conflict-auditor` (contradictions/boundary)
> **Epistemic Status:** interpretation, contested.
> **status:** provisional
> **Last audited:** 2026-10-01 UTC by `@conflict-auditor` (verdict: not yet active; findings fixed in this revision)

---

## Surveys the tradition superset was drawn from

This superset **inherits a single survey's canon per topic**, with that survey's blind spots:

- **Conditionals:** Egré and Rott 2026 (SEP, "The Logic of Conditionals"), retrieved as an
  excerpt. The canon in the retrieved passages runs through Adams, Stalnaker, Lewis, Bradley,
  Hájek, Égré and Cozic, Charlow, and Gärdenfors. Exclusions beyond the elided passages are
  unknown.
- **Dutch Books:** Vineberg 2022 (SEP, "Dutch Book Arguments"), retrieved as an excerpt. The
  canon in the retrieved passages runs through Ramsey, de Finetti, Kemeny, Lehman, Hájek, Skyrms,
  Teller and Lewis, and the authors of depragmatized arguments. Exclusions beyond the elided
  passages are unknown.

Neither survey is neutral. A second independent survey per topic is an open item.

## Traditions / Schools

| School | Core methodological commitment | Philosophy-of-science source | Key figures | Canonical texts (citation keys) | Standard of evidence |
|--------|-------------------------------|------------------------------|-------------|----------------------------------|----------------------|
| Probability of conditionals (Adams) | the probability of a simple conditional equals the conditional probability [P2C6] | Egré and Rott 2026 | Adams | primary not retrieved | from inside Adams's logic, a definition [P2C29] |
| Stalnaker's Hypothesis | extends that identity to conditionals of arbitrary complexity [P2C4] | Egré and Rott 2026 | Stalnaker | primary not retrieved; `Lewis1976` is existence only | the triviality results bear on it [P2C10] |
| Pragmatic reading of the Dutch Book | incoherent credences lead to bad consequences [P3C18] | Vineberg 2022 | (as the survey attributes) Ramsey, de Finetti | `deFinetti1937` existence only | betting behaviour |
| Consistency (logical-defect) reading | incoherence as a kind of logical defect, not a pragmatic defect per se [P3C19]; depragmatized versions [P3C20] | Vineberg 2022 | (as the survey attributes) Ramsey, per Skyrms | primary not retrieved | consistency, not loss |

Kemeny appears in this guide only as one of the two people the survey credits with independently
proving the converse theorem [P3C9]. His record is abstract only, and the theorem statement was not
retrieved [P3C24]. He is not assigned to either school.

## Genealogy (lineage to foundational figures)

> Every arrow is the cited survey's assertion, with the validated ledger row in brackets. None is
> stated as settled fact.

- Stalnaker's Hypothesis → named for Stalnaker, who formulates it in his 1970 article (per Egré and Rott 2026) [P2C18].
- Lewis 1976 → shows that, under assumptions on the probability of nested conditionals, the thesis leads to triviality (per Egré and Rott 2026) [P2C10].
- Lewis → assumes the Factorization Hypothesis, the label being Fitelson 2015's, and derives the theorem from it (per Egré and Rott 2026) [P2C9, P2C20]. The survey does not tie this derivation to a specific Lewis publication.
- Converse Dutch Book theorem → proven independently by Lehman (1955) and Kemeny (1955) (per Vineberg 2022) [P3C9].
- Dutch Book argument for probabilism → traces to Ramsey's "Truth and Probability" (per Vineberg 2022) [P3C14].
- Consistency reading → attributed to Ramsey by Skyrms (per Vineberg 2022) [P3C19].

## Interpretive nuances (contested terms; evidence bars)

| Term | School X reads it as | School Y reads it as |
|------|----------------------|----------------------|
| Probability of a conditional | conditional probability, for simple conditionals (Adams) [P2C6] | for Stalnaker's conditional, the probability of the consequent under imaging (Lewis) [P2C16] |
| Sure loss | a guaranteed net loss, as the theorem is stated [P3C2] | restricted: a loss not depending on contingent facts, or inflicted by a mechanical formula [P3C12] |
| Normalization | value one for tautologies [P3C1] | value one for logical truths, or for necessary truths [P3C5] |
| Incoherence | a pragmatic liability [P3C18] | a kind of logical defect [P3C19] |

These pairs come from the two surveys. They are not presented as exhaustive binaries: other
readings may exist outside the retrieved passages.

## Conflicts register

| Conflict | Kind (intellectual/methodological/political) | Stakes | Provenance of each side's commitment |
|----------|----------------------------------------------|--------|--------------------------------------|
| Adams's Thesis as definition vs empirical claim | methodological | [editors' inference — unsourced] whether triviality refutes a definition or an empirical thesis | Egré and Rott 2026 [P2C29, P2C30, P2C31] |
| Restrictor view and triviality | intellectual | [editors' inference — unsourced] whether if-clauses escape triviality | Egré and Rott 2026 [P2C33]; which result that passage refers to **cannot be identified from the record** |
| Pragmatic vs consistency reading of the Dutch Book | methodological | [editors' inference — unsourced] what the theorem shows, as opposed to what it states | Vineberg 2022 [P3C18, P3C19, P3C21] |
| Dutch Book vs Czech Book | intellectual | [editors' inference — unsourced] whether the argument cancels out | Vineberg 2022 [P3C17] |

## Interpretive directives (how the team should read this domain's sources)

1. Keep the **mathematical statement** separate from the **normative argument**. Whether a
   normative reading belongs in a formal target is a G-FID decision.
2. Before any formal statement, fix the **bet/payoff definition, axiom formulation, sure-loss
   notion and finiteness** from a primary source. The Dutch Book survey says the theorem and its
   converse are sensitive to these [P3C11]. The conditionals record states no finiteness
   condition and no bet notion for Lewis's theorem.
3. For conditionals, fix whether Pr ranges over a language containing nested conditionals before
   formalizing any triviality statement [P2C4, P2C10].
4. Treat every primary text cited only through a survey as **existence only** until a human
   supplies its statement and its location.

## Verification ledger

| Claim / arrow | Cited source | reference-manager (exists?) | technical-validator (ledger) | Rendered as |
|---------------|-------------|-----------------------------|------------------------------|-------------|
| Adams's Thesis; Stalnaker's Hypothesis; definition vs empirical | Egre2026 | yes (inventory + bibliography) | ledger rows P2C4, P2C6, P2C29–P2C31: validator PASS | sourced (per survey) |
| Lewis 1976 → triviality; Factorization; Fitelson label; Stalnaker 1970 | Egre2026 | yes | P2C9, P2C10, P2C18, P2C20: validator PASS | sourced (per survey) |
| Imaging probability | Egre2026 | yes | P2C16: validator PASS | sourced (per survey) |
| Restrictor view | Egre2026 | yes | P2C33: validator PASS | sourced; referent unidentified |
| Dutch Book theorem and its converse; sensitivity; sure loss; normalization | Vineberg2022 | yes | P3C1, P3C2, P3C3, P3C5, P3C11, P3C12: validator PASS | sourced (per survey) |
| Lehman and Kemeny → converse | Vineberg2022 | yes | P3C9: validator PASS | sourced (per survey) |
| Pragmatic and consistency readings; Czech Book; Ramsey lineage | Vineberg2022 | yes | P3C14, P3C17–P3C21: validator PASS | sourced (per survey) |
| Lewis 1976 | Lewis1976 | yes | P2C35: existence only | existence only |
| de Finetti 1937 | deFinetti1937 | yes | P3C23: existence only | existence only |
| Kemeny 1955 | Kemeny1955 | yes | P3C24: abstract only; theorem statement not retrieved | abstract only |
| Stakes column of the Conflicts register | n/a | n/a | n/a | editors' inference |

The ledger ids refer to `reports/dossiers/<slug>/interpretation.claims.csv`. "Validator PASS"
means `scripts/validate_claim_ledger.py` confirmed that each sentence appears verbatim in its
brief and that each quote appears verbatim in the retrieved SEP text, on 2026-10-01 UTC. A
`@technical-validator` **semantic** review of these rows is still pending.

## Open questions / audit log

- 2026-10-01 UTC: created as **provisional**.
- 2026-10-01 UTC: `@conflict-auditor` returned NO to activation, with 9 findings. This revision
  fixes them:
  - the ledger overclaim (the briefs' stale "pending" status was corrected at the source);
  - directive 2's attribution;
  - per-claim ledger rows;
  - tagged inferences;
  - the split genealogy;
  - the restrictor caveat;
  - Kemeny's status;
  - template structure;
  - UTC dating.
- Pending before activation:
  - a `@technical-validator` semantic review;
  - an `@adversarial` selection review: the single-survey canon; schools that may be dropped
    (Gärdenfors's AGM analogue, Popper-style primitive conditional probability,
    accuracy-dominance arguments); whether the nuance pairs force binaries; Kemeny's placement.
- Open: a second independent survey per topic, and the primary statements of Lewis 1976, de
  Finetti 1937, Kemeny 1955 and Lehman 1955.
<!-- AGENTTEAMS:END content -->
