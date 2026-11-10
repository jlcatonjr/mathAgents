"""The decision-spec preflight (scripts/operator/check_decision_spec.py): it mirrors the security gate's author
and scope rules, so a spec that cannot clear is refused before the operator's key is read."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "operator"))
cds = pytest.importorskip("check_decision_spec")

GOOD = {"requesting_agent": "security", "author": "operator", "action_reviewed": "pin-x",
        "scope": "pin-x", "date": "2026-10-28", "timestamp": "2026-10-28"}


def _repo(tmp_path: Path, roster: str | None = None) -> Path:
    for rel in (".github/agents", ".claude/agents"):
        (tmp_path / rel / "references").mkdir(parents=True)
    if roster is not None:
        (tmp_path / ".github/agents" / cds.ROSTER).write_text(roster, encoding="utf-8")
    return tmp_path


def _problems(spec: dict, repo: Path, team: str = ".github/agents") -> list[str]:
    return cds.check(spec, team, repo)[0]


def test_good_spec_passes(tmp_path):
    assert _problems(GOOD, _repo(tmp_path)) == []


@pytest.mark.parametrize("change, reason", [
    ({"requesting_agent": "", "author": ""}, "no author"),
    ({"requesting_agent": "orchestrator"}, "not an approved security author"),
    ({"action_reviewed": ""}, "action_reviewed is empty"),
    ({"scope": "something-else"}, "does not contain action_reviewed"),
    ({"date": "<set at signing>"}, "date"),
    ({"timestamp": "today"}, "timestamp"),
])
def test_bad_specs_refused(tmp_path, change, reason):
    problems = _problems({**GOOD, **change}, _repo(tmp_path))
    assert any(reason in p for p in problems), problems


def test_author_rule_matches_gate(tmp_path):
    repo = _repo(tmp_path)
    # requesting_agent wins over author; "@" is stripped; owner is read when requesting_agent is empty
    assert _problems({**GOOD, "requesting_agent": "@security", "author": "x"}, repo) == []
    assert _problems({**GOOD, "requesting_agent": "", "owner": "Security"}, repo) == []
    assert "not an approved" in _problems({**GOOD, "requesting_agent": "", "author": "operator"}, repo)[0]


def test_scope_rule_matches_gate(tmp_path):
    repo = _repo(tmp_path)
    assert _problems({**GOOD, "scope": ""}, repo) == []
    assert _problems({**GOOD, "scope": "other; pin-x"}, repo) == []


def test_roster_overrides_default(tmp_path):
    repo = _repo(tmp_path, roster="# approvers\n@sec-lead\n")
    assert "not an approved" in _problems(GOOD, repo)[0]
    assert _problems({**GOOD, "requesting_agent": "sec-lead"}, repo) == []
    assert _problems(GOOD, _repo(tmp_path / "b", roster="# only comments\n")) == []


def _log(repo: Path, rows: list[tuple[str, str]]) -> None:
    lines = ["action_reviewed,derives_from"] + [f"{a},{d}" for a, d in rows]
    (repo / ".github/agents" / cds.LOG).write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_lineage_must_resolve_through_recorded_rows(tmp_path):
    repo = _repo(tmp_path)
    _log(repo, [("root-row", ""), ("child-row", "root-row"), ("broken-row", "missing-row")])
    assert _problems({**GOOD, "derives_from": "child-row"}, repo) == []
    assert "names no recorded decision row" in _problems({**GOOD, "derives_from": "charter-d36"}, repo)[0]
    assert any("missing-row" in p for p in _problems({**GOOD, "derives_from": "broken-row"}, repo))


def test_an_action_id_with_a_broken_recorded_lineage_cannot_clear(tmp_path):
    repo = _repo(tmp_path)
    _log(repo, [("root-row", ""), ("pin-x", "d18")])  # an earlier signed row for pin-x named a charter id
    assert any("'d18'" in p for p in _problems({**GOOD, "derives_from": "root-row"}, repo))


def test_team_dir_and_branch_tool_warning(tmp_path):
    repo = _repo(tmp_path)
    assert "not one --sign-decision writes to" in _problems(GOOD, repo, ".codex/agents")[0]
    spec = {**GOOD, "action_reviewed": "branch-cleanup:abc", "scope": "branch-cleanup:abc"}
    problems, warnings = cds.check(spec, ".github/agents", repo)
    assert problems == [] and "--team-dir .github/agents" in warnings[0]


def test_cli_exit_codes(tmp_path):
    repo = _repo(tmp_path)
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    good.write_text(json.dumps(GOOD), encoding="utf-8")
    bad.write_text(json.dumps({**GOOD, "requesting_agent": ""}), encoding="utf-8")
    assert cds.main([str(good), "--team-dir", ".github/agents", "--repo", str(repo)]) == 0
    assert cds.main([str(bad), "--team-dir", ".github/agents", "--repo", str(repo)]) == 1
    assert cds.main([str(tmp_path / "missing.json"), "--team-dir", ".github/agents", "--repo", str(repo)]) == 2


SPECS = sorted((ROOT / "docs" / "release").glob("*.decision-spec.json")) if (ROOT / "docs" / "release").is_dir() else []


@pytest.mark.skipif(not SPECS, reason="docs/release/ is not in this tree (the public export excludes it)")
@pytest.mark.parametrize("spec_path", SPECS, ids=lambda p: p.name)
def test_committed_specs_pass(spec_path):
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if "<" in str(spec.get("date", "")):
        spec["date"] = "2026-10-28"  # signing scripts set the date at signing time
    assert cds.check(spec, ".github/agents", ROOT)[0] == []
