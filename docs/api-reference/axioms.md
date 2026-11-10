# `mathagents.axioms`

G-AX: the axiom envelope and statement-change records (spec DD-36, DD-37, DD-38).

Read-only by design: approving an axiom or a statement change is a human decision (DD-29), recorded by
the operator in `references/axiom-allowlist.json` or `reports/dossiers/<slug>/gax.json`.

**CLI surface:** `references/axiom-allowlist.json (operator-edited)`

## Public Surface

### class `AxiomEnvelope`

*frozen dataclass*

The axioms G-KERNEL accepts: `base` (Lean's standard axioms named in the allowlist) and
`approved` (human G-AX approvals). Any `problems` make the envelope unusable.

| Field | Type |
|---|---|
| `base` | `frozenset[str]` |
| `approved` | `frozenset[str]` |
| `problems` | `tuple[str, ...]` |

### class `GaxRecord`

*frozen dataclass*

`reports/dossiers/<slug>/gax.json`, schema-validated; `records` keep the schema's fields.

| Field | Type |
|---|---|
| `slug` | `str` |
| `records` | `tuple[Mapping, ...]` |

### `axiom_usage(*, root=None, namespace=None)`

Returns `dict[str, list[str]]`.

`{axiom: [declarations that depend on it]}` from the fresh kernel report.

**Args:**

- `root`: mathAgents checkout.
- `namespace`: restrict to declarations under this namespace.

**Raises:**

- `KernelReportError`: the kernel report is not usable.

### `load_axiom_envelope(*, root=None)`

Returns `AxiomEnvelope`.

Load `references/axiom-allowlist.json` through the same loader G-KERNEL uses.

### `read_gax_record(*, root=None, slug)`

Returns `GaxRecord | None`.

The dossier's G-AX record, or None when it has none.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.
- `RecordError`: the record is malformed, fails its schema, or names another slug.
