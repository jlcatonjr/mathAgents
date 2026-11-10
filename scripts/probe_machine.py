#!/usr/bin/env python3
"""Probe this machine's hardware and installed engines; write .machine/profile.json.

The repository is shared by machines with very different GPUs, so engine availability is a
per-machine fact, never a committed one. @engine-advisor joins this profile with
references/prover-engines.json to decide what it may offer in a session.

`lean_version` is the Lean that runs in the instance's `lean/` (elan selects it from `lean/lean-toolchain`, unless an
override such as ELAN_TOOLCHAIN, recorded as `elan_toolchain_override`, selects another), and only when that
toolchain is installed: the probe never makes elan download one. `lean_version_source` says which it is. It is
evidence about this machine, never the pin (docs/lean-version-governance.md): the pin is `lean/lean-toolchain`.

Usage: python3 scripts/probe_machine.py [--print]
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lean_pin  # noqa: E402  (the instance's lean-toolchain)
from instance_root import instance_root  # noqa: E402

ROOT = instance_root()
OUT = ROOT / ".machine" / "profile.json"

# Executables and Python modules that correspond to engine ids in references/prover-engines.json.
EXECUTABLES = {"lean": "lean", "lake": "lake", "z3": "z3", "cvc5": "cvc5", "vampire": "vampire",
               "eprover": "eprover", "ollama": "ollama", "llama-server": "llama-server",
               "pandoc": "pandoc", "dot": "dot", "leanblueprint": "leanblueprint"}
PY_MODULES = {"z3-solver": "z3", "cvc5-python": "cvc5"}


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20, cwd=cwd).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def toolchain_installed(toolchain: str, elan_home: Path) -> bool:
    """Whether elan has ``toolchain`` (e.g. `leanprover/lean4:v4.32.1`) installed, so running it downloads nothing."""
    return (elan_home / "toolchains" / toolchain.strip().replace("/", "--").replace(":", "---")).is_dir()


def lean_versions(elan_bin: Path) -> dict:
    """The instance's Lean: run in lean/, and only when the toolchain elan would select there is installed."""
    lean, override = str(elan_bin / "lean"), os.environ.get("ELAN_TOOLCHAIN") or None
    pinned = lean_pin.read_pin(ROOT / "lean")["toolchain"]
    selected = override or pinned
    if pinned is None:
        version, source = None, "no lean/lean-toolchain in the instance"
    elif not toolchain_installed(selected, elan_bin.parent):
        version, source = None, f"{selected} is not installed (not probed: running it would download it)"
    else:
        version = _run([lean, "--version"], cwd=ROOT / "lean") or None
        source = ("instance lean/ under the elan override ELAN_TOOLCHAIN (not the pin)" if override
                  else "instance lean/ (lean/lean-toolchain)")
    return {"lean_version": version, "lean_version_source": source, "elan_toolchain_override": override}


def gpus() -> list[dict]:
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    found = []
    for line in filter(None, out.splitlines()):
        name, mem = (s.strip() for s in line.rsplit(",", 1))
        found.append({"vendor": "nvidia", "name": name, "vram_gb": round(int(mem) / 1024, 1)})
    return found


def ram_gb() -> float | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 1024 / 1024, 1)
    except OSError:
        pass
    return None


def main() -> int:
    elan_bin = Path.home() / ".elan" / "bin"
    path = os.environ.get("PATH", "") + os.pathsep + str(elan_bin)
    execs = {k: bool(shutil.which(v, path=path)) for k, v in EXECUTABLES.items()}
    mods = {}
    for k, mod in PY_MODULES.items():
        try:
            __import__(mod)
            mods[k] = True
        except ImportError:
            mods[k] = False
    lean = lean_versions(elan_bin) if execs["lean"] else {"lean_version": None, "lean_version_source": "no lean",
                                                             "elan_toolchain_override": None}
    profile = {
        "probed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "os": platform.platform(), "cpu_threads": os.cpu_count(), "ram_gb": ram_gb(),
        "gpus": gpus(), **lean,
        "executables": execs, "python_modules": mods,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(profile, indent=2) + "\n")
    if "--print" in sys.argv:
        print(json.dumps(profile, indent=2))
    else:
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
