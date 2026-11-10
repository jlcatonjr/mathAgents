"""The signing helper (scripts/operator/lib_signer.sh): signer_check refuses a signer whose ownership, PROVENANCE.json
or installed package set differs from the provisioned one. Tests build a fake signer in a temporary directory and
reassign the helper's variables after sourcing it; the helper itself reads nothing from the environment."""
from __future__ import annotations

import getpass
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "scripts" / "operator" / "lib_signer.sh"
FRAMEWORK = Path("/Library/Frameworks/Python.framework/Versions/3.13")
BASE_PY = FRAMEWORK / "bin" / "python3.13"
pytestmark = pytest.mark.skipif(sys.platform != "darwin" or not BASE_PY.exists(),
                                reason="needs the operator's macOS and the python.org 3.13 framework")

PKGSET = """
import hashlib, importlib.metadata as m
s = "\\n".join(sorted({d.metadata["Name"].lower().replace("_", "-") + "==" + d.version for d in m.distributions()}))
print(hashlib.sha256((s + "\\n").encode()).hexdigest())
"""


def _fake_signer(tmp: Path) -> tuple[Path, str]:
    root = tmp / "signer"
    (root / "bin").mkdir(parents=True)
    os.symlink(BASE_PY, root / "bin" / "python")
    pkgset = subprocess.run([str(BASE_PY), "-I", "-c", PKGSET], capture_output=True, text=True,
                            check=True).stdout.strip()
    (root / "PROVENANCE.json").write_text(json.dumps({"commit": "c", "tag_signer": "f", "package_set_sha256": pkgset}))
    return root, pkgset


def _run(root: Path, pkgset: str, parents: int = 0, framework: Path = FRAMEWORK) -> subprocess.CompletedProcess:
    version = subprocess.run([str(BASE_PY), "-I", "-c", "import platform; print(platform.python_version())"],
                             capture_output=True, text=True, check=True).stdout.strip()
    script = (f'source "{LIB}"; SIGNER_ROOT="{root}"; SIGNER_OWNER="{getpass.getuser()}"; SIGNER_COMMIT=c; '
              f'SIGNER_TAG_FPR=f; SIGNER_SET={pkgset}; SIGNER_CHECK_PARENTS={parents}; '
              f'SIGNER_FRAMEWORK="{framework}"; SIGNER_PYVERSION={version}; '
              'signer_check && echo "OK $SIGNER_PY"')
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True)


def test_accepts_an_intact_signer(tmp_path):
    root, pkgset = _fake_signer(tmp_path)
    r = _run(root, pkgset)
    assert r.returncode == 0 and r.stdout.startswith("OK "), r.stderr


def test_refuses_a_changed_package_set(tmp_path):
    root, _ = _fake_signer(tmp_path)
    r = _run(root, "0" * 64)
    assert r.returncode != 0 and "differ" in r.stderr


def test_refuses_a_pth_file(tmp_path):
    root, pkgset = _fake_signer(tmp_path)
    (root / "x.pth").write_text("import os\n")
    r = _run(root, pkgset)
    assert r.returncode != 0 and ".pth" in r.stderr


def test_refuses_a_group_writable_file(tmp_path):
    root, pkgset = _fake_signer(tmp_path)
    (root / "PROVENANCE.json").chmod(0o664)
    r = _run(root, pkgset)
    assert r.returncode != 0 and "writable by others" in r.stderr


def test_refuses_a_different_base_interpreter(tmp_path):
    root, pkgset = _fake_signer(tmp_path)
    other = tmp_path / "other-framework"; other.mkdir()
    r = _run(root, pkgset, framework=other)
    assert r.returncode != 0 and "base interpreter" in r.stderr


def test_signer_run_needs_signer_check_and_runs_isolated():
    text = LIB.read_text()
    assert '"$SIGNER_PY" -I "$SIGNER_ROOT/bin/agentteams" "$@"' in text
    r = subprocess.run(["bash", "-c", f'source "{LIB}"; signer_run --version'], capture_output=True, text=True)
    assert r.returncode != 0 and "call signer_check" in r.stderr
    env = {**os.environ, "SIGNER_PY": "/bin/echo"}  # an inherited value must not skip the gate
    r = subprocess.run(["bash", "-c", f'source "{LIB}"; signer_run x'], capture_output=True, text=True, env=env)
    assert r.returncode != 0 and "call signer_check" in r.stderr


def test_system_tools_are_called_by_absolute_path():
    body = LIB.read_text().split("_signer_die()")[1]
    for tool in ("stat", "find", "dirname"):
        assert f" {tool} " not in body.replace(f"/usr/bin/{tool} ", ""), tool


def test_refuses_a_missing_signer(tmp_path):
    r = _run(tmp_path / "absent", "0" * 64)
    assert r.returncode != 0 and "no signer" in r.stderr


def test_the_parent_walk_refuses_a_group_writable_parent(tmp_path):
    parent = tmp_path / "shared"; parent.mkdir(); parent.chmod(0o775)
    root, pkgset = _fake_signer(parent)
    r = _run(root, pkgset, parents=1)
    assert r.returncode != 0 and "group- or world-writable" in r.stderr


def test_the_helper_is_fixed_to_the_root_owned_signer():
    text = LIB.read_text()
    assert "SIGNER_ROOT=/opt/agentteams-signer-v1.0.0" in text and "SIGNER_OWNER=root" in text
    assert "SIGNER_CHECK_PARENTS=1" in text and "SIGNER_FRAMEWORK=/Library/Frameworks/Python.framework/Versions/3.13" in text
    head = text.split("signer_check()")[0]
    assert "${SIGNER_ROOT" not in head and "${SIGNER_OWNER" not in head  # nothing from the environment
    assert "anaconda3" not in text.replace("/opt/anaconda3 is not used for signing", "")
