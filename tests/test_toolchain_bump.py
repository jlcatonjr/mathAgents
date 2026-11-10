"""The toolchain-bump tools (scripts/toolchain_bump/): statement_drift.py on synthetic version repositories,
statement_types.py compare, and bump_trial.sh with a stub `lake`. No network, no Lean."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import json
import os

TOOLS = Path(__file__).resolve().parent.parent / "scripts" / "toolchain_bump"
TOOL = TOOLS / "statement_drift.py"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args], check=True,
                   capture_output=True)


def tagged_repo(root: Path, old: dict[str, str], new: dict[str, str]) -> Path:
    root.mkdir(parents=True)
    git(root, "init", "-q")
    for tag, files in (("v4.32.1", old), ("v4.34.1", new)):
        for rel in list(p.relative_to(root).as_posix() for p in root.rglob("*.lean")):
            if rel not in files:
                (root / rel).unlink()
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text)
        git(root, "add", "-A")
        git(root, "commit", "-q", "--allow-empty", "-m", tag)
        git(root, "tag", tag)
    return root


def lines(n: int, edit: int | None = None) -> str:
    return "".join("edited\n" if i == edit else f"line {i}\n" for i in range(1, n + 1))


def run(tmp: Path, deps: list[tuple[str, str, int, int]], mathlib: Path, lean4: Path):
    d = tmp / "deps.tsv"
    d.write_text("".join(f"{n}\t{m}\t{a}\t{b}\n" for n, m, a, b in deps))
    return subprocess.run([sys.executable, str(TOOL), "--lean-dir", str(tmp), "--old", "v4.32.1", "--new", "v4.34.1",
                           "--deps", str(d), "--repo", f"mathlib4={mathlib}", "--repo", f"lean4={lean4}"],
                          capture_output=True, text=True)


def test_classification(tmp_path):
    ml = tagged_repo(tmp_path / "mathlib4",
                     {"Mathlib/A.lean": lines(20), "Mathlib/B.lean": lines(20)},
                     {"Mathlib/A.lean": lines(20, edit=10), "Mathlib/B.lean": lines(20, edit=6)})
    core = tagged_repo(tmp_path / "lean4", {"src/Init/X.lean": lines(5)},
                       {"src/Init/X.lean": lines(5), "src/Init/New.lean": lines(5)})
    deps = [("A.changed", "Mathlib.A", 8, 12),      # line 10 edited inside the declaration
            ("B.adjacent", "Mathlib.B", 4, 4),      # line 6 edited: not adjacent, not flagged
            ("X.same", "Init.X", 2, 3),
            ("N.moved", "Init.New", 1, 2),          # file absent under OLD
            ("Q.other", "Qq.Macro", 1, 2),          # a package the screen does not cover
            ("Z.noRange", "Mathlib.A", 0, 0)]       # no declaration range
    r = run(tmp_path, deps, ml, core)
    assert r.returncode == 1, r.stdout
    out = r.stdout
    assert "changed 1, moved/new 1, unknown 2, unchanged 2" in out, out
    assert "changed      A.changed" in out and "moved_or_new N.moved" in out
    assert "B.adjacent" not in out and "X.same" not in out


def test_clean_screen_exits_0(tmp_path):
    ml = tagged_repo(tmp_path / "mathlib4", {"Mathlib/A.lean": lines(9)}, {"Mathlib/A.lean": lines(9, edit=9)})
    core = tagged_repo(tmp_path / "lean4", {"src/Init/X.lean": lines(3)}, {"src/Init/X.lean": lines(3)})
    r = run(tmp_path, [("A.f", "Mathlib.A", 1, 4)], ml, core)
    assert r.returncode == 0 and "changed 0" in r.stdout


def test_unreachable_repository_fails_closed(tmp_path):
    d = tmp_path / "deps.tsv"
    d.write_text("A.f\tMathlib.A\t1\t2\n")
    r = subprocess.run([sys.executable, str(TOOL), "--lean-dir", str(tmp_path), "--old", "v4.32.1", "--new", "v4.34.1",
                        "--deps", str(d), "--cache", str(tmp_path / "cache"), "--repo", f"lean4={tmp_path}",
                        ], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "GIT_ALLOW_PROTOCOL": "none"})
    assert r.returncode == 2 and "cannot fetch mathlib4" in r.stdout


def test_a_deletion_at_a_declaration_edge_is_flagged(tmp_path):
    old = lines(10)
    new = "".join(f"line {i}\n" for i in range(1, 11) if i != 5)  # line 5 deleted: new lines 4|5 straddle it
    ml = tagged_repo(tmp_path / "mathlib4", {"Mathlib/A.lean": old}, {"Mathlib/A.lean": new})
    core = tagged_repo(tmp_path / "lean4", {"src/Init/X.lean": lines(3)}, {"src/Init/X.lean": lines(3)})
    r = run(tmp_path, [("A.f", "Mathlib.A", 5, 7)], ml, core)
    assert r.returncode == 1 and "changed      A.f" in r.stdout


def test_an_empty_extraction_is_an_error_not_a_pass(tmp_path):
    ml = tagged_repo(tmp_path / "mathlib4", {"Mathlib/A.lean": lines(3)}, {"Mathlib/A.lean": lines(3)})
    core = tagged_repo(tmp_path / "lean4", {"src/Init/X.lean": lines(3)}, {"src/Init/X.lean": lines(3)})
    r = run(tmp_path, [], ml, core)
    assert r.returncode == 2 and "empty screen" in r.stdout


def test_statement_types_compare(tmp_path):
    old, new = tmp_path / "old.tsv", tmp_path / "new.tsv"
    old.write_text("ZIT.a\t@Eq Nat x y\nZIT.b\tTrue\nZIT.gone\tFalse\n")
    new.write_text("ZIT.a\t@Eq Int x y\nZIT.b\tTrue\nZIT.new\tTrue\n")
    cmd = [sys.executable, str(TOOLS / "statement_types.py"), "compare", str(old), str(new)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 1 and "changed 1, removed 1, added 1" in r.stdout
    assert subprocess.run(cmd[:-1] + [str(old)], capture_output=True).returncode == 0
    (tmp_path / "empty.tsv").write_text("")
    assert subprocess.run(cmd[:-2] + [str(old), str(tmp_path / "empty.tsv")], capture_output=True).returncode == 2


LAKEFILE = """name = "demo"
defaultTargets = ["Ghost"]

[[require]]
name = "mathlib"
git = "https://github.com/leanprover-community/mathlib4"
rev = "v4.32.1"

[[lean_lib]]
name = "Ghost"

[[lean_lib]]
name = "Demo"
"""


@pytest.fixture
def package(tmp_path):
    pkg = tmp_path / "src" / "lean"
    (pkg / "Demo").mkdir(parents=True)
    (pkg / "lakefile.toml").write_text(LAKEFILE)
    (pkg / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n")
    (pkg / "Demo.lean").write_text("import Demo.A\n")
    (pkg / "Demo" / "A.lean").write_text("theorem t : True := by\n  trivial\n")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": "1.1.0", "packagesDir": ".lake/packages", "name": "other",
                                    "packages": [{"name": "mathlib", "inputRev": "v4.34.1", "rev": "abc"}]}))
    (tmp_path / "packages").mkdir()
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "lake").write_text("#!/bin/sh\necho \"stub lake $*\"\nexit ${STUB_LAKE_EXIT:-0}\n")
    (stub / "lake").chmod(0o755)
    return tmp_path


def bump(base: Path, *extra: str, exit_code: int = 0):
    # the active interpreter first after the stubs: /usr/bin/python3 is 3.9 on macOS (no tomllib)
    env = dict(os.environ, PATH=f"{base / 'bin'}:{Path(sys.executable).parent}:/usr/bin:/bin", HOME=str(base),
               STUB_LAKE_EXIT=str(exit_code))
    return subprocess.run(["bash", str(TOOLS / "bump_trial.sh"), "--from", "src/lean", "--to", "trials/t1",
                           "--tag", "v4.34.1", "--manifest-from", "manifest.json", "--packages-from", "packages",
                           *extra], cwd=base, capture_output=True, text=True, env=env)


def test_bump_trial_retargets_a_copy_with_relative_paths(package):
    patch = package / "fix.patch"
    patch.write_text("--- a/Demo/A.lean\n+++ b/Demo/A.lean\n@@ -1,2 +1,2 @@\n theorem t : True := by\n-  trivial\n+  exact True.intro\n")
    r = bump(package, "--wip-lib", "DemoWIP", "--patch", "fix.patch")
    assert r.returncode == 0, r.stdout + r.stderr
    t = package / "trials" / "t1" / "lean"
    import tomllib
    cfg = tomllib.loads((t / "lakefile.toml").read_text())
    assert [r["rev"] for r in cfg["require"]] == ["v4.34.1"]
    assert sorted(l["name"] for l in cfg["lean_lib"]) == ["Demo", "DemoWIP"] == sorted(cfg["defaultTargets"])
    assert (t / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"
    assert "exact True.intro" in (t / "Demo" / "A.lean").read_text()
    assert json.loads((t / "lake-manifest.json").read_text())["name"] == "demo"
    assert (t / ".lake" / "packages").resolve() == (package / "packages").resolve()
    assert (package / "src" / "lean" / "lakefile.toml").read_text() == LAKEFILE  # source untouched
    assert "trivial" in (package / "src" / "lean" / "Demo" / "A.lean").read_text()


def test_bump_trial_never_overwrites_and_reports_build_failure(package):
    assert bump(package).returncode == 0
    r = bump(package)
    assert r.returncode == 2 and "never overwrites" in r.stderr
    (package / "trials" / "t2").mkdir()
    env_fail = bump(package, exit_code=1)
    assert env_fail.returncode == 2  # t1 exists
    import shutil
    shutil.rmtree(package / "trials" / "t1")
    assert bump(package, exit_code=1).returncode == 1  # the stub build fails


def test_bump_trial_refuses_a_lakefile_it_cannot_retarget(package):
    lf = package / "src" / "lean" / "lakefile.toml"
    lf.write_text(LAKEFILE.replace('rev = "v4.32.1"\n', ""))  # no rev to retarget
    r = bump(package)
    assert r.returncode == 2 and "mathlib rev" in r.stderr


def test_shared_packages_need_a_manifest(package):
    env = dict(os.environ, PATH=f"{package / 'bin'}:{Path(sys.executable).parent}:/usr/bin:/bin", HOME=str(package))
    r = subprocess.run(["bash", str(TOOLS / "bump_trial.sh"), "--from", "src/lean", "--to", "trials/t9", "--tag",
                        "v4.34.1", "--packages-from", "packages"], cwd=package, capture_output=True, text=True, env=env)
    assert r.returncode == 2 and "needs --manifest-from" in r.stderr
    assert not (package / "trials" / "t9").exists()


def test_bump_trial_refuses_a_manifest_for_another_tag(package):
    m = package / "manifest.json"
    m.write_text(m.read_text().replace("v4.34.1", "v4.33.0"))
    r = bump(package)
    assert r.returncode == 2 and "pins mathlib" in r.stderr


def test_a_lean_lib_without_sources_is_not_the_proved_library(tmp_path):
    sys.path.insert(0, str(TOOLS))
    from lean_template import proved_library

    (tmp_path / "lakefile.toml").write_text(LAKEFILE)  # Ghost has no sources, Demo has
    (tmp_path / "Demo.lean").write_text("")
    assert proved_library(tmp_path) == "Demo"
    (tmp_path / "Demo.lean").unlink()
    with pytest.raises(RuntimeError):
        proved_library(tmp_path)
