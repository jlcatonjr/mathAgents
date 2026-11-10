<!-- AGENTTEAMS:BEGIN content v=1 -->
# Elementary number theory — Interpretive Methodology Guide

> **Purpose:** Guide how elementary number theory problems are read and formalized: the proof-method families, the contested points in turning informal statements into formal ones, and the directives that follow from them. Serves dossier `p4-thirty-divides-n5-minus-n`.
> **Applies to:** elementary number theory problems (divisibility, congruences, small-modulus identities, competition exercises) formalized under `classical-hol` in Lean 4/Mathlib; `reports/dossiers/p4-thirty-divides-n5-minus-n/` and any later dossier of this kind.
> **Relationship:** Reasoning reference, **NOT authoritative**; one interpretation among
> several. Not a citation database.
> **Authority Position:** Complements `orchestrator.agent.md`; does not supersede.
> **Commissioned by:** `@interpretation-advisor` (approved in session by the operator, 2026-10-16) · **Authored by:** `@content-enricher`
> · **Maintenance owner:** `@agent-updater`
> **Audited by:** `@reference-manager` (existence) + `@technical-validator` (claim ledger)
> + `@adversarial` (selection) + `@conflict-auditor` (contradictions/boundary)
> **Epistemic Status:** interpretation, contested; **unsourced**.
> **status:** provisional            <!-- provisional | active -->
> **Last audited:** 2026-10-16, not audited (pending `@reference-manager`, `@technical-validator`, `@adversarial`)

---

## Surveys the tradition superset was drawn from

- **None.** This guide draws on no survey, handbook, textbook, article or author. The "tradition superset" below is the editors' own grouping of proof-method families, so it has whatever blind spots the editors have. The guide is **unsourced and provisional**. Every substantive statement carries the tag [editors' inference — unsourced].

## Traditions / Schools

This section treats "schools" loosely as proof-method families, not as historical schools of thought. [editors' inference — unsourced]

| School | Core methodological commitment | Philosophy-of-science source | Key figures | Canonical texts (citation keys) | Standard of evidence |
|--------|-------------------------------|------------------------------|-------------|----------------------------------|----------------------|
| Case analysis on residues | reduce the claim to finitely many residue classes modulo m and check each class [editors' inference — unsourced] | none claimed | none named | none | the reduction to residues is proved, and every case is closed by the kernel [editors' inference — unsourced] |
| Fermat/Euler-style exponent arguments | use a known exponent identity modulo a prime (or modulus) to collapse powers [editors' inference — unsourced] | none claimed | none named | none | the identity used is a kernel-checked library or project lemma, with its hypotheses (primality, coprimality) discharged [editors' inference — unsourced] |
| Factor the modulus into coprime parts | prove divisibility by each pairwise coprime factor, then combine [editors' inference — unsourced] | none claimed | none named | none | coprimality is proved explicitly, and the combining step is a named lemma [editors' inference — unsourced] |
| Polynomial factorization (consecutive-integer products) | factor the expression so that it contains a product of consecutive integers, then use divisibility of such products [editors' inference — unsourced] | none claimed | none named | none | the factorization is proved as a ring identity in the stated type [editors' inference — unsourced] |
| Induction | induct on n, using a binomial-style expansion of the step difference [editors' inference — unsourced] | none claimed | none named | none | the step identity holds in the stated type, which matters most under ℕ subtraction [editors' inference — unsourced] |

## Genealogy (lineage to foundational figures)

> Every arrow is EITHER `A → B (per <Author Year>, <work>)` OR
> `A → B [editors' inference — unsourced]`. No arrow is stated as settled fact.

- **None claimed.** These method families are treated as folklore, and the guide asserts no provenance, attribution or lineage for them. [editors' inference — unsourced]

## Historical setting (periods, chronology, text versions)

> Per `docs/historical-context-protocol.md`.

| Period | Dates (basis) | Categories not to read back into it | Text-version cautions |
|--------|---------------|-------------------------------------|-----------------------|
| none claimed | none (no source) | n/a | n/a; competition statements should be taken from the problem card as recorded at intake [editors' inference — unsourced] |

## Interpretive nuances (contested terms; evidence bars)

| Term | Reading A | Reading B | Why it matters |
|------|-----------|-----------|----------------|
| Subtraction | ℕ truncated subtraction (a − b = 0 when b > a) | ℤ subtraction | the two readings can differ in truth value and in proof route; whether truncation ever applies to a given target must be checked, not assumed [editors' inference — unsourced] |
| "m divides x" | divisibility m ∣ x | congruence x ≡ 0 (mod m), or an identity in ZMod m | these are different formal statements; their equivalence must be proved (or cited as a confirmed declaration), not assumed [editors' inference — unsourced] |
| Coercion placement | cast each atom and then operate, e.g. ((n:ℤ)^5 − n) | operate in ℕ and then cast the result | different placements give different statements under truncation [editors' inference — unsourced] |
| Quantifier scope | ∀ n in the stated domain (ℕ or ℤ) | a fixed n, a bounded range, or a different domain | domain and scope belong to the statement, not the proof, and are a G-FID matter [editors' inference — unsourced] |
| Literal constants | the numeral as written (e.g. 30) in the intended type | a factored or re-typed form (2·3·5, or a literal elaborated in a different type) | a rewritten constant is a different statement until it is proved equal [editors' inference — unsourced] |

## Conflicts register

| Conflict | Kind (intellectual/methodological/political) | Stakes | Provenance of each side's commitment |
|----------|----------------------------------------------|--------|--------------------------------------|
| ℕ versus ℤ formalization | methodological | fidelity to the informal "n" versus convenience of proof [editors' inference — unsourced] | none claimed |
| Kernel-checked decision procedures versus `native_decide` | methodological | `native_decide` places trust outside the kernel and is excluded by project policy [editors' inference — unsourced] | project policy, as stated in the commission |
| Residue enumeration versus structural proof | methodological | whether brute-force case checks count as an explanation in the dossier narration [editors' inference — unsourced] | none claimed |

## Interpretive directives (how the team should read this domain's sources)

1. Fix the carrier type (ℕ or ℤ) at intake and record it on the problem card. If the target uses ℕ subtraction, state whether truncation is ever active, and prove that claim rather than assert it. [editors' inference — unsourced]
2. Treat divisibility, congruence and ZMod formulations as **distinct statements**. Any switch between them is a proved step with a named lemma, and the lemma's name must be confirmed against the pinned name index. [editors' inference — unsourced]
3. Write coercions explicitly in the formal statement, and check their placement against the informal statement during G-FID back-translation. [editors' inference — unsourced]
4. Check quantifier scope and domain in the back-translation. A statement proved for a bounded range or a single instance is not the universal claim. [editors' inference — unsourced]
5. Keep literal constants as written. Any refactoring of a constant (e.g. 30 into 2·3·5) is an internal proof step, never part of the target statement. [editors' inference — unsourced]
6. For finite instances, prefer `decide`, `omega` or `norm_num`. Do not use `native_decide`, which per project policy is outside the trusted kernel. [editors' inference — unsourced]
7. Flag vacuity. If truncation makes a target trivially true (for example, an expression that is 0 for every input), report it as a fidelity finding and do not count it as proved content. [editors' inference — unsourced]
8. This guide names no Mathlib declarations. Every declaration used must be confirmed against the pinned name index (`python3 scripts/lean_docs.py`), never taken from memory. [editors' inference — unsourced]
9. Anachronism guard: not applicable, since the guide claims no historical sources. Text-version caution applies only to the recorded competition statement. [editors' inference — unsourced]

## Verification ledger

| Claim / arrow | Cited source | reference-manager (exists?) | technical-validator (ledger) | Rendered as |
|---------------|-------------|-----------------------------|------------------------------|-------------|
| all statements in this guide | none | n/a | n/a | editors' inference |

There are **no sourced claims** in this guide. Every row is editors' inference, and none has been reviewed by `@technical-validator`. [editors' inference — unsourced]

## Open questions / audit log

- 2026-10-16: created as **provisional** at `@interpretation-advisor`'s commission for `p4-thirty-divides-n5-minus-n`, which the operator approved in session.
- Pending before activation: `@reference-manager` (confirm that no references are claimed), `@technical-validator` (semantic review of the nuances and directives), and `@adversarial` (selection review: whether the five method families are exhaustive and whether the nuance pairs force false binaries).
- Open: whether any survey should be drawn on to source this guide; this needs a verified entry in `reports/references/bibliography.bib` first.
<!-- AGENTTEAMS:END content -->
