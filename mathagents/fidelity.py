"""G-FID: read statement-fidelity approvals and check their coverage (spec DD-26, DD-29, DD-35).

Read-only by design. Approvals are human decisions (DD-29): the operator records them with
``scripts/operator/record_gfid_approval.py`` in a terminal, and this API offers no way to write one.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mathagents import _scripts
from mathagents.results import GateResult

__all__ = ["FidelityCoverage", "FidelityEntry", "FidelityRecord", "fidelity_coverage", "read_fidelity_record",
           "require_fidelity"]


@dataclass(frozen=True)
class FidelityEntry:
    """One G-FID decision: ``status`` is ``approved`` (human) or ``waived`` (kernel-as-judge, one conversation)."""

    decl: str
    statement_fingerprint: str
    status: str
    approver: str | None = None
    date: str | None = None
    reading: str | None = None
    waiver_conversation: str | None = None


@dataclass(frozen=True)
class FidelityRecord:
    """``reports/dossiers/<slug>/fidelity.json``, schema-validated."""

    slug: str
    lean_namespace: str
    intake_sha256: str | None
    entries: tuple[FidelityEntry, ...]


@dataclass(frozen=True)
class FidelityCoverage:
    """A description of how the record covers the namespace's claims in the fresh kernel report.

    ``current``: approved and fingerprint unchanged; ``lapsed``: the statement changed since approval
    (or left the namespace); ``waived``: kernel-as-judge waivers; ``uncovered``: claims with no entry;
    ``intake_current``: the record's intake_sha256 matches the current problem card and preferences.

    This is a summary for planning, not the gate: the G-FID decision (waiver scope, approver fields,
    helper dependencies and everything else the validator checks) is ``require_fidelity``.
    """

    slug: str
    current: tuple[str, ...]
    lapsed: tuple[str, ...]
    waived: tuple[str, ...]
    uncovered: tuple[str, ...]
    intake_current: bool


def read_fidelity_record(*, root: Path | None = None, slug: str) -> FidelityRecord | None:
    """The dossier's fidelity record, or None when it has none.

    Raises:
        ValueError: invalid slug.
        FileNotFoundError: no such dossier.
        RecordError: the record is malformed, fails its schema, or names another slug.
    """
    data = _scripts.read_record(_scripts.resolve_root(root), slug, "fidelity.json")
    if data is None:
        return None
    return FidelityRecord(
        slug=data["slug"], lean_namespace=data["lean_namespace"], intake_sha256=data.get("intake_sha256"),
        entries=tuple(FidelityEntry(decl=e["decl"], statement_fingerprint=e["statement_fingerprint"], status=e["status"],
                                    approver=e.get("approver"), date=e.get("date"), reading=e.get("reading"),
                                    waiver_conversation=(e.get("waiver") or {}).get("conversation"))
                      for e in data["declarations"]))


def fidelity_coverage(*, root: Path | None = None, slug: str) -> FidelityCoverage:
    """Compare the fidelity record with the fresh kernel report (claims only; ``Aux``/``CX`` exempt).

    Raises:
        FileNotFoundError: no such dossier, or it has no fidelity record.
        KernelReportError: the kernel report is not usable.
        RecordError: the record is invalid.
    """
    from mathagents.kernel import declarations_in_namespace

    r = _scripts.resolve_root(root)
    rec = read_fidelity_record(root=r, slug=slug)
    if rec is None:
        raise FileNotFoundError(f"{slug} has no fidelity record")
    claims = {d.name: d for d in declarations_in_namespace(root=r, namespace=rec.lean_namespace, include_helpers=False)}
    by = {e.decl: e for e in rec.entries}
    current = tuple(n for n, e in sorted(by.items()) if e.status == "approved" and n in claims
                    and claims[n].statement_fingerprint == e.statement_fingerprint)
    lapsed = tuple(n for n, e in sorted(by.items()) if n not in claims or claims[n].statement_fingerprint != e.statement_fingerprint)
    waived = tuple(n for n, e in sorted(by.items()) if e.status == "waived")
    digest = _scripts.gate("dossier_structure").intake_digest(_scripts.dossier_dir(r, slug))
    return FidelityCoverage(slug=slug, current=current, lapsed=lapsed, waived=waived,
                            uncovered=tuple(sorted(set(claims) - set(by))), intake_current=rec.intake_sha256 == digest)


def require_fidelity(*, root: Path | None = None, slug: str, conversation: str | None = None) -> GateResult:
    """The G-FID gate for ``slug`` (the precondition for dispatching Stage 2), via the dossier validator.

    Raises:
        ValueError: invalid slug.
    """
    from mathagents.dossiers import validate_dossiers

    return validate_dossiers(root=root, require_fid=[slug], conversation=conversation)
