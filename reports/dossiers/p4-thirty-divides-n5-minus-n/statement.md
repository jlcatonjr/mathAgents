# Stage 1 statement — P4 thirty divides n⁵ − n

> **Drafted by:** `@statement-formalizer` · 2026-10-18 · **Status:** draft for the human G-FID review. Nothing here is claimed correct, faithful or proved; every Lean body is `sorry`.
> **Lean stub:** `lean/MathAgentsWIP/P4ThirtyDividesN5MinusN.lean`, namespace `MathAgents.P4ThirtyDividesN5MinusN`, importing only `Mathlib.Algebra.Ring.Int.Defs`. Object logic `classical-hol`; engine `lean-builtin`.
> **Pin (R6):** Lean 4.34.1 (`lean/lean-toolchain`); Mathlib `d13f23b723b8a846827a245b89c10fc7d3f11612` (inputRev v4.34.1, `lean/lake-manifest.json`).
> **Readings formalized (`readings.selected`):** R1, R2. R3 is not selected and is not formalized.

## 0. Source text

Quoted from `problem-card.md` (operator-posed at intake, 2026-10-16; no citation claimed):

- **Informal statement:** "For every integer n, 30 divides n⁵ − n."
- **R1:** "for every integer n, 30 ∣ n⁵ − n (over ℤ)."
- **R2:** "for every natural number n, 30 ∣ n⁵ − n (over ℕ, with truncated subtraction; harmless since n ≤ n⁵, which the fidelity review should confirm the formal statement respects)."

## 1. Common setting

No definitions are introduced; the stub uses only core/Mathlib `∣` (`Dvd.dvd`), `^` (`HPow` with a `ℕ` exponent) and `-` (`HSub`). There are no hypotheses and no parameters besides the universally quantified n.

## 2. Theorems

### `thirty_dvd_pow_five_sub_self_int_R1` (reading R1)

For every n ∈ ℤ, there exists k ∈ ℤ with n⁵ − n = 30 · k; the subtraction is integer subtraction.

```lean
theorem thirty_dvd_pow_five_sub_self_int_R1 :
    ∀ n : ℤ, (30 : ℤ) ∣ n ^ 5 - n
```

### `thirty_dvd_pow_five_sub_self_nat_R2` (reading R2)

For every n ∈ ℕ, there exists k ∈ ℕ with n⁵ ∸ n = 30 · k, where ∸ is truncated subtraction on ℕ (a ∸ b = 0 when a < b). The operand order is n⁵ first, n second.

```lean
theorem thirty_dvd_pow_five_sub_self_nat_R2 :
    ∀ n : ℕ, (30 : ℕ) ∣ n ^ 5 - n
```

Full names: `MathAgents.P4ThirtyDividesN5MinusN.thirty_dvd_pow_five_sub_self_int_R1` and `MathAgents.P4ThirtyDividesN5MinusN.thirty_dvd_pow_five_sub_self_nat_R2`.

## 3. Formalization hazards (checklist)

- **H1 Truncated subtraction (R2).** R2 relies on `Nat.sub` truncation by the problem card's own choice. The term is `n ^ 5 - n` (n⁵ minus n, never `n - n ^ 5`, which would be 0 for every n : ℕ and so would make R2 trivially true). Whether n ≤ n⁵ holds for all n : ℕ, so that truncation never fires, is for the G-FID review to confirm; this draft does not rely on it and adds no hypothesis for it. R1 uses total integer subtraction. No division appears.
- **H2 Coercions.** None. In R1 the binder, both literals and the subtraction are in `ℤ`; in R2 all are in `ℕ`. No `↑`/`Nat.cast`/`Int.toNat` appears; in particular, R1 does not quantify over ℕ cast into ℤ, and R2 does not compute in ℤ.
- **H3 The `∣` notation.** `∣` is the divisibility relation `Dvd.dvd` (U+2223), not the ASCII `|`; `a ∣ b` means ∃ c, b = a * c in the stated type. Divisibility, not a congruence or a `ZMod 30` identity, matches the source's "divides".
- **H4 Literal types.** `30` is written `(30 : ℤ)` in R1 and `(30 : ℕ)` in R2, so its type is explicit. The exponent `5` is a `ℕ` literal in both (`Monoid.npow`), which is the intended n⁵.
- **H5 Quantifier.** Each theorem is a closed `∀ n` statement with no implicit or fixed n; there are no other variables, so no constant can depend on n.
- **H6 Finset/Set, Fintype, decidability:** not applicable.
- **H7 Classical choice:** classical object logic; no restriction.

## 4. G-AX candidates

None. No hypothesis beyond the source's is added to either theorem.

## 5. Open items

- `@adversarial` hidden-hypothesis audit of both declarations (and of the reading enumeration in `interpretation.md` §2: congruence form, `ZMod 30` form, fixed n), to be dispatched by the orchestrator.
- Independent back-translation by `@fidelity-auditor`, dispatched by the orchestrator with the declaration names only.
- G-FID review: confirm the operand order and the truncation point in H1 for R2. The `[fidelity.kernel_as_judge]` waiver is only offered, not recorded.
- G-KERNEL: the stubs count as `open` with a `statement_fingerprint` only once `reports/kernel/latest.json` says so.
