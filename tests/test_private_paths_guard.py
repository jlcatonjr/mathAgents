"""The tmp/ private-paths pre-commit guard (pr11 P12 L5): tmp/ holds this checkout's private records and plans."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "hooks" / "private-paths-guard.sh"
INSTALL = ROOT / "scripts" / "install_private_paths_guard.sh"
BEGIN = "# >>> MATHAGENTS:private-paths-guard >>>"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def make_repo(tmp_path: Path, hook: str | None = None) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts" / "hooks").mkdir(parents=True)
    git(repo, "init", "-q")
    shutil.copy(GUARD, repo / "scripts" / "hooks" / "private-paths-guard.sh")
    shutil.copy(INSTALL, repo / "scripts" / "install_private_paths_guard.sh")
    (repo / ".gitignore").write_text("tmp/\n")
    if hook is not None:
        (repo / ".git" / "hooks" / "pre-commit").write_text(hook)
    r = subprocess.run(["bash", str(repo / "scripts" / "install_private_paths_guard.sh")], capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stderr
    return repo


def test_refuses_force_added_tmp_file(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "tmp" / "private-records").mkdir(parents=True)
    (repo / "tmp" / "private-records" / "note.md").write_text("private\n")
    assert git(repo, "add", "-f", "tmp/private-records/note.md").returncode == 0
    r = git(repo, "commit", "-q", "-m", "x")
    assert r.returncode != 0 and "refusing to commit files under tmp/" in r.stderr, r.stderr


def test_allows_ordinary_commit_and_deletion_of_tmp_path(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "README.md").write_text("ok\n")
    git(repo, "add", "README.md", ".gitignore", "scripts")
    assert git(repo, "commit", "-q", "-m", "ok").returncode == 0
    # a tmp/ path committed by mistake (hook bypassed) can still be removed
    (repo / "tmp").mkdir()
    (repo / "tmp" / "x.md").write_text("x\n")
    git(repo, "add", "-f", "tmp/x.md")
    assert git(repo, "commit", "-q", "--no-verify", "-m", "mistake").returncode == 0
    git(repo, "rm", "-q", "--cached", "tmp/x.md")
    r = git(repo, "commit", "-q", "-m", "remove")
    assert r.returncode == 0, r.stderr


def test_install_is_idempotent_and_runs_before_an_exiting_block(tmp_path):
    hook = "#!/bin/sh\n# >>> AGENTTEAMS:x >>>\nexit 0\n# <<< AGENTTEAMS:x <<<\n"
    repo = make_repo(tmp_path, hook=hook)
    subprocess.run(["bash", str(repo / "scripts" / "install_private_paths_guard.sh")], check=True,
                   capture_output=True)
    text = (repo / ".git" / "hooks" / "pre-commit").read_text()
    assert text.count(BEGIN) == 1
    assert text.index(BEGIN) < text.index("# >>> AGENTTEAMS:x >>>")
    (repo / "tmp").mkdir()
    (repo / "tmp" / "p.md").write_text("p\n")
    git(repo, "add", "-f", "tmp/p.md")
    assert git(repo, "commit", "-q", "-m", "x").returncode != 0


def test_guard_fails_closed_outside_a_repository(tmp_path):
    r = subprocess.run(["sh", str(GUARD)], cwd=tmp_path, capture_output=True, text=True,
                       env={**os.environ, "GIT_DIR": str(tmp_path / "nope")})
    assert r.returncode == 1 and "fail closed" in r.stderr, r.stderr


def test_installed_block_warns_when_guard_missing(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "scripts" / "hooks" / "private-paths-guard.sh").unlink()
    (repo / "a.md").write_text("a\n")
    git(repo, "add", "a.md")
    r = git(repo, "commit", "-q", "-m", "a")
    assert r.returncode == 0 and "NOT being checked" in r.stderr, r.stderr
