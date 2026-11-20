# Operator preferences

Standing preferences for how agents in this repository work with the operator. Project-owned; not synced.

## Decisions (2026-11-20)

When an agent needs the operator's input on a decision, it asks through the host's interactive picker
(Claude Code's AskUserQuestion), with the options it judges best listed first and its recommendation marked,
so the operator can click to choose. It does not ask open-ended questions in prose when a picker would do.

## Scripts the operator runs (2026-11-20)

When a step must run outside the agent's sandbox (signing, a merge the operator performs, anything needing the
operator's keys or credentials), the agent writes it as a `.sh` file and gives one command that works from any
directory: an absolute path, never one relative to the current directory. Example:

```bash
shasum -a 256 ~/githubrepositories/mathAgents/tmp/by-week/2026-W47/operator/<script>.sh   # compare with the hash given
/bin/bash -p ~/githubrepositories/mathAgents/tmp/by-week/2026-W47/operator/<script>.sh
```

Operator scripts live under the gitignored `tmp/by-week/<week>/operator/`. The agent gives their sha256 for the
operator to compare before running them.
