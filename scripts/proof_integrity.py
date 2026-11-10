#!/usr/bin/env python3
"""G-KERNEL — fail-closed proof-integrity gate for the mathAgents Lean libraries.

Two libraries are gated:
  MathAgents     the proved library. Everything below applies strictly.
  MathAgentsWIP  open work (theorem stubs, partial proofs). `sorry` / `admit` / `stop` are
                 tolerated here as *open markers*; every other check stays fatal. MathAgents must
                 never import MathAgentsWIP, so an open result cannot leak into a proved one.
Each declaration receives its own status — proved | open | failed — so an open stub does not
change the status of proved theorems. A result may be called proved only when its declaration's
status is `proved`.

Checks, in order (every check runs; any finding => FAIL):
  0. toolchain     the Lean that runs in lean/ (`lean --version`) is the release lean-toolchain pins. An elan
                   override (ELAN_TOOLCHAIN, `elan override`) can select another; then nothing is built under
                   it (steps 3-5 are skipped) and the gate FAILs naming both releases
                   (docs/lean-version-governance.md, R5).
  1. config scan   lakefile / lean-toolchain carry no kernel-weakening options, and the pin is consistent:
                   the lakefile's mathlib `rev` equals the manifest's `inputRev` (P2). After a successful
                   build, the Mathlib checkout in .lake was built for the pinned toolchain (P4).
  2. source scan   comment- and string-aware scan of every library module for escape hatches
                   (sorry, admit, stop, native_decide, +native, unsafe, implemented_by, extern)
                   and for metaprogramming commands that can add declarations without a kernel
                   check (run_cmd, #eval, elab, initialize, ...). `axiom` declarations must be
                   approved by fully-qualified name in references/axiom-allowlist.json (G-AX).
  3. lake build    the elaborator + kernel accept every module; `declaration uses 'sorry'`
                   warnings are failures.
  4. replay        `leanchecker` re-checks each library module's declarations in the kernel,
                   so declarations smuggled in by metaprograms are caught.
  5. envelope      every theorem/def (public and private) in a MathAgents module depends only on
                   {propext, Classical.choice, Quot.sound} plus G-AX approvals. sorryAx,
                   Lean.ofReduceBool, Lean.trustCompiler and the auxiliary axioms that
                   native_decide mints (Lean >= 4.3x: `<decl>._native.native_decide.ax_*`)
                   always fail. The audit must cover at
                   least as many theorems as the source declares.

Writes reports/kernel/latest.json with provenance (commit, dirty flag, source hash, the Lean
binary's own version) and a statement fingerprint per declaration, to which G-FID approvals are
keyed: a fidelity sign-off is valid only while the fingerprint is unchanged.

Usage: python3 scripts/proof_integrity.py [--lean-dir DIR] [--report FILE | --no-report]
Exit 0 = PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import axiom_allowlist  # noqa: E402  (DD-38 shared envelope loader)
import lean_pin  # noqa: E402  (P1-P4: the instance's pin)
from instance_root import LEAN_TEMPLATES, harness_sha256, instance_root  # noqa: E402

ROOT = instance_root()
OPEN_MARKERS = ["sorry", "admit", "stop"]
ESCAPE_TOKENS = OPEN_MARKERS + ["native_decide", "unsafe", "implemented_by", "extern"]
META_COMMANDS = ["run_cmd", "run_elab", "run_meta", "#eval", "#exit", "elab", "elab_rules",
                 "macro_rules", "initialize", "builtin_initialize", "declare_syntax_cat",
                 "addDecl", "addDeclWithoutChecking", "modifyEnv", "set_option debug"]
CONFIG_FORBIDDEN = re.compile(r"debug\.|skipKernelTC|-D\s*debug", re.I)
THEOREM_DECL = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:(?:private|protected|noncomputable)\s+)*(?:theorem|lemma)\s", re.M)
AXIOM_DECL = re.compile(r"^\s*(?:(?:private|protected)\s+)*axiom\s+([^\s:({\[]+)", re.M)
NAMESPACE = re.compile(r"^\s*(namespace|end)\s+([^\s]+)?", re.M)


def strip_comments_and_strings(src: str) -> str:
    """Blank out comments (line, nested block, doc) and string literals, keeping line numbers."""
    out, i, n, depth = [], 0, len(src), 0
    while i < n:
        c2 = src[i:i + 2]
        if depth:
            if c2 == "/-":
                depth += 1; out.append("  "); i += 2; continue
            if c2 == "-/":
                depth -= 1; out.append("  "); i += 2; continue
            out.append("\n" if src[i] == "\n" else " "); i += 1; continue
        if c2 == "/-":
            depth = 1; out.append("  "); i += 2; continue
        if c2 == "--":
            while i < n and src[i] != "\n":
                out.append(" "); i += 1
            continue
        if src[i] == '"':
            out.append(" "); i += 1
            while i < n and src[i] != '"':
                if src[i] == "\\":
                    out.append(" "); i += 1
                out.append("\n" if i < n and src[i] == "\n" else " "); i += 1
            out.append(" "); i += 1; continue
        out.append(src[i]); i += 1
    return "".join(out)


def token_pattern(tok: str) -> re.Pattern[str]:
    if tok.startswith("#") or " " in tok:
        return re.compile(re.escape(tok).replace(r"\ ", r"\s+") + r"\b")
    return re.compile(r"(?<![\w.'])" + re.escape(tok) + r"(?![\w'])")


def qualified_axioms(code: str) -> list[tuple[int, str]]:
    """Return (line, fully-qualified name) for axiom declarations, tracking namespaces."""
    ns: list[str] = []
    found = []
    for lineno, line in enumerate(code.splitlines(), 1):
        m = NAMESPACE.match(line)
        if m and m.group(1) == "namespace" and m.group(2):
            ns.extend(m.group(2).split("."))
        elif m and m.group(1) == "end" and m.group(2):
            parts = m.group(2).split(".")
            if ns[-len(parts):] == parts:
                del ns[-len(parts):]
        a = AXIOM_DECL.match(line)
        if a:
            name = a.group(1)
            found.append((lineno, name[len("_root_."):] if name.startswith("_root_.") else ".".join(ns + [name])))
    return found


def libraries(lean_dir: Path) -> tuple[list[str], str]:
    """Library names from lakefile.toml (the single source of truth); the WIP library is the one
    whose name ends in `WIP`. Fails closed unless exactly one proved and one WIP library exist."""
    names = [lib["name"] for lib in tomllib.loads((lean_dir / "lakefile.toml").read_text()).get("lean_lib", [])]
    wip = [n for n in names if n.endswith("WIP")]
    if len(names) != 2 or len(wip) != 1:
        raise RuntimeError(f"expected one proved and one *WIP lean_lib in lakefile.toml, found {names}")
    return names, wip[0]


def library_files(lean_dir: Path, libs: list[str]) -> list[Path]:
    """Every Lean source of the gated libraries, in the canonical order used for hashing."""
    files: list[Path] = []
    for lib in libs:
        files += sorted((lean_dir / lib).rglob("*.lean")) + [lean_dir / f"{lib}.lean"]
    return [f for f in files if f.exists()]


def source_digest(lean_dir: Path, libs: list[str]) -> str:
    """SHA-256 over (relative path, content) of every library source. Shared with
    scripts/validate_dossier.py, which recomputes it to reject stale or foreign kernel reports."""
    digest = hashlib.sha256()
    # Build inputs too: a toolchain or dependency bump must invalidate old reports and approvals.
    build_inputs = [lean_dir / n for n in ("lean-toolchain", "lakefile.toml", "lakefile.lean", "lake-manifest.json")]
    for f in [p for p in build_inputs if p.exists()] + library_files(lean_dir, libs):
        digest.update(f.relative_to(lean_dir).as_posix().encode() + b"\0" + f.read_text().encode())
    return digest.hexdigest()


def lineno(code: str, pos: int) -> int:
    return code.count("\n", 0, pos) + 1


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PATH=f"{Path.home() / '.elan' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lean-dir", type=Path, default=ROOT / "lean")
    ap.add_argument("--report", type=Path, default=ROOT / "reports" / "kernel" / "latest.json")
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--allowlist", type=Path, default=ROOT / "references" / "axiom-allowlist.json",
                    help="G-AX axiom allowlist (tests pass a fixture)")
    args = ap.parse_args()
    lean_dir = args.lean_dir.resolve()
    default_allowlist = (ROOT / "references" / "axiom-allowlist.json").resolve()
    if args.allowlist.resolve() != default_allowlist and not args.no_report \
            and args.report.resolve() == (ROOT / "reports" / "kernel" / "latest.json").resolve():
        print("[G-KERNEL] FAIL: a non-default --allowlist may not write the authoritative report; "
              "pass --no-report or another --report")
        return 2
    findings: list[str] = []
    # A stale report must never outlive a failed or crashed run.
    if not args.no_report:
        args.report.unlink(missing_ok=True)
    libs, wip_lib = libraries(lean_dir)
    is_wip = lambda mod: mod.split(".")[0] == wip_lib  # noqa: E731

    base_axioms, approved, problems = axiom_allowlist.load(args.allowlist)  # DD-38: one home, one loader
    findings += [f"allowlist: {msg}" for msg in problems]

    # 0. toolchain: never build under a Lean other than the pinned one (an elan override would make the run
    # record one pin and check with another; building would also rebuild .lake for the wrong toolchain)
    pin = lean_pin.read_pin(lean_dir)
    toolchain_pin = pin["toolchain"]
    lean_version = run(["lean", "--version"], lean_dir).stdout.strip()
    wrong_toolchain = lean_pin.toolchain_mismatch(lean_version, toolchain_pin)
    if wrong_toolchain:
        findings.append(wrong_toolchain + "; build, replay and envelope were not run")

    # 1. config scan (P1-P3; P4 waits for the build, which checks out the manifest's Mathlib)
    findings += [f"config: {f}" for f in lean_pin.pin_findings(pin)[0]]
    for cfg in ("lakefile.toml", "lakefile.lean", "lean-toolchain"):
        p = lean_dir / cfg
        if p.exists() and CONFIG_FORBIDDEN.search(p.read_text()):
            findings.append(f"config: kernel-weakening option in {cfg}")
    # a local path dependency is neither gated nor hashed (only lake-manifest.json is), so editing it
    # could change what an approved statement means without lapsing anything: forbid it
    toml_cfg = lean_dir / "lakefile.toml"
    if toml_cfg.exists():
        for req in tomllib.loads(toml_cfg.read_text()).get("require", []):
            if "path" in req:
                findings.append(f"config: local path dependency `{req.get('name', '?')}` in lakefile.toml (use a pinned git dependency)")
    lean_cfg = lean_dir / "lakefile.lean"
    # any `require … from <non-git source>`, across lines; comments ignored (strings blanked, keywords kept)
    if lean_cfg.exists() and re.search(r"\brequire\b[\s\S]*?\bfrom\b(?!\s+git\b)",
                                       strip_comments_and_strings(lean_cfg.read_text())):
        findings.append("config: local path dependency in lakefile.lean (use a pinned git dependency)")

    # 2. source scan
    files = library_files(lean_dir, libs)
    modules = [".".join(f.relative_to(lean_dir).with_suffix("").parts) for f in files]
    bad_modules: set[str] = set()
    open_markers: list[str] = []
    src_theorems = 0
    for f, mod in zip(files, modules):
        raw = f.read_text()
        code = strip_comments_and_strings(raw)
        rel = f.relative_to(ROOT) if f.is_relative_to(ROOT) else f
        wip = is_wip(mod)
        src_theorems += len(THEOREM_DECL.findall(code))
        for tok in ESCAPE_TOKENS + META_COMMANDS:
            for m in token_pattern(tok).finditer(code):
                if wip and tok in OPEN_MARKERS:
                    open_markers.append(f"{rel}:{lineno(code, m.start())}: `{tok}`")
                    continue
                findings.append(f"source: {rel}:{lineno(code, m.start())}: forbidden `{tok}`"); bad_modules.add(mod)
        for m in re.finditer(r"\+native\b", code):
            findings.append(f"source: {rel}:{lineno(code, m.start())}: forbidden `+native`"); bad_modules.add(mod)
        for ax_line, name in qualified_axioms(code):
            if name not in approved:
                findings.append(f"source: {rel}:{ax_line}: unapproved axiom `{name}` (G-AX)"); bad_modules.add(mod)
        if not wip:
            for m in re.finditer(r"^\s*(?:\w+\s+)*import\b[^\n]*(?<![\w.])" + wip_lib + r"\b", code, re.M):
                findings.append(f"source: {rel}:{lineno(code, m.start())}: proved library imports {wip_lib}"); bad_modules.add(mod)

    # 3. build
    if wrong_toolchain:
        build = subprocess.CompletedProcess(["lake", "build"], 1, "", "not run: wrong toolchain")
    else:
        build = run(["lake", "build"], lean_dir)
        if build.returncode != 0:
            findings.append("build: lake build failed: " + (build.stdout + build.stderr).strip()[-600:])
        elif p4 := lean_pin.checkout_finding(lean_pin.read_pin(lean_dir)):  # now that lake has checked it out
            findings.append(f"config: {p4}")
    # Wording differs across Lean versions: 'sorry' (older) vs `sorry` (4.34). Open markers in
    # MathAgentsWIP are expected; anywhere else they are findings.
    for m in re.finditer(r"^warning: (\S+?):\d+:\d+: declaration uses ['`]sorry['`]", build.stdout + build.stderr, re.M):
        if not m.group(1).startswith(wip_lib + "/"):
            findings.append(f"build: a declaration uses sorry ({m.group(1)})")

    # 4. kernel replay of each library module
    if build.returncode == 0:
        for mod in modules:
            r = run(["lake", "env", "leanchecker", mod], lean_dir)
            if r.returncode != 0:
                findings.append(f"replay: leanchecker rejected {mod}: {(r.stdout + r.stderr).strip()[-300:]}")
                bad_modules.add(mod)

    # 5. axiom envelope
    rows: list[dict] = []
    if build.returncode == 0:
        # the audit file lives in the gitignored lean/.lake/tmp, the only lean/ path a confined run may write
        tmp_dir = lean_dir / ".lake" / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=tmp_dir, delete=False) as tf:
            tf.write("".join(f"import {m}\n" for m in modules))
            roots = ", ".join(f"`{n}" for n in libs)
            tf.write((LEAN_TEMPLATES / "AxiomAudit.lean").read_text().replace("GKERNEL_ROOTS", roots))
            audit_path = Path(tf.name)
        try:
            r = run(["lake", "env", "lean", str(audit_path)], lean_dir)
        finally:
            audit_path.unlink(missing_ok=True)
        payload = [ln for ln in r.stdout.splitlines() if ln.startswith("GKERNEL-JSON ")]
        if r.returncode != 0 or len(payload) != 1:
            findings.append(f"envelope: audit did not run cleanly (exit {r.returncode}): {(r.stdout + r.stderr).strip()[-400:]}")
        else:
            try:
                rows = json.loads(payload[0][len("GKERNEL-JSON "):])
            except ValueError as exc:
                findings.append(f"envelope: unparseable audit output: {exc}")
        allowed = base_axioms | approved
        for d in rows:
            extra = set(d["axioms"]) - allowed
            wip = is_wip(d["module"])
            if wip and extra == {"sorryAx"}:
                d["status"] = "open"
            elif extra:
                findings.append(f"envelope: {d['decl']} depends on {', '.join(sorted(extra))}")
                d["status"] = "failed"
            else:
                d["status"] = "failed" if d["module"] in bad_modules else "proved"
        audited_theorems = sum(1 for d in rows if d["kind"] == "theorem")
        if audited_theorems < src_theorems:
            findings.append(f"envelope: audited {audited_theorems} theorems but source declares {src_theorems}")

    verdict = "FAIL" if findings else "PASS"
    if not args.no_report:
        git = lambda *a: run(["git", *a], ROOT).stdout.strip()  # noqa: E731
        report = {
            "gate": "G-KERNEL", "verdict": verdict,
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "lean_version": lean_version,
            "toolchain_pin": toolchain_pin,
            "commit": git("rev-parse", "HEAD") or None,
            "dirty": bool(git("status", "--porcelain", "--", str(lean_dir))),
            "source_sha256": source_digest(lean_dir, libs),
            "harness_sha256": harness_sha256(),
            "allowlist": {"path": str(args.allowlist.resolve().relative_to(ROOT)) if args.allowlist.resolve().is_relative_to(ROOT)
                          else str(args.allowlist), "sha256": hashlib.sha256(args.allowlist.read_bytes()).hexdigest()},
            "findings": findings, "open_markers": open_markers, "declarations": rows,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(f"[G-KERNEL] report: {args.report}")
    for f in findings:
        print(f"  - {f}")
    counts = {k: sum(1 for d in rows if d.get("status") == k) for k in ("proved", "open", "failed")}
    print(f"[G-KERNEL] {verdict} ({len(rows)} declarations audited, {src_theorems} theorems in source; "
          f"proved={counts['proved']} open={counts['open']} failed={counts['failed']})")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed on any tool error; main() already removed old reports
        print(f"[G-KERNEL] FAIL: gate error: {exc!r}")
        sys.exit(2)
