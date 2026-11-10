#!/usr/bin/env python3
"""Print, and check, the agentteams code a render is about to run (refresh_agent_surfaces.sh, before step 1).

researchteam drives the first `agentteams` on PATH. Which code that is depends on how it was installed (PEP 610
direct_url.json): an EDITABLE install runs a source checkout, which on this workspace is shared and switched
between branches by other sessions; a VCS install is pinned to a commit; a non-editable install from a local folder
is a frozen snapshot of whatever that folder held at install time. A render must run reviewed code, so:
  editable          refused unless the checkout's HEAD is on its origin/main and the imported package directory has no
                    uncommitted or untracked sources (bytecode caches excepted);
  vcs / released    passes, naming the source and commit or version;
  local snapshot    refused unless MATHAGENTS_ALLOW_AGENTTEAMS_SNAPSHOT=1: it cannot be verified after the fact, and
                    a stale snapshot (researchteam/.venv at 5090eb0, from before agentteams PR #106) is what dropped
                    the adopted routing rows in v0.2.6's render (CA-033, reproduced by agentteams-a9).

Two stages: run by any Python, it finds the interpreter the `agentteams` launcher uses (a direct shebang, an
`#!/usr/bin/env python3` shebang, or pip's `#!/bin/sh` trampoline for long interpreter paths) and re-runs itself
there with --inner, so the install it inspects is the one the launcher imports.
With a toolchain.lock at the repository root (next to scripts/; MATHAGENTS_TOOLCHAIN_LOCK names another file, for tests), the render
must run exactly the locked agentteams commit (the 1.0 line pins a release, D43): a VCS install at that commit, or an
editable checkout whose HEAD is that commit (a detached release checkout; it need not be on origin/main). A released
package or a snapshot cannot show its commit and is refused. MATHAGENTS_ALLOW_UNLOCKED_AGENTTEAMS=1 accepts a mismatch
knowingly, with a warning. Without a lock the checks above apply unchanged.
Exit 0 = OK to render; 1 = refused; 127 = agentteams not installed.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TAG = "agentteams_provenance"


def launcher_interpreter(exe: str) -> str | None:
    """The interpreter `exe` runs under, from its shebang (direct, env-style) or pip's /bin/sh trampoline."""
    try:
        head = Path(exe).read_text(encoding="utf-8", errors="replace").splitlines()[:3]
    except OSError:
        return None
    if not head or not head[0].startswith("#!"):
        return None
    parts = head[0][2:].strip().split()
    if not parts:
        return None
    if Path(parts[0]).name == "env":
        args = [a for a in parts[1:] if not a.startswith("-")]
        return shutil.which(args[0]) if args else None
    if Path(parts[0]).name in ("sh", "bash") and len(head) > 1:  # pip: '''exec' "/long/path/python" "$0" "$@"
        # a quoted interpreter path may contain spaces; an unquoted one stops at the first space (and then fails
        # the os.access check below: a refusal, never a wrong interpreter)
        m = re.search(r"exec'?\s+(?:\"([^\"]+)\"|(\S+))\s+\"\$0\"", head[1])
        return (m.group(1) or m.group(2)) if m else None
    return parts[0]


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    except OSError as exc:  # git missing: a failure the caller refuses on, never a pass
        return subprocess.CompletedProcess(["git", *args], 127, "", str(exc))


def refuse(msg: str) -> int:
    print(f"{TAG}: REFUSED: {msg}", file=sys.stderr)
    return 1


LOCK = Path(__file__).resolve().parents[2] / "toolchain.lock"  # the repository root, wherever the caller runs


def lock_path() -> Path:
    return Path(os.environ["MATHAGENTS_TOOLCHAIN_LOCK"]) if os.environ.get("MATHAGENTS_TOOLCHAIN_LOCK") else LOCK


def locked_commit(lock: Path | None = None, name: str = "agentteams") -> str | None:
    """The commit toolchain.lock pins for `name` (`<name>=<owner>/<name>@<sha>`), or None without a lock.
    Raises ValueError on a lock that names no well-formed commit for `name`. Other keys (researchteam's
    `<name>.tag=` lines) are ignored."""
    lock = lock_path() if lock is None else lock
    if not lock.is_file():
        return None
    for line in lock.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and line.split("=", 1)[0].strip() == name:
            m = re.fullmatch(rf"{name}\s*=\s*[\w.-]+/{name}@([0-9a-f]{{40}})", line)
            if not m:
                raise ValueError(f"{lock}: malformed {name} line: {line!r} (want {name}=<owner>/{name}@<40-hex>)")
            return m.group(1)
    raise ValueError(f"{lock}: no {name} line")


def against_lock(commit: str | None, what: str, want: str | None | bool = False) -> int:
    """0 when no lock is present or `commit` is the locked one; otherwise a refusal (or a warning when accepted).
    `want` is the locked commit when the caller already read it (False: read it here)."""
    if want is False:
        try:
            want = locked_commit()
        except ValueError as exc:
            return refuse(str(exc))
    if want is None or commit == want:
        if want:
            print(f"{TAG}: matches toolchain.lock (agentteams {want[:12]})")
        return 0
    msg = (f"{what} is agentteams {commit[:12] if commit else 'at an unknown commit'}, but toolchain.lock pins "
           f"{want[:12]}; install the locked commit (or check it out detached) before rendering")
    if os.environ.get("MATHAGENTS_ALLOW_UNLOCKED_AGENTTEAMS") == "1":
        print(f"{TAG}: WARNING: {msg} (accepted: MATHAGENTS_ALLOW_UNLOCKED_AGENTTEAMS=1)", file=sys.stderr)
        return 0
    return refuse(msg)


def inner(exe: str) -> int:
    """Run under the launcher's interpreter: classify the install and check an editable checkout."""
    from importlib import metadata
    from urllib.parse import unquote, urlparse
    try:
        dist = metadata.distribution("agentteams")
        direct = json.loads(dist.read_text("direct_url.json") or "{}")
    except metadata.PackageNotFoundError:
        dist, direct = None, {"dir_info": {"editable": True}}  # a bare source tree on sys.path: check it as editable
    except (OSError, ValueError) as exc:
        return refuse(f"cannot read the agentteams install record ({exc})")
    if not isinstance(direct, dict):
        return refuse("the agentteams install record (direct_url.json) is not an object")
    url = direct.get("url", "")
    try:
        import agentteams
    except ImportError as exc:
        return refuse(f"agentteams cannot be imported ({exc})")
    imported = Path(agentteams.__file__).resolve()
    editable = bool(direct.get("dir_info", {}).get("editable"))
    if dist is not None and not editable:  # the code that runs must be the install judged, not a shadowing copy
        owned = {Path(str(dist.locate_file(f))).resolve() for f in (dist.files or [])}
        if imported not in owned:
            return refuse(f"the agentteams that Python imports ({imported.parent}) is not the installed copy the record "
                          "describes (a checkout earlier on sys.path shadows it)")
    if direct.get("vcs_info", {}).get("commit_id"):
        print(f"{TAG}: agentteams ({exe}) is a VCS install of {url} @ {direct['vcs_info']['commit_id'][:12]}")
        return against_lock(direct["vcs_info"]["commit_id"], "the install")
    if not editable:
        if url.startswith("file:"):
            print(f"{TAG}: agentteams ({exe}) is a non-editable snapshot of {unquote(urlparse(url).path)}")
            if os.environ.get("MATHAGENTS_ALLOW_AGENTTEAMS_SNAPSHOT") != "1":
                return refuse("a local-folder snapshot cannot be verified (a stale one dropped the adopted routing rows "
                              "in v0.2.6, CA-033); use a VCS install pinned to the toolchain.lock commit (or, without a lock, "
                              "an editable checkout on main), or set MATHAGENTS_ALLOW_AGENTTEAMS_SNAPSHOT=1 to accept it knowingly")
            print(f"{TAG}: WARNING: accepting an unverifiable local snapshot (MATHAGENTS_ALLOW_AGENTTEAMS_SNAPSHOT=1)",
                  file=sys.stderr)
        else:
            print(f"{TAG}: agentteams ({exe}) is a released package, version {dist.version if dist else '?'}")
        return against_lock(None, "the install (a package or snapshot, whose commit cannot be shown)")
    pkg = imported.parent  # the directory actually imported (handles a src/ layout)
    if url.startswith("file:"):
        src = Path(unquote(urlparse(url).path)).resolve()
        if src != pkg and src not in pkg.parents:
            return refuse(f"the agentteams that Python imports ({pkg}) is outside the editable checkout {src}")
    top = git(pkg, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return refuse(f"the editable agentteams at {pkg} is not in a git checkout")
    repo = Path(top.stdout.strip())
    head, branch = git(repo, "rev-parse", "HEAD"), git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if head.returncode != 0:
        return refuse(f"cannot read HEAD of {repo}")
    sha, name = head.stdout.strip(), branch.stdout.strip() or "?"
    print(f"{TAG}: agentteams ({exe}) is an editable checkout {repo}, branch {name}, commit {sha[:12]}")
    try:
        want = locked_commit()
    except ValueError as exc:
        return refuse(str(exc))
    if want is not None:  # a pinned release: the checkout must be exactly the locked commit, on main or not
        rc = against_lock(sha, f"the editable checkout {repo}", want)
        if rc:
            return rc
    anc = git(repo, "merge-base", "--is-ancestor", sha, "origin/main") if want is None else None
    if anc is not None and anc.returncode != 0:
        return refuse(f"commit {sha[:12]} (branch {name}) is not on origin/main (or origin/main is missing); render only "
                      "merged agentteams: check out main there, or fetch if origin/main is stale")
    status = git(repo, "status", "--porcelain", "--", str(pkg))
    if status.returncode != 0:
        return refuse(f"git status failed in {repo}: {status.stderr.strip()[:200]}")
    dirty = [ln for ln in status.stdout.splitlines() if not re.search(r"(__pycache__/|\.pyc$)", ln)]
    if dirty:
        return refuse(f"uncommitted or untracked agentteams sources in {pkg}: {', '.join(d[3:] for d in dirty[:5])}")
    return 0


def inner_researchteam() -> int:
    """Under researchteam's own interpreter: the researchteam that renders must be the lock's `researchteam=` commit,
    a VCS install at it or a clean checkout whose HEAD is it. Without a lock (or a researchteam line) it only reports."""
    from importlib import metadata
    from urllib.parse import unquote, urlparse
    try:
        want = locked_commit(name="researchteam")
    except ValueError as exc:
        return refuse(str(exc))
    try:
        dist = metadata.distribution("researchteam")
        direct = json.loads(dist.read_text("direct_url.json") or "{}")
    except (metadata.PackageNotFoundError, OSError, ValueError) as exc:
        return refuse(f"cannot read the researchteam install record ({exc})")
    if direct.get("vcs_info", {}).get("commit_id"):
        sha, what = direct["vcs_info"]["commit_id"], f"the researchteam VCS install of {direct.get('url', '?')}"
    elif direct.get("dir_info", {}).get("editable") and str(direct.get("url", "")).startswith("file:"):
        src = Path(unquote(urlparse(direct["url"]).path)).resolve()
        head = git(src, "rev-parse", "HEAD")
        if head.returncode != 0:
            return refuse(f"the editable researchteam at {src} is not a readable git checkout")
        try:
            import researchteam  # judge the package that is imported, as for agentteams (not the repo's own agents)
            pkg = Path(researchteam.__file__).resolve().parent
        except ImportError as exc:
            return refuse(f"researchteam cannot be imported ({exc})")
        if src != pkg and src not in pkg.parents:
            return refuse(f"the researchteam that Python imports ({pkg}) is outside the editable checkout {src}")
        dirty = [ln for ln in git(src, "status", "--porcelain", "--", str(pkg)).stdout.splitlines()
                 if not re.search(r"(__pycache__/|\.pyc$)", ln)]
        if dirty:
            return refuse(f"uncommitted or untracked researchteam sources in {src}: {', '.join(d[3:] for d in dirty[:5])}")
        sha, what = head.stdout.strip(), f"the editable researchteam checkout {src}"
    else:
        sha, what = None, "the researchteam install (a package or snapshot, whose commit cannot be shown)"
    print(f"{TAG}: researchteam is {what} @ {sha[:12] if sha else '?'}")
    if want is None:
        return 0
    if sha == want:
        print(f"{TAG}: matches toolchain.lock (researchteam {want[:12]})")
        return 0
    return refuse(f"{what} is researchteam {sha[:12] if sha else 'at an unknown commit'}, but toolchain.lock pins "
                  f"{want[:12]}; check out or install the locked commit before rendering")


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "--inner":
        return inner(argv[1])
    if argv == ["--inner-researchteam"]:
        return inner_researchteam()
    if argv == ["--researchteam"]:
        exe = shutil.which("researchteam")
        py = launcher_interpreter(exe) if exe else None
        if not py or not os.access(py, os.X_OK):
            return refuse("cannot find researchteam or its interpreter")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([py, str(Path(__file__).resolve()), "--inner-researchteam"], env=env).returncode
    if len(argv) == 2 and argv[0] == "--interpreter-of":
        # The interpreter a CLI's launcher runs under, so a caller imports the same install the CLI runs
        # (a bare `python3` on PATH may be another environment without it).
        exe = shutil.which(argv[1])
        py = launcher_interpreter(exe) if exe else None
        if not py or not os.access(py, os.X_OK):
            print(f"{TAG}: cannot determine the interpreter of {argv[1]}", file=sys.stderr)
            return 127
        print(py)
        return 0
    exe = shutil.which("agentteams")
    if not exe:
        print(f"{TAG}: agentteams is not installed", file=sys.stderr)
        return 127
    py = launcher_interpreter(exe)
    if not py or not os.access(py, os.X_OK):
        return refuse(f"cannot determine the interpreter of {exe} (shebang not understood)")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([py, str(Path(__file__).resolve()), "--inner", exe], env=env).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
