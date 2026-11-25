# `mathagents.registries`

The object-logic and prover-engine registries (`references/object-logics.json`,
`references/prover-engines.json`) and their validator.

Decision IDs, gate codes and terms are defined in the [glossary](index.md#glossary).

**CLI surface:** `scripts/validate_registries.py`

## Public Surface

### class `Registry`

*frozen dataclass*

A registry: its default id and its entries (each keeps the registry schema's fields).

**Methods and properties:**

- `get(entry_id) -> Mapping | None`: the entry whose `id` is `entry_id`, or None.
- `ids -> tuple[str, ...]`: every entry's `id`, in file order.

| Field | Type |
|---|---|
| `default` | `str` |
| `entries` | `tuple[Mapping, ...]` |

### `load_object_logics(*, root=None)`

Returns `Registry`.

`references/object-logics.json` (unvalidated; run `validate_registries` for the checks).

**Raises:**

- `FileNotFoundError`: no such file.
- `json.JSONDecodeError`: the file is not valid JSON.
- `KeyError`: the file lacks its default id or its entry list.

### `load_prover_engines(*, root=None)`

Returns `Registry`.

`references/prover-engines.json` (unvalidated; run `validate_registries` for the checks).

**Raises:**

- `FileNotFoundError`: no such file.
- `json.JSONDecodeError`: the file is not valid JSON.
- `KeyError`: the file lacks its default id or its entry list.

### `validate_registries(*, root=None)`

Returns `CommandResult`.

Validate both registries against their schemas and source rules (`validate_registries.py`).
