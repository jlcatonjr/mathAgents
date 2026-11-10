#!/usr/bin/env python3
"""Resolve the Lean and Mathlib documentation that matches the toolchain the instance pins.

Agents cite the documentation of the Lean version the target work builds with, never `latest` and never a
version written into an agent file: an instance on v4.32.1 and one on v4.34.1 read different references.
The pin is the instance's `lean/lean-toolchain` (e.g. `leanprover/lean4:v4.32.1`) and, for Mathlib, the rev
recorded in `lean/lake-manifest.json`.

- Lean reference: the versioned manual, exact release first, else the minor's `X.Y.0` edition (the manual
  is not published for every patch release). `--online` probes the candidates and picks the first that
  resolves; offline, both are listed in order.
- Mathlib: its online docs track master only, so the pinned source is the authority. The rev's tree on
  GitHub and the local `lean/.lake/packages/mathlib` checkout are given; confirm names there or with the
  pinned name index (`build_name_index.py`).

Usage: python3 scripts/lean_docs.py [--json] [--online]
Exit 0 on success, 1 when lean/lake-manifest.json is unreadable or its mathlib entry has no rev, 2 when the
instance has no readable lean-toolchain.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lean_pin  # noqa: E402  (the pin: one reader for every gate)
from instance_root import instance_root  # noqa: E402

REFERENCE = "https://lean-lang.org/doc/reference/{}/"
RELEASE_NOTES = "{}releases/v{}/"
LEAN_SOURCE = "https://github.com/leanprover/lean4/tree/v{}"
MATHLIB_SOURCE = "https://github.com/leanprover-community/mathlib4/tree/{}"
MATHLIB_DOCS_MASTER = "https://leanprover-community.github.io/mathlib4_docs/"


def lean_version(lean_dir: Path) -> str | None:
    """The version in `lean-toolchain`, e.g. `4.32.1` or `4.35.0-rc1`; None when absent, unparsable, or not a
    numbered release (a nightly has no versioned manual)."""
    version = lean_pin.read_pin(lean_dir)["lean_release"]
    return version if version and not version.startswith("nightly-") else None


def reference_candidates(version: str) -> list[str]:
    """Versioned manual URLs, most specific first: the exact release, then the minor's `X.Y.0` edition."""
    major, minor = version.split(".")[:2]
    minor_edition = f"{major}.{minor}.0"
    return [REFERENCE.format(v) for v in dict.fromkeys((version, minor_edition))]


def mathlib_pin(lean_dir: Path) -> dict | None:
    """Mathlib's rev and input rev from `lake-manifest.json`; None when there is no manifest or Mathlib is not in it.
    Exits (status 1) when the manifest is unreadable or its mathlib entry has no rev."""
    try:
        pkg = lean_pin.manifest_mathlib(lean_dir)
    except lean_pin.ManifestError as exc:
        raise SystemExit(f"lean_docs: {exc}; run `lake update`")
    if pkg is None:
        return None
    if not isinstance(pkg["rev"], str) or not pkg["rev"]:
        raise SystemExit("lean_docs: lean/lake-manifest.json has a mathlib package with no rev; run `lake update`")
    local = lean_dir / ".lake" / "packages" / "mathlib"
    return {"rev": pkg["rev"], "input_rev": pkg["input_rev"], "source": MATHLIB_SOURCE.format(pkg["rev"]),
            "local_source": str(local.relative_to(lean_dir.parent)), "local_present": local.is_dir(),
            "online_docs": MATHLIB_DOCS_MASTER, "online_docs_pinned": False}


def resolves(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (fixed https hosts above)
            return resp.status == 200
    except OSError:
        return False


def resolve(root: Path, online: bool) -> dict | None:
    lean_dir = root / "lean"
    version = lean_version(lean_dir)
    if version is None:
        return None
    candidates = reference_candidates(version)
    reference = next((u for u in candidates if resolves(u)), None) if online else None
    major, minor = version.split(".")[:2]
    # the release notes live inside each versioned manual; use the minor's X.Y.0 edition, which always has them
    notes_base = candidates[-1]
    return {"lean": {"version": version, "toolchain_file": "lean/lean-toolchain",
                     "reference": reference, "reference_candidates": candidates, "probed": online,
                     "release_notes": RELEASE_NOTES.format(notes_base, f"{major}.{minor}.0"),
                     "source": LEAN_SOURCE.format(version)},
            "mathlib": mathlib_pin(lean_dir)}


def render(info: dict) -> str:
    lean, mathlib = info["lean"], info["mathlib"]
    out = [f"Lean {lean['version']} (pinned in {lean['toolchain_file']})"]
    if lean["probed"]:
        out.append(f"  reference:     {lean['reference'] or 'NONE RESOLVED (do not fall back to latest silently)'}")
    else:
        out.append("  reference:     first that resolves of " + ", ".join(lean["reference_candidates"]))
    out += [f"  release notes: {lean['release_notes']}", f"  source:        {lean['source']}"]
    if mathlib:
        out += [f"Mathlib {mathlib['rev']} (inputRev {mathlib['input_rev']}, lean/lake-manifest.json)",
                f"  source:        {mathlib['source']}",
                f"  local source:  {mathlib['local_source']}"
                f"{'' if mathlib['local_present'] else ' (absent: run `lake exe cache get` in lean/)'}",
                f"  online docs:   {mathlib['online_docs']} (tracks master, NOT this pin: confirm names in the "
                "pinned source or the name index)"]
    else:
        out.append("Mathlib: not a dependency of this instance")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="print the resolution as JSON")
    ap.add_argument("--online", action="store_true", help="probe the reference candidates (network)")
    args = ap.parse_args()
    info = resolve(instance_root(), args.online)
    if info is None:
        print(f"lean_docs: no readable lean/lean-toolchain under {instance_root()}", file=sys.stderr)
        return 2
    print(json.dumps(info, indent=2) if args.json else render(info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
