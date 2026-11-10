# Initiating Prompt — mathAgents: a ResearchTeam instance for symbolic-logic-driven proof development

> Status: ACCEPTED as the founding brief (2026-09-30). This is a historical record of the refined
> request. Where it differs from later decisions, **`03-decisions.md` governs**. In particular, the
> open questions at the end are resolved by D8–D13, and the per-machine availability in §7
> replaces the `local_status` field (D10).

---

## 1. Mission

Stand up **mathAgents**, a `researchteam` instance whose purpose is to *develop, verify, and explain
proofs*. Its governance harness must make the **symbolic logic of each proof explicit** at every
stage between a natural-language claim and a kernel-checked Lean 4 artifact, and every design
decision in that harness must be **derived from, and cited to, research** on automated and
LLM-assisted theorem proving, autoformalization, and proof engineering.

**Proof standard (artifact of record): Blueprint + Lean.** A claim is *proved* only when:
1. an informal, symbolic-logic blueprint exists whose every node is name-linked to a Lean
   declaration, **and**
2. the Lean development builds with no `sorry`/`admit`/new `axiom`, and `#print axioms` for each
   headline theorem falls within the declared axiom envelope.

The Lean kernel is the final judge of validity. Humans are the final judges of *fidelity*: the
kernel cannot tell whether the formal statement says what was meant.

## 2. Scope: proof domains (all in scope)

| Domain | Examples / benchmark anchors |
|---|---|
| Applied / modeling proofs | Market, mechanism, and ABM properties (precedent: `baseAgent/Projects/AgenticCapital` ZIT theorems) |
| Research-level mathematics | Theorems from papers and textbooks, formalized in Mathlib style with a blueprint |
| Competition problems | Olympiad and Putnam style; miniF2F, PutnamBench, ProofNet subsets |
| Logic and foundations | Propositional, first-order, and modal logic; soundness and completeness; proof-theoretic results |
| Proofs used by philosophers of science | e.g. Arrow-type impossibility results, Dutch-book / probabilism arguments, Bayesian convergence, triviality results for conditionals, confirmation paradoxes, underdetermination and identifiability arguments. *The operator curates the list.* |

## 3. Logic policy: declared object logic

- Every problem **declares its object logic** at intake (default: classical higher-order logic, as
  in Lean and Mathlib).
- A non-classical logic (modal, deontic, intuitionistic, conditional or counterfactual,
  probabilistic, relevance/paraconsistent) is **deeply embedded** in Lean as an object logic:
  syntax, a proof system and/or semantics, and soundness where it is needed. Reasoning *about* it
  stays in Lean's classical metatheory.
- A registry at `references/object-logics.json` tracks each logic: name, proof system(s), semantics,
  Lean embedding status, library location, and sources.
- Use of `Classical.choice`/LEM is recorded in the axiom envelope. It is not forbidden, but a
  "constructive" label on a result requires that the envelope exclude it.

## 4. The symbolic-logic pipeline (the harness's core)

Each stage produces a named artifact and has a gate. Stages 1–4 are the "articulation" layer that
the operator asked for.

| # | Stage | Artifact | Gate |
|---|---|---|---|
| 0 | Intake | Problem card: source, informal statement, domain, declared object logic, engine choice | Complete card |
| 1 | **Formal statement + fidelity** | Quantified symbolic statement with all hypotheses explicit, plus a Lean `theorem … := sorry` stub; independent back-translation to prose | **HUMAN: statement-fidelity sign-off** (fail-closed) |
| 2 | **Proof-strategy skeleton** | Blueprint DAG of lemmas; the method at each node (induction, contradiction, case split, diagonalization, construction, compactness, …); dependency edges | Adversarial review: missing cases, circularity, hidden assumptions |
| 3 | **Explicit derivations** | Natural-deduction or sequent-calculus derivations for the logical spine, with the inference rule named at each step. Mathematical steps cite the lemma or Mathlib fact. | Mechanical rule-check where feasible; no unnamed steps |
| 4 | **Tactic-level plans** | For each blueprint node: candidate tactics, Mathlib lemmas, and engine hints | — (advisory) |
| 5 | Formalization | Lean 4 proofs filling the stubs | Kernel gate (§6) |
| 6 | Counterexample track (parallel) | Attempts to falsify the statement or a lemma (small models, SMT/ATP search, `decide` on finite instances) | **HUMAN: counterexample verdict** before a claim is declared false or revised |
| 7 | Informalization | Prose narration name-bound to Lean (port the `lean-informalization` agent and its G1–G7 gates from baseAgent) | No net-new claims; `[Lean: name]` binding |
| 8 | Dossier assembly | Proof dossier (§8) | Full audit (§6) |

Stage 2 must be able to loop back to Stage 1 when a strategy exposes a mis-stated theorem. That
loop-back re-triggers the human fidelity gate.

## 5. Agent harness

Keep the standard researchteam governance team (orchestrator, security, adversarial,
conflict-auditor, reference-manager, and the rest). Add domain agents. Where no agentteams archetype
fits, hand-write the agent following the `lean-informalization` pattern, using a USER-EDITABLE
region that survives `--update --merge`.

| Agent | Role | Tools posture |
|---|---|---|
| `@statement-formalizer` | Stage 1: NL → symbolic statement → Lean stub | Write |
| `@fidelity-auditor` | Independent back-translation; diffs meaning against intake; flags drift | Read-only |
| `@proof-strategist` | Stage 2: blueprint DAG and method selection | Write |
| `@logic-articulator` | Stage 3: ND/sequent derivations with named rules; object-logic aware | Write |
| `@tactic-planner` | Stage 4: tactic and lemma plans, engine hints | Write |
| `@lean-prover` | Stage 5: writes Lean, iterates on kernel feedback | Write + Bash (`lake`) |
| `@counterexample-hunter` | Stage 6: falsification attempts | Read + Bash |
| `@axiom-auditor` | Kernel gate: build, `sorry`/`admit`/`axiom` scan, `#print axioms` vs. envelope | Read + Bash |
| `@engine-advisor` | Consults `references/prover-engines.json`; proposes engines (§7) | Read-only |
| `@lean-informalization` | Stage 7 (ported from baseAgent with provenance note) | Write |
| `tool-lean` | Generated from a `tools` entry in `brief.json` (Lean/Lake operational reference) | per archetype |
| Workstream experts | Methods Lit Review · Harness Spec · Proof Dossiers · Evaluation · Proof Library | per archetype |

> Postures as amended since: D27 (`@statement-formalizer` also holds `execute`) and D39 (the five "Write" pipeline
> agents above, all but `@lean-informalization`, lose `edit`: they return text and only the orchestrator writes).

## 6. Governance gates (fail-closed)

- **G-FID (human):** statement-fidelity sign-off before any proving effort is spent.
- **G-AX (human):** any new axiom, postulate, added hypothesis, or weakening of a statement.
  Precedent: the false upstream Agda postulate `greedy-optimal` in AgenticCapital.
- **G-CX (human):** counterexample verdicts.
- **G-KERNEL (automated):** a script (e.g. `scripts/check_proof_integrity.sh`) that runs
  `lake build`, scans for `sorry`/`admit`/`axiom`/`native_decide`/`unsafe`, and compares
  `#print axioms` against the envelope ⊆ `{propext, Classical.choice, Quot.sound}` unless a
  G-AX approval widens it. It emits a machine-readable report consumed by the dossier.
- **Open-item discipline:** unproved nodes are flagged in source and in the wave manifest. They are
  never silently dropped. (This adopts AgenticCapital's wave + manifest workflow as the baseline.)
- **Kernel-as-judge override:** the operator may, *within a specific conversation*, direct that the
  kernel alone suffices, waiving G-FID/G-AX/G-CX for that conversation only. Agents accept that
  directive, record it in the session plan, and never carry it into another session. When an agent
  requests feedback at a human gate, it **also offers** this override as an option.
- Citation gates: the existing 2-fold citation & claim audit applies to all prose deliverables.

## 7. Prover-engine policy and registry

- **Default:** Lean automation only (`simp`, `omega`, `decide`, `aesop`, `linarith`, `nlinarith`,
  `polyrith`, `norm_num`, `exact?`/`apply?`, and hammer-style tactics if available).
- **Offer alternatives** (a) at the start of every new working session and (b) whenever
  `@engine-advisor` judges that another engine would likely help (e.g. a large first-order subgoal
  goes to ATP; a finite counterexample search goes to SMT; a stuck competition problem goes to an
  open prover model).
- **Registry:** `references/prover-engines.json`, validated by a JSON Schema. One entry per engine:
  `id`, `kind` (lean-tactic | smt | atp | llm-prover | interaction-layer), `strengths`,
  `suited_domains`, `logic_fragment`, `unsuited_for`, `install`, `resource_needs` (GPU/RAM),
  `result_trust` (e.g. "must be re-checked in Lean kernel"), `local_status` (installed / not
  installed), and `sources` (bibliography keys). Initial candidates: Lean built-ins; Z3 and cvc5
  (SMT-LIB); Vampire and E (TPTP); DeepSeek-Prover, Kimina-Prover, Goedel-Prover (LLM provers);
  Pantograph, LeanDojo, a Lean LSP/MCP server (interaction layers). **Every strength or domain
  claim in the registry must cite a verified source.** No unsourced capability claims.
- Non-Lean results are **hints until re-checked by the Lean kernel**.

## 8. Deliverables and research aims

1. **Methods literature review** (first, because the harness design is derived from it). It covers
   autoformalization and statement fidelity, informal→formal pipelines (Draft-Sketch-Prove,
   blueprints), LLM provers and search (AlphaProof, DeepSeek-Prover, Kimina, Goedel-Prover, COPRA,
   Baldur, Lean Copilot, LeanDojo), benchmarks (miniF2F, ProofNet, PutnamBench), proof-theoretic
   representations (natural deduction, sequent calculus, TPTP, SMT-LIB), and embeddings of
   non-classical logics in proof assistants. Reuse and **re-verify** the LeanProofNarration
   bibliography (ProofNet and DSP are still search-level only). No fabricated references.
2. **Harness specification**: every pipeline stage, agent, and gate has a design rationale that
   cites the literature review. Traceability table: design decision → finding → source.
3. **Proof dossiers**, one per theorem: problem card, formal statement plus fidelity record,
   blueprint DAG, derivations, tactic plan, Lean code, G-KERNEL report / axiom envelope, prose
   narration, open items.
4. **Reusable proof library**: a Lake package of lemmas and object-logic embeddings, designed to be
   consumable by other repos such as AgenticCapital.
5. **Harness evaluation**: results on miniF2F / ProofNet / PutnamBench subsets plus a curated
   philosophy-of-science set. Report success rate, gate interventions, and a taxonomy of failure
   modes (mis-formalization, strategy error, tactic failure, false statement).

## 9. Environment and setup

- Location: the sibling repo `../mathAgents` (currently empty) via `researchteam init`, then
  `brief.json` edits, then `researchteam materialize`.
- `brief.json` changes:
  - `project_goal` rewritten for proof development.
  - Components: Methods Review, Harness Spec, Proof Dossiers, Proof Library, Evaluation.
  - Authority sources extended: Lean 4 reference and Mathlib docs, arXiv cs.LO/cs.AI/math.LO,
    Stanford Encyclopedia of Philosophy (for philosophy-of-science statements), and CrossRef for
    verification.
  - A Lean/Lake `tools` entry.
- Toolchain: install `elan`; pin Lean and Mathlib (see open question 1); run `lake exe cache get`.
  Verify with a hello-Mathlib build before any gate is declared active.
- Cross-repo: baseAgent assets (the `lean-informalization` agent, the LeanProofNarration
  bibliography, the AgenticCapital workflow) are **copied with provenance notes**, never edited in
  place. If a proof archetype belongs in `agentteams` itself, produce a handoff report for that repo
  instead of patching it.

## 10. Phasing and acceptance

| Phase | Output | Done when |
|---|---|---|
| 0 Bootstrap | Instance scaffolded, toolchain installed, G-KERNEL script passing on a hello-Mathlib file | `researchteam doctor` clean; the gate script fails on an injected `sorry` |
| 1 Research | Methods literature review | Citation audit clean; every source verified |
| 2 Harness | Agents, gates, and the two JSON registries plus their schemas | Each design choice traced to a Phase 1 finding |
| 3 Pilot | 3–5 dossiers spanning ≥3 domains, including ≥1 non-classical object logic | All gates pass or open items are recorded |
| 4 Evaluation | Benchmark report | Failure taxonomy populated |

Per repo rules: every multi-step phase gets a `tmp/by-week/YYYY-Www/` plan and steps CSV; every
multi-file session closes with `@conflict-auditor`; completed plans go into daily work summaries.

---

## Open questions (resolve before execution)

> Researched recommendations for all five questions are in `02-open-questions-research.md`
> (2026-09-30). They await operator acceptance.

1. **Lean/Mathlib pin:** match AgenticCapital (`v4.32.1`) so the library is shared, or use the
   latest stable release at bootstrap time?
2. **Hardware:** is a local GPU available? This decides whether LLM-prover engines are
   `installable` or only `documented` in the registry.
3. **Pilot theorems:** which 3–5 theorems (at least one philosophy-of-science result) should the
   Phase 3 pilot use?
4. **Dossier output format:** Markdown + Chicago (repo default), or also a `leanblueprint`
   LaTeX/PDF/web blueprint? What citation style should math-facing text use?
5. **Repo hosting:** create a GitHub remote for mathAgents? Public or private?
