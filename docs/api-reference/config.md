# `mathagents.config`

Whether the mathAgents architecture is switched on for this machine (D35).

It is on by default. A machine switches it off with `MATHAGENTS_ENABLED=0` in a `.env` file. That file
is machine-local and gitignored, so it is never committed. The process environment overrides `.env`.
The `.env` used is the nearest one at or above the instance root, up to the enclosing git work-tree
root. Only the `MATHAGENTS_ENABLED` line is read; no other value in the file is parsed, kept or
printed. Switched off, `mathagents run` refuses with exit code 3, so a gate that did not run never
reads as a pass.

**CLI surface:** `mathagents status`, `mathagents doctor`

## Public Surface

### `DISABLED_EXIT`

Constant: `3`

### `ENV_KEY`

Constant: `'MATHAGENTS_ENABLED'`

### class `Switch`

*dataclass, frozen*

The effective setting: `enabled`, where it came from (`default`, `environment` or a `.env` path), and
`problem` when the value is not a recognised boolean (the switch then reads as off).

| Field | Type |
|---|---|
| `enabled` | `bool` |
| `source` | `str` |
| `problem` | `str \| None` |

### `switch(*, root=None)`

Returns `Switch`.

The switch for an instance (default: the working directory). Recognised values: `1/0`, `true/false`,
`yes/no`, `on/off` (case-insensitive, optionally quoted, optionally `export`ed). An unrecognised value
fails closed (off).
