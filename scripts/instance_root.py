"""The root a gate operates on (docs/module.md: harness vs instance).

The gate scripts are the harness; the tree they check (lean/, reports/, references/) is the instance.
In this checkout both are the same directory. A consuming repository (an instance scaffolded with
`mathagents init`) is selected with MATHAGENTS_ROOT, which the `mathagents run` CLI sets; the scripts
always read their own Lean templates from beside themselves (HARNESS_SCRIPTS), never from the instance.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

HARNESS_SCRIPTS = Path(__file__).resolve().parent
LEAN_TEMPLATES = HARNESS_SCRIPTS / "lean"


def instance_root() -> Path:
    """MATHAGENTS_ROOT when set, else the checkout these scripts live in."""
    env = os.environ.get("MATHAGENTS_ROOT")
    return Path(env).resolve() if env else HARNESS_SCRIPTS.parent


def charter_path(root: Path) -> Path:
    """The decision charter whose rows (`| D1 |`, `| C1 |`) settings and claim ledgers cite: the public summary
    `docs/charter/decisions-summary.md` where it exists (from the public release on, D45: it is the maintained file,
    and an instance may still hold a stale vendored full charter), else the full charter `docs/charter/03-decisions.md`."""
    for name in ("decisions-summary.md", "03-decisions.md"):
        if (p := root / "docs" / "charter" / name).is_file():
            return p
    raise FileNotFoundError("no decision charter: docs/charter/03-decisions.md or docs/charter/decisions-summary.md")


# the gate scripts and templates the package ships (mathagents/_harness_files.py GATE_SCRIPTS lists the same
# files; tests/test_module_packaging.py keeps the two in step)
GATE_FILES = (
    "instance_root.py", "proof_integrity.py", "check_proof_integrity.sh", "axiom_allowlist.py", "validate_dossier.py",
    "dossier_structure.py", "check_lean_bindings.py", "check_blueprint_consistency.py", "build_name_index.py",
    "preferences.py", "snapshot_kernel.py", "log_counterexample.py", "validate_registries.py", "probe_machine.py",
    "validate_evidence.py", "validate_claim_ledger.py", "lean_docs.py", "lean_pin.py", "scan_lean_draft.py", "check_strategy_sha.py", "lean/AxiomAudit.lean",
    "lean/NameIndex.lean",
)


def harness_sha256() -> str:
    """SHA-256 over the gate scripts and Lean templates, recorded in the G-KERNEL report so a verdict
    names the gate logic that produced it (a `pip install -U mathagents` changes it). The same files give
    the same digest in a checkout and in an installed wheel."""
    digest = hashlib.sha256()
    for rel in GATE_FILES:
        digest.update(rel.encode() + b"\0" + (HARNESS_SCRIPTS / rel).read_bytes())
    return digest.hexdigest()
