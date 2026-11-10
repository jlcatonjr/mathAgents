#!/usr/bin/env python3
"""Toolchain-bump statement check, the primary meaning check of the wave: dump every project theorem's
elaborated statement (`pp.all`) under one toolchain, then compare two dumps. Run `dump` on the OLD build
(before the bump) and on the NEW build, then `compare`. A theorem whose elaborated statement differs,
appears or disappears goes to a human fidelity review. This catches what a source diff cannot: changed
coercions, instances, notation and unfolding. statement_drift.py is a secondary screen.

  statement_types.py dump --lean-dir DIR --out FILE
  statement_types.py compare OLD.tsv NEW.tsv
Exit 0 = written / identical; 1 = differences; 2 = error (an empty dump is an error, never a pass).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lean_template import run_template  # noqa: E402


def load(path: Path) -> dict[str, str]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            name, _, stmt = line.partition("\t")
            rows[name] = stmt
    if not rows:
        raise RuntimeError(f"{path} lists no theorem statements")
    return rows


def compare(old: Path, new: Path) -> int:
    a, b = load(old), load(new)
    changed = sorted(n for n in a.keys() & b.keys() if a[n] != b[n])
    gone, added = sorted(a.keys() - b.keys()), sorted(b.keys() - a.keys())
    print(f"statement_types: {len(a)} old, {len(b)} new; changed {len(changed)}, removed {len(gone)}, added {len(added)}")
    for kind, names in (("changed", changed), ("removed", gone), ("added", added)):
        for n in names:
            print(f"  {kind:8} {n}")
    return 1 if changed or gone or added else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump")
    d.add_argument("--lean-dir", type=Path, required=True)
    d.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("compare")
    c.add_argument("old", type=Path)
    c.add_argument("new", type=Path)
    args = ap.parse_args()
    if args.cmd == "compare":
        return compare(args.old, args.new)
    n = run_template(args.lean_dir.resolve(), "StatementTypes.lean", "STATEMENT_TYPES_OUT", args.out, "STATEMENT-TYPES")
    if n == "0":
        raise RuntimeError("no project theorems found (is the proved library's module prefix right?)")
    print(f"statement_types: {n} theorem statement(s) written to {args.out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed
        print(f"statement_types: error: {exc}")
        sys.exit(2)
