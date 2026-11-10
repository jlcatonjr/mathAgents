"""The pinned-Mathlib name index behind G-NAME and G-BLUEPRINT (spec DD-17).

``reports/kernel/name-index.txt`` (gitignored, machine-local) lists every declaration name in the
pinned Mathlib. A Lean name in prose resolves if it is in the fresh kernel report (project library)
or in this index; nothing is resolved by naming convention.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mathagents import _scripts
from mathagents.errors import KernelReportError, NameIndexError
from mathagents.results import CommandResult

__all__ = ["NameResolution", "build_name_index", "load_name_index", "resolve_lean_name"]

DEFAULT_INDEX = Path("reports") / "kernel" / "name-index.txt"


@dataclass(frozen=True)
class NameResolution:
    """Where a Lean name resolved: ``source`` is ``kernel``, ``mathlib`` or None (unresolved)."""

    name: str
    source: str | None
    status: str | None = None  # kernel status when source == "kernel"

    @property
    def resolved(self) -> bool:
        return self.source is not None


def build_name_index(*, root: Path | None = None, timeout: float | None = None) -> CommandResult:
    """(Re)build the name index for the pinned toolchain (``scripts/build_name_index.py``). Slow.

    Args:
        root: mathAgents checkout.
        timeout: seconds before the subprocess is killed (default: none).
    """
    return _scripts.run_script(_scripts.resolve_root(root), "build_name_index.py", timeout=timeout)


def load_name_index(*, root: Path | None = None) -> frozenset[str]:
    """The names in the index.

    Raises:
        NameIndexError: the index is missing, stale for the pinned toolchain, or malformed.
    """
    r = _scripts.resolve_root(root)
    index, problem = _scripts.gate("build_name_index").load_index(r / DEFAULT_INDEX, r / "lean")
    if index is None:
        raise NameIndexError(str(problem))
    return frozenset(index)


def resolve_lean_name(*, root: Path | None = None, name: str) -> NameResolution:
    """Resolve a fully-qualified Lean name against the fresh kernel report, then the name index.

    Raises:
        KernelReportError: the kernel report is not usable.
        NameIndexError: the name is not a project declaration and the index is not usable.
    """
    from mathagents.kernel import load_kernel_report

    r = _scripts.resolve_root(root)
    try:
        rep = load_kernel_report(root=r)
    except FileNotFoundError as exc:
        raise KernelReportError(str(exc)) from exc
    if name in rep.declarations:
        return NameResolution(name=name, source="kernel", status=rep.declarations[name].status)
    return NameResolution(name=name, source="mathlib" if name in load_name_index(root=r) else None)
