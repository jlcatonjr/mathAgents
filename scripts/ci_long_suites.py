#!/usr/bin/env python3
"""Decide whether the long CI suites run (charter D46; supersedes D36/IA-08). Fail-closed.

The long suites are the G-KERNEL gate tests and the Lean half of the G-AX governance tests (over an hour on a hosted
runner). G-KERNEL itself and every other gate still run on every push in the `gates` job. The long suites run:
  - on a manual dispatch, a `v*` tag, a push to a `release/**` branch, and the monthly schedule (MONTHLY_CRON);
  - on a pull request whose diff against its base touches an input (scripts/ci_long_suite_inputs.txt);
  - on a push to main, unless HEAD merges a pull-request head whose own Gates run passed `long-suites`, the pull
    request did not change a decision file (DECISION_FILES: a PR could otherwise define its own `long-suites`), and
    nothing in the inputs changed between that head and HEAD. Then the PR's run already covered it. Otherwise the
    inputs are compared with the newest ancestor whose Gates run passed `long-suites` (never a run that skipped
    it, such as the weekly schedule), or with the root commit when there is none;
  - whenever anything cannot be determined (an unknown event, a git or API error).
The weekly schedule runs `gates` only.

    EVENT=<event> REF=<github.ref> SCHEDULE=<cron> PR_BASE=<sha> REPO=<owner/name> GH_TOKEN=<token> \\
        python3 scripts/ci_long_suites.py      # prints true or false, and the reason on stderr
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS_FILE = ROOT / "scripts" / "ci_long_suite_inputs.txt"
MONTHLY_CRON = "0 6 1 * *"
WEEKLY_CRON = "0 5 * * 2"
LONG_JOB = "long-suites"
#: The files that decide whether the long suites run. A pull request that changes one is never trusted to have
#: covered its merge (security review 2026-10-28).
DECISION_FILES = (".github/workflows/gates.yml", "scripts/ci_long_suites.py", "scripts/ci_long_suite_inputs.txt",
                  "scripts/tests/test_ci_workflow.py", "tests/test_ci_long_suites.py", "scripts/ci_base.sh")


def read_inputs(path: Path = INPUTS_FILE) -> list[str]:
    """The input paths and prefixes, without comments or blank lines."""
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")]


def touches(changed: Iterable[str], inputs: list[str]) -> list[str]:
    """The changed files that are inputs (exact path, or under a prefix ending in "/")."""
    return [f for f in changed if any(f == i or (i.endswith("/") and f.startswith(i)) for i in inputs)]


def _git(*args: str) -> str:
    """stdout of a git command in the repository; raises on failure."""
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def changed_files(base: str, head: str = "HEAD") -> list[str]:
    """The paths that differ between two commits."""
    return [line for line in _git("diff", "--name-only", base, head).splitlines() if line]


def _gh_json(path: str) -> dict:
    """A GitHub API response as JSON; raises on failure."""
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def pr_head_passed_long_suites(repo: str, sha: str, gh: Callable[[str], dict] = _gh_json) -> bool:
    """True when a pull_request Gates run on head `sha` succeeded with a successful long-suites job."""
    runs = gh(f"repos/{repo}/actions/workflows/gates.yml/runs?head_sha={sha}&event=pull_request&status=success")
    for run in runs.get("workflow_runs", []):
        jobs = gh(f"repos/{repo}/actions/runs/{run['id']}/jobs")
        if any(j.get("name") == LONG_JOB and j.get("conclusion") == "success" for j in jobs.get("jobs", [])):
            return True
    return False


def last_long_green(repo: str, gh: Callable[[str], dict] = _gh_json,
                    is_ancestor: Callable[[str], bool] = lambda sha: subprocess.run(
                        ["git", "merge-base", "--is-ancestor", sha, "HEAD"], cwd=ROOT).returncode == 0,
                    root: Callable[[], str] = lambda: _git("rev-list", "--max-parents=0", "HEAD").split()[-1]) -> str:
    """The newest ancestor of HEAD on main whose Gates run passed `long-suites`, else the root commit."""
    runs = gh(f"repos/{repo}/actions/workflows/gates.yml/runs?branch=main&status=success&per_page=50")
    for run in runs.get("workflow_runs", []):
        if run.get("event") == "pull_request" or not is_ancestor(run["head_sha"]):
            continue
        jobs = gh(f"repos/{repo}/actions/runs/{run['id']}/jobs")
        if any(j.get("name") == LONG_JOB and j.get("conclusion") == "success" for j in jobs.get("jobs", [])):
            return run["head_sha"]
    return root()


def decide(env: dict[str, str], inputs: list[str], *,
           changed: Callable[[str, str], list[str]] = changed_files,
           parents: Callable[[], list[str]] = lambda: _git("rev-list", "--parents", "-n", "1", "HEAD").split()[1:],
           ci_base: Callable[[str], str] = last_long_green,
           passed: Callable[[str, str], bool] = pr_head_passed_long_suites) -> tuple[bool, str]:
    """Return (run the long suites?, reason). Any exception is the caller's to turn into True."""
    event, ref = env.get("EVENT", ""), env.get("REF", "")
    if event == "workflow_dispatch":
        return True, "manual dispatch"
    if event == "schedule":
        sched = env.get("SCHEDULE", "")
        if sched == WEEKLY_CRON:
            return False, "weekly schedule: gates only"
        return True, f"schedule {sched!r} (monthly, or unrecognised: fail closed)"
    if event == "push" and ref.startswith("refs/tags/v"):
        return True, f"release tag {ref}"
    if event == "push" and ref.startswith("refs/heads/release/"):
        return True, f"release line {ref}"
    if event == "pull_request":
        hit = touches(changed(env["PR_BASE"], "HEAD"), inputs)
        return bool(hit), f"pull request inputs changed: {hit[:5]}" if hit else "pull request: no input changed"
    if event == "push" and ref == "refs/heads/main":
        ps = parents()
        if len(ps) == 2 and passed(env["REPO"], ps[1]):
            if touches(changed(ps[0], ps[1]), list(DECISION_FILES)):
                pass  # the PR changed what decides the suites: its own run is not trusted
            elif not touches(changed(ps[1], "HEAD"), inputs):
                return False, f"merge of PR head {ps[1][:12]}, whose run passed {LONG_JOB}; no input changed since"
        base = ci_base(env["REPO"])
        hit = touches(changed(base, "HEAD"), inputs)
        return bool(hit), (f"push to main: inputs changed since {base[:12]} (last {LONG_JOB} pass): {hit[:5]}" if hit
                           else f"push to main: no input changed since {base[:12]} (last {LONG_JOB} pass)")
    return True, f"event {event!r} on {ref!r}: not recognised, fail closed"


def main() -> int:
    try:
        run, why = decide(dict(os.environ), read_inputs())
    except Exception as exc:  # fail closed: anything undetermined runs the suites
        run, why = True, f"could not decide ({type(exc).__name__}: {exc}); fail closed"
        print(f"::warning::long-suites decision failed, running the suites: {why}", file=sys.stderr)
    print(f"long suites run: {str(run).lower()} ({why})", file=sys.stderr)
    print(str(run).lower())
    return 0


if __name__ == "__main__":
    sys.exit(main())
