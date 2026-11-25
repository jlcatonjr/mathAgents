# `mathagents.fidelity`

[G-FID](index.md#glossary): read statement-fidelity approvals and check their coverage (spec DD-26, DD-29,
DD-35).

Read-only by design: the operator records approvals with `scripts/operator/record_gfid_approval.py` in a
terminal, and this API offers no way to write one (see
[the human-decision boundary](index.md#the-human-decision-boundary-dd-29)).

**CLI surface:** `scripts/validate_dossier.py --require-fid`; operator: `scripts/operator/record_gfid_approval.py`

## Public Surface

### class `FidelityCoverage`

*frozen dataclass*

How the record covers the namespace's claims in the fresh kernel report.

`current`: approved and fingerprint unchanged; `lapsed`: the statement changed since approval
(or left the namespace); `waived`: [kernel-as-judge](index.md#glossary) waivers; `uncovered`: claims
with no entry; `intake_current`: the record's intake_sha256 matches the current problem card and
preferences.

Only claims count, so an entry for an `Aux` helper or a `CX` witness declaration is counted as
`lapsed` (it is not among the claims).

This is a summary for planning, not the gate: the G-FID decision (waiver scope, approver fields,
helper dependencies and everything else the validator checks) is `require_fidelity`.

| Field | Type |
|---|---|
| `slug` | `str` |
| `current` | `tuple[str, ...]` |
| `lapsed` | `tuple[str, ...]` |
| `waived` | `tuple[str, ...]` |
| `uncovered` | `tuple[str, ...]` |
| `intake_current` | `bool` |

### class `FidelityEntry`

*frozen dataclass*

One G-FID decision: `status` is `approved` (human) or `waived` (kernel-as-judge, one conversation).

| Field | Type |
|---|---|
| `decl` | `str` |
| `statement_fingerprint` | `str` |
| `status` | `str` |
| `approver` | `str \| None` |
| `date` | `str \| None` |
| `reading` | `str \| None` |
| `waiver_conversation` | `str \| None` |

### class `FidelityRecord`

*frozen dataclass*

`reports/dossiers/<slug>/fidelity.json`, schema-validated.

| Field | Type |
|---|---|
| `slug` | `str` |
| `lean_namespace` | `str` |
| `intake_sha256` | `str \| None` |
| `entries` | `tuple[FidelityEntry, ...]` |

### `fidelity_coverage(*, root=None, slug)`

Returns `FidelityCoverage`.

Compare the fidelity record with the fresh kernel report (claims only; `Aux`/`CX` exempt).

**Raises:**

- `FileNotFoundError`: no such dossier, no fidelity record, or no kernel report.
- `KernelReportError`: the kernel report is not usable.
- `RecordError`: the record is invalid.

### `read_fidelity_record(*, root=None, slug)`

Returns `FidelityRecord | None`.

The dossier's fidelity record, or None when it has none.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.
- `RecordError`: the record is malformed, fails its schema, or names another slug.

### `require_fidelity(*, root=None, slug, conversation=None)`

Returns `GateResult`.

The G-FID gate for `slug` (the precondition for dispatching Stage 2), via the dossier validator. It is
[`validate_dossiers`](dossiers.md) with `require_fid=[slug]`, so its `notices` carry the validator's
pin-stamp warnings.

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `slug`: the dossier.
- `conversation`: current conversation id, the scope of kernel-as-judge waivers.

**Raises:**

- `ValueError`: invalid slug.
- `RuntimeError`: git itself failed (fail-closed).
