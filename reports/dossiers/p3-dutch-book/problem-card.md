# Problem card: P3 finite Dutch book

Stage 0 intake, 2026-10-01. The structured choices are in `preferences.toml` (D32); this card must
agree with them, and any later change to either lapses a G-FID approval (`intake_sha256`).

- **Source:** Primary, open access: de Finetti, "La prévision : ses lois logiques, ses sources subjectives", *Annales de l'institut Henri Poincaré* 7(1), pp. 1–68 (1937), Chapitre I, quoted verbatim in French with printed page numbers and marked translations in `sources/definetti-1937-extract.md` (D29): the bet and its payoff, stakes of either sign (pp. 6–7, 14); coherence and the sure win it excludes (pp. 7–9); the forward direction for a finite complete class of events (pp. 7–8); the converse, asserted as sufficiency for bets on one partition (pp. 8, 15). Survey statement of record for the general converse (D29: Kemeny 1955 and Lehman 1955 are paywalled), flagged: Vineberg 2022, quoted in `interpretation.md` §1.
- **Informal statement:** Dutch Book theorem: "Given a set of betting quotients that fails to satisfy the probability axioms, there is a set of bets with those quotients that guarantees a net loss to one side" (Vineberg 2022). Converse, "roughly stated": "For a set of betting quotients that obeys the probability axioms, there is no set of bets (with those quotients) that guarantees a sure loss (win) to one side" (Vineberg 2022). Both as formulated in de Finetti 1937, Chapitre I (see the extract).
- **Domain:** philosophy-of-science
- **Object logic:** finite-probability
- **Engine:** lean-builtin, z3
- **Reading:** R1, R2, R3

Hypothesis choices (G-AX-P3-1 to P3-8) are in `preferences.toml` `[gax]`; the extract's table records
how each compares with de Finetti's text. R4 and R5 are deferred (D30).
