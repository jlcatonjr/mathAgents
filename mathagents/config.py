"""Whether the mathAgents architecture is switched on for this machine (D35).

On by default. A machine turns it off with ``MATHAGENTS_ENABLED=0`` in a ``.env`` file, which is
machine-local and never committed (it must be gitignored). The process environment overrides ``.env``,
so CI and one-off runs can set it too. The ``.env`` used is the nearest one at or above the instance root,
up to the enclosing git work-tree root. Only the ``MATHAGENTS_ENABLED`` line is read; no other value in
the file is parsed, kept or printed.

Switched off, ``mathagents run`` refuses with exit code 3: a gate that did not run must never read as a
pass, so a stage precondition (``validate_dossier --require-fid``) can never succeed vacuously.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

__all__ = ["DISABLED_EXIT", "ENV_KEY", "Switch", "switch"]

ENV_KEY = "MATHAGENTS_ENABLED"
DISABLED_EXIT = 3
_TRUE, _FALSE = {"1", "true", "yes", "on"}, {"0", "false", "no", "off"}
_LINE = re.compile(rf"^\s*(?:export\s+)?{ENV_KEY}\s*=\s*(.*?)\s*$")


@dataclass(frozen=True)
class Switch:
    """The effective setting: ``enabled``, where it came from (``default``, ``environment`` or a ``.env``
    path), and ``problem`` when the value is not a recognised boolean (the switch then reads as off)."""

    enabled: bool
    source: str
    problem: str | None = None


def _env_files(root: Path) -> list[Path]:
    """Candidate .env files from ``root`` upward, stopping at the git work-tree root that contains it."""
    out = []
    for d in (root, *root.parents):
        out.append(d / ".env")
        if (d / ".git").exists():
            break
    return out


def _parse(value: str, source: str) -> Switch:
    v = value.strip().strip("'\"").lower()
    if v in _TRUE:
        return Switch(True, source)
    if v in _FALSE:
        return Switch(False, source)
    return Switch(False, source, f"{ENV_KEY}={value!r} in {source} is not one of 1/0, true/false, yes/no, on/off")


def switch(*, root: Path | None = None) -> Switch:
    """The switch for an instance (default: the working directory). Unrecognised values fail closed (off)."""
    if os.environ.get(ENV_KEY) is not None:
        return _parse(os.environ[ENV_KEY], "environment")
    for f in _env_files(Path(root or Path.cwd()).resolve()):
        if f.is_file():
            value = None
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                m = _LINE.match(line)
                if m:
                    value = m.group(1)  # the last assignment wins, as in a shell
            if value is not None:
                return _parse(value, str(f))
    return Switch(True, "default")
