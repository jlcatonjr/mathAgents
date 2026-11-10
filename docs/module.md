# mathagents as a module

`mathagents` packages the mathAgents proof-development harness so another repository can use its Lean
gates, its dossier pipeline and its pipeline agents (decision D35). The source is public on GitHub under the Apache-2.0 licence. The package is classified
"Private :: Do Not Upload", so it is never uploaded to PyPI: install it from git or from a local checkout.

## Harness and instance

| | Owned by | Contents |
|---|---|---|
| **Harness** | mathAgents (this repository) | gate scripts (`scripts/*.py`, `check_proof_integrity.sh`), Lean templates (`scripts/lean/`), record schemas, the object-logic and engine registries, the decision charter, `docs/kernel-gate.md`, the Lean-version rules (`docs/lean-version-governance.md`), the eleven pipeline agents, the harness spec, the toolchain-bump tools and guide, the register of verified toolchains |
| **Instance** | the consuming repository | `lean/` (the Lake package under the gates), `reports/dossiers/`, `reports/kernel/` (generated), `references/preferences.toml`, `references/axiom-allowlist.json`, `mathagents.toml`, `mathagents.lock.json` |

The gate scripts are the single source of gate logic. They check the tree named by `MATHAGENTS_ROOT`
(the CLI sets it), or this checkout when it is unset. An instance never runs gate code of its own.

In a checkout or an editable install, the harness is the checkout. In a wheel, `setup.py` copies the
harness files, listed in `mathagents/_harness_files.py`, into `mathagents/_harness/` with the same layout.

## Install

```bash
# from a local checkout (editable: tracks this working tree)
pip install -e /path/to/mathAgents
# from git, at a signed release tag or its commit; never a branch (CONTRIBUTING.md has the verified install)
pip install "mathagents @ git+https://github.com/jlcatonjr/mathAgents.git@<tag-or-commit>"
```

Python 3.11 or later; the only dependency is `jsonschema`. The gates also need elan/Lean and the
instance's Mathlib build cache (`cd lean && lake exe cache get`).

## Instance requirements

- `lean/lakefile.toml` declares exactly two `lean_lib`s: a proved library and an open-work library
  whose name ends in `WIP`. The proved library never imports the WIP one. `defaultTargets` names both.
- Mathlib (and every other dependency) is a pinned **git** dependency; a local `path` dependency fails
  G-KERNEL. `lake-manifest.json` is committed.
- Library names come from the lakefile, and the name index and the agents use them. Declarations may
  live in any namespace (baseAgent's are `ZIT.*`). New dossiers use `[agents] namespace` for theirs.
- The G-KERNEL report lists theorems, definitions, opaques and, from v0.2.1, structure and inductive
  types. So prose can bind `[Lean: ZIT.Env]`. A type declared inside a dossier's namespace therefore
  needs a G-FID entry, as a definition there already does.

## Orchestrator required

The pipeline agents run only under an orchestrator. It holds the team's write authority and dispatches every
stage, and each agent returns to it.

- `sync --write` and `agents export` refuse a destination that has no `orchestrator.agent.md`, before writing
  anything. In that case, instantiate an agentteams team there first
  (`agentteams --description <brief.json> --output <dir>`), then export. The check reads only the Copilot
  file; with `[agents] surfaces` set, it does not check that the Claude, Goose or Codex orchestrator exists.
- Fold the exported agents into that orchestrator's `agents:` roster with `agentteams --adopt-orphans`. It's a
  reviewed step, because it widens the orchestrator's grant.
- Until then, `doctor` lists the agents that are missing from the roster as an advisory line, not a failure.
  Route them through the orchestrator meanwhile.

## Commands

```bash
mathagents init Projects/MyProofs --agents-to ../../.github/agents --team baseAgent \
  --exclude lean-informalization --namespace ZIT   # scaffold an instance; never exports agents
mathagents sync --write                     # exports the agents, once the settings are reviewed; refuses a
                                            # destination with no orchestrator.agent.md
mathagents run check_proof_integrity        # G-KERNEL -> reports/kernel/latest.json
mathagents run build_name_index             # Mathlib name index for G-NAME and G-BLUEPRINT
mathagents run lean_docs [--online]         # Lean reference + Mathlib source for the pinned toolchain
mathagents run lean_pin                     # the pin (P1-P4) and its consistency (exit 1 on a problem)
mathagents run validate_dossier [--require-fid <slug>] [--require-stage <slug> N]
mathagents run validate_registries
mathagents run preferences check
mathagents run log_counterexample add ...   # G-CX log, append-only
mathagents run snapshot_kernel <slug>       # Stage 8
mathagents status                           # on/off for this machine (exit 0 on, 3 off); the pin, verified?
mathagents doctor                           # version, harness, instance, switch, lakefile rule, lock drift,
                                            # the pin (P1-P4) and version text that is not the pin
mathagents bump trial --to /tmp/trial --tag <tag>   # toolchain-bump wave (docs/lean-toolchain-upgrade.md)
```

The instance root is `--root`, else `MATHAGENTS_ROOT`, else the nearest `mathagents.toml` above the
working directory, else this checkout when the working directory is inside it. A repository-level `mathagents.toml` with `[workspace] default = "Projects/MyProofs"`
points repository-level agents at the instance.

From Python, every API function takes `root=`, else `MATHAGENTS_ROOT`, else (editable install only) this
checkout; the search for the nearest `mathagents.toml` is the CLI's alone. See `docs/api-reference/`.

## `mathagents.toml`

```toml
[instance]
name = "MyProofs"
created_with = "1.0.0"

[agents]
export_to = "../../.github/agents"   # where sync keeps the pipeline agents (relative to this file)
team = "baseAgent"                   # the team name in the agents' `name:` lines
exclude = ["lean-informalization"]   # agents the consumer maintains itself
namespace = "ZIT"                    # dossier declarations live in `ZIT.<Slug>` (default: the proved library)
surfaces = ["claude", "goose", "codex"]  # also derive and lock the agents' other surfaces (agentteams 1.0.0rc9+)
```

With `surfaces` set (and `export_to` a repository's `.github/agents`), `sync` runs `agentteams --interop-from`
on the rendered agents. It writes `.claude/agents/<name>.md`, `.goose/recipes/<name>.yaml` and
`.codex/agents/<name>.toml` next to them, each scoped to the agent's `tools:`, and locks them like the
Copilot files. Each Goose recipe lists only the extensions and `available_tools` its tools grant. Codex takes
agentteams' `sandbox_mode` (`workspace-write` exactly when an agent declares `edit`), which mathagents checks
and never rewrites; `codex_workspace_write` was retired with the agentteams conformance work (D42, folded into the 1.0 line by D43) and is ignored with a notice (D42). Sync and
`doctor` refuse an agentteams older than 1.0.0rc9. The pipeline agents are researchers (D39): none holds `edit`,
the orchestrator writes what they return, and the four that keep `execute` run `read-only` on Codex (which may
block `lake`'s `.lake` writes there; the agent then returns the command to the orchestrator, which runs it); on Claude and Goose their shell is still a write path, held by their
instructions and the orchestrator. A projection carrying any key that could widen an agent is
refused. See `docs/uniform-surface-projection.md`.

## Switching it off on one machine

The architecture is **on by default**. A machine that prefers not to use it adds one line to its `.env`
at the repository root:

```bash
MATHAGENTS_ENABLED=0        # also: false / no / off; 1 / true / yes / on switches it back on
```

`.env` is machine-local and must be gitignored. `mathagents doctor` reports a `.env` that is not
gitignored. A process environment variable of the same name overrides `.env`, for example in CI. Only
that one line of `.env` is read, so other settings and secrets in the file are left alone.

Switched off:

- `mathagents run` refuses with **exit 3** and runs nothing. It never exits 0, because a stage
  precondition such as `validate_dossier --require-fid` must not pass without running.
- `mathagents status` exits 3, and the exported agents and the consumer's rules tell the orchestrator
  to check it before dispatching a pipeline agent.
- `init`, `sync` and `agents export` still work. They maintain shared repository files, which must not
  depend on one machine's preference.
- CI has no `.env`, so the gates stay on there unless the workflow sets the variable.

## Updating an instance

```bash
pip install -U "mathagents @ git+ssh://git@github.com/jlcatonjr/mathAgents.git@<new-tag>"
mathagents sync            # dry run: lists add / update / conflict
mathagents sync --write    # applies; refuses every file edited locally since it was vendored
mathagents run check_proof_integrity   # re-run G-KERNEL under the new gate logic
```

`mathagents.lock.json` records the sha256 of every vendored file and exported agent. `sync` updates a
file only when it still matches its lock entry. A locally edited file is reported as a conflict. You
can reconcile it by hand, or replace it with `--overwrite PATH`.

An agent file's `AGENTTEAMS-LEARNED` block is the one exception. `agentteams --sync-agent-docs` copies
that block across an agent's surfaces, so it is left out of the agent's digest, and `sync` carries it
into the new render after an upgrade. A malformed or misplaced block, or one whose content trips the
policy denylist (instruction overrides, capability lifts, permission widening), reads as an edit. The lock
records each block's digest, so `sync` and `doctor` report a block added, changed or removed. Every byte
outside the block is still checked (`docs/uniform-surface-projection.md`).

The seeded files (`preferences.toml`, `axiom-allowlist.json`) are the instance's own and are never
synced. Every G-KERNEL report records `harness_sha256`, the digest of the gate logic that produced it,
so a verdict reached before an upgrade can be told apart from one reached after it.

## Governance that travels with the harness

- G-KERNEL, G-FID, G-AX, G-CX, G-NAME and G-BLUEPRINT run unchanged against an instance. The
  append-only G-CX and fidelity comparisons also apply to an instance in a subdirectory of a git
  work tree (D35).
- An instance cannot widen the base axiom envelope. `scripts/axiom_allowlist.py` refuses any
  `base_axioms` beyond Lean's three standard axioms. Further axioms need G-AX approvals in the
  instance's own allowlist.
- DD-29 still holds: no API function and no CLI command writes a G-FID approval, a G-AX record or a
  G-CX verdict. Those stay human decisions in the consuming repository.
- The pipeline rules the agents rely on (the G-FID precondition, G-CX logging only through the script,
  the Stage 0 problem card, D32 preferences) belong in the consumer's instruction file. See
  `docs/baseagent-integration-plan.md` for the block baseAgent adds.

## The grammars the validators check

Three dossier artifacts are parsed, not just read, so a draft that is fine as prose can still fail. The pipeline
agents that produce them carry these rules in their bodies; a consumer orchestrator needs the first one itself.

- **Problem card** (`problem-card.md`; `card_fields`, `check_card` and `check_card_vs_preferences` in
  `scripts/dossier_structure.py`). One `- **<Field>:** <value>` line per field, each field once. `Object logic:`,
  `Engine:` and `Domain:` hold exact registry ids and nothing else on that line: an `id` from
  `references/object-logics.json` that is not `planned`; one or more comma-separated `id`s from
  `references/prover-engines.json`; one value of the `suited_domains` enum in
  `references/schemas/prover-engines.schema.json`. A gloss goes on the next line, indented. The orchestrator
  writes the card (its Project-Specific Notes give right and wrong examples).
- **Derivations** (`derivations.md`; `check_derivations`). Steps are `<n>. <formula>  [<justification>]`; only
  the last bracket is the justification, and every integer in it is a citation of an earlier step in the same
  node, so instantiations and notes go in the formula text. See `@logic-articulator`.
- **Node headers** (`derivations.md` and `tactic-plan.md`; `NODE_LEAN` in `scripts/check_lean_bindings.py`). The
  first token after `Lean:` must resolve to a declaration in the kernel report or the pinned name index; an
  inline step binds to its enclosing declaration. See `@logic-articulator` and `@tactic-planner`.

## Lean versions

Agents work to the instance's pin, never to a version written in prose: `lean/lean-toolchain` (P1), the
lakefile's Mathlib `rev` (P2) and the `lake-manifest.json` Mathlib entry (P3), with the `.lake` Mathlib checkout
built for P1 (P4). The rules are `docs/lean-version-governance.md`, vendored into every instance, and each
pipeline agent's Invariant Core (`@lean-informalization`: its notes) points to them. The harness enforces what it can (D38):

- G-KERNEL runs `lean --version` in `lean/` before building, and fails without building when the Lean that runs
  is not the pinned release (for example under an `ELAN_TOOLCHAIN` override). Every reader of the report refuses
  one whose `lean_version` and `toolchain_pin` disagree.
- G-KERNEL fails when the lakefile's Mathlib `rev` differs from the manifest's `inputRev`, and, after its build,
  when the `.lake` Mathlib checkout was built for another toolchain. `build_name_index` and G-NAME refuse such a
  checkout, and `build_name_index` refuses a missing one ("Mathlib not built").
- `mathagents doctor` reports pin problems, and warns about any `v4.x.y` in an exported agent or a vendored doc
  that is not the pin. A line that names the harness's own pin on purpose (charter D8) carries
  `<!-- harness-pin -->`.
- `mathagents status` prints the pin and whether the harness is verified on it
  (`references/verified-toolchains.json`, shipped with the harness). An unverified pin is a warning.
- Fidelity, G-AX and counterexample records take optional `toolchain_pin` and `mathlib_rev` stamps.
  `validate_dossier` warns about a fidelity or G-AX stamp from an earlier pin, which needs re-approval.
- The bump tools ship in the wheel (`mathagents bump trial | statement-types | statement-drift`).

## Not shipped

The operator tools (`scripts/operator/`) are not shipped: approval recording and signed rendering
stay with each repository's operator. The researchteam bridge and maintenance scripts, and the
mathAgents dossiers and Lean library, are not shipped either.
