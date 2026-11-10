#!/usr/bin/env python3
"""CI workflow check (spec G-KERNEL "CI tests to build"; DD-41; decision D18). Fail-closed.

Parses .github/workflows/gates.yml and fails unless:
  - push and pull_request triggers carry path filters covering lean/, scripts/ and references/
    (and reports/dossiers/, for the dossier validator, and every agent surface, IA-02), with no
    paths-ignore;
  - a weekly schedule exists (a cron with a fixed day of week and every day of month);
  - one step runs scripts/check_proof_integrity.sh and another runs scripts/tests/test_mathagents_gates.sh,
    and steps run the G-FID, G-CX, G-AX, dossier-structure, G-NAME and G-BLUEPRINT suites, the
    name-index build, G-NAME, G-BLUEPRINT, the preferences check and suite, the Python API parity
    check and tests (tests/test_api_*.py), and scripts/validate_dossier.py with --base;
  - no job or step sets continue-on-error, and no gate step swallows its exit code (`|| true`,
    `|| :`, `set +e`);
  - the dossier validator's base on main is the last commit with a successful Gates run (the
    workflow can read runs: `actions: read`), never HEAD itself (IA-01);
  - the long-suites job (charter D46) is decided by scripts/ci_long_suites.py, which forces it on workflow_dispatch,
    `v*` tags, `release/**` pushes and the monthly cron and falls back to running on any error; the job runs when
    its decision job fails or is cancelled; the weekly and monthly crons match the script's; both halves of the
    G-AX tests run (`--part validator` and `--part lean`);
  - every job runs on the pinned GitHub-hosted image, and every job starts with the hosted-runner guard,
    which fails any run on a self-hosted runner (D45 retired the operator's fallback runner, D37);
  - every job that runs Lean installs it with scripts/install_lean.sh (pinned, hash-verified elan
    installer), and no step pipes a download into a shell (IA-26).
`--self-test` mutates the workflow in memory and checks that each mutation is rejected.
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "gates.yml"
REQUIRED_PATHS = ("lean/", "scripts/", "references/", "reports/dossiers/",
                  ".github/agents/", ".claude/", ".codex/", ".goose/", ".agents/", "AGENTS.md")  # surfaces: IA-02
GATE_SCRIPTS = ("scripts/check_proof_integrity.sh", "scripts/tests/test_mathagents_gates.sh",
                "scripts/tests/test_fidelity_gate.sh", "scripts/tests/test_counterexample_gate.sh",
                "scripts/tests/test_axiom_governance.sh", "scripts/tests/test_dossier_gate.sh",
                "scripts/tests/test_lean_bindings.sh", "scripts/tests/test_blueprint_gate.sh",
                "scripts/build_name_index.py", "scripts/check_lean_bindings.py",
                "scripts/check_blueprint_consistency.py", "scripts/preferences.py check",
                "scripts/tests/test_preferences.sh", "scripts/check_api_doc_parity.py --strict",
                "tests/test_api_boundary.py", "tests/test_api_site.py")
SWALLOW = ("|| true", "|| :", "set +e")
CI_BASE = Path(__file__).resolve().parents[2] / "scripts" / "ci_base.sh"
LONG_DECIDER = Path(__file__).resolve().parents[2] / "scripts" / "ci_long_suites.py"
#: What the decision script must force (D46): each string must appear in its source.
LONG_FORCED = ('"workflow_dispatch"', '"refs/tags/v"', '"refs/heads/release/"', "MONTHLY_CRON", "fail closed")
#: The pinned GitHub-hosted image (gates.yml, remediation A2): `ubuntu-latest` moved to 26.04, which doubled the
#: G-KERNEL gate-test time, so jobs name the image.
HOSTED_RUNS_ON = "ubuntu-24.04"
#: The hosted-runner guard every job starts with (D45): it fails the job on anything but a GitHub-hosted runner.
GUARD_IF = "runner.environment != 'github-hosted'"
PIPE_TO_SHELL = re.compile(r"\b(curl|wget)\b[^\n|]*(\\\n[^\n|]*)*\|\s*(sudo\s+)?(ba|z)?sh\b")


def check(wf: dict) -> list[str]:
    errs: list[str] = []
    on = wf.get("on", wf.get(True))  # PyYAML reads the bare key `on` as boolean True
    if not isinstance(on, dict):
        return ["no `on:` trigger mapping"]
    for trig in ("push", "pull_request"):
        t = on.get(trig)
        if not isinstance(t, dict):
            errs.append(f"{trig}: trigger missing")
            continue
        if "paths-ignore" in t:
            errs.append(f"{trig}: paths-ignore is not allowed (it can silently skip the gates)")
        paths = t.get("paths") or []
        for req in REQUIRED_PATHS:
            if not any(str(p).startswith(req) for p in paths):
                errs.append(f"{trig}: no path filter covering {req}")
    crons = [s.get("cron", "") for s in (on.get("schedule") or []) if isinstance(s, dict)]
    weekly = [c for c in crons if len(c.split()) == 5 and c.split()[2] == "*" and c.split()[3] == "*"
              and c.split()[4].isdigit()]
    if not weekly:
        errs.append("no weekly schedule (cron with a fixed day of week)")
    steps: list[dict] = []
    for name, job in (wf.get("jobs") or {}).items():
        if "continue-on-error" in job:
            errs.append(f"job {name}: sets continue-on-error")
        for st in job.get("steps") or []:
            steps.append(st)
            if "continue-on-error" in st:
                errs.append(f"step {st.get('name', '?')!r}: sets continue-on-error")
    runs = [(st, str(st.get("run", ""))) for st in steps]
    hosts = {}
    for script in GATE_SCRIPTS:
        found = [st for st, r in runs if script in r]
        if not found:
            errs.append(f"no step runs {script}")
        hosts[script] = found
    kernel, gate_tests = hosts[GATE_SCRIPTS[0]], hosts[GATE_SCRIPTS[1]]
    if kernel and gate_tests and all(k is g for k in kernel for g in gate_tests):
        errs.append("check_proof_integrity.sh and test_mathagents_gates.sh must run in separate steps")
    if not any("scripts/validate_dossier.py" in r and "--base" in r for _, r in runs):
        errs.append("no step runs scripts/validate_dossier.py with --base")
    for st, r in runs:
        if "scripts/validate_dossier.py" in r:
            if "scripts/ci_base.sh" in r:  # the base logic lives in the shared script (IA-01, IA-08)
                r = r + (CI_BASE.read_text(encoding="utf-8") if CI_BASE.is_file() else "")
            if "rev-parse HEAD)" in r or "rev-parse HEAD~1)" in r:
                errs.append(f"step {st.get('name', '?')!r}: bases the dossier validator on HEAD or HEAD~1, which "
                            "skips commits whose run was cancelled (IA-01)")
            if "status=success" not in r or "--is-ancestor" not in r:
                errs.append(f"step {st.get('name', '?')!r}: does not base the dossier validator on the last "
                            "verified commit (a successful Gates run that is an ancestor of HEAD; IA-01)")
            if "--no-history" in r:
                errs.append(f"step {st.get('name', '?')!r}: disables the per-commit history check (IA-01)")
    jobs = wf.get("jobs") or {}
    # No self-hosted route (D45): every job runs on the pinned hosted image and starts with the hosted-runner guard.
    if "runner" in (((wf.get("on") or wf.get(True) or {}).get("workflow_dispatch") or {}).get("inputs") or {}):
        errs.append("workflow_dispatch has a runner input: a route to a self-hosted runner (retired by D45)")
    for name, job in jobs.items():
        ro = job.get("runs-on")
        if ro != HOSTED_RUNS_ON:  # exact: no expression, label list or self-hosted route
            errs.append(f"job {name!r}: runs-on {str(ro)[:60]!r} is not {HOSTED_RUNS_ON}; it may reach a self-hosted "
                        "runner (D45)")
        steps = job.get("steps") or []
        first = steps[0] if steps else {}
        if str(first.get("if", "")).strip() != GUARD_IF or "exit 1" not in str(first.get("run", "")):
            errs.append(f"job {name!r}: first step is not the hosted-runner guard ({GUARD_IF}; exit 1)")
    kj = next((j for j in jobs.values() if any("test_mathagents_gates.sh" in str(st.get("run", ""))
                                               for st in j.get("steps") or [])), None)
    if kj is not None and kj.get("if") and ("needs.changes.result != 'success'" not in str(kj.get("if"))
                                             or not any(f in str(kj.get("if")) for f in ("!cancelled()", "always()"))):
        errs.append("the G-KERNEL gate-test job is skipped when its decision job fails or is cancelled; "
                    "it must run then (fail closed)")
    kjob = next((j for j in jobs.values() if any("test_mathagents_gates.sh" in str(st.get("run", ""))
                                                  for st in j.get("steps") or [])), None)
    if kjob is not None and kjob.get("if"):  # D46: a conditional long-suites job must be decided by the script
        dep = jobs.get(str(kjob.get("needs") or "")) or {}
        text = " ".join(str(st.get("run", "")) for st in dep.get("steps") or [])
        if "scripts/ci_long_suites.py" not in text:
            errs.append("the long-suites job is conditional but not decided by scripts/ci_long_suites.py (D46)")
        elif "then t=true" not in text:
            errs.append("the long-suites decision step does not fall back to running when the script fails")
        src = LONG_DECIDER.read_text(encoding="utf-8") if LONG_DECIDER.is_file() else ""
        missing = [f for f in LONG_FORCED if f not in src]
        if missing:
            errs.append(f"scripts/ci_long_suites.py does not force the long suites on {missing} (D46)")
        m = re.search(r'MONTHLY_CRON = "([^"]+)"', src); wk = re.search(r'WEEKLY_CRON = "([^"]+)"', src)
        for label, cron in (("monthly", m.group(1) if m else None), ("weekly", wk.group(1) if wk else None)):
            if cron not in crons:
                errs.append(f"the {label} cron of scripts/ci_long_suites.py ({cron}) is not a schedule in the workflow")
    gax = [r for _, r in runs if "test_axiom_governance.sh" in r]
    if not any("--part lean" in r or "--part" not in r for r in gax):
        errs.append("the Lean half of the G-AX tests runs nowhere (--part lean)")
    if not any("--part validator" in r or "--part" not in r for r in gax):
        errs.append("the validator half of the G-AX tests runs nowhere (--part validator)")
    if (wf.get("permissions") or {}).get("actions") != "read":
        errs.append("workflow permissions lack `actions: read` (needed to find the last verified commit)")
    for name, job in (wf.get("jobs") or {}).items():
        jruns = [str(st.get("run", "")) for st in job.get("steps") or []]
        if any("lake " in r or any(g in r for g in GATE_SCRIPTS) for r in jruns) \
                and not any("scripts/install_lean.sh" in r for r in jruns):
            errs.append(f"job {name!r}: does not install Lean with scripts/install_lean.sh")
    for st, r in runs:
        if PIPE_TO_SHELL.search(r):
            errs.append(f"step {st.get('name', '?')!r}: pipes a download into a shell; use a pinned, hash-verified installer")
    for st, r in runs:
        if any(s in r for s in ("scripts/", "lake ")) and any(sw in r for sw in SWALLOW):
            errs.append(f"step {st.get('name', '?')!r}: swallows a failure ({[s for s in SWALLOW if s in r]})")
    return errs


def self_test(wf: dict) -> list[str]:
    """Each mutation must produce at least one finding."""
    def drop_path(w):
        on = w.get("on", w.get(True)); on["push"]["paths"] = [p for p in on["push"]["paths"] if not p.startswith("lean/")]
    def drop_surface(w):
        on = w.get("on", w.get(True)); on["pull_request"]["paths"] = [p for p in on["pull_request"]["paths"] if not p.startswith(".goose/")]
    def drop_weekly(w):
        on = w.get("on", w.get(True)); on.pop("schedule", None)
    def all_steps(w):  # every job's steps: the gates span more than one job
        return [st for job in w["jobs"].values() for st in job.get("steps") or []]
    def coe_step(w):
        next(iter(w["jobs"].values()))["steps"][-1]["continue-on-error"] = True
    def coe_job(w):
        next(iter(w["jobs"].values()))["continue-on-error"] = True
    def coe_last_job(w):
        list(w["jobs"].values())[-1]["continue-on-error"] = True
    def drop_kernel(w):
        for st in all_steps(w):
            if "check_proof_integrity.sh" in str(st.get("run", "")):
                st["run"] = "echo skipped"
    def drop_gate_tests(w):
        for st in all_steps(w):
            if "test_mathagents_gates.sh" in str(st.get("run", "")):
                st["run"] = "echo skipped"
    def swallow(w):
        for st in all_steps(w):
            if "test_mathagents_gates.sh" in str(st.get("run", "")):
                st["run"] += " || true"
    def ignore(w):
        on = w.get("on", w.get(True)); on["pull_request"]["paths-ignore"] = ["lean/**"]
    def no_base(w):
        for st in all_steps(w):
            if "validate_dossier.py" in str(st.get("run", "")):
                st["run"] = "python3 scripts/validate_dossier.py"
    def pipe_installer(w):
        for st in all_steps(w):
            if "install_lean.sh" in str(st.get("run", "")):
                st["run"] = ("curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \\\n"
                             "  | sh -s -- -y --default-toolchain none\n")
    def head_base(w):
        for st in all_steps(w):
            if "validate_dossier.py" in str(st.get("run", "")):
                st["run"] = 'BASE="$(git rev-parse HEAD)"\npython3 scripts/validate_dossier.py --base "$BASE"\n'
    def no_actions_read(w):
        w["permissions"].pop("actions", None)
    def no_history(w):
        for st in all_steps(w):
            if "validate_dossier.py" in str(st.get("run", "")):
                st["run"] = str(st["run"]).replace('--base "$BASE"', '--base "$BASE" --no-history')
    def skip_forced(w):
        for j in w["jobs"].values():
            for st in j.get("steps") or []:
                if "ci_long_suites.py" in str(st.get("run", "")):
                    st["run"] = 'echo "long_suites=false" >> "$GITHUB_OUTPUT"\n'
    def no_fallback(w):
        for j in w["jobs"].values():
            for st in j.get("steps") or []:
                if "ci_long_suites.py" in str(st.get("run", "")):
                    st["run"] = 't="$(python3 scripts/ci_long_suites.py)"\necho "long_suites=$t" >> "$GITHUB_OUTPUT"\n'
    def drop_monthly(w):
        on = w.get("on", w.get(True)); on["schedule"] = [s for s in on["schedule"] if s.get("cron") != "0 6 1 * *"]
    def drop_lean_half(w):
        for st in all_steps(w):
            if "--part lean" in str(st.get("run", "")):
                st["run"] = "echo skipped"
    def drop_validator_half(w):
        for st in all_steps(w):
            if "--part validator" in str(st.get("run", "")):
                st["run"] = "echo skipped"
    def hardcode_self_hosted(w):
        next(iter(w["jobs"].values()))["runs-on"] = ["self-hosted"]
    def fallback_route_back(w):
        next(iter(w["jobs"].values()))["runs-on"] = ("${{ inputs.runner == 'mac' && fromJSON('[\"self-hosted\"]') "
                                                     "|| 'ubuntu-24.04' }}")
    def drop_guard(w):
        list(w["jobs"].values())[-1]["steps"].pop(0)
    def drop_guard_first(w):
        list(w["jobs"].values())[0]["steps"].pop(0)
    def weaken_guard(w):
        list(w["jobs"].values())[0]["steps"][0]["if"] = "false"
    def runner_input_back(w):
        on = w.get("on") or w.get(True)
        on["workflow_dispatch"] = {"inputs": {"runner": {"type": "choice", "options": ["github", "mac"]}}}
    def kernel_no_status_fn(w):
        for j in w["jobs"].values():
            if "needs.changes.result" in str(j.get("if", "")):
                j["if"] = "${{ needs.changes.result != 'success' || needs.changes.outputs.long_suites == 'true' }}"
    def kernel_skip_on_cancel(w):
        for j in w["jobs"].values():
            if any("test_mathagents_gates.sh" in str(st.get("run", "")) for st in j.get("steps") or []):
                j["if"] = "needs.changes.outputs.long_suites == 'true'"
    failures = []
    for mut in (drop_path, drop_weekly, coe_step, coe_job, coe_last_job, drop_kernel, drop_gate_tests, swallow,
                ignore, no_base, pipe_installer, drop_surface, skip_forced, no_fallback, drop_monthly, drop_lean_half,
                drop_validator_half, hardcode_self_hosted, fallback_route_back,
                drop_guard, kernel_skip_on_cancel, drop_guard_first, weaken_guard, runner_input_back,
                kernel_no_status_fn, head_base, no_actions_read, no_history):
        w = copy.deepcopy(wf); mut(w)
        if not check(w):
            failures.append(f"self-test: mutation {mut.__name__} was not rejected")
    return failures


def main() -> int:
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    errs = check(wf)
    if "--self-test" in sys.argv or not errs:
        errs += self_test(wf)
    for e in errs:
        print(f"FAIL {e}")
    print(f"CI workflow check ({WORKFLOW.name}): " + ("FAIL" if errs else "PASS"))
    return 1 if errs else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed
        print(f"CI workflow check: FAIL: error: {exc!r}")
        sys.exit(2)
