"""Build hook (D35): the wheel carries the harness under mathagents/_harness/, with the checkout's layout.

The harness files stay where they are in the checkout (scripts/, references/, docs/, .github/agents/),
so nothing is duplicated in git; their list lives in mathagents/_harness_files.py. An editable install
uses the checkout itself and copies nothing.
"""
import importlib.util
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_harness_files", HERE / "mathagents" / "_harness_files.py")
_files = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_files)


def _copy(dest: Path) -> None:
    for rel in _files.ALL:
        src = HERE / rel
        if not src.is_file():
            raise FileNotFoundError(f"harness file missing from the checkout: {rel}")
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest / rel)


class BuildPyWithHarness(build_py):
    def run(self):
        super().run()
        if not getattr(self, "editable_mode", False):
            _copy(Path(self.build_lib) / "mathagents" / "_harness")


class SdistWithHarness(sdist):
    def make_release_tree(self, base_dir, files):
        super().make_release_tree(base_dir, files)
        _copy(Path(base_dir))


setup(cmdclass={"build_py": BuildPyWithHarness, "sdist": SdistWithHarness})
