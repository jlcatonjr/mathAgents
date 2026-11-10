# Interpretation Brief — P4 thirty divides n⁵ − n

> **Commissioned by:** `@interpretation-advisor` · **Written by:** the orchestrator, verbatim from the advisor's return · **Drafted:** 2026-10-16
> **Status:** advisory input to Stage 1 only. This brief is not a formal statement and not a fidelity decision, and it calls nothing proved. Choosing a reading is the human G-FID gate's decision.
> **Intake:** Stage 0 intake done 2026-10-16 by the operator (Jim). Object logic declared: `classical-hol`. Readings selected at intake: R1 and R2 (`preferences.toml` `[readings.selected]`, D43). R3 is listed as an alternative only.
> **Evidence base:** none. The operator posed the statement at intake as folklore, with no citation (`problem-card.md`). This brief cites no literature and makes no cited claim, so it has no `interpretation.claims.csv` rows. Every mathematical remark below is tagged [editors' inference — unsourced].
> **Guide drawn on:** `elementary-number-theory.methodology.guide.md` (status: provisional; unsourced). It was commissioned for this dossier after the brief was drafted (2026-10-16); the orchestrator added this line.

**Source framing.** The only source is the operator's informal sentence. The problem card calls it "a standard number-theory exercise", a framing that excludes any literature claim about its origin or variants.

## 1. Claim and scope

The informal statement, quoted from `problem-card.md`: "For every integer n, 30 divides n⁵ − n."

**Scope** [editors' inference — unsourced]:

- The sentence fixes the domain as the integers, so R1 is the literal reading. R2 is the operator's own restatement over ℕ, recorded at intake as a separate theorem.
- The sentence states divisibility, not a congruence. Both forms are on the checklist in §6.
- There are no further parameters or hypotheses. The modulus 30 and the exponent 5 are fixed literals.

## 2. Readings

The readings are listed in the order of `preferences.toml` (selected readings first, then the alternative). **That order is not a ranking and sets no default.** No Mathlib or Lean declaration is named here.

### R1. Over the integers: ∀ n : ℤ, 30 ∣ n⁵ − n

- **Source support:** the operator's sentence, quoted in §1.
- **Object logic:** `classical-hol`, which matches intake. No divergence.
- **Explicit hypotheses:** none beyond n ∈ ℤ.
- **G-AX candidates:** none identified.
- **Formalization note** [editors' inference — unsourced]: subtraction in ℤ is total and exact, so n⁵ − n has its intended meaning for negative n too. Formalization in Lean/Mathlib looks plausible. Whether it succeeds is untested.

### R2. Over the naturals: ∀ n : ℕ, 30 ∣ n⁵ − n, with truncated subtraction

- **Source support:** the operator's restatement at intake (`problem-card.md`, Readings).
- **Object logic:** `classical-hol`, which matches intake. No divergence.
- **Explicit hypotheses:** none beyond n ∈ ℕ.
- **Truncation** [editors' inference — unsourced]: in ℕ, a − b is 0 when a < b. For every n : ℕ we have n ≤ n⁵ (equality at n = 0 and n = 1, and n⁵ ≥ n for n ≥ 1). So n⁵ − n never truncates and equals the true difference. The fidelity check must confirm that the formal statement subtracts in exactly the order n⁵ − n. It must also confirm that no coercion moves the subtraction into or out of ℕ and changes its meaning.
- **Formalization note** [editors' inference — unsourced]: plausible. Under this restriction R2 is the case n ≥ 0 of R1, so it is a weaker statement.

### R3. Generalization: for every prime p and every integer n, p ∣ nᵖ − n (not selected)

- **Source support:** recorded at intake as an alternative (`preferences.toml` `alternatives = ["R3"]`). No source is cited.
- **Object logic:** `classical-hol`. No divergence.
- **Explicit hypotheses:** p is prime.
- **Relation to R1** [editors' inference — unsourced]: R3 at p = 5 gives 5 ∣ n⁵ − n directly. For p = 2 and p = 3 the exponent 5 differs from p, so a further step is needed: iterate nᵖ ≡ n (mod p) to reach n⁵ ≡ n. R1 then follows by combining the three coprime moduli. So R1 is a corollary of R3 only with these extra steps.
- **Not selected at intake.** It is listed here so that `@adversarial` can audit the enumeration.

**Possibly unenumerated readings** [editors' inference — unsourced], for `@adversarial` to audit:

- the congruence form n⁵ ≡ n (mod 30);
- the identity x⁵ = x for every x in ℤ/30ℤ;
- a reading with a fixed n rather than a universally quantified one.

## 3. Variants and provenance

None is claimed. The statement comes to this dossier as operator-posed folklore, and this brief makes no provenance, priority or variant claim.

## 4. Method lineage

These are possible proof routes only. None is asserted to work or to be proved [editors' inference — unsourced]:

- **Factor the modulus:** 30 = 2 · 3 · 5, with pairwise coprime factors.
- **Per prime:** show p ∣ n⁵ − n for p ∈ {2, 3, 5}, using either
  - Fermat's little theorem, iterated where the exponent 5 ≠ p, or
  - a finite case analysis on the residue of n mod p (or mod 30 directly).
- **Combine:** pairwise-coprime divisors of a number divide it together, so their product does.
- **Alternative:** the factorization n⁵ − n = (n − 1) n (n + 1)(n² + 1) gives divisibility by 2 and 3 from consecutive integers, with 5 still needing its own argument.

## 5. Interpretive conflicts

None is known to the editors, and none is sourced. The only live choice is the domain and subtraction semantics (R1 against R2). Intake settled it by selecting both as separate theorems.

## 6. Checklist for the Stage 1 fidelity check

These are inputs for `@fidelity-auditor` (or `@proof-dossiers-expert` standing in for it), not verdicts.

1. **ℤ or ℕ.** R1 must quantify over ℤ and R2 over ℕ. Check that no cast changes the domain (for example, ℕ-valued n cast to ℤ inside R1).
2. **Subtraction semantics.** In R2, check the operand order n⁵ − n and the type the subtraction is computed in. Confirm that n ≤ n⁵ makes truncation harmless (§2, R2), and that no rewriting reintroduces a truncating n − n⁵.
3. **Divisibility or congruence.** The informal statement uses divisibility. If a congruence or ℤ/30ℤ form is used instead, it is a different statement whose equivalence must be shown, not assumed. In ℕ that equivalence depends on the ordering in item 2.
4. **Quantifier.** The statement must hold for **all** n, universally quantified, not for a fixed or implicit n. Also check the literals 30 and 5.
5. **Trivially true or false** [editors' inference — unsourced]: the statement becomes vacuous if the subtraction truncates to 0 (for example, n − n⁵ in ℕ, which 30 always divides). It becomes false if the exponent or modulus is mistyped.

## 7. Verification status

- **Sources:** none, so there is nothing for `@reference-manager` to confirm.
- **Claim ledger:** no provenance or lineage arrows and no cited claims, so `@technical-validator` has an empty ledger.
- **Lean/Mathlib:** no declaration is named in this brief, and no Lean pin was consulted.
- **Guides:** `elementary-number-theory.methodology.guide.md`, provisional and unsourced, so its directives are editors' inference.
