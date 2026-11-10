"""G-AX: the axiom envelope and statement-change records (spec DD-36, DD-37, DD-38).

Read-only by design: approving an axiom or a statement change is a human decision (DD-29), recorded by
the operator in ``references/axiom-allowlist.json`` or ``reports/dossiers/<slug>/gax.json``.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from mathagents import _scripts

__all__ = ["AxiomEnvelope", "GaxRecord", "axiom_usage", "load_axiom_envelope", "read_gax_record"]


@dataclass(frozen=True)
class AxiomEnvelope:
    """The axioms G-KERNEL accepts: ``base`` (Lean's standard axioms named in the allowlist) and
    ``approved`` (human G-AX approvals). Any ``problems`` make the envelope unusable."""

    base: frozenset[str]
    approved: frozenset[str]
    problems: tuple[str, ...]

    @property
    def allowed(self) -> frozenset[str]:
        return self.base | self.approved

    @property
    def usable(self) -> bool:
        return not self.problems


@dataclass(frozen=True)
class GaxRecord:
    """``reports/dossiers/<slug>/gax.json``, schema-validated; ``records`` keep the schema's fields."""

    slug: str
    records: tuple[Mapping, ...]


def load_axiom_envelope(*, root: Path | None = None) -> AxiomEnvelope:
    """Load ``references/axiom-allowlist.json`` through the same loader G-KERNEL uses."""
    r = _scripts.resolve_root(root)
    base, approved, problems = _scripts.gate("axiom_allowlist").load(r / "references" / "axiom-allowlist.json")
    return AxiomEnvelope(base=frozenset(base), approved=frozenset(approved), problems=tuple(problems))


def read_gax_record(*, root: Path | None = None, slug: str) -> GaxRecord | None:
    """The dossier's G-AX record, or None when it has none.

    Raises:
        ValueError: invalid slug.
        FileNotFoundError: no such dossier.
        RecordError: the record is malformed, fails its schema, or names another slug.
    """
    data = _scripts.read_record(_scripts.resolve_root(root), slug, "gax.json")
    if data is None:
        return None
    return GaxRecord(slug=data["slug"], records=tuple(MappingProxyType(dict(x)) for x in data["records"]))


def axiom_usage(*, root: Path | None = None, namespace: str | None = None) -> dict[str, list[str]]:
    """``{axiom: [declarations that depend on it]}`` from the fresh kernel report.

    Args:
        root: mathAgents checkout.
        namespace: restrict to declarations under this namespace.

    Raises:
        KernelReportError: the kernel report is not usable.
    """
    from mathagents.kernel import load_kernel_report

    prefix = None if namespace is None else namespace.rstrip(".") + "."
    out: dict[str, list[str]] = {}
    for name, d in sorted(load_kernel_report(root=root).declarations.items()):
        if prefix is None or name.startswith(prefix):
            for ax in d.axioms:
                out.setdefault(ax, []).append(name)
    return out
