# `mathagents.dossiers`

Dossiers and the eight-stage pipeline: status, stage preconditions, validation, result labels.

A dossier is `reports/dossiers/<slug>/`. `validate_dossiers` runs the dossier validator
(structure, G-FID, G-AX, G-CX) exactly as `scripts/validate_dossier.py` does; `require_stage` is
the precondition for dispatching stage N (spec DD-43), which at N = 8 also runs G-NAME and, when a
blueprint exists, G-BLUEPRINT.

**CLI surface:** `scripts/validate_dossier.py`

## Public Surface

### `STAGES`

Constant tuple of 9 entries.

### class `DossierStatus`

*frozen dataclass*

What a dossier holds. `stages_with_artifacts` lists the stages whose artifacts all exist;
whether a stage may be dispatched is decided by `require_stage`, never by this summary.

| Field | Type |
|---|---|
| `slug` | `str` |
| `path` | `Path` |
| `artifacts` | `tuple[str, ...]` |
| `stages_with_artifacts` | `tuple[int, ...]` |
| `lean_namespace` | `str \| None` |
| `result_labels` | `tuple[ResultLabel, ...]` |
| `has_fidelity_record` | `bool` |
| `has_counterexample_log` | `bool` |
| `has_gax_record` | `bool` |
| `has_kernel_snapshot` | `bool` |

### class `ResultLabel`

*frozen dataclass*

A result label found in a dossier file (`Result status: proved` and the like).

| Field | Type |
|---|---|
| `file` | `str` |
| `value` | `str` |

### class `Stage`

*frozen dataclass*

One pipeline stage: the agents that run it and the dossier artifacts it produces.

| Field | Type |
|---|---|
| `number` | `int` |
| `name` | `str` |
| `agents` | `tuple[str, ...]` |
| `artifacts` | `tuple[str, ...]` |

### `dossier_status(*, root=None, slug)`

Returns `DossierStatus`.

Summarize a dossier's artifacts and labels (no gate is run).

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.

### `list_dossiers(*, root=None)`

Returns `list[str]`.

Slugs of every dossier directory, sorted.

### `require_stage(*, root=None, slug, stage, conversation=None, base=None)`

Returns `GateResult`.

Precondition for dispatching `stage` on `slug` (spec DD-43).

**Raises:**

- `ValueError`: invalid slug or stage.

### `result_labels(*, root=None, slug)`

Returns `list[ResultLabel]`.

Every result label in the dossier's text files (records excluded), as the validator sees them.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.

### `validate_dossiers(*, root=None, slugs=(), require_fid=(), require_stages=None, kernel_report=None, conversation=None, base=None)`

Returns `GateResult`.

Run the dossier validator (structure, G-FID, G-AX, G-CX); fail-closed.

**Args:**

- `root`: mathAgents checkout.
- `slugs`: dossiers to check; none named (and no requirements) checks every dossier.
- `require_fid`: dossiers that must hold a current G-FID approval for every claim (Stage 2 gate).
- `require_stages`: `{slug: N}` preconditions for dispatching stage N (N >= 2 implies require_fid).
- `kernel_report`: report path (default `reports/kernel/latest.json`).
- `conversation`: current conversation id, the scope of kernel-as-judge waivers.
- `base`: git ref for the append-only checks (default: merge base of HEAD with origin/HEAD).

**Raises:**

- `ValueError`: an invalid slug or stage number.
- `TypeError`: a single string passed where a list of slugs is expected.
