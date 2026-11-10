"""Documented signatures (### `fn(params)`) match the code's parameter names, in order."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "api-reference"
PKG = ROOT / "mathagents"
HEADING = re.compile(r"^#{2,4}\s+`([a-zA-Z_][a-zA-Z0-9_.]*)\(([^`]*)\)`")


def _split(params: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in params:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [p.split("=")[0].split(":")[0].strip() for p in out if p.strip()]


def _functions(mod: Path) -> dict[str, list[str]]:
    out = {}
    for node in ast.parse(mod.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef):
            a = node.args
            names = [x.arg for x in a.posonlyargs + a.args]
            if a.vararg:
                names.append("*" + a.vararg.arg)
            elif a.kwonlyargs:
                names.append("*")
            names += [x.arg for x in a.kwonlyargs]
            if a.kwarg:
                names.append("**" + a.kwarg.arg)
            out[node.name] = names
    return out


def _rows():
    for page in sorted(DOCS.glob("*.md")):
        mod = PKG / f"{page.stem.replace('-', '_')}.py"
        if not mod.is_file():
            continue
        funcs = _functions(mod)
        for line in page.read_text(encoding="utf-8").splitlines():
            m = HEADING.match(line)
            if m and m.group(1).split(".")[-1] in funcs:
                yield page.name, m.group(1), _split(m.group(2)), funcs[m.group(1).split(".")[-1]]


def test_signatures_match():
    bad = [f"{p}: {n}: documented {d} != code {c}" for p, n, d, c in _rows() if d != c]
    assert not bad, "\n".join(bad)


def test_not_vacuous():
    rows = list(_rows())
    assert len(rows) >= 40 and len({p for p, *_ in rows}) >= 14


def test_every_public_function_is_documented_with_a_signature():
    import importlib
    import sys

    sys.path.insert(0, str(ROOT))
    documented = {(p, n.split(".")[-1]) for p, n, *_ in _rows()}
    missing = []
    for page in sorted(DOCS.glob("*.md")):
        mod_name = page.stem.replace("-", "_")
        if not (PKG / f"{mod_name}.py").is_file():
            continue
        mod = importlib.import_module(f"mathagents.{mod_name}")
        for name in getattr(mod, "__all__", []):
            if callable(getattr(mod, name)) and not isinstance(getattr(mod, name), type) and (page.name, name) not in documented:
                missing.append(f"{mod_name}.{name}")
    assert not missing, missing
