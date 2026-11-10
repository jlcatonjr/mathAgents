"""This machine's hardware and installed engines (``.machine/profile.json``, never committed).

``@engine-advisor`` joins the profile with the prover-engine registry to decide what it may offer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from mathagents import _scripts

__all__ = ["MachineProbe", "probe_machine", "read_machine_profile"]


@dataclass
class MachineProbe:
    """Outcome of ``probe_machine``: the profile it wrote, or the reason it failed."""

    success: bool
    profile: dict | None = None
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


def probe_machine(*, root: Path | None = None) -> MachineProbe:
    """Probe the machine and (re)write ``.machine/profile.json`` (machine-local; no dry run: the probe is
    the write)."""
    r = _scripts.resolve_root(root)
    res = _scripts.run_script(r, "probe_machine.py", "--print")
    if not res.success:
        return MachineProbe(success=False, errors=res.errors)
    return MachineProbe(success=True, profile=read_machine_profile(root=r), notices=["wrote .machine/profile.json"])


def read_machine_profile(*, root: Path | None = None) -> dict | None:
    """The last probed profile, or None when this machine has not been probed."""
    p = _scripts.resolve_root(root) / ".machine" / "profile.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
