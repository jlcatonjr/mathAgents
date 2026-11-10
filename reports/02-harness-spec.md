# Harness Specification

This component specifies the mathAgents harness: the nine pipeline stages, the agent roster, the governance gates, and the two registries.

**Status labels.** Each element carries one of three labels:
- **IMPLEMENTED**: it exists today, at the repository path given.
- **PARTIAL**: part of it exists, and the text says which part.
- **SPECIFIED**: it is still to be built.

**Decision tags and the ledger.** Every normative design decision is one sentence that opens with a bracketed decision tag, DD-1 through DD-59. Each tagged sentence is one row of the claim ledger `reports/02-harness-spec.claims.csv`, and its basis is one of two kinds:
- A `design-inference` row cites claim identifiers from the Methods Literature Review ledger, `reports/01-methods-review.claims.csv`, written here as `MR:C<n>`.
- A `policy` row cites decisions or orchestrator clarifications from `docs/charter/03-decisions.md`.

**Gaps.** Several decisions fall in the review's Gaps list: the counterexample track, axiom governance, the Stage 3 calculus, solver output, non-modal logics, the informal skeleton, unverified interaction layers, and the Lean 4 port of miniF2F. Each of those decisions states in its own sentence that no reviewed finding supports it.

**Review claims that are themselves policy.** Where the review labels one of its own implications as charter policy, the decision here is `policy` and is described as consistent with that review claim, not supported by it.

**Strength of evidence.** The Traceability Table at the end maps every tag to its basis and status. Literature enters only through the review. The review is bounded by retrieved abstracts and consists largely of preprints, so a `design-inference` row is at most as strong as the review claim it cites.

## Pipeline Stages

The stages follow charter §4 (`docs/charter/01-initiating-prompt.md`), as amended by the decision record. Each stage below gives its artifact, its status, and the decisions that govern it.

### Stage 0: Intake

**Artifact:** a problem card at `reports/dossiers/<slug>/problem-card.md`, written by the orchestrator with the operator at intake. **IMPLEMENTED** as a checked format: the dossier-structure module requires the fields Source, Informal statement, Domain (from the D2 enum), Object logic (a registered, non-planned id) and Engine (a registered id), plus Reading (an R-id of the brief) whenever an Interpretation Brief exists.

**Inputs, IMPLEMENTED:**
- `references/object-logics.json`, the source of object-logic ids;
- `references/prover-engines.json`, the source of engine ids;
- the per-machine engine profile `.machine/profile.json`, written by `scripts/probe_machine.py` and uncommitted by design.

**Interpretation Briefs, IMPLEMENTED in practice:**
- `reports/dossiers/p2-lewis-triviality/interpretation.md`;
- `reports/dossiers/p3-dutch-book/interpretation.md`.

The P2 brief shows the gap that the problem card closes. Intake has not happened for P2, so every object-logic entry reads "intake pending", and twelve G-AX candidates are open before any Stage 1 work.

- [DD-1] Every problem enters the pipeline through a Stage 0 problem card that records its source, informal statement, domain, declared object logic as an id from `references/object-logics.json` with `classical-hol` as the default, and engine choice, and no Stage 1 artifact is drafted for a problem without a complete card.
- [DD-2] When an informal statement admits rival readings, an Interpretation Brief commissioned by `@interpretation-advisor` precedes Stage 1, lists the readings without ranking them, and routes every hypothesis the source does not state to G-AX as a candidate; no reviewed finding addresses reading enumeration, so this rests on charter policy D24 and D5.

**Preferences, IMPLEMENTED (D32):** the operator's choices are settings, not fixed history. `references/preferences.toml` holds the project defaults (statement of record when a primary is inaccessible, translation, how readings are chosen, default object logic and engines, the kernel-as-judge override), and `reports/dossiers/<slug>/preferences.toml` holds one dossier's overrides and choices (readings, object logic, engines, domain, G-AX answers). Each setting records its `choice`, its `alternatives` and the decision that recorded it. `scripts/preferences.py check` validates them (in CI), `show <slug>` prints the settings in force with their source, and the dossier-structure module requires the problem card to agree with the enforced settings (readings, domain, object logic, engines), binds each fidelity record to the hash of its problem card and preferences (`intake_sha256`), and rejects every waiver record, including in-session allowlist approvals, under `kernel_as_judge = never`. `sources.*`, `readings.selection` and `gax.*` are advisory: checked at the human G-FID review. Unknown or malformed settings fail; allowlist approvals must name a real dossier and carry `conversation` (null unless in-session), and a `never` dossier may not depend on any axiom approved in session. Test: `scripts/tests/test_preferences.sh`, 35 cases.

### Stage 1: Formal statement and fidelity

**Artifacts:**
- a quantified statement with every hypothesis explicit;
- a Lean stub `theorem … := sorry`, written by `@statement-formalizer` into the WIP library. The library is **IMPLEMENTED** at `lean/MathAgentsWIP/`, with conventions in `lean/MathAgentsWIP/README.md`;
- an independent back-translation to prose;
- a fidelity record at `reports/dossiers/<slug>/fidelity.json`. **IMPLEMENTED** (schema `references/schemas/fidelity-record.schema.json`).

**Statement fingerprint, IMPLEMENTED:** each G-FID record keys to the fingerprint that `scripts/lean/AxiomAudit.lean` emits into `reports/kernel/latest.json`. Under DD-34 it hashes the statement's type together with the type and, for definitions, the body of every project constant the statement reaches (constructor types included), so editing such a definition lapses the approval.

- [DD-3] Automated statement formalization may draft the Stage 1 stub, and any success rate quoted for a drafting engine is recorded with its benchmark and sampling budget, because the reviewed rates are preprint-level figures reported on the authors' own benchmarks.
- [DD-4] A Stage 1 stub that elaborates under the pinned toolchain is a precondition for G-FID review but never evidence of fidelity, since the reviewed preprint evidence reports compiler feedback improving autoformalization accuracy without equating compiling with fidelity.
- [DD-5] Stage 1 stubs are placed in the `MathAgentsWIP` library, where G-KERNEL reports them as `open`, so that adding a stub never changes the status of a proved declaration; this rests on orchestrator clarification C2 rather than on an operator decision.

### Stage 2: Proof-strategy skeleton

**Artifacts:**
- A leanblueprint project at `lean/blueprint/`, where `leanblueprint new` scaffolds it (a top-level `blueprint/` also counts). **SPECIFIED**: no blueprint exists yet; its gate G-BLUEPRINT is IMPLEMENTED. The tool is pinned in `environment.yml`, and agent guidance exists in `.claude/skills/tool-leanblueprint/SKILL.md` (IMPLEMENTED).
- An adversarial review record at `reports/dossiers/<slug>/strategy-review.md`. **IMPLEMENTED** as a checked format: each review round states `Verdict: CLEARED` or `Verdict: BLOCKED` and `Strategy sha256:` of the strategy it reviewed; the latest round decides, and Stage 3 may be dispatched only when it is `CLEARED` for the current `strategy.md`.

- [DD-6] The Stage 2 dependency graph is generated by leanblueprint from each node's declared `\uses` labels and Lean names, and because those `\uses` edges are author-declared and not checked against the Lean dependencies, the graph is treated as the author's claim about dependencies rather than as a verified one.
- [DD-7] Stage 2 keeps an informal proof-strategy skeleton as a required artifact even though the reviewed evidence on informal guidance is mixed and preprint-level, with one source reporting sketch-guided gains and another an inverse relation between natural-language guidance and proof success; no reviewed finding supports keeping it, so it rests on charter policy D3, and the Harness Evaluation tests whether the skeleton helps.
- [DD-8] Any Stage 2 change that alters a Stage 1 statement sends the problem back to Stage 1, and because a G-FID approval is keyed to the declaration's `statement_fingerprint`, the changed statement needs a fresh human sign-off.
- [DD-9] Stage 2 closes with an `@adversarial` review record covering missing cases, circularity, and hidden assumptions, and every hidden assumption it finds becomes a G-AX candidate.

### Stage 3: Explicit derivations

**Artifact:** derivation records at `reports/dossiers/<slug>/derivations.md`, one step per line, with a rule or lemma named at each step. **IMPLEMENTED** as a checked format: every `## Node:` states its calculus and its object logic (which must match the problem card) and has at least one step; every numbered step is `<n>. <formula>  [<rule or lemma> <premises>]` with a named justification, and cites only existing, earlier steps.

- [DD-10] Each Stage 3 derivation record names its calculus and its object logic, an inference the review draws from a single proof-theory text that spans intuitionistic, classical, modal, and linear applications.
- [DD-11] Stage 3 admits natural-deduction or sequent-calculus derivations without fixing one calculus, and a mechanical rule-check is built only for calculi whose rules the harness encodes, with every other derivation checked for named steps alone; no reviewed finding settles the calculus or what a rule-check needs, so this rests on charter policy D3.

### Stage 4: Tactic-level plans

**Artifact:** one tactic plan per blueprint node, at `reports/dossiers/<slug>/tactic-plan.md`. **PARTIAL**: the plan's names are checked mechanically. Each node is headed `## Node: <label>   Lean: <name>`, and each `Lemmas:` list sits on one line, `|`-separated, one name per item before any `(located: …)` note.

As in the charter, Stage 4 has no gate of its own. The Mathlib names in a plan go through the same name-binding check as Stage 7 (DD-17).

- [DD-12] Each Stage 4 tactic plan acts as a formal sketch for one blueprint node and carries candidate tactics, Mathlib lemmas, and engine hints, by the review's analogy, which its sources do not draw, with sketch-guided proving and in-editor suggestion tools.

### Stage 5: Formalization

**Artifact:** Lean proofs in `lean/MathAgents/`, written by `@lean-prover`. **IMPLEMENTED** as a library; `lean/MathAgents.lean` imports its four files: `FiniteProbability` (the `finite-probability` object logic), `P2LewisTriviality`, `P3DutchBook`, and `Smoke`. `Smoke` is a toolchain smoke test, not a research result: it confirms that the pinned Lean and Mathlib pair builds and that the G-KERNEL axiom audit sees a Mathlib-dependent declaration.

**Gate:** G-KERNEL. **IMPLEMENTED.**

- [DD-13] `@lean-prover` iterates on kernel feedback by passing each failed attempt and its error message into the next attempt, a pattern whose reviewed evidence is a preprint reporting a fine-tuned repair model on Isabelle/HOL theorems rather than Lean, so its benefit for Lean 4 is untested.
- [DD-14] A Stage 5 result counts as proved only when its declaration has status `proved` in the G-KERNEL report, whatever engine produced the proof.

### Stage 6: Counterexample track

**Artifact:** a counterexample log at `reports/dossiers/<slug>/counterexamples.json`. The record format (schema `references/schemas/counterexample-log.schema.json`) and its G-CX check are **IMPLEMENTED**; `@counterexample-hunter`, which writes candidates into it through `scripts/log_counterexample.py`, is **IMPLEMENTED** (bespoke, D27).

- [DD-15] Stage 6 runs a counterexample track in parallel with Stages 2 to 5, using small models, `decide` on finite instances, and SMT or ATP search, and its results go to the human G-CX gate; no reviewed finding addresses counterexample search, so this rests on charter policy D5.
- [DD-16] A counterexample found by an SMT or ATP engine is a hint until it is re-established in Lean, for example by `decide` on the finite instance, because no reviewed finding establishes whether solver output is proof-producing, so this rests on charter policy D6 and D5.

### Stage 7: Informalization

**Artifact:** prose narration with `[Lean: name]` bindings, inside the dossier at `informalization.md`. `@lean-informalization` is **IMPLEMENTED** (bespoke, D28); the name-binding check G-NAME is **IMPLEMENTED**, and Stage 8 assembly runs it.

- [DD-17] Every `[Lean: name]` binding in Stage 7 prose is confirmed against documentation generated for the pinned Mathlib and the project library, never against naming conventions alone, because conventions describe how names are formed, not which declarations exist.
- [DD-18] Stage 7 narration introduces no claim absent from the bound Lean statement, and a narrated result is called proved only when its bound declaration is `proved` in the G-KERNEL report.

### Stage 8: Dossier assembly

**Artifact:** the proof dossier at `reports/dossiers/<slug>/`, with the eight sections that `brief.json` defines for the `proof-dossiers` component. **SPECIFIED**: only the Interpretation Briefs exist today. The kernel snapshot `kernel-snapshot.json` is **IMPLEMENTED**: `scripts/snapshot_kernel.py` takes it from a fresh report of a clean tree during assembly, and the dossier validator checks it against the fidelity record and the current report.

**Kernel report:** the per-run report `reports/kernel/latest.json` is **IMPLEMENTED** and gitignored.

- [DD-19] Each dossier embeds a snapshot of the G-KERNEL report taken at assembly, including commit, source hash, Lean version, and per-declaration status, so the dossier's claims are tied to one checked state of the library.

### Evaluation hooks

The Harness Evaluation (component 5) is **SPECIFIED**. The pipeline must supply it with the following records.

- [DD-20] Every Harness Evaluation figure states its metric, split, sampling budget, and benchmark version, because the reviewed abstracts already report different totals for the same benchmark.
- [DD-21] The evaluation never sets a local result beside a published figure as a comparison; this rests on the evaluation component's quality criterion in `brief.json` against transferring published benchmark numbers to local runs, with D7 listing the evaluation as a deliverable, and is consistent with, not supported by, MR:C75.
- [DD-22] Mis-formalization stays a failure category for every benchmark the evaluation samples, a decision resting on a single preprint, FormalMATH, whose statement validation still ends in manual verification.
- [DD-23] The evaluation does not treat the Lean 4 port of miniF2F as faithful to the original statements; no reviewed finding assesses that port, so it rests on charter policy D7.

## Agent Roster

The roster has four groups: generated governance and production agents, workstream experts, the one bespoke advisory agent, and the charter's domain agents. Paths are canonical Copilot files. The Claude Code, Goose, and Codex forms are projections of these files, re-rendered under D20.

| Agent | Stage or role | Tools posture | Status and path |
|---|---|---|---|
| `@orchestrator`, `@security`, `@adversarial`, `@conflict-auditor`, `@conflict-resolution`, `@navigator`, `@code-hygiene`, `@cleanup`, `@agent-updater`, `@agent-refactor`, `@repo-liaison`, `@git-operations` | Governance | per archetype | **IMPLEMENTED**: `.github/agents/<name>.agent.md` |
| `@primary-producer`, `@quality-auditor`, `@cohesion-repairer`, `@technical-validator`, `@format-converter`, `@reference-manager`, `@output-compiler`, `@visual-designer`, `@post-production-auditor`, `@retrieval-integrator`, `@research-analyst`, `@content-enricher`, `@team-builder`, `@work-summarizer` | Production and audit | per archetype | **IMPLEMENTED**: `.github/agents/<name>.agent.md` |
| `@methods-review-expert`, `@harness-spec-expert`, `@proof-dossiers-expert`, `@proof-library-expert`, `@evaluation-expert` | Workstream experts | read, search, agent | **IMPLEMENTED**: `.github/agents/<name>.agent.md` |
| `@interpretation-advisor` | Pre-Stage-1 readings and provenance; advises G-FID | read-only | **IMPLEMENTED** (bespoke): `.github/agents/interpretation-advisor.agent.md` |
| Lean 4, Mathlib, leanblueprint, Pandoc tool guidance | Operational reference | n/a | **IMPLEMENTED**: `.claude/skills/tool-lean-4/SKILL.md`, `.claude/skills/tool-mathlib/SKILL.md`, `.claude/skills/tool-leanblueprint/SKILL.md`, `.claude/skills/tool-pandoc/SKILL.md` |
| `@statement-formalizer` | Stage 1; drafts Lean stubs for `MathAgentsWIP` (the orchestrator writes them, D39) | read, commands (D27, D39) | **IMPLEMENTED** (bespoke, D27): `.github/agents/statement-formalizer.agent.md` |
| `@fidelity-auditor` | Stage 1 back-translation | read-only | **IMPLEMENTED** (bespoke, D27): `.github/agents/fidelity-auditor.agent.md` |
| `@proof-strategist` | Stage 2 | read-only (D39) | **IMPLEMENTED** (bespoke, D27): `.github/agents/proof-strategist.agent.md` |
| `@logic-articulator` | Stage 3 | read-only (D39) | **IMPLEMENTED** (bespoke, D27): `.github/agents/logic-articulator.agent.md` |
| `@tactic-planner` | Stage 4 | read-only (D39) | **IMPLEMENTED** (bespoke, D27): `.github/agents/tactic-planner.agent.md` |
| `@lean-prover` | Stage 5; drafts Lean proofs, checked with `lake env lean --stdin` (the orchestrator writes them, D39) | read, `lake` and gates (D39) | **IMPLEMENTED** (bespoke, D27): `.github/agents/lean-prover.agent.md` |
| `@counterexample-hunter` | Stage 6 | read, commands | **IMPLEMENTED** (bespoke, D27): `.github/agents/counterexample-hunter.agent.md` |
| `@axiom-auditor` | Runs G-KERNEL and the other automated gates (dossier validator, G-NAME, G-BLUEPRINT, name index; the Stage 8 snapshot's preconditions, which the orchestrator then takes, D39) | read, commands | **IMPLEMENTED** (bespoke, D28): `.github/agents/axiom-auditor.agent.md` |
| `@engine-advisor` | Engine selection | read-only | **IMPLEMENTED** (bespoke, D28): `.github/agents/engine-advisor.agent.md` |
| `@lean-informalization` | Stage 7 | write | **IMPLEMENTED** (bespoke, D28): `.github/agents/lean-informalization.agent.md` |

The seven Stage 1–6 agents are bespoke (D27). `scripts/tests/test_stage_agents.sh` checks that each exists on all four surfaces, sits in `BESPOKE_AGENTS` and the orchestrator rosters, and carries the tools posture of charter §5 as amended in D27 and D39, on the Copilot, Claude Code and Codex projections. The orchestrator's pipeline duties (Stage 0 problem card, independent dispatch of `@fidelity-auditor`, writing every artifact the pipeline agents return, persisting back-translations, logging counterexample candidates, recording witnesses and waivers, taking the Stage 8 snapshot) are a `brief.json` style rule; since D39 the nine pipeline agents are researchers that write nothing and only the orchestrator writes. `@axiom-auditor`, `@engine-advisor` and `@lean-informalization` are bespoke under D28 and covered by the same test; `@lean-informalization` is a copy of the baseAgent agent with a provenance note (DD-31). Every stage dispatch is gated by `scripts/validate_dossier.py --require-stage <slug> N` (a `brief.json` style rule).

- [DD-24] The ten charter domain agents are bespoke agents whose canonical files live in `.github/agents/`, are listed in `BESPOKE_AGENTS` in `scripts/refresh_agent_surfaces.sh`, and reach the other agent surfaces through that refresh, re-rendered under D20; D24 covers `@interpretation-advisor`, and the operator's decision D27 extends the pattern to the seven Stage 1–6 agents, and D28 to `@axiom-auditor`, `@engine-advisor` and `@lean-informalization`.
- [DD-25] Each agent's tools posture from the charter's agent table is written into its front matter as a binding limit, as amended by D39 (only the orchestrator writes): only `@statement-formalizer` drafts Lean stubs, and only for `MathAgentsWIP`; only `@lean-prover` drafts Lean proofs; the orchestrator writes both; `@statement-formalizer`, `@lean-prover`, `@counterexample-hunter` and `@axiom-auditor` may run checking commands but write no file; and `@fidelity-auditor`, `@proof-strategist`, `@logic-articulator`, `@tactic-planner`, `@engine-advisor`, and `@interpretation-advisor` are read-only. Charter D34 extends the postures to every agent and surface: a surface may never grant more than the canonical `tools:` list, which `scripts/tests/test_stage_agents.sh` checks for all agents on the Claude, Codex and Goose surfaces in CI. The limit is enforced on Copilot and Claude Code; Codex's `sandbox_mode` is a default rather than a ceiling; the test requires `read-only` for read-only roles, some `sandbox_mode` for command-running roles, and `danger-full-access` for none (per-role write sets wait on agentteams), the twelve Codex gaps once tracked as known in that test were fixed by agentteams#100 and removed on 2026-10-05, and since D39 the command-running researchers are also required `read-only` on Codex; Goose read-only roles kept `developer` by accepted risk (D34); the bespoke recipes are now scoped to the `developer` tools their grant needs (`tree`, plus `shell` for command-running roles; `analyze` off), and the generated recipes still carry the whole extension under that accepted risk.
- [DD-26] `@fidelity-auditor` produces its back-translation independently of the Stage 1 drafter and passes it to G-FID as one more filter, never as the gate; this is charter policy D5, consistent with, not supported by, MR:C105, which the review itself labels charter policy.
- [DD-27] Automated alignment or back-translation scores reach G-FID as advisory inputs that do not replace human sign-off; this is charter policy D5, consistent with, not supported by, MR:C103, MR:C17, and MR:C127, which the review labels charter policy.
- [DD-28] `@engine-advisor` offers non-default engines at the start of each working session and whenever it judges another engine would help, and it offers only engines that the registry lists and the current machine's profile reports as present.
- [DD-29] No agent writes an approval into `references/axiom-allowlist.json`, a G-FID record, or a G-CX verdict, because approvals are human decisions and agent-authored clearances cannot currently be prevented by signing; the only exceptions are the records an agent writes under an operator's in-session kernel-as-judge directive, namely waivers under DD-35 and DD-59 and, when the operator extends the override to G-AX, allowlist approvals naming the operator as approver under DD-30.
- [DD-30] Whenever an agent requests feedback at G-FID or G-CX it also offers the kernel-as-judge override, and an accepted override is recorded in the session plan and applies to that conversation only; by default the override does not extend to G-AX, because the kernel accepts any declared axiom and the allowlist is human-only under DD-29, but the operator may explicitly extend it to G-AX within a session and direct the agent to proceed automatically, in which case the agent records each approval with the operator, via the in-session directive, as approver (operator decision D26)
- [DD-31] `@lean-informalization` is ported from its origin repository as a copy carrying a provenance note, never edited in place there; the port follows the founding charter §9 and is recorded in decision D28, and its re-rendering follows D20.

**Command limits are prose.** `@statement-formalizer`'s, `@lean-prover`'s, `@counterexample-hunter`'s and `@axiom-auditor`'s command grants are narrowed only in their bodies; a shell can write any file, so on Claude and Goose D39's "commands check, never author" rests on those bodies and the orchestrator (Codex runs them read-only). The gates (G-KERNEL, the G-FID and G-CX records, the append-only log) are the mechanical backstop.

**DD-29 is PARTIAL.** The allowlist rule is recorded in `docs/kernel-gate.md` and in the allowlist's own note. G-FID records and G-CX verdicts now exist as schema-checked records, and the rule is carried to every agent surface as a `brief.json` style rule, but nothing technically prevents an agent from writing an approval (D14a). The two operator commands refuse to run without an interactive terminal: `scripts/operator/record_gfid_approval.py`, and `scripts/preferences.py set` for the `gax.*` and `fidelity.*` settings, which record the operator's G-AX answers and kernel-as-judge policy. This is a guard against accidents, not authentication, because a shell can fake a terminal.

## Governance Gates

Each gate is listed with its status, what it blocks, how it fails closed, and its test. One rule applies to all of them:

- [DD-32] Every gate treats a missing input file, an unparseable record, or a tool that fails to run as a failure, so that no gate can pass by being unable to look.

**DD-32 is PARTIAL.**
- G-KERNEL and the citation, evidence, and claim validators already behave this way.
- Most of the other gates listed below are SPECIFIED.
- The methodology-coverage gate exits 0 when `reports/dossiers/` is absent or contains no unit. An empty dossier set therefore passes that gate today.

### G-FID: statement fidelity (human)

**Status:** **PARTIAL.**
- Fingerprint emission is **IMPLEMENTED** in `scripts/lean/AxiomAudit.lean`, run via `scripts/proof_integrity.py`.
- The fidelity record `reports/dossiers/<slug>/fidelity.json` (schema `references/schemas/fidelity-record.schema.json`) and its checker `scripts/validate_dossier.py` (G-FID module) are **IMPLEMENTED.**
- The dispatch precondition is carried to every surface as a `brief.json` style rule. CI runs the dossier validator on every relevant push and pull request (`.github/workflows/gates.yml`, D18); the transitive fingerprint (DD-34) is **IMPLEMENTED**.

**Blocks:**
- Stage 2 and later effort on the declaration. The mechanism to build is a precondition: `scripts/validate_dossier.py --require-fid <slug>` must exit 0 before the orchestrator dispatches `@proof-strategist`. The same command also runs in CI on every dossier, so a Stage 2 artifact committed without a matching record fails the build.
- Any plain "proved" wording in the dossier.

**Fails closed when:**
- the record is missing;
- the record lacks an approver or a date;
- the approved fingerprint differs from the one in the current `reports/kernel/latest.json`.

**Test (IMPLEMENTED):** `scripts/tests/test_fidelity_gate.sh`, 36 cases. A matching record must exit 0, and each of the spec's cases must exit 1:
- the approved fingerprint differs from the report;
- the record has no approver;
- a fidelity-waived result is labelled plain proved;
- a waiver record names no waiving conversation.

The suite also covers the following, all of which must exit 1:
- a missing record;
- a missing, failed or stale kernel report: the source hash covers library sources plus `lean-toolchain`, `lakefile.*` and `lake-manifest.json`, and is recomputed by the helper shared with G-KERNEL;
- partial coverage (`lean_namespace`), a namespace narrowed to a single declaration, and entries outside the namespace. Helper lemmas under `<namespace>.Aux.` and counterexample witnesses under `<namespace>.CX.` are not claims of the dossier and are exempt from coverage; in exchange, an approved statement must not reach them. `scripts/lean/AxiomAudit.lean` reports each declaration's `statement_uses` (the project constants its type reaches, followed through project definition bodies), and the gate fails an approved statement that uses an `Aux` or `CX` declaration, or a report that lacks the field;
- duplicate entries;
- a waiver reused outside its conversation (D5, D26);
- result labels in headings, bullets, tables or nested files;
- non-canonical labels;
- a proved label on a kernel-open declaration.

**Known limits:**
- Scan mode detects Stage 2 artifacts without a fidelity record through the dossier-structure module (DD-43).
- An approval written by an agent, a hand-edited kernel report with a matching hash, or a false `--conversation` value cannot be technically prevented (DD-29; D14a).
- Result labels are detected only in text files (`.md`, `.txt`, `.json`, `.csv`, `.yaml`, `.yml`, `.tex`), and only as a result, status, label, verdict, outcome or conclusion key with a value.

- [DD-33] G-FID is a human gate that blocks Stage 2 and later proving effort and blocks any proved label in a dossier, except the fidelity-waived label under DD-35, until a fidelity record approves the exact `statement_fingerprint` of the declaration; the reviewed findings neither force nor contradict keeping this gate human, so it rests on charter policy D1 and D5.
- [DD-34] The fingerprint audit is extended to hash every `MathAgents` definition a statement mentions transitively, so that changing such a definition lapses the G-FID approval just as changing the statement does.
- [DD-35] A result accepted under the kernel-as-judge override is labelled proved, fidelity-waived in its dossier and never plain proved, the label persists with the waiving conversation recorded, and only a later G-FID approval of the same fingerprint removes it; this is charter policy D5 and D1, consistent with, not supported by, MR:C127.

### G-AX: axioms, added hypotheses, weakened statements (human)

**Status:** **IMPLEMENTED.**
- **Axiom envelope.** `references/axiom-allowlist.json` is the single home of the envelope (DD-38): `base_axioms` (Lean's three standard axioms; a widened base is refused) and `approved_axioms`, each with a complete record (axiom, approver, date, reason, dossier). G-KERNEL and the registry validator load it through `scripts/axiom_allowlist.py`. The kernel report records the allowlist's path and hash, and the dossier validator rejects a report produced with any other allowlist; a non-default `--allowlist` may not write the authoritative report.
- **Statement changes.** The G-AX module of `scripts/validate_dossier.py` compares each fidelity record with its state at the base and at `HEAD`: a declaration that was approved and now carries a different fingerprint, or no entry, needs a record in `reports/dossiers/<slug>/gax.json` (schema `references/schemas/gax-record.schema.json`) naming the old and new fingerprints and the kind of change, approved by a human or waived under the operator's in-session G-AX extension (D26; a new waiver counts only with its `--conversation`, and forces the label `proved, fidelity-waived`). `gax.json` is append-only, and a dossier with gate records can be removed only by a human tombstone `reports/dossiers/<slug>.retired.json` that lists every declaration its fidelity record approved.

**Blocks:**
- any declaration that depends on an axiom outside the envelope;
- any approved statement whose fingerprint changes without a G-AX record.

**Fails closed:** G-KERNEL marks the dependent declaration `failed` and exits 1.

**Tests (IMPLEMENTED):** `scripts/tests/test_mathagents_gates.sh` ("axiom: source + envelope", "WIP still rejects unapproved axioms", the DD-34 fingerprint and the path-dependency ban) and `scripts/tests/test_axiom_governance.sh`, 22 cases, including the four the spec required: an incomplete approval record (registry), an approved axiom with no record (both validators), namespaced and `_root_` axiom probes on real Lean, and a fingerprint change on an approved declaration without a G-AX record.

**Known limits:**
- Fingerprints stop at the Mathlib boundary: a Mathlib bump (which changes `lake-manifest.json`, so every kernel report is re-run) leaves approvals standing even if a Mathlib definition a statement uses changed meaning.
- A `partial def` is opaque to the kernel; editing its body does not change the fingerprint, and statements about it are not meaningfully pinned.
- Fingerprints combine Lean's structural expression hashes; they detect change, not adversarial collisions.
- Approver strings are unauthenticated (DD-29; D14a).

- [DD-36] G-AX blocks any axiom beyond `{propext, Classical.choice, Quot.sound}`, any hypothesis added to an approved statement, and any weakening of an approved statement until a human approval record exists; no reviewed finding addresses the governance of added axioms, hypotheses, or weakened statements, so this rests on charter policy D5.
- [DD-37] An added hypothesis or a weakened statement is detected as a `statement_fingerprint` change on a declaration that already holds a G-FID approval, and the dossier validator then requires a G-AX record naming the old and new fingerprints before the new statement can be approved.
- [DD-38] The base axiom set is defined once, in `references/axiom-allowlist.json`, and both G-KERNEL and the registry validator load it through one shared function; this is an open gate follow-up in the decision record rather than a numbered decision, cited to D18, which settles the CI part of those follow-ups.


### G-CX: counterexample verdicts (human)

**Status:** **IMPLEMENTED.** Verdicts go in `reports/dossiers/<slug>/counterexamples.json` (schema `references/schemas/counterexample-log.schema.json`) and are checked by the G-CX module of `scripts/validate_dossier.py`, which runs on every dossier in scan mode, and in CI with the pull request's base (D18).

**Blocks:** labelling a statement refuted, and revising a statement in response to a counterexample.

**Fails closed:** a dossier that marks a statement refuted, or revises it after a logged counterexample, fails unless a human verdict carries the statement's current fingerprint. In detail, it fails when:
- a verdict's fingerprint differs from the target's fingerprint in the current, fresh kernel report;
- a target's fingerprint has changed since its counterexample was logged, and there is no `revise` verdict on the new fingerprint;
- a target named in the log is absent from the kernel report;
- a refutation label does not name its target, as in `Result status: refuted (Pilot.conj)`, or names a target with no current human `refutes` verdict, or a target that is `proved` in the kernel report;
- a `decide`, SMT or ATP refutation has no kernel-proved `lean_witness` (DD-16; a `decide` result counts only as a Lean declaration), or a witness does not negate exactly the logged statement. A witness is written `theorem cx_<n> : ¬ (type_of% @<target>)`, or, for a target revised since logging, with the logged statement written out in full; `scripts/lean/AxiomAudit.lean` reports the fingerprint of `X` for every theorem of type `¬ X` as `negates_fingerprint`, and the gate requires it to equal the fingerprint the counterexample was logged against;
- a waived `refutes` or `revise` verdict has no kernel-proved `lean_witness`, a waived `spurious` verdict's target is not `proved` in the kernel report, or a waived refutation is labelled plain `refuted` (DD-59);
- a verdict has neither an approver and date nor a waiver, or has both;
- the log is not append-only against the base commit: an entry was removed, the log or its dossier directory was deleted or renamed, or an entry's `decl`, `statement_fingerprint` or `method` changed. The base is `--base REF`, or by default the merge base of `HEAD` with `origin/HEAD`, the default branch, so an edit committed or pushed on a feature branch is still compared with the default branch; the log is also compared with `HEAD`, so an entry committed locally cannot be removed either; with no `origin/HEAD` and no `--base` the check fails closed. Every commit between the base and `HEAD` that touches a dossier record is also compared with its parent under the same rules (and the G-AX and deletion rules), so a change made in one commit and undone in a later one is caught; `--no-history` turns this walk off (IA-01). Candidates are written only through `scripts/log_counterexample.py add`, which takes the fingerprint from a fresh kernel report and never writes a verdict, and witnesses only through `log_counterexample.py witness`, which applies the same binding check;
- the log's `lean_namespace` differs from the fidelity record's;
- a label is non-canonical ("disproved", "refuted by …", "false", "not a theorem", "counterexample found"), or the dossier carries both a proved and a refuted label.

Label detection, shared with G-FID, covers `key: value` lines (quoted JSON or YAML keys and `result_status` included), Markdown table columns whose header ends in a key or reads "<key> of/on/for …" (such as "Kernel status"), and such a heading followed by its first line. The status keys (result, status, verdict) take the broad vocabulary above anywhere in the value; the loose keys (label, outcome, conclusion) take proof and refutation words anywhere, and the broad words only when the value opens with one, so mathematical prose such as "Conclusion: the converse is false without positivity" is not a label while "Outcome: false" is. An unquoted JSON or YAML boolean is not a label under a loose key, but is one under a status key. The two record files are not scanned for labels.

**Test (IMPLEMENTED):** `scripts/tests/test_counterexample_gate.sh`, 90 cases, including the two the spec required: a dossier labelled refuted with no verdict, and one whose verdict fingerprint is stale, both exit 1. The gate was revised after an `@adversarial` review returned BLOCKED on five fail-opens: unscanned JSON and underscore keys, a narrow label vocabulary, a log that could be edited to hide a revision, labels not bound to a target, and waived non-refuting verdicts without a witness. A second round returned BLOCKED on labels in table columns and under headings, and recommended the upstream merge-base default; both are fixed, together with three regressions it found. A third round returned CLEARED on condition that the default base be the default branch rather than the current branch's upstream; that change is made, with its follow-ups. The stage-agent review then found that a waived refutation could rest on an unrelated proved theorem; the `negates_fingerprint` binding closes that.

**Known limits:**
- A verdict written by an agent, or a false waiver conversation, cannot be technically prevented (DD-29; D14a).
- The witness binding compares type hashes. A universe-polymorphic target, or a hand-written statement that elaborates differently from the logged one, hashes differently and is then rejected (fail closed); prefer `type_of%` whenever the target is unrevised.
- Unverdicted candidates on an unchanged statement pass; the gate does not force a verdict before Stage 5 continues.
- The append-only check trusts its refs: an entry never committed, or a rewritten upstream history, is outside it. CI on a detached checkout must pass `--base` explicitly. On `main`, CI passes the last commit with a successful Gates run that is an ancestor of `HEAD`, or the root commit when there is none, so a commit whose own run was cancelled, failed or skipped is still walked (IA-01).
- The label vocabulary cannot be complete: synonyms such as "falsified" or "does not hold" are not detected, nor is a refutation word more than 200 characters into its clause.
- Setext headings and tables inside blockquotes are not parsed as labels.
- A dossier cannot carry a refuted original and a proved corrected statement together: the validator forbids proved and refuted labels in one dossier (per-declaration result labels are future work).
- Each entry holds one verdict, so a later statement change makes the verdict stale; earlier verdicts survive only in git history.
- Witnesses must lie inside the dossier's `lean_namespace`.
- Labels are detected only in the text file types listed under G-FID, and only inside the dossier directory.

- [DD-39] G-CX is a human gate that blocks declaring a statement false, and blocks revising it in response to a counterexample, until a human verdict, or a waiver under DD-59, is recorded against the statement's fingerprint; no reviewed finding addresses counterexample verdicts, so this rests on charter policy D5.
- [DD-59] A G-CX verdict accepted under the kernel-as-judge override counts only when a `lean_witness` re-establishing the counterexample is `proved` in the G-KERNEL report, and the dossier is then labelled refuted, verdict-waived and never plain refuted, mirroring DD-35; this is charter policy D5 and D26, with no reviewed finding behind it.

### G-KERNEL: proof integrity (automated)

**Status:** **IMPLEMENTED.**
- Entry point: `scripts/check_proof_integrity.sh`.
- Implementation: `scripts/proof_integrity.py` and `scripts/lean/AxiomAudit.lean`.
- Documentation: `docs/kernel-gate.md`.
- Output: `reports/kernel/latest.json`.

**Blocks:** the `proved` status for any declaration with a finding. The gate runs five layers: config scan, source scan, `lake build`, `leanchecker` replay, and axiom envelope.

**Fails closed:**
- exit 1 on any finding, including a tool that fails to run;
- exit 2 on an internal error;
- the previous report is deleted at the start of every run, so a crash cannot leave a stale PASS behind.

**Existing test:** `scripts/tests/test_mathagents_gates.sh`. It seeds sorry, stop, admit, `native_decide`, `+native`, an unapproved axiom, a private theorem, `#eval`, an unchecked `False` declaration, and a kernel-weakening option, plus five WIP cases.

**Test to build:** dedicated `unsafe`, `implemented_by`, and `extern` probes. Today those tokens are covered only by the source-scan token list.

**CI:** **IMPLEMENTED**: `.github/workflows/gates.yml`. It runs on pushes to `main` and `release/**`, on `v*` tags, and on pull requests that touch `lean/`, `scripts/`, `references/`, `reports/dossiers/`, any agent surface (`.github/agents/`, `.claude/`, `.codex/`, `.goose/`, `.agents/`, `AGENTS.md`; D34), `blueprint/`, `mathagents/`, `tests/`, `docs/api-reference/`, `pyproject.toml`, `toolchain.lock`, the workflow or `brief.json`; weekly on Tuesday and monthly on the 1st; and on demand. Every run uses the pinned GitHub-hosted image (`ubuntu-24.04`); D45 retired D37's self-hosted fallback runner. The long suites (the G-KERNEL gate tests and the Lean half of the G-AX tests) run in their own `long-suites` job only where they can matter (D46, superseding D36): on dispatch, `v*` tags, `release/**` pushes and the monthly schedule; on a pull request that changes one of their inputs (`scripts/ci_long_suite_inputs.txt`); on a push to `main` that its pull request's run did not already cover; and whenever the decision (`scripts/ci_long_suites.py`) cannot be made. The weekly schedule runs the other gates only. It installs Lean with `scripts/install_lean.sh` (a pinned, hash-verified elan installer) and fetches the Mathlib cache, then runs, each in its own step, G-KERNEL, the Mathlib name index, the G-KERNEL, G-FID, G-CX, G-AX (validator half; D46), dossier-structure, G-NAME and G-BLUEPRINT test suites, G-NAME on every dossier, G-BLUEPRINT when a blueprint exists, the registry validator, the stage-agent test, the workflow self-check, and the dossier validator with `--base` set to the pull request's base or, on `main`, the last commit with a successful Gates run (IA-01; the workflow has `actions: read` for this). A newer push cancels an older run; the per-commit history walk makes that safe.

**CI test (IMPLEMENTED):** `scripts/tests/test_ci_workflow.py` parses the workflow and fails unless all of the following hold:
- push and pull-request triggers carry path filters on `lean/`, `scripts/`, `references/`, `reports/dossiers/` and every agent surface, with no `paths-ignore`;
- a weekly schedule exists;
- one step runs `scripts/check_proof_integrity.sh` and another runs `scripts/tests/test_mathagents_gates.sh`, and steps run the G-FID, G-CX, G-AX, dossier-structure, G-NAME and G-BLUEPRINT suites, the name-index build, G-NAME, G-BLUEPRINT and the dossier validator with `--base` set to the last verified commit on `main` (never `HEAD` or `HEAD~1`, never `--no-history`);
- no job or step sets `continue-on-error`, and no gate step swallows its exit code;
- the workflow can read Actions runs (`actions: read`), every job that runs Lean installs it with `scripts/install_lean.sh`, and no step pipes a download into a shell.
- every job's `runs-on` is exactly the pinned hosted image `ubuntu-24.04`, every job starts with the hosted-runner guard (it fails on any self-hosted runner; D45), and the conditional `long-suites` job is decided by `scripts/ci_long_suites.py`, which forces it on dispatch, tags, release lines and the monthly cron, the job runs when its decision job fails, both crons match the script's, and both halves of the G-AX tests run (D45, D46).

It also mutates the workflow in memory, one or more mutations per rule, and fails unless each mutation is rejected.

- [DD-40] G-KERNEL is the sole authority on whether a declaration is proved, issuing per-declaration `proved`, `open`, or `failed` verdicts and treating every non-zero exit, including a crash of the gate itself, as a failure.
- [DD-41] G-KERNEL runs in CI on every push to `main` and every pull request touching the paths above, and on a weekly schedule; its long suites run on releases, dispatch, the monthly schedule, pull requests that change their inputs, pushes to `main` not already covered by the merged pull request's run, and whenever the decision fails (D46).

### G-BLUEPRINT: marker consistency (automated)

**Status:** **IMPLEMENTED**: `scripts/check_blueprint_consistency.py`. It reads `lean/blueprint/` (where `leanblueprint new` scaffolds the project; a top-level `blueprint/` also counts) and runs in CI whenever a blueprint exists, and in `validate_dossier.py --require-stage <slug> 8`.

**Blocks:** blueprint publication and Stage 8 assembly.

**Fails closed:** the check fails when the blueprint, the kernel report or the name index is absent or stale, when a `\lean{}` name resolves to no declaration, or when a `\leanok` node names no declaration or names one that is not `proved`. A proof environment is bound to the statement its `\proves{label}` names (an unknown label fails), or else to the theorem-like statement before it (a standard statement environment, or any non-proof environment carrying `\lean` or `\label`, so custom node types count; duplicate labels fail), so a proof's `\leanok` also requires that statement's declarations to be `proved`. A `\leanok` outside any parsed environment, or a macro or environment definition that mentions `\lean`/`\leanok` (in `.tex`, `.sty` or `.cls` files, across lines), or a `leanok` written other than as a literal `\leanok`, fails; LaTeX comments and URLs are stripped first. Every blueprint that exists (`lean/blueprint/`, `blueprint/`) is checked. The name resolution is the check `leanblueprint checkdecls` performs, made against the same pinned environment through the name index (`scripts/build_name_index.py`), so the blueprint needs no `checkdecls` Lake dependency, which would change `lake-manifest.json`.

**Test (IMPLEMENTED):** `scripts/tests/test_blueprint_gate.sh`, 25 cases, including the spec's: a `\leanok` node bound to an `open` WIP stub, and a `\lean{}` name that does not exist, each exit 1, and a node bound to a `proved` declaration passes.

**Known limit:** a `\leanok` in a statement environment is held to the same bar as one in a proof (the named declaration must be `proved`), which is stricter than leanblueprint's convention.

- [DD-42] A blueprint check fails whenever a `\leanok` marker sits on a node whose named declaration is not `proved` in the G-KERNEL report or whenever `leanblueprint checkdecls` cannot resolve a `\lean{}` name, because the review reads `\leanok` as an author's declaration and the retrieved README excerpt describes no check against kernel status.

### G-NAME: Lean name binding (automated)

**Status:** **IMPLEMENTED**: `scripts/check_lean_bindings.py`. It implements DD-17 and the mechanical half of DD-18 (a narrated "proved" must bind a `proved` declaration); that narration adds no other claim stays a `@technical-validator` review. It runs on every dossier in CI and in `validate_dossier.py --require-stage <slug> 8`.

**Name index:** `scripts/build_name_index.py` imports the pinned Mathlib and writes every non-internal, non-private constant name (about 470,000) to `reports/kernel/name-index.txt` (gitignored), with a header binding it to `lean-toolchain` and the SHA-256 of `lake-manifest.json`. It is a generated name index rather than doc-gen documentation; it answers the same question DD-17 asks, which declarations exist in the pinned environment. It skips matchers, auxiliary recursors and deprecated aliases, and refuses to write if the toolchain or manifest changed during the build. It needs the Mathlib build cache (`lake exe cache get`).

**Blocks:** Stage 8 assembly when a `[Lean: name]` or a tactic-plan lemma resolves to neither of:
- a declaration in `reports/kernel/latest.json`;
- an entry in the name index for the pinned Mathlib.

**Fails closed:** a missing, stale or malformed index (count mismatch, or a project name in it) counts as unresolved; a tactic-plan lemma marked `(UNVERIFIED)` fails; anything that looks like a binding or a lemma item but does not parse fails, as does an unterminated `[Lean:`; and the `Lean:` name of every `## Node:` header in `tactic-plan.md` and `derivations.md` is resolved. Bindings are matched case-insensitively and across lines. Under DD-18, a binding may carry a status tag, `[Lean: X | open]` (proved, open, failed, refuted), which must match the kernel report (`refuted` only for a target the dossier labels `Result status: refuted (<decl>)` under G-CX); a declaration that is not `proved` must be bound with its tag, and its paragraph must not call it proved.

**Known limits:** the index is a local, gitignored artifact rebuilt by CI; a hand-forged local index is a DD-29-class trust limit for local `--require-stage 8` runs. The DD-18 check is lexical: the status tag pins each binding, but prose around it is reviewed by `@technical-validator`, not parsed.

**Test (IMPLEMENTED):** `scripts/tests/test_lean_bindings.sh`, 34 cases, including the spec's: a dossier citing an invented name, and one citing an `open` declaration as proved, each exit 1.

### Dossier structure (automated)

**Status:** **IMPLEMENTED**: `scripts/dossier_structure.py`, run by `scripts/validate_dossier.py`, which also hosts the G-FID, G-AX and G-CX record checks. Scan mode checks the artifacts that exist (a pre-intake dossier holding only its Interpretation Brief passes; any other artifact makes the problem card mandatory, and empty artifacts fail). `--require-stage <slug> N` is the dispatch precondition: the artifacts of every stage before N must exist, N ≥ 2 implies `--require-fid`, N ≥ 3 needs a `CLEARED` strategy review, and N ≥ 7 needs every approved declaration proved or refuted under G-CX. The Stage 8 snapshot is produced by assembly, so it is checked when present rather than required for dispatch.

**Blocks:**
- dispatch of the next stage's agent, used as an orchestrator precondition;
- Stage 8 assembly;
- CI on any change under `reports/dossiers/`.

**Fails closed:** exit 1 when any required artifact is absent or unparseable, or when artifacts disagree.

**Test (IMPLEMENTED):** `scripts/tests/test_dossier_gate.sh`, 59 cases, including the four the spec required (no problem card; a derivation step naming no rule; no strategy review; a kernel snapshot whose fingerprint differs from the fidelity record), card and registry checks, derivation parsing (numbering forms, steps outside nodes, empty nodes, missing and forward citations, fenced examples), forged and stale snapshots, stage preconditions, and the security conditions on slugs, `--root`, `--base` and the allowlist.

**Known limits:** the derivation check is structural (DD-11): a named rule is not checked against a calculus, so `[obvious]` passes; and the problem card's Source is not checked against the bibliography.

- [DD-43] A single dossier validator checks, per dossier, that the problem card, fidelity record, Stage 2 review record, Stage 3 derivation records with a named rule or lemma at every step, and kernel snapshot exist and are mutually consistent, and an absent or unparseable artifact counts as a failure, never as a skip.

### Citation, evidence, and claim gates (automated)

**Status:** **IMPLEMENTED**:
- `scripts/check_citation_integrity.sh`;
- `scripts/validate_evidence.py`;
- `scripts/validate_claim_ledger.py`.

**Blocks:** compilation of any prose deliverable.

**Fails closed:** each script exits 1 on any finding.

**Existing test:** `scripts/tests/test_citation_integrity.sh`.

**Test to build:** `scripts/tests/test_claim_ledger.sh`. Each of these must exit 1:
- a ledger row whose claim is not verbatim in the deliverable;
- a policy row that cites an unknown decision id;
- a decision tag that appears in two ledger rows.

- [DD-44] Every prose deliverable passes the citation-integrity check, the evidence-layer validator, and the claim-ledger validator before compilation, and this specification is itself held to that ledger through its decision tags.

### Registry gate (automated)

**Status:** **IMPLEMENTED**: `scripts/validate_registries.py`.

**Blocks:** any change to `references/prover-engines.json`, `references/object-logics.json`, or `references/axiom-allowlist.json` that would break the registries. It runs within `scripts/check_render_consistency.sh` and, once DD-41 is built, in CI.

**Fails closed:** exit 1 on any of the following, and an uncaught error, including a missing `jsonschema` module, also exits non-zero:
- a schema violation;
- an unsourced capability claim;
- a duplicate id;
- an unresolved default;
- an incomplete approval record.

**Existing test:** the unsourced-claim case in `scripts/tests/test_mathagents_gates.sh`.

**Test to build:** `scripts/tests/test_registries.sh`, with cases for a duplicate id, an unresolved default, and an incomplete approval record.

### Methodology-coverage gate (automated)

**Status:** **IMPLEMENTED**: `scripts/check_methodology_coverage.sh`. It is configured through `methodology_coverage` in `brief.json`, which resolves the decision record's open item on retargeting this gate.

**Blocks:** compilation of deliverables while any dossier unit lacks coverage.

**Fails closed:** exit 1 when a unit lacks `interpretation.md` or names a methodology guide that does not exist. As noted under DD-32, it exits 0 when there are no units.

**Existing test:** `scripts/tests/test_methodology_coverage.sh` is upstream-only. It exercises researchteam's default layout, not this repository's configuration.

**Test to build:** `scripts/tests/test_dossier_coverage.sh`. It runs against a fixture `reports/dossiers/<slug>/` with no `interpretation.md` and expects exit 1.

- [DD-45] The methodology-coverage gate treats every directory under `reports/dossiers/` as a unit and fails when its `interpretation.md` is missing or names a methodology guide that does not exist, and it exits 0 when no units exist (orchestrator clarification C4).

### Render-consistency gate (automated)

**Status:** **IMPLEMENTED**: `scripts/check_render_consistency.sh`, the final step of `scripts/refresh_agent_surfaces.sh`.

**Blocks:** acceptance of an agent-surface re-render, which D20 treats as non-destructive.

**Fails closed:** exit 1 when any of the following fails, including the embedded G-KERNEL and registry runs:
- roster parity;
- stale references;
- Goose sub-recipes;
- the Codex projection;
- skill parity;
- the home-path check.

**Existing test:** none beyond the script itself.

**Test to build:** `scripts/tests/test_render_consistency.sh`. It uses a fixture with mismatched build-log rosters and expects exit 1.

## Engine and Object-Logic Registries

### Prover-engine registry

The registry is `references/prover-engines.json`. `scripts/validate_registries.py` validates it against `references/schemas/prover-engines.schema.json`.

| Field | Content | Status |
|---|---|---|
| `id`, `name`, `kind`, `logic_fragment`, `install`, `probe` | Identity, engine class, logic fragment, installation route, profile key | **IMPLEMENTED** |
| `strengths`, `suited_domains`, `unsuited_for` | Capability claims, each requiring sources | **IMPLEMENTED**; no entry makes one yet |
| `resource_needs` | Static requirements: GPU, parameters, weight sizes | **IMPLEMENTED** |
| `result_trust` | `kernel-checked` or `hint-until-kernel-recheck` | **IMPLEMENTED**; kind-conditional constraint **SPECIFIED** |
| `evidence_status`, `sources` | Review state and citations | **IMPLEMENTED**; source resolution **SPECIFIED** |
| `paradigm`, `interface` | Generation paradigm and required interface | **SPECIFIED** |
| `local_status` | Availability | Removed from the registry under D10 |

**Contents today:**
- Lean built-ins, Z3, cvc5, Vampire, E, and four LLM provers, all at `evidence_status` `pending-review`;
- empty `sources` for the SMT and ATP entries, consistent with the review's labelling of those systems as unverified;
- no `interaction-layer` entries.

**Tests to build:** each must fail:
- an `smt` engine with `result_trust` `kernel-checked`, which must fail schema validation;
- a `sources` entry that is neither a bibliography key nor a URL;
- a registry engine missing from the profile's probe list, which must fail a probe-coverage test.

- [DD-46] Each engine entry gains a `paradigm` field naming its generation paradigm and an `interface` field stating whether it needs an interactive proof-state interface or only a compiler, a distinction that is the review's own inference from preprint descriptions rather than a reported finding.
- [DD-47] Every engine of kind `smt` or `atp` carries `result_trust` value `hint-until-kernel-recheck`, and its results enter the harness only after reconstruction or re-proof in Lean, by analogy with the proof reconstruction that the hammer survey counts among a hammer's ingredients.
- [DD-48] Every engine of kind `llm-prover` also carries `hint-until-kernel-recheck`, which is charter policy that the review finds consistent with, but not established by, its sources.
- [DD-49] No published benchmark figure or sampling budget is copied into the prover-engine registry or the per-machine profile as an expectation for a local run, because the reviewed figures are tied to stated budgets and describe published experiments.
- [DD-50] The registry's `resource_needs` records only static requirements such as GPU need, parameter count, and weight sizes from cited model cards or documentation, while measured performance belongs in the per-machine profile; this split is charter policy D10, and no reviewed finding concerns model cards.
- [DD-51] Engine availability is never recorded in the registry; `scripts/probe_machine.py` derives the engines it probes from the registry's `probe` keys and writes availability to `.machine/profile.json`.
- [DD-52] Interaction layers enter the registry with capability claims only when the claim cites a verified source, which would admit LeanDojo and Lean Copilot and excludes Pantograph and a Lean LSP or MCP server; no reviewed finding characterizes those two layers, so their exclusion rests on charter policy D6.
- [DD-53] A capability claim's `sources` entries resolve to keys in `reports/references/bibliography.bib` or to official documentation URLs, and `evidence_status` becomes `verified` only after `@reference-manager` confirms them.

The probe list in `scripts/probe_machine.py` is hard-coded today, so the derivation in DD-51 is **SPECIFIED**.

### Object-logic registry

The registry is `references/object-logics.json`, validated against `references/schemas/object-logics.schema.json`.

| Field | Content | Status |
|---|---|---|
| `id`, `name`, `family` | Identity and family enum | **IMPLEMENTED** |
| `proof_systems`, `semantics` | The calculi and semantics available to Stage 3 | **IMPLEMENTED** |
| `embedding` | `native`, `deep`, or `shallow` | **IMPLEMENTED**; family-conditional constraint **SPECIFIED** |
| `lean_module`, `status`, `pilot` | Library location, maturity, pilot link | **IMPLEMENTED** |
| `cross_checks`, `sources` | Reference formalizations and citations | **IMPLEMENTED**; source resolution **SPECIFIED** |

**Entries today:**
- `classical-hol`: available, native;
- `modal-k`: planned, deep, pilot P4;
- `finite-probability`: available, shallow, pilot P3, in `MathAgents.FiniteProbability`;
- `stalnaker-conditional`: planned, deep, pilot P2.

**Cross-check provenance:** the `modal-k` cross-check URL points to a repository that is not in the Phase 1 inventory. The inventory's Lean 4 logic library is a different repository, and its coverage is not established.

**Tests to build:** each must fail:
- a `modal` family entry marked `shallow`;
- a `cross_checks` entry that resolves to nothing.

- [DD-54] Non-classical object logics are deep embeddings in Lean, with syntax, a proof system or semantics, and soundness where needed, a charter decision on which the reviewed evidence is neutral.
- [DD-55] Entries in `cross_checks` serve as reference statements to re-prove in Lean 4, never as libraries to import, since the mechanized modal metatheory the review found is in Lean 3 or Isabelle/HOL, and the one Lean 4 logic library is treated the same way until its coverage is established.
- [DD-56] Object logics of the families `intuitionistic`, `deontic`, `conditional`, `probabilistic`, `substructural`, and `paraconsistent` stay at status `planned` with no capability claim until a verified source supports their embedding; no reviewed finding establishes any of them as a declared Lean object logic, so this rests on charter policy D4.
- [DD-57] A probability theory over a finite Boolean algebra is classified as a theory inside `classical-hol`, registered with family `classical`, and may remain a shallow formalization, while a probabilistic logic over a deeply embedded conditional language, as P2 needs, is a deep embedding; this follows orchestrator clarification C3 under D4.
- [DD-58] The registry validator rejects `embedding` value `shallow` for every family other than `classical`, so a finite-algebra probability theory must be registered as `classical` under clarification C3; `scripts/tests/test_mathagents_gates.sh` checks the rejection.

### Axiom allowlist and machine profile

- **Axiom allowlist:** `references/axiom-allowlist.json` is **IMPLEMENTED**. DD-36 and DD-38 govern it.
- **Machine profile:** `.machine/profile.json` is written by `scripts/probe_machine.py` (**IMPLEMENTED**). DD-28 and DD-51 govern it.

## Traceability Table

| Decision | Element | Basis kind | Review claim ids or charter ids | Status |
|---|---|---|---|---|
| DD-1 | Stage 0 problem card | policy | charter:D2; charter:D4; charter:D6 | IMPLEMENTED |
| DD-2 | Interpretation Brief before Stage 1 | policy | charter:D24; charter:D5 | IMPLEMENTED |
| DD-3 | Stage 1 automated drafting | design-inference | MR:C142; MR:C126; MR:C17 | SPECIFIED |
| DD-4 | Stage 1 elaboration precondition | design-inference | MR:C104; MR:C12; MR:C18 | SPECIFIED |
| DD-5 | Stage 1 stubs in WIP library | policy | charter:C2 | IMPLEMENTED |
| DD-6 | Stage 2 blueprint DAG | design-inference | MR:C39; MR:C24 | SPECIFIED |
| DD-7 | Stage 2 informal skeleton | policy | charter:D3 | SPECIFIED |
| DD-8 | Stage 2 loop-back to Stage 1 | policy | charter:D1; charter:C2 | SPECIFIED |
| DD-9 | Stage 2 adversarial review | policy | charter:D3; charter:D5 | PARTIAL |
| DD-10 | Stage 3 record names calculus and logic | design-inference | MR:C115; MR:C87 | PARTIAL |
| DD-11 | Stage 3 calculus and rule-check | policy | charter:D3 | SPECIFIED |
| DD-12 | Stage 4 tactic plan as sketch | design-inference | MR:C108; MR:C31; MR:C22 | SPECIFIED |
| DD-13 | Stage 5 error-conditioned iteration | design-inference | MR:C108; MR:C40; MR:C29; MR:C30 | SPECIFIED |
| DD-14 | Stage 5 proved status | policy | charter:D1; charter:C2 | IMPLEMENTED |
| DD-15 | Stage 6 counterexample track | policy | charter:D5 | SPECIFIED |
| DD-16 | Stage 6 solver counterexamples | policy | charter:D6; charter:D5 | IMPLEMENTED |
| DD-17 | Stage 7 name binding | design-inference | MR:C109; MR:C41; MR:C37 | IMPLEMENTED |
| DD-18 | Stage 7 no net-new claims | policy | charter:D1 | PARTIAL |
| DD-19 | Stage 8 kernel snapshot | policy | charter:D1; charter:C2 | IMPLEMENTED |
| DD-20 | Evaluation reporting fields | design-inference | MR:C113; MR:C78 | SPECIFIED |
| DD-21 | Evaluation local versus published figures | policy | charter:D7; brief:evaluation | SPECIFIED |
| DD-22 | Evaluation mis-formalization category | design-inference | MR:C114; MR:C137 | SPECIFIED |
| DD-23 | Evaluation miniF2F Lean 4 port | policy | charter:D7 | SPECIFIED |
| DD-24 | Domain agents as bespoke agents | policy | charter:D24; charter:D20; charter:D27; charter:D28 | IMPLEMENTED |
| DD-25 | Tools postures binding | policy | charter:D3; charter:D24; charter:D34 | PARTIAL |
| DD-26 | Fidelity auditor back-translation | policy | charter:D1; charter:D5 | SPECIFIED |
| DD-27 | Alignment scores advisory | policy | charter:D1; charter:D5 | SPECIFIED |
| DD-28 | Engine advisor offers | policy | charter:D6; charter:D10 | IMPLEMENTED |
| DD-29 | No agent-authored approvals | policy | charter:D5; charter:D14a; charter:D21; charter:D26 | PARTIAL |
| DD-30 | Kernel-as-judge override: G-FID and G-CX by default; G-AX only by explicit in-session operator extension | policy | charter:D5; charter:D26 | SPECIFIED |
| DD-31 | Informalization agent port | policy | charter:D20; charter:D28 | IMPLEMENTED |
| DD-32 | All gates fail closed on missing input | policy | charter:D1; charter:D18 | PARTIAL |
| DD-33 | G-FID | policy | charter:D1; charter:D5 | PARTIAL |
| DD-34 | G-FID transitive fingerprint | policy | charter:D1; charter:C2 | IMPLEMENTED |
| DD-35 | Fidelity-waived label | policy | charter:D1; charter:D5 | IMPLEMENTED |
| DD-36 | G-AX | policy | charter:D5 | IMPLEMENTED |
| DD-37 | G-AX hypothesis and weakening detection | policy | charter:D5; charter:C2 | IMPLEMENTED |
| DD-38 | Base axiom set single home | policy | charter:D18 | IMPLEMENTED |
| DD-39 | G-CX | policy | charter:D5; charter:D26 | IMPLEMENTED |
| DD-40 | G-KERNEL | policy | charter:D1; charter:C2 | IMPLEMENTED |
| DD-41 | G-KERNEL in CI | policy | charter:D18 | IMPLEMENTED |
| DD-42 | G-BLUEPRINT | design-inference | MR:C107; MR:C39; MR:C25 | IMPLEMENTED |
| DD-43 | Dossier validator | policy | charter:D1; charter:D3 | IMPLEMENTED |
| DD-44 | Citation, evidence, and claim gates | policy | charter:D25 | IMPLEMENTED |
| DD-45 | Methodology-coverage gate | policy | charter:C4 | PARTIAL |
| DD-46 | Engine `paradigm` and `interface` | design-inference | MR:C110; MR:C64; MR:C61 | SPECIFIED |
| DD-47 | SMT and ATP `result_trust` | design-inference | MR:C111; MR:C116; MR:C62; MR:C86 | IMPLEMENTED |
| DD-48 | LLM-prover `result_trust` | policy | charter:D6; charter:D1 | IMPLEMENTED |
| DD-49 | No published figure transferred | design-inference | MR:C112; MR:C63; MR:C66 | IMPLEMENTED |
| DD-50 | Static versus measured resources | policy | charter:D10 | IMPLEMENTED |
| DD-51 | Availability in machine profile | policy | charter:D10 | SPECIFIED |
| DD-52 | Interaction-layer entries | policy | charter:D6 | SPECIFIED |
| DD-53 | Engine source resolution | policy | charter:D25; charter:D6 | SPECIFIED |
| DD-54 | Deep embedding of object logics | policy | charter:D4 | SPECIFIED |
| DD-55 | Object-logic `cross_checks` | design-inference | MR:C117; MR:C100; MR:C102 | SPECIFIED |
| DD-56 | Non-classical families stay planned | policy | charter:D4 | IMPLEMENTED |
| DD-57 | Finite probability as a classical theory | policy | charter:D4, C3 | IMPLEMENTED |
| DD-58 | Shallow-embedding check | policy | charter:D4, C3 | IMPLEMENTED |
| DD-59 | Waived G-CX verdict | policy | charter:D5; charter:D26 | IMPLEMENTED |

**Reading the Status column.** Status describes each element as the repository stands today:
- IMPLEMENTED means the files cited above enforce or embody the decision. For DD-2, DD-47 through DD-50, DD-56, and DD-57, that is the current content of the registries or briefs. The matching automated checks remain SPECIFIED where the sections above say so.
- PARTIAL marks decisions of which only a part is in force, as stated in their sections.

## References

Sources are cited through `reports/01-methods-review.md` (claim ids in `reports/01-methods-review.claims.csv`) and decisions through `docs/charter/03-decisions.md`.
