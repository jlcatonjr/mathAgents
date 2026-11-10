# `mathagents.registries`

The object-logic and prover-engine registries (`references/object-logics.json`,
`references/prover-engines.json`) and their validator.

**CLI surface:** `scripts/validate_registries.py`

## Public Surface

### class `Registry`

*frozen dataclass*

A registry: its default id and its entries (each keeps the registry schema's fields).

| Field | Type |
|---|---|
| `default` | `str` |
| `entries` | `tuple[Mapping, ...]` |

### `load_object_logics(*, root=None)`

Returns `Registry`.

`references/object-logics.json` (unvalidated; run `validate_registries` for the checks).

### `load_prover_engines(*, root=None)`

Returns `Registry`.

`references/prover-engines.json` (unvalidated; run `validate_registries` for the checks).

### `validate_registries(*, root=None)`

Returns `CommandResult`.

Validate both registries against their schemas and source rules (`validate_registries.py`).
