#!/usr/bin/env python3
"""Dossier validator — structure, G-FID, G-AX and G-CX modules (spec DD-33..DD-39, DD-43, DD-59;
charter D5, D26). Fail-closed.

Hosts the per-dossier record checks of the harness specification:
  structure  stage artifacts present and consistent (scripts/dossier_structure.py; DD-1, DD-19, DD-43);
  G-FID      fidelity records `reports/dossiers/<slug>/fidelity.json`
             (schema: references/schemas/fidelity-record.schema.json);
  G-AX       statement-change records `reports/dossiers/<slug>/gax.json` (schema:
             references/schemas/gax-record.schema.json): an approved declaration whose fingerprint
             changed since the base or HEAD needs a record naming the old and new fingerprints (DD-37);
  G-CX       counterexample logs `reports/dossiers/<slug>/counterexamples.json`
             (schema: references/schemas/counterexample-log.schema.json).
All are keyed to each declaration's `statement_fingerprint` in the current G-KERNEL report, which
under DD-34 also covers the project definitions a statement reaches.

Kernel report freshness: the report must have verdict PASS and a `source_sha256` equal to the hash
recomputed now from the Lean sources (shared helper in scripts/proof_integrity.py). A report from
another branch, an edited tree, or a failed run is rejected as stale.

Coverage: each record names its `lean_namespace`; every kernel-report declaration under that
namespace must have an entry, so approving one theorem cannot cover another. Helper lemmas
(`<ns>.Aux.`) and counterexample witnesses (`<ns>.CX.`) are exempt, and in exchange an approved
statement may not reach them: its `statement_uses` (from the kernel report) must name none.

Result labels: any line in any text file under the dossier that gives a status/result key the value
"proved..." (headings, bullets, tables, bold or italic markup, `Result:`, `Status:`, `Label:`) is a
result label. Its value must be exactly `proved` or `proved, fidelity-waived`, backed by the record
and the kernel report. Prose that merely mentions "proved" is not a label.

Waivers (D5, D26): a waived entry satisfies --require-fid only in the conversation that waived it
(`--conversation <id>` must equal `waiver.conversation`). Its label persists as "proved,
fidelity-waived" (DD-35).

G-CX (DD-39): every verdict must carry the target statement's CURRENT fingerprint. A target whose
fingerprint has changed since its counterexample was logged was revised after it, and needs a
`revise` verdict on the new fingerprint. A target missing from the kernel report fails. A refuted
label names its target -- "refuted (<decl>)" or "refuted, verdict-waived (<decl>)"; "disproved",
"refuted by ..." and an unbound "refuted" are non-canonical -- and needs a current `refutes` verdict
on that target, which the kernel must not report proved. A decide/SMT/ATP refutation counts only
once a kernel-proved `lean_witness` re-establishes it (DD-16). A kernel-as-judge waiver of a
`refutes` or `revise` verdict needs a kernel-proved witness, and of a `spurious` verdict the target
proved in the kernel; a waived refutation is labelled "refuted, verdict-waived (<decl>)", never
plain "refuted" (DD-59). The log is append-only against --base (default: the merge base with
origin/HEAD). A dossier may not carry both proved and refuted labels.

Modes:
  validate_dossier.py                      check every dossier (consistency of what exists)
  validate_dossier.py <slug> [...]         check the named dossiers
  validate_dossier.py --require-fid <slug> PRECONDITION for dispatching Stage 2 (@proof-strategist)
  validate_dossier.py --require-stage <slug> N
                                           PRECONDITION for dispatching stage N: the artifacts of
                                           stages < N exist (N >= 2 implies --require-fid)
Options: --root DIR (default: MATHAGENTS_ROOT, set by `mathagents run`, else this checkout), --kernel-report FILE,
         --conversation ID, --base REF (G-AX and G-CX comparison; default the merge base with origin/HEAD
         when --root is in a git work tree, failing closed when there is none), --no-history (skip the
         per-commit walk below)

History (IA-01): besides comparing the base and HEAD with the working tree, every commit in
base..HEAD that touches a dossier record is compared with its first parent under the same rules, so a
change made in one commit and undone in a later one is caught. CI passes as --base the last commit
with a successful Gates run, which makes a cancelled, failed or skipped run harmless.
Pin stamps (docs/lean-version-governance.md R6): a fidelity entry or G-AX record whose optional `toolchain_pin`
or `mathlib_rev` differs from the instance's current pin is reported as a WARN line (it predates a bump and needs
re-approval); a warning never changes the exit code.
Exit 0 = pass; 1 = findings; 2 = usage/tool error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proof_integrity  # noqa: E402  (shared library list + source digest)
import dossier_structure  # noqa: E402  (DD-43 structure module)
import lean_pin  # noqa: E402  (the toolchain check, docs/lean-version-governance.md R5)
from instance_root import instance_root  # noqa: E402

# A result label: a key (optionally quoted, as in JSON/YAML; `result_status` too), a separator, then a
# value read to the end of its clause (a sentence-ending period, `|`, `"` or newline; dots inside
# names such as `Pilot.conj` do not end it) that uses a proof or refutation word.
# Status keys take the broad vocabulary (false, not a theorem, counterexample found); the looser keys
# label/outcome/conclusion take only proof/refutation words, so mathematical prose ("Conclusion: the
# converse is false without positivity") is not a label. Values are capped (no quadratic backtracking).
_STRONG_KEY = r"(?:result(?:[\s_]+status)?|status|verdict)"
_WEAK_KEY = r"(?:label|outcome|conclusion)"
_NARROW = r"(?:prove[dn]|disprove[dn]|disproof|refut\w*)"
_BROAD = r"(?:prove[dn]|disprove[dn]|disproof|refut\w*|false|not\s+a\s+theorem|counterexample\s+(?:found|exists|established))"
_VCHAR = r"(?:[^|\n.\"]|\.(?=[^\s\"]))"
_SEP = r"[\"']?[\s*_`]*[:|=—–]"


def _label_re(key: str, words: str) -> re.Pattern:
    return re.compile(rf"(?i)(?<![A-Za-z])[\"']?{key}(?![A-Za-z]){_SEP}(?P<pre>[\s*_`|\"']*)"
                      rf"(?P<value>{_VCHAR}{{0,200}}?\b{words}\b{_VCHAR}{{0,200}})")


# loose keys also take a broad word when the value OPENS with it ("Outcome: false", "Conclusion: not a theorem")
LABELS = ((_label_re(_STRONG_KEY, _BROAD), re.compile(rf"(?i)\b{_BROAD}\b")),
          (re.compile(rf"(?i)(?<![A-Za-z])[\"']?{_WEAK_KEY}(?![A-Za-z]){_SEP}(?P<pre>[\s*_`|\"']*)"
                      rf"(?P<value>(?:{_BROAD}|{_VCHAR}{{0,200}}?\b{_NARROW})\b{_VCHAR}{{0,200}})"),
           re.compile(rf"(?i)^\W*{_BROAD}\b|\b{_NARROW}\b")))
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
HEADING = re.compile(r"^\s*#{1,6}\s+(.*?)\s*#*\s*$")
CANONICAL = {"proved", "proved, fidelity-waived"}
# refutation labels name their target: "refuted (Pilot.conj)" / "refuted, verdict-waived (Pilot.conj)"
CX_CANONICAL = re.compile(r"(?i:refuted)(?P<waived>(?i:, verdict-waived))? \((?P<decl>[^\s()]+)\)")
CX_WORD = re.compile(r"(?i)\b(?:disprove[dn]|disproof|refut\w*|false|not\s+a\s+theorem|counterexample)")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".tex"}
# records, not prose: never scanned for labels (a kernel snapshot's per-declaration "status" is the
# kernel's, checked against the fidelity record by the structure module, not a result claim)
RECORD_FILES = {"fidelity.json", "counterexamples.json", "gax.json", "kernel-snapshot.json"}
IMMUTABLE_CX = ("decl", "statement_fingerprint", "method")  # append-only log (fixed at logging time)
EXEMPT_SUBNAMESPACES = ("Aux.", "CX.")  # G-FID coverage: helper lemmas and counterexample witnesses
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")


def load_kernel(root: Path, path: Path) -> tuple[dict[str, dict] | None, str | None]:
    """Return (declarations by name, problem) — problem is set when the report is unusable."""
    if not path.exists():
        return None, "no kernel report; run scripts/check_proof_integrity.sh first"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("verdict") != "PASS":
        return None, f"kernel report verdict is {data.get('verdict')!r}, not PASS"
    if not data.get("lean_version") or not data.get("toolchain_pin"):
        return None, "kernel report lacks lean_version or toolchain_pin, so the Lean that ran is unknown; re-run G-KERNEL"
    if wrong := lean_pin.toolchain_mismatch(data["lean_version"], data["toolchain_pin"]):
        return None, f"kernel report was produced under another Lean than its pin ({wrong}); re-run G-KERNEL"
    lean_dir = root / "lean"
    try:
        libs, _ = proof_integrity.libraries(lean_dir)
        current = proof_integrity.source_digest(lean_dir, libs)
    except Exception as exc:  # noqa: BLE001 — any failure to recompute is a stale report
        return None, f"cannot recompute Lean source hash ({exc!r})"
    if data.get("source_sha256") != current:
        return None, "stale kernel report: its source_sha256 does not match the current Lean sources; re-run G-KERNEL"
    allow = root / "references" / "axiom-allowlist.json"
    want = hashlib.sha256(allow.read_bytes()).hexdigest() if allow.exists() else None
    used = data.get("allowlist") or {}
    if used.get("sha256") != want or used.get("path") != "references/axiom-allowlist.json":
        return None, ("kernel report was not produced with the committed references/axiom-allowlist.json "
                      "(allowlist path or hash missing or different); re-run G-KERNEL")
    names = [d["decl"] for d in data.get("declarations", [])]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:  # e.g. a private and a public declaration with the same user name in different modules
        return None, f"kernel report lists declaration name(s) more than once: {', '.join(dup)}"
    return {d["decl"]: d for d in data.get("declarations", [])}, None


def _clean(value: str) -> str:
    return re.sub(r"[*`|\"]", "", value).strip().strip("_").strip().rstrip(".").strip()


def _key_kind(text: str) -> int | None:
    """0 = status key, 1 = loose key, None = not a key (a header cell or heading text)."""
    t = _clean(text).rstrip(":").strip()
    for kind, key in ((0, _STRONG_KEY), (1, _WEAK_KEY)):
        # "Status", "Kernel status", "Status of Pilot.conj", "Verdict on CX-1"
        if re.fullmatch(rf"(?i)(?:.*\s)?{key}(?:\s+(?:of|on|for)\b.*)?", t):
            return kind
    return None


def text_labels(text: str, structured: bool) -> list[str]:
    """Label values in one file: `key: value` forms, Markdown table columns headed by a key, and a
    heading that is a key followed by its first paragraph line."""
    found = []
    for rx, _ in LABELS:
        for m in rx.finditer(text):
            value = _clean(m["value"])
            if rx is LABELS[1][0] and structured and value.lower().rstrip(",}] ") in ("false", "true") \
                    and not re.search("[\"']", m["pre"]):
                continue  # an unquoted boolean under a loose key; under a status key it stays a label
            found.append(value)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if i + 1 < len(lines) and "|" in line and TABLE_RULE.match(lines[i + 1]):
            header = CELL_SPLIT.split(line.strip().strip("|"))
            cols = {j: k for j, c in enumerate(header) if (k := _key_kind(c)) is not None}
            for row in lines[i + 2:]:
                if "|" not in row:
                    break
                cells = CELL_SPLIT.split(row.strip().strip("|"))
                for j, k in cols.items():
                    if j < len(cells) and LABELS[k][1].search(cells[j]):
                        found.append(_clean(cells[j]))
        h = HEADING.match(line)
        if h and (k := _key_kind(h.group(1))) is not None:
            nxt = next((x for x in lines[i + 1:] if x.strip()), "")
            if not HEADING.match(nxt):
                value = re.split(r"\.(?=\s|$)", nxt.strip(), maxsplit=1)[0][:400]
                if LABELS[k][1].search(value):
                    found.append(_clean(value))
    return found


def result_labels(dossier: Path) -> list[tuple[str, str]]:
    """(file, value) per label; value keeps its case (refutation labels carry a declaration name)."""
    found = []
    for f in sorted(dossier.rglob("*")):
        if f.parent == dossier and f.name in RECORD_FILES:
            continue
        if f.is_file() and f.suffix.lower() in TEXT_SUFFIXES:
            text = f.read_text(encoding="utf-8", errors="replace")
            for value in text_labels(text, f.suffix.lower() in (".json", ".yaml", ".yml")):
                found.append((str(f.relative_to(dossier)), value))
    return found


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    # LC_ALL=C: resolve_base matches git's English "not a git repository" message
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          env={**os.environ, "LC_ALL": "C"})


def resolve_base(root: Path, base: str | None) -> tuple[str | None, str | None]:
    """The commit the append-only counterexample logs are compared with: (ref, problem).
    Default: the merge base of HEAD with origin/HEAD (the default branch), so edits committed or pushed on
    a feature branch are still compared with the default branch; no origin/HEAD fails closed. An instance
    in a subdirectory of a work tree (docs/module.md) is compared like a work-tree root; the git paths
    below are relative to `root`. Outside any git work tree with no explicit --base there is nothing to
    compare: (None, None)."""
    top = _git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 and "not a git repository" not in top.stderr:
        # git itself failed (it could not run, or broke): that is not "no work tree", so the append-only
        # checks must not be skipped (M6-F4: a sandboxed git exiting 71 made every check pass silently)
        raise RuntimeError(f"git rev-parse failed (exit {top.returncode}): {top.stderr.strip()}")  # fail closed (exit 2)
    if top.returncode != 0 or not root.resolve().is_relative_to(Path(top.stdout.strip()).resolve()):
        return None, (f"--base {base} given but {root} is not in a git work tree" if base else None)
    if base:
        if base.startswith("-") or _git(root, "rev-parse", "--verify", "--quiet", "--end-of-options",
                                         f"{base}^{{commit}}").returncode != 0:
            return None, f"--base {base}: not a commit"
        return base, None
    # the default branch, not the current branch's own upstream: a pushed feature branch would
    # otherwise already contain a laundered edit
    mb = _git(root, "merge-base", "HEAD", "origin/HEAD")
    if mb.returncode != 0:
        return None, ("no origin/HEAD (default branch) to compare the append-only counterexample logs with; "
                      "run `git remote set-head origin --auto` or pass --base REF")
    return mb.stdout.strip(), None


def base_record_slugs(root: Path, ref: str) -> list[str]:
    """Slugs that had any gate record (fidelity, G-AX, G-CX) at `ref`: each must still exist, or be
    retired by a human tombstone, so deleting or renaming a dossier cannot launder its history."""
    out = _git(root, "ls-tree", "-r", "--name-only", ref, "--", "reports/dossiers")
    if out.returncode != 0:
        raise RuntimeError(f"git ls-tree {ref} failed: {out.stderr.strip()}")  # fail closed (exit 2)
    return sorted({Path(n).parent.name for n in out.stdout.splitlines()
                   if re.fullmatch(r"reports/dossiers/[^/]+/(counterexamples|fidelity|gax)\.json", n)})


def retired(root: Path, slug: str, refs: list[str]) -> bool:
    """A dossier is retired only by a human tombstone reports/dossiers/<slug>.retired.json naming an
    approver, a date, a reason, and every declaration the dossier's fidelity record approved at any of
    `refs` (removing a dossier drops approved claims: a G-AX-level human decision, DD-37)."""
    t = root / "reports" / "dossiers" / f"{slug}.retired.json"
    try:
        d = json.loads(t.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    fids = []
    for ref in refs:
        old, problem = git_base_log(root, slug, ref, "fidelity.json")
        if problem:
            return False
        fids.append(old)
    return tombstone_covers(d, slug, fids)


def git_base_log(root: Path, slug: str, ref: str | None, name: str = "counterexamples.json") -> tuple[dict | None, str | None]:
    """A dossier record file as committed at `ref`: (data or None, problem)."""
    if ref is None:
        return None, None
    rel = f"reports/dossiers/{slug}/{name}"
    listed = _git(root, "ls-tree", "--name-only", ref, "--", rel)
    if listed.returncode != 0:
        return None, f"cannot list {rel} at {ref}: {listed.stderr.strip()}"
    if not listed.stdout.strip():
        return None, None  # the log did not exist at the base
    shown = _git(root, "show", f"{ref}:./{rel}")  # ./ : relative to `root`, which may be a subdirectory
    if shown.returncode != 0:
        return None, f"cannot read {rel} at {ref}: {shown.stderr.strip()}"
    try:
        return json.loads(shown.stdout), None
    except ValueError:
        return None, f"{rel} at {ref} is not valid JSON; cannot compare it with the working tree"


def cx_log_changes(old: dict | None, new: dict | None, new_exists: bool, ref: str) -> list[str]:
    """Append-only rules for counterexamples.json between an older version (at `ref`) and a newer one:
    the log is never deleted, no entry is removed, and logged fields never change."""
    if not old:
        return []
    if not new_exists:
        return [f"counterexamples.json was deleted (present at {ref}); the log is append-only"]
    if new is None:
        return []  # an unreadable newer version is reported by its own load
    now = {e.get("id"): e for e in new.get("counterexamples", [])}
    out = []
    for o in old.get("counterexamples", []):
        cur = now.get(o.get("id"))
        if cur is None:
            out.append(f"{o.get('id')} was removed from the log; the log is append-only")
            continue
        bad = [f for f in IMMUTABLE_CX if cur.get(f) != o.get(f)]
        if bad:
            out.append(f"{cur.get('id')}: {bad[0]} changed from {o.get(bad[0])!r} to {cur.get(bad[0])!r}; "
                       "logged fields are immutable (append a new entry instead)")
    return out


def gax_log_changes(old: dict | None, new_records: list[dict], ref: str) -> list[str]:
    """gax.json is append-only: every record present at `ref` survives unedited."""
    now = {r.get("id"): r for r in new_records}
    out = []
    for o in (old or {}).get("records", []):
        cur = now.get(o.get("id"))
        if cur is None or any(cur.get(f) != o.get(f) for f in ("decl", "old_fingerprint", "new_fingerprint", "change")):
            out.append(f"{o.get('id')} was removed or edited (present at {ref}); gax.json is append-only")
    return out


def approved_changes(old_fid: dict | None, current: dict[str, str], transitions: set, ref: str) -> list[str]:
    """DD-37: a declaration approved at `ref` whose fingerprint is now different (or which is gone)
    needs an approved or waived G-AX record naming that exact transition."""
    out = []
    for e in (old_fid or {}).get("declarations", []):
        d, fp = e.get("decl"), str(e.get("statement_fingerprint"))
        new = current.get(d, "removed")
        if new != fp and (d, fp, new) not in transitions:
            out.append(f"{d} was approved with fingerprint {fp} (at {ref}) and is now "
                       + ("absent from the fidelity record" if new == "removed" else f"{new}")
                       + f"; a changed approved statement needs a G-AX record in gax.json naming "
                       f"old_fingerprint {fp} and new_fingerprint {new} (DD-37)")
    return out


def gax_transitions(records: list[dict]) -> set:
    return {(r.get("decl"), r.get("old_fingerprint"), r.get("new_fingerprint")) for r in records
            if (r.get("approver") and r.get("date")) or r.get("waiver")}


RECORD = re.compile(r"reports/dossiers/([^/]+)/(counterexamples|fidelity|gax)\.json")


def _json_at(root: Path, commit: str | None, rel: str) -> tuple[bool, dict | None, str | None]:
    """(exists, data, problem) for a file as committed at `commit` (None: before the first commit)."""
    if commit is None:
        return False, None, None
    listed = _git(root, "ls-tree", "--name-only", commit, "--", rel)
    if listed.returncode != 0:
        return False, None, f"cannot list {rel} at {commit[:9]}: {listed.stderr.strip()}"
    if not listed.stdout.strip():
        return False, None, None
    shown = _git(root, "show", f"{commit}:./{rel}")  # ./ : relative to `root`
    if shown.returncode != 0:
        return True, None, f"cannot read {rel} at {commit[:9]}: {shown.stderr.strip()}"
    try:
        data = json.loads(shown.stdout)
    except ValueError:
        return True, None, f"{rel} at {commit[:9]} is not valid JSON; its history cannot be checked"
    if not isinstance(data, dict):
        return True, None, f"{rel} at {commit[:9]} is not a JSON object; its history cannot be checked"
    return True, data, None


def check_history(root: Path, base: str) -> list[str]:
    """IA-01: compare every commit in base..HEAD that touches a dossier record with its first parent,
    under the same append-only, immutability, G-AX and deletion rules as the snapshot check. A change
    made in one commit and undone in a later one (which the base and the tip alone cannot show) is
    caught, so a commit whose own CI run was cancelled, failed or skipped is still checked."""
    revs = _git(root, "rev-list", "--reverse", f"{base}..HEAD")
    if revs.returncode != 0:
        return [f"history: git rev-list {base}..HEAD failed: {revs.stderr.strip()}"]
    errs: list[str] = []
    for c in revs.stdout.split():
        par = _git(root, "rev-list", "--parents", "-n", "1", c)
        if par.returncode != 0:
            errs.append(f"history {c[:9]}: cannot read its parents: {par.stderr.strip()}")
            continue
        # every parent: a merge resolution may not drop what either side had (IA-01)
        for parent in par.stdout.split()[1:] or [None]:
            if parent:
                listing = _git(root, "diff", "--no-renames", "--relative", "--name-only", parent, c, "--",
                               "reports/dossiers")  # --relative: an instance may be a subdirectory (D35)
            else:
                listing = _git(root, "ls-tree", "-r", "--name-only", c, "--", "reports/dossiers")
            if listing.returncode != 0:
                errs.append(f"history {c[:9]}: cannot list its changes: {listing.stderr.strip()}")
                continue
            for slug in sorted({m.group(1) for n in listing.stdout.split() if (m := RECORD.fullmatch(n))}):
                errs += [f"history {c[:9]}: {slug}: {msg}" for msg in history_step(root, slug, parent, c)]
    return list(dict.fromkeys(errs))


def history_step(root: Path, slug: str, parent: str | None, commit: str) -> list[str]:
    old, new, problems = {}, {}, []
    for name in ("counterexamples", "fidelity", "gax"):
        rel = f"reports/dossiers/{slug}/{name}.json"
        for side, ref in ((old, parent), (new, commit)):
            exists, data, problem = _json_at(root, ref, rel)
            side[name] = (exists, data)
            if problem:
                problems.append(problem)
    if problems:
        return problems  # fail closed: an unreadable version cannot be compared
    ref = parent[:9] if parent else "the first commit"
    if any(e for e, _ in old.values()) and not any(e for e, _ in new.values()):
        if not retired_at(root, slug, commit, old["fidelity"][1]):
            return [f"gate records deleted (present at {ref}) without a retirement tombstone "
                    f"reports/dossiers/{slug}.retired.json; dossier history is append-only"]
        return []
    out = [f"G-CX: {m}" for m in cx_log_changes(old["counterexamples"][1], new["counterexamples"][1],
                                                 new["counterexamples"][0], ref)]
    new_recs = (new["gax"][1] or {}).get("records", [])
    out += [f"G-AX: {m}" for m in gax_log_changes(old["gax"][1], new_recs, ref)]
    current = {e.get("decl"): str(e.get("statement_fingerprint")) for e in (new["fidelity"][1] or {}).get("declarations", [])}
    out += [f"G-AX: {m}" for m in approved_changes(old["fidelity"][1], current, gax_transitions(new_recs), ref)]
    return out


def retired_at(root: Path, slug: str, commit: str, old_fid: dict | None) -> bool:
    """retired() as of `commit`: a human tombstone that lists every declaration approved before."""
    exists, d, problem = _json_at(root, commit, f"reports/dossiers/{slug}.retired.json")
    return exists and not problem and tombstone_covers(d, slug, [old_fid])


def tombstone_covers(d, slug: str, fids: list) -> bool:
    """A tombstone names the slug, an approver, a date and a reason, and lists every declaration
    that any of `fids` (fidelity records) approved."""
    if not isinstance(d, dict) or d.get("slug") != slug:
        return False
    if not all(isinstance(d.get(k), str) and d[k].strip() for k in ("approver", "date", "reason")):
        return False
    listed = set(d.get("declarations") or [])
    return all({e.get("decl") for e in (f or {}).get("declarations", [])} <= listed for f in fids)


def load_record(path: Path, schema: dict, slug: str, errs: list[str]) -> dict | None:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.validate(record, schema)
    except (ValueError, jsonschema.ValidationError) as exc:
        errs.append(f"{slug}: {path.name} invalid: {getattr(exc, 'message', exc)}")
        return None
    if record["slug"] != slug:
        errs.append(f"{slug}: {path.name} slug {record['slug']!r} does not match directory")
    return record


def check_cx(root, slug, dossier, kernel, kernel_problem, schema, cx_labels, has_proved_label,
             fid_namespace, base) -> list[str]:
    """G-CX (DD-15, DD-16, DD-39, DD-59)."""
    errs: list[str] = []
    path = dossier / "counterexamples.json"
    log = load_record(path, schema, slug, errs) if path.exists() else None
    entries = log["counterexamples"] if log else []

    # append-only: a logged counterexample is never removed and its target never re-pointed, so a
    # revision cannot be laundered by editing the log (compared with the resolved base)
    # Compared with the base AND with HEAD, so entries committed locally but not yet on the default
    # branch cannot be removed or rewritten either.
    refs = [base] + (["HEAD"] if base is not None and base != "HEAD" else [])
    seen: set[str] = set()
    for ref in refs:
        base_log, base_problem = git_base_log(root, slug, ref)
        if base_problem:
            errs.append(f"{slug}: G-CX: {base_problem}")
        if not base_log or (path.exists() and log is None):
            continue
        for m in cx_log_changes(base_log, log, path.exists(), ref):
            msg = f"{slug}: G-CX: {m}"
            if msg not in seen:
                seen.add(msg)
                errs.append(msg)
        if not path.exists():
            break
    if log is not None and fid_namespace is not None and \
            log["lean_namespace"].rstrip(".") != fid_namespace.rstrip("."):
        errs.append(f"{slug}: G-CX: lean_namespace {log['lean_namespace']!r} differs from the fidelity record's "
                    f"{fid_namespace!r}; a dossier has one namespace")
    if (log is not None or cx_labels) and kernel is None:
        errs.append(f"{slug}: G-CX: {kernel_problem}")
    ids = [e["id"] for e in entries]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errs.append(f"{slug}: G-CX: duplicate counterexample id {dup}")
    ns = log["lean_namespace"].rstrip(".") + "." if log else ""
    if log is not None and kernel is not None and ns[:-1] in kernel:
        errs.append(f"{slug}: G-CX: lean_namespace {ns[:-1]!r} is itself a declaration; name the enclosing namespace")

    valid_refutes: dict[str, set[str]] = {"human": set(), "waived": set()}  # target decls
    for e in entries:
        cid, d, v = e["id"], e["decl"], e.get("verdict")
        for name in [d] + ([e["lean_witness"]] if e.get("lean_witness") else []):
            if not name.startswith(ns):
                errs.append(f"{slug}: G-CX: {cid}: {name} is outside lean_namespace {ns[:-1]!r}")
        kind = None
        if v is not None:
            human = bool(v.get("approver") and v.get("date"))
            if human and v.get("waiver"):
                errs.append(f"{slug}: G-CX: {cid}: verdict carries both an approval and a waiver")
            elif human:
                kind = "human"
            elif v.get("waiver"):
                kind = "waived"
            else:
                errs.append(f"{slug}: G-CX: {cid}: verdict lacks approver and date, and records no waiving conversation")
        if kernel is None:
            continue
        k = kernel.get(d)
        if k is None:
            errs.append(f"{slug}: G-CX: {cid}: target {d} is absent from the kernel report "
                        "(renamed or removed after a logged counterexample needs a revise verdict on the new declaration)")
            continue
        current = str(k.get("statement_fingerprint"))
        revised = current != e["statement_fingerprint"]
        if v is None:
            if revised:
                errs.append(f"{slug}: G-CX: {cid}: {d} was revised after this counterexample was logged "
                            f"(fingerprint {e['statement_fingerprint']} -> {current}) without a G-CX verdict")
            continue
        if v["statement_fingerprint"] != current:
            errs.append(f"{slug}: G-CX: {cid}: verdict fingerprint {v['statement_fingerprint']} differs from the "
                        f"kernel report {current} for {d} (verdict stale)")
            continue
        if revised and v["decision"] != "revise":
            errs.append(f"{slug}: G-CX: {cid}: {d} was revised after this counterexample, but the verdict is "
                        f"{v['decision']!r}, not 'revise'")
        if v["decision"] == "revise" and not revised:
            errs.append(f"{slug}: G-CX: {cid}: 'revise' verdict but {d} is unchanged since the counterexample was logged")
        witness_ok = False
        if e.get("lean_witness"):
            w = kernel.get(e["lean_witness"])
            if w is None or w.get("status") != "proved":
                errs.append(f"{slug}: G-CX: {cid}: lean_witness {e['lean_witness']} is "
                            f"{'absent from' if w is None else repr(w.get('status')) + ' in'} the kernel report, not proved")
            elif str(w.get("negates_fingerprint")) != e["statement_fingerprint"]:
                # the witness must be `¬ T` for exactly the logged statement T (write it as
                # `theorem cx_<n> : ¬ (type_of% @<target>)`); a proved but unrelated theorem is no witness
                errs.append(f"{slug}: G-CX: {cid}: lean_witness {e['lean_witness']} does not negate the logged "
                            f"statement of {d} (negates_fingerprint {w.get('negates_fingerprint')!r}, "
                            f"logged fingerprint {e['statement_fingerprint']})")
            else:
                witness_ok = True
        if kind == "waived" and v["decision"] == "spurious":
            # the kernel dismisses a candidate only by proving the target itself
            if k.get("status") != "proved":
                errs.append(f"{slug}: G-CX: {cid}: a kernel-as-judge 'spurious' waiver needs {d} proved in the "
                            "kernel report (DD-59)")
        elif kind == "waived" and not witness_ok:
            # a waived refutes or revise: the kernel is the judge only through a witness
            errs.append(f"{slug}: G-CX: {cid}: a kernel-as-judge waiver needs a kernel-proved lean_witness (DD-59)")
        elif v["decision"] == "refutes" and kind is not None:
            if e["method"] in ("decide", "smt", "atp") and not witness_ok:
                errs.append(f"{slug}: G-CX: {cid}: a {e['method']} counterexample counts only once a kernel-proved "
                            "lean_witness re-establishes it (DD-16)")
            elif k.get("status") == "proved":
                errs.append(f"{slug}: G-CX: {cid}: {d} is proved in the kernel report yet the verdict says it is refuted")
            else:
                valid_refutes[kind].add(d)

    for fname, value in cx_labels:
        m = CX_CANONICAL.fullmatch(value)
        if m is None:
            errs.append(f"{slug}: {fname}: non-canonical result label {value!r} (use 'Result status: refuted "
                        "(<decl>)' or 'Result status: refuted, verdict-waived (<decl>)')")
            continue
        if has_proved_label:
            errs.append(f"{slug}: {fname}: dossier carries both a proved and a refuted result label")
        if kernel is None:
            continue
        target = m["decl"]
        if not m["waived"] and target not in valid_refutes["human"]:
            errs.append(f"{slug}: {fname}: 'refuted ({target})' label without a current human G-CX 'refutes' "
                        f"verdict on {target}" + (" (only a waived verdict: label must be 'refuted, verdict-waived')"
                                                   if target in valid_refutes["waived"] else ""))
        if m["waived"] and target not in valid_refutes["waived"]:
            errs.append(f"{slug}: {fname}: 'verdict-waived' label without a current waived 'refutes' verdict on {target}")
    return errs


def check_dossier(root, slug, kernel, kernel_problem, schemas, require_fid, conversation, base=None,
                  require_stage: int | None = None) -> list[str]:
    errs: list[str] = []
    schema = schemas["fid"]
    dossier = root / "reports" / "dossiers" / slug
    if not dossier.is_dir():
        refs = [r for r in [base] + (["HEAD"] if base is not None and base != "HEAD" else []) if r]
        if not require_fid and require_stage is None and retired(root, slug, refs):
            return []
        return [f"{slug}: dossier directory not found (a dossier with gate records is removed only by a "
                f"human tombstone reports/dossiers/{slug}.retired.json)"]
    rec_path = dossier / "fidelity.json"
    record = None
    if rec_path.exists():
        record = load_record(rec_path, schema, slug, errs)
    elif require_fid:
        errs.append(f"{slug}: G-FID: no fidelity record (reports/dossiers/{slug}/fidelity.json)")

    entries = record["declarations"] if record else []
    all_labels = result_labels(dossier)
    cx_labels = [(f, v) for f, v in all_labels if CX_WORD.search(v)]
    labels = [(f, v.lower()) for f, v in all_labels if not CX_WORD.search(v)]
    needs_kernel = record is not None or require_fid or any(v.startswith("proved") for _, v in labels)
    if needs_kernel and kernel is None:
        errs.append(f"{slug}: G-FID: {kernel_problem}")

    names = [e["decl"] for e in entries]
    for dup in sorted({n for n in names if names.count(n) > 1}):
        errs.append(f"{slug}: G-FID: duplicate entry for {dup}")
    for e in entries:
        d = e["decl"]
        if e["status"] == "approved" and (not e.get("approver") or not e.get("date")):
            errs.append(f"{slug}: G-FID: {d}: approval lacks approver or date")
        if e["status"] == "waived":
            if not e.get("waiver"):
                errs.append(f"{slug}: G-FID: {d}: waiver names no waiving conversation (D5/D26)")
            elif require_fid and e["waiver"]["conversation"] != conversation:
                errs.append(f"{slug}: G-FID: {d}: waiver applies only to conversation "
                            f"{e['waiver']['conversation']!r} (pass --conversation; D5 'that conversation only')")
        if kernel is not None:
            k = kernel.get(d)
            if k is None:
                errs.append(f"{slug}: G-FID: {d}: declaration absent from the kernel report")
            elif str(k.get("statement_fingerprint")) != e["statement_fingerprint"]:
                errs.append(f"{slug}: G-FID: {d}: approved fingerprint {e['statement_fingerprint']} "
                            f"differs from kernel report {k.get('statement_fingerprint')} (approval lapsed)")
            elif not isinstance(k.get("statement_uses"), list):
                errs.append(f"{slug}: G-FID: {d}: kernel report lacks statement_uses; re-run G-KERNEL")
            else:
                # Aux/CX are exempt from coverage and editable, so an approved statement must not
                # reach them (type, or transitively through project definitions): its meaning would
                # be pinned only by code the prover may edit (Aux/CX are exempt from coverage)
                ns_dot = record["lean_namespace"].rstrip(".") + "."
                helpers = [u for u in k["statement_uses"]
                           if u.startswith(tuple(ns_dot + sub for sub in EXEMPT_SUBNAMESPACES))]
                if helpers:
                    errs.append(f"{slug}: G-FID: {d}: approved statement depends on helper declaration(s) "
                                f"{', '.join(helpers)}; definitions a statement uses belong outside Aux/CX")
    if record is not None:
        ns_name = record["lean_namespace"].rstrip(".")
        if kernel is not None and ns_name in kernel:
            errs.append(f"{slug}: G-FID: lean_namespace {ns_name!r} is itself a declaration; name the enclosing namespace")
        for n in names:
            if not n.startswith(ns_name + "."):
                errs.append(f"{slug}: G-FID: entry {n} is outside lean_namespace {ns_name!r}")
    if record is not None and kernel is not None:
        ns = record["lean_namespace"].rstrip(".") + "."
        # helper lemmas (<ns>Aux.) and counterexample witnesses (<ns>CX.) are not claims of the
        # dossier, so they need no fidelity entry; every other declaration under the namespace does
        exempt = tuple(ns + sub for sub in EXEMPT_SUBNAMESPACES)
        uncovered = sorted(n for n in kernel if n.startswith(ns) and n not in names and not n.startswith(exempt))
        for n in uncovered:
            errs.append(f"{slug}: G-FID: {n} is in namespace {record['lean_namespace']} but has no fidelity entry")
    if require_fid and record is not None and not entries:
        errs.append(f"{slug}: G-FID: fidelity record lists no declarations")

    for fname, value in labels:
        if value not in CANONICAL:
            errs.append(f"{slug}: {fname}: non-canonical result label {value!r} "
                        "(use 'Result status: proved' or 'Result status: proved, fidelity-waived')")
            continue
        if not entries:
            errs.append(f"{slug}: {fname}: result label {value!r} without a fidelity record")
            continue
        waived = [e for e in entries if e["status"] == "waived"]
        if value == "proved" and waived:
            errs.append(f"{slug}: {fname}: plain 'proved' but {len(waived)} declaration(s) are fidelity-waived; "
                        "label must be 'proved, fidelity-waived' (DD-35)")
        if value == "proved, fidelity-waived" and not waived and not gax_waived(dossier):
            errs.append(f"{slug}: {fname}: 'fidelity-waived' label but no declaration is waived")
        if kernel is not None:
            for e in entries:
                k = kernel.get(e["decl"])
                if k is not None and k.get("status") != "proved":
                    errs.append(f"{slug}: {fname}: {e['decl']} is {k.get('status')!r} in the kernel report, "
                                f"so the dossier cannot be labelled {value!r}")
    refuted = {m["decl"] for _, v in cx_labels if (m := CX_CANONICAL.fullmatch(v))}
    if require_stage is not None and require_stage >= 8:  # Stage 8 assembly waits on G-NAME (DD-17, DD-18)
        import build_name_index, check_lean_bindings  # noqa: E401 (imported here: they import this module)
        index, index_problem = build_name_index.load_index(root / "reports" / "kernel" / "name-index.txt", root / "lean")
        errs += check_lean_bindings.check_bindings(root, slug, kernel, kernel_problem, index, index_problem)
        import check_blueprint_consistency as gbp  # G-BLUEPRINT also blocks Stage 8 when a blueprint exists
        for bp in gbp.default_blueprints(root):
            if bp.is_dir():
                errs += gbp.check(root, bp)
    return (errs + dossier_structure.check_structure(root, slug, dossier, record, kernel, require_stage, refuted)
            + check_gax(root, slug, dossier, record, schemas["gax"], base, labels, require_fid, conversation)
            + check_cx(root, slug, dossier, kernel, kernel_problem, schemas["cx"], cx_labels, bool(labels),
                       record["lean_namespace"] if record else None, base))


def gax_waived(dossier: Path) -> bool:
    try:
        return any(r.get("waiver") for r in json.loads((dossier / "gax.json").read_text(encoding="utf-8")).get("records", []))
    except (OSError, ValueError, AttributeError):
        return False


def check_gax(root, slug, dossier, record, schema, base, labels, require=False, conversation=None) -> list[str]:
    """G-AX statement changes (DD-36, DD-37). A declaration that held a G-FID approval (or waiver)
    at the base or at HEAD and now carries a different fingerprint, or no entry at all, needs a G-AX
    record naming the old and new fingerprints: an added hypothesis, a weakening, or any other change
    (under DD-34 this includes a changed definition the statement reaches). gax.json is append-only."""
    errs: list[str] = []
    path = dossier / "gax.json"
    gax = load_record(path, schema, slug, errs) if path.exists() else None
    recs = gax["records"] if gax else []
    ids = [r["id"] for r in recs]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errs.append(f"{slug}: G-AX: duplicate record id {dup}")
    for r in recs:
        human = bool(r.get("approver") and r.get("date"))
        if human and r.get("waiver"):
            errs.append(f"{slug}: G-AX: {r['id']}: record carries both an approval and a waiver")
        elif not human and not r.get("waiver"):
            errs.append(f"{slug}: G-AX: {r['id']}: record lacks approver and date, and records no waiving "
                        "conversation (a waiver needs the operator's in-session G-AX extension, D26)")
    if require:  # a waiver new since the base counts only in the conversation that granted it (D26)
        base_gax, _ = git_base_log(root, slug, base, "gax.json")
        old_ids = {r.get("id") for r in (base_gax or {}).get("records", [])}
        for r in recs:
            if r.get("waiver") and r["id"] not in old_ids and r["waiver"]["conversation"] != conversation:
                errs.append(f"{slug}: G-AX: {r['id']}: waiver applies only to conversation "
                            f"{r['waiver']['conversation']!r} (pass --conversation; D26 'within a session')")
    transitions = gax_transitions(recs)
    current = {e["decl"]: e["statement_fingerprint"] for e in (record["declarations"] if record else [])}
    refs = [base] + (["HEAD"] if base is not None and base != "HEAD" else [])
    seen: set[str] = set()
    for ref in refs:
        for name in ("fidelity.json", "gax.json"):
            old, problem = git_base_log(root, slug, ref, name)
            if problem:
                errs.append(f"{slug}: G-AX: {problem}")
            if not old:
                continue
            found = (gax_log_changes(old, recs, ref) if name == "gax.json"
                     else approved_changes(old, current, transitions, ref))
            for m in found:
                msg = f"{slug}: G-AX: {m}"
                if msg not in seen:
                    seen.add(msg)
                    errs.append(msg)
    if any(r.get("waiver") for r in recs):
        for fname, value in labels:
            if value == "proved":
                errs.append(f"{slug}: {fname}: plain 'proved' but a G-AX change was waived under the operator's "
                            "kernel-as-judge extension; label must be 'proved, fidelity-waived' (D26)")
    return errs


def stamp_warnings(root: Path, slugs: list[str]) -> list[str]:
    """Non-blocking warnings (docs/lean-version-governance.md R6): a fidelity entry or G-AX record stamped with a
    `toolchain_pin` or `mathlib_rev` other than the instance's current pin was made before a bump and needs
    re-approval. The counterexample log is not compared: it is append-only, so its entries keep the pin they were
    logged under."""
    pin = lean_pin.read_pin(root / "lean")
    now = {"toolchain_pin": pin["toolchain"], "mathlib_rev": pin["mathlib_rev"]}
    out = []
    for slug in slugs:
        dossier = root / "reports" / "dossiers" / slug
        for name, key, ident in (("fidelity.json", "declarations", "decl"), ("gax.json", "records", "id")):
            try:
                entries = json.loads((dossier / name).read_text(encoding="utf-8")).get(key, [])
            except (OSError, ValueError, AttributeError):
                continue  # absent or malformed: the gate's own checks report it
            for e in entries if isinstance(entries, list) else []:
                for field, current in now.items():
                    stamped = e.get(field) if isinstance(e, dict) else None
                    if stamped and current and stamped != current:
                        out.append(f"{slug}: {name}: {e.get(ident)} was recorded under {field} {stamped}, not the current "
                                   f"{current}: it predates a bump; re-approve it (docs/lean-toolchain-upgrade.md §3)")
    return out


def load_schemas(root: Path) -> dict[str, dict]:
    return {k: json.loads((root / "references" / "schemas" / f).read_text(encoding="utf-8"))
            for k, f in (("fid", "fidelity-record.schema.json"), ("cx", "counterexample-log.schema.json"),
                         ("gax", "gax-record.schema.json"))}


def run(root: Path, slugs: list[str], require_fid: list[str], stages: dict[str, int],
        kernel_report: Path | None = None, conversation: str | None = None,
        base: str | None = None, history: bool = True) -> tuple[list[str], list[tuple[str, bool]]]:
    """The validator's whole run, for main() and the mathagents API: (findings, [(slug, require_fid)]).
    Slugs must already be valid (SLUG). No dossier named = every dossier, plus any that had gate
    records at the base or HEAD. With a base and `history`, every commit in base..HEAD is checked too (IA-01)."""
    schemas = load_schemas(root)
    kernel, problem = load_kernel(root, kernel_report or root / "reports" / "kernel" / "latest.json")
    dossiers = root / "reports" / "dossiers"
    targets = ([(s, True) for s in require_fid] + [(s, n >= 2) for s, n in stages.items() if s not in require_fid]
               + [(s, False) for s in slugs])
    base, base_problem = resolve_base(root, base)
    errs: list[str] = [f"G-CX: {base_problem}"] if base_problem else []
    if not targets:
        targets = [(p.name, False) for p in sorted(dossiers.iterdir()) if p.is_dir()] if dossiers.is_dir() else []
        if base:  # a dossier that had gate records at the base or HEAD must still exist (renames, deletions)
            for ref in {base, "HEAD"}:
                targets += [(s, False) for s in base_record_slugs(root, ref) if (s, False) not in targets]
    for slug, req in targets:
        errs += check_dossier(root, slug, kernel, problem, schemas, req, conversation, base, stages.get(slug))
    if base and history:
        errs += check_history(root, base)
    return errs, targets


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--require-fid", metavar="SLUG", action="append", default=[])
    ap.add_argument("--require-stage", nargs=2, metavar=("SLUG", "N"), action="append", default=[],
                    help="precondition for dispatching stage N on SLUG (DD-43); N >= 2 implies --require-fid")
    ap.add_argument("--root", type=Path, default=instance_root())
    ap.add_argument("--kernel-report", type=Path)
    ap.add_argument("--conversation", default=None, help="current conversation id (waiver scope)")
    ap.add_argument("--base", default=None, help="git ref the append-only counterexample logs are compared with "
                    "(default: merge base of HEAD with origin/HEAD; CI passes the PR base)")
    ap.add_argument("--no-history", action="store_true",
                    help="skip the per-commit walk over base..HEAD (snapshot comparison only)")
    args = ap.parse_args()
    stages = {slug: int(n) for slug, n in args.require_stage}
    for s in [*args.require_fid, *stages, *args.slugs]:
        if not SLUG.fullmatch(s):
            print(f"dossier validator: FAIL: invalid slug {s!r} (expected {SLUG.pattern})")
            return 2
    errs, targets = run(args.root.resolve(), args.slugs, args.require_fid, stages, args.kernel_report,
                        args.conversation, args.base, history=not args.no_history)
    for e in errs:
        print(f"FAIL {e}")
    for w in stamp_warnings(args.root.resolve(), list(dict.fromkeys(s for s, _ in targets))):
        print(f"WARN {w}")
    print(f"dossier validator (structure, G-FID, G-AX, G-CX): {len(targets)} dossier(s): " + ("FAIL" if errs else "PASS"))
    return 1 if errs else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed on any tool error
        print(f"dossier validator: FAIL: error: {exc!r}")
        sys.exit(2)
