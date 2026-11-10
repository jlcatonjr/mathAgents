#!/usr/bin/env python3
"""G-NAME: Lean name binding (spec DD-17, DD-18). Fail-closed.

  check_lean_bindings.py [<slug> ...]      check every dossier, or the named ones
  check_lean_bindings.py --assembled-only  check only dossiers at Stage 7+ (informalization.md or a kernel
                                           snapshot); CI uses this, and --require-stage 8 checks any dossier

Every `[Lean: name]` binding in a dossier's prose, and every lemma a Stage 4 tactic plan names on its
`Lemmas:` line, must resolve to
  - a declaration in the current, fresh G-KERNEL report (project names), or
  - an entry of the declaration-name index for the pinned Mathlib (scripts/build_name_index.py).
Bindings are found case-insensitively and across lines; anything that looks like a binding or a lemma
item but does not parse fails, as does an unterminated `[Lean:`. The `Lean:` name of every `## Node:`
header in tactic-plan.md and derivations.md is resolved too. A missing, stale or malformed index
counts as unresolved; a lemma marked `(UNVERIFIED)` is unresolved.

DD-18: a binding may carry its status, `[Lean: X | open]` (proved, open, failed, refuted), which must
match the kernel report (refuted: a non-proved target refuted under G-CX). A project declaration
that is not `proved` must be bound with its status tag, and its paragraph must not call it proved
("proved", "proves", "proven", "proof of"; not "not proved"/"unproved").

Also run by `validate_dossier.py --require-stage <slug> 8` (Stage 8 assembly waits on G-NAME).
Exit 0 = pass; 1 = findings; 2 = error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_name_index  # noqa: E402
import validate_dossier as vd  # noqa: E402

BINDING = re.compile(r"\[\s*lean\s*:\s*([^\]]*)\]", re.I)        # may span lines
ANY_BINDING = re.compile(r"\[\s*lean\s*:", re.I)                  # every opening must parse
LEMMAS_LINE = re.compile(r"^\s*(?:[-*]\s*)?[*_`]*\s*Lemmas\s*[*_`]*\s*:\s*(.*)$", re.I)
NODE_LEAN = re.compile(r"^#{2,4}\s*Node:.*?\bLean:\s*(\S+)", re.I)
LEAN_NAME = re.compile(r"[^\s\[\](){}|,`*]+")
PROVED_CLAIM = re.compile(r"(?i)(?<!not )(?<!un)(?<!never )\b(?:proved|proves|proven|proof of)\b")
STATUSES = {"proved", "open", "failed", "refuted"}  # `[Lean: X | <status>]`
TEXT_SUFFIXES = {".md", ".tex", ".txt"}
MARKUP = "*_`"


def clean(token: str) -> str:
    t = token.strip().strip("*`").strip()
    if len(t) > 2 and t.startswith("_") and t.endswith("_"):  # markdown _emphasis_, not a trailing `_`
        t = t[1:-1]
    return t


def binding_status(kind: str, context: str) -> str | None:
    """The status tag of a narration binding from its `bindings()` context ('' tag = None)."""
    return (context.rsplit("\x00", 1)[1] or None) if kind == "narration" else None


def bindings(dossier: Path, errs: list[str], slug: str) -> list[tuple[str, int, str, str, str]]:
    """(file, line, name, paragraph, kind) for every binding; kind is "narration", "lemma" or "node".
    Anything that looks like a binding but does not parse is an error, never skipped."""
    out = []
    for f in sorted(dossier.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = str(f.relative_to(dossier))
        text = f.read_text(encoding="utf-8", errors="replace")
        paragraphs = [(m.start(), m.group(0)) for m in re.finditer(r"(?:[^\n]+\n?)+", text)]

        def para_at(pos: int) -> str:
            return next((p for start, p in paragraphs if start <= pos < start + len(p)), "")
        parsed = set()
        for m in BINDING.finditer(text):
            parsed.add(m.start())
            line = text.count("\n", 0, m.start()) + 1
            body, _, status = m.group(1).partition("|")
            status = status.strip().lower()
            if status and status not in STATUSES:
                errs.append(f"{slug}: {rel}:{line}: G-NAME: unknown status {status!r} in binding (use {sorted(STATUSES)})")
            names = [clean(x) for x in body.split(",")]
            if not any(names):
                errs.append(f"{slug}: {rel}:{line}: G-NAME: empty binding")
            for name in filter(None, names):
                if not LEAN_NAME.fullmatch(name):
                    errs.append(f"{slug}: {rel}:{line}: G-NAME: cannot parse binding {name!r}")
                else:
                    out.append((rel, line, name, para_at(m.start()) + "\x00" + status, "narration"))
        for m in ANY_BINDING.finditer(text):
            if m.start() not in parsed:
                errs.append(f"{slug}: {rel}:{text.count(chr(10), 0, m.start()) + 1}: G-NAME: unterminated binding")
        if f.name not in ("tactic-plan.md", "derivations.md"):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            nm = NODE_LEAN.match(line)
            if nm:
                out.append((rel, n, clean(nm.group(1)), line, "node"))
            lm = LEMMAS_LINE.match(line) if f.name == "tactic-plan.md" else None
            if not lm:
                continue
            value = clean(lm.group(1))
            if not value:
                errs.append(f"{slug}: {rel}:{n}: G-NAME: a Lemmas: list must be on its own line, '|'-separated")
                continue
            for item in value.split("|"):
                item = item.strip().lstrip("-*0123456789. ").strip()
                head = item.split("(", 1)[0].strip()  # "<name> (located: …)": one name before the note
                token = clean(head)
                if not token or not LEAN_NAME.fullmatch(token):
                    errs.append(f"{slug}: {rel}:{n}: G-NAME: cannot parse tactic-plan lemma {item!r}")
                else:
                    out.append((rel, n, token, item, "lemma"))
    return out


def check_bindings(root: Path, slug: str, kernel: dict | None, kernel_problem: str | None,
                   index: set[str] | None, index_problem: str | None) -> list[str]:
    errs: list[str] = []
    dossier = root / "reports" / "dossiers" / slug
    if not dossier.is_dir():
        return [f"{slug}: G-NAME: dossier directory not found"]
    found = bindings(dossier, errs, slug)
    # `refuted` tags only for targets the dossier labels refuted under G-CX (the label's own validity
    # is the G-CX module's check in validate_dossier.py)
    refuted = {m["decl"] for _, v in vd.result_labels(dossier) if (m := vd.CX_CANONICAL.fullmatch(v))}
    if found and kernel is None:
        errs.append(f"{slug}: G-NAME: {kernel_problem}")
    if found and index is None:
        errs.append(f"{slug}: G-NAME: {index_problem} (unresolved names fail closed)")
    for rel, n, name, context, kind in found:
        where = f"{slug}: {rel}:{n}"
        if kind == "lemma" and "UNVERIFIED" in context.upper():
            errs.append(f"{where}: G-NAME: tactic-plan lemma {name} is marked UNVERIFIED")
            continue
        k = (kernel or {}).get(name)
        if k is None and not (index and name in index):
            if kernel is not None and index is not None:
                errs.append(f"{where}: G-NAME: {name} resolves to no declaration in the kernel report or the "
                            "pinned Mathlib (DD-17; use the fully-qualified name)")
            continue
        if kind == "narration" and k is not None:
            context, _, tag = context.partition("\x00")
            actual = k.get("status")
            # DD-18: a binding's own status tag must match the kernel; a non-proved declaration must carry
            # one (open/failed, or refuted under G-CX), and its paragraph must not call it proved
            if tag == "refuted" and name not in refuted:
                errs.append(f"{where}: G-NAME: binding tags {name} as 'refuted', but the dossier has no G-CX "
                            f"'Result status: refuted ({name})' label")
            elif tag and tag != "refuted" and tag != actual:
                errs.append(f"{where}: G-NAME: binding tags {name} as {tag!r}, but the kernel report says {actual!r}")
            if actual != "proved":
                if PROVED_CLAIM.search(context):
                    errs.append(f"{where}: G-NAME: narration calls {name} proved, but the kernel report says "
                                f"{actual!r} (DD-18)")
                elif not tag:
                    errs.append(f"{where}: G-NAME: {name} is {actual!r} in the kernel report; bind it with its status, "
                                f"[Lean: {name} | {actual}] (DD-18)")
    return errs


def run(root: Path, slugs: list[str], assembled_only: bool = False) -> tuple[list[str], list[str]]:
    """G-NAME over the named dossiers (all when none; with assembled_only, only Stage 7+ dossiers):
    (findings, slugs checked). For main() and the mathagents API; slugs must already be valid."""
    dossiers = root / "reports" / "dossiers"
    if not slugs:
        slugs = sorted(p.name for p in dossiers.iterdir() if p.is_dir()) if dossiers.is_dir() else []
        if assembled_only:  # G-NAME is the Stage 8 gate: a dossier mid-pipeline may name Aux lemmas not yet written
            slugs = [s for s in slugs if any((dossiers / s / f).exists() for f in ("informalization.md", "kernel-snapshot.json"))]
    kernel, kp = vd.load_kernel(root, root / "reports" / "kernel" / "latest.json")
    index, ip = build_name_index.load_index(root / "reports" / "kernel" / "name-index.txt", root / "lean")
    return [e for s in slugs for e in check_bindings(root, s, kernel, kp, index, ip)], slugs


def main(argv: list[str]) -> int:
    root = vd.instance_root()
    if len(argv) >= 3 and argv[1] == "--root":
        root, argv = Path(argv[2]).resolve(), [argv[0]] + argv[3:]
    assembled_only = "--assembled-only" in argv
    slugs = [a for a in argv[1:] if a != "--assembled-only"]
    for s in slugs:
        if not vd.SLUG.fullmatch(s):
            print(f"G-NAME: FAIL: invalid slug {s!r}")
            return 2
    errs, slugs = run(root, slugs, assembled_only)
    for e in errs:
        print(f"FAIL {e}")
    print(f"G-NAME: {len(slugs)} dossier(s): " + ("FAIL" if errs else "PASS"))
    return 1 if errs else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:  # fail closed
        print(f"G-NAME: FAIL: error: {exc!r}")
        sys.exit(2)
