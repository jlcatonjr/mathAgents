# `mathagents.fidelity`

G-FID: read statement-fidelity approvals and check their coverage (spec DD-26, DD-29, DD-35).

Read-only by design. Approvals are human decisions (DD-29): the operator records them with
`scripts/operator/record_gfid_approval.py` in a terminal, and this API offers no way to write one.

**CLI surface:** `scripts/validate_dossier.py --require-fid; operator: scripts/operator/record_gfid_approval.py`

## Public Surface

### class `FidelityCoverage`

*frozen dataclass*

A description of how the record covers the namespace's claims in the fresh kernel report.

`current`: approved and fingerprint unchanged; `lapsed`: the statement changed since approval
(or left the namespace); `waived`: kernel-as-judge waivers; `uncovered`: claims with no entry;
`intake_current`: the record's intake_sha256 matches the current problem card and preferences.

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

- `FileNotFoundError`: no such dossier, or it has no fidelity record.
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

The G-FID gate for `slug` (the precondition for dispatching Stage 2), via the dossier validator.

**Raises:**

- `ValueError`: invalid slug.
