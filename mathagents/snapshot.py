"""Stage 8 kernel snapshot (spec DD-19, DD-43): freeze a dossier's declarations at one checked state.

``snapshot_kernel`` copies the provenance and the namespace's declarations from the fresh G-KERNEL
report into ``reports/dossiers/<slug>/kernel-snapshot.json``. It refuses a report from a dirty
``lean/`` tree, a stale report, and a dossier without a fidelity record.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from mathagents import _scripts
from mathagents.errors import RecordError
from mathagents.kernel import Declaration

__all__ = ["KernelSnapshot", "SnapshotResult", "read_kernel_snapshot", "snapshot_kernel"]


@dataclass(frozen=True)
class KernelSnapshot:
    """``kernel-snapshot.json``: the provenance of the report it was taken from, and its declarations."""

    lean_namespace: str
    commit: str
    dirty: bool
    checked_at: str
    source_sha256: str
    lean_version: str
    declarations: tuple[Declaration, ...]


@dataclass
class SnapshotResult:
    """Outcome of ``snapshot_kernel``; a refusal is ``success`` False with the reason in ``errors``."""

    success: bool
    slug: str
    path: Path
    dry_run: bool
    commit: str | None = None
    declaration_count: int = 0
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


def snapshot_kernel(*, root: Path | None = None, slug: str, dry_run: bool = False) -> SnapshotResult:
    """Write the dossier's kernel snapshot (Stage 8 assembly).

    Args:
        root: mathAgents checkout or instance.
        slug: the dossier.
        dry_run: run every check, write nothing.

    Raises:
        ValueError: invalid slug.
        FileNotFoundError: no such dossier.
        PermissionError: a real write into a tree that is neither the package's own checkout nor a
            declared instance (``mathagents.toml``, D35); that is for the test suite only (``MATHAGENTS_TEST=1``).
    """
    r = _scripts.resolve_root(root)
    if not dry_run and r != _scripts.CHECKOUT and not (r / _scripts.INSTANCE_MARKER).is_file() \
            and os.environ.get("MATHAGENTS_TEST") != "1":
        raise PermissionError("snapshot_kernel writes only into the package's own checkout or a declared instance "
                              "(mathagents.toml, D35); another tree is for the test suite: MATHAGENTS_TEST=1")
    d = _scripts.dossier_dir(r, slug)
    snap, msg = _scripts.gate("snapshot_kernel").snapshot(r, slug, write=not dry_run)
    path = d / "kernel-snapshot.json"
    if snap is None:
        return SnapshotResult(success=False, slug=slug, path=path, dry_run=dry_run, errors=[msg])
    return SnapshotResult(success=True, slug=slug, path=path, dry_run=dry_run, commit=snap.get("commit"),
                          declaration_count=len(snap["declarations"]),
                          notices=[msg[0].upper() + msg[1:]] if dry_run else [])


def read_kernel_snapshot(*, root: Path | None = None, slug: str) -> KernelSnapshot | None:
    """The dossier's kernel snapshot, or None when it has none. Its consistency with the fidelity record
    and the kernel report is the dossier validator's check, not this reader's.

    Raises:
        RecordError: the snapshot is not a JSON object with ``lean_namespace``, ``commit`` and ``declarations``.
    """
    p = _scripts.dossier_dir(_scripts.resolve_root(root), slug) / "kernel-snapshot.json"
    if not p.exists():
        return None
    try:
        s = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(s, dict) or not all(k in s for k in ("lean_namespace", "commit", "declarations")):
            raise ValueError("missing lean_namespace, commit or declarations")
        decls = tuple(Declaration.from_report(x) for x in s["declarations"])
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise RecordError(f"{slug}: kernel-snapshot.json invalid: {exc}") from exc
    return KernelSnapshot(lean_namespace=s.get("lean_namespace", ""), commit=s.get("commit", ""), dirty=bool(s.get("dirty")),
                          checked_at=s.get("checked_at", ""), source_sha256=s.get("source_sha256", ""),
                          lean_version=s.get("lean_version", ""),
                          declarations=decls)
