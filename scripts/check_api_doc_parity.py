#!/usr/bin/env python3
"""Check that docs/api-reference/ and the mathagents package correspond (agentteams pattern).

  check_api_doc_parity.py [--strict] [--json]

STALE_PAGE: a page names a module that does not exist (always a failure).
COVERAGE_GAP: a public module has no page (a failure only with --strict; CI passes --strict).
UNDOCUMENTED_SYMBOL: a name in a module's __all__ has no heading on its page (a failure with --strict).
MISSING_SYMBOL: a page documents a heading that is not in the module's __all__ (always a failure).
Exit 0 = pass; 1 = findings; 2 = error.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NON_MODULE_PAGES = {"index"}
EXEMPT_MODULES: set[str] = set()
HEADING = re.compile(r"^#{2,4}\s+(?:class\s+)?`([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class Parity:
    documented: list[str] = field(default_factory=list)
    stale_pages: list[str] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)
    undocumented_symbols: list[str] = field(default_factory=list)
    missing_symbols: list[str] = field(default_factory=list)


def public_modules(pkg_dir: Path) -> list[str]:
    return sorted(p.stem for p in pkg_dir.glob("*.py") if not p.stem.startswith("_"))


def module_all(path: Path) -> list[str] | None:
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            return list(ast.literal_eval(node.value))
    return None


def compute_parity(pkg_dir: Path, docs_dir: Path) -> Parity:
    res = Parity()
    for page in sorted(docs_dir.glob("*.md")):
        if page.stem in NON_MODULE_PAGES:
            continue
        mod = page.stem.replace("-", "_")
        src = pkg_dir / f"{mod}.py"
        if not src.is_file():
            res.stale_pages.append(page.stem)
            continue
        res.documented.append(mod)
        names = module_all(src) or []
        heads = {m.group(1) for ln in page.read_text(encoding="utf-8").splitlines() if (m := HEADING.match(ln))}
        res.undocumented_symbols += [f"{mod}.{n}" for n in names if n not in heads]
        res.missing_symbols += [f"{mod}.{h}" for h in sorted(heads) if h not in names]
    res.coverage_gaps = [m for m in public_modules(pkg_dir) if m not in res.documented and m not in EXEMPT_MODULES]
    return res


def main(argv: list[str]) -> int:
    strict, as_json = "--strict" in argv, "--json" in argv
    res = compute_parity(ROOT / "mathagents", ROOT / "docs" / "api-reference")
    if as_json:
        print(json.dumps(asdict(res), indent=2))
    fails = [f"STALE_PAGE {p}" for p in res.stale_pages] + [f"MISSING_SYMBOL {s}" for s in res.missing_symbols]
    soft = [f"COVERAGE_GAP {m}" for m in res.coverage_gaps] + [f"UNDOCUMENTED_SYMBOL {s}" for s in res.undocumented_symbols]
    if strict:
        fails += soft
    if not as_json:
        for f in fails:
            print(f"FAIL {f}")
        for s in ([] if strict else soft):
            print(f"WARN {s}")
        print(f"API doc parity: {len(res.documented)} module(s) documented: " + ("FAIL" if fails else "PASS"))
    return 1 if fails else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:  # fail closed
        print(f"API doc parity: FAIL: error: {exc!r}")
        sys.exit(2)
