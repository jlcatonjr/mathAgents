# `mathagents.name_index`

The pinned-Mathlib name index behind [G-NAME and G-BLUEPRINT](index.md#glossary) (spec DD-17).

`reports/kernel/name-index.txt` (gitignored, machine-local) lists every declaration name in the
pinned Mathlib. A Lean name in prose resolves if it is in the fresh kernel report (project library)
or in this index; nothing is resolved by naming convention.

**CLI surface:** `scripts/build_name_index.py`

## Public Surface

### class `NameResolution`

*frozen dataclass*

Where a Lean name resolved: `source` is `kernel`, `mathlib` or None (unresolved). `status` is the
kernel status (`proved`, `open` or `failed`), set only when `source == "kernel"`; otherwise None.

**Properties:**

- `resolved -> bool`: `source is not None`.

| Field | Type |
|---|---|
| `name` | `str` |
| `source` | `str \| None` |
| `status` | `str \| None` |

### `build_name_index(*, root=None, timeout=None)`

Returns `CommandResult`.

(Re)build the name index for the pinned toolchain (`scripts/build_name_index.py`). Slow.

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `timeout`: seconds before the subprocess is killed (default: none).

**Raises:**

- `subprocess.TimeoutExpired`: `timeout` elapsed.

### `load_name_index(*, root=None)`

Returns `frozenset[str]`.

The names in the index.

**Raises:**

- `NameIndexError`: the index is missing, stale for the pinned toolchain, or malformed.

### `resolve_lean_name(*, root=None, name)`

Returns `NameResolution`.

Resolve a fully-qualified Lean name against the fresh kernel report, then the name index.

**Raises:**

- `KernelReportError`: the kernel report is not usable.
- `NameIndexError`: the name is not a project declaration and the index is not usable.
