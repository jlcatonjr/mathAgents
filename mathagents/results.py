"""Result types shared by the mathagents API.

Every gate or command returns one of these instead of printing or exiting: ``success`` is the verdict,
``errors`` the findings (complete sentences, as the gate scripts print them after ``FAIL``), and
``notices`` the non-blocking remarks.
"""
from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["CommandResult", "GateResult"]


@dataclass
class GateResult:
    """Outcome of one automated gate run in-process (fail-closed: any finding means ``success`` False)."""

    gate: str
    success: bool
    checked: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


@dataclass
class CommandResult:
    """Outcome of a gate script the API runs as a subprocess (G-KERNEL, the name index, registries...)."""

    command: list[str]
    returncode: int
    success: bool
    output: str = ""
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
