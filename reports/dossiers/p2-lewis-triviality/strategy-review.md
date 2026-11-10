# P2 Stage 2 strategy review (@adversarial, DD-9)

Review of `strategy.md`, 2026-10-01, persisted from the reviewer's report.

- **No circularity (L6):** Stalnaker's Hypothesis is used only at the conditioned functions
  P_C(X) = P(C⊓X)/P C. C side: P_C(A) = P(C⊓A)/P C > 0 (`div_pos`; P(C⊓A) > 0 from hAC with `inf_comm`,
  P C > 0 from L4), so P_C(A>C) = P(C⊓(A⊓C))/P(C⊓A) = 1. Cᶜ side: P(Cᶜ⊓(A⊓C)) = P ⊥ = 0. General form
  via `inf_assoc` and `div_div_div_cancel_right₀`.
- **No missing cases;** every denominator is shown positive (hAC, hAnC, L4, hA).
- **No hidden assumptions;** R3:all uses K := setOf IsFinAddProb with `Set.mem_setOf_eq`.
- **L7 true:** nonnegativity (`div_nonneg`), the ≤ 1 field (L2 with `inf_le_left`, `div_le_one_of_le₀`),
  top (`inf_top_eq`, `div_self`), additivity (`inf_sup_left`, `Disjoint.mono`, additivity of P, `add_div`).
- **Dependency list acyclic:** L1, L2 → L4, L5 → R2 → R3:closed (+L6, hK) → R3:all (+L8 ← L7).
- **Mathlib names all exist** (`sup_inf_inf_compl`, `disjoint_compl_right`, `div_div_div_cancel_right₀`,
  `div_le_one_of_le₀`; `inf_*` generated from `sup_*` by `@[to_dual]`; `Mathlib.Data.Real.Basic` is a
  deprecated shim for `Mathlib.Basic.Real.Basic`).
- **Low (fingerprint risk):** extra imports in the approved file could, in principle, change elaborated
  instance terms and so the fingerprint. *Orchestrator resolution:* the theorems' proofs must live in the
  approved file, so a separate Aux file importing it cannot supply their lemmas (that would be an import
  cycle). Aux lemmas go in the same file under `namespace MathAgents.P2LewisTriviality.Aux`, imports may
  be added, and G-KERNEL plus `validate_dossier.py --require-fid` then confirm every approved fingerprint
  is unchanged; any change fails closed and returns that statement to the operator for re-approval.
- **Info:** R3:closed also uses hK; L7 must prove the ≤ 1 field (it does).
- **Refresh note (@proof-strategist, 2026-10-16; pin re-check, not a new review round).** Re-checked
  against Lean 4.34.1 and Mathlib `d13f23b723b8a846827a245b89c10fc7d3f11612` (`lean/lake-manifest.json`)
  and `reports/kernel/name-index.txt`. Every Mathlib name cited above and in `strategy.md` §2 is in the
  name index, except `Set.mem_setOf_eq`: at this pin it is
  `@[deprecated (since := "2026-07-09")] alias mem_setOf_eq := mem_ofPred_eq`
  (`Mathlib/Data/Set/Operations.lean`, line 81), and the name index lists only `Set.mem_ofPred_eq`.
  It still resolves, but with a deprecation warning; R3:all and L8 should use `Set.mem_ofPred_eq`.
  `Mathlib.Data.Real.Basic` is confirmed as a `deprecated_module (since := "2026-08-27")` that imports
  `Mathlib.Basic.Real.Basic`. Neither point changes the method, the lemma plan or the dependencies.
  `strategy.md` (§5 risk 4) still names `Set.mem_setOf_eq`. Correcting it is an edit to the strategy,
  so it would need a new review round under a new hash. It is left for the orchestrator to schedule.
  The verdict below is the reviewer's verdict of 2026-10-01 and is unchanged.

Verdict: CLEARED
Strategy sha256: 185c01e2bf5292052c23a0452bc4b0ebc97593f419f3e7a14b13ce79e20a9c7c
