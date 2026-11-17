"""The decision-spec preflight (scripts/operator/check_decision_spec.py): it mirrors the security gate's author
and scope rules, so a spec that cannot clear is refused before the operator's key is read."""
from __future__ import annotations

import csv
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


SPEC_DIRS = [ROOT / "docs" / "governance", ROOT / "docs" / "release"]  # docs/release/ only in the private history
SPECS = sorted(p for d in SPEC_DIRS if d.is_dir() for p in d.glob("*.decision-spec.json"))


def _dated(spec: dict) -> dict:
    """Signing scripts set the date at signing time (a DATE or <...> placeholder in the committed spec)."""
    for key in ("date", "timestamp"):
        if key in spec and (spec[key] == "DATE" or "<" in str(spec[key])):
            spec[key] = "2026-11-15"
    return spec


def _repo_with_unsigned_parents(tmp_path: Path) -> Path:
    """The team's real log and roster, plus a stand-in row for each committed spec not yet signed into the log.

    Lineage then resolves through committed specs (a child drafted before its parent is signed still checks), while
    an id that is neither recorded nor a committed spec still fails.
    """
    refs = tmp_path / ".github/agents/references"
    refs.mkdir(parents=True)
    real = ROOT / ".github/agents" / cds.LOG
    rows = list(csv.DictReader(real.open(encoding="utf-8", newline=""))) if real.exists() else []
    out = [(r.get("action_reviewed") or "", r.get("derives_from") or "") for r in rows]
    recorded = {a.strip().lower() for a, _ in out}
    for p in SPECS:
        s = json.loads(p.read_text(encoding="utf-8"))
        aid = str(s.get("action_reviewed") or "").strip().lower()
        if aid and aid not in recorded:
            out.append((aid, str(s.get("derives_from") or "")))
    with (refs / Path(cds.LOG).name).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["action_reviewed", "derives_from"])
        w.writerows(out)
    roster = ROOT / ".github/agents" / cds.ROSTER
    if roster.exists():
        (refs / Path(cds.ROSTER).name).write_text(roster.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


@pytest.mark.skipif(not SPECS, reason="no committed decision specs in docs/governance/ (or docs/release/)")
@pytest.mark.parametrize("spec_path", SPECS, ids=lambda p: p.name)
def test_committed_specs_pass(spec_path, tmp_path):
    spec = _dated(json.loads(spec_path.read_text(encoding="utf-8")))
    assert cds.check(spec, ".github/agents", _repo_with_unsigned_parents(tmp_path))[0] == []


def test_committed_spec_lineage_cannot_name_an_unknown_id(tmp_path):
    if not SPECS:
        pytest.skip("no committed decision specs")
    spec = _dated({**json.loads(SPECS[0].read_text(encoding="utf-8")), "derives_from": "no-such-row-anywhere"})
    assert any("no-such-row-anywhere" in p for p in cds.check(spec, ".github/agents", _repo_with_unsigned_parents(tmp_path))[0])
