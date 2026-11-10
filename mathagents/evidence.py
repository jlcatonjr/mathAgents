"""The Phase 1 evidence layer and claim ledgers (fail-closed source grounding of the project reports)."""
from __future__ import annotations

from pathlib import Path

from mathagents import _scripts
from mathagents.results import CommandResult

__all__ = ["validate_claim_ledger", "validate_evidence"]


def validate_evidence(*, root: Path | None = None) -> CommandResult:
    """Check ``references/phase1-evidence/*.jsonl`` against the source inventory (``validate_evidence.py``)."""
    return _scripts.run_script(_scripts.resolve_root(root), "validate_evidence.py")


def validate_claim_ledger(*, root: Path | None = None, deliverable: Path) -> CommandResult:
    """Check a report against its claim ledger ``reports/<name>.claims.csv`` (``validate_claim_ledger.py``).

    Args:
        root: mathAgents checkout.
        deliverable: the report, relative to ``root`` (e.g. ``reports/01-methods-review.md``).

    Raises:
        FileNotFoundError: the deliverable does not exist.
        ValueError: the deliverable is outside ``root``.
    """
    r = _scripts.resolve_root(root)
    p = deliverable if deliverable.is_absolute() else r / deliverable
    p = p.resolve()
    if not p.is_relative_to(r):
        raise ValueError(f"{deliverable} is outside the checkout")
    if not p.is_file():
        raise FileNotFoundError(f"no deliverable at {deliverable}")
    return _scripts.run_script(r, "validate_claim_ledger.py", str(p.relative_to(r)))
