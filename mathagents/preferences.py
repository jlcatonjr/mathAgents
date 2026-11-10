"""Project and dossier preferences (charter D32): every operator decision as a reversible setting.

Each setting has a ``choice``, its ``alternatives`` and the charter ``decision`` that recorded it, in
``references/preferences.toml`` (project defaults) and ``reports/dossiers/<slug>/preferences.toml``.
Writers check the result and leave nothing behind on a dry run: a dry run executes the real writer on
a scratch copy of the files it reads.

``set_preference`` refuses ``gax.*`` and ``fidelity.*`` settings: those record the operator's G-AX
answers and kernel-as-judge policy, which are human decisions (DD-29). The operator changes them with
``scripts/preferences.py set`` in a terminal.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from mathagents import _scripts
from mathagents.results import GateResult

__all__ = ["OPERATOR_ONLY_PREFIXES", "Preference", "PreferenceChange", "Reading", "check_preferences",
           "create_dossier", "effective_preferences", "intake_digest", "list_readings", "set_preference"]

OPERATOR_ONLY_PREFIXES: tuple[str, ...] = ("gax.", "fidelity.")
_SCRATCH = (Path("references"), Path("docs") / "charter", Path("reports") / "dossiers")


@dataclass(frozen=True)
class Preference:
    """A setting in force for a dossier. ``enforcement`` is ``enforced`` (checked mechanically) or
    ``advisory`` (followed by agents, checked at the human G-FID review)."""

    key: str
    choice: object
    source: str
    enforcement: str
    alternatives: tuple = ()
    decision: str | None = None


@dataclass(frozen=True)
class Reading:
    """A reading of the dossier's Interpretation Brief (``## R2. title``)."""

    id: str
    title: str


@dataclass
class PreferenceChange:
    """Outcome of ``set_preference`` or ``create_dossier``."""

    success: bool
    target: str
    dry_run: bool
    written: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


def _prefs():
    return _scripts.gate("preferences")


def _scratch(root: Path) -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory(prefix="mathagents-dry-")
    for rel in _SCRATCH:
        if (root / rel).exists():
            shutil.copytree(root / rel, Path(tmp.name) / rel)
    return tmp


def check_preferences(*, root: Path | None = None) -> GateResult:
    """Check the project file and every dossier's preferences.toml (``preferences.py check``)."""
    errs = _prefs().check_all(_scripts.resolve_root(root))
    return GateResult(gate="preferences", success=not errs, errors=errs)


def effective_preferences(*, root: Path | None = None, slug: str) -> dict[str, Preference]:
    """The settings in force for ``slug``: the dossier's own, else the project default.

    Raises:
        ValueError: invalid slug.
        FileNotFoundError: no such dossier, or no references/preferences.toml.
    """
    r = _scripts.resolve_root(root)
    d = _scripts.dossier_dir(r, slug)
    p = _prefs()
    tables: dict[str, dict] = {}
    for f in (r / "references" / "preferences.toml", d / "preferences.toml"):
        if f.exists():
            tables.update(p.settings(tomllib.loads(f.read_text(encoding="utf-8"))))
    return {k: Preference(key=k, choice=v, source=src, enforcement=p.enforcement(k),
                          alternatives=tuple(tables.get(k, {}).get("alternatives") or ()),
                          decision=tables.get(k, {}).get("decision"))
            for k, (v, src) in sorted(p.effective(r, slug).items())}


def list_readings(*, root: Path | None = None, slug: str) -> list[Reading]:
    """The readings of the dossier's Interpretation Brief (empty when it has none)."""
    r = _scripts.resolve_root(root)
    _scripts.dossier_dir(r, slug)
    return [Reading(i, t.strip()) for i, t in _prefs().readings_of(r, slug)]


def intake_digest(*, root: Path | None = None, slug: str) -> str:
    """The ``intake_sha256`` a G-FID approval binds (problem-card.md + preferences.toml)."""
    return _scripts.gate("dossier_structure").intake_digest(_scripts.dossier_dir(_scripts.resolve_root(root), slug))


def set_preference(*, root: Path | None = None, target: str, key: str, value: object,
                   dry_run: bool = False) -> PreferenceChange:
    """Change one setting: ``value`` becomes the choice and the old choice joins the alternatives.
    The result is checked and the file restored if any preference check fails.

    Args:
        root: mathAgents checkout.
        target: ``project`` or a dossier slug.
        key: dotted setting key, e.g. ``readings.selected``.
        value: the new choice (a string or a list of strings).
        dry_run: apply to a scratch copy and report; the checkout is not touched.

    Raises:
        ValueError: invalid target, or an operator-only key (``gax.*``, ``fidelity.*``).
    """
    if target != "project":
        _scripts.check_slug(target)
    if key.startswith(OPERATOR_ONLY_PREFIXES):
        raise ValueError(f"{key} records an operator decision (DD-29); change it with "
                         "`scripts/preferences.py set` in a terminal")
    r = _scripts.resolve_root(root)
    rel = "references/preferences.toml" if target == "project" else f"reports/dossiers/{target}/preferences.toml"
    if dry_run:
        with _scratch(r) as tmp:
            err = _prefs().set_setting(Path(tmp), target, key, value)
    else:
        err = _prefs().set_setting(r, target, key, value)
    if err:
        return PreferenceChange(success=False, target=target, dry_run=dry_run, errors=[err])
    shown = json.dumps(value, ensure_ascii=False)
    return PreferenceChange(success=True, target=target, dry_run=dry_run, written=[] if dry_run else [rel],
                            notices=[f"Would set {key} = {shown} in {rel}"] if dry_run else [f"{key} = {shown} in {rel}"])


def create_dossier(*, root: Path | None = None, slug: str, domain: str, readings: Iterable[str] = (),
                   dry_run: bool = False) -> PreferenceChange:
    """Start a dossier at intake: its preferences.toml (from the project defaults) and a problem-card
    skeleton. Never overwrites an existing file.

    Args:
        root: mathAgents checkout.
        slug: new dossier slug.
        domain: a D2 domain from the prover-engine registry.
        readings: selected readings of the Interpretation Brief, if one exists.
        dry_run: run on a scratch copy; the checkout is not touched.

    Raises:
        ValueError: invalid slug.
    """
    _scripts.check_slug(slug)
    r = _scripts.resolve_root(root)
    files = [f"reports/dossiers/{slug}/preferences.toml", f"reports/dossiers/{slug}/problem-card.md"]
    if any((r / f).exists() for f in files):
        return PreferenceChange(success=False, target=slug, dry_run=dry_run,
                                errors=["preferences.toml or problem-card.md already exists; edit it (or use set_preference)"])
    if dry_run:
        with _scratch(r) as tmp:
            err = _prefs().new_dossier(Path(tmp), slug, domain, _scripts.names(readings, "readings"))
        err = err.removeprefix("written, but: ") if err else None  # nothing was written to the checkout
        return PreferenceChange(success=err is None, target=slug, dry_run=True, errors=[err] if err else [],
                                notices=[f"Would write {f}" for f in files] if err is None else [])
    err = _prefs().new_dossier(r, slug, domain, _scripts.names(readings, "readings"))
    written = [f for f in files if (r / f).exists()]
    return PreferenceChange(success=err is None, target=slug, dry_run=False, written=written,
                            errors=[err] if err else [],
                            notices=["the files were written but fail the preference checks; fix them"] if err and written else [])
