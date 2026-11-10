#!/usr/bin/env python3
"""Toolchain-bump drift screen (secondary to statement_types.py): which Mathlib/core declarations that the
project's theorem statements reach changed between two toolchain tags. Every flagged constant goes to a human
fidelity review (G-FID; a statement change is a G-AX decision). Advisory: it flags, it never approves.
Fail-closed: a constant it cannot locate is UNKNOWN, and an empty extraction is an error.

It is a screen, not a proof of sameness. It sees only text changes inside (or deletions at the edge of) a
reached declaration's own line range. It does not follow external constants further, so drift in what they
use is not seen, and it does not see edits elsewhere that change a declaration's behaviour (`attribute`,
`instance` priorities, `set_option`). Those are what statement_types.py's elaborated comparison is for.

  statement_drift.py --lean-dir DIR --old v4.32.1 --new v4.34.1 [--cache DIR] [--deps FILE] [--out FILE]

1. Extract (needs the NEW build of the project): `lake env lean` on StatementDeps.lean lists every external
   constant reached from a theorem statement with its module and line range under the new toolchain.
   `--deps FILE` reuses an earlier extraction.
2. Compare (needs network once; cached in --cache): shallow-fetch both tags of mathlib4 and lean4, and flag a
   constant whose declaration lines (new version) overlap a changed hunk of `git diff OLD NEW -- <file>`, or
   whose file did not exist under OLD (moved or new: review by hand).
Exit 0 = no constant changed; 1 = constants flagged or unknown (review them); 2 = error.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lean_template import run_template  # noqa: E402

REPOS = {"mathlib4": "https://github.com/leanprover-community/mathlib4", "lean4": "https://github.com/leanprover/lean4"}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.M)


def module_file(module: str) -> tuple[str, str] | None:
    """(repo, path) of a module's source, or None for a package this screen does not cover."""
    top = module.split(".")[0]
    rel = module.replace(".", "/") + ".lean"
    if top == "Mathlib":
        return "mathlib4", rel
    if top in ("Init", "Std", "Lean", "Lake"):
        return "lean4", "src/" + rel
    return None


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def fetch(cache: Path, name: str, tags: list[str]) -> Path:
    repo = cache / name
    if not (repo / ".git").exists():
        repo.mkdir(parents=True, exist_ok=True)
        git(repo, "init", "-q")
    for t in tags:
        if git(repo, "rev-parse", "-q", "--verify", f"refs/tags/{t}").returncode != 0:
            r = git(repo, "fetch", "-q", "--depth", "1", "--filter=blob:none", REPOS[name], f"refs/tags/{t}:refs/tags/{t}")
            if r.returncode != 0:
                raise RuntimeError(f"cannot fetch {name} {t}: {r.stderr.strip()}")
    return repo


def changed_lines(repo: Path, old: str, new: str, path: str) -> list[tuple[int, int]] | None:
    """New-side line ranges touched by the diff; None when the file is absent under OLD."""
    if git(repo, "cat-file", "-e", f"{old}:{path}").returncode != 0:
        return None
    out = git(repo, "diff", "-U0", old, new, "--", path)
    if out.returncode != 0:
        raise RuntimeError(f"git diff failed for {path}: {out.stderr.strip()}")
    spans = []
    for m in HUNK.finditer(out.stdout):
        start, count = int(m.group(1)), int(m.group(2) or 1)
        # a pure deletion sits between lines `start` and `start + 1`: flag both neighbours
        spans.append((start, start + 1) if count == 0 else (start, start + count - 1))
    return spans


def screen(deps: list[tuple[str, str, int, int]], repos: dict[str, Path], old: str, new: str) -> dict:
    result = {"changed": [], "moved_or_new": [], "unknown": [], "unchanged": 0}
    cache: dict[tuple[str, str], list | None] = {}
    for name, module, a, b in deps:
        loc = module_file(module)
        if loc is None or a == 0:
            result["unknown"].append({"constant": name, "module": module})
            continue
        if loc not in cache:
            cache[loc] = changed_lines(repos[loc[0]], old, new, loc[1])
        spans = cache[loc]
        if spans is None:
            result["moved_or_new"].append({"constant": name, "module": module})
        elif any(s <= b and a <= e for s, e in spans):
            result["changed"].append({"constant": name, "module": module, "lines": [a, b]})
        else:
            result["unchanged"] += 1
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lean-dir", type=Path, required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--cache", type=Path, default=Path(tempfile.gettempdir()) / "toolchain-bump-cache")
    ap.add_argument("--deps", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--repo", action="append", default=[], metavar="NAME=PATH",
                    help="use an existing clone holding both tags (tests, offline mirrors)")
    args = ap.parse_args()
    deps_file = args.deps or (args.cache / "statement-deps.tsv")
    if not args.deps:
        args.cache.mkdir(parents=True, exist_ok=True)
        run_template(args.lean_dir.resolve(), "StatementDeps.lean", "STATEMENT_DEPS_OUT", deps_file, "STATEMENT-DEPS")
    deps = []
    for line in deps_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            n, m, a, b = line.split("\t")
            deps.append((n, m, int(a), int(b)))
    if not deps:
        raise RuntimeError("no external constants extracted: an empty screen is not a clean one")
    given = dict(r.split("=", 1) for r in args.repo)
    repos = {k: Path(v) for k, v in given.items()}
    for name in REPOS:
        if name not in repos:
            repos[name] = fetch(args.cache, name, [args.old, args.new])
    res = screen(deps, repos, args.old, args.new)
    res.update(old=args.old, new=args.new, constants=len(deps))
    if args.out:
        args.out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(f"statement_drift {args.old} -> {args.new}: {len(deps)} constants; changed {len(res['changed'])}, "
          f"moved/new {len(res['moved_or_new'])}, unknown {len(res['unknown'])}, unchanged {res['unchanged']}")
    for k in ("changed", "moved_or_new", "unknown"):
        for e in res[k]:
            print(f"  {k:12} {e['constant']}  ({e['module']})")
    return 1 if res["changed"] or res["moved_or_new"] or res["unknown"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed
        print(f"statement_drift: error: {exc}")
        sys.exit(2)
