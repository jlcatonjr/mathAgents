"""Shared fixture helpers: a throwaway copy of this checkout's gate inputs (no .lake, no git), and a consumer
team's orchestrator file."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def copy_checkout(dest: Path) -> Path:
    for rel in ("scripts", "references", "docs/charter", "reports/dossiers", "reports/references"):
        if (ROOT / rel).exists():
            shutil.copytree(ROOT / rel, dest / rel, ignore=shutil.ignore_patterns("__pycache__", "security-approvers.txt"))
    shutil.copytree(ROOT / "lean", dest / "lean", ignore=shutil.ignore_patterns(".lake", "build"))
    (dest / "reports" / "kernel").mkdir(parents=True, exist_ok=True)
    for f in ("latest.json", "name-index.txt"):
        if (ROOT / "reports" / "kernel" / f).exists():
            shutil.copy2(ROOT / "reports" / "kernel" / f, dest / "reports" / "kernel" / f)
    for f in ("brief.json",):
        if (ROOT / f).exists():
            shutil.copy2(ROOT / f, dest / f)
    return dest


def orchestrator(agents_dir: Path, roster: tuple[str, ...] = ()) -> None:
    """A consumer team's orchestrator: the pipeline agents are exported only next to one (M2)."""
    import sys
    sys.path.insert(0, str(ROOT))
    from mathagents import cli
    agents_dir.mkdir(parents=True, exist_ok=True)
    listed = "".join(f"  - {a}\n" for a in ("orchestrator", *roster))
    (agents_dir / cli.ORCHESTRATOR).write_text(f"---\nname: Orchestrator\nagents:\n{listed}---\n# Orchestrator\n")
