"""Preparation for agentteams' write_policy pilot (P5): the strategy-review proposal gate, and gate temp files kept
inside lean/.lake (the only lean/ path a confined run may write)."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "check_strategy_sha.py"


def run(proposal: str, dest: Path, tmp: Path) -> subprocess.CompletedProcess:
    f = tmp / "proposal.md"
    f.write_text(proposal)
    return subprocess.run([sys.executable, str(GATE), str(f), str(dest)], capture_output=True, text=True)


def dossier(tmp: Path, strategy: str | None = "# Strategy\n\nInduct on n.\n") -> Path:
    d = tmp / "reports" / "dossiers" / "demo"
    d.mkdir(parents=True)
    if strategy is not None:
        (d / "strategy.md").write_text(strategy)
    return d / "strategy-review.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_a_review_naming_the_current_strategy_passes(tmp_path):
    dest = dossier(tmp_path)
    r = run(f"## Round 1\n\nStrategy sha256: {sha(dest.parent / 'strategy.md')}\n\nVerdict: CLEARED\n", dest, tmp_path)
    assert r.returncode == 0, r.stdout


def test_a_stale_or_missing_sha_is_refused(tmp_path):
    dest = dossier(tmp_path)
    assert run("## Round 1\n\nStrategy sha256: " + "0" * 64 + "\n\nVerdict: CLEARED\n", dest, tmp_path).returncode == 1
    r = run("## Round 1\n\nVerdict: CLEARED\n", dest, tmp_path)
    assert r.returncode == 1 and "Strategy sha256" in r.stdout


def test_the_latest_round_decides(tmp_path):
    dest = dossier(tmp_path)
    cur = sha(dest.parent / "strategy.md")
    old = "## Round 1\n\nStrategy sha256: " + "1" * 64 + "\n\nVerdict: BLOCKED\n\n"
    assert run(old + f"## Round 2\n\nStrategy sha256: {cur}\n\nVerdict: CLEARED\n", dest, tmp_path).returncode == 0
    assert run(f"## Round 1\n\nStrategy sha256: {cur}\n\nVerdict: CLEARED\n\n" + old, dest, tmp_path).returncode == 1


def test_a_review_before_its_strategy_or_without_a_verdict_is_refused(tmp_path):
    dest = dossier(tmp_path, strategy=None)
    r = run("Strategy sha256: " + "0" * 64 + "\nVerdict: CLEARED\n", dest, tmp_path)
    assert r.returncode == 1 and "apply strategy.md before" in r.stdout
    dest2 = dossier(tmp_path / "b")
    assert run(f"Strategy sha256: {sha(dest2.parent / 'strategy.md')}\n", dest2, tmp_path).returncode == 1


def test_a_blocked_round_must_name_its_strategy_too(tmp_path):
    """Stricter than the validator (which checks CLEARED rounds only): any proposed round names what it reviewed."""
    dest = dossier(tmp_path)
    assert run("## Round 1\n\nVerdict: BLOCKED\n", dest, tmp_path).returncode == 1
    cur = sha(dest.parent / "strategy.md")
    assert run(f"## Round 1\n\nStrategy sha256: {cur}\n\nVerdict: BLOCKED\n", dest, tmp_path).returncode == 0


def test_a_sha_inside_a_code_fence_does_not_count(tmp_path):
    dest = dossier(tmp_path)
    cur = sha(dest.parent / "strategy.md")
    r = run(f"## Round 1\n\n```\nStrategy sha256: {cur}\n```\n\nVerdict: CLEARED\n", dest, tmp_path)
    assert r.returncode == 1 and "Strategy sha256" in r.stdout


def test_wrong_destination_and_usage_errors(tmp_path):
    dest = dossier(tmp_path)
    r = run("Verdict: CLEARED\n", dest.parent / "strategy.md", tmp_path)
    assert r.returncode == 1 and "checks strategy-review.md" in r.stdout
    assert subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True).returncode == 2


def test_gate_temp_files_stay_inside_lean_dot_lake():
    for script in ("proof_integrity.py", "build_name_index.py"):
        src = (ROOT / "scripts" / script).read_text()
        assert 'dir=lean_dir, delete=False' not in src, script
        assert 'lean_dir / ".lake" / "tmp"' in src, script
