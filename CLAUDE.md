# Claude Interface Bridge for mathAgents

This file is the operating bridge for Claude users working in this repository.

## Project Purpose

Develop, verify, and explain mathematical and logical proofs across applied/modeling mathematics, research-level mathematics, competition problems, logic and foundations, and proofs used in the philosophy of science. Every proof is articulated through an explicit symbolic-logic pipeline (formal statement with fidelity check, proof-strategy blueprint, named-rule derivations, tactic plans) and is accepted only as Blueprint + Lean: a blueprint whose nodes are name-linked to Lean 4 declarations that build with no sorry, admit, or unapproved axiom. The Lean kernel judges validity; a human judges statement fidelity. Harness design decisions are derived from, and cited to, research on automated and LLM-assisted theorem proving, with Chicago author-date citations to verified sources.

Primary outputs:
- Deliverables in `reports/` and/or `Projects/`
- Reference/bibliography data under `references/`
- Governance and execution plans in `tmp/by-week/`

<!-- researchteam:generated sha256=89da0c3481b2c5022ce28e61d9764e4dae11fd94bc352eb648bd8007aba58f87 — regenerate with `researchteam personalize`; edits to generated regions are overwritten -->
<!-- >>> researchteam:managed — synced from upstream; do not edit inside this block -->
<!-- Everything ABOVE this marker (title + Project Purpose) is project-owned and preserved across
     `researchteam update`. Everything between the markers is synced from the framework. -->

## Working Rules

1. Keep claims traceable to explicit sources.
2. Do not fabricate references.
3. Preserve existing file structure and naming conventions.
4. For multi-step work, create a plan and step CSV in `tmp/by-week/YYYY-Www/`.
5. Prefer non-destructive changes unless explicitly requested.
6. When the project produces cited research deliverables, run the 2-fold citation & claim audit
   before compiling — `bash scripts/claude_researchteam_bridge.sh citation-audit <project>`
   (mechanical layer), then the doubled semantic audit in
   `docs/citation-claim-audit-protocol.md`. Unresolved citation/claim findings block compilation
   (fail-closed). A clean run means WELL-FORMED, not proof of non-fabrication.
7. Place every load-bearing source in its own time: date, place, audience and text version, with
   anachronism guarded in both directions. Follow `docs/historical-context-protocol.md`, and run
   `bash scripts/claude_researchteam_bridge.sh history-check <project>` before compiling.

## Quick Start

Run the bridge helper:

```bash
bash scripts/claude_researchteam_bridge.sh help
```

## Standard Workflow

1. Inspect current repo state.
2. Create/update plan artifacts in `tmp/by-week/` for multi-step edits.
3. Edit target files.
4. Run `bash scripts/claude_researchteam_bridge.sh validate`.
5. Commit and push when requested.

## Key Paths

- Agent infrastructure: `.github/agents/`
- Project definition: `brief.json`
- CI workflow: `.github/workflows/agentteams-sync.yml`
- Bridge docs: `docs/claude-interface-bridge.md`
- Framework + CLI reference: `docs/researchteam-framework.md`
- Claude support folder: `.claude/`

## Keeping Infrastructure Current

Keep framework infrastructure current with the researchteam CLI:

```bash
researchteam update          # interactive — shows diffs before applying
researchteam update --yes    # non-interactive (CI-safe)
researchteam update --dry-run  # preview only
```

`researchteam update` syncs framework files under `docs/`, `scripts/`, `.claude/`, and the
**managed block of this `CLAUDE.md`** from the upstream template, then (unless `.researchteam` sets
`layer1 = off`) runs `agentteams --update --merge` for agent infrastructure. A release-locked
`toolchain.lock` makes it sync from the verified researchteam tag instead of `main`. It never touches `brief.json`,
`Projects/`, or `references/`. This file's title and Project Purpose header, and `README.md`, are
project-owned and are generated from `brief.json` — not synced. To re-render them run
`researchteam personalize`; to re-render the agent team after a domain/identity change in
`brief.json` run `researchteam materialize`.

### Installing the toolchain (agents: verify this before relying on either tool)

`researchteam` is the entry point. `agentteams` is **installed through it as an extra**, never on
its own — it is not published to PyPI, so the base install deliberately declares
`dependencies = []` and a bare `pip install researchteam` leaves layer-1 agent regeneration
unavailable.

```bash
# base CLI only — layer-2 file sync, no agent regeneration
pip install "git+https://github.com/jlcatonjr/researchteam.git"

# recommended — pulls agentteams in, enabling `researchteam update`'s layer-1 pass
pip install "researchteam[update] @ git+https://github.com/jlcatonjr/researchteam.git"

# adds agentteams' research extra (web search, curated-source rating, claim verification)
pip install "researchteam[research] @ git+https://github.com/jlcatonjr/researchteam.git"

# a release instead of main: append the signed tag, e.g. ...researchteam.git@v1.0.2
# (pin the tag's peeled commit in toolchain.lock; see docs/release-policy.md upstream:
#  https://github.com/jlcatonjr/researchteam/blob/main/docs/release-policy.md)
```

Agents must not assume the toolchain is present, and must not assume that an `agentteams` found on
`PATH` belongs to the interpreter they are running under. Check both:

```bash
python -m pip show researchteam agentteams   # both must resolve in the ACTIVE interpreter
which researchteam agentteams                # both should sit in that same environment
python -c "import sys; print(sys.prefix)"    # the environment those two must belong to
```

If `agentteams` is missing, install the `update` extra above; if it resolves from a different
environment than `sys.prefix`, treat the toolchain as unavailable. Do not hand-edit generated
agent infrastructure as a workaround — the next sync discards the edit. Run `researchteam doctor`
for a full diagnosis.

**Pinned toolchain (derived repos).** `toolchain.lock` records the researchteam and agentteams
commits the repo was last synced and verified with; the AgentTeams Autosync rewrites it after each
green sync. To run exactly that pair:

```bash
bash scripts/bootstrap_toolchain.sh          # .venv with the pinned commits (gitignored)
bash scripts/bootstrap_toolchain.sh --local  # editable installs from your own checkouts
python3 scripts/check_toolchain.py           # installed vs toolchain.lock vs upstream main (not for release-locked pins)
```

The bootstrap installs researchteam *without* the `[update]` extra, because that extra pins the
agentteams commit researchteam was released with, which can differ from this repo's lock. It installs
agentteams *with* its `[signing]` extra (`cryptography`, under the S-10 vetted pins), so signed decision rows
verify in `.venv`. researchteam runs the `agentteams` installed beside it, so
`.venv/bin/researchteam` works without activating the venv; it falls back to `PATH` only when none
is installed beside it, and says so. To be warned at the start of each Claude session, merge
`.claude/settings.toolchain.example.json` into `.claude/settings.json` (an operator step;
researchteam never edits `settings.json`). `researchteam doctor` reports both.

## Notes for Claude Users

- If running outside a git worktree context, some validation checks may be reduced.
- Do not manually edit AGENTTEAMS fenced sections in agent docs. Route multi-file agent changes
  through orchestrated workflows.
- Back up research and agent files before update or merge runs.
- Use `.claude/README.md` for reusable templates and preflight checklists.

<!-- <<< researchteam:managed -->

## mathAgents: How Agent Infrastructure Is Updated

Project-owned. This section sits below the managed block, so `researchteam update` and `researchteam personalize`
keep it. Operator decision, 2026-10-28.

- **One update procedure.** Agent infrastructure is updated only by `bash scripts/refresh_agent_surfaces.sh`. It
  runs `researchteam update`, re-projects the bespoke agents through interop, renders every unfrozen surface
  natively, and checks render consistency, with a bridge guard before and after. It projects to every unfrozen
  surface on each update. A bare `researchteam update` or `agentteams --update` is not a complete update here.
- **Codex and Goose (CX-3, operator ruling 2026-11-09).** Both are unfrozen for 1.1.0 (`brief.json`
  `frozen_surfaces` is empty), effective with the agentteams v1.1.0 pin (MA-6) and the operator's Ed25519-signed
  Rule 11 rows `unfreeze-codex` and `unfreeze-goose` (`docs/release/unfreeze-*.decision-spec.json`), which researchteam itself verifies. Codex is under orchestrator-only: a native
  render with the role gate, hooks and launcher, then the bespoke agents imported into it read-only
  (`scripts/lib/project_bespoke_codex.sh`; agentteams #319). Goose runs **UNENFORCED**: agentteams still refuses
  orchestrator-only on Goose (`GOOSE_SWITCH_REFUSED`), so its recipes render off the switch: the bespoke ones are
  grant-scoped (`mathagents._surfaces scope-goose`), and the read-only and command-running ones carry `developer`
  (D34's accepted risk, accepted again 2026-11-09; `docs/release/unfreeze-goose.conditions.txt`). Also accepted
  ("Unfreeze both, accept the gap"): off the switch, Goose's sandbox profile no longer write-denies `.agentteams`
  or `.goose/recipes`, so a Goose session could edit the Codex role gate (item 3a there; agentteams handoff
  `docs/handoffs/2026-11-09-to-agentteams-goose-sandbox-control-plane.md`). Re-freeze Goose, or put it under the switch, once agentteams enforces it
  there (gap 1 in `docs/handoffs/2026-10-27-to-agentteams-native-projection-gaps.md`).
- **Autosync is paused.** The `agentteams-sync` workflow's schedule is disabled, and it runs only when the
  operator dispatches it. Pins move only to verified signed tags (`toolchain.lock`), with an @security row.
