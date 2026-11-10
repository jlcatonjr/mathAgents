#!/usr/bin/env python3
"""Write a dossier's kernel snapshot at Stage 8 assembly (spec DD-19, DD-43). Fail-closed.

  snapshot_kernel.py <slug>

Copies, from the current and fresh G-KERNEL report (verdict PASS, source hash matching the Lean tree),
the provenance fields and every declaration under the dossier's `lean_namespace` into
`reports/dossiers/<slug>/kernel-snapshot.json`, so the dossier's claims are tied to one checked state
of the library. The dossier validator then checks the snapshot against the fidelity record.
Exit 0 = written; 1 = refused; 2 = error.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_dossier as vd  # noqa: E402
from instance_root import instance_root  # noqa: E402

PROVENANCE = ("gate", "verdict", "checked_at", "lean_version", "toolchain_pin", "commit", "dirty", "source_sha256")


def snapshot(root: Path, slug: str, write: bool = True) -> tuple[dict | None, str]:
    """(snapshot, message) on success, written to the dossier unless write=False; (None, reason) when
    refused. For main() and the mathagents API; slug must already be valid."""
    dossier = root / "reports" / "dossiers" / slug
    fid = dossier / "fidelity.json"
    if not fid.exists():
        return None, f"{slug} has no fidelity record"
    report_path = root / "reports" / "kernel" / "latest.json"
    kernel, problem = vd.load_kernel(root, report_path)
    if kernel is None:
        return None, str(problem)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    ns = json.loads(fid.read_text(encoding="utf-8"))["lean_namespace"].rstrip(".") + "."
    if report.get("dirty"):
        return None, "the kernel report was taken from a dirty lean/ tree; commit first"
    snap = {k: report.get(k) for k in PROVENANCE}
    snap["lean_namespace"] = ns[:-1]
    snap["declarations"] = sorted((d for d in report["declarations"] if d["decl"].startswith(ns)), key=lambda d: d["decl"])
    verb = "wrote" if write else "would write"
    if write:
        (dossier / "kernel-snapshot.json").write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    return snap, f"{verb} {len(snap['declarations'])} declaration(s) for {slug} at commit {snap['commit']}"


def main(argv: list[str]) -> int:
    root = instance_root()
    if len(argv) >= 3 and argv[1] == "--root":  # tests only: writing into another tree is not a product path
        if os.environ.get("MATHAGENTS_TEST") != "1":
            print("snapshot_kernel: REFUSED: --root is for the test suite (set MATHAGENTS_TEST=1)")
            return 2
        root, argv = Path(argv[2]).resolve(), [argv[0]] + argv[3:]
    # MATHAGENTS_ROOT (D35) may name only this checkout or a declared instance, never an arbitrary tree
    elif root != Path(__file__).resolve().parent.parent and not (root / "mathagents.toml").is_file() \
            and os.environ.get("MATHAGENTS_TEST") != "1":
        print(f"snapshot_kernel: REFUSED: {root} is not a mathAgents instance (no mathagents.toml)")
        return 2
    if len(argv) != 2:
        print(__doc__)
        return 2
    slug = argv[1]
    if not vd.SLUG.fullmatch(slug):
        print(f"snapshot_kernel: REFUSED: invalid slug {slug!r}")
        return 2
    snap, msg = snapshot(root, slug)
    if snap is None:
        print(f"snapshot_kernel: REFUSED: {msg}")
        return 1
    print(f"snapshot_kernel: {msg}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:  # fail closed
        print(f"snapshot_kernel: error: {exc!r}")
        sys.exit(2)
