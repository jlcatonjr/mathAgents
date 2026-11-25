# `mathagents.cli`

The `mathagents` command ([D35](index.md#glossary); guide: `docs/module.md`): run the harness's gate
scripts against an [instance](index.md#glossary), scaffold an instance, and keep its vendored files and
exported agents current.

**CLI surface:** `mathagents` (console script), `python -m mathagents.cli`

## Public Surface

### `main(argv=None)`

Returns `int`.

Run the `mathagents` command with `argv` (default `sys.argv[1:]`). Unlike the rest of the API, `main`
prints its output, and it is the command's entry point.

**Exit codes** (returned):

- 0: done, or in sync;
- 1: findings (conflicts, pending changes, a failing gate);
- 2: usage error, including a `sync` or `agents export` destination that has no `orchestrator.agent.md`
  (the pipeline agents run only under an orchestrator);
- 3: switched off on this machine (see [`config`](config.md)).

**Raises** `SystemExit` instead of returning in these cases:

- an argparse usage error (code 2), `--help`, or `--version` (code 0);
- no instance found (code 1, with a message to pass `--root`, set `MATHAGENTS_ROOT`, or run
  `mathagents init`);
- an invalid `[agents]` setting in `mathagents.toml` (`namespace`, `team`, `surfaces`, `exclude`) or a
  surfaces projection error, with a message naming the setting.

The global option `--version` prints `mathagents <version>`.

The instance root is `--root`, else `MATHAGENTS_ROOT`, else the nearest `mathagents.toml` above the
working directory (`[workspace] default` there points at the instance), else this checkout when the
working directory is inside it.

| Command | Effect |
|---|---|
| `run [--root DIR] <gate> [args]` | run a harness gate script with `MATHAGENTS_ROOT` set to the instance; exit 3, without running, when switched off |
| `init <dir> [--name N] [--agents-to DIR] [--team T] [--exclude A ...] [--namespace NS]` | scaffold an instance: vendored contract files, seeded preferences and allowlist, `mathagents.toml`, `mathagents.lock.json`. Never exports agents (a later `sync --write` does) |
| `sync [--root DIR] [--write] [--overwrite PATH ...]` | refresh vendored files and exported agents (details below) |
| `agents export [--root DIR] [--to DIR] [--write] [--overwrite PATH ...]` | render the pipeline agents for the consumer's roster (and its `[agents] surfaces`, unless `--to` names a one-off destination) |
| `status [--root DIR]` | whether the architecture is on for this machine: exit 0 on, 3 off; also the Lean pin (details below) |
| `doctor [--root DIR]` | diagnose the instance (details below) |
| `bump [--root DIR] {trial,statement-types,statement-drift} [args]` | the toolchain-bump wave's tools, run from the harness (`docs/lean-toolchain-upgrade.md`). `trial` defaults `--from` to the instance's `lean/` and refuses a `--to` inside the instance or its git repository; exit 3, without running, when switched off |

#### The `sync` command

- Refreshes the vendored files and the exported agents. With `[agents] surfaces` set, it also refreshes
  the agents' claude, goose and codex forms: they are derived with `agentteams --interop-from`, then
  scoped to each agent's `tools:`.
- Codex takes agentteams' `sandbox_mode`, which is checked and never rewritten
  ([D42](index.md#glossary)). `[agents] codex_workspace_write` is retired and ignored with a notice.
- A file edited since its lock entry is a conflict; `--overwrite PATH` overwrites it anyway.
- An agent file's AGENTTEAMS-LEARNED block is left out of the lock digest (unless it trips the policy
  denylist), carried into a re-render, and reported when added, changed or removed.
- Agents no longer exported are reported as `untracked`; their files are kept.
- Without `--write` it is a dry run that lists the changes.

#### The `status` command

Prints whether the architecture is on for this machine (exit 0 on, 3 off). It also prints the instance's
Lean pin and whether the harness is verified on it, for example `pin v4.34.1: verified (…)`, from the
harness's `references/verified-toolchains.json`. That line never changes the exit code.

#### The `doctor` command

Prints, and checks:

- the version, harness, instance and switch, and whether the switch's `.env` is gitignored;
- the lakefile rule, and drift from the lock (learned blocks excluded, and reported when changed since
  the lock);
- the configured surfaces (from the lock), a problem when the installed agentteams is older than
  1.0.0rc9 or unusable, and how many agent files carry a learned block;
- the Lean pin. A [P1-P3](index.md#glossary) problem fails. These are warnings that never change the exit
  code: a `.lake` Mathlib checkout built for another toolchain; an unverified pin; and any `v4.x.y` in an
  exported agent or vendored doc other than the pin (a line carrying `<!-- harness-pin -->` is exempt).
