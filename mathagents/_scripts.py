"""Internal: access to the gate scripts, which stay the CLI and the single source of gate logic.

The gate scripts are the **harness**; the tree they check is the **instance** (docs/module.md). In a
checkout (or an editable install) the harness is the checkout itself; in a wheel it is the copy the
build put in ``mathagents/_harness``. In-process gate functions are imported from the harness and
always receive the caller's ``root``; scripts that only have a ``main`` run as subprocesses from the
harness with ``MATHAGENTS_ROOT=<root>``. An instance never supplies gate code of its own.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

from mathagents.errors import MathAgentsError, RecordError
from mathagents.results import CommandResult

PACKAGE = Path(__file__).resolve().parent
CHECKOUT = PACKAGE.parent
IS_CHECKOUT = (CHECKOUT / "scripts" / "validate_dossier.py").is_file()
HARNESS = CHECKOUT if IS_CHECKOUT else PACKAGE / "_harness"
SCRIPTS = HARNESS / "scripts"
INSTANCE_MARKER = "mathagents.toml"
# the gate modules this package imports in-process (tests/test_api_boundary.py scans them for DD-29 writes)
IN_PROCESS = ("validate_dossier.py", "dossier_structure.py", "check_lean_bindings.py", "check_blueprint_consistency.py",
              "build_name_index.py", "preferences.py", "snapshot_kernel.py", "log_counterexample.py", "axiom_allowlist.py",
              "instance_root.py")


def resolve_root(root: Path | None) -> Path:
    """The tree to operate on: ``root``, else ``MATHAGENTS_ROOT``, else this checkout (an installed wheel
    has no default). It must be a mathAgents checkout or an instance (``mathagents.toml``) with ``reports/``."""
    if root is None and os.environ.get("MATHAGENTS_ROOT"):
        root = Path(os.environ["MATHAGENTS_ROOT"])
    if root is None:
        if not IS_CHECKOUT:
            raise FileNotFoundError("no instance root: pass root= or set MATHAGENTS_ROOT")
        root = CHECKOUT
    r = Path(root).resolve()
    declared = (r / INSTANCE_MARKER).is_file() or (r / "scripts" / "validate_dossier.py").is_file()
    if not declared or not (r / "reports").is_dir():
        raise FileNotFoundError(f"{r} is neither a mathAgents checkout nor an instance ({INSTANCE_MARKER} and reports/)")
    return r


def check_slug(slug: str) -> str:
    pattern = gate("validate_dossier").SLUG
    if not isinstance(slug, str) or not pattern.fullmatch(slug):
        raise ValueError(f"invalid dossier slug {slug!r} (expected {pattern.pattern})")
    return slug


def read_record(root: Path, slug: str, name: str) -> dict | None:
    """A dossier gate record (``fidelity.json``, ``gax.json``, ``counterexamples.json``) validated as the
    dossier validator validates it, or None when absent. Raises RecordError when invalid."""
    path = dossier_dir(root, slug) / name
    if not path.exists():
        return None
    vd = gate("validate_dossier")
    key = {"fidelity.json": "fid", "gax.json": "gax", "counterexamples.json": "cx"}[name]
    errs: list[str] = []
    record = vd.load_record(path, vd.load_schemas(root)[key], slug, errs)
    if errs:
        raise RecordError("; ".join(errs))
    return record


def dossier_dir(root: Path, slug: str, must_exist: bool = True) -> Path:
    d = root / "reports" / "dossiers" / check_slug(slug)
    if must_exist and not d.is_dir():
        raise FileNotFoundError(f"no dossier {slug!r} under reports/dossiers/")
    return d


def gate(name: str) -> ModuleType:
    """Import a gate script module (``validate_dossier``, ``preferences``...) from the harness."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))  # the scripts import each other by bare name
    mod = importlib.import_module(name)
    if Path(getattr(mod, "__file__", "") or "").resolve().parent != SCRIPTS:  # a host module of the same name
        raise MathAgentsError(f"module {name!r} is already imported from {getattr(mod, '__file__', '?')}, not from "
                              "the mathAgents gate scripts; import mathagents before that module, or rename it")
    return mod


def names(value, what: str) -> list[str]:
    """A list of strings from an iterable argument; a bare string is a caller mistake, not a list."""
    if isinstance(value, str):
        raise TypeError(f"{what} must be an iterable of strings, not a single string {value!r}")
    return list(value)


def run_script(root: Path, script: str, *args: str, timeout: float | None = None) -> CommandResult:
    """Run the harness's ``scripts/<script>`` against ``root`` with this interpreter; never raises on a
    non-zero exit."""
    path = SCRIPTS / script
    cmd = ([sys.executable, str(path)] if script.endswith(".py") else ["bash", str(path)]) + list(args)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MATHAGENTS_ROOT=str(root))
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, env=env, timeout=timeout)
    out = (r.stdout + r.stderr).strip()
    errs = [ln[5:] for ln in out.splitlines() if ln.startswith("FAIL ")]
    if r.returncode != 0 and not errs:
        errs = [out.splitlines()[-1] if out else f"{script} exited {r.returncode}"]
    shown = ["python3" if script.endswith(".py") else "bash", f"scripts/{script}", *args]  # no local paths
    return CommandResult(command=shown,
                         returncode=r.returncode, success=r.returncode == 0, output=out, errors=errs)
