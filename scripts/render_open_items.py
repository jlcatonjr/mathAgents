#!/usr/bin/env python3
"""Render an open-items CSV into its markdown report, and check that the two agree. Fail-closed.

  render_open_items.py <report.md>           rewrite the table between the markers from the CSV
  render_open_items.py --check <report.md>   exit 1 if the table is stale or any item lacks a section

The report names its CSV on a line `<!-- open-items-csv: <path relative to the report> -->` and holds
the rendered table between `<!-- open-items:begin -->` and `<!-- open-items:end -->`. Every CSV id must
have a section headed `### <id>: ...`, and every such section must have a CSV row.
Exit 0 = in sync; 1 = out of sync; 2 = error.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

SOURCE = re.compile(r"<!--\s*open-items-csv:\s*(\S+)\s*-->")
BLOCK = re.compile(r"(<!-- open-items:begin -->\n).*?(<!-- open-items:end -->)", re.S)
SECTION = re.compile(r"^###\s+(OI-\d+)\b", re.M)
COLUMNS = (("id", "ID"), ("area", "Area"), ("item", "Item"), ("status", "Status"), ("owner", "Owner"),
           ("priority", "Priority"))


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def table(rows: list[dict]) -> str:
    head = "| " + " | ".join(t for _, t in COLUMNS) + " |\n|" + "---|" * len(COLUMNS) + "\n"
    return head + "".join("| " + " | ".join(cell(r[k]) for k, _ in COLUMNS) + " |\n" for r in rows)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    if len(args) != 1:
        print(__doc__)
        return 2
    report = Path(args[0])
    text = report.read_text(encoding="utf-8")
    src = SOURCE.search(text)
    if not src or not BLOCK.search(text):
        print(f"open items: FAIL: {report} lacks the open-items-csv line or the table markers")
        return 1
    rows = list(csv.DictReader((report.parent / src.group(1)).open(encoding="utf-8", newline="")))
    ids = [r["id"] for r in rows]
    rendered = BLOCK.sub(lambda m: m.group(1) + table(rows) + m.group(2), text)
    sections = SECTION.findall(text)
    errs = [f"{i}: no section in the report" for i in ids if i not in sections]
    errs += [f"{s}: section has no CSV row" for s in sections if s not in ids]
    errs += [f"{i}: listed more than once in the CSV" for i in sorted({i for i in ids if ids.count(i) > 1})]
    if check:
        if rendered != text:
            errs.append("the table is stale; re-run without --check")
    elif rendered != text:
        report.write_text(rendered, encoding="utf-8")
    for e in errs:
        print(f"FAIL {e}")
    print(f"open items: {len(rows)} item(s), {len(sections)} section(s): " + ("FAIL" if errs else "PASS"))
    return 1 if errs else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:  # fail closed
        print(f"open items: FAIL: error: {exc!r}")
        sys.exit(2)
