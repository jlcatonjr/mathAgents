# Plan: integrating mathAgents into baseAgent

Status (2026-10-05, D35): **in progress in baseAgent.**
- Done: Phases 0–4, 6, 7 (inert until enabled) and 8 on baseAgent's side. The commits are the Lean
  scaffold `59147bb` (for the AgenticCapital owner's approval), the integration `4c5270d` and the CI review `7064c3f`.
- **Held:** Phase 5, until the operator signs the decision.

Every step that changes baseAgent runs there: on a feature branch, under baseAgent's `@security`
clearance and its signed decision log (`enforce_decision_signing: true`, `signing-governed.marker`).
Follow-ups baseAgent sent back: `docs/handoffs/2026-10-05-from-baseagent-integration-followups.md`.

## 1. What baseAgent gains

baseAgent's Lean work is `Projects/AgenticCapital/lean/`: the ZIT market development, eight files and
230 theorems in source as counted on 2026-10-04. The Lean is its artifact of record. Today its
integrity rests on convention:

- the axiom envelope is checked by hand with `#print axioms`;
- no script or CI job runs Lean;
- acceptance is a referee's note.

The mathagents module brings four things.

- **G-KERNEL, mechanized.** One command (`mathagents run check_proof_integrity`) does the build,
  the source scan for `sorry`, escape hatches and meta-commands, a `leanchecker` kernel replay of
  every module, and a per-declaration axiom envelope. It writes a fingerprinted report
  (`reports/kernel/latest.json`).
- **G-NAME and G-BLUEPRINT.** Every `[Lean: name]` in a narration or blueprint must resolve against
  the kernel report or the pinned Mathlib name index. That makes "no paraphrase drift" checkable,
  and it directly serves `@lean-informalization` and the LeanProofNarration project.
- **The dossier pipeline for new results.** It runs Stage 0 intake through Stage 8 snapshot:
  - human statement-fidelity approval (G-FID);
  - append-only counterexample logging (G-CX);
  - a human G-AX gate for any axiom or statement change.
- **The pipeline agents** that run those stages and gates (see §3).

All four are on by default. Any machine can switch them off for itself with `MATHAGENTS_ENABLED=0`
in its gitignored `.env`, without changing anything in the repository (§2, Phase 3). A switched-off
gate refuses with exit 3; it never reports a pass.

An offline run of G-KERNEL's source scan over `AgenticCapital/` on 2026-10-04 found **no** forbidden
token (`sorry`, `admit`, `native_decide`, `unsafe`, `#eval`, `elab`…) and no `axiom` declaration. The
build, replay and envelope steps have not run, because they need a Mathlib v4.32.1 cache. *(Update,
same day: a trial bump to v4.34.1 on a copy ran them all. G-KERNEL PASS, 649 proved; one proof-local
fix. See `docs/lean-toolchain-upgrade.md` §4.)*

## 2. Where things go

| Piece | Location in baseAgent | Why |
|---|---|---|
| The `mathagents` package | optional extra in `pyproject.toml`: `proofs = ["mathagents @ git+ssh://git@github.com/jlcatonjr/mathAgents.git@<tag>"]` | Pinned to a reviewed tag. The base install stays stdlib-only, as baseAgent's packaging policy requires. |
| Instance | `Projects/AgenticCapital/` (its `lean/` is already where the gates look) | Proofs belong to a research project; a second proof project becomes a second instance. |
| Workspace pointer | repository-root `mathagents.toml` with `[workspace] default = "Projects/AgenticCapital"` | Agents run from the repository root, and `mathagents run …` finds the instance through this pointer. |
| Pipeline agents | `.github/agents/<agent>.agent.md`, **repository level**, as adopted orphans | See §3. |
| Pipeline rules | a registration block in `.claude/CLAUDE.md` Project-Specific Rules, plus orchestrator Project-Specific Notes | These regions are outside the AGENTTEAMS fences, so updates preserve them. |
| Gate CI | a new `.github/workflows/lean-gates.yml` | baseAgent has no CI that runs Lean today. |
| On/off switch | `MATHAGENTS_ENABLED` in each machine's `.env` (already gitignored: `.gitignore:83`) | On by default. A collaborator who prefers not to use the architecture sets `MATHAGENTS_ENABLED=0` locally; nothing committed changes. |

## 3. Governance agents: repository level, but only the proof-specific ones

**Yes, at the repository level.** agentteams keeps one roster per repository, in `.github/agents/`;
nothing generates a per-project team. baseAgent already adds hand-written specialists this way
(`lean-informalization`, `wasm-wat-expert`, `ztree-expert`), and `agentteams --update --merge`
preserves them. Adding a project-level roster would mean a second orchestrator and a second set of
gates to keep consistent, which is worse.

**Import only the proof-specific agents, not mathAgents' generic governance team.** Both teams have
`@security`, `@adversarial`, `@conflict-auditor`, `@code-hygiene` and the other governance agents,
generated from the same agentteams templates. baseAgent's own copies govern baseAgent, so importing
mathAgents' copies would create duplicates with conflicting project facts. What is specific to
mathAgents is the gates, which travel inside the module, and these agents. Since D39 the nine pipeline agents
are researchers: they hold no `edit`, return every artifact as text, and the orchestrator writes it.

| Agent | Role | Tools |
|---|---|---|
| `interpretation-advisor` | competing readings, provenance (advises G-FID) | read |
| `statement-formalizer` | Stage 1 statement and stub (drafts) | read, execute |
| `fidelity-auditor` | Stage 1 cold back-translation (advisory filter for G-FID) | read |
| `proof-strategist` | Stage 2 strategy and blueprint graph (drafts) | read |
| `logic-articulator` | Stage 3 named-rule derivations (drafts) | read |
| `tactic-planner` | Stage 4 tactic plans (drafts) | read |
| `lean-prover` | Stage 5 proofs, kernel-driven (drafts, checked with `lake env lean --stdin`) | read, execute |
| `counterexample-hunter` | Stage 6 falsification; returns G-CX log commands for the orchestrator | read, execute |
| `axiom-auditor` | runs and explains every gate; checks the Stage 8 snapshot's preconditions (the orchestrator takes it) | read, execute |
| `engine-advisor` | engine selection (SMT/ATP as hints) | read |
| ~~`lean-informalization`~~ | **excluded**: baseAgent is its origin (mathAgents D28 copied it from baseAgent `9dcabb9`) | — |

One name collides: baseAgent already has an `interpretation-advisor`, a generated agent. mathAgents'
`interpretation-advisor` is bespoke and has a different contract (D24). The operator has two options:

- keep baseAgent's, and add the mathAgents one to `exclude`; or
- replace baseAgent's, which is an agent change under `@security`.

`mathagents agents export` renders each agent for baseAgent:

- gate commands become `mathagents run <gate>`;
- `MathAgents` / `MathAgentsWIP` become `AgenticCapital` / `AgenticCapitalWIP`;
- the team name becomes `baseAgent`;
- a provenance comment marks the file as generated, so `mathagents sync` refuses to overwrite a
  hand edit.

baseAgent-specific notes for these agents go in `.claude/CLAUDE.md`, not in the agent files.

Adding agents that hold `execute` grants adds capabilities (since D39 none of the nine holds `edit`). That is privileged under C-3,
and in a governed workspace it is constraint-relaxing under Rule 11. It therefore needs `@security`
clearance and the operator's signed decision. Folding the agents into the generated orchestrator
roster (`agentteams --adopt-orphans --overwrite`) is a separate maintainer step. That step is
currently blocked by baseAgent's stale security-intel gate.

## 4. Steps

Each phase is one baseAgent branch and PR. Paste the plan and steps CSV into the PR description,
because baseAgent's `tmp/` is gitignored.

**Phase 0: operator decisions** (see §6). Record them in baseAgent's decisions log.

**Phase 1: release and install.**
1. In mathAgents, merge `feat/importable-module` and tag `v0.2.0`.
2. In baseAgent, add the `proofs` extra pinned to `@v0.2.0`, then `pip install -e ".[proofs]"`.
3. Verify the install with `mathagents doctor`.
   *(Update: pin `@v0.2.1` or later to get the structure and inductive rows, which `[Lean: ZIT.Env]`
   bindings need, and `[agents] namespace = "ZIT"`.)*

**Phase 2: make AgenticCapital's Lean package conform.**
1. Change `lakefile.toml`:
   - remove the phantom `Zitcheck` library (no source exists, so a bare `lake build` fails);
   - add an `AgenticCapitalWIP` library with a root file `AgenticCapitalWIP.lean`;
   - set `defaultTargets = ["AgenticCapital", "AgenticCapitalWIP"]`;
   - keep Mathlib as a pinned git dependency.
2. Run `lake update` once and commit `lake-manifest.json`. Without the manifest, a change in
   dependency resolution can't invalidate old reports.
3. Toolchain: baseAgent is on **v4.32.1**, mathAgents on **v4.34.1**. The harness's Lean templates
   (`AxiomAudit.lean`, `NameIndex.lean`) were exercised on 4.34.1 here, and on 4.32.1 in baseAgent on 2026-10-05 (both PASS). Recommendation: first run
   the gates on 4.32.1 as is. If the templates fail there, fix them in mathAgents (a harness release);
   do not patch them in baseAgent. A toolchain bump is a separate, later wave.

**Phase 3: scaffold the instance.**
```bash
mathagents init Projects/AgenticCapital --agents-to ../../.github/agents
# edit Projects/AgenticCapital/mathagents.toml: team = "baseAgent", exclude = ["lean-informalization", ...]
printf '[workspace]\ndefault = "Projects/AgenticCapital"\n' > mathagents.toml
```
Commit `mathagents.toml`, `mathagents.lock.json`, the vendored contract files (`references/schemas/`,
the registries, `docs/charter/03-decisions.md`, `docs/kernel-gate.md`) and the seeded
`references/preferences.toml` and `references/axiom-allowlist.json`. `reports/kernel/` is gitignored
by its own `.gitignore`.

The architecture is then **on** for every machine. A machine opts out by adding
`MATHAGENTS_ENABLED=0` to its own `.env`, the file that already holds baseAgent's local API settings
and is gitignored. `mathagents doctor` confirms that the `.env` is ignored. Only that one line is read.

**Phase 4: first G-KERNEL run.**
```bash
cd Projects/AgenticCapital/lean && lake exe cache get
mathagents run check_proof_integrity && mathagents run build_name_index
```
STATUS.md claims the envelope {propext, Classical.choice, Quot.sound}, which is exactly the base
envelope. A finding here is a real defect to report, not a gate to relax. An axiom beyond the base
envelope needs a G-AX approval from a human.

**Phase 5: agents.**
1. `mathagents sync --write` writes the rendered agents.
2. Add the registration block (§5) to `.claude/CLAUDE.md` and orchestrator routing notes.
3. Derive the `.claude/`, `.codex/` and `.goose/` surfaces from the canonical files with
   `agentteams --interop-from`, as mathAgents' `scripts/refresh_agent_surfaces.sh` does. Never
   hand-write them. *(Update, after the uniform-surface-projection release: set
   `[agents] surfaces` instead, and `mathagents sync` derives, grant-scopes and locks them; take the
   pipeline agents out of any manual derivation. See `docs/uniform-surface-projection.md` and
   `docs/handoffs/2026-10-05-to-baseagent-uniform-projection.md`.)*
4. All of this is under `@security` clearance and a signed decision.

A repository with `enforce_decision_signing` has no record-now-sign-later path. Until the decision is
signed, keep `[agents] export_to` commented out. From v0.2.1, `init` never exports agents, and
`sync --write` stops tracking agents that are no longer exported (reported as `untracked`; no file is
deleted).

**Phase 6: existing results versus new results.** The ZIT theorems were referee-accepted, not
G-FID-approved. Recommendation:
- G-KERNEL and G-NAME cover the whole existing library immediately.
- The full dossier pipeline applies to new results.
- Retroactive dossiers, with a problem card and human fidelity review, are made only for headline
  theorems the operator names.

**Phase 7: CI.** Add `lean-gates.yml`, modelled on mathAgents' `gates.yml`. It should:
- install the pinned `proofs` extra;
- install elan and fetch the Lake cache;
- run `mathagents run check_proof_integrity`, `build_name_index`,
  `check_lean_bindings --assembled-only`, `validate_registries`, `preferences check`,
  `validate_dossier`;
- run `mathagents doctor`, which fails when the lock has drifted.

CI has no `.env`, so the gates are on there. The workflow must not set `MATHAGENTS_ENABLED=0`: a
switched-off gate exits 3, which fails the job, by design.

A consumer whose own repository is private cannot install the private package with the default
`GITHUB_TOKEN`. It needs:
- a read-only deploy key on mathAgents, stored as a repository secret;
- the job gated on a repository variable, so it is reported as skipped (not failed) until enabled;
- `actions: read` in `permissions`, for the IA-01 base query.

baseAgent's `.github/workflows/lean-gates.yml` is a worked example.

**Phase 8: registry.** Each repository's `@repo-liaison` records the other in its
`adjacent-repos.md`: baseAgent records mathAgents as an upstream dependency, and mathAgents records
baseAgent as a consumer.

## 5. Registration block for baseAgent's `.claude/CLAUDE.md` (Project-Specific Rules)

```markdown
### mathAgents proof pipeline (adopted bespoke agents, mathagents module)

- **Agents:** `@interpretation-advisor`*, `@statement-formalizer`, `@fidelity-auditor`, `@proof-strategist`,
  `@logic-articulator`, `@tactic-planner`, `@lean-prover`, `@counterexample-hunter`, `@axiom-auditor`,
  `@engine-advisor`, rendered from the pinned `mathagents` package by `mathagents sync --write`; never
  hand-edited (*only if the operator chose mathAgents' version).
- **On/off:** before dispatching any of these agents or running a gate, run `mathagents status`. Exit 3 means
  the architecture is switched off on this machine (`MATHAGENTS_ENABLED=0` in the gitignored `.env`): do not
  dispatch the pipeline agents, and treat proof work as outside the pipeline (no result is labelled proved
  by the pipeline). A switched-off `mathagents run` exits 3 and is never a pass.
- **Instance:** `Projects/AgenticCapital` (repository-root `mathagents.toml` points at it). Gates:
  `mathagents run <gate>`; status: `mathagents doctor`.
- **Rules (from mathAgents' style rules):** a result is called proved only when its declaration is `proved` in
  the G-KERNEL report; before Stage 2+ work on a dossier, `mathagents run validate_dossier --require-fid <slug>`
  must exit 0, and before stage N, `--require-stage <slug> N`; counterexample candidates enter only through
  `mathagents run log_counterexample add`, which the orchestrator runs, and the log is append-only; the
  nine pipeline agents are researchers that write no file, and only the orchestrator writes (D39); no agent
  writes a G-FID approval, a G-AX record or a G-CX verdict; outputs of non-Lean engines are hints until the kernel re-checks them; the settings
  in force come from the instance's `references/preferences.toml` and each dossier's `preferences.toml`.
- **Orchestrator duties (D39; mathAgents' orchestrator-duties rule, which is not exported, so it is stated
  here):** write each artifact a pipeline agent returns verbatim at the path it names, after resolving the path
  and checking that it lies in that agent's declared draft scope; scan every returned Lean draft with `mathagents
  run scan_lean_draft` before writing it or piping it to Lean (a finding goes to @security, since Lean runs
  `#eval`/`run_cmd`/`initialize` while checking); run a returned command only as an argument list; run every
  command that writes: `mathagents run
  log_counterexample add` (each candidate @counterexample-hunter returns) and `witness`, the Stage 8
  `mathagents run snapshot_kernel <slug>` once @axiom-auditor reports its preconditions met, and a command a
  researcher returns because its surface cannot run it, but only if it is on that agent's own declared
  command list (anything else goes to @security); the one line you add to a returned artifact is a
  strategy-review round's `Strategy sha256:`, computed from `strategy.md` as written; include
  `mathagents status` and `mathagents run lean_docs` output in every dispatch to a researcher without execute (and the
  `mathagents run validate_dossier --require-fid <slug>` output when its precondition names it); after writing
  any returned dossier artifact, run `mathagents run validate_dossier --require-fid <slug>` (before G-FID is recorded,
  `mathagents run validate_dossier <slug>`; and `mathagents run check_lean_bindings <slug>` once a name index exists) before dispatching the next stage, and return a failure to
  the authoring agent; persist @fidelity-auditor's back-translation. Write the Stage 0 problem card to the
  validator's grammar: one `- **<Field>:** <value>` line per field, and `Object logic:`, `Engine:` and `Domain:`
  hold exact registry ids only (`classical-hol`, `lean-builtin`, a `suited_domains` value such as
  `competition`), with any gloss on the next line (mathAgents `docs/module.md`, "The grammars the validators
  check"). Writing a researcher's returned artifact verbatim, and running the record commands it
  names, is not domain work (a carve-out from the orchestrator's "never handle domain work directly").
- **Updating:** bump the pinned tag, `pip install -e ".[proofs]"`, `mathagents sync` (review), then
  `mathagents sync --write`; re-run G-KERNEL. A conflict means a vendored file was edited here: reconcile it
  upstream in mathAgents rather than overwriting.
```

## 6. Decisions for the operator

1. **Toolchain.** Run on v4.32.1 first, or bump AgenticCapital to v4.34.1 now. *(Update: the v4.34.1
   bump was trialled successfully, one proof line, and is offered in
   `docs/handoffs/2026-10-04-baseagent-agenticcapital-v4.34.1.md`.)* **Decided 2026-10-05:** stay on
   v4.32.1. The bump is deferred to the AgenticCapital owner and was not applied.
2. **`interpretation-advisor`.** Keep baseAgent's and exclude mathAgents', or replace it.
3. **`lean-informalization`.** baseAgent's copy stays canonical (recommended). The operator decides
   whether mathAgents' Stage 7 notes (its Project-Specific Notes) are offered upstream to baseAgent's
   copy.
4. **Retroactive dossiers.** Choose which existing ZIT theorems, if any, get the full pipeline.
5. **Pinning.** Pin to a tag (recommended) or track `main`. A tag makes every harness change a
   reviewed upgrade.
6. **Signing posture for the agent PR.** baseAgent enforces signed decisions, so the agent PR needs
   the operator's signature.

## 7. How future mathAgents updates reach baseAgent

1. **In mathAgents**, any change to a harness file (`mathagents/_harness_files.py` lists them) bumps
   `version` in `pyproject.toml` and is tagged. Gate-logic changes also change `harness_sha256`, which
   every new kernel report records.
2. **In baseAgent**, the upgrade is a PR that:
   - moves the pinned tag;
   - runs `mathagents sync` (a dry run that lists what changes) and then `sync --write`;
   - re-runs G-KERNEL and the other gates.
3. `mathagents.lock.json` makes the upgrade safe.
   - An unedited vendored file or agent is updated.
   - A file edited in baseAgent is refused as a conflict, so local changes are never lost silently.
   - The fix for a conflict belongs upstream in mathAgents.
4. CI's `mathagents doctor` fails when the lock and the installed package disagree, so a half-done
   upgrade cannot merge.
5. The instance's own files are never synced: `lean/`, the dossiers, `preferences.toml` and the
   allowlist. A new harness default for preferences reaches baseAgent only by a deliberate edit.

## 8. Known limits

- `scripts/operator/` (G-FID approval recording) is not shipped. baseAgent's operator records
  approvals by hand in the schema format, or a later release ports a root-aware recorder.
- ~~The harness's Lean templates are verified on Lean v4.34.1 only.~~ **Resolved 2026-10-05:** on baseAgent's
  v4.32.1 instance, G-KERNEL passed (649 proved, 230 theorems) and the name index built (464,060 names).
  This was mathagents `3959c55`, harness `c168b3567ae4742d`, reported by baseAgent.
- The kernel report records `harness_sha256`, but an upgrade does not by itself lapse G-FID approvals
  made under older gate logic. Reviewers compare the digests when an upgrade changes a verdict.
- An agent's text describes mathAgents' pipeline. Its USER-EDITABLE notes mention mathAgents decisions
  (D-rows) that baseAgent receives in its vendored `docs/charter/03-decisions.md`.
