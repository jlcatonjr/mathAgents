"""Exception hierarchy for errors the mathagents API raises.

Caller mistakes raise built-in exceptions (``ValueError`` for an invalid slug, ``FileNotFoundError``
for a missing dossier or checkout). Domain errors derive from ``MathAgentsError``; each also inherits
the built-in a caller would otherwise catch, so ``except RuntimeError`` keeps working.
"""
from __future__ import annotations

__all__ = ["KernelReportError", "MathAgentsError", "NameIndexError", "RecordError"]


class MathAgentsError(Exception):
    """Base class for all mathagents-raised errors."""


class KernelReportError(MathAgentsError, RuntimeError):
    """The G-KERNEL report is missing, failing, stale, or otherwise unusable (fail-closed)."""


class NameIndexError(MathAgentsError, RuntimeError):
    """The pinned-Mathlib name index is missing, stale, or malformed."""


class RecordError(MathAgentsError, ValueError):
    """A dossier record (fidelity.json, gax.json, counterexamples.json, kernel-snapshot.json) is malformed,
    fails its schema, or names another dossier's slug."""
