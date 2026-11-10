"""Agent capability postures (IA-02; charter D34), shared by scripts/codex_preflight.py and the
conformance test in scripts/tests/test_stage_agents.sh.

The canonical declaration is the `tools:` list in .github/agents/<slug>.agent.md. Its posture class:
  RO  no edit, execute or retrieval (read-only; may search and hand off)
  RX  execute without edit (runs commands; its shell can still write)
  W   everything else
"""
from __future__ import annotations

import re
from pathlib import Path

WRITE_TOKENS = frozenset({"edit", "execute", "retrieval"})
# canonical token -> Claude tools (agentteams capability_map.py; `retrieval` is a scoped Bash grant)
CLAUDE = {"read": {"Read"}, "edit": {"Edit", "Write"}, "search": {"Grep", "Glob"}, "execute": {"Bash"},
          "todo": {"TodoWrite"}, "agent": {"Task"}, "retrieval": {"Bash(python -m agentteams.research:*)"}}
_TOOLS = re.compile(r"^tools:\s*\[([^\]]*)\]", re.M)


def canonical_tools(path: Path) -> set[str]:
    m = _TOOLS.search(path.read_text(encoding="utf-8"))
    return {t.strip().strip("'\"") for t in m.group(1).split(",") if t.strip()} if m else set()


def canonical_team(root: Path) -> dict[str, set[str]]:
    return {p.name[: -len(".agent.md")]: canonical_tools(p)
            for p in sorted((root / ".github" / "agents").glob("*.agent.md"))}


def posture(tools: set[str]) -> str:
    if not tools & WRITE_TOKENS:
        return "RO"
    return "RX" if "execute" in tools and "edit" not in tools else "W"


def claude_allowed(tools: set[str]) -> set[str]:
    """The Claude tools a canonical declaration grants."""
    return set().union(*(CLAUDE.get(t, set()) for t in tools)) if tools else set()


def claude_tools(path: Path) -> set[str] | None:
    """The Claude tool list, or None when the file has no `tools:` line (the agent inherits every tool)."""
    m = re.search(r"^tools:\s*(.*)$", path.read_text(encoding="utf-8"), re.M)
    return {t.strip() for t in m.group(1).split(",") if t.strip()} if m else None
