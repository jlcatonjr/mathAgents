"""Grant-scoped projection of the pipeline agents onto the other agent surfaces (claude, goose, codex).

The canonical form of a pipeline agent is the Copilot file ``mathagents sync`` renders into ``[agents] export_to``
(``<repo>/.github/agents``). With ``[agents] surfaces = [...]`` set, sync also derives the agent for each named
surface by running ``agentteams --interop-from`` on those renders, then scopes the result to the agent's declared
``tools:`` before it is written and hash-locked like every other managed file:

* **claude** (``<repo>/.claude/agents/<name>.md``): agentteams' ``tools:`` mapping is already exact; it is
  verified, and a projection that grants more than the declared tools, or whose front matter carries any key
  but ``name``, ``description`` and one ``tools`` (``permissionMode``, ``mcpServers``, ``hooks``, ``model``...),
  is refused.
* **goose** (``<repo>/.goose/recipes/<name>.yaml``): agentteams gives every recipe the whole ``developer``
  extension (shell and file writes), and ``summon`` to the agents with handoffs. The ``extensions:`` key is
  replaced with one that lists only the extensions the tools need, each with ``available_tools``
  (GOOSE_TOOL_MAP). A recipe with any other top-level key than ``version``, ``title``, ``description``,
  ``instructions`` and ``extensions`` (``retry``, ``sub_recipes``, ``mcp_servers``...) is refused.
* **codex** (``<repo>/.codex/agents/<name>.toml``): Codex has no per-tool limit, and ``sandbox_mode`` is a
  declaration, not a ceiling (codex-cli drops it for a spawned agent; agentteams labels it "not enforced"). The
  projection is checked, never rewritten, against agentteams' rule (``sandbox_mode_for``): ``workspace-write``
  exactly when the agent declares ``edit``, else ``read-only``. A projection that differs, or carries any key but
  ``name``, ``description``, ``sandbox_mode`` and ``developer_instructions`` (parsed with ``tomllib``), is refused.
  None of the pipeline agents declares ``edit`` (D39), so every one is ``read-only``; real per-role limits on Codex
  come from the launcher and, under agentteams' pilot, its role gate.

``execute`` without ``edit`` still has a write path where the surface's command tool is a general shell: Claude's
``Bash`` and Goose's ``developer.shell``. On those surfaces "commands check, never author" is enforced by the
agent's instructions and by the orchestrator, which alone writes (D39); only Codex ``read-only`` enforces it.

Goose tool names (GOOSE_TOOL_MAP) were checked against Goose 1.37.0, the version the map is pinned to: the
``developer`` platform extension exposes exactly ``write``, ``edit``, ``shell`` and ``tree`` (block/goose v1.37.0,
``crates/goose/src/agents/platform_extensions/developer/mod.rs``), and a recipe run against a local stub model
showed the tool list each scoped recipe offers and that a call to a withheld tool is refused at dispatch
(``docs/uniform-surface-projection.md``). ``available_tools`` is an allowlist, so a Goose release that renames a
tool loses that tool (fails closed); it never gains one.
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import hashlib
import tempfile
import tomllib
from pathlib import Path

from mathagents import _learned as learned

__all__ = ["SURFACES", "GOOSE_TOOL_MAP", "GOOSE_MAP_VERSION", "CLAUDE_TOOL_MAP",
           "SurfaceError", "repo_root",
           "surface_dirs", "surface_path", "declared_tools", "goose_extensions", "scope_goose", "check_claude",
           "check_codex", "MIN_AGENTTEAMS", "version_key", "agentteams_too_old", "agentteams",
           "agentteams_version", "project", "main"]

# surface -> (directory under the repository root, file suffix, learned-block host format). The single source of
# where each surface's agent files live; mathagents.cli derives its lock rules from it.
SURFACES = {
    "claude": (".claude/agents", ".md", learned.MARKDOWN),
    "goose": (".goose/recipes", ".yaml", learned.RECIPE),
    "codex": (".codex/agents", ".toml", learned.TOML),
}
# the only keys a projection may carry; anything else could widen the agent outside its tools (C-3)
CLAUDE_KEYS = frozenset({"name", "description", "tools"})
GOOSE_KEYS = frozenset({"version", "title", "description", "instructions", "extensions"})
CODEX_KEYS = frozenset({"name", "description", "sandbox_mode", "developer_instructions"})

GOOSE_MAP_VERSION = "1.37.0"
# canonical tool token -> the (extension, tool) pairs it grants in Goose 1.37. Goose has no file-read or search
# tool apart from `shell`, so `read`/`search` get the directory tree only: a read-only agent cannot print a
# file's contents on this surface (under-grant, by design). No Goose 1.37 path tool is workspace-confined: `tree`
# lists names and line counts, and `analyze` names and symbols, for any path the user can read (agentteams Goose
# spike, 2026-10-05). So `analyze` is never granted: Goose adds it beside `developer` unless a recipe lists it,
# and an empty allowlist means "no restriction", so every scoped recipe lists it with ANALYZE_OFF, a name no
# tool has (spike A2: the call is refused). Contain `tree` with an OS sandbox (the `exclusive` profile) until a
# workspace-confined read tool replaces it (agentteams_readfs). summon's `load` (which
# reads a named recipe, agent or skill into context, possibly from user-global directories) and `delegate`
# (which starts a subagent) both need `agent`; agentteams 1.0.0rc8 writes Goose handoffs as `load` calls, so an
# agent without `agent` cannot follow a handoff on Goose (under-grant, by design).
GOOSE_TOOL_MAP = {
    "read": (("developer", "tree"),),
    "search": (("developer", "tree"),),
    "edit": (("developer", "write"), ("developer", "edit")),
    "execute": (("developer", "shell"),),
    "agent": (("summon", "delegate"), ("summon", "load")),
}
_GOOSE_EXTENSIONS = {  # extension -> (YAML lines before available_tools, tool order)
    "developer": (("type: builtin", "name: developer", "bundled: true", "timeout: 300"),
                  ("write", "edit", "shell", "tree")),
    "analyze": (("type: platform", "name: analyze"), ("analyze",)),
    "summon": (("type: platform", "name: summon"), ("delegate", "load")),
}
ANALYZE_OFF = "__none__"  # never `[]`: Goose 1.37 reads an empty available_tools as "no restriction" (spike A1)
CLAUDE_TOOL_MAP = {"read": {"Read"}, "search": {"Grep", "Glob"}, "edit": {"Edit", "Write"}, "execute": {"Bash"},
                   "agent": {"Task"}}

_TOOLS = re.compile(r"^tools:[ \t]*(\[.*\])[ \t]*$", re.M)
_TOP_KEY = re.compile(r"^([A-Za-z_][\w-]*)\s*:")


class SurfaceError(RuntimeError):
    """A surface cannot be projected safely (fail-closed: nothing is written)."""


def repo_root(export_dir: Path) -> Path:
    """The repository whose surfaces sit next to ``export_dir``, which must be ``<repo>/.github/agents``."""
    if export_dir.parts[-2:] != (".github", "agents"):
        raise SurfaceError(f"[agents] surfaces needs export_to to be a repository's .github/agents, not {export_dir}")
    return export_dir.parent.parent


def surface_dirs(export_dir: Path) -> list[Path]:
    """The surface directories next to ``export_dir`` (none unless it is a repository's ``.github/agents``)."""
    try:
        repo = repo_root(export_dir)
    except SurfaceError:
        return []
    return [repo / directory for directory, _, _ in SURFACES.values()]


def surface_path(repo: Path, surface: str, name: str) -> Path:
    directory, suffix, _ = SURFACES[surface]
    return repo / directory / f"{name}{suffix}"


def _front_keys(md: str) -> list[tuple[str, str]]:
    """The top-level ``(key, value)`` lines of a Markdown file's YAML front matter, in order (duplicates kept)."""
    front = md.split("\n---\n", 1)[0] if md.startswith("---\n") else ""
    out = []
    for line in front.splitlines()[1:]:
        m = _TOP_KEY.match(line)
        if m and line[0] not in " \t#":
            out.append((m.group(1), line[m.end():].strip()))
        elif line.strip() and line[0] not in " \t#":
            raise SurfaceError(f"unreadable front-matter line {line!r}")
    return out


def declared_tools(agent_md: str) -> list[str]:
    """The canonical ``tools:`` list in a Copilot agent file's front matter."""
    values = [v for k, v in _front_keys(agent_md) if k == "tools"]
    if len(values) != 1 or not _TOOLS.match(f"tools: {values[0]}"):
        raise SurfaceError("expected exactly one `tools: [...]` line in the agent's front matter")
    try:
        tools = ast.literal_eval(values[0])
    except (ValueError, SyntaxError) as exc:
        raise SurfaceError(f"unreadable tools list {values[0]!r}") from exc
    if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
        raise SurfaceError(f"tools must be a list of strings, not {values[0]!r}")
    return tools


def _sections(text: str) -> list[tuple[str, str]]:
    """Top-level YAML sections in order: (key, raw text); comments and blank lines before the first key under ''.

    Every unindented line must be a comment or a plain ``key:``; anything else at column 0 (a quoted key
    ``"retry":``, a merge key ``<<:``, a complex key ``? k``, a document marker, a flow mapping) is refused, so
    no top-level key can slip past the allowlist inside another section's text."""
    out: list[tuple[str, list[str]]] = [("", [])]
    for line in text.splitlines(keepends=True):
        if line[0] == "\t":  # YAML never indents with tabs; refuse rather than guess what a parser makes of it
            raise SurfaceError(f"tab-indented recipe line {line.rstrip()!r}")
        if line.strip() and line[0] not in " #":
            m = _TOP_KEY.match(line)
            if not m:
                raise SurfaceError(f"unreadable top-level recipe line {line.rstrip()!r}")
            out.append((m.group(1), []))
        out[-1][1].append(line)
    return [(k, "".join(v)) for k, v in out if k or v]


def goose_extensions(tools: list[str]) -> str:
    """The ``extensions:`` section granting exactly ``tools`` in Goose 1.37."""
    granted = _granted(tools)
    lines = ["extensions:\n",
             f"  # mathagents: scoped to tools {tools} (Goose {GOOSE_MAP_VERSION} tool names; an extension not\n",
             "  # listed here is not loaded, and a tool not in available_tools is refused)\n"]
    for ext, (head, order) in _GOOSE_EXTENSIONS.items():
        if ext in granted:
            lines.append(f"  - {head[0]}\n")
            lines += [f"    {h}\n" for h in head[1:]]
            allowed = [t for t in order if t in granted[ext]] or sorted(granted[ext])  # ANALYZE_OFF matches no tool
            lines.append(f"    available_tools: [{', '.join(allowed)}]\n")
    return "".join(lines)


def _extension_names(section: str) -> list[str | None]:
    """The ``name`` of each entry in a recipe's ``extensions:`` section, in order; ``None`` for an entry with no
    name of its own. Only two-space ``  - `` items are read, and only a ``name:`` at the entry's own key indent
    counts, so a nested ``name:`` (under ``envs:``, say) can't stand in for it. A section with content but no such
    item fails closed."""
    body = [line for line in section.splitlines()[1:] if line.strip() and not line.lstrip().startswith("#")]
    entries = re.split(r"(?m)^  - ", "\n".join(body))[1:]
    if body and not entries and section.split(":", 1)[1].strip() != "[]":
        raise SurfaceError("the recipe's extensions section has entries mathagents cannot read; "
                           "refused rather than dropped")
    names = []
    for entry in entries:
        m = re.search(r"(?m)^ {4}name: *[\"']?([^\s\"']+)", "    " + entry)
        names.append(m.group(1) if m else None)
    return names


# agentteams >= 1.0.0rc12 (#210) renders Goose recipes in grant mode: the workspace-confined agentteams_readfs server,
# launched exactly like this (agentteams.frameworks.goose_tool_scoping.READFS_SCRIPT, its server pinned by READFS_SHA256).
READFS_SCRIPT = "scripts/goose-readfs-mcp.py"
READFS_SHA256 = "dc8413e8ec16298e79b5ff27e6629c792693ef88bcae4c9f9c40e85d127cab58"
_READFS_BLOCK = ('  - type: stdio\n    name: "agentteams_readfs"\n    cmd: "python3"\n    args:\n      - "-I"\n      - "-S"\n'
                 f'      - "{READFS_SCRIPT}"\n      - "--root"\n      - "."\n    timeout: 300\n'
                 '    available_tools: [read_file, list_dir, find, grep, stat]\n')


def _granted(tools: list[str]) -> dict[str, set[str]]:
    """{extension: tools} mathagents' Goose scoping grants for ``tools``; raises on an unmapped token or a tool set
    that cannot read."""
    unknown = sorted(set(tools) - set(GOOSE_TOOL_MAP))
    if unknown:
        raise SurfaceError(f"no Goose mapping for tool(s) {', '.join(unknown)}")
    if not {"read", "search"} & set(tools):
        # every pipeline agent reads; a tool set that cannot even read is malformed, so it fails closed rather
        # than being scoped (or checked) against whatever its other tokens happen to map to
        raise SurfaceError("an agent without read or search cannot be scoped on Goose")
    granted: dict[str, set[str]] = {}
    for token in tools:
        for ext, tool in GOOSE_TOOL_MAP[token]:
            granted.setdefault(ext, set()).add(tool)
    if "developer" in granted:  # Goose would add `analyze` unrestricted otherwise; it reaches outside the workspace
        granted["analyze"] = {ANALYZE_OFF}
    return granted


def check_goose_grant(recipe: str, tools: list[str]) -> None:
    """Refuse a grant-mode recipe (agentteams >= 1.0.0rc12) whose ``extensions:`` grant anything mathagents' scoping
    would not for ``tools``. Each item must be agentteams_readfs exactly as pinned, or a known extension whose header
    lines are mathagents' (or their first two, type and name: agentteams omits bundled/timeout) and whose
    ``available_tools`` are within its grant; anything else is refused, never dropped.
    Checked, never rewritten: agentteams may grant less (summon [load] without delegate, no developer for read-only)."""
    granted = _granted(tools)
    ext = dict(_sections(recipe)).get("extensions", "")
    body = ext.split("\n", 1)[1] if "\n" in ext else ""
    items = re.split(r"(?m)^(?=  - )", body)
    if items and items[0].strip():
        raise SurfaceError("the grant-mode recipe's extensions section has lines outside its items; refused")
    readfs = 0
    for item in (i for i in items if i.strip()):
        if item == _READFS_BLOCK:
            readfs += 1
            continue
        lines = item.rstrip("\n").split("\n")
        heads = tuple(l.strip().removeprefix("- ") for l in lines[:-1])
        m = re.fullmatch(r"    available_tools: \[([\w, ]*)\]", lines[-1])
        name = next((n for n, (head, _) in _GOOSE_EXTENSIONS.items() if heads in (head, head[:2])), None)
        if m is None or name is None or name not in granted:
            raise SurfaceError(f"the grant-mode recipe carries an extension mathagents does not grant for tools {tools} "
                               f"({heads[:2]}); refused rather than dropped")
        have = {x.strip() for x in m.group(1).split(",") if x.strip()}
        if not have or have - granted[name]:
            raise SurfaceError(f"the grant-mode recipe grants {name} {sorted(have)} beyond {sorted(granted[name])} for "
                               f"tools {tools}; refused rather than dropped")
    if readfs != 1:
        raise SurfaceError("a grant-mode recipe needs exactly one agentteams_readfs entry as pinned; refused rather "
                           "than dropped")


def scope_goose(recipe: str, tools: list[str]) -> str:
    """``recipe`` with its ``extensions:`` section replaced by the scoped one; nothing else changes. A grant-mode
    recipe (agentteams_readfs, agentteams >= 1.0.0rc12) is checked instead and returned unchanged."""
    sections = _sections(recipe)
    keys = [k for k, _ in sections]
    if keys.count("instructions") != 1 or len(set(keys)) != len(keys):
        raise SurfaceError("the recipe does not have one instructions key and unique top-level keys")
    extra = sorted(set(keys) - GOOSE_KEYS - {""})
    if extra:
        raise SurfaceError(f"the recipe carries top-level key(s) {', '.join(extra)} that could act outside its "
                           "tools; only " + ", ".join(sorted(GOOSE_KEYS)) + " are allowed")
    names = _extension_names(dict(sections).get("extensions", "extensions:"))
    if "agentteams_readfs" in names:
        check_goose_grant(recipe, tools)  # grant mode (agentteams >= rc12): never wider than these tools, or refused
        return recipe
    scoped = goose_extensions(tools)
    # an extension this map doesn't produce (an operator MCP server, ...) is refused, never silently dropped: dropping
    # hid a projection that tried to give the agent more than its tools
    for name in names:
        if name not in _GOOSE_EXTENSIONS:
            raise SurfaceError(f"the recipe carries extension {name or '(unnamed)'!r}, which mathagents does not "
                               "grant; refused rather than dropped")
    out = [(k, v) for k, v in sections if k != "extensions"]
    if out[-1][1] and not out[-1][1].endswith("\n"):
        out[-1] = (out[-1][0], out[-1][1] + "\n")
    text = "".join(v for _, v in out) + scoped
    if [k for k, _ in _sections(text)] != [k for k in keys if k != "extensions"] + ["extensions"]:
        raise SurfaceError("scoping the recipe changed its other top-level keys")
    return text


def check_claude(md: str, tools: list[str]) -> None:
    """Refuse a Claude projection that grants a tool the declared tools do not, or carries any other key that
    could widen it (permissionMode, mcpServers, hooks, model, a second tools line...)."""
    keys = _front_keys(md)
    names = [k for k, _ in keys]
    if len(set(names)) != len(names):
        raise SurfaceError(f"the Claude projection repeats a front-matter key ({', '.join(names)})")
    extra = sorted(set(names) - CLAUDE_KEYS)
    if extra:
        raise SurfaceError(f"the Claude projection carries front-matter key(s) {', '.join(extra)}; only "
                           + ", ".join(sorted(CLAUDE_KEYS)) + " are allowed")
    value = dict(keys).get("tools")
    if not value:  # a Claude agent without `tools:` inherits every tool
        raise SurfaceError("the Claude projection has no tools: line (it would inherit every tool)")
    granted = {t.strip() for t in value.split(",") if t.strip()}
    allowed = set().union(*(CLAUDE_TOOL_MAP.get(t, set()) for t in tools))
    if granted - allowed:
        raise SurfaceError(f"the Claude projection grants {sorted(granted - allowed)} beyond tools {tools}")


def check_codex(toml: str, tools: list[str]) -> None:
    """Refuse a Codex projection that does not parse, carries a key beyond CODEX_KEYS, or whose ``sandbox_mode``
    is not agentteams' value for the declared tools: ``workspace-write`` exactly when they include ``edit``, else
    ``read-only`` (agentteams ``sandbox_mode_for``). Checked, never rewritten."""
    try:
        data = tomllib.loads(toml)
    except tomllib.TOMLDecodeError as exc:
        raise SurfaceError(f"the Codex projection does not parse ({exc})") from exc
    extra = sorted(set(data) - CODEX_KEYS)
    if extra:
        raise SurfaceError(f"the Codex projection carries key(s) {', '.join(extra)}; only "
                           + ", ".join(sorted(CODEX_KEYS)) + " are allowed")
    want = "workspace-write" if "edit" in tools else "read-only"
    if data.get("sandbox_mode") != want:
        raise SurfaceError(f"Codex sandbox_mode {data.get('sandbox_mode')!r}; agentteams' rule for tools "
                           f"{tools} is {want!r}")


def agentteams() -> list[str]:
    cmd = os.environ.get("MATHAGENTS_AGENTTEAMS") or shutil.which("agentteams")
    if not cmd or not os.access(cmd, os.X_OK):
        raise SurfaceError(f"agentteams {'at ' + cmd + ' is not executable' if cmd else 'is not installed'} "
                           "(needed for [agents] surfaces; install researchteam[update], or point "
                           "MATHAGENTS_AGENTTEAMS at it)")
    return [cmd]


# The oldest agentteams whose interop this projection is written against: 1.0.0rc9 (9928a3a) carries #174, the
# write-policy carry into imported agents that scripts/refresh_agent_surfaces.sh relies on.
MIN_AGENTTEAMS = "1.0.0rc9"
# From agentteams 1.0.0rc12 (#210) Codex interop refuses the pipeline agents' narrow grants (Codex does not enforce
# them). agentteams 1.1.0rc17 (#319) accepts codex as an interop target under write_policy "orchestrator-only", but only
# into the project's native Codex team (its build-log, role gate, hooks and launcher; require_native_codex_gate). So the
# codex surface is allowed exactly when the installed agentteams has that capability (codex_interop_supported), not by
# version: a version regex can't order 1.1.0.dev0 or a vcs-pinned build. These are the native team's files the
# projection stages, at their project paths, so the import runs against the instance's own enforcement.
CODEX_NATIVE_FILES = (".codex/agents/references/build-log.json", ".agentteams/bin/codex-role-gate.py",
                      ".codex/hooks.json", ".codex/confined-run.example.sh")
_CODEX_PROBE = ("import agentteams.interop_write_policy as i; "
                "print('yes' if 'codex' in i.SUPPORTED and hasattr(i, 'require_native_codex_gate') else 'no')")
_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:-?(a|b|rc)\.?(\d+)|\.?(dev)\.?(\d+))?(?=$|[\s+(])")


def version_key(version: str) -> tuple[int, ...] | None:
    """A sortable key for an agentteams version (``1.0.0rc9``, ``1.0.0-rc.9``, ``1.1.0.dev0``, ``1.0.0``; a release
    sorts after its pre-releases, a development build before them), from the first token of ``agentteams --version``; None when it does not parse."""
    m = _VERSION.match(version.strip())
    if not m:
        return None
    if m.group(6):  # a development build sorts before every pre-release of its version (PEP 440)
        return (*map(int, m.group(1, 2, 3)), -1, int(m.group(7)))
    rank = {"a": 0, "b": 1, "rc": 2, None: 3}[m.group(4)]
    return (*map(int, m.group(1, 2, 3)), rank, int(m.group(5) or 0))


def agentteams_too_old(version: str) -> str | None:
    """Why ``version`` cannot be used (older than MIN_AGENTTEAMS, or unparsable), else None."""
    key = version_key(version)
    if key is None:
        return f"agentteams version {version!r} does not parse; need {MIN_AGENTTEAMS} or later"
    if key < version_key(MIN_AGENTTEAMS):
        return f"agentteams {version} is older than {MIN_AGENTTEAMS}, the oldest this projection supports"
    return None


def agentteams_version() -> str:
    try:
        r = subprocess.run(agentteams() + ["--version"], capture_output=True, text=True)
    except OSError as exc:
        raise SurfaceError(f"agentteams --version: {exc}") from exc
    if r.returncode != 0:
        raise SurfaceError(f"agentteams --version failed ({r.returncode}): {(r.stderr or r.stdout).strip()[-200:]}")
    return (r.stdout.strip() or r.stderr.strip() or "unknown").splitlines()[-1].removeprefix("agentteams ")


def _agentteams_python(cmd: list[str]) -> str:
    """The interpreter the agentteams executable runs under (its ``#!`` line), so a capability probe reads the same
    agentteams the projection will run, not whatever this interpreter can import. MATHAGENTS_AGENTTEAMS_PYTHON
    overrides it (an agentteams installed as a binary wrapper, and the tests' stand-in)."""
    if override := os.environ.get("MATHAGENTS_AGENTTEAMS_PYTHON"):
        # Only mathagents' early refusal reads it; agentteams' own gate (#210, require_native_codex_gate) still decides.
        print(f"mathagents: surfaces: MATHAGENTS_AGENTTEAMS_PYTHON={override} overrides the agentteams capability probe",
              file=sys.stderr)
        return override
    try:
        with open(cmd[0], "rb") as fh:
            first = fh.readline().decode("utf-8", "replace").strip()
    except OSError as exc:
        raise SurfaceError(f"cannot read the agentteams executable {cmd[0]} ({exc})") from exc
    if not first.startswith("#!"):
        raise SurfaceError(f"cannot tell which Python runs agentteams ({cmd[0]} has no #! line)")
    parts = first[2:].split()
    if parts and os.path.basename(parts[0]) == "env":
        parts = parts[1:]
    if not parts:
        raise SurfaceError(f"cannot tell which Python runs agentteams ({cmd[0]})")
    return parts[0]


def codex_interop_supported(cmd: list[str]) -> bool:
    """Whether the installed agentteams accepts codex as an interop target under write_policy (agentteams #319:
    ``interop_write_policy.SUPPORTED`` names codex and ``require_native_codex_gate`` exists)."""
    try:
        r = subprocess.run([_agentteams_python(cmd), "-I", "-c", _CODEX_PROBE], capture_output=True, text=True)
    except OSError as exc:
        raise SurfaceError(f"agentteams capability probe: {exc}") from exc
    return r.returncode == 0 and r.stdout.strip() == "yes"


def _stage_native_codex(repo: Path, proj: Path | None) -> None:
    """Copy the instance's native Codex team files (CODEX_NATIVE_FILES) into the staging project ``proj``, so
    agentteams' gate checks the instance's own enforcement. Raise, naming what is missing, when the instance has
    no native Codex team rendered under the switch; a symlink is not followed (the gate refuses it). With ``proj``
    None, only check."""
    missing = [rel for rel in CODEX_NATIVE_FILES if (repo / rel).is_symlink() or not (repo / rel).is_file()]
    if missing:
        raise SurfaceError("the codex surface imports into this project's native Codex team, rendered under "
                           'write_policy "orchestrator-only" (agentteams #319); missing: ' + ", ".join(missing)
                           + ". Put codex in brief.json write_policy_frameworks and render it first: "
                           "agentteams --description brief.json --framework codex")
    if proj is None:  # check only
        return
    for rel in CODEX_NATIVE_FILES:
        (proj / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / rel, proj / rel)


def _native_codex_unchanged(repo: Path, proj: Path) -> None:
    """After the import, the instance's real gate files must still equal the staged copies the gate checked."""
    changed = [rel for rel in CODEX_NATIVE_FILES if rel != CODEX_NATIVE_FILES[0] and
               ((repo / rel).is_symlink() or not (repo / rel).is_file()
                or hashlib.sha256((repo / rel).read_bytes()).digest() != hashlib.sha256((proj / rel).read_bytes()).digest())]
    if changed:
        raise SurfaceError("the native Codex team changed while it was projected (" + ", ".join(changed) + "); "
                           "nothing was written")


def _pinned_readfs() -> str:
    """agentteams' shipped readfs server, only when it matches READFS_SHA256 (internal agentteams accessor, guarded by
    tests/test_surfaces.py; no public one before agentteams 1.1, GOOSE-READFS-PUBLIC-ACCESSOR)."""
    try:
        from agentteams.frameworks.goose_docs import pinned_readfs_mcp_content
        from agentteams.frameworks.goose_tool_scoping import READFS_SHA256 as pinned
        content = pinned_readfs_mcp_content()
    except (ImportError, ValueError, OSError) as exc:
        raise SurfaceError(f"agentteams' pinned goose readfs server is unavailable ({exc})") from exc
    if pinned != READFS_SHA256 or hashlib.sha256(content.encode("utf-8")).hexdigest() != READFS_SHA256:
        raise SurfaceError("agentteams' goose readfs server does not match the pin mathagents was checked against "
                           f"({READFS_SHA256[:12]}); update mathagents with agentteams")
    return content


def project(renders: dict[str, bytes], surfaces: list[str], repo: Path | None = None,
            description: Path | None = None) -> dict[tuple[str, str], bytes]:
    """Derive and scope each rendered Copilot agent for each surface: ``{(surface, agent): bytes}``. Raises
    SurfaceError, before anything is written, when agentteams fails or a projection cannot be scoped. The codex
    surface needs ``repo`` (its native Codex team is staged) and ``description`` (the brief whose write_policy
    covers codex); every projection still runs in a temporary directory."""
    unknown = sorted(set(surfaces) - set(SURFACES))
    if unknown:
        raise SurfaceError(f"unknown surface(s) {', '.join(unknown)}; one of {', '.join(SURFACES)}")
    out: dict[tuple[str, str], bytes] = {}
    if not surfaces or not renders:
        return out
    tools = {name: declared_tools(data.decode("utf-8")) for name, data in renders.items()}
    cmd = agentteams()
    version = agentteams_version()
    if problem := agentteams_too_old(version):
        raise SurfaceError(problem)
    if "codex" in surfaces:
        if not codex_interop_supported(cmd):
            raise SurfaceError(f"agentteams {version} cannot import into Codex under write_policy (it needs agentteams "
                               "#319, in 1.1.0rc17 and later; #210 refuses the pipeline agents' narrow grants without "
                               'it): remove "codex" from [agents] surfaces in mathagents.toml, or update agentteams')
        if repo is None:
            raise SurfaceError("the codex surface needs the project root (its native Codex team is staged)")
        _stage_native_codex(Path(repo), None)  # refuses, naming the missing files, before agentteams runs
        if description is None or not Path(description).is_file():
            raise SurfaceError("the codex surface needs the project's brief.json (its write_policy must cover codex)")
    with tempfile.TemporaryDirectory(prefix="mathagents-surfaces-") as tmp:
        src = Path(tmp) / "src"
        src.mkdir()
        for name, data in renders.items():
            (src / f"{name}.agent.md").write_bytes(data)
        for surface in surfaces:
            dest = Path(tmp) / surface
            extra: list[str] = []
            if surface == "goose":  # agentteams >= rc12 refuses unless its pinned readfs server is in the output project
                proj, dest = dest, dest / ".goose" / "recipes"
                (proj / "scripts").mkdir(parents=True)
                (proj / READFS_SCRIPT).write_text(_pinned_readfs(), encoding="utf-8")
            elif surface == "codex":  # #319: only into the native team, staged here with its gate files
                proj, dest = dest, dest / ".codex" / "agents"
                _stage_native_codex(Path(repo), proj)
                extra = ["--description", str(Path(description).resolve()), "--overwrite"]
            try:
                r = subprocess.run(cmd + ["--interop-from", str(src), "--framework", surface, "--output",
                                          str(dest), *extra, "--yes"], capture_output=True, text=True)
            except OSError as exc:
                raise SurfaceError(f"agentteams: {exc}") from exc
            if surface == "codex" and r.returncode == 0:
                _native_codex_unchanged(Path(repo), proj)
            if r.returncode != 0:
                raise SurfaceError(f"agentteams --interop-from --framework {surface} failed ({r.returncode}): "
                                   f"{(r.stderr or r.stdout).strip()[-400:]}")
            for name in renders:
                f = dest / f"{name}{SURFACES[surface][1]}"
                if not f.is_file():
                    raise SurfaceError(f"agentteams wrote no {surface} file for {name}")
                text = f.read_text(encoding="utf-8")
                try:
                    if surface == "goose":
                        text = scope_goose(text, tools[name])
                    elif surface == "claude":
                        check_claude(text, tools[name])
                    else:
                        check_codex(text, tools[name])
                except SurfaceError as exc:
                    raise SurfaceError(f"{surface} {name}: {exc}") from exc
                out[(surface, name)] = text.encode("utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """``python -m mathagents._surfaces scope-goose AGENTS_DIR RECIPES_DIR NAME...``: scope the Goose recipes of
    the named agents in place from their canonical ``AGENTS_DIR/<name>.agent.md`` tools (the mathAgents checkout's
    own refresh, scripts/refresh_agent_surfaces.sh). Exit 1, changing nothing, if any recipe cannot be scoped."""
    import sys
    args = sys.argv[1:] if argv is None else argv
    if len(args) < 4 or args[0] != "scope-goose":
        print(main.__doc__)
        return 2
    agents, recipes, names = Path(args[1]), Path(args[2]), args[3:]
    out = {}
    try:
        for name in names:
            tools = declared_tools((agents / f"{name}.agent.md").read_text(encoding="utf-8"))
            out[name] = scope_goose((recipes / f"{name}.yaml").read_text(encoding="utf-8"), tools)
    except (OSError, SurfaceError) as exc:
        print(f"scope-goose: {name}: {exc}; nothing was changed")
        return 1
    for name, text in out.items():  # each file replaced atomically; every recipe was scoped before any is written
        tmp = recipes / f".{name}.yaml.scoping"
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, recipes / f"{name}.yaml")
    print(f"scope-goose: scoped {len(out)} recipe(s) to Goose {GOOSE_MAP_VERSION} tool names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
