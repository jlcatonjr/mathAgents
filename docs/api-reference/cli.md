# `mathagents.cli`

The `mathagents` command (D35; guide: `docs/module.md`): run the harness's gate scripts against an
instance, scaffold an instance, and keep its vendored files and exported agents current.

**CLI surface:** `mathagents` (console script), `python -m mathagents.cli`

## Public Surface

### `main(argv=None)`

Returns `int`.

Run the `mathagents` command with `argv` (default `sys.argv[1:]`); returns the exit code: 0 done or
in sync, 1 findings (conflicts, pending changes, a failing gate), 2 usage error, 3 switched off on this
machine (see [`config`](config.md)). Subcommands:

| Command | Effect |
|---|---|
| `run [--root DIR] <gate> [args]` | run a harness gate script with `MATHAGENTS_ROOT` set to the instance; exit 3, without running, when switched off |
| `init <dir> [--name N] [--agents-to DIR] [--team T] [--exclude A ...] [--namespace NS]` | scaffold an instance: vendored contract files, seeded preferences and allowlist, `mathagents.toml`, `mathagents.lock.json`. Never exports agents (a later `sync --write` does) |
| `sync [--root DIR] [--write] [--overwrite PATH ...]` | refresh vendored files and exported agents, and, with `[agents] surfaces`, the agents' claude/goose/codex forms (derived with `agentteams --interop-from`, then scoped to each agent's `tools:`; Codex takes agentteams' `sandbox_mode` and is checked, never rewritten (D42; `[agents] codex_workspace_write` is retired and ignored with a notice)); a file edited since its lock entry is a conflict; an agent file's AGENTTEAMS-LEARNED block is left out of the lock digest (unless it trips the policy denylist), carried into a re-render, and reported when added, changed or removed; agents no longer exported are `untracked` (files kept) |
| `agents export [--root DIR] [--to DIR] [--write]` | render the pipeline agents for the consumer's roster (and its `[agents] surfaces`, unless `--to` names a one-off destination) |
| `status [--root DIR]` | whether the architecture is on for this machine: exit 0 on, 3 off. Also prints the instance's Lean pin and whether the harness is verified on it (`pin v4.32.1: verified (…)`, from the harness's `references/verified-toolchains.json`); that line never changes the exit code |
| `doctor [--root DIR]` | version, harness, instance, switch (and whether its `.env` is gitignored), lakefile rule and lock drift (learned blocks excluded, and reported when changed since the lock); the surfaces, the Codex opt-ins and how many agent files carry a learned block; the Lean pin (P1-P3 problems fail; a `.lake` Mathlib checkout built for another toolchain, an unverified pin, and any `v4.x.y` in an exported agent or vendored doc other than the pin are warnings, which never change the exit code; a line carrying `<!-- harness-pin -->` is exempt) |
| `bump [--root DIR] {trial,statement-types,statement-drift} [args]` | the toolchain-bump wave's tools, run from the harness (`docs/lean-toolchain-upgrade.md`). `trial` defaults `--from` to the instance's `lean/` and refuses a `--to` inside the instance or its git repository; exit 3, without running, when switched off |

The instance root is `--root`, else `MATHAGENTS_ROOT`, else the nearest `mathagents.toml` above the
working directory (`[workspace] default` there points at the instance), else this checkout when the
working directory is inside it.
