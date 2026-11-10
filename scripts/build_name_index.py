#!/usr/bin/env python3
"""Build the declaration-name index for G-NAME and G-BLUEPRINT (spec DD-17, DD-42). Fail-closed.

  build_name_index.py [--lean-dir DIR] [--out FILE]

Imports the pinned Mathlib (`import Mathlib`, so the Mathlib build cache must be present:
`cd lean && lake exe cache get`) and writes every non-internal, non-private constant name to
`reports/kernel/name-index.txt` (gitignored). The first line binds the index to the exact toolchain and
dependency manifest it was built from:

  # name-index toolchain=<lean-toolchain> manifest_sha256=<sha256 of lake-manifest.json> count=<n>

`load_index` refuses an index whose header does not match the current tree, so a Mathlib bump makes
the index stale until it is rebuilt. Both refuse a Mathlib checkout (`lean/.lake/packages/mathlib`) built for
another toolchain than the pin (P4, docs/lean-version-governance.md); building also refuses a missing checkout
("Mathlib not built"). Project names (the lakefile's lean_lib prefixes) are not indexed:
they resolve against the fresh G-KERNEL report.
Exit 0 = written; 1 = failed; 2 = error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lean_pin  # noqa: E402  (P4: the Mathlib checkout matches the pin)
from instance_root import LEAN_TEMPLATES, instance_root  # noqa: E402

ROOT = instance_root()
DEFAULT_OUT = ROOT / "reports" / "kernel" / "name-index.txt"


def header_for(lean_dir: Path) -> str:
    toolchain = (lean_dir / "lean-toolchain").read_text(encoding="utf-8").strip()
    manifest = hashlib.sha256((lean_dir / "lake-manifest.json").read_bytes()).hexdigest()
    return f"# name-index toolchain={toolchain} manifest_sha256={manifest}"


PROJECT_PREFIXES = ("MathAgents.", "MathAgentsWIP.")  # this checkout's; an instance's come from its lakefile


def project_prefixes(lean_dir: Path) -> tuple[str, ...]:
    """The `<lib>.` prefix of every lean_lib in the instance's lakefile.toml (project names resolve only
    via the kernel report); PROJECT_PREFIXES when there is no lakefile.toml."""
    cfg = lean_dir / "lakefile.toml"
    if not cfg.exists():
        return PROJECT_PREFIXES
    return tuple(f"{lib['name']}." for lib in tomllib.loads(cfg.read_text(encoding="utf-8")).get("lean_lib", []))


def checkout_problem(lean_dir: Path, require_built: bool) -> str | None:
    """A reason not to read Mathlib names from this tree: the .lake Mathlib checkout was built for another
    toolchain than the pin (P4), or, with ``require_built``, there is no checkout at all."""
    pin = lean_pin.read_pin(lean_dir)
    if require_built and pin["uses_mathlib"] and pin["checkout_toolchain"] is None:
        return lean_pin.NOT_BUILT
    return lean_pin.checkout_finding(pin)


def load_index(path: Path, lean_dir: Path) -> tuple[set[str] | None, str | None]:
    """Return (names, problem); a missing, stale or malformed index is a problem, never an empty index.
    The index is a local, gitignored artifact: CI rebuilds it, and a hand-written one is a DD-29-class
    trust limit. The checks here catch accidents (truncation, a project name in it), not forgery."""
    if not path.exists():
        return None, f"no name index ({path.name}); run scripts/build_name_index.py"
    with path.open(encoding="utf-8") as fh:
        first = fh.readline().strip()
        lines = [line.strip() for line in fh if line.strip()]
    names = set(lines)
    count = first.rsplit("count=", 1)[-1] if "count=" in first else ""
    if not count.isdigit() or int(count) != len(lines):
        return None, "malformed name index: its count does not match its entries; rebuild it"
    if any(n.startswith(project_prefixes(lean_dir)) for n in names):
        return None, "malformed name index: it lists project declarations, which resolve only via the kernel report"
    try:
        want = header_for(lean_dir)
    except OSError as exc:
        return None, f"cannot read the toolchain or manifest ({exc})"
    if not first.startswith(want + " "):
        return None, "stale name index: built for another toolchain or lake-manifest; rebuild it"
    if problem := checkout_problem(lean_dir, require_built=False):
        return None, f"name index not usable: {problem}"
    if not names:
        return None, "empty name index"
    return names, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lean-dir", type=Path, default=ROOT / "lean")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    lean_dir = args.lean_dir.resolve()
    if problem := checkout_problem(lean_dir, require_built=True):
        print(f"build_name_index: REFUSED: {problem}")
        return 1
    header = header_for(lean_dir)  # computed before the run and compared after: no toolchain/manifest race
    tmp_out = args.out.with_suffix(".tmp")
    template = (LEAN_TEMPLATES / "NameIndex.lean").read_text(encoding="utf-8")
    env = dict(os.environ, PATH=f"{Path.home() / '.elan' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}")
    tmp_dir = lean_dir / ".lake" / "tmp"  # gitignored; the only lean/ path a confined run may write
    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=tmp_dir, delete=False) as tf:
        # only the string literal: the doc comment names the placeholder too, and a path containing `/-`
        # would open a Lean comment there
        tf.write("import Mathlib\n" + template.replace('"NAME_INDEX_OUT"', json.dumps(str(tmp_out.resolve()))))
        src = Path(tf.name)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(["lake", "env", "lean", str(src)], cwd=lean_dir, capture_output=True, text=True, env=env)
    finally:
        src.unlink(missing_ok=True)
    count = [ln for ln in r.stdout.splitlines() if ln.startswith("NAME-INDEX ")]
    if r.returncode != 0 or len(count) != 1 or not tmp_out.exists():
        tmp_out.unlink(missing_ok=True)
        print(f"build_name_index: FAIL (exit {r.returncode}): {(r.stdout + r.stderr).strip()[-600:]}")
        return 1
    names = tmp_out.read_text(encoding="utf-8")
    if header_for(lean_dir) != header:
        tmp_out.unlink(missing_ok=True)
        print("build_name_index: FAIL: lean-toolchain or lake-manifest.json changed during the build; re-run")
        return 1
    n = len([ln for ln in names.splitlines() if ln.strip()])
    args.out.write_text(f"{header} count={n}\n{names}", encoding="utf-8")
    tmp_out.unlink(missing_ok=True)
    print(f"build_name_index: wrote {n} names to {args.out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed
        print(f"build_name_index: error: {exc!r}")
        sys.exit(2)
