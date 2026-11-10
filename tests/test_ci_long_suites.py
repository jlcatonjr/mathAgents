"""The long-suites decision (scripts/ci_long_suites.py, charter D46) and its input list. The decision is
fail-closed; the list must cover every local module the long suites import and every file they read."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ci_long_suites as cls  # noqa: E402

SUITES = (ROOT / "scripts/tests/test_mathagents_gates.sh", ROOT / "scripts/tests/test_axiom_governance.sh")
INPUTS = cls.read_inputs()


def _decide(env, changed=None, parents=None, passed=None, base="b" * 40):
    return cls.decide(env, INPUTS, changed=changed or (lambda a, b: []), parents=parents or (lambda: ["p1"]),
                      ci_base=lambda repo: base, passed=passed or (lambda repo, sha: False))[0]


@pytest.mark.parametrize("env", [
    {"EVENT": "workflow_dispatch", "REF": "refs/heads/main"},
    {"EVENT": "push", "REF": "refs/tags/v1.1.0"},
    {"EVENT": "push", "REF": "refs/heads/release/1.1"},
    {"EVENT": "schedule", "SCHEDULE": cls.MONTHLY_CRON},
    {"EVENT": "schedule", "SCHEDULE": "17 3 * * *"},          # unknown cron: fail closed
    {"EVENT": "merge_group", "REF": "refs/heads/main"},       # unknown event: fail closed
])
def test_forced(env):
    assert _decide(env) is True


def test_weekly_runs_gates_only():
    assert _decide({"EVENT": "schedule", "SCHEDULE": cls.WEEKLY_CRON}) is False


def test_pull_request_follows_inputs():
    pr = {"EVENT": "pull_request", "PR_BASE": "a" * 40}
    assert _decide(pr, changed=lambda a, b: ["docs/x.md", ".claude/agents/x.md"]) is False
    assert _decide(pr, changed=lambda a, b: ["scripts/proof_integrity.py"]) is True
    assert _decide(pr, changed=lambda a, b: ["references/object-logics.json"]) is True
    assert _decide(pr, changed=lambda a, b: [".github/workflows/gates.yml"]) is True


def test_push_to_main_skips_only_when_the_pr_run_covered_it():
    env = {"EVENT": "push", "REF": "refs/heads/main", "REPO": "o/r"}
    merge = lambda: ["p1", "prhead"]  # noqa: E731
    covered = lambda repo, sha: sha == "prhead"  # noqa: E731
    # merged PR head passed long-suites, nothing changed since: skip
    assert _decide(env, parents=merge, passed=covered, changed=lambda a, b: []) is False
    # an input changed between the PR head and HEAD: compare with ci_base, which shows the change
    assert _decide(env, parents=merge, passed=covered,
                   changed=lambda a, b: ["scripts/ci_base.sh"]) is True
    # PR head never passed long-suites: falls back to ci_base
    assert _decide(env, parents=merge, passed=lambda r, s: False,
                   changed=lambda a, b: ["scripts/proof_integrity.py"]) is True
    # a direct (non-merge) push with an input change: runs
    assert _decide(env, parents=lambda: ["p1"], changed=lambda a, b: ["lean/lean-toolchain"]) is True
    assert _decide(env, parents=lambda: ["p1"], changed=lambda a, b: ["README.md"]) is False


def test_a_pr_that_changes_the_decision_is_not_trusted():
    env = {"EVENT": "push", "REF": "refs/heads/main", "REPO": "o/r"}
    merge = lambda: ["p1", "prhead"]  # noqa: E731
    covered = lambda repo, sha: True  # noqa: E731
    def changed(a, b):  # the PR (p1..prhead) edited gates.yml; nothing changed after it
        if (a, b) == ("p1", "prhead"):
            return [".github/workflows/gates.yml"]
        return [] if a == "prhead" else [".github/workflows/gates.yml"]
    assert _decide(env, parents=merge, passed=covered, changed=changed) is True


def test_last_long_green_skips_runs_that_did_not_pass_long_suites():
    runs = {"workflow_runs": [
        {"id": 1, "head_sha": "weekly", "event": "schedule"},          # skipped long-suites
        {"id": 2, "head_sha": "prrun", "event": "pull_request"},       # a PR merge tree, never a base
        {"id": 3, "head_sha": "elsewhere", "event": "push"},           # not an ancestor
        {"id": 4, "head_sha": "good", "event": "push"},
    ]}
    jobs = {1: [{"name": "long-suites", "conclusion": "skipped"}], 2: [{"name": "long-suites", "conclusion": "success"}],
            3: [{"name": "long-suites", "conclusion": "success"}], 4: [{"name": "long-suites", "conclusion": "success"}]}
    def gh(path):
        if path.endswith("/jobs"):
            return {"jobs": jobs[int(path.split("/")[-2])]}
        return runs
    assert cls.last_long_green("o/r", gh=gh, is_ancestor=lambda s: s != "elsewhere", root=lambda: "root") == "good"
    assert cls.last_long_green("o/r", gh=lambda p: {"workflow_runs": []}, root=lambda: "root") == "root"


def test_decision_files_are_inputs():
    assert all(cls.touches([f], INPUTS) for f in cls.DECISION_FILES)


def test_errors_fail_closed(monkeypatch, capsys):
    def boom(*a, **k):
        raise RuntimeError("api down")
    monkeypatch.setattr(cls, "decide", boom)
    assert cls.main() == 0
    out = capsys.readouterr()
    assert out.out.strip() == "true" and "::warning::" in out.err


def _entry() -> list[str]:
    """The Python scripts the two suites run directly."""
    return sorted({m for s in SUITES for m in re.findall(r"scripts/([a-z_]+)\.py", s.read_text(encoding="utf-8"))})


def _local_imports(entry: list[str]) -> set[str]:
    local = {p.stem for p in (ROOT / "scripts").glob("*.py")}
    seen, todo = set(), list(entry)
    while todo:
        mod = todo.pop()
        if mod in seen:
            continue
        seen.add(mod)
        for node in ast.walk(ast.parse((ROOT / "scripts" / f"{mod}.py").read_text(encoding="utf-8"))):
            names = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else \
                [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module and not node.level else []
            todo += [n for n in names if n in local and n not in seen]
    return seen


def test_inputs_cover_every_imported_module():
    entry = _entry()
    assert entry, "no Python entry points found in the suites"
    missing = [f"scripts/{m}.py" for m in sorted(_local_imports(entry)) if not cls.touches([f"scripts/{m}.py"], INPUTS)]
    assert not missing, f"add to scripts/ci_long_suite_inputs.txt: {missing}"


def test_inputs_cover_every_path_the_suites_read():
    read = set()
    for s in SUITES:
        read |= set(re.findall(r'\$ROOT/((?:lean|references|docs|scripts)/[A-Za-z0-9_./-]+)', s.read_text(encoding="utf-8")))
    read = {p.rstrip("/").split("*")[0].rstrip("/") for p in read}
    read = {p for p in read if not p.startswith("lean/.lake") and not p.startswith("lean/MathAgents/")
            and not p.startswith("lean/MathAgentsWIP/") and p not in ("lean/MathAgents", "lean/MathAgentsWIP")}
    missing = sorted(p for p in read if not cls.touches([p], INPUTS) and not any(i.startswith(p + "/") for i in INPUTS))
    assert not missing, f"add to scripts/ci_long_suite_inputs.txt: {missing}"


def test_inputs_exist():
    gone = [i for i in INPUTS if not (ROOT / i.rstrip("/")).exists()]
    assert not gone, f"stale entries in scripts/ci_long_suite_inputs.txt: {gone}"


def test_gax_lean_half_does_not_depend_on_the_validator_half():
    """--part lean once failed with 'allowlist: command not found' (run 40704937719): helpers both halves use must be
    defined before either half's block."""
    text = (ROOT / "scripts/tests/test_axiom_governance.sh").read_text(encoding="utf-8")
    first_block = text.index("if [[ $PART != lean ]]")
    for helper in ("allowlist() {", "REC='", "ok() {", "bad() {"):
        assert text.index(helper) < first_block, helper


def test_inputs_cover_every_references_file_the_suites_or_their_modules_read():
    """references/ is listed file by file (operator, 2026-10-29), so a new registry read must be added here."""
    entry = _entry()
    texts = [s.read_text(encoding="utf-8") for s in SUITES]
    texts += [(ROOT / "scripts" / f"{m}.py").read_text(encoding="utf-8") for m in sorted(_local_imports(entry))]
    named = set()
    for text in texts:
        named |= set(re.findall(r"references/([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.*-]+)?)", text))  # "references/x.json"
        named |= set(re.findall(r'"references"\s*/\s*"([A-Za-z0-9_.-]+)"', text))  # root / "references" / "x.json"
    paths = {("references/" + n).rstrip(".").split("*")[0].rstrip("/") for n in named if n}
    paths = {p for p in paths if (ROOT / p).exists()}
    missing = sorted(p for p in paths if not cls.touches([p], INPUTS) and not any(i.startswith(p + "/") for i in INPUTS))
    assert not missing, f"add to scripts/ci_long_suite_inputs.txt: {missing}"


def test_records_under_references_are_not_inputs():
    for rec in ("references/branch-deletions.log.csv", "references/pending-security-rows.csv",
                "references/public-export.toml"):
        assert not cls.touches([rec], INPUTS), rec


def test_every_registry_validate_registries_reads_is_an_input():
    """validate_registries.py builds registry paths with f"{name}.json", which the scan above can't see."""
    import validate_registries as vr
    for name, *_ in vr.REGISTRIES:
        for path in (f"references/{name}.json", f"references/schemas/{name}.schema.json"):
            assert cls.touches([path], INPUTS), path
