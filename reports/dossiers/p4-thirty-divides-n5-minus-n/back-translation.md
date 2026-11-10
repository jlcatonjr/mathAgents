# Stage 1 back-translation: P4 thirty divides n⁵ − n

> **Auditor:** `@fidelity-auditor`, dispatch `e0d0daf8a2cd2fdeb75513b110147fbb`, 2026-10-18. This report is advisory only (DD-26, DD-27). It declares nothing faithful, approved or proved, and it does not stand in for the human G-FID review.
> **Pin:** Lean 4.34.1 (`lean/lean-toolchain`); Mathlib `d13f23b723b8a846827a245b89c10fc7d3f11612` (inputRev v4.34.1, `lean/lake-manifest.json`), as reported by `python3 scripts/lean_docs.py`.
> **Source read:** `lean/MathAgentsWIP/P4ThirtyDividesN5MinusN.lean`. It imports only `Mathlib.Algebra.Ring.Int.Defs`, and both bodies are `sorry`.

## Independence note

I read the Lean file first, before the problem card, the Interpretation Brief and `statement.md`. The file holds one-line docstrings on each theorem ("Reading R1: ...", "Reading R2: ... (truncated subtraction)"). I could see them on screen but did not use them. The back-translation below comes from the signatures alone. I had not seen the drafter's handoff in this conversation.

---

## 1. `MathAgents.P4ThirtyDividesN5MinusN.thirty_dvd_pow_five_sub_self_int_R1`

```
Declaration: MathAgents.P4ThirtyDividesN5MinusN.thirty_dvd_pow_five_sub_self_int_R1   fingerprint: 2249006667
Independent: yes (signature read before the card, the brief and statement.md; docstrings seen but not used)
```

**Signature:** `∀ n : ℤ, (30 : ℤ) ∣ n ^ 5 - n`

**Back-translation.** This is a closed proposition with no parameters and no hypotheses. It has a single universal quantifier, and its bound variable n ranges over the integers ℤ. For each such n, the integer 30 divides the integer n⁵ − n. Here n⁵ is the 5-fold product of n with itself: `^` is `HPow ℤ ℕ ℤ` with the natural-number literal 5 as exponent, and under Mathlib this is the monoid power, which agrees with core `Int.pow`. The minus sign is integer subtraction, which is total and exact. `∣` is `Dvd.dvd` on ℤ, so a ∣ b means ∃ c : ℤ, b = a * c. Unfolded, the statement reads: for every n ∈ ℤ there is c ∈ ℤ with n⁵ − n = 30c. No project definitions are used. All terms (the binder, the literal 30 and the subtraction) live in ℤ, and no casts appear.

**Drift.**

1. `∀ n : ℤ` | universal quantifier over all integers | card: "For every integer n"; brief R1 "∀ n : ℤ" | no drift.
2. `(30 : ℤ) ∣ n ^ 5 - n` | divisibility in ℤ, exponent 5, operand order n⁵ then n | card: "30 divides n⁵ − n"; brief §6 items 3 and 4 | no drift. Divisibility is used, not a congruence or a `ZMod 30` form, and the literals 30 and 5 are correct.
3. Degenerate cases | n = 0, 1 and −1 give 0, which every number divides; this is true and non-vacuous, and the source admits these n too | no drift.
4. Object logic | classical Lean statement; the card declares `classical-hol` | no shallow-embedding issue.

**G-AX candidates:** none. The Lean adds no hypothesis.

**Matches reading:** R1.

---

## 2. `MathAgents.P4ThirtyDividesN5MinusN.thirty_dvd_pow_five_sub_self_nat_R2`

```
Declaration: MathAgents.P4ThirtyDividesN5MinusN.thirty_dvd_pow_five_sub_self_nat_R2   fingerprint: 3359412615
Independent: yes (signature read before the card, the brief and statement.md; docstrings seen but not used)
```

**Signature:** `∀ n : ℕ, (30 : ℕ) ∣ n ^ 5 - n`

**Back-translation.** This is a closed proposition with no parameters and no hypotheses. It has a single universal quantifier, and its bound variable n ranges over the natural numbers ℕ, including 0. For each such n, the natural number 30 divides n⁵ ∸ n. Here n⁵ is the power in ℕ (`HPow ℕ ℕ ℕ`). The minus sign is `Nat.sub`, which is truncated: a ∸ b = 0 when a < b, and the operands appear in the order n⁵ first, n second. `∣` is `Dvd.dvd` on ℕ, so a ∣ b means ∃ c : ℕ, b = a * c. Unfolded, the statement reads: for every n ∈ ℕ there is c ∈ ℕ with n⁵ ∸ n = 30c. No project definitions are used, and no casts appear.

**On truncation (my own check):** n ≤ n⁵ for every n : ℕ. At n = 0, 0 ≤ 0. For n ≥ 1, n⁵ = n · n⁴ ≥ n · 1. So n⁵ ∸ n always equals the true difference n⁵ − n, and the truncation never fires. The statement is therefore not vacuous. Writing `n - n ^ 5` instead would have made it vacuous, and the Lean does not do that.

**Drift.**

1. `∀ n : ℕ` | universal quantifier over the naturals, 0 included | card R2: "for every natural number n"; brief R2 | no drift. Note that the card's top-line informal statement says "integer". R2 is the operator's own restatement over ℕ, recorded at intake (brief §1), so this is not drift against R2.
2. `n ^ 5 - n` in ℕ | truncated subtraction, order n⁵ then n | card: "with truncated subtraction; harmless since n ≤ n⁵"; brief §6 item 2 | no drift. The order matches, and truncation never fires (see above).
3. Coercions | none; every term is in ℕ | brief §6 item 1 | no drift.
4. `(30 : ℕ) ∣ ...` | divisibility, not a congruence | brief §6 item 3 | no drift.
5. Strength | R2 is the n ≥ 0 case of R1 (brief §2 R2) | the Lean is consistent with that relation; no drift.
6. Object logic | classical; the card declares `classical-hol` | no issue.

**G-AX candidates:** none. The Lean adds no hypothesis.

**Matches reading:** R2.

---

## Notes for the human reviewer

- I diffed my reading against `statement.md` §2 and §3 (H1 to H7) and found no disagreement. The independent reading agrees with the drafter on both declarations.
- The kernel report lists both declarations as `status: open`, with `sorryAx` in their axiom sets. This is expected for Stage 1 stubs.
- I found no instruction-like text in the card, the brief, `statement.md` or the Lean file (C-4).
