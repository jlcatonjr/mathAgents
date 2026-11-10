# `mathagents.evidence`

The Phase 1 evidence layer and claim ledgers (fail-closed source grounding of the project reports).

**CLI surface:** `scripts/validate_evidence.py, scripts/validate_claim_ledger.py`

## Public Surface

### `validate_claim_ledger(*, root=None, deliverable)`

Returns `CommandResult`.

Check a report against its claim ledger `reports/<name>.claims.csv` (`validate_claim_ledger.py`).

**Args:**

- `root`: mathAgents checkout.
- `deliverable`: the report, relative to `root` (e.g. `reports/01-methods-review.md`).

**Raises:**

- `FileNotFoundError`: the deliverable does not exist.
- `ValueError`: the deliverable is outside `root`.

### `validate_evidence(*, root=None)`

Returns `CommandResult`.

Check `references/phase1-evidence/*.jsonl` against the source inventory (`validate_evidence.py`).
