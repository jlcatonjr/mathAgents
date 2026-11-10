#!/usr/bin/env python3
"""Codex session preflight: check that each agent's declared capability holds on the Codex surface,
and turn any problem into a feedback request for agentteams (IA-02; operator decision D-c).

  codex_preflight.py                       static checks of .codex/agents against the canonical team
  codex_preflight.py --live --agent SLUG   also probe what the running sandbox enforces for SLUG
                                           (only agents granted `execute`; C-3 bars read-only roles)
  options: --root DIR (tests), --no-write (print only; never write the request file)

Postures come from the canonical `tools:` list in .github/agents/<slug>.agent.md:
  RO  no edit, execute or retrieval      Codex must set sandbox_mode = "read-only"
  RX  execute without edit               Codex must declare a sandbox_mode (the shell can write)
  W   everything else                    not checked here
The live probe creates and removes one sentinel file at the repository root, so it runs only as an
agent whose canonical tools include `execute`. An agent whose Codex file sets sandbox_mode =
"read-only" yet can create the sentinel shows that the per-agent sandbox_mode is a default, not a
ceiling; the same mechanism then applies to every read-only role.

New findings (deduplicated by fingerprint against earlier drafts and forwarded requests) are written
as a draft request to agentteams in references/agentteams-feedback/, a user-owned folder that updates
never overwrite. @repo-liaison forwards each draft through
.github/agents/references/cross-orchestrator-requests/; the fix arrives through an agentteams or
researchteam update, never a hand edit. When the sandbox blocks that write, the draft is printed instead,
to be saved by the user.
Exit 0 = no findings; 1 = findings; 2 = error.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from agent_postures import canonical_team as canonical, posture  # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    print("codex_preflight: needs Python 3.11+ (tomllib)", file=sys.stderr)
    sys.exit(2)

class UsageError(Exception):
    pass


DRAFTS = Path("references/agentteams-feedback")  # user-owned; @repo-liaison forwards to agentteams
FORWARDED = Path(".github/agents/references/cross-orchestrator-requests")
FP_LINE = re.compile(r"^- fingerprint: `([0-9a-f]{12})`", re.M)


def finding(check: str, subject: str, severity: str, text: str) -> dict:
    fp = hashlib.sha256(f"{check}:{subject}".encode()).hexdigest()[:12]
    return {"check": check, "subject": subject, "severity": severity, "text": text, "fingerprint": fp}


def static_checks(root: Path, team: dict[str, set[str]]) -> list[dict]:
    out = []
    codex = {}
    for p in sorted((root / ".codex/agents").glob("*.toml")):
        try:
            data = tomllib.loads(p.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            out.append(finding("parse", p.name, "high", f"{p.name} does not parse: {exc}"))
            continue
        name = str(data.get("name") or p.stem)
        if name in codex:
            out.append(finding("roster", name, "medium", f"two Codex agents are named `{name}` ({p.name})"))
        codex[name] = data
    for slug in sorted(set(team) - set(codex)):
        out.append(finding("roster", slug, "medium", f"`{slug}` is in the canonical team but has no Codex agent"))
    for slug in sorted(set(codex) - set(team)):
        out.append(finding("roster", slug, "low", f"Codex agent `{slug}` has no canonical agent (orphan)"))
    for slug in sorted(set(team) & set(codex)):
        cls, mode = posture(team[slug]), codex[slug].get("sandbox_mode")
        if mode == "danger-full-access":
            out.append(finding("sandbox", slug, "high", f"`{slug}` sets sandbox_mode = \"danger-full-access\" (D34)"))
        elif cls == "RO" and mode != "read-only":
            out.append(finding("sandbox", slug, "high",
                               f"`{slug}` is read-only (tools {sorted(team[slug])}) but its Codex sandbox_mode is "
                               f"{mode!r}; it inherits the session's sandbox and can write (C-3)"))
        elif cls == "RX" and mode is None:
            out.append(finding("sandbox", slug, "medium",
                               f"`{slug}` runs commands without edit rights (tools {sorted(team[slug])}) but declares no "
                               "Codex sandbox_mode; its shell can write wherever the session allows"))
    built = (root / ".codex/agents/references/build-log.json")
    try:
        want = json.loads(built.read_text(encoding="utf-8")).get("agentteams_version")
    except (OSError, ValueError):
        want = None
    try:
        from importlib.metadata import PackageNotFoundError, version
        have = version("agentteams")
    except PackageNotFoundError:
        have = None
    if want and have and have != want:
        out.append(finding("version", f"{have}->{want}", "low",
                           f"agentteams {have} is installed in this interpreter, but .codex was built with {want}"))
    return out


def live_check(root: Path, team: dict[str, set[str]], slug: str) -> tuple[list[dict], str]:
    if slug not in team:
        raise UsageError(f"--agent {slug!r} is not a canonical agent")
    if "execute" not in team[slug]:
        raise UsageError(f"--agent {slug!r} is not granted `execute`; a read-only role never runs the probe (C-3)")
    toml = root / ".codex/agents" / f"{slug}.toml"
    try:
        mode = tomllib.loads(toml.read_text(encoding="utf-8")).get("sandbox_mode")
    except (OSError, tomllib.TOMLDecodeError):
        mode = None
    sentinel = root / f".codex-preflight-{os.getpid()}.tmp"
    try:
        sentinel.write_text("codex preflight sentinel\n", encoding="utf-8")
        writable = True
    except OSError:
        writable = False
    left = []
    if writable:
        try:
            sentinel.unlink()
        except OSError as exc:
            left = [finding("sentinel", slug, "low", f"could not remove {sentinel.name}: {exc}; delete it by hand")]
    env = ", ".join(f"{k}={os.environ[k]}" for k in sorted(os.environ) if k.startswith("CODEX_")) or "none"
    note = (f"live probe as `{slug}` (sandbox_mode {mode!r}): repository "
            f"{'writable' if writable else 'not writable'}; CODEX_* env: {env}")
    if writable and mode == "read-only":
        return left + [finding("ceiling", slug, "high",
                               f"`{slug}` has sandbox_mode = \"read-only\", yet it could write to the repository: "
                               "per-agent sandbox_mode is not a ceiling here, so no read-only role is confined "
                               f"by its own setting (CODEX_* env: {env})")], note
    return left, note


def known_fingerprints(root: Path) -> set[str]:
    seen: set[str] = set()
    for folder in (DRAFTS, FORWARDED):
        for p in (root / folder).glob("*-agentteams-codex-preflight-*.md"):
            seen |= set(FP_LINE.findall(p.read_text(encoding="utf-8")))
    return seen


def head(root: Path) -> str:
    r = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def request(root: Path, new: list[dict], notes: list[str]) -> str:
    today = dt.date.today().isoformat()
    lines = [
        "# Request to agentteams: Codex capability findings from a preflight run", "",
        "- **From:** mathAgents (scripts/codex_preflight.py, run in a Codex session)",
        "- **To:** agentteams orchestrator",
        f"- **Date:** {today}",
        f"- **Commit:** `{head(root)}`",
        "- **Type:** defect report, draft. `@repo-liaison` reviews and forwards it. agentteams owns the fix,",
        "  and it reaches this repository through an agentteams or researchteam update; generated",
        "  infrastructure is never hand-edited.", "",
        "## Findings", "",
    ]
    for f in new:
        lines += [f"### {f['severity'].upper()}: {f['check']} `{f['subject']}`", "", f["text"], "",
                  f"- fingerprint: `{f['fingerprint']}`", ""]
    if notes:
        lines += ["## Environment", ""] + [f"- {n}" for n in notes] + [""]
    lines += ["## Request", "",
              "Project each agent's canonical posture onto Codex so that it holds: read-only agents get",
              "`sandbox_mode = \"read-only\"`, and agents that run commands declare their sandbox. Where Codex",
              "cannot enforce a posture, say so in the agent file. See the IA-02 remediation plan in mathAgents.", ""]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--agent")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    if args.live != bool(args.agent):
        ap.error("--live and --agent go together")
    root = args.root.resolve()
    if not (root / ".github/agents").is_dir() or not (root / ".codex/agents").is_dir():
        print(f"codex_preflight: no .github/agents or .codex/agents under {root}", file=sys.stderr)
        return 2
    team = canonical(root)
    found, notes = static_checks(root, team), []
    if args.live:
        try:
            live, note = live_check(root, team, args.agent)
        except UsageError as exc:
            print(f"codex_preflight: {exc}", file=sys.stderr)
            return 2
        found += live
        notes.append(note)
        print(f"[codex-preflight] {note}")
    for f in found:
        print(f"[codex-preflight] {f['severity'].upper():6} {f['text']}")
    if not found:
        print("[codex-preflight] no findings")
        return 0
    known = known_fingerprints(root)
    new = [f for f in found if f["fingerprint"] not in known]
    if not new:
        print(f"[codex-preflight] {len(found)} finding(s), all already reported to agentteams")
        return 1
    body = request(root, new, notes)
    name = f"{dt.date.today().isoformat()}-agentteams-codex-preflight-{new[0]['fingerprint']}.md"
    target = root / DRAFTS / name
    if not args.no_write:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            print(f"[codex-preflight] {len(new)} new finding(s) written to {target.relative_to(root)}; "
                  "commit it and tell the operator (@repo-liaison forwards it to agentteams)")
            return 1
        except OSError as exc:
            print(f"[codex-preflight] could not write {target.relative_to(root)}: {exc}")
    print(f"[codex-preflight] {len(new)} new finding(s). The sandbox blocked the request file (or --no-write);"
          f" save the text below as {DRAFTS / name} and send it to the operator:\n")
    print(body)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
