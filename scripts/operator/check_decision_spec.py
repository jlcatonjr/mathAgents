#!/usr/bin/env python3
"""Preflight for an operator decision spec, run before `agentteams --sign-decision` reads the key.

Operator-only signing helper. Long-lived; doc owner: docs/release-policy.md §7. Every new
signing script calls it on each spec, before its y/N prompt:

    python3 -I scripts/operator/check_decision_spec.py SPEC.json --team-dir .github/agents

It checks what the security gate (agentteams `cli/decision_log.py`, `check_clearance`) will check on the signed
row, so a spec that cannot clear is refused before a signature is spent (2026-10-27: a spec without
`requesting_agent` produced a row the gate refused as "issued by 'an unnamed author'"):
  - author: the first non-empty of `requesting_agent`, `owner`, `author`, lower-cased with "@" stripped, must be on
    the team's roster (`references/security-approvers.txt`), or `security` when the roster lists no names;
  - `action_reviewed` is non-empty, and `scope` is empty or a ";"-list that contains it;
  - `date` (and `timestamp`, when present) is an ISO date with no placeholder left;
  - the team dir is one `--sign-decision` may write to;
  - lineage: every `derives_from` id names an action recorded in the team's log, and the whole chain resolves with
    no cycle. The gate unions `derives_from` over every row with the same action id, so an action id whose recorded
    rows already carry a broken lineage can never clear: use a new id (2026-10-28: two signed rows refused).
For `branch-cleanup:` and `branch-post-merge` actions it also warns when the branch tools would read a different
team dir (they take the first of .claude/agents, .github/agents, .codex/agents that has references/).

A pass is not a clearance: the effect class, non-eligibility and lineage are checked by `--sign-decision` itself,
and the clearance is the signed row. It reads no key and writes nothing.
Exit 0 = the spec can clear; 1 = it cannot (reasons listed); 2 = the spec or team dir could not be read.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

SIGN_TEAM_DIRS = (".github/agents", ".claude/agents", ".goose/recipes")
BRANCH_TOOL_TEAM_DIRS = (".claude/agents", ".github/agents", ".codex/agents")  # agentteams cli/branch_switch.py:25
DEFAULT_AUTHORS = frozenset({"security"})
ROSTER = "references/security-approvers.txt"
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$")


def decision_author(spec: dict) -> str:
    """The author the gate reads: the first non-empty requesting_agent, owner or author."""
    for field in ("requesting_agent", "owner", "author"):
        value = str(spec.get(field) or "").strip()
        if value:
            return value.lower().lstrip("@").strip() or value.lower()
    return ""


def approved_authors(team_dir: Path) -> frozenset[str]:
    """The roster's names with "@" stripped, or the default when the roster is absent or lists none."""
    path = team_dir / ROSTER
    if not path.exists():
        return DEFAULT_AUTHORS
    names = {line.strip().lower().lstrip("@") for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.strip().startswith("#")}
    return frozenset(names) or DEFAULT_AUTHORS


LOG = "references/security-decisions.log.csv"


def _ids(raw: str) -> set[str]:
    return {part.strip().lower() for part in re.split(r"[;,]", raw or "") if part.strip()}


def lineage_problems(spec: dict, team_dir: Path) -> list[str]:
    """Walk the spec's lineage as the gate does (agentteams cli/decision_lineage.py), fail-closed."""
    log = team_dir / LOG
    rows = list(csv.DictReader(log.open(encoding="utf-8", newline=""))) if log.exists() else []
    lineage: dict[str, set[str]] = {}
    for row in rows:
        aid = (row.get("action_reviewed") or row.get("decision") or "").strip().lower()
        if aid:
            lineage.setdefault(aid, set()).update(_ids(row.get("derives_from", "")))
    action = str(spec.get("action_reviewed") or "").strip().lower()
    lineage.setdefault(action, set()).update(_ids(str(spec.get("derives_from") or "")))
    problems: list[str] = []
    on_path: set[str] = set()
    explored: set[str] = set()

    def descend(node: str) -> None:
        on_path.add(node)
        for parent in sorted(lineage.get(node, set())):
            if parent in on_path:
                problems.append(f"lineage cycle at {parent!r} (via {node!r})")
            elif parent not in lineage:
                problems.append(f"lineage: {parent!r} (from {node!r}) names no recorded decision row")
            elif parent not in explored:
                descend(parent)
        on_path.discard(node)
        explored.add(node)

    descend(action)
    return problems


def branch_tool_team_dir(repo: Path) -> str | None:
    """The team dir the agentteams branch tools resolve by default."""
    for rel in BRANCH_TOOL_TEAM_DIRS:
        if (repo / rel / "references").is_dir():
            return rel
    return None


def check(spec: dict, team_rel: str, repo: Path) -> tuple[list[str], list[str]]:
    """Return (problems, warnings) for a spec signed into team_rel under repo."""
    problems: list[str] = []
    warnings: list[str] = []
    if team_rel not in SIGN_TEAM_DIRS:
        problems.append(f"team dir {team_rel!r} is not one --sign-decision writes to ({', '.join(SIGN_TEAM_DIRS)})")
        return problems, warnings
    author = decision_author(spec)
    allowed = approved_authors(repo / team_rel)
    if not author:
        problems.append("no author: set requesting_agent to 'security' (the gate reads requesting_agent, owner, "
                        "then author)")
    elif author not in allowed:
        problems.append(f"author {author!r} is not an approved security author {sorted(allowed)}")
    action = str(spec.get("action_reviewed") or "").strip()
    if not action:
        problems.append("action_reviewed is empty")
    scope = str(spec.get("scope") or "").strip()
    if action and scope:
        permitted = {part.strip().lower() for part in scope.split(";") if part.strip()}
        if action.lower() not in permitted:
            problems.append(f"scope {scope!r} does not contain action_reviewed {action!r}")
    for field in ("date", "timestamp"):
        if field not in spec and field == "timestamp":
            continue
        value = str(spec.get(field) or "").strip()
        if not ISO_DATE.match(value):
            problems.append(f"{field} {value!r} is not an ISO date (a placeholder left unset?)")
    problems += lineage_problems(spec, repo / team_rel)
    if action.startswith("branch-cleanup:") or action == "branch-post-merge":
        tool_dir = branch_tool_team_dir(repo)
        if tool_dir and tool_dir != team_rel:
            warnings.append(f"the branch tools read {tool_dir} by default; run them with --team-dir {team_rel}")
    return problems, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("spec", type=Path)
    parser.add_argument("--team-dir", required=True, help="the --output dir the row will be signed into")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"check_decision_spec: cannot read {args.spec}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(spec, dict):
        print(f"check_decision_spec: {args.spec} is not a JSON object", file=sys.stderr)
        return 2
    team_rel = args.team_dir.rstrip("/")
    try:
        problems, warnings = check(spec, team_rel, args.repo)
    except OSError as exc:
        print(f"check_decision_spec: cannot read the roster: {exc}", file=sys.stderr)
        return 2
    for w in warnings:
        print(f"WARNING: {w}")
    if problems:
        for p in problems:
            print(f"REFUSE: {p}")
        print("check_decision_spec: this spec cannot clear; fix it before signing (the key was not read).")
        return 1
    print(f"check_decision_spec: OK for {team_rel} ({spec.get('action_reviewed')}). Not a clearance: "
          "--sign-decision still checks the effect class, non-eligibility and lineage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
