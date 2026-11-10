"""Dossiers and the eight-stage pipeline: status, stage preconditions, validation, result labels.

A dossier is ``reports/dossiers/<slug>/``. ``validate_dossiers`` runs the dossier validator
(structure, G-FID, G-AX, G-CX) exactly as ``scripts/validate_dossier.py`` does; ``require_stage`` is
the precondition for dispatching stage N (spec DD-43), which at N = 8 also runs G-NAME and, when a
blueprint exists, G-BLUEPRINT.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from mathagents import _scripts
from mathagents.results import GateResult

__all__ = ["STAGES", "DossierStatus", "ResultLabel", "Stage", "dossier_status", "list_dossiers", "require_stage",
           "result_labels", "validate_dossiers"]


@dataclass(frozen=True)
class Stage:
    """One pipeline stage: the agents that run it and the dossier artifacts it produces."""

    number: int
    name: str
    agents: tuple[str, ...]
    artifacts: tuple[str, ...]


# Stage artifacts mirror scripts/dossier_structure.py STAGE_ARTIFACTS (tests/test_api_functional.py checks this).
STAGES: tuple[Stage, ...] = (
    Stage(0, "Intake", ("orchestrator", "interpretation-advisor"), ("problem-card.md",)),
    Stage(1, "Formal statement and fidelity", ("statement-formalizer", "fidelity-auditor"),
          ("statement.md", "fidelity.json", "back-translation.md")),
    Stage(2, "Proof-strategy skeleton", ("proof-strategist", "adversarial"), ("strategy.md", "strategy-review.md")),
    Stage(3, "Explicit derivations", ("logic-articulator",), ("derivations.md",)),
    Stage(4, "Tactic-level plans", ("tactic-planner",), ("tactic-plan.md",)),
    Stage(5, "Formalization", ("lean-prover",), ()),
    Stage(6, "Counterexample track", ("counterexample-hunter",), ()),
    Stage(7, "Informalization", ("lean-informalization",), ("informalization.md",)),
    Stage(8, "Dossier assembly", ("orchestrator", "axiom-auditor"), ("kernel-snapshot.json",)),
)


@dataclass(frozen=True)
class ResultLabel:
    """A result label found in a dossier file (``Result status: proved`` and the like)."""

    file: str
    value: str


@dataclass(frozen=True)
class DossierStatus:
    """What a dossier holds. ``stages_with_artifacts`` lists the stages whose artifacts all exist;
    whether a stage may be dispatched is decided by ``require_stage``, never by this summary."""

    slug: str
    path: Path
    artifacts: tuple[str, ...]
    stages_with_artifacts: tuple[int, ...]
    lean_namespace: str | None
    result_labels: tuple[ResultLabel, ...]
    has_fidelity_record: bool
    has_counterexample_log: bool
    has_gax_record: bool
    has_kernel_snapshot: bool


def list_dossiers(*, root: Path | None = None) -> list[str]:
    """Slugs of every dossier directory, sorted."""
    d = _scripts.resolve_root(root) / "reports" / "dossiers"
    slug = _scripts.gate("validate_dossier").SLUG
    return sorted(p.name for p in d.iterdir() if p.is_dir() and slug.fullmatch(p.name)) if d.is_dir() else []


def result_labels(*, root: Path | None = None, slug: str) -> list[ResultLabel]:
    """Every result label in the dossier's text files (records excluded), as the validator sees them.

    Raises:
        ValueError: invalid slug.
        FileNotFoundError: no such dossier.
    """
    d = _scripts.dossier_dir(_scripts.resolve_root(root), slug)
    return [ResultLabel(f, v) for f, v in _scripts.gate("validate_dossier").result_labels(d)]


def dossier_status(*, root: Path | None = None, slug: str) -> DossierStatus:
    """Summarize a dossier's artifacts and labels (no gate is run).

    Raises:
        ValueError: invalid slug.
        FileNotFoundError: no such dossier.
    """
    import json

    r = _scripts.resolve_root(root)
    d = _scripts.dossier_dir(r, slug)
    files = tuple(sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()))
    top = {p.name for p in d.iterdir() if p.is_file()}
    done = tuple(s.number for s in STAGES if s.artifacts and all(a in top for a in s.artifacts))
    ns = None
    for rec in ("fidelity.json", "kernel-snapshot.json", "counterexamples.json"):
        try:
            ns = json.loads((d / rec).read_text(encoding="utf-8")).get("lean_namespace")
        except (OSError, ValueError, AttributeError):
            continue
        if ns:
            break
    return DossierStatus(slug=slug, path=d, artifacts=files, stages_with_artifacts=done, lean_namespace=ns,
                         result_labels=tuple(result_labels(root=r, slug=slug)),
                         has_fidelity_record="fidelity.json" in top, has_counterexample_log="counterexamples.json" in top,
                         has_gax_record="gax.json" in top, has_kernel_snapshot="kernel-snapshot.json" in top)


def validate_dossiers(*, root: Path | None = None, slugs: Iterable[str] = (), require_fid: Iterable[str] = (),
                      require_stages: Mapping[str, int] | None = None, kernel_report: Path | None = None,
                      conversation: str | None = None, base: str | None = None) -> GateResult:
    """Run the dossier validator (structure, G-FID, G-AX, G-CX); fail-closed.

    Args:
        root: mathAgents checkout.
        slugs: dossiers to check; none named (and no requirements) checks every dossier.
        require_fid: dossiers that must hold a current G-FID approval for every claim (Stage 2 gate).
        require_stages: ``{slug: N}`` preconditions for dispatching stage N (N >= 2 implies require_fid).
        kernel_report: report path (default ``reports/kernel/latest.json``).
        conversation: current conversation id, the scope of kernel-as-judge waivers.
        base: git ref for the append-only checks (default: merge base of HEAD with origin/HEAD).

    Raises:
        ValueError: an invalid slug or stage number.
        TypeError: a single string passed where a list of slugs is expected.
    """
    r = _scripts.resolve_root(root)
    stages = dict(require_stages or {})
    named = [_scripts.check_slug(s) for s in _scripts.names(slugs, "slugs")]
    fid = [_scripts.check_slug(s) for s in _scripts.names(require_fid, "require_fid")]
    for s, n in stages.items():
        _scripts.check_slug(s)
        if not isinstance(n, int) or not 0 <= n <= 8:
            raise ValueError(f"stage for {s!r} must be an int in 0..8, got {n!r}")
    errs, targets = _scripts.gate("validate_dossier").run(r, named, fid, stages, kernel_report, conversation, base)
    return GateResult(gate="dossier validator (structure, G-FID, G-AX, G-CX)", success=not errs,
                      checked=[s for s, _ in targets], errors=errs)


def require_stage(*, root: Path | None = None, slug: str, stage: int, conversation: str | None = None,
                  base: str | None = None) -> GateResult:
    """Precondition for dispatching ``stage`` on ``slug`` (spec DD-43).

    Raises:
        ValueError: invalid slug or stage.
    """
    return validate_dossiers(root=root, require_stages={slug: stage}, conversation=conversation, base=base)
