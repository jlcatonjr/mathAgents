# `mathagents.snapshot`

Stage 8 kernel snapshot (spec DD-19, DD-43): freeze a dossier's declarations at one checked state.

`snapshot_kernel` copies the provenance and the namespace's declarations from the fresh G-KERNEL
report into `reports/dossiers/<slug>/kernel-snapshot.json`. It refuses a report from a dirty
`lean/` tree, a stale report, and a dossier without a fidelity record.

**CLI surface:** `scripts/snapshot_kernel.py`

## Public Surface

### class `KernelSnapshot`

*frozen dataclass*

`kernel-snapshot.json`: the provenance of the report it was taken from, and its declarations.

| Field | Type |
|---|---|
| `lean_namespace` | `str` |
| `commit` | `str` |
| `dirty` | `bool` |
| `checked_at` | `str` |
| `source_sha256` | `str` |
| `lean_version` | `str` |
| `declarations` | `tuple[Declaration, ...]` |

### class `SnapshotResult`

*dataclass*

Outcome of `snapshot_kernel`; a refusal is `success` False with the reason in `errors`.

| Field | Type |
|---|---|
| `success` | `bool` |
| `slug` | `str` |
| `path` | `Path` |
| `dry_run` | `bool` |
| `commit` | `str \| None` |
| `declaration_count` | `int` |
| `errors` | `list[str]` |
| `notices` | `list[str]` |

### `read_kernel_snapshot(*, root=None, slug)`

Returns `KernelSnapshot | None`.

The dossier's kernel snapshot, or None when it has none. Its consistency with the fidelity record
and the kernel report is the dossier validator's check, not this reader's.

**Raises:**

- `RecordError`: the snapshot is not a JSON object with `lean_namespace`, `commit` and `declarations`.

### `snapshot_kernel(*, root=None, slug, dry_run=False)`

Returns `SnapshotResult`.

Write the dossier's kernel snapshot (Stage 8 assembly).

**Args:**

- `root`: mathAgents checkout or instance.
- `slug`: the dossier.
- `dry_run`: run every check, write nothing.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.
- `PermissionError`: a real write into a tree that is neither the package's own checkout nor a declared instance (`mathagents.toml`, D35); like `snapshot_kernel.py --root`, that is for the test suite only (`MATHAGENTS_TEST=1`).
