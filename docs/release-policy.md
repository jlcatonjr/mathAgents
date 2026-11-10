# Release policy: the coordinated v1.0.0

mathAgents' adoption of the shared release policy for agentteams, researchteam, mathAgents and baseAgent. The source
is agentteams `tmp/by-week/2026-W42/v1.0.0-shared-release-policy.md`, draft 3, as later amended (draft 6 §5: Codex
frozen for 1.0; draft 9: the v1.0.0 waiver of the soak-pass criterion). The operator confirmed it for
mathAgents in session on 2026-10-15 (D43). mathAgents may add rules to it but may not weaken it. The procedure is
[`release-checklist.md`](release-checklist.md), and the version contract is [`STABILITY.md`](../STABILITY.md).

How collaborators work within this policy (branches, installs, contributions, backports): [`CONTRIBUTING.md`](CONTRIBUTING.md).

## 1. Versions and branches

- SemVer. mathagents 1.x supports agentteams 1.x.
- **Branches.** `main` is the trunk, and every fix lands on `main` first. `release/1.0` is cut at `1.0.0rc1` and takes
  selected fixes only: a regular merge or a `git cherry-pick -x` PR of a fix already merged to `main` (the `-x` records
  the source commit). **Never squash** into `release/1.0`. This repository allows squash merges and has no branch
  protection (a private repository without GitHub Pro), so the rule is procedural: the merge `@security` row names the
  merge method. During the 1.0 freeze `main` took fixes only as well; the freeze ended at `v1.0.0`, and `main` is open for features.
- **Merge forward.** After each RC or final tag, `release/1.0` is merged forward into `main` with a regular merge, so
  `main` always contains every tagged commit. At `v1.0.0`, `main` then moves to `1.1.0.dev0`.
- **Patches.** `v1.0.N` is tagged on `release/1.0`. `release/0.2` is cut from `v0.2.7` only if someone asks for a fix.
- **The 1.1 line (intake rule, public repository).** Confirmed by the operator in this repository's session on 2026-11-06 (AskUserQuestion, "Confirm as written"); it
  takes effect with D45 (recorded with its signed Rule 11 row). `release/1.1` is cut in the public, fresh-history repository from its `main`, at the
  commit before the version moves from `1.1.0.dev0` to the release version, so the signed commit's version differs
  from its first parent's (`tag-release.sh` refuses otherwise). It takes in only: the release PR (version, CHANGELOG
  `[1.1.0]` with its Toolchain block, and the pins that block names); afterwards, `1.1.N` backports under the rules
  above (a fix merged to `main` first, a regular merge or `cherry-pick -x`, never a squash). A release PR may not
  change `scripts/operator/tag-release.sh`. Every signed row about the release names the history it refers to:
  `private` (this repository) or `public`. `release/1.0` and the `v0.x`–`v1.0.1` tags stay in the archived private
  repository.

## 2. Tags

- **Form.** `vX.Y.Z` or `vX.Y.Z-rc.N`, annotated and SSH-signed by the operator from a plain terminal with
  `scripts/operator/tag-release.sh`. No agent signs a tag.
- **Key.** The agentteams release key (`SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM`; it signs the 1.0 and 1.1 lines). Its
  `allowed_signers` line is in agentteams SECURITY.md, under "Release signers".
  The same key signs the 1.1 line. On `main`, 1.1-line agentteams and researchteam tags are exempt from the S-10
  cooldown only under the operator-signed rows `s10-release-key-exemption-1.1` and
  `s10-release-key-exemption-researchteam-1.1`, whose binding texts are in `docs/release/` (PR #78).
- **Verification.** Against `~/.config/agentteams/allowed_signers`, which is outside every write root. Installing
  or changing it is operator-only. Use the neutralised verify command from agentteams SECURITY.md.
- **The RC.** mathAgents' RC is the signed tag `v1.0.0-rc.1` on `release/1.0`, so baseAgent can pin it.
- **Tags are immutable.** A pushed tag is never moved or deleted. Fix forward with `v1.0.1`.

## 3. Pins

- **What a pin is.** Every cross-repository pin (`toolchain.lock`, the rendered surfaces' `build-log.json`, pip
  extras refs) is the peeled 40-hex commit of a verified signed tag: agentteams' and researchteam's. Nothing pins a
  branch, a branch head or an unverified tag. Extras install agentteams from git at `@<peeled-sha>`.
- **One source of truth.** When both the extras and `toolchain.lock` carry a pin, `check_toolchain.py` fails if they
  disagree (implemented by researchteam). mathAgents also tests that the `.github` and `.claude` build-logs name the
  locked agentteams commit.
- **Moving a pin.** Each move is an `@security` row naming the tag and its peeled SHA.
  `scripts/lib/agentteams_provenance.py` refuses a render on any other agentteams commit.
- **Pins today (2026-11-09).** Both are peeled commits of verified signed tags, with `.tag=` lines.
  - `release/1.0`: agentteams `v1.0.0` (`cc5b8c9e`, moved in Phase T on 2026-10-19 from the joint soak pair
    agentteams `v1.0.0-rc.14` + researchteam `v1.0.0-rc.3`) and researchteam `v1.0.1` (`b55e2307`, for its
    frozen-surfaces fix).
  - `main`: **the 1.1 line**: agentteams `v1.1.0` (`9b16fb54`, tag object `093c38fd`) and researchteam `v1.1.0`
    (`938dd663`, tag object `4f0fb292`), in the operator-signed rows `pin-agentteams-v1.1.0` and
    `pin-researchteam-v1.1.0` (MA-6, 2026-11-09), first rendered under the single-use row
    `overwrite-agentteams-v1.1.0`. Before that: agentteams `v1.1.0-rc.15` (`9900fbd3`) and researchteam `v1.1.0-rc.4`
    (`4af46b7d`), in the operator-signed rows `pin-agentteams-v1.1.0-rc.15` and `pin-researchteam-v1.1.0-rc.4`. rc.15 carries the
    restored S-10 cooldown; mathAgents' brief names no `s10_cooldown_exempt_repos` (operator decision, 2026-11-03), so
    the rendered rule applies the cooldown to every release, and the 1.1-line pins rest on the two signed S-10
    exemptions above. Before that: agentteams `v1.1.0-rc.12` (`ac93628a`) and researchteam `v1.1.0-rc.3`
    (`6b69b999`), in the rows `pin-agentteams-v1.1.0-rc.12` and `pin-researchteam-v1.1.0-rc.3`. The second is
    retroactive: the moves to agentteams `v1.1.0-rc.11` and researchteam `v1.1.0-rc.3` (PR #90) were merged without
    pin rows. Earlier pins on this line: agentteams `v1.1.0-rc.7` and researchteam `v1.1.0-rc.2` (PR #80).
    The line began with PR #78: agentteams `v1.1.0-rc.6` (`0ef4404c`) and researchteam `v1.1.0-rc.1`
    (`e6d5d5e5`). That move is recorded in six operator-signed rows: `release-line-agentteams-1.1`,
    `release-line-researchteam-1.1`, the two S-10 exemptions above, `pin-agentteams-v1.1.0-rc.6` and
    `pin-researchteam-v1.1.0-rc.1` (specs in `docs/release/`, minted by the one-shot `scripts/operator/sign_pr78_rows.sh`, since removed).
    Before that, `main` pinned researchteam `v1.0.2` (`10a36758`) by the operator's decision of 2026-10-23 (#66).
    researchteam `v1.1.0-rc.1` builds with setuptools 84.1.0, which was still inside the cooldown when it was
    adopted; its pin row recorded a re-vet, closed on 2026-11-03 by the row `revet-setuptools-84.1.0-researchteam` (15 days
    old, no OSV advisory).
  - baseAgent stays on the agentteams 1.0 line.

## 4. Autosync

- **Paused** (PR #48). researchteam 1.0.0's sync gate rewrites the Goose and Codex surfaces
  this repository keeps frozen (soak run 39173598260). researchteam 1.0.1 fixes this: its `update` and managed gate
  honour `brief.json` `"frozen_surfaces"`, which this repository set to `["codex", "goose"]` until CX-3 (§5). The lock moved to it
  in 1.0.1. The 1.0.1 soak passed under the operator's waiver (§6). Resuming the schedule is constraint-relaxing (it
  relaxes the freeze), so it takes its own PR on `main` and the operator's Ed25519-signed Rule 11 row.
- researchteam's tag-tracking fix (CA-058, researchteam #52/#67) is synced at rc.3: under the release lock the managed
  gate follows the locked tag's release line, verified, and never moves the lock to `main`
  (`docs/agentteams-update-policy.md`). It is dispatched only by the operator; before the lock reached researchteam 1.0.1, a dispatched
  run failed for want of the frozen-surfaces fix.
- **On the public repository (operator ruling, 2026-11-09).** After release day (runbook step 11), the operator may
  turn on "Allow GitHub Actions to create and approve pull requests", provision the `AGENTTEAMS_ALLOWED_SIGNERS`
  secret, and dispatch the autosync (docs/release/public-repo-setup.md, "After step 11"). The schedule stays off.
  - Its pull request targets `dev`, which is protected like `main`.
  - The ruleset requires no approving review (count 0), so a workflow approval adds nothing. CODEOWNERS review applies
    only to the paths in `.github/CODEOWNERS`, and a workflow can't be a code owner.
  - The workflow declares its own `contents: write` and `pull-requests: write`; the default token stays read-only. Its
    actions are pinned to commit SHAs.
  - The autosync runs a bare `researchteam update`, which isn't a complete update here (CLAUDE.md). Its pull request
    merges only after: `bash scripts/refresh_agent_surfaces.sh` has run on its branch and the operator has pushed that
    commit (a pull request opened with the workflow token starts no checks, so this push is what starts them); `gates`
    and `long-suites` pass; the agentteams and
    researchteam pin move has its own @security row (S-10: tag verification, provenance, an OSV check); and, when it carries the `security-review-required` label, an
    @security review.

## 5. Codex and AGENTS.md

- **1.0 line.** Codex and the Goose-owned `AGENTS.md` stay **frozen** (shared policy draft 6 §5; Jim-signed row
  `write-policy-orchestrator-only-codex-210`): this team has adopted agents, and agentteams 1.0 has no Codex
  write-policy interop (#210). The earlier orchestrator-only row (`codex-agentsmd-orchestrator-only-210`) is
  superseded.
- **1.1 line (CX-3, operator ruling 2026-11-09, "Both now, Goose UNENFORCED").** Codex and Goose are unfrozen from
  the agentteams v1.1.0 pin (MA-6), under the operator's Ed25519-signed Rule 11 rows `unfreeze-codex` and `unfreeze-goose` (one per surface; researchteam verifies each). Goose is reviewed by 2027-02-09.
  - **Codex** is in `write_policy_frameworks`: agentteams renders it natively under orchestrator-only (role gate,
    hooks, launcher), and the bespoke pipeline agents are imported into that team read-only (#319,
    `scripts/lib/project_bespoke_codex.sh`). The #249 fix scopes Codex's write-policy fence in the shared `AGENTS.md`.
    `mcp_grants` don't hold on Codex; the role gate allows spawned agents read-only tools only.
  - **Goose** runs **UNENFORCED**: agentteams refuses orchestrator-only there (`GOOSE_SWITCH_REFUSED`), so Goose renders
    off the switch. The bespoke recipes are grant-scoped; the read-only and command-running recipes carry `developer`,
    which also writes and runs commands (19 in the MA-6 rehearsal; D34's accepted risk, accepted again by the operator
    on 2026-11-09, "Both, accept D34 widening"). Off the switch agentteams also drops the Goose sandbox's write-denies
    on `.agentteams` and `.goose/recipes`, exposing the Codex role gate to Goose sessions (accepted, "Unfreeze both,
    accept the gap"; `docs/release/unfreeze-goose.conditions.txt` item 3a). Of the three denies agentteams ties to the
    switch (`.agentteams`, `.agentteams-status`, `.goose/recipes`), the frozen profile carried two, `.agentteams` and
    `.goose/recipes`; the render removed both. This is weaker than the frozen state it replaces, by the operator's
    decision; it is reviewed by 2027-02-09 and ends when agentteams enforces the switch on Goose.
  - **Superseded text.** `docs/release/cx3-unfreeze-codex-goose.conditions.txt` stays as signed (the `unfreeze-codex`
    row's `conditions_verified` hashes it), but its Goose half is superseded by `unfreeze-goose.conditions.txt`: its
    item 3 ("no Goose agent gains a tool") does not hold for Goose, and its review date reads "90 days" where
    2027-02-09 is about three months. Its claim, also in the `unfreeze-codex` spec, that Codex renders under its own
    signed overwrite row was a prediction: the native Codex render runs with overwrite off and needed no row (MA-6
    rehearsal and render, 2026-11-09).
  - `mathagents sync` projects codex only through an agentteams with #319, into the instance's own native Codex team
    (`mathagents/_surfaces.py`, `codex_interop_supported`).

## 6. Joint cut: mathAgents' part

**Order:** agentteams → researchteam → **mathAgents** → baseAgent.

**Phase R (RC).** Once agentteams signs `v1.0.0-rc.10` and researchteam signs `v1.0.0-rc.1` (as run: the agentteams
pin moved alone to rc.12 on 2026-10-16, researchteam's alone to rc.1 and agentteams' to rc.13 on 2026-10-17, then
both together to agentteams rc.14 + researchteam rc.3 for the 1.0 render, each move under its own `@security` row;
by the operator's decision of 2026-10-18, rc.1 is cut before the M6 phase 2 re-run, which runs during the soak):
1. Verify both tag signatures.
2. Move `toolchain.lock` to both peeled SHAs, under an `@security` row.
3. Install the agentteams RC (a VCS install at the peeled commit, or a detached checkout at the tag).
4. `agentteams --verify-integrity`: review the pre-upgrade HALT report.
5. `--migrate-decision-log`.
6. Collect the operator's Ed25519-signed rows: the three HALT retractions (ids from the report), the Rule 11
   `run_command` decision for `@statement-formalizer`, and the #210 row (as run: the frozen-Codex row
   `write-policy-orchestrator-only-codex-210`, superseding the orchestrator-only one; §5).
7. Re-render: settings regenerated; two signed rows, with `--verify-integrity` showing the chain; `--check-wiring`.
8. Merge #49 and #50.
9. Cut `release/1.0` at `1.0.0rc1`, and the operator signs `v1.0.0-rc.1`.
10. The full M6 re-run (phase 2, the 14b rollback drill, the step-15 report and go/no-go), during the joint soak (the
    operator's decision of 2026-10-18; it was step 7's second half before).

**Joint soak.**
- researchteam blocker 1 (the tag-tracking gate, CA-058) is merged and synced (rc.3), so a soak dispatch follows the
  locked tags and never installs agentteams `main` or moves the lock off a verified tag.
- No soak sync is ever dispatched from `main`.
- One operator-dispatched sync against the pinned RCs, from `release/1.0`.
- The full suite and CI pass on `release/1.0`.
- Only backports land. Any backport means a new signed RC and another soak.

**Go/no-go (one operator decision across all four).** For mathAgents: the M6 re-run passes, including
`--check-wiring` and both signed rows; CI passes on `release/1.0`; the soak dispatch passed; no must-fix-for-1.0 issue
is open. For v1.0.0 the soak-pass criterion was waived under shared policy draft 9 (run 39173598260 failed in
researchteam's sync gate, see §4; recorded by agentteams-d4, 2026-10-18); the M6 go/no-go was GO, conditional.
For v1.0.1 the operator waived the run-success criterion for the soak's pull-request step only: run 39880227613 on
`v1.0.1-rc.2` passed the autosync gate with the frozen surfaces untouched. Its final step was refused only because this
repository does not let GitHub Actions open pull requests (rc.1's soak, run 39817544064, failed in the gate and led to rc.2).

**Phase T (same day, in order).** After agentteams and researchteam tag `v1.0.0`:
1. Verify their signatures.
2. Move the lock to their peeled SHAs.
3. Do the 1.0 render: Codex and AGENTS.md stay frozen (§5); Goose follows what agentteams 1.0 supports under the
   write switch (#204), which refuses Goose there, so Goose stays as rendered before M6.
4. Tag `v1.0.0` on `release/1.0`.
5. Send baseAgent the pin-move handoff.

If a step fails, the cut stops at mathAgents. Tags already pushed stay; mathAgents fixes forward, and baseAgent
waits.

## 7. Operator-only actions

- Signing every tag.
- Installing `allowed_signers`.
- The signed rows: HALT retractions, Rule 11, and #210. These relax constraints, so they need an Ed25519 signature;
  an HMAC is valid but not enough. Each is signed in mathAgents' own session. Every signing script first runs
  `scripts/operator/check_decision_spec.py` on each spec, through `lib_signer.sh`'s `preflight SPEC TEAMDIR REPO`
  (after `signer_check`). It refuses a spec the
  security gate could never clear before the key is read: no approved author, a scope that excludes the action, an
  unset date, a team dir the signer doesn't write to, or a `derives_from` chain that doesn't resolve to recorded rows
  (the gate pools lineage per action id, so a bad first row makes an id unclearable: use a new id).
- The signer is the root-owned `/opt/agentteams-signer-v1.0.0` (agentteams v1.0.0, cc5b8c9e; cryptography 50.0.0),
  provisioned once by `scripts/operator/provision_signer_venv.sh` under the operator's row
  `provision-operator-signer-agentteams-v1.0.0-r3` (operator decision 2026-10-28). Every new signing script sources
  `scripts/operator/lib_signer.sh` and calls `signer_check`. It refuses unless the signer and its parents are
  root-owned and not writable by others, `PROVENANCE.json` names that commit and package set, and the installed
  packages match, and its base Python is the root-owned python.org 3.13.16 framework. Then it signs with
  `signer_run --sign-decision …`, which runs agentteams as `python -I` so no `PYTHON*` variable from the caller applies. There is no fallback: `/opt/anaconda3` is not used for signing. Run the branch tools with `--team-dir` set to the dir the row was signed into.
- Before Phase R: installing `~/.config/agentteams/allowed_signers` and proving `git tag -v v1.0.0-rc.9` on
  agentteams with the neutralised command.
- Merges that name the head SHA: merges into `release/*` and the merge-forward. Collaborators may merge their own
  pull requests into `main` once the checks that ran are green (operator decision, 2026-10-19; `CONTRIBUTING.md`).
- The go/no-go.
