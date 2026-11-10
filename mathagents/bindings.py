"""G-NAME: ``[Lean: name | status]`` bindings in dossier prose (spec DD-17, DD-18).

Every binding must resolve against the fresh kernel report or the pinned-Mathlib name index, and its
status tag must match the kernel. ``check_lean_bindings`` runs ``scripts/check_lean_bindings.py``'s
logic in-process.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from mathagents import _scripts
from mathagents.results import GateResult

__all__ = ["BindingScan", "LeanBinding", "check_lean_bindings", "list_lean_bindings"]


@dataclass(frozen=True)
class LeanBinding:
    """One binding. ``kind`` is ``narration`` (``[Lean: X | status]``), ``node`` (a derivation or
    tactic-plan node's ``Lean:`` name) or ``lemma`` (a tactic plan's ``Lemmas:`` entry)."""

    file: str
    line: int
    name: str
    kind: str
    status: str | None


@dataclass
class BindingScan:
    """The bindings found in a dossier; ``errors`` are bindings that look like one but do not parse."""

    slug: str
    bindings: list[LeanBinding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def list_lean_bindings(*, root: Path | None = None, slug: str) -> BindingScan:
    """Parse the dossier's bindings without resolving them.

    Raises:
        ValueError: invalid slug.
        FileNotFoundError: no such dossier.
    """
    d = _scripts.dossier_dir(_scripts.resolve_root(root), slug)
    errs: list[str] = []
    out = []
    gn = _scripts.gate("check_lean_bindings")
    for f, line, name, ctx, kind in gn.bindings(d, errs, slug):
        out.append(LeanBinding(file=f, line=line, name=name, kind=kind, status=gn.binding_status(kind, ctx)))
    return BindingScan(slug=slug, bindings=out, errors=errs)


def check_lean_bindings(*, root: Path | None = None, slugs: Iterable[str] = (),
                        assembled_only: bool = False) -> GateResult:
    """Run G-NAME.

    Args:
        root: mathAgents checkout.
        slugs: dossiers to check (default: all).
        assembled_only: with no slugs, check only Stage 7+ dossiers (as CI does).

    Raises:
        ValueError: invalid slug.
    """
    r = _scripts.resolve_root(root)
    named = [_scripts.check_slug(s) for s in _scripts.names(slugs, "slugs")]
    errs, checked = _scripts.gate("check_lean_bindings").run(r, named, assembled_only)
    return GateResult(gate="G-NAME", success=not errs, checked=list(checked), errors=errs)
