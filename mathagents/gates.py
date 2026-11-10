"""Run the automated gates together, in CI order (``.github/workflows/gates.yml``, minus the test suites).

Order: G-KERNEL (rebuilt only with ``run_kernel``; otherwise the report's freshness is checked), G-NAME
(Stage 7+ dossiers), G-BLUEPRINT, registries, preferences, then the dossier validator. Every gate runs
even after one fails, so the report is complete.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mathagents import _scripts
from mathagents.results import CommandResult, GateResult

__all__ = ["GATES", "GatesReport", "run_gates"]

GATES: tuple[str, ...] = ("G-KERNEL", "G-NAME", "G-BLUEPRINT", "registries", "preferences", "dossiers")


@dataclass
class GatesReport:
    """Results by gate name (``GATES`` order); ``success`` only when every gate that ran passed.
    ``errors`` and ``notices`` collect every gate's, prefixed with the gate name."""

    success: bool
    results: dict[str, GateResult | CommandResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)

    @property
    def failed(self) -> list[str]:
        return [name for name, res in self.results.items() if not res.success]


def run_gates(*, root: Path | None = None, run_kernel: bool = False, base: str | None = None,
              conversation: str | None = None) -> GatesReport:
    """Run every automated gate.

    Args:
        root: mathAgents checkout.
        run_kernel: rebuild and audit the Lean library first (slow); otherwise the existing report must
            be current and PASS (G-KERNEL fails when it is not).
        base: git ref for the dossier validator's append-only checks.
        conversation: current conversation id (waiver scope).
    """
    from mathagents.bindings import check_lean_bindings
    from mathagents.blueprint import check_blueprint
    from mathagents.dossiers import validate_dossiers
    from mathagents.kernel import run_kernel_gate
    from mathagents.preferences import check_preferences
    from mathagents.registries import validate_registries

    r = _scripts.resolve_root(root)
    rep = GatesReport(success=True)
    if run_kernel:
        k = run_kernel_gate(root=r)
        rep.results["G-KERNEL"] = GateResult(gate="G-KERNEL", success=k.success, errors=k.errors,
                                             notices=[f"proved={k.proved} open={k.open} failed={k.failed}"])
    else:  # not rebuilt: the existing report must still be current and PASS
        from mathagents.kernel import kernel_report_problem

        problem = kernel_report_problem(root=r)
        rep.results["G-KERNEL"] = GateResult(gate="G-KERNEL", success=problem is None,
                                             errors=[problem] if problem else [],
                                             notices=["report not rebuilt; checked that it is current and PASS"])
    rep.results["G-NAME"] = check_lean_bindings(root=r, assembled_only=True)
    rep.results["G-BLUEPRINT"] = check_blueprint(root=r)
    rep.results["registries"] = validate_registries(root=r)
    rep.results["preferences"] = check_preferences(root=r)
    rep.results["dossiers"] = validate_dossiers(root=r, base=base, conversation=conversation)
    for name, res in rep.results.items():
        rep.errors += [f"{name}: {e}" for e in res.errors]
        rep.notices += [f"{name}: {n}" for n in res.notices]
    rep.success = not rep.failed
    return rep
