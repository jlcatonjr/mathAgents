# `mathagents.counterexamples`

G-CX: the counterexample log (spec DD-15, DD-16, DD-39, DD-59).

`log_counterexample` and `record_lean_witness` call the sanctioned writer
(`scripts/log_counterexample.py`): the statement fingerprint always comes from the fresh kernel
report, never from the caller. Neither writes, changes or removes a verdict; verdicts are human
decisions (DD-29) and this API offers no way to record one.

**CLI surface:** `scripts/log_counterexample.py`

## Public Surface

### `METHODS`

Constant: `('decide', 'small-model', 'smt', 'atp', 'manual')`

### class `CounterexampleLog`

*frozen dataclass*

`reports/dossiers/<slug>/counterexamples.json`, schema-validated; entries keep the schema's fields.

| Field | Type |
|---|---|
| `slug` | `str` |
| `lean_namespace` | `str` |
| `entries` | `tuple[Mapping, ...]` |

### class `LogResult`

*dataclass*

Outcome of a log write; a refusal is `success` False with the reason in `errors`.

| Field | Type |
|---|---|
| `success` | `bool` |
| `slug` | `str` |
| `dry_run` | `bool` |
| `message` | `str` |
| `errors` | `list[str]` |
| `notices` | `list[str]` |

### `log_counterexample(*, root=None, slug, decl, method, description, engine=None, namespace=None, dry_run=False)`

Returns `LogResult`.

Append a counterexample candidate against `decl` with the next `CX-n` id.

**Args:**

- `root`: mathAgents checkout.
- `slug`: the dossier.
- `decl`: fully-qualified target declaration (must be in the fresh kernel report).
- `method`: one of `METHODS`.
- `description`: what the candidate is and how it was found.
- `engine`: engine id from `references/prover-engines.json`, if one was used.
- `namespace`: lean_namespace for a new log when the dossier has no fidelity record yet.
- `dry_run`: run every check, write nothing.

**Raises:**

- `ValueError`: invalid slug or method.

### `read_counterexample_log(*, root=None, slug)`

Returns `CounterexampleLog | None`.

The dossier's counterexample log, or None when it has none.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.
- `RecordError`: the log is malformed, fails its schema, or names another slug.

### `record_lean_witness(*, root=None, slug, cx_id, witness_decl, dry_run=False)`

Returns `LogResult`.

Record `lean_witness` on an entry once the witness `¬ (type_of% @target)` is kernel-proved.

**Raises:**

- `ValueError`: invalid slug.
