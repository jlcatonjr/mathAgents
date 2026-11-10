"""G-BLUEPRINT: leanblueprint ``\\lean{}`` names and ``\\leanok`` markers against the kernel (DD-42).

With no blueprint in the checkout the gate does not apply and passes with a notice, as in CI and at
Stage 8 assembly (both run it only when a blueprint exists). The bare CLI
(``check_blueprint_consistency.py`` with no blueprint) fails instead; ``check_blueprint(blueprint=...)``
on a missing directory fails the same way.
"""
from __future__ import annotations

from pathlib import Path

from mathagents import _scripts
from mathagents.results import GateResult

__all__ = ["check_blueprint", "find_blueprints"]


def find_blueprints(*, root: Path | None = None) -> list[Path]:
    """Existing blueprint directories among the gate's defaults (``lean/blueprint/``, ``blueprint/``)."""
    return [p for p in _scripts.gate("check_blueprint_consistency").default_blueprints(_scripts.resolve_root(root))
            if p.is_dir()]


def check_blueprint(*, root: Path | None = None, blueprint: Path | None = None) -> GateResult:
    """Run G-BLUEPRINT on ``blueprint`` (default: every blueprint ``find_blueprints`` returns)."""
    r = _scripts.resolve_root(root)
    bps = [blueprint.resolve()] if blueprint is not None else find_blueprints(root=r)
    gbp = _scripts.gate("check_blueprint_consistency")
    errs = [e for bp in bps for e in gbp.check(r, bp)]
    notices = [] if bps else ["no blueprint in this checkout; G-BLUEPRINT does not apply"]
    return GateResult(gate="G-BLUEPRINT", success=not errs, checked=[str(b) for b in bps], errors=errs, notices=notices)
