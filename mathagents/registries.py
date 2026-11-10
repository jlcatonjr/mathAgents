"""The object-logic and prover-engine registries (``references/object-logics.json``,
``references/prover-engines.json``) and their validator."""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from mathagents import _scripts
from mathagents.results import CommandResult

__all__ = ["Registry", "load_object_logics", "load_prover_engines", "validate_registries"]


@dataclass(frozen=True)
class Registry:
    """A registry: its default id and its entries (each keeps the registry schema's fields)."""

    default: str
    entries: tuple[Mapping, ...]

    def get(self, entry_id: str) -> Mapping | None:
        return next((e for e in self.entries if e.get("id") == entry_id), None)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(e["id"] for e in self.entries)


def _load(root: Path | None, name: str, default_key: str, list_key: str) -> Registry:
    data = json.loads((_scripts.resolve_root(root) / "references" / name).read_text(encoding="utf-8"))
    return Registry(default=data[default_key], entries=tuple(MappingProxyType(dict(e)) for e in data[list_key]))


def load_object_logics(*, root: Path | None = None) -> Registry:
    """``references/object-logics.json`` (unvalidated; run ``validate_registries`` for the checks)."""
    return _load(root, "object-logics.json", "default_logic", "logics")


def load_prover_engines(*, root: Path | None = None) -> Registry:
    """``references/prover-engines.json`` (unvalidated; run ``validate_registries`` for the checks)."""
    return _load(root, "prover-engines.json", "default_engine", "engines")


def validate_registries(*, root: Path | None = None) -> CommandResult:
    """Validate both registries against their schemas and source rules (``validate_registries.py``)."""
    return _scripts.run_script(_scripts.resolve_root(root), "validate_registries.py")
