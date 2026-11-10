"""G-CX: the counterexample log (spec DD-15, DD-16, DD-39, DD-59).

``log_counterexample`` and ``record_lean_witness`` call the sanctioned writer
(``scripts/log_counterexample.py``): the statement fingerprint always comes from the fresh kernel
report, never from the caller. Neither writes, changes or removes a verdict; verdicts are human
decisions (DD-29) and this API offers no way to record one.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from mathagents import _scripts

__all__ = ["METHODS", "CounterexampleLog", "LogResult", "log_counterexample", "read_counterexample_log",
           "record_lean_witness"]

METHODS: tuple[str, ...] = ("decide", "small-model", "smt", "atp", "manual")  # = log_counterexample.METHODS (tested)


@dataclass(frozen=True)
class CounterexampleLog:
    """``reports/dossiers/<slug>/counterexamples.json``, schema-validated; entries keep the schema's fields."""

    slug: str
    lean_namespace: str
    entries: tuple[Mapping, ...]

    def entry(self, cx_id: str) -> Mapping | None:
        return next((e for e in self.entries if e.get("id") == cx_id), None)


@dataclass
class LogResult:
    """Outcome of a log write; a refusal is ``success`` False with the reason in ``errors``."""

    success: bool
    slug: str
    dry_run: bool
    message: str = ""
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


def read_counterexample_log(*, root: Path | None = None, slug: str) -> CounterexampleLog | None:
    """The dossier's counterexample log, or None when it has none.

    Raises:
        ValueError: invalid slug.
        FileNotFoundError: no such dossier.
        RecordError: the log is malformed, fails its schema, or names another slug.
    """
    data = _scripts.read_record(_scripts.resolve_root(root), slug, "counterexamples.json")
    if data is None:
        return None
    return CounterexampleLog(slug=data["slug"], lean_namespace=data["lean_namespace"],
                             entries=tuple(MappingProxyType(dict(e)) for e in data["counterexamples"]))


def _result(slug: str, dry_run: bool, msg: str | None, refusal: str | None) -> LogResult:
    if refusal:
        return LogResult(success=False, slug=slug, dry_run=dry_run, errors=[refusal])
    return LogResult(success=True, slug=slug, dry_run=dry_run, message=msg or "",
                     notices=[f"Would {msg[len('would '):]}"] if dry_run and msg else [])


def log_counterexample(*, root: Path | None = None, slug: str, decl: str, method: str, description: str,
                       engine: str | None = None, namespace: str | None = None, dry_run: bool = False) -> LogResult:
    """Append a counterexample candidate against ``decl`` with the next ``CX-n`` id.

    Args:
        root: mathAgents checkout.
        slug: the dossier.
        decl: fully-qualified target declaration (must be in the fresh kernel report).
        method: one of ``METHODS``.
        description: what the candidate is and how it was found.
        engine: engine id from ``references/prover-engines.json``, if one was used.
        namespace: lean_namespace for a new log when the dossier has no fidelity record yet.
        dry_run: run every check, write nothing.

    Raises:
        ValueError: invalid slug or method.
    """
    _scripts.check_slug(slug)
    if method not in METHODS:
        raise ValueError(f"unknown method {method!r} (use one of {', '.join(METHODS)})")
    msg, refusal = _scripts.gate("log_counterexample").add_candidate(
        _scripts.resolve_root(root), slug, decl, method, description, engine, namespace, write=not dry_run)
    return _result(slug, dry_run, msg, refusal)


def record_lean_witness(*, root: Path | None = None, slug: str, cx_id: str, witness_decl: str,
                        dry_run: bool = False) -> LogResult:
    """Record ``lean_witness`` on an entry once the witness ``¬ (type_of% @target)`` is kernel-proved.

    Raises:
        ValueError: invalid slug.
    """
    _scripts.check_slug(slug)
    msg, refusal = _scripts.gate("log_counterexample").add_witness(
        _scripts.resolve_root(root), slug, cx_id, witness_decl, write=not dry_run)
    return _result(slug, dry_run, msg, refusal)
