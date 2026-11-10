# Problem card: P2 Lewis triviality

Stage 0 intake, 2026-10-01. The structured choices are in `preferences.toml` (D32); this card must
agree with them, and any later change to either lapses a G-FID approval (`intake_sha256`).

- **Source:** Statement of record (D29: the primary text, Lewis 1976, *The Philosophical Review* 85, doi 10.2307/2184045, is paywalled and the operator has no access): the Triviality Theorem (Lewis) as stated in Egré and Rott, "The Logic of Conditionals", *Stanford Encyclopedia of Philosophy* (Summer 2026 edition), https://plato.stanford.edu/archives/sum2026/entries/logic-conditionals/ — quoted verbatim below and in `interpretation.md` §1. The retrieved entry has no section headings; the theorem follows its statements of Stalnaker's Hypothesis and the Factorization Hypothesis. Fidelity to Lewis's own wording is an open item until a primary copy is available.
- **Informal statement:** "If \(A\) is probabilistically compatible with both \(C\) and \(\neg C\), that is, if \(\Pr(A\wedge C)>0\) and \(\Pr(A\wedge \neg C)>0\), then \(\Pr(A>C)=\Pr(C)\)." (Egré and Rott 2026, verbatim with LaTeX as served)
- **Domain:** philosophy-of-science
- **Object logic:** classical-hol
- **Engine:** lean-builtin, z3
- **Reading:** R2, R3:all, R3:closed-under-conditioning

Hypothesis choices (G-AX-P2-1 to P2-5 and P2-12) are in `preferences.toml` `[gax]`. The Stage 1 draft
(`statement.md`) lists further candidates for the operator's review at G-FID.
