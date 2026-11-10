#!/usr/bin/env python3
"""Read the instance's Lean pin and check that its parts agree (docs/lean-version-governance.md, P1-P4).

The pin is three files under the instance's `lean/`, all required, none a fallback for another:
  P1  lean-toolchain                         the Lean release, e.g. `leanprover/lean4:v4.32.1`
  P2  lakefile.toml (or lakefile.lean)       the Mathlib `rev` the package requires; must equal P3's inputRev
  P3  lake-manifest.json, the mathlib entry  `rev` (the exact commit built) and `inputRev`
and one check of the build on disk:
  P4  .lake/packages/mathlib/lean-toolchain  the toolchain the Mathlib checkout was built for; must equal P1.
      Missing is normal on a fresh clone or in CI (`.lake/` is gitignored): it means "Mathlib not built for
      this pin", never "pin unknown".

A version written in prose (agent files, CLAUDE.md, the charter, guides, memory) is never the pin. What a past
gate run used is evidence about that run (the G-KERNEL report's `toolchain_pin` and `lean_version`), never the pin.

The gates import this module (G-KERNEL, the name index, the dossier validator, `mathagents doctor`); run as a
script it prints the pin and its findings, so an agent can check the pin (R1) in one command.

Usage: python3 scripts/lean_pin.py [--json]
Exit 0 = pin known and consistent (P4 notices do not fail); 1 = findings; 2 = no lean/lean-toolchain.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instance_root import instance_root  # noqa: E402

_RELEASE = re.compile(r"(?<![\d.])v?(\d+\.\d+\.\d+(?:-rc\d+)?)(?![\d.])")
_NIGHTLY = re.compile(r"nightly-(\d{4}-\d{2}-\d{2})")
_LEAN_VERSION = re.compile(r"\bversion (\d+\.\d+\.\d+(?:-rc\d+)?)(?:-nightly-(\d{4}-\d{2}-\d{2}))?")
_LAKEFILE_LEAN_MATHLIB = re.compile(r'\brequire\s+"?mathlib"?\s+from\s+git\s+"[^"]*"\s*@\s*"([^"]+)"')
# a line carrying this marker deliberately names the harness's own pin, not the instance's (`mathagents doctor`)
HARNESS_PIN_MARKER = "<!-- harness-pin -->"
# a Lean or Mathlib release written in prose, e.g. v4.32.1 or v4.35.0-rc1
PROSE_VERSION = re.compile(r"(?<![\w.])v4\.\d+\.\d+(?:-rc\d+)?(?![\w.])")


def release(text: str | None) -> str | None:
    """The release in a toolchain string (`leanprover/lean4:v4.32.1` -> `4.32.1`, `...:v4.35.0-rc1` ->
    `4.35.0-rc1`, `...:nightly-2026-10-01` -> `nightly-2026-10-01`) or in `lean --version` output
    (`Lean (version 4.32.1, ...)` -> `4.32.1`; a nightly build's `4.x.0-nightly-2026-10-01` -> `nightly-2026-10-01`);
    None when there is none."""
    if not text:
        return None
    m = _LEAN_VERSION.search(text)
    if m:
        return f"nightly-{m.group(2)}" if m.group(2) else m.group(1)
    m = _NIGHTLY.search(text)
    if m:
        return f"nightly-{m.group(1)}"
    m = _RELEASE.search(text)
    return m.group(1) if m else None


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


class LakefileError(ValueError):
    """lakefile.toml does not parse."""


def lakefile_rev(lean_dir: Path) -> str | None:
    """P2: the `rev` of the mathlib requirement in lakefile.toml (or lakefile.lean), None when absent. Raises
    LakefileError when lakefile.toml does not parse."""
    toml = lean_dir / "lakefile.toml"
    if toml.is_file():
        try:
            reqs = tomllib.loads(toml.read_text(encoding="utf-8")).get("require", [])
        except tomllib.TOMLDecodeError as exc:
            raise LakefileError(f"lakefile.toml does not parse ({exc})") from exc
        return next((r.get("rev") for r in reqs if r.get("name") == "mathlib"), None)
    text = _read(lean_dir / "lakefile.lean")
    m = _LAKEFILE_LEAN_MATHLIB.search(text or "")
    return m.group(1) if m else None


class ManifestError(ValueError):
    """lake-manifest.json exists but cannot be read as a Lake manifest: never the same as "no mathlib"."""


def manifest_mathlib(lean_dir: Path) -> dict | None:
    """P3: the manifest's mathlib entry (`rev`, `inputRev`); None when there is no manifest or it names no mathlib.
    Raises ManifestError when the manifest exists but is unreadable or not a Lake manifest."""
    path = lean_dir / "lake-manifest.json"
    if not path.exists():
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ManifestError(f"lean/lake-manifest.json is unreadable ({exc})") from exc
    packages = manifest.get("packages", []) if isinstance(manifest, dict) else None
    if not isinstance(packages, list) or not all(isinstance(p, dict) for p in packages):
        raise ManifestError("lean/lake-manifest.json is not a Lake manifest (`packages` is not a list of objects)")
    pkg = next((p for p in packages if p.get("name") == "mathlib"), None)
    return {"rev": pkg.get("rev"), "input_rev": pkg.get("inputRev")} if pkg else None


def read_pin(lean_dir: Path) -> dict:
    """P1-P4 as read from disk (None where a file or field is absent). ``uses_mathlib`` is False when neither the
    lakefile nor the manifest names mathlib, in which case P2-P4 do not apply."""
    toolchain = _read(lean_dir / "lean-toolchain")
    try:
        p2, lakefile_error = lakefile_rev(lean_dir), None
    except LakefileError as exc:
        p2, lakefile_error = None, str(exc)
    try:
        p3, manifest_error = manifest_mathlib(lean_dir), None
    except ManifestError as exc:
        p3, manifest_error = None, str(exc)
    checkout = _read(lean_dir / ".lake" / "packages" / "mathlib" / "lean-toolchain")
    return {"toolchain": toolchain, "lean_release": release(toolchain), "lakefile_rev": p2,
            "lakefile_error": lakefile_error,
            "mathlib_rev": (p3 or {}).get("rev"), "mathlib_input_rev": (p3 or {}).get("input_rev"),
            "manifest_error": manifest_error,
            "checkout_toolchain": checkout,
            "uses_mathlib": any(v is not None for v in (p2, p3, lakefile_error, manifest_error))}


NOT_BUILT = ("P4: Mathlib not built for this pin (no lean/.lake/packages/mathlib; run `lake exe cache get` in lean/); "
             "Mathlib lookups need the checkout or the name index")


def checkout_finding(pin: dict) -> str | None:
    """P4: a finding when the .lake Mathlib checkout was built for another toolchain than P1, else None (also when
    there is no checkout: see NOT_BUILT, a notice, not a finding)."""
    if not pin["uses_mathlib"] or pin["checkout_toolchain"] is None or not pin["toolchain"]:
        return None
    if pin["checkout_toolchain"] != pin["toolchain"]:
        return (f"P4: the Mathlib checkout in lean/.lake was built for {pin['checkout_toolchain']!r}, not the pin "
                f"{pin['toolchain']!r}; rebuild it (`lake exe cache get`, then `lake build`)")
    return None


def pin_findings(pin: dict) -> tuple[list[str], list[str]]:
    """(findings, notices) for P1-P3 of a pin from ``read_pin``. A finding means the pin is unknown or
    inconsistent (stop). The notice NOT_BUILT reports a missing Mathlib checkout, which blocks local Mathlib lookups
    but not the pin. P4 (a checkout built for another toolchain) is ``checkout_finding``: a gate that runs before
    lake checks the build out must not apply it yet."""
    findings, notices = [], []
    if not pin["toolchain"]:
        findings.append("P1: no lean/lean-toolchain")
    elif not pin["lean_release"]:
        findings.append(f"P1: lean/lean-toolchain names no release ({pin['toolchain']!r})")
    if not pin["uses_mathlib"]:
        return findings, notices
    if pin["lakefile_error"]:
        findings.append(f"P2: {pin['lakefile_error']}")
    elif pin["lakefile_rev"] is None:
        findings.append("P2: the lakefile requires no mathlib `rev`")
    if pin.get("manifest_error"):
        findings.append(f"P3: {pin['manifest_error']}")
    elif not pin["mathlib_rev"]:
        findings.append("P3: lean/lake-manifest.json has no mathlib entry with a rev (run `lake update` once on an "
                        "authorised bump, and commit it)")
    if pin["lakefile_rev"] is not None and pin["mathlib_input_rev"] is not None \
            and pin["lakefile_rev"] != pin["mathlib_input_rev"]:
        findings.append(f"P2: the lakefile's mathlib rev {pin['lakefile_rev']!r} differs from the manifest's inputRev "
                        f"{pin['mathlib_input_rev']!r}: the manifest was not updated with the lakefile")
    if pin["checkout_toolchain"] is None:
        notices.append(NOT_BUILT)
    return findings, notices


def toolchain_mismatch(ran: str | None, toolchain: str | None) -> str | None:
    """A finding when the Lean that ran (``lean --version`` output) is not the pinned release, else None. An elan
    override (``ELAN_TOOLCHAIN``, ``elan override``, ``+<toolchain>``) is the usual cause."""
    want, got = release(toolchain), release(ran)
    if want is None:
        return f"toolchain: lean-toolchain names no release ({toolchain!r})"
    if got is None:
        return f"toolchain: cannot read the Lean release from `lean --version` ({(ran or '').strip()[:120]!r})"
    if got != want:
        return (f"toolchain: the Lean that ran is {got} (`lean --version`) but lean-toolchain pins {want} "
                f"({toolchain}); an elan override (ELAN_TOOLCHAIN, `elan override`) selects another toolchain")
    return None


def stale_versions(text: str, lean_release: str | None) -> list[tuple[int, str]]:
    """(line number, version) for each Lean/Mathlib release in ``text`` other than ``lean_release``. Lines that
    carry HARNESS_PIN_MARKER are exempt: they describe the harness's own pin on purpose."""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        if HARNESS_PIN_MARKER in line:
            continue
        hits += [(n, v) for v in PROSE_VERSION.findall(line) if release(v) != lean_release]
    return hits


def render(pin: dict, findings: list[str], notices: list[str]) -> str:
    out = [f"P1 lean-toolchain:        {pin['toolchain'] or 'MISSING'}"]
    if pin["uses_mathlib"]:
        out += [f"P2 lakefile mathlib rev:  {pin['lakefile_rev'] or 'MISSING'}",
                f"P3 manifest mathlib:      rev {pin['mathlib_rev'] or 'MISSING'}, inputRev {pin['mathlib_input_rev']}",
                f"P4 .lake mathlib built:   {pin['checkout_toolchain'] or 'not built'}"]
    else:
        out.append("Mathlib: not a dependency of this instance")
    out += [f"  - {f}" for f in findings] + [f"  note: {n}" for n in notices]
    out.append("pin: " + ("UNKNOWN or inconsistent: stop and report it" if findings else "known and consistent"))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    lean_dir = instance_root() / "lean"
    pin = read_pin(lean_dir)
    if not pin["toolchain"]:
        print(f"lean_pin: no readable lean/lean-toolchain under {lean_dir.parent}", file=sys.stderr)
        return 2
    findings, notices = pin_findings(pin)
    findings += [f for f in [checkout_finding(pin)] if f]
    print(json.dumps({**pin, "findings": findings, "notices": notices}, indent=2) if args.json
          else render(pin, findings, notices))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
