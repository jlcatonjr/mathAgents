"""G-KERNEL: run the kernel gate and read its report (spec DD-14, DD-19, DD-34).

The report (``reports/kernel/latest.json``) is the only authority on whether a declaration is proved.
``load_kernel_report`` applies the same freshness checks as every gate (verdict PASS, source hash
matching the Lean tree, allowlist hash, no duplicate declarations) and refuses a report that fails
them, so a caller can never read a stale status as current.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from mathagents import _scripts
from mathagents.errors import KernelReportError

__all__ = ["Declaration", "KernelGateResult", "KernelReport", "declarations_in_namespace", "kernel_report_problem",
           "load_kernel_report", "run_kernel_gate"]

DEFAULT_REPORT = Path("reports") / "kernel" / "latest.json"


@dataclass(frozen=True)
class Declaration:
    """One audited declaration. ``status`` is ``proved``, ``open`` or ``failed``."""

    name: str
    kind: str
    module: str
    status: str
    statement_fingerprint: str
    statement_uses: tuple[str, ...] = ()
    axioms: tuple[str, ...] = ()
    negates_fingerprint: str | None = None
    private: bool = False

    @classmethod
    def from_report(cls, d: Mapping) -> Declaration:
        neg = d.get("negates_fingerprint")
        return cls(name=d["decl"], kind=d.get("kind", ""), module=d.get("module", ""), status=d.get("status", ""),
                   statement_fingerprint=str(d.get("statement_fingerprint", "")),
                   statement_uses=tuple(d.get("statement_uses") or ()), axioms=tuple(d.get("axioms") or ()),
                   negates_fingerprint=None if neg is None else str(neg), private=bool(d.get("private", False)))


@dataclass(frozen=True)
class KernelReport:
    """A G-KERNEL report that passed the freshness checks (unless loaded with ``require_fresh=False``)."""

    path: Path
    verdict: str
    checked_at: str
    lean_version: str
    toolchain_pin: str
    commit: str
    dirty: bool
    source_sha256: str
    allowlist_sha256: str | None
    findings: tuple[str, ...]
    open_markers: tuple[str, ...]
    declarations: Mapping[str, Declaration] = field(default_factory=dict)

    def status(self, name: str) -> str | None:
        """The kernel status of ``name``, or None when the report does not list it."""
        d = self.declarations.get(name)
        return d.status if d else None


@dataclass
class KernelGateResult:
    """Outcome of ``run_kernel_gate``; ``report`` is the fresh report when the gate passed."""

    success: bool
    verdict: str
    report_path: Path | None
    proved: int = 0
    open: int = 0
    failed: int = 0
    report: KernelReport | None = None
    output: str = ""
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


def kernel_report_problem(*, root: Path | None = None, path: Path | None = None) -> str | None:
    """Why the kernel report is unusable, or None when it is current and PASS.

    Args:
        root: mathAgents checkout (default: the one this package lives in).
        path: report path (default ``reports/kernel/latest.json`` under ``root``).
    """
    r = _scripts.resolve_root(root)
    _, problem = _scripts.gate("validate_dossier").load_kernel(r, path or r / DEFAULT_REPORT)
    return problem


def load_kernel_report(*, root: Path | None = None, path: Path | None = None,
                       require_fresh: bool = True) -> KernelReport:
    """Load the G-KERNEL report.

    Args:
        root: mathAgents checkout.
        path: report path (default ``reports/kernel/latest.json``).
        require_fresh: refuse a report the gates would refuse (default True). False reads it as-is,
            for diagnostics only; statuses in a stale report are not current.

    Raises:
        FileNotFoundError: no report at ``path``.
        KernelReportError: ``require_fresh`` and the report is not usable.
    """
    r = _scripts.resolve_root(root)
    p = path or r / DEFAULT_REPORT
    if not p.is_file():
        raise FileNotFoundError(f"no kernel report at {p}; run run_kernel_gate() first")
    if require_fresh:
        problem = kernel_report_problem(root=r, path=p)
        if problem:
            raise KernelReportError(problem)
    data = json.loads(p.read_text(encoding="utf-8"))
    decls = {d["decl"]: Declaration.from_report(d) for d in data.get("declarations", [])}
    allow = data.get("allowlist") or {}
    return KernelReport(path=p, verdict=data.get("verdict", ""), checked_at=data.get("checked_at", ""),
                        lean_version=data.get("lean_version", ""), toolchain_pin=data.get("toolchain_pin", ""),
                        commit=data.get("commit", ""), dirty=bool(data.get("dirty")),
                        source_sha256=data.get("source_sha256", ""), allowlist_sha256=allow.get("sha256"),
                        findings=tuple(map(str, data.get("findings") or ())),
                        open_markers=tuple(map(str, data.get("open_markers") or ())),
                        declarations=MappingProxyType(decls))


def run_kernel_gate(*, root: Path | None = None, write_report: bool = True,
                    timeout: float | None = None) -> KernelGateResult:
    """Build the Lean library and audit every declaration (``scripts/check_proof_integrity.sh``).

    Slow: runs ``lake build`` and a ``leanchecker`` replay.

    Args:
        root: mathAgents checkout.
        write_report: write ``reports/kernel/latest.json`` (False passes ``--no-report``).
        timeout: seconds before the subprocess is killed (default: none).
    """
    r = _scripts.resolve_root(root)
    cmd = _scripts.run_script(r, "proof_integrity.py", *([] if write_report else ["--no-report"]), timeout=timeout)
    res = KernelGateResult(success=cmd.success, verdict="PASS" if cmd.success else "FAIL",
                           report_path=r / DEFAULT_REPORT if write_report else None, output=cmd.output,
                           errors=[] if cmd.success else cmd.errors)
    if write_report and cmd.success:
        rep = load_kernel_report(root=r)
        res.report = rep
        for d in rep.declarations.values():
            if d.status in ("proved", "open", "failed"):
                setattr(res, d.status, getattr(res, d.status) + 1)
    return res


def declarations_in_namespace(*, root: Path | None = None, namespace: str,
                              include_helpers: bool = True) -> list[Declaration]:
    """Declarations under ``namespace`` in the fresh kernel report, sorted by name.

    Args:
        root: mathAgents checkout.
        namespace: e.g. ``MathAgents.P3DutchBook``.
        include_helpers: include ``<ns>.Aux.`` helper lemmas and ``<ns>.CX.`` witnesses.

    Raises:
        KernelReportError: the report is not usable.
    """
    ns = namespace.rstrip(".") + "."
    exempt = tuple(ns + s for s in _scripts.gate("validate_dossier").EXEMPT_SUBNAMESPACES)
    rep = load_kernel_report(root=root)
    return sorted((d for n, d in rep.declarations.items()
                   if n.startswith(ns) and (include_helpers or not n.startswith(exempt))), key=lambda d: d.name)
