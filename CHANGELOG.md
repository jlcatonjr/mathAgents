# Changelog

All notable changes to the `mathagents` harness are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and from 1.0.0 the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) as defined in [`STABILITY.md`](STABILITY.md).

From 1.0.0rc1, every released section opens with a `### release notes` summary for consumers (the block a release
page is built from) and ends with a **Toolchain** block: the agentteams and researchteam commits the release
renders with (from `toolchain.lock`; before the lock existed, the agentteams version and, where the build-log recorded
it, its commit; the researchteam commit was not recorded for 0.x), and the Lean toolchain and
Mathlib revision it was verified on (`lean/lean-toolchain`, `lean/lake-manifest.json`). Proof results are not
versioned here; a result's status is its G-KERNEL report.

## [Unreleased]

## [1.1.0] — 2026-11-10

### release notes

`v1.1.0` is the first release of the 1.1 line, tagged on `release/1.1`, and the first from this public repository.
Its history starts fresh at an export of the private repository's `main` (charter D45): the 1.0.x tags and their
history stay in the archived private repository, so the 1.0.x sections below are kept for reference and their compare
links name tags this repository does not have. The release:
- moves the toolchain to agentteams `v1.1.0` and researchteam `v1.1.0`, the peeled commits of verified signed tags;
- unfreezes the Codex and Goose surfaces: Codex runs under the orchestrator-only write policy, and Goose is rendered
  off the switch, UNENFORCED, as an accepted risk until agentteams enforces the policy there;
- is licensed Apache-2.0 (`LICENSE`, `NOTICE`, and the `pyproject.toml` licence metadata). The package keeps the
  "Private :: Do Not Upload" classifier, so nothing is uploaded to PyPI: install it from this repository;
- runs the long suites only where they can matter, and before every release (D46).

**To pin this release:** verify the tag against `~/.config/agentteams/allowed_signers`, then pin the commit it points to
(its peeled commit), never a branch.

### Added
- A documentation site and an interactive explorer, built like agentteams' and baseAgent's (MkDocs Material). It
  has Home, Getting Started, Concepts, a CLI reference, the API reference, the Explorer, the Proof Library,
  Stability and Changelog.
  - `scripts/build_api_site.py` generates the API pages, the CLI reference and the explorer's data, all of which are
    gitignored and rebuilt in CI.
    - The API pages come from the canonical `docs/api-reference/` pages, with their links rewritten. A link to an
      internal document fails the build.
    - The CLI reference is read from the real parser.
    - The explorer's `api.json` comes from the parity gate's definition of the public surface.
    - The explorer's `library.json` is built through the documented `mathagents` API, plus the dossier gate's
      card reader, the G-KERNEL source hash, and the pins and allowlist files.
  - The explorer (`docs_src/explorer/`) runs entirely in the browser, with no CDN, text-only rendering and a strict
    CSP. It shows each dossier's `Result status:` line word for word, and each declaration's G-KERNEL status as
    recorded in the dossier's snapshot.
  - `.github/workflows/docs.yml` builds on pull requests and on main. It deploys to GitHub Pages only from main and
    only while the repository is public. Its actions are pinned by SHA and its dependencies are hash-locked
    (`.github/ci/requirements-docs.txt`).
  - `tests/test_api_site.py` runs in the gates job.
- `mathagents.cli` builds its parser in a private `_build_parser()`, so the site can read it. Arguments that had
  no help text now have it. Nothing else in the behaviour changes, and no public name changes.
- A public summary of the decision charter, `docs/charter/decisions-summary.md`, which keeps every decision number
  (the full charter stays in the archived private repository). `scripts/instance_root.py`'s `charter_path()` resolves
  the summary where it exists.
- The operator's release tooling gains a decision-spec preflight (`scripts/operator/check_decision_spec.py`) and a
  root-owned signer (`scripts/operator/lib_signer.sh`); the tag signer uses no python.

### Changed
- `toolchain.lock` pins agentteams `v1.1.0` (`9b16fb54`) and researchteam `v1.1.0` (`938dd663`), the peeled commits of
  verified signed tags, and the agent surfaces are re-rendered on them through `scripts/refresh_agent_surfaces.sh`.
  `brief.json` `frozen_surfaces` is empty: Codex is rendered natively with the role gate, and Goose's recipes are
  grant-scoped, off the write-policy switch (accepted risk, `docs/release/unfreeze-goose.conditions.txt`).
- Native per-provider projection, phase 1: the Copilot-to-Claude bridge is retired, and a fail-closed bridge guard
  runs before and after every agent-surface update.
- CI follows an integration-branch model: pull requests go into `dev`, and `dev` reaches `main` through a release PR.
- **CI cost (charter D46, superseding D36):** the long suites run only where they can matter. They are the
  G-KERNEL gate tests and the Lean half of the G-AX tests, now in the `long-suites` job. They run on releases,
  manual dispatch, a monthly schedule, PRs that change their inputs (`scripts/ci_long_suite_inputs.txt`), and
  pushes to `main` that the merged PR's run did not cover. `scripts/ci_long_suites.py` decides, fail-closed, and
  `tag-release.sh` refuses a commit without a green `long-suites` run. G-KERNEL itself still runs on every push.
- `.agentteams-status/.gitignore`, committed by an earlier sync, is untracked; the directory has been ignored since 1.0.1.
- The harness spec's account of the Lean library is corrected (audit finding IA-39): `lean/MathAgents/` holds four
  files, `Smoke` is documented as a toolchain smoke test, and the `finite-probability` object logic is `available`.
- Charter decision D40: the operator chose route A for G-FID delegation, a pre-screened review queue with no
  delegation, and no delegation setting is added (the design's `fidelity.delegation` key stays unimplemented).
- `CONTRIBUTING.md`, `STABILITY.md`, `docs/module.md` and the concepts page describe the public repository.

### Removed
- The self-hosted fallback runner (charter D37) and its scripts are retired; CI runs on GitHub-hosted runners only.

### Fixed
- Five gate tests (G-FID, G-CX, the G-AX validator, dossier structure, preferences) copied the full charter into
  their fixtures and failed on the public tree, which carries only the summary; they now copy the file
  `charter_path()` resolves. `test_stage_agents.sh` still checks every stage agent's grants, and runs its cross-check
  against the full charter's D27, D39 and D41 rows only where that file exists.
- The release tools accept a Gates run started by `workflow_dispatch` on exactly the commit in question, as well as a
  push run: `tag-release.sh` for the long-suites evidence (D46 is unchanged: the long suites must pass on the signed
  commit), and `release-merge-and-sign.sh` and `merge-forward.sh` when no pull-request check registers. On release day
  the public repository's push and pull_request events started no workflow (D45 condition 4).
- The p2 and p3 kernel snapshots are re-taken under the public history.

**Toolchain:** agentteams `v1.1.0` at `9b16fb54` · researchteam `v1.1.0` at `938dd663` · Lean `leanprover/lean4:v4.34.1` · Mathlib `d13f23b`.

## [1.0.1] — 2026-10-23

### release notes

`v1.0.1` is the first 1.0.x patch of mathagents, tagged on `release/1.0`. It carries `v1.0.1-rc.2` unchanged apart
from the version, this section and the §6 waiver note in `docs/release-policy.md`:
- the researchteam pin moves to `v1.0.1`, whose `update` and autosync gate honour `brief.json` `"frozen_surfaces"`
  (`["codex", "goose"]` here);
- #53 is included;
- the 1.0.1 render, which changes no agent's instructions;
- the `.agentteams-status/` ignore fix from rc.2.

The rc.2 soak (run 39880227613) passed the autosync gate and left the frozen Codex and Goose surfaces, AGENTS.md and
the governance roots untouched. The run is marked failed only because this repository does not let GitHub Actions
open pull requests, so its final step was refused. The operator waived the run-success criterion for that step
(`docs/release-policy.md` §6). See the `[1.0.1rc1]` and `[1.0.1rc2]` sections for the details.

**To pin this release:** verify the tag against `~/.config/agentteams/allowed_signers`, then pin the commit it points to
(its peeled commit), never a branch.

**Toolchain:** agentteams `v1.0.0` at `cc5b8c9e` · researchteam `v1.0.1` at `b55e2307` · Lean `leanprover/lean4:v4.34.1` · Mathlib `d13f23b`.

## [1.0.1rc2] — 2026-10-22

### release notes

`v1.0.1-rc.2` replaces `v1.0.1-rc.1`, whose soak failed (run 39817544064): the AgentTeams Autosync gate's file-scope
check stopped on agentteams' runtime `.agentteams-status/.gitignore`, which un-ignores itself. The frozen Codex and
Goose surfaces held in that run. This candidate adds the one fix below to rc.1 and gets a new soak before `v1.0.1`.

### Fixed
- `.gitignore` ignores agentteams' runtime `.agentteams-status/` directory. Its own `.gitignore` un-ignores itself, so
  the AgentTeams Autosync gate's file-scope check stopped on it as an out-of-scope change (the v1.0.1 soak, run
  39817544064). With it ignored, an autosync run that creates the directory passes the check.

**Toolchain:** agentteams `v1.0.0` at `cc5b8c9e` · researchteam `v1.0.1` at `b55e2307` · Lean `leanprover/lean4:v4.34.1` · Mathlib `d13f23b`.

## [1.0.1rc1] — 2026-10-21

### release notes

`v1.0.1-rc.1` is the release candidate for the first 1.0.x patch, tagged on `release/1.0`. It moves the researchteam
pin to `v1.0.1`, whose `update` and managed autosync gate honour `brief.json` `"frozen_surfaces"`. This repository
sets that key to `["codex", "goose"]`, so the gate leaves the frozen Codex and Goose surfaces alone and the paused
autosync schedule can resume after the 1.0.1 soak. It also carries #53, and the 1.0.1 render on the new pins (the
render itself changes no agent's instructions). Following the existing practice, it gets a signed RC and a soak
before the final `v1.0.1` tag.

**To pin this release:** verify the tag against `~/.config/agentteams/allowed_signers`, then pin the commit it points to
(its peeled commit), never a branch.

### Changed
- `toolchain.lock` pins researchteam `v1.0.1` (`b55e2307`, the peeled commit of its verified signed tag). agentteams
  stays at `v1.0.0` (`cc5b8c9e`).
- `brief.json` declares `"frozen_surfaces": ["codex", "goose"]`. `scripts/lib/frozen_surfaces.sh` reads it, and
  validates it as researchteam does (a non-array value, an unknown id or a duplicate stops the run), so the gate and
  the refresh can't disagree. `MATHAGENTS_FROZEN_SURFACES` stays as an override that must name the same set.
- The 1.0.1 render on these pins: the build-logs still name agentteams `cc5b8c9e`, and no agent's instructions change.
  researchteam's sync adds `.env`, `.env.*` and `*.env` to `.gitignore` (templates stay committable).
- `references/preferences.toml` no longer calls the `finite-probability` object logic planned.

### Fixed
- The M6 pilot notes in `@statement-formalizer`, `@proof-strategist` and `@tactic-planner` apply only where the
  project's `brief.json` grants the agent agentteams_runner tools (`mcp_grants`). An instance that vendors these
  agents without the grant (`mathagents sync`) no longer tells them they hold runner tools; they return text (D39).
  Found by baseAgent in a trial rc.1 sync.

**Toolchain:** agentteams `v1.0.0` at `cc5b8c9e` · researchteam `v1.0.1` at `b55e2307` · Lean `leanprover/lean4:v4.34.1` · Mathlib `d13f23b`.

## [1.0.0] — 2026-10-19

### release notes

`v1.0.0` is the first stable release of mathagents, tagged on `release/1.0` in the coordinated 1.0 release with
agentteams, researchteam and baseAgent (`docs/release-policy.md` §6). It carries `v1.0.0-rc.1`'s content, plus the
version, this section, and the Phase T lock move from the release candidates to agentteams `v1.0.0` and researchteam
`v1.0.0`, with the 1.0 render on them (`docs/release-policy.md` §6: Codex and AGENTS.md stay frozen; Goose stays
as rendered before M6, since agentteams refuses Goose under the write switch). From this release
the project follows Semantic Versioning as defined in `STABILITY.md`; fixes land on `release/1.0` as 1.0.x.

**To pin this release:** verify the tag against `~/.config/agentteams/allowed_signers`, then pin the commit it points to
(its peeled commit), never a branch.

### Changed
- `toolchain.lock` pins agentteams `v1.0.0` and researchteam `v1.0.0`, the peeled commits of verified signed tags.
- The 1.0 render on them: the build-logs name agentteams `cc5b8c9e`; no agent's instructions change. researchteam's
  Layer-2 sync brings its citation-audit fix (#87): `bridge citation-audit` now exits 2 when nothing could be checked and
  reports `DEFECT[NOBIB]` for cited deliverables with no `.bib`, instead of passing; mathAgents' `reports/` audit is
  unchanged by it (0 DEFECT).
- `docs/release-policy.md`: the pins, the autosync resume condition, and the v1.0.0 waiver of the soak-pass criterion
  (shared policy draft 9).

### Known limitations
- **The AgentTeams Autosync stays paused** (`workflow_dispatch` only). researchteam 1.0.0's sync gate runs
  `researchteam update` in a way that rewrites the Goose and Codex surfaces mathagents keeps frozen for 1.0, so a
  dispatched run fails (joint soak, run 39173598260). The fix is planned for researchteam 1.0.1; the schedule resumes once
  the lock moves to a release that has it. Until then, render with `scripts/refresh_agent_surfaces.sh`, which keeps the frozen surfaces.
- **M6 (staged writes, Claude only) continues as a 1.0.x pilot.** The operator's go/no-go was GO,
  conditional. Open in 1.0.x: agentteams counts the client's `.claude/hook-notices`
  writes as a confined command's undeclared writes, so a passing command can return ok:false (M6-F7; rerun it); a
  granted agent can't fetch a long `run_command`'s result (M6-F5); `@axiom-auditor` has no confined entry, so its gate
  runs stay on the orchestrator; and the runner notes in four agents' Project-Specific Notes don't yet follow
  `mcp_grants` (#53, 1.0.1).
- The Goose readfs path issue under 1.0.0rc1's Known issues still applies while Goose is not re-rendered.

**Toolchain:** agentteams `v1.0.0` at `cc5b8c9e` · researchteam `v1.0.0` at `a21e7db7` · Lean `leanprover/lean4:v4.34.1` · Mathlib `d13f23b`.

## [1.0.0rc1] — 2026-10-18

### release notes

`v1.0.0-rc.1` is the first release candidate of the mathagents 1.0 line, tagged on `release/1.0`. It is part of a
coordinated release with agentteams, researchteam and baseAgent: all four repositories test their release candidates
together (the "joint soak") and then tag 1.0.0 on the same day, in dependency order (`docs/release-policy.md` §6).

This candidate renders its agent team with agentteams `v1.0.0-rc.14` and researchteam `v1.0.0-rc.3`, both signed release
tags. Three researcher agents now write only through agentteams' runner, and the orchestrator approves each staged
write. The Goose and Codex surfaces are left as they were rendered before this line (frozen) for 1.0. An instance whose
`mathagents.toml` lists `codex` among `[agents] surfaces` must remove it: on agentteams 1.0 `mathagents sync` refuses
that surface and leaves the committed `.codex` files as they are. From 1.0.0 the project follows Semantic Versioning as
defined in `STABILITY.md`.

**To pin this release:** verify the tag against `~/.config/agentteams/allowed_signers`, then pin the commit it points to
(its peeled commit), never a branch. baseAgent moves its `proofs` extra from v0.2.7 to that commit in its own reviewed
PR. v0.2.7 was the last 0.x release; the unreleased v0.2.8 work is part of this line.


mathagents freezes at 1.0.0 on agentteams 1.0 final (decision D43). v0.2.7 is the last 0.x release; the v0.2.8 work
(#44) is folded into this line without a tag.

### Added
- **M6 pilot (D43), staged, Claude only:** `@proof-strategist`, `@tactic-planner` and `@statement-formalizer` write
  through agentteams' `agentteams_runner` MCP server (`read_file_hashed`, `write_file`); the orchestrator approves
  each staged write. `@statement-formalizer` also holds `run_command` for its allowlisted commands, run confined (a
  Rule 11 relaxation by the operator's Ed25519-signed decision). The pinned server is installed at
  `.agentteams/bin/agentteams-runner-mcp.py`.
- `toolchain.lock` at the repository root: the one record of the agentteams and researchteam commits this checkout
  renders with. `scripts/lib/agentteams_provenance.py` refuses a render on any other agentteams commit (unless
  `MATHAGENTS_ALLOW_UNLOCKED_AGENTTEAMS=1`, which warns), and accepts a detached release checkout at the locked commit.
- `scripts/lib/guard_bespoke_canonical.sh`: snapshots the bespoke agents' canonical `.github` sources before
  `researchteam update` and verifies them after it; a changed source stops the run (researchteam 1.0.0rc1, #50, keeps
  them), and is fixed from git, never by the guard.
- `STABILITY.md` for 1.0, `docs/release-policy.md` (the shared v1.0.0 policy with agentteams, researchteam and
  baseAgent), `docs/release-checklist.md`, and `scripts/operator/tag-release.sh` (SSH-signed tags, verified against
  `~/.config/agentteams/allowed_signers`).
- CI runs the gates on `release/**` branches and `v*` tags.
- The AgentTeams Autosync workflow verifies a release-locked researchteam before installing it (researchteam
  #77/#78, from the signed v1.0.0-rc.3 scaffold): an annotated tag, signed by a key in the `AGENTTEAMS_ALLOWED_SIGNERS`
  secret, whose peeled commit is the lock's. It refuses without the secret.

### Changed
- From #44 (agentteams conformance, D42): the bespoke agents take the brief's write policy from agentteams itself
  (`--interop-from … --description brief.json`, agentteams #174); `scripts/lib/bespoke_write_policy.py` is retired;
  Codex takes agentteams' `sandbox_mode` and is checked, never rewritten; pilot-only agent text is conditional.
- The write switch covers Claude only (`write_policy_frameworks: ["claude"]`); agentteams #204 refuses Goose under it.
  Goose, Codex and the Goose-owned AGENTS.md stay frozen as rendered before M6. Codex stays frozen for 1.0 (shared
  policy draft 6 §5, agentteams #210); orchestrator-only comes with agentteams' 1.0.x Codex interop backport.
- `toolchain.lock` pins agentteams `v1.0.0-rc.14` and researchteam `v1.0.0-rc.3` (the joint soak pair), the peeled
  commits of verified signed tags, with `agentteams.tag=` and `researchteam.tag=` lines.
- `scripts/refresh_agent_surfaces.sh` derives the bespoke agents in canonical shape (`$T/proj/.claude/agents`,
  `--overwrite`), copies back only the 11 bespoke files, and installs the runner server after an sha256 check.
- The agentteams autosync's weekly schedule is paused for the freeze (`workflow_dispatch` only).
- A frozen Codex is skipped by `researchteam update --no-codex` (researchteam #64), then checked against HEAD, instead
  of being moved aside for the run (`scripts/refresh_agent_surfaces.sh`, `scripts/operator/pause_signing_and_render.sh`).
- `brief.json` excludes the bespoke `interpretation-advisor` from researchteam's upstream notes sync
  (`researchteam_notes.exclude`, researchteam #79), so `researchteam update` leaves it byte-identical on every surface.
- `brief.json` declares its retrieval contract (`retrieval_integration`, sparse-vector over the `reports` literature
  library; researchteam #62), so every surface's roster is built from the same declaration.
- `mathagents` doctor and the refresh refuse an agentteams older than 1.0.0rc9.

### Fixed
- `interpretation-advisor` is restored on every surface. researchteam's scholarly sync ("above-notes", researchteam
  90f497a) had replaced the retargeted bespoke agent (D24) with researchteam's in the 2026-10-14 autosync.

- `scripts/validate_dossier.py` fails closed (exit 2) when git cannot run, instead of reading the failure as "not a
  git work tree" and skipping the append-only counterexample checks (M6-F4: under the runner's macOS sandbox, git
  exited 71 and every check passed). git runs with `LC_ALL=C`.

- `mathagents sync`'s Goose export works with agentteams 1.0.0rc12+: the pinned `agentteams_readfs` server is
  staged for the projection (agentteams' internal `pinned_readfs_mcp_content`, guarded by a test), and grant-mode
  recipes are checked, never wider than the agent's tools, instead of being refused. A `codex` surface is refused
  with an explicit message (Codex is frozen for 1.0; shared policy section 5, agentteams #210): instances remove it
  from `[agents] surfaces` and keep their committed `.codex` files. CI runs the real-agentteams projection tests.
- The refresh keeps the security gate's consumption mark in Goose's decisions log when it restores the frozen
  `.goose`; the 1.0 render's single-use clearance is marked used there as in the other two logs.

### Known issues
- Goose grant-mode recipes exported by `mathagents sync` launch `scripts/goose-readfs-mcp.py` relative to the
  instance, which sync does not ship (the instance's own Goose render installs it). Goose is frozen for 1.0, so this is
  not live; before Goose is unfrozen, sync should ship the pinned server and check its sha256 at runtime.

### Known issues (M6)
- On macOS, agentteams rc.12's sandbox couldn't run git (`/usr/bin/git` is the xcrun shim), and a confined write root
  covering `lean/.lake` let lake delete the worktree's Mathlib sources (M6-F3, restored). Fixed in agentteams rc.13
  (xcrun launchers resolve to the real tool; a package-store write root warns), with a narrowed confined file that
  keeps `lean/.lake/packages` out of `@statement-formalizer`'s write roots. rc.14 fixes the runner failing long
  confined commands on its own heartbeat (M6-F6). M6-F5 (a granted agent can't fetch a long run_command's result)
  is a 1.0.x item. The M6 phase 2 re-run follows the rc.1 cut, during the joint soak.

**Toolchain:** agentteams `v1.0.0-rc.14` at `c22aca0e` · researchteam `v1.0.0-rc.3` at `3358b6c2` · Lean `leanprover/lean4:v4.34.1` · Mathlib `d13f23b`.

## [0.2.7] — 2026-10-08

### Added
- P5: agentteams' write-policy pilot. Only the orchestrator writes, enforced on Claude and Goose (D41, amending D39).
  Researchers return change-proposals and command-requests, which the orchestrator applies through agentteams'
  runner. Gates: lean-draft-scan and strategy-sha. Records under protected paths.

### Changed
- The constitutional gate is fail-closed on error.

**Toolchain:** agentteams 1.0.0rc8 at `5562222` · Lean `leanprover/lean4:v4.34.1` · Mathlib `d13f23b`.

## [0.2.6] — 2026-10-06

### Fixed
- Pipeline friction from the odd-sum trial: `scan_lean_draft` reads stdin; the validator grammars are in the
  producing agents; the orchestrator re-validates.

**Toolchain:** agentteams 1.0.0rc8 (commit not recorded) · Lean `v4.34.1` · Mathlib `d13f23b`.

## [0.2.5] — 2026-10-06

### Changed
- The pipeline agents are researchers; only the orchestrator writes (D39, PR #18).

**Toolchain:** agentteams 1.0.0rc8 (commit not recorded) · Lean `v4.34.1` · Mathlib `d13f23b`.

## [0.2.4] — 2026-10-06

### Added
- Lean-version governance as harness features (baseAgent LV1–LV11; D38; PR #16): the pin is read in one place
  (`scripts/lean_pin.py`), G-KERNEL fails on a toolchain mismatch, `verified-toolchains.json`, `mathagents bump`.

**Toolchain:** agentteams 1.0.0rc8 (commit not recorded) · Lean `v4.34.1` · Mathlib `d13f23b`.

## [0.2.3] — 2026-10-05

### Changed
- The pipeline agents conform to the agentteams contract: only the orchestrator dispatches; each agent has an
  Invariant Core; on a read-only surface the orchestrator runs the agent's writes.
- Export requires an orchestrator (`sync` and `agents export` refuse otherwise; `doctor` reports roster gaps).

### Added
- `lean_docs` gate: Lean and Mathlib documentation follow the instance's pinned toolchain, never latest.

**Toolchain:** agentteams 1.0.0rc8 (commit not recorded) · Lean `v4.34.1` · Mathlib `d13f23b`.

## [0.2.2] — 2026-10-05

### Added
- Learned-block-aware lock: learned blocks are excluded from the agent-file digest, carried across re-renders,
  policy-screened and reported when changed.
- `[agents] surfaces`: mathagents derives, scopes (to `tools:`) and locks the claude, goose and codex forms of the
  pipeline agents.

**Toolchain:** agentteams 1.0.0rc8 (commit not recorded) · Lean `v4.34.1` · Mathlib `d13f23b`.

## [0.2.1] — 2026-10-05

### Added
- G-KERNEL rows for structure and inductive types; the `[agents]` namespace; baseAgent follow-ups H1–H4.

**Toolchain:** agentteams 1.0.0rc7 (commit not recorded) · Lean `v4.34.1` · Mathlib `d13f23b`.

## [0.2.0] — 2026-10-05

### Added
- First release for in-house consumers: an importable private package (D35) and toolchain-bump tooling. Verified on
  Lean/Mathlib v4.34.1 only.

**Toolchain:** agentteams 1.0.0rc7 (commit not recorded) · Lean `v4.34.1` · Mathlib `d13f23b`.

[Unreleased]: https://github.com/jlcatonjr/mathAgents/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/jlcatonjr/mathAgents/releases/tag/v1.1.0
[1.0.1]: https://github.com/jlcatonjr/mathAgents/compare/v1.0.0...v1.0.1
[1.0.1rc2]: https://github.com/jlcatonjr/mathAgents/compare/v1.0.1-rc.1...v1.0.1-rc.2
[1.0.1rc1]: https://github.com/jlcatonjr/mathAgents/compare/v1.0.0...v1.0.1-rc.1
[1.0.0]: https://github.com/jlcatonjr/mathAgents/compare/v1.0.0-rc.1...v1.0.0
[1.0.0rc1]: https://github.com/jlcatonjr/mathAgents/compare/v0.2.7...v1.0.0-rc.1
[0.2.7]: https://github.com/jlcatonjr/mathAgents/compare/v0.2.6...v0.2.7
[0.2.6]: https://github.com/jlcatonjr/mathAgents/compare/v0.2.5...v0.2.6
[0.2.5]: https://github.com/jlcatonjr/mathAgents/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/jlcatonjr/mathAgents/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/jlcatonjr/mathAgents/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/jlcatonjr/mathAgents/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/jlcatonjr/mathAgents/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/jlcatonjr/mathAgents/releases/tag/v0.2.0
