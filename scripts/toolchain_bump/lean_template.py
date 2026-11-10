"""Shared by the toolchain-bump tools: run a Lean template against a project's build.

The template is appended after `import <proved library>`; the quoted placeholders `"PROJECT_LIB"` and
`"<OUT>"` (only the string literals, never comments) become the library name and the output path.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent


def proved_library(lean_dir: Path) -> str:
    """The one non-WIP lean_lib that has sources (a lean_lib without sources, like a stale entry, is ignored)."""
    libs = [lib["name"] for lib in tomllib.loads((lean_dir / "lakefile.toml").read_text()).get("lean_lib", [])]
    libs = [n for n in libs if (lean_dir / f"{n}.lean").exists() or (lean_dir / n).is_dir()]
    proved = [n for n in libs if not n.endswith("WIP")]
    if len(proved) != 1:
        raise RuntimeError(f"expected one proved lean_lib in {lean_dir}/lakefile.toml, found {proved}")
    return proved[0]


def run_template(lean_dir: Path, template: str, out_placeholder: str, out: Path, marker: str) -> str:
    """Run HERE/<template> in `lean_dir` (needs the build); returns the marker line's last field."""
    lib = proved_library(lean_dir)
    src = (HERE / template).read_text(encoding="utf-8")
    src = src.replace('"PROJECT_LIB"', json.dumps(lib)).replace(f'"{out_placeholder}"', json.dumps(str(out.resolve())))
    env = dict(os.environ, PATH=f"{Path.home() / '.elan' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}")
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=lean_dir, delete=False) as tf:
        tf.write(f"import {lib}\n" + src)
        path = Path(tf.name)
    try:
        r = subprocess.run(["lake", "env", "lean", str(path)], cwd=lean_dir, capture_output=True, text=True, env=env)
    finally:
        path.unlink(missing_ok=True)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith(marker + " ")]
    if r.returncode != 0 or len(lines) != 1 or not out.exists():
        raise RuntimeError(f"{template} failed: {(r.stdout + r.stderr).strip()[-600:]}")
    return lines[0].split()[-1]
