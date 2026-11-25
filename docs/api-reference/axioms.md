# `mathagents.axioms`

[G-AX](index.md#glossary): the axiom envelope and statement-change records (spec DD-36, DD-37, DD-38).

Read-only by design: approving an axiom or a statement change is a human decision, recorded by the
operator in `references/axiom-allowlist.json` or `reports/dossiers/<slug>/gax.json` (see
[the human-decision boundary](index.md#the-human-decision-boundary-dd-29)).

**CLI surface:** `references/axiom-allowlist.json` (operator-edited)

## Public Surface

### class `AxiomEnvelope`

*frozen dataclass*

The axioms G-KERNEL accepts: `base` (Lean's standard axioms named in the allowlist) and
`approved` (human G-AX approvals). Any `problems` make the envelope unusable.

**Properties:**

- `allowed -> frozenset[str]`: `base | approved`, the axioms a declaration may use.
- `usable -> bool`: True when there are no `problems`.

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

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `namespace`: restrict to declarations under this namespace.

**Raises:**

- `FileNotFoundError`: no kernel report.
- `KernelReportError`: the kernel report is not usable.

### `load_axiom_envelope(*, root=None)`

Returns `AxiomEnvelope`.

Load `references/axiom-allowlist.json` through the same loader G-KERNEL uses. Problems with the
allowlist's content (no base axioms, a widened base, an approval without a complete record) are reported
in `problems`; a file that cannot be read or parsed raises.

**Raises:**

- `FileNotFoundError`: no allowlist.
- `json.JSONDecodeError`: the allowlist is not valid JSON.

### `read_gax_record(*, root=None, slug)`

Returns `GaxRecord | None`.

The dossier's G-AX record, or None when it has none.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.
- `RecordError`: the record is malformed, fails its schema, or names another slug.
