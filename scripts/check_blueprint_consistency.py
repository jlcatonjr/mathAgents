#!/usr/bin/env python3
"""G-BLUEPRINT: blueprint marker consistency (spec DD-42). Fail-closed.

  check_blueprint_consistency.py [--blueprint DIR]

Reads every `.tex` file under the leanblueprint project (default `lean/blueprint/`, where leanblueprint
scaffolds it, else `blueprint/`; the generated `web/` output is skipped). For each node (a LaTeX
environment such as `theorem`, `lemma`, `definition` or `proof`; a proof is bound to the statement
before it, so its `\\leanok` also certifies that statement):
  - every name in `\\lean{...}` must resolve to a declaration in the current, fresh G-KERNEL report
    or in the pinned-Mathlib name index (scripts/build_name_index.py). This is the check that
    `leanblueprint checkdecls` performs, done here against the same pinned environment without adding
    the `checkdecls` Lake dependency (which would change lake-manifest.json);
  - a `\\leanok` marker is allowed only when every project declaration the node names is `proved`
    in the kernel report (a `\\leanok` is the author's declaration; DD-42 checks it against the kernel).
A missing blueprint, kernel report or name index fails. Blocks blueprint publication and Stage 8.
Exit 0 = pass; 1 = findings; 2 = error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_name_index  # noqa: E402
import validate_dossier as vd  # noqa: E402
from instance_root import instance_root  # noqa: E402

ENV = re.compile(r"\\begin\{([\w*-]+)\}(.*?)\\end\{\1\}", re.S)
LEAN = re.compile(r"\\lean\s*\{([^}]*)\}")
LEANOK = re.compile(r"\\leanok\b")
LABEL = re.compile(r"\\label\s*\{([^}]*)\}")
PROVES = re.compile(r"\\proves\s*\{([^}]*)\}")
URL = re.compile(r"\\(?:url|href)\s*\{[^}]*\}")
COMMENT = re.compile(r"(?<!\\)%.*$", re.M)
MACRO_CMD = re.compile(r"\\(?:newcommand|renewcommand|providecommand|DeclareRobustCommand|NewDocumentCommand|"
                       r"RenewDocumentCommand|ProvideDocumentCommand|DeclareDocumentCommand|newenvironment|"
                       r"renewenvironment|NewDocumentEnvironment|RenewDocumentEnvironment|def|gdef|edef|xdef|let)\b")
PROOF_ENVS = {"proof", "proof*"}
STATEMENT_ENVS = {"theorem", "lemma", "proposition", "corollary", "definition", "conjecture", "claim"}


def is_statement(env: str, body: str = "") -> bool:
    """Theorem-like: a standard statement environment, or any non-proof environment carrying a
    \\lean or \\label (custom node types configured through plastexdepgraph's thms= option)."""
    if env in PROOF_ENVS:
        return False
    return env.rstrip("*") in STATEMENT_ENVS or bool(LEAN.search(body) or LABEL.search(body))


def default_blueprints(root: Path) -> list[Path]:
    """leanblueprint scaffolds inside the Lake project (lean/blueprint); a top-level blueprint/ also
    counts. Every one that exists is checked."""
    found = [b for b in (root / "lean" / "blueprint", root / "blueprint") if b.is_dir()]
    return found or [root / "lean" / "blueprint"]


def default_blueprint(root: Path) -> Path:
    return default_blueprints(root)[0]


def sources(blueprint: Path) -> list[Path]:
    # skip only the generated top-level web/ output; scan style files too (macros live there)
    return sorted(p for p in blueprint.rglob("*") if p.suffix in (".tex", ".sty", ".cls")
                  and p.relative_to(blueprint).parts[0] != "web")


def check(root: Path, blueprint: Path) -> list[str]:
    errs: list[str] = []
    if not blueprint.is_dir():
        return [f"G-BLUEPRINT: no blueprint at {blueprint}"]
    files = sources(blueprint)
    if not any(f.suffix == ".tex" for f in files):
        return [f"G-BLUEPRINT: no .tex files under {blueprint}"]
    kernel, kp = vd.load_kernel(root, root / "reports" / "kernel" / "latest.json")
    index, ip = build_name_index.load_index(root / "reports" / "kernel" / "name-index.txt", root / "lean")
    if kernel is None:
        errs.append(f"G-BLUEPRINT: {kp}")
    if index is None:
        errs.append(f"G-BLUEPRINT: {ip}")
    if kernel is None or index is None:
        return errs
    texts = {f: COMMENT.sub("", URL.sub("", f.read_text(encoding="utf-8", errors="replace"))) for f in files}
    # every labelled statement's names, across all files, for \proves{label}
    by_label: dict[str, list[str]] = {}
    for text in texts.values():
        for m in ENV.finditer(text):
            if is_statement(m.group(1), m.group(2)):
                names = [n.strip() for grp in LEAN.findall(m.group(2)) for n in grp.split(",") if n.strip()]
                for lab in LABEL.findall(m.group(2)):
                    if lab.strip() in by_label:
                        errs.append(f"G-BLUEPRINT: label {lab.strip()!r} is defined more than once")
                    by_label[lab.strip()] = names
    for f, text in texts.items():
        rel = f.relative_to(root) if f.is_relative_to(root) else f
        for m in MACRO_CMD.finditer(text):
            if re.search(r"\\lean", text[m.end():m.end() + 400].split("\n\n")[0]):
                errs.append(f"G-BLUEPRINT: {rel}:{text.count(chr(10), 0, m.start()) + 1}: a macro or environment "
                            "definition mentions \\lean or \\leanok; markers must be written literally")
        if f.suffix != ".tex":
            continue
        statement_names: list[str] = []  # names of the last theorem-like statement, for a following proof
        covered = 0
        for m in ENV.finditer(text):
            env, body = m.group(1), m.group(2)
            covered += len(LEANOK.findall(body))
            names = [n.strip() for grp in LEAN.findall(body) for n in grp.split(",") if n.strip()]
            label = (LABEL.search(body) or [None, env])[1]
            line = text.count("\n", 0, m.start()) + 1
            for n in names:
                if n not in kernel and n not in index:
                    errs.append(f"G-BLUEPRINT: {rel}:{line}: node {label!r}: \\lean{{{n}}} resolves to no declaration")
            bound = list(names)
            if env in PROOF_ENVS:
                # a proof certifies the statement it proves: the one its \proves{label} names, else the
                # theorem-like statement before it
                target = PROVES.search(body)
                if target:
                    lab = target.group(1).strip()
                    if lab not in by_label:
                        errs.append(f"G-BLUEPRINT: {rel}:{line}: \\proves{{{lab}}} names no labelled statement")
                    bound += by_label.get(lab, [])
                else:
                    bound += statement_names
            if LEANOK.search(body):
                if not bound:
                    errs.append(f"G-BLUEPRINT: {rel}:{line}: node {label!r} is \\leanok but names no declaration")
                for n in bound:
                    k = kernel.get(n)
                    if k is not None and k.get("status") != "proved":
                        errs.append(f"G-BLUEPRINT: {rel}:{line}: node {label!r} is \\leanok but {n} is "
                                    f"{k.get('status')!r} in the kernel report (DD-42)")
            if is_statement(env, body):
                statement_names = names
        if len(LEANOK.findall(text)) > covered:
            errs.append(f"G-BLUEPRINT: {rel}: a \\leanok marker sits outside any parsed environment")
        if text.count("leanok") > len(LEANOK.findall(text)):
            errs.append(f"G-BLUEPRINT: {rel}: 'leanok' appears other than as a literal \\leanok "
                        "(e.g. through \\csname); markers must be written literally")
    return errs


def main(argv: list[str]) -> int:
    root = instance_root()
    args = argv[1:]
    if args[:1] == ["--root"]:
        root, args = Path(args[1]).resolve(), args[2:]
    blueprints = default_blueprints(root)
    if args[:1] == ["--blueprint"]:
        blueprints = [Path(args[1]).resolve()]
    errs = [e for bp in blueprints for e in check(root, bp)]
    for e in errs:
        print(f"FAIL {e}")
    print("G-BLUEPRINT: " + ("FAIL" if errs else "PASS"))
    return 1 if errs else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:  # fail closed
        print(f"G-BLUEPRINT: FAIL: error: {exc!r}")
        sys.exit(2)
