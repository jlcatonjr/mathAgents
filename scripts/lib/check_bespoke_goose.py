#!/usr/bin/env python3
"""Check the bespoke agents' Goose recipes with agentteams' own audit (refresh_agent_surfaces.sh, step 3b).

Under the write-policy pilot (D41, ``write_policy: "orchestrator-only"`` with ``goose`` among
``write_policy_frameworks``), ``agentteams --interop-from ... --description brief.json`` (agentteams #174, 1.0.0rc9)
renders the bespoke agents' recipes in agentteams' grant mode: one ``# agentteams-declared-tools:`` marker and the
workspace-confined ``agentteams_readfs`` extension, the same shape as every rendered read-only agent. mathagents'
own Goose scoping (``python3 -m mathagents._surfaces scope-goose``) would refuse that extension, so under the pilot
the recipes are checked instead of rescoped, with agentteams' audit (``agentteams.audit.run_post_audit``: the
``AR_GOOSE_*`` grant checks and ``AR_WRITE_POLICY``), and the readfs server they launch is checked byte for byte
against the copy agentteams ships.

Usage: check_bespoke_goose.py RECIPES_DIR BRIEF_JSON NAME...
Exit 0 = every named recipe passes; 1 = a finding or an error (the findings are printed); 3 = the pilot is off for
Goose (the caller scopes the recipes with mathagents instead).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

READFS = Path(".agentteams/bin/goose-readfs-mcp.py")
CODES = ("AR_GOOSE", "AR_WRITE_POLICY")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(next(l for l in __doc__.splitlines() if l.startswith("Usage:")), file=sys.stderr)
        return 1
    recipes, brief_path, names = Path(argv[0]), Path(argv[1]), argv[2:]
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    frameworks = brief.get("write_policy_frameworks") or []
    if not isinstance(frameworks, list):
        print(f"check-bespoke-goose: write_policy_frameworks must be a list, not {frameworks!r}", file=sys.stderr)
        return 1
    if brief.get("write_policy") != "orchestrator-only" or "goose" not in frameworks:
        print("check-bespoke-goose: the pilot is off for goose; scope the recipes with mathagents")
        return 3
    try:
        import agentteams
        from agentteams.audit import run_post_audit
    except ImportError as exc:
        print(f"check-bespoke-goose: agentteams' audit is unavailable ({exc})", file=sys.stderr)
        return 1
    try:
        files = [(f"{n}.yaml", (recipes / f"{n}.yaml").read_text(encoding="utf-8")) for n in names]
    except OSError as exc:
        print(f"check-bespoke-goose: {exc}", file=sys.stderr)
        return 1
    manifest = {"framework": "goose", "goose_tool_scoping": "grant", "write_policy": "orchestrator-only",
                "mcp_grants": brief.get("mcp_grants") or {}}
    result = run_post_audit(recipes.resolve(), manifest, rendered_files=files, ai_audit=False)
    findings = [f for f in result.agent_refactor_findings if f.code.startswith(CODES)]
    problems = [f"{f.severity} {f.code} {f.file}: {f.description}" for f in findings]
    problems += [f"{n}.yaml: no agentteams_readfs extension (expected under the pilot)"
                 for n, text in files if "agentteams_readfs" not in text]
    # agentteams ships the server as package data (agentteams/data/); no public accessor yet, so a layout change
    # fails this check closed, as a missing server
    shipped = Path(agentteams.__file__).parent / "data" / "goose-readfs-mcp.py"
    if not READFS.is_file() or not shipped.is_file():
        problems.append(f"readfs server missing: {READFS if not READFS.is_file() else shipped}")
    elif hashlib.sha256(READFS.read_bytes()).digest() != hashlib.sha256(shipped.read_bytes()).digest():
        problems.append(f"{READFS} differs from the copy agentteams {agentteams.__version__} ships ({shipped})")
    for p in problems:
        print(f"check-bespoke-goose: {p}", file=sys.stderr)
    if problems:
        return 1
    print(f"check-bespoke-goose: {len(files)} recipe(s) pass agentteams' grant and write-policy audit; "
          f"readfs matches agentteams {agentteams.__version__}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
