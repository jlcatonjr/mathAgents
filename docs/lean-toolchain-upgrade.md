# Upgrading Lean work to a new toolchain (v4.32.1 → v4.34.1)

This is the toolchain-bump wave for any repository whose Lean work is checked by the mathAgents harness,
mathAgents itself or a consumer such as baseAgent. Its first use was a trial on baseAgent's
`Projects/AgenticCapital/lean` (2026-10-04). The trial ran on a copy, outside both repositories, and is
described in §4.

## 1. Rules of the wave

- **A statement never changes in a bump.** Fixes are proof-local: tactic scripts, `simp` sets, lemma
  names inside proofs. If a theorem's statement has to change, that is a G-AX decision for a human
  (DD-37), not part of the bump.
- **The kernel decides.** The bump is done when G-KERNEL passes on the new toolchain: build, kernel
  replay of every module, and the axiom envelope.
- **Meaning is checked, not assumed.** A statement whose text is unchanged can still change meaning:
  coercions, instances, notation, or a Mathlib definition it relies on may have changed. The primary
  check is `statement_types.py`. It compares every theorem's fully elaborated statement (`pp.all`)
  under the old and new toolchains, so it needs a build of each. `statement_drift.py` is a secondary
  screen over the Mathlib and core declarations the statements reach. Anything flagged goes to a
  human fidelity review.
- **Nothing in the repositories is overwritten while trialling.** `bump_trial.sh` reads the package
  and works in a new directory, refusing an existing one. `--packages-from` shares an existing
  Mathlib build instead of copying it. The script accepts it only together with `--manifest-from`, and
  checks that the manifest pins Mathlib at the bump's tag. Whether the shared build was made from that
  manifest is the operator's responsibility; the script does not check it.

## 2. Tools (`scripts/toolchain_bump/`)

The tools ship in the `mathagents` wheel, so a consumer runs the wave without a mathAgents checkout:
`mathagents bump trial …` (with `--from` defaulting to the instance's `lean/`, and refusing a `--to` inside the
instance or its repository), `mathagents bump statement-types …` and `mathagents bump statement-drift …`. In the
mathAgents checkout, call the scripts directly. The rules agents follow about versions throughout the wave are
`docs/lean-version-governance.md` (vendored into every instance).

| Tool | Does |
|---|---|
| `bump_trial.sh` | Copies a Lake package to a **new** directory and retargets `lean-toolchain` and the Mathlib `rev`. It removes a `lean_lib` that has no sources, optionally adds a `*WIP` library and applies a patch, then builds. Output: `build.log` and `source.diff`. It refuses an existing directory. |
| `statement_types.py` | `dump` writes every project theorem's elaborated statement (`StatementTypes.lean`), including private theorems and propositional structure fields, but not compiler-generated lemmas. `compare OLD NEW` lists the ones changed, removed or added. **Primary meaning check.** An empty dump is an error. |
| `statement_drift.py` | Secondary screen. It extracts the Mathlib or core constants that statements reach through project definitions (`StatementDeps.lean`), then diffs their declarations between the two tags (shallow fetch of mathlib4 and lean4; network needed once). Flags `changed`, `moved_or_new` and `unknown`. It sees only text changes inside or at the edge of a reached declaration. It sees neither drift in what that declaration uses, nor `attribute`, `instance` or `set_option` edits elsewhere. Fail-closed: an unreachable repository or an empty extraction exits 2. |
| `lean_template.py` | Shared runner for the two Lean templates. |
| `tests/test_toolchain_bump.py` | The screen and the comparison on synthetic data, and `bump_trial.sh` with a stub `lake` (no network, no Lean). |

## 3. The wave, by agent

Steps 0 and 5 are gates: nothing after them runs until they pass. Every gate in step 7 runs on the bump branch,
before the merge.

| Step | Agent | Action |
|---|---|---|
| 0 | `@orchestrator`, the instance owner | **Consumer decision gate.** The instance owner's decision on timing (and target) is recorded: in baseAgent, the AgenticCapital owner's (D9), under its signed-decision regime. The target is in the harness's register of verified toolchains (`mathagents status`), or the harness is verified on it as part of this wave. `@security` clears running harness tooling against the consumer before it starts. |
| 1 | `@orchestrator` | Open a plan (`tmp/by-week/…`) and a branch. Run `mathagents status`: the wave needs the architecture on. |
| 2 | `@lean-prover` | The trial copy is outside `@lean-prover`'s standing write scope (the library), so the plan names it as this step's scope. `mathagents bump trial --to <new dir outside the repository> --tag <new tag> [--wip-lib <Lib>WIP]`. For each build error, make the smallest proof-local fix in the trial copy and rebuild. Collect the fixes as one patch (`-p1`, relative to the Lake package). |
| 3 | `@axiom-auditor` | On the patched trial: G-KERNEL (`check_proof_integrity`; it also checks that the Lean that ran is the trial's pin), `build_name_index`, and the G-NAME check of narrations and dossiers. Compare the number of declarations audited and theorems in source with the pre-bump report. |
| 4 | `@axiom-auditor` | `mathagents bump statement-types dump` on the OLD build (the unchanged tree, before the bump) and on the trial, then `statement-types compare old.tsv new.tsv`. Next, `mathagents bump statement-drift --lean-dir <trial>/lean --old <old tag> --new <new tag> --out drift.json`. **`--lean-dir` is required**: without it the extraction has no package to read. |
| 5 | `@fidelity-auditor` (advisory), then a human | **G-FID re-approval gate.** A bump makes every kernel report stale (`source_sha256` hashes `lean-toolchain`, the lakefile and the manifest), but a G-FID approval is keyed to `statement_fingerprint`, which stops at the Mathlib boundary, so the gates leave approvals standing (`docs/kernel-gate.md`, "What the gate does not establish"). This step is the check they cannot make. Review every statement step 4 flagged: does it still mean what its narration and fidelity record say? The operator then re-approves each approval in the dossiers the bump touches, stamping it with the new `toolchain_pin` and `mathlib_rev`, or opens a G-AX record. An approval stamped with the old pin draws a validator warning until it is re-approved, so a missed one is visible. `validate_dossier --require-fid <slug>` must pass on the trial for every dossier. |
| 6 | `@security`, `@git-operations` | Apply the patch, toolchain, lakefile and `lake-manifest.json` in one PR, with every version text the instance owns updated in the same PR (`mathagents doctor` lists stale version text in exported agents and vendored docs; `git grep -nE 'v4\.[0-9]+\.[0-9]+'` finds the rest). In baseAgent, under its signed-decision regime. |
| 7 | `@axiom-auditor` | **Every gate on the bump branch, before the merge:** G-KERNEL (with the toolchain check), `build_name_index`, G-NAME, `validate_dossier` (with `--require-fid` for every dossier) and CI. `mathagents doctor` reports no `lean pin: P2` problem and no `lean pin: P4` warning. |
| 8 | `@lean-informalization` | Re-check `[Lean: …]` bindings in narrations (G-NAME) and re-stamp narrations with the new pin. Nothing to re-narrate unless step 5 found drift. |
| 9 | `@orchestrator` | If the harness was verified on the new pin in this wave, propose an entry for mathAgents' `references/verified-toolchains.json`, with its evidence, upstream. |

## 4. Trial result: baseAgent AgenticCapital, v4.32.1 → v4.34.1

The trial ran on a copy of baseAgent's `Projects/AgenticCapital/lean`, as of baseAgent HEAD `4136d17`; the
directory's last change was at `cfd2449`. It was built against mathAgents' Mathlib v4.34.1, commit
`d13f23b723b8a846827a245b89c10fc7d3f11612`.

- **Breaks:** one, at `ZITCallAuction.lean:1005`, inside the proof of the private theorem
  `settled_order_spread`. `simpa only [List.getElem_take] using hget` no longer rewrites under
  v4.34.1, where core's `List.getElem_take` is a `@[simp]` lemma with a different form.
  - **Fix (one line, proof-local):** `rw [← hget]; exact (List.getElem_take).symm`. `grind` also works.
  - **Candidates that failed:** `rwa [List.getElem_take] at hget`, `simpa using hget`,
    `simpa [List.getElem_take] using hget`, `simp only … at hget`.
  - **Patch:** `docs/handoffs/2026-10-04-baseagent-agenticcapital-v4.34.1-proofs.patch`.
- **Lakefile:**
  - drop the phantom `Zitcheck` library, which has no sources, so a bare `lake build` failed;
  - the trial also added `AgenticCapitalWIP`, an empty library, and set
    `defaultTargets = ["AgenticCapital", "AgenticCapitalWIP"]`, because the harness's G-KERNEL requires
    an open-work library. For baseAgent this is optional, and depends on whether it adopts the gates
    (see the handoff);
  - Mathlib `rev = "v4.34.1"`;
  - commit a `lake-manifest.json`. The trial used mathAgents', which pins Mathlib `d13f23b`.
- **G-KERNEL on v4.34.1: PASS.** 649 declarations audited, 230 theorems in source, 649 proved, kernel
  replay clean. Every `#print axioms` line in `ZITAudit` is within {propext, Classical.choice,
  Quot.sound}.
- **Narration bindings:** 44 distinct `[Lean: …]` names in `Projects/LeanProofNarration` and
  `Projects/AgenticCapital`. Every real name resolves after the bump. The seven that do not resolve
  are unaffected by the bump:
  - four are placeholders in protocol docs;
  - three are structures cited by short name (`Env`, `Match`, `L0Match`). G-NAME requires the full
    name (`ZIT.Env`), and at the time the kernel report listed theorems and definitions but not
    structure types. That harness limit is recorded in §5, and was fixed in v0.2.1.
- **Meaning: not yet compared.**
  - The new-side dump ran: 249 statements, the 230 source theorems plus 19 propositional structure
    fields.
  - The old-side dump needs a v4.32.1 build, which did not exist on the trial machine.
  - The drift extraction ran and found 188 external constants: 136 core and 52 Mathlib. Four of the
    188 are auto-generated (`_sizeOf_inst`) and come out as `unknown`.
  - The drift comparison needs GitHub, which the trial's sandbox could not reach.
  - Both checks must pass before the bump PR merges (step 4). Tag v4.34.1 resolves to `d13f23b`, the
    commit the manifest pins.
- **Before the bump:** the source declares 230 theorems, the same count as after. No G-KERNEL report
  exists for v4.32.1, so there is no earlier count of audited declarations to compare with the 649.
- **Reproduce:**
  ```bash
  scripts/toolchain_bump/bump_trial.sh --from ~/…/baseAgent/Projects/AgenticCapital/lean --to /tmp/trial \
    --tag v4.34.1 --wip-lib AgenticCapitalWIP \
    --patch docs/handoffs/2026-10-04-baseagent-agenticcapital-v4.34.1-proofs.patch \
    [--manifest-from lean/lake-manifest.json --packages-from lean/.lake/packages]   # reuse mathAgents' Mathlib
  ```
  Without the patch the build fails at line 1005, the expected regression. With it, it builds in
  about 40 s on a warm Mathlib. Both runs were repeated with the hardened script (trials A2 and B2).

## 5. Findings for the harness

- ~~The G-KERNEL report omits structure and inductive types.~~ **Fixed in v0.2.1:** the report has
  `structure` and `inductive` rows (12 on the AgenticCapital copy, among them `ZIT.Env`), so
  `[Lean: ZIT.Env]` passes G-NAME.
- `mathagents agents export` renames `MathAgents.<Slug>` to `<Library>.<Slug>`. baseAgent's
  declarations live in namespace `ZIT`, not `AgenticCapital`, so the rendered agents' namespace
  convention does not match baseAgent's code. Name resolution is unaffected, because it is by exact
  name. **Fixed in v0.2.1:** `[agents] namespace` (for example `"ZIT"`) sets the declaration
  namespace; see `docs/module.md`.
- On v4.34.1 the build emits 10 deprecation warnings (for example `Mathlib.Data.Real.Basic` →
  `Mathlib.Basic.Real.Basic`) and some unused-`simp`-argument lints. None is an error. They are
  candidates for a follow-up tidy, not part of the bump.
