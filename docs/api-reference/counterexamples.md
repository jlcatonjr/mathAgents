# `mathagents.counterexamples`

[G-CX](index.md#glossary): the counterexample log (spec DD-15, DD-16, DD-39, DD-59).

`log_counterexample` and `record_lean_witness` call the sanctioned writer
(`scripts/log_counterexample.py`): the statement fingerprint always comes from the fresh kernel
report, never from the caller. Neither writes, changes or removes a verdict, and this API offers no way
to record one (see [the human-decision boundary](index.md#the-human-decision-boundary-dd-29)).

Both writers refuse (`success` False, the reason in `errors`) rather than raise when the dossier does not
exist or the kernel report is not fresh. A log or entry that fails the counterexample-log schema raises
`jsonschema.ValidationError`.

**CLI surface:** `scripts/log_counterexample.py`

## Public Surface

### `METHODS`

Constant: `('decide', 'small-model', 'smt', 'atp', 'manual')`

### class `CounterexampleLog`

*frozen dataclass*

`reports/dossiers/<slug>/counterexamples.json`, schema-validated; entries keep the schema's fields.

**Methods:**

- `entry(cx_id) -> Mapping | None`: the entry with id `cx_id` (such as `CX-1`), or None when the log has
  none.

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

The writer also records `statement_fingerprint` (from the fresh kernel report), `logged_by`
(`counterexample-hunter`), `logged_date` (today, UTC), and the instance's `toolchain_pin` and
`mathlib_rev` when the Lean pin gives them. A new log takes its `lean_namespace` from the dossier's
fidelity record, else from `namespace`.

Refusals (`success` False): the dossier does not exist; the kernel report is not fresh; `decl` is not in
it; no namespace is available for a new log.

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `slug`: the dossier.
- `decl`: fully-qualified target declaration (must be in the fresh kernel report).
- `method`: one of `METHODS`.
- `description`: what the candidate is and how it was found.
- `engine`: engine id from `references/prover-engines.json`, if one was used.
- `namespace`: lean_namespace for a new log when the dossier has no fidelity record yet.
- `dry_run`: run every check, write nothing.

**Raises:**

- `ValueError`: invalid slug or method.
- `jsonschema.ValidationError`: the existing log, or the log with the new entry, fails its schema.

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

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `slug`: the dossier.
- `cx_id`: the log entry, such as `CX-1`.
- `witness_decl`: the fully-qualified witness declaration, written as
  `theorem cx_<n> : ¬ (type_of% @<target>)` in the dossier's `CX` namespace.
- `dry_run`: run every check, write nothing.

Refusals (`success` False): the dossier does not exist; the kernel report is not fresh; there is no log;
`cx_id` is not in it; the entry already records a witness; `witness_decl` is not `proved` in the kernel
report; the witness's `negates_fingerprint` does not match the entry's `statement_fingerprint`.

**Raises:**

- `ValueError`: invalid slug.
- `jsonschema.ValidationError`: the log fails its schema.
