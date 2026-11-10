# Problem card: P4 thirty divides n⁵ − n

Stage 0 intake, 2026-10-16. The structured choices are in `preferences.toml` (D32); this card must
agree with them, and any later change to either lapses a G-FID approval (`intake_sha256`). P4 is the measured
dossier of the M6 pilot (D43): staged agentteams_runner writes on Claude, against an interleaved baseline.

- **Source:** Posed by the operator at intake (Jim, 2026-10-16). It is a standard number-theory exercise; no
  citation is claimed, and the dossier makes no literature claim.
- **Informal statement:** "For every integer n, 30 divides n⁵ − n."
- **Domain:** competition
- **Object logic:** classical-hol
- **Engine:** lean-builtin
- **Reading:** R1, R2

Readings (each its own theorem):
- **R1:** for every integer n, 30 ∣ n⁵ − n (over ℤ).
- **R2:** for every natural number n, 30 ∣ n⁵ − n (over ℕ, with truncated subtraction; harmless since n ≤ n⁵, which
  the fidelity review should confirm the formal statement respects).

The fidelity policy offers an operator kernel-as-judge waiver for this toy lemma (`preferences.toml`
`[fidelity]`); by default the operator still reviews the statement at G-FID.
