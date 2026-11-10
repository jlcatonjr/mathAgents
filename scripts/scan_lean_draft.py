#!/usr/bin/env python3
"""Scan a returned Lean draft before it is piped to Lean or written (D39; @security condition on v0.2.5).

Lean runs code while it elaborates a file: `#eval`, `run_cmd`, `initialize` and the other metaprogramming commands
execute during `lake env lean --stdin`, so piping a researcher's returned draft to Lean, or writing it into the
library, would run content the orchestrator did not author (C-4). This scan uses G-KERNEL's own comment- and
string-aware scanner and token lists (scripts/proof_integrity.py), so it flags exactly the constructs G-KERNEL
would reject later, plus the other code-running constructs a proof draft never needs (elaborators, tactics,
simprocs, initializers and linters registered by attribute; `run_tac`, `by_elab`; `import Lean`; `IO.Process`,
`IO.FS`, `Lean.Elab`), before anything runs. `sorry`, `admit` and `stop` are allowed: they are open markers in a
WIP draft, and G-KERNEL still decides where they may stand.

Usage: python3 scripts/scan_lean_draft.py [FILE|- ...]   (`-`, or no argument at all: the draft is read from stdin)
Reading stdin lets a researcher scan a draft without saving it: hold the draft in one heredoc and pipe the same
text to this scan and, only if it is clean, to `lake env lean --stdin` (the agents' bodies show the form).
`-h` or `--help` as the first argument prints this text and exits 0 (scan a file of that name as `./--help`).
`--help` exiting 0 is not a clean scan verdict; only a scan of `-` or a path is.
Exit 0 = no finding; 1 = findings (do not pipe or write the draft; send it to @security); 2 = usage error
(an unreadable FILE, undecodable input, or `-` given more than once).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from proof_integrity import ESCAPE_TOKENS, META_COMMANDS, OPEN_MARKERS, lineno, strip_comments_and_strings, \
    token_pattern  # noqa: E402

FORBIDDEN = [t for t in ESCAPE_TOKENS if t not in OPEN_MARKERS] + META_COMMANDS
# A proof draft never needs metaprogramming, so this scan is stricter than G-KERNEL's source scan: it also refuses
# the other ways Lean runs code while reading a file (an elaborator, tactic, simproc, initializer or linter
# registered by attribute, `run_tac`, `by_elab`) and the APIs such code would use.
DRAFT_ONLY = ["run_tac", "by_elab", "IO.Process", "IO.FS", "Lean.Elab"]
_CODE_ATTRIBUTE = re.compile(r"@\[[^\]]*\b(?:builtin_)?(?:command_elab|term_elab|tactic|simproc|dsimproc|init|"
                             r"env_linter|linter|code_action|delab|app_unexpander|widget_module)\b[^\]]*\]")
_IMPORT_LEAN = re.compile(r"^\s*import\s+Lean(?:\.\S+)?\s*$", re.M)


def findings(src: str, label: str) -> list[str]:
    """Every construct in a draft that executes code or weakens the kernel, as `<label>:<line>: `<token>``."""
    code = strip_comments_and_strings(src)
    hits = [(m.start(), f"`{tok}`") for tok in FORBIDDEN + DRAFT_ONLY for m in token_pattern(tok).finditer(code)]
    hits += [(m.start(), "`+native`") for m in re.finditer(r"\+native\b", code)]
    hits += [(m.start(), f"code-running attribute `{m.group(0)}`") for m in _CODE_ATTRIBUTE.finditer(code)]
    hits += [(m.start(), f"`{m.group(0).strip()}` (a draft imports Mathlib, not Lean's internals)")
             for m in _IMPORT_LEAN.finditer(code)]
    return [f"{label}:{lineno(code, pos)}: {what}" for pos, what in sorted(hits)]


STDIN = "-"


def read_draft(arg: str) -> tuple[str, str]:
    """(label, text) of one argument: `-` is standard input, anything else a file path."""
    if arg == STDIN:
        return "<stdin>", sys.stdin.read()
    return arg, Path(arg).read_text(encoding="utf-8")


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):  # a file with such a name is still scanned as ./--help
        print(__doc__.strip())
        return 0
    if argv.count(STDIN) > 1:
        print("scan_lean_draft: `-` (standard input) may be given only once")
        return 2
    try:
        drafts = [read_draft(a) for a in (argv or [STDIN])]
    except (OSError, UnicodeDecodeError) as exc:
        print(f"scan_lean_draft: cannot read the draft ({exc})")
        return 2
    found = [f for label, src in drafts for f in findings(src, label)]
    for f in found:
        print(f"  - {f}")
    print(f"scan_lean_draft: {'FINDINGS: do not pipe or write this draft; send it to @security' if found else 'clean'}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
