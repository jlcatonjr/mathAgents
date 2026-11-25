# `mathagents.evidence`

The evidence layer (`references/phase1-evidence/`) and claim ledgers: fail-closed source grounding of
the project reports.

Decision IDs, gate codes and terms are defined in the [glossary](index.md#glossary).

**CLI surface:** `scripts/validate_evidence.py`, `scripts/validate_claim_ledger.py`

## Public Surface

### `validate_claim_ledger(*, root=None, deliverable)`

Returns `CommandResult`.

Check a report against its claim ledger `reports/<name>.claims.csv` (`validate_claim_ledger.py`).

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `deliverable`: a `Path` (not a `str`) to the report, relative to `root` (e.g.
  `Path("reports/01-methods-review.md")`); an absolute path inside `root` is accepted too.

**Raises:**

- `FileNotFoundError`: the deliverable does not exist.
- `ValueError`: the deliverable is outside `root`.

### `validate_evidence(*, root=None)`

Returns `CommandResult`.

Check `references/phase1-evidence/*.jsonl` against the source inventory (`validate_evidence.py`).
