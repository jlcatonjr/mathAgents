"""The ``mathagents`` command: run the harness against an instance, and keep an instance current (D35).

  mathagents run [--root DIR] <gate> [args...]   run a gate script against the instance
  mathagents init <dir> [--name NAME] [--agents-to DIR] [--team T] [--exclude A ...] [--namespace NS]
                                                 scaffold an instance (vendored contract files, seeds; never agents)
  mathagents sync [--root DIR] [--write] [--overwrite PATH ...]
                                                 refresh vendored files and exported agents (and, with
                                                 [agents] surfaces, their claude/goose/codex forms)
  mathagents agents export [--root DIR] [--to DIR] [--write]
                                                 render the pipeline agents for the consumer's roster (and,
                                                 without --to, their [agents] surfaces)
  mathagents doctor [--root DIR]                 version, harness, instance, switch, lock status (learned
                                                 blocks excluded and reported), surfaces, the Lean pin (P1-P4)
                                                 and version text in agents and vendored docs that is not the pin
  mathagents status [--root DIR]                 is the architecture on for this machine? (exit 0 on, 3 off);
                                                 also the Lean pin and whether the harness is verified on it
  mathagents bump [--root DIR] {trial,statement-types,statement-drift} [args...]
                                                 the toolchain-bump wave's tools (docs/lean-toolchain-upgrade.md);
                                                 `trial` copies the instance's lean/ to a new directory outside
                                                 its repository and never touches the instance

The instance root is ``--root``, else ``MATHAGENTS_ROOT``, else the nearest ``mathagents.toml`` above the
working directory (a ``[workspace] default`` entry there points at the instance), else this checkout when the
working directory is inside it.
Every file the CLI manages is recorded with its sha256 in ``<instance>/mathagents.lock.json``; a file whose
content no longer matches its lock entry was edited locally and is never overwritten without ``--overwrite``.
For a pipeline agent file the digest leaves out its AGENTTEAMS-LEARNED block, which a re-render carries over
(mathagents/_learned.py); anything else in the file is governed byte for byte. The block's own digest is recorded
under ``learned`` in the lock, so sync and doctor report a block added, changed or removed since the lock.
The architecture is on by default; a machine switches it off with MATHAGENTS_ENABLED=0 in its gitignored
.env (mathagents/config.py). Switched off, `run` refuses with exit 3, so a gate never passes without running.
Exit 0 = done / in sync; 1 = findings (conflicts, pending changes, a failing gate); 2 = usage error;
3 = switched off on this machine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from mathagents import __version__, _harness_files, _scripts
from mathagents import _learned as learned, _surfaces as surfaces
from mathagents.config import DISABLED_EXIT, ENV_KEY, switch

__all__ = ["main"]

LOCK = "mathagents.lock.json"
GATES = {Path(f).stem: f for f in _harness_files.GATE_SCRIPTS if f.endswith((".py", ".sh"))}


# --- instance discovery --------------------------------------------------------------------------------

def find_root(explicit: str | None = None, start: Path | None = None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    if os.environ.get("MATHAGENTS_ROOT"):
        return Path(os.environ["MATHAGENTS_ROOT"]).resolve()
    here = (start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        marker = d / _scripts.INSTANCE_MARKER
        if marker.is_file():
            pointer = tomllib.loads(marker.read_text(encoding="utf-8")).get("workspace", {}).get("default")
            return (d / pointer).resolve() if pointer else d
    if _scripts.IS_CHECKOUT and here.is_relative_to(_scripts.CHECKOUT):
        return _scripts.CHECKOUT
    raise SystemExit("mathagents: no instance found (pass --root, set MATHAGENTS_ROOT, or run `mathagents init`)")


def instance_config(root: Path) -> dict:
    marker = root / _scripts.INSTANCE_MARKER
    return tomllib.loads(marker.read_text(encoding="utf-8")) if marker.is_file() else {}


# --- the lock and managed writes -----------------------------------------------------------------------

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_lock(root: Path) -> dict:
    p = root / LOCK
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"files": {}}


def write_lock(root: Path, lock: dict) -> None:
    lock["mathagents_version"] = __version__
    lock["harness_sha256"] = harness_sha256()
    lock["files"] = dict(sorted(lock["files"].items()))
    if lock.get("learned"):
        lock["learned"] = dict(sorted(lock["learned"].items()))
    else:
        lock.pop("learned", None)
    (root / LOCK).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")


def harness_sha256() -> str:
    return _scripts.gate("instance_root").harness_sha256()


# (parent dir, its dir) of each surface's agent files -> (learned-block host format, file suffix); from SURFACES
_AGENT_HOMES = {tuple(Path(d).parts): (kind, suffix) for d, suffix, kind in surfaces.SURFACES.values()}


def agent_kind(key: str) -> str | None:
    """The learned-block host format of a managed pipeline-agent file (by its lock key), else None: the exported
    ``<name>.agent.md`` and its claude, goose and codex forms. Every other managed file is hashed whole."""
    p = Path(key)
    if p.name.endswith(".agent.md"):
        return learned.MARKDOWN if p.name.removesuffix(".agent.md") in _harness_files.AGENTS else None
    home = _AGENT_HOMES.get(p.parts[-3:-1])
    return home[0] if home and p.stem in _harness_files.AGENTS and p.suffix == home[1] else None


def digest(key: str, data: bytes) -> str:
    """The lock digest of managed file ``key``: its learned block left out for a pipeline-agent file."""
    return learned.digest(data, agent_kind(key))


def learned_change(lock: dict, key: str, data: bytes) -> str | None:
    """``added``, ``changed`` or ``removed`` when agent file ``key``'s learned block differs from the lock's record."""
    kind = agent_kind(key)
    if not kind:
        return None
    now, before = learned.block_digest(data, kind), lock.get("learned", {}).get(key)
    if now is None and (learned.BEGIN_MARKER.encode() in data or learned.END_MARKER.encode() in data):
        return "unsafe (the file reads as an edit)"
    if now == before:
        return None
    return "added" if before is None else "removed" if now is None else "changed"


def record_learned(lock: dict, key: str, data: bytes) -> None:
    kind = agent_kind(key)
    if kind:
        block = learned.block_digest(data, kind)
        if block:
            lock.setdefault("learned", {})[key] = block
        else:
            lock.get("learned", {}).pop(key, None)


def manage(root: Path, lock: dict, target: Path, content: bytes, write: bool, overwrite: set[str]) -> str:
    """Bring one managed file to ``content``: add, ok, update, or conflict (edited locally since the lock).
    A pipeline-agent file's learned block is not compared and is carried into ``content`` on update."""
    key = os.path.relpath(target, root)
    kind = agent_kind(key)
    if target.is_file():
        old = target.read_bytes()
        change = learned_change(lock, key, old)
        if change:  # not hash-governed, but never invisible
            print(f"mathagents: {key}: learned block {change} since the lock (screened; recorded by sync --write)")
        current = digest(key, old)
        if current == digest(key, content):
            lock["files"][key] = current
            if write:
                record_learned(lock, key, old)
            return "ok"
        if current != lock["files"].get(key) and key not in overwrite:
            return "conflict"
        if kind:
            content, problem = learned.carry(old, content, kind)
            if problem:  # never drop an agent's learned block silently
                print(f"mathagents: {key}: {problem}"
                      f"{'; --overwrite drops it' if key in overwrite else '; reconcile it by hand'}")
                if key not in overwrite:
                    return "conflict"
        status = "update"
    else:
        status = "add"
    if write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        lock["files"][key] = digest(key, content)
        record_learned(lock, key, content)
    return status


def report(results: list[tuple[str, str]], write: bool) -> int:
    for status, key in results:
        if status != "ok":
            print(f"{status:9} {key}")
    conflicts = [k for s, k in results if s == "conflict"]
    pending = [k for s, k in results if s in ("add", "update", "untracked")]
    for k in conflicts:
        print(f"mathagents: {k} was edited locally since it was vendored; reconcile it by hand, or pass "
              f"--overwrite {k} to replace it with the harness version")
    if not write and pending:
        print(f"mathagents: {len(pending)} file(s) to add or update; re-run with --write")
    print(f"mathagents: {len(results) - len(conflicts) - len(pending)} in sync, {len(pending)} "
          f"{'written' if write else 'pending'}, {len(conflicts)} conflict(s)")
    return 1 if conflicts or (pending and not write) else 0


# --- agents --------------------------------------------------------------------------------------------

_COMMAND = re.compile(r"\b(?:python3?|bash) scripts/(\w+)\.(?:py|sh)\b")
_LEAN_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*")
_TEAM = re.compile(r"[^\n\r\\\"']{1,80}")


def valid_team(team) -> bool:
    return isinstance(team, str) and bool(_TEAM.fullmatch(team))


_GATE_PATH = re.compile(r"\bscripts/(\w+)\.(?:py|sh)\b")


def instance_libraries(root: Path) -> tuple[str, str] | None:
    """(proved, WIP) lean_lib names of the instance, or None when its lakefile does not follow the rule."""
    try:
        libs, wip = _scripts.gate("proof_integrity").libraries(root / "lean")
    except (OSError, RuntimeError):
        return None
    return next(n for n in libs if n != wip), wip


def render_agent(name: str, root: Path, cfg: dict) -> bytes:
    """A pipeline agent for a consumer roster: gate commands and paths become ``mathagents run <gate>``,
    the Lean library names become the instance's, the team name the consumer's, and a provenance comment
    follows the front matter (agentteams preserves the file as an adopted orphan)."""
    src = (_scripts.HARNESS / ".github" / "agents" / f"{name}.agent.md").read_text(encoding="utf-8")
    try:  # the harness checkout's own learned notes are about mathAgents, not the consumer: never exported
        body = learned.strip(src, learned.MARKDOWN)
    except learned.LearnedBlockError as exc:
        raise SystemExit(f"mathagents: harness agent {name}: {exc}")
    body = _COMMAND.sub(lambda m: f"mathagents run {m.group(1)}", body)
    body = _GATE_PATH.sub(lambda m: f"mathagents run {m.group(1)}" if m.group(1) in GATES else m.group(0), body)
    body = body.replace("`scripts/refresh_agent_surfaces.sh`; maintain the body here",
                        "`mathagents agents export` from the mathAgents harness; maintain the body upstream in mathAgents")
    body = body.replace("scripts/refresh_agent_surfaces.sh", "mathagents agents export")
    # the declaration namespace (`MathAgents.<Slug>.<name>`) first: it need not be the library's name
    namespace = cfg.get("agents", {}).get("namespace")
    if namespace is not None:
        if not isinstance(namespace, str) or not _LEAN_NAME.fullmatch(namespace):
            raise SystemExit(f"mathagents: [agents] namespace {namespace!r} is not a Lean dotted identifier")
        body = re.sub(r"\bMathAgents\.(?=<)", lambda _: f"{namespace}.", body)
    libs = instance_libraries(root) if root != _scripts.CHECKOUT else None
    if libs:
        body = re.sub(r"\bMathAgentsWIP\b", libs[1], body)
        body = re.sub(r"\bMathAgents\b", libs[0], body)
    team = cfg.get("agents", {}).get("team")
    if team is not None and not valid_team(team):
        raise SystemExit(f"mathagents: [agents] team {team!r} must be one line of plain text (no backslash or quotes)")
    if team:
        body = re.sub(r"^(name: .*) — mathAgents$", lambda m: f"{m.group(1)} — {team}", body, count=1, flags=re.M)
    note = (f"<!-- mathagents-export: agent={name} mathagents={__version__} source_sha256={sha(src.encode())}\n"
            "     Generated by `mathagents agents export` from the mathAgents harness (D35). Bespoke custom agent\n"
            "     (adopted orphan): agentteams preserves it verbatim. Do not hand-edit: `mathagents sync --write`\n"
            "     replaces it after an upgrade and refuses if it was edited. Paths under references/, reports/ and\n"
            "     lean/ are relative to the mathAgents instance root (`mathagents doctor`). Before dispatching\n"
            "     this agent, run `mathagents status`: exit 3 means the architecture is switched off on this\n"
            "     machine (MATHAGENTS_ENABLED=0 in .env), so do not dispatch it"
            f"{'; library names were rewritten for ' + ', '.join(libs) if libs else ''}"
            f"{'; declaration namespace ' + namespace if namespace else ''}. -->\n")
    if body.startswith("---\n"):
        end = body.index("\n---\n", 4) + 5
        return (body[:end] + note + body[end:]).encode()
    return (note + body).encode()


def configured_surfaces(cfg: dict) -> list[str]:
    value = cfg.get("agents", {}).get("surfaces", [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise SystemExit("mathagents: [agents] surfaces must be a list such as [\"claude\", \"goose\", \"codex\"]")
    unknown = sorted(set(value) - set(surfaces.SURFACES))
    if unknown:
        raise SystemExit(f"mathagents: [agents] surfaces names {', '.join(unknown)}; one of: {', '.join(surfaces.SURFACES)}")
    return value


def retired_codex_opt_in(cfg: dict) -> str | None:
    """A notice when ``mathagents.toml`` still sets ``[agents] codex_workspace_write`` (retired in 0.2.8: the Codex
    projection takes agentteams' ``sandbox_mode`` and is checked, never narrowed or widened). Ignored, not refused:
    it only ever named agents that declare ``edit``, and no pipeline agent does."""
    if "codex_workspace_write" in cfg.get("agents", {}):
        return ("[agents] codex_workspace_write is retired (0.2.8) and ignored: Codex takes agentteams' "
                "sandbox_mode; remove the line")
    return None


def export_agents(root: Path, lock: dict, dest: Path, write: bool, overwrite: set[str],
                  with_surfaces: bool = False) -> list[tuple[str, str]]:
    """Render the pipeline agents into ``dest``; with ``with_surfaces``, also their ``[agents] surfaces`` forms
    (derived with agentteams and grant-scoped, mathagents/_surfaces.py). Every projection is computed before
    anything is written, so a surface that cannot be scoped leaves every file as it was."""
    out, cfg = [], instance_config(root)
    # `exclude`: e.g. an agent the consumer is the origin of
    renders = {name: render_agent(name, root, cfg) for name in exported_names(cfg)}
    projected: dict[tuple[str, str], bytes] = {}
    wanted = configured_surfaces(cfg) if with_surfaces else []
    if wanted:
        try:
            repo = surfaces.repo_root(dest)
            projected = surfaces.project(renders, wanted, repo=repo, description=repo / "brief.json")
            version = surfaces.agentteams_version() if write else None
        except surfaces.SurfaceError as exc:
            raise SystemExit(f"mathagents: surfaces: {exc}; no agent or surface file was written")
        if notice := retired_codex_opt_in(cfg):
            print(f"mathagents: {notice}")
        if write:
            lock["surfaces"] = {"surfaces": wanted, "agentteams": version, "goose_tool_map": surfaces.GOOSE_MAP_VERSION}
    elif with_surfaces and write:
        lock.pop("surfaces", None)
    for name, content in renders.items():
        target = dest / f"{name}.agent.md"
        out.append((manage(root, lock, target, content, write, overwrite), os.path.relpath(target, root)))
    for (surface, name), content in projected.items():
        target = surfaces.surface_path(repo, surface, name)
        out.append((manage(root, lock, target, content, write, overwrite), os.path.relpath(target, root)))
    return out


ORCHESTRATOR = "orchestrator.agent.md"
_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def exported_names(cfg: dict) -> list[str]:
    """The pipeline agents to export: every one but those ``[agents] exclude`` names (a list of agent names; a
    string or an unknown name is refused rather than silently excluding nothing)."""
    value = cfg.get("agents", {}).get("exclude", [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise SystemExit("mathagents: [agents] exclude must be a list of agent names, "
                         "such as [\"lean-informalization\"]")
    unknown = sorted(set(value) - set(_harness_files.AGENTS))
    if unknown:
        raise SystemExit(f"mathagents: [agents] exclude names no pipeline agent: {', '.join(unknown)} "
                         f"(one of: {', '.join(_harness_files.AGENTS)})")
    return [a for a in _harness_files.AGENTS if a not in value]


def orchestrator_problem(dest: Path) -> str | None:
    """The pipeline agents run only under an orchestrator, which holds the team's write authority and dispatches
    every stage: exported into a directory without one, they would form a team with no one to dispatch them or
    close their work. None when ``dest`` has an orchestrator."""
    if (dest / ORCHESTRATOR).is_file():
        return None
    return (f"no {ORCHESTRATOR} in {dest}: the pipeline agents run only under an orchestrator. Instantiate an "
            "agentteams team there first (`agentteams --description <brief.json> --output <that directory>`), "
            "then export")


def roster_missing(dest: Path, names: list[str]) -> list[str]:
    """Exported agents absent from the orchestrator's ``agents:`` front matter (not yet folded into its roster with
    ``agentteams --adopt-orphans``). Raises OSError when the orchestrator cannot be read."""
    m = _FRONT_MATTER.match((dest / ORCHESTRATOR).read_text(encoding="utf-8"))
    block = re.search(r"^agents:[ \t]*(\[[^\]]*\]|(?:\n[ \t]+-[^\n]*)*)", m.group(1), re.M) if m else None
    listed = set(re.findall(r"[A-Za-z0-9][\w-]*", block.group(1))) if block else set()
    return [n for n in names if n not in listed]


def untrack_withdrawn(root: Path, lock: dict, exported: list[tuple[str, str]], write: bool,
                      dest: Path | None) -> list[tuple[str, str]]:
    """Lock entries of pipeline agents no longer exported (export_to unset, the agent excluded, or its surface
    dropped from [agents] surfaces) are dropped, so `doctor` stops tracking them: those in `dest` or its
    repository's surface directories, or, with export_to unset (`dest` None), anywhere. Their files, if any,
    are left alone: they are the consumer's now, and deleting one is the consumer's decision."""
    kept = {key for _, key in exported}
    where = None
    if dest:
        where = {os.path.relpath(d, root) for d in [dest, *surfaces.surface_dirs(dest)]}
    gone = [k for k in lock["files"] if agent_kind(k) and k not in kept
            and (where is None or os.path.dirname(k) in where)]
    if write:
        for k in gone:
            lock["files"].pop(k)
            lock.get("learned", {}).pop(k, None)
    return [("untracked", k) for k in gone]


# --- the Lean pin (docs/lean-version-governance.md) ----------------------------------------------------

def verified_toolchains() -> list[dict]:
    """The harness's register of verified toolchains (references/verified-toolchains.json in the harness)."""
    path = _scripts.HARNESS / _harness_files.VERIFIED_TOOLCHAINS
    return json.loads(path.read_text(encoding="utf-8")).get("toolchains", [])


def pin_verification(pin: dict) -> tuple[str, bool, str | None]:
    """(``v4.32.1: verified (Mathlib 520045a; harness 0.2.1, 2026-10-06)`` or a NOT-verified line, verified?, the
    register's evidence) for a pin from ``lean_pin.read_pin``. A pin is verified when the register lists its
    toolchain and, when the instance uses Mathlib, its exact Mathlib commit."""
    version, mathlib = pin["toolchain"].rsplit(":", 1)[-1], pin["mathlib_rev"]
    same = [t for t in verified_toolchains() if t.get("toolchain") == pin["toolchain"]]
    hit = next((t for t in same if not pin["uses_mathlib"] or t.get("mathlib_rev") == mathlib), None)
    if hit:
        where = f"Mathlib {mathlib[:7]}; " if mathlib else ""
        return f"{version}: verified ({where}harness {hit.get('harness_version')}, {hit.get('verified')})", True, \
            hit.get("evidence")
    if same:
        return (f"{version}: NOT verified with Mathlib {str(mathlib)[:7]} (the harness is verified on this release with "
                f"Mathlib {', '.join(str(t.get('mathlib_rev'))[:7] for t in same)}); the gates still decide"), False, None
    known = ", ".join(t.get("toolchain", "?").rsplit(":", 1)[-1] for t in verified_toolchains())
    return f"{version}: NOT verified (the harness is verified on {known or 'no toolchain'}); the gates still decide", \
        False, None


def version_text_files(root: Path, lock: dict) -> list[str]:
    """The emitted text `doctor` scans for stale versions: exported pipeline-agent files (every surface) and the
    vendored docs; in the mathAgents checkout, its canonical pipeline agents and the same docs."""
    keys = [k for k in lock.get("files", {}) if agent_kind(k)]
    if root == _scripts.CHECKOUT:
        keys += list(_harness_files.AGENT_FILES)
    keys += [k for k in _harness_files.VENDORED if k.endswith(".md")]
    return [k for k in dict.fromkeys(keys) if (root / k).is_file()]


def pin_report(root: Path, lock: dict) -> tuple[list[str], list[str], list[str]]:
    """(lines to print, problems, warnings) for the instance's Lean pin: P1-P3 problems fail doctor; a Mathlib
    checkout built for another toolchain (P4), an unverified pin and stale version text are warnings."""
    lean_pin = _scripts.gate("lean_pin")
    pin = lean_pin.read_pin(root / "lean")
    if not pin["toolchain"]:
        return [], [], []  # doctor already reports a missing lean/
    findings, notices = lean_pin.pin_findings(pin)
    problems = [f"lean pin: {f}" for f in findings]
    warnings = [f"lean pin: {f}" for f in [lean_pin.checkout_finding(pin)] if f]  # a stale local build
    line, verified, evidence = pin_verification(pin)
    lines = [f"pin:      {line}"] + ([f"          evidence: {evidence}"] if evidence else []) \
        + [f"pin:      note: {n}" for n in notices]
    if not verified:
        warnings.append(f"lean pin: {pin['toolchain']} is not in the harness's register of verified toolchains")
    stale = [f"version text: {key}:{n} names {v}, not the pin {pin['lean_release']}"
             for key in version_text_files(root, lock)
             for n, v in lean_pin.stale_versions((root / key).read_text(encoding="utf-8"), pin["lean_release"])]
    if stale:  # R2: the pin wins; R9: the fix belongs to the text's owner (upstream for harness files)
        lines.append(f"pin:      version text that is not the pin is reported below (R2, R9); a line naming the "
                     f"harness's own pin on purpose carries {lean_pin.HARNESS_PIN_MARKER}")
    return lines, problems, warnings + stale


# --- commands ------------------------------------------------------------------------------------------

def vendor(root: Path, lock: dict, write: bool, overwrite: set[str]) -> list[tuple[str, str]]:
    return [(manage(root, lock, root / rel, (_scripts.HARNESS / rel).read_bytes(), write, overwrite), rel)
            for rel in _harness_files.VENDORED]


def agents_dir(root: Path, cfg: dict, override: str | None) -> Path | None:
    to = override or cfg.get("agents", {}).get("export_to")
    return (root / to).resolve() if to else None


def cmd_run(args) -> int:
    gate = args.gate.replace("-", "_").removesuffix(".py").removesuffix(".sh")
    if gate not in GATES:
        print(f"mathagents: unknown gate {args.gate!r}; one of: {', '.join(sorted(GATES))}")
        return 2
    try:  # a root that is not an instance would make a gate pass on nothing
        root = _scripts.resolve_root(find_root(args.root))
    except FileNotFoundError as exc:
        print(f"mathagents: {exc}")
        return 2
    sw = switch(root=root)
    if not sw.enabled:  # never exit 0: a gate that did not run is not a pass
        print(f"mathagents: {sw.problem or f'switched off on this machine ({ENV_KEY}=0, {sw.source})'}; "
              f"{gate} did not run")
        return DISABLED_EXIT
    script = _scripts.HARNESS / GATES[gate]
    cmd = ([sys.executable, str(script)] if script.suffix == ".py" else ["bash", str(script)]) + args.args
    return subprocess.run(cmd, cwd=root, env=dict(os.environ, MATHAGENTS_ROOT=str(root))).returncode


def cmd_init(args) -> int:
    root = Path(args.dir).resolve()
    if args.team is not None and not valid_team(args.team):
        print(f"mathagents: --team {args.team!r} must be one line of plain text (no backslash or quotes)")
        return 2
    if args.namespace is not None and not _LEAN_NAME.fullmatch(args.namespace):
        print(f"mathagents: --namespace {args.namespace!r} is not a Lean dotted identifier")
        return 2
    unknown = sorted(set(args.exclude or []) - set(_harness_files.AGENTS))
    if unknown:
        print(f"mathagents: --exclude names no pipeline agent: {', '.join(unknown)} (one of: {', '.join(_harness_files.AGENTS)})")
        return 2
    if (root / _scripts.INSTANCE_MARKER).exists():
        print(f"mathagents: {root} is already an instance; use `mathagents sync`")
        return 2
    for d in ("reports/dossiers", "reports/kernel", "references"):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "reports" / "kernel" / ".gitignore").write_text("latest.json\nname-index.txt\n*.tmp\n", encoding="utf-8")
    (root / "reports" / "dossiers" / ".gitkeep").touch()
    for rel in _harness_files.SEEDED:  # instance-owned from here on: seeded once, never synced
        if not (root / rel).exists():
            data = (_scripts.HARNESS / rel).read_text(encoding="utf-8")
            if rel.endswith("axiom-allowlist.json"):  # the instance starts with no G-AX approvals of its own
                allow = json.loads(data)
                allow["approved_axioms"], allow["approvals"] = [], []
                data = json.dumps(allow, indent=2) + "\n"
            (root / rel).write_text(data, encoding="utf-8")
    agents_line = (f"export_to = {json.dumps(args.agents_to)}" if args.agents_to
                   else '# export_to = "../../.github/agents"')
    team_line = f"team = {json.dumps(args.team)}" if args.team else '# team = "baseAgent"'
    exclude_line = (f"exclude = {json.dumps(args.exclude)}" if args.exclude
                    else '# exclude = ["lean-informalization"]')
    namespace_line = f"namespace = {json.dumps(args.namespace)}" if args.namespace else '# namespace = "ZIT"'
    (root / _scripts.INSTANCE_MARKER).write_text(
        "# A mathAgents instance (D35): lean/, reports/dossiers/ and references/ here are checked by the\n"
        "# mathagents harness. Gates: `mathagents run <gate>`. After `pip install -U mathagents`:\n"
        "# `mathagents sync` (dry run), then `mathagents sync --write`.\n"
        f'[instance]\nname = {json.dumps(args.name or root.name)}\ncreated_with = "{__version__}"\n\n'
        f"[agents]\n# where `mathagents sync` keeps the pipeline agents (relative to this file)\n{agents_line}\n"
        f"# the team name in the agents' `name:` lines (default: mathAgents)\n{team_line}\n"
        f"# agents not to export, e.g. one the consumer already maintains\n{exclude_line}\n"
        "# the namespace of dossier declarations (`<namespace>.<Slug>.<name>`; default: the proved library)\n"
        f"{namespace_line}\n"
        "# other agent surfaces sync derives with agentteams and scopes to each agent's tools (export_to must be\n"
        "# a repository's .github/agents; docs/uniform-surface-projection.md)\n"
        '# surfaces = ["claude", "goose", "codex"]\n',
        encoding="utf-8")
    lock = read_lock(root)
    results = vendor(root, lock, True, set())  # never agents: they hold edit/execute grants, so exporting them
    write_lock(root, lock)                      # is a separate, reviewable `sync --write` (or `agents export`)
    report(results, True)
    if args.agents_to:
        print("mathagents: agents are not exported by init; review team/exclude/namespace in mathagents.toml, "
              "then run `mathagents sync --write`")
    if not (root / "lean" / "lakefile.toml").is_file():
        print("mathagents: next, add lean/ (a Lake package with one proved lean_lib and one *WIP lean_lib, "
              "Mathlib as a pinned git dependency, and a lake-manifest.json); see docs/module.md")
    return 0


def cmd_sync(args) -> int:
    root = find_root(args.root)
    lock, overwrite = read_lock(root), set(args.overwrite or [])
    dest = agents_dir(root, instance_config(root), None)
    if dest and (problem := orchestrator_problem(dest)):  # refused before anything is written
        print(f"mathagents: {problem}")
        return 2
    # the export first: its validation (`[agents] exclude`, surfaces) and projection can refuse, and must do so
    # before any vendored file is written
    exported = export_agents(root, lock, dest, args.write, overwrite, with_surfaces=True) if dest else []
    results = vendor(root, lock, args.write, overwrite)
    results += exported + untrack_withdrawn(root, lock, exported, args.write, dest)
    if args.write:
        if not dest:
            lock.pop("surfaces", None)
        write_lock(root, lock)
    return report(results, args.write)


def cmd_agents_export(args) -> int:
    root = find_root(args.root)
    dest = agents_dir(root, instance_config(root), args.to)
    if dest is None:
        print("mathagents: no destination: pass --to DIR or set [agents] export_to in mathagents.toml")
        return 2
    if problem := orchestrator_problem(dest):
        print(f"mathagents: {problem}")
        return 2
    lock = read_lock(root)
    # the configured export also refreshes its [agents] surfaces; a one-off `--to` export touches neither the
    # surfaces nor the configured export's tracking
    results = export_agents(root, lock, dest, args.write, set(args.overwrite or []), with_surfaces=not args.to)
    if not args.to:
        results += untrack_withdrawn(root, lock, results, args.write, dest)
    if args.write:
        write_lock(root, lock)
    return report(results, args.write)


BUMP = {"trial": "bump_trial.sh", "statement-types": "statement_types.py", "statement-drift": "statement_drift.py"}


def git_toplevel(path: Path) -> Path | None:
    r = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(r.stdout.strip()).resolve() if r.returncode == 0 else None


def cmd_bump(args) -> int:
    """The toolchain-bump wave's tools, run from the harness (docs/lean-toolchain-upgrade.md §2). ``trial``
    defaults ``--from`` to the instance's lean/ and refuses a ``--to`` inside the instance or its repository: a
    trial runs on a copy, and the pin files change only on the bump branch after the decision and G-FID gates."""
    try:
        root = _scripts.resolve_root(find_root(args.root))
    except FileNotFoundError as exc:
        print(f"mathagents: {exc}")
        return 2
    sw = switch(root=root)
    if not sw.enabled:
        print(f"mathagents: {sw.problem or f'switched off on this machine ({ENV_KEY}=0, {sw.source})'}; "
              f"bump {args.tool} did not run")
        return DISABLED_EXIT
    rest = list(args.args)
    if args.tool == "trial":
        repeated = sorted({o for o in rest if o.startswith("--") and rest.count(o) > 1})
        if repeated:  # bump_trial.sh keeps the last value, the fence below checks one: allow exactly one
            print(f"mathagents: bump trial: {', '.join(repeated)} given more than once")
            return 2
        if "--from" not in rest:
            rest = ["--from", str(root / "lean"), *rest]
        if "--to" in rest and rest.index("--to") + 1 < len(rest):
            to = Path(rest[rest.index("--to") + 1]).expanduser().resolve()
            for fence in {root, git_toplevel(root)} - {None}:
                if to == fence or to.is_relative_to(fence):
                    print(f"mathagents: bump trial --to {to} is inside {fence}; a trial runs on a copy outside the "
                          "instance and its repository (docs/lean-toolchain-upgrade.md §1)")
                    return 2
    script = _scripts.HARNESS / "scripts" / "toolchain_bump" / BUMP[args.tool]
    cmd = (["bash", str(script)] if script.suffix == ".sh" else [sys.executable, str(script)]) + rest
    # bump_trial.sh calls `python3`: make that this interpreter (a system python3 may predate tomllib). The tool runs
    # in the caller's directory, so relative paths (--to, --patch, --manifest-from) mean what the fence checked
    path = os.pathsep.join([str(Path(sys.executable).parent), os.environ.get("PATH", "")])
    return subprocess.run(cmd, env=dict(os.environ, MATHAGENTS_ROOT=str(root), PATH=path)).returncode


def cmd_status(args) -> int:
    try:  # the same instance `run` and `doctor` use, so the same .env decides
        root = find_root(args.root)
    except SystemExit:  # no instance at all: the working directory's .env, if any
        root = None
    if root is not None:
        try:  # a named root that is not an instance fails here as it does for `run`, never as "on"
            root = _scripts.resolve_root(root)
        except FileNotFoundError as exc:
            print(f"mathagents: {exc}")
            return 2
    sw = switch(root=root)
    if sw.problem:
        print(f"mathagents: off ({sw.problem})")
    else:
        print(f"mathagents: {'on' if sw.enabled else 'off'} ({sw.source})")
    if root is not None and (root / "lean" / "lean-toolchain").is_file():  # informational: never changes the exit
        pin = _scripts.gate("lean_pin").read_pin(root / "lean")
        print(f"pin {pin_verification(pin)[0]}")  # e.g. "pin v4.32.1: verified (Mathlib 520045a; ...)"
    return 0 if sw.enabled else DISABLED_EXIT


def env_is_ignored(path: Path) -> bool:
    r = subprocess.run(["git", "-C", str(path.parent), "check-ignore", "-q", "--", path.name], capture_output=True)
    return r.returncode == 0


def cmd_doctor(args) -> int:
    print(f"mathagents {__version__}")
    print(f"harness:  {_scripts.HARNESS} ({'checkout' if _scripts.IS_CHECKOUT else 'installed'}), "
          f"sha256 {harness_sha256()[:16]}")
    root = find_root(args.root)
    print(f"instance: {root}")
    problems = []
    sw = switch(root=root)
    print(f"switch:   {'on' if sw.enabled else 'off'} ({sw.source})")
    if sw.problem:
        problems.append(sw.problem)
    if sw.source.endswith(".env") and (Path(sw.source).parent / ".git").exists() and not env_is_ignored(Path(sw.source)):
        problems.append(f"{sw.source} is not gitignored: it is machine-local and must never be committed")
    lock = read_lock(root)
    if root != _scripts.CHECKOUT:
        if not (root / _scripts.INSTANCE_MARKER).is_file():
            problems.append(f"no {_scripts.INSTANCE_MARKER}: not an instance")
        if lock.get("mathagents_version") != __version__ or lock.get("harness_sha256") != harness_sha256():
            problems.append(f"lock written by mathagents {lock.get('mathagents_version')} (harness "
                            f"{str(lock.get('harness_sha256'))[:16]}), not this harness; run `mathagents sync`")
        carrying = 0
        for key, locked in lock.get("files", {}).items():
            p = root / key
            data = p.read_bytes() if p.is_file() else None
            if data is None or digest(key, data) != locked:
                problems.append(f"{key}: missing or edited since it was vendored")
            elif agent_kind(key) and learned.BEGIN_MARKER.encode() in data:
                carrying += 1
            if data is not None and (change := learned_change(lock, key, data)):
                print(f"learned:  {key}: block {change} since the lock (not hash-checked; screened; "
                      "`mathagents sync --write` records it)")
        if lock.get("surfaces"):
            s = lock["surfaces"]
            print(f"surfaces: {', '.join(s.get('surfaces', []))} (agentteams {s.get('agentteams')}, Goose tool map "
                  f"{s.get('goose_tool_map')})")
            try:  # the agentteams a sync would project with now, not the one recorded in the lock
                if too_old := surfaces.agentteams_too_old(surfaces.agentteams_version()):
                    problems.append(too_old)
            except surfaces.SurfaceError as exc:
                problems.append(f"surfaces are configured but agentteams is unusable: {exc}")
        if carrying:
            print(f"learned:  {carrying} agent file(s) carry an AGENTTEAMS-LEARNED block (not hash-checked; its "
                  "content is screened with the policy denylist, and a change is reported)")
    cfg = instance_config(root)
    dest = agents_dir(root, cfg, None)
    if dest:
        missing: list[str] = []
        if problem := orchestrator_problem(dest):
            problems.append(problem)
        else:
            try:
                missing = roster_missing(dest, exported_names(cfg))
            except (OSError, UnicodeDecodeError) as exc:
                problems.append(f"{dest / ORCHESTRATOR}: unreadable ({exc})")
            except SystemExit as exc:  # e.g. `[agents] exclude` names no pipeline agent: a problem, not an abort
                problems.append(str(exc).removeprefix("mathagents: "))
        if missing:  # advisory: the fold-in is a reviewed step
            print(f"roster:   not yet in the orchestrator's agents: list: {', '.join(missing)} "
                  "(fold in with `agentteams --adopt-orphans`; route through the orchestrator meanwhile)")
    lean = root / "lean"
    if (lean / "lakefile.toml").is_file():
        try:
            libs, wip = _scripts.gate("proof_integrity").libraries(lean)
            print(f"lean:     libraries {', '.join(libs)} (open work in {wip})")
        except RuntimeError as exc:
            problems.append(f"lean: {exc}")
        if not (lean / "lake-manifest.json").is_file():
            problems.append("lean: no lake-manifest.json (run `lake update` once and commit it)")
    else:
        problems.append("lean: no lean/lakefile.toml")
    lines, pin_problems, warnings = pin_report(root, lock)
    for line in lines:
        print(line)
    problems += pin_problems
    for w in warnings:  # advisory: never changes the exit code
        print(f"  warning: {w}")
    for p in problems:
        print(f"  - {p}")
    print("doctor: " + ("PASS" if not problems else f"{len(problems)} problem(s)")
          + (f", {len(warnings)} warning(s)" if warnings else ""))
    return 1 if problems else 0


def _build_parser() -> argparse.ArgumentParser:
    """The ``mathagents`` argument parser, built without running anything (the docs site reads it)."""
    ap = argparse.ArgumentParser(prog="mathagents", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"mathagents {__version__}")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run", help="run a gate script against the instance")
    p.add_argument("--root", help="the instance root (default: MATHAGENTS_ROOT, else the nearest mathagents.toml, else this checkout)")
    p.add_argument("gate", help="the gate script to run, e.g. check_proof_integrity, validate_dossier, preferences")
    p.add_argument("args", nargs=argparse.REMAINDER, help="arguments passed to the gate script")
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("init", help="scaffold an instance")
    p.add_argument("dir", help="the directory to scaffold the instance in")
    p.add_argument("--name", help="the instance's name (default: the directory name)")
    p.add_argument("--agents-to", help="where sync keeps the pipeline agents, relative to the instance")
    p.add_argument("--team", help="team name in the exported agents' `name:` lines")
    p.add_argument("--exclude", nargs="*", metavar="AGENT", help="agents not to export")
    p.add_argument("--namespace", help="namespace of dossier declarations (a Lean dotted identifier)")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("sync", help="refresh vendored files and exported agents (and their [agents] surfaces)")
    p.add_argument("--root", help="the instance root (default: MATHAGENTS_ROOT, else the nearest mathagents.toml, else this checkout)")
    p.add_argument("--write", action="store_true", help="apply the changes (default: a dry run that lists them)")
    p.add_argument("--overwrite", nargs="*", metavar="PATH", help="files edited locally to overwrite anyway")
    p.set_defaults(func=cmd_sync)
    p = sub.add_parser("agents", help="pipeline agents")
    asub = p.add_subparsers(dest="agents_command", required=True)
    e = asub.add_parser("export", help="render the pipeline agents for a consumer roster (and, without --to, "
                                          "their [agents] surfaces)")
    e.add_argument("--root", help="the instance root (default: MATHAGENTS_ROOT, else the nearest mathagents.toml, else this checkout)")
    e.add_argument("--to", help="a one-off destination directory (default: the agents directory set in mathagents.toml)")
    e.add_argument("--write", action="store_true", help="write the files (default: a dry run that lists them)")
    e.add_argument("--overwrite", nargs="*", metavar="PATH", help="files edited locally to overwrite anyway")
    e.set_defaults(func=cmd_agents_export)
    p = sub.add_parser("status", help="is the architecture on for this machine? (exit 0 on, 3 off); and the Lean pin")
    p.add_argument("--root", help="the instance root (default: MATHAGENTS_ROOT, else the nearest mathagents.toml, else this checkout)")
    p.set_defaults(func=cmd_status)
    p = sub.add_parser("bump", help="the toolchain-bump wave's tools (docs/lean-toolchain-upgrade.md)")
    p.add_argument("--root", help="the instance root (default: MATHAGENTS_ROOT, else the nearest mathagents.toml, else this checkout)")
    p.add_argument("tool", choices=sorted(BUMP), help="the bump tool to run")
    p.add_argument("args", nargs=argparse.REMAINDER, help="arguments passed to the tool")
    p.set_defaults(func=cmd_bump)
    p = sub.add_parser("doctor", help="version, harness, instance, switch, lock status (learned blocks excluded "
                                       "and reported), surfaces, the Lean pin and stale version text")
    p.add_argument("--root", help="the instance root (default: MATHAGENTS_ROOT, else the nearest mathagents.toml, else this checkout)")
    p.set_defaults(func=cmd_doctor)
    return ap


def main(argv: list[str] | None = None) -> int:
    """Run the ``mathagents`` command with ``argv`` (default ``sys.argv[1:]``); returns the exit code."""
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
