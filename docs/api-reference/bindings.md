# `mathagents.bindings`

G-NAME: `[Lean: name | status]` bindings in dossier prose (spec DD-17, DD-18).

Every binding must resolve against the fresh kernel report or the pinned-Mathlib name index, and its
status tag must match the kernel. `check_lean_bindings` runs `scripts/check_lean_bindings.py`'s
logic in-process.

**CLI surface:** `scripts/check_lean_bindings.py`

## Public Surface

### class `BindingScan`

*dataclass*

The bindings found in a dossier; `errors` are bindings that look like one but do not parse.

| Field | Type |
|---|---|
| `slug` | `str` |
| `bindings` | `list[LeanBinding]` |
| `errors` | `list[str]` |

### class `LeanBinding`

*frozen dataclass*

One binding. `kind` is `narration` (`[Lean: X | status]`), `node` (a derivation or
tactic-plan node's `Lean:` name) or `lemma` (a tactic plan's `Lemmas:` entry).

| Field | Type |
|---|---|
| `file` | `str` |
| `line` | `int` |
| `name` | `str` |
| `kind` | `str` |
| `status` | `str \| None` |

### `check_lean_bindings(*, root=None, slugs=(), assembled_only=False)`

Returns `GateResult`.

Run G-NAME.

**Args:**

- `root`: mathAgents checkout.
- `slugs`: dossiers to check (default: all).
- `assembled_only`: with no slugs, check only Stage 7+ dossiers (as CI does).

**Raises:**

- `ValueError`: invalid slug.

### `list_lean_bindings(*, root=None, slug)`

Returns `BindingScan`.

Parse the dossier's bindings without resolving them.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.
