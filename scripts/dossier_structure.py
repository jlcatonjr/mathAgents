"""Dossier-structure module of the dossier validator (spec DD-1, DD-19, DD-43). Fail-closed.

Imported by scripts/validate_dossier.py. Checks, per dossier, that the stage artifacts that exist
are complete and mutually consistent, and (with --require-stage SLUG N) that every artifact the
stages before N produce exists, as the orchestrator's precondition for dispatching stage N.

Artifacts (reports/dossiers/<slug>/):
  Stage 0  problem-card.md          Source, Informal statement, Domain, Object logic, Engine
                                    (+ Reading when an Interpretation Brief exists)
  Stage 1  statement.md, fidelity.json, back-translation.md
  Stage 2  strategy.md, strategy-review.md
  Stage 3  derivations.md           every step names a rule or lemma
  Stage 4  tactic-plan.md
  Stage 7  informalization.md
  Stage 8  kernel-snapshot.json     (scripts/snapshot_kernel.py), produced BY Stage 8 assembly: consistent
                                    with fidelity.json and with the current fresh kernel report

A pre-intake dossier (only interpretation.md / README.md) passes scan mode: intake has not begun.
Any other artifact makes the problem card mandatory.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import lean_pin  # P1-P4 and the toolchain check (docs/lean-version-governance.md)

CARD_FIELDS = ("Source", "Informal statement", "Domain", "Object logic", "Engine")
PRE_INTAKE = {"interpretation.md", "interpretation.claims.csv", "README.md", "preferences.toml"}
STAGE_ARTIFACTS = {  # artifacts a stage produces; dispatching stage N requires those of stages < N
    1: ("statement.md", "fidelity.json", "back-translation.md"),
    2: ("strategy.md", "strategy-review.md"),
    3: ("derivations.md",),
    4: ("tactic-plan.md",),
    7: ("informalization.md",),
}
# kernel-snapshot.json is not a dispatch precondition: Stage 8 assembly produces it (via
# scripts/snapshot_kernel.py), and scan mode then checks it whenever it exists.
FIELD = re.compile(r"^\s*[-*]?\s*\**\s*([A-Za-z][A-Za-z ]*?)\s*\**\s*:\s*\**\s*(.*?)\s*$")
STEP = re.compile(r"^\s*(\d+)\.\s+(.*?)\s*$")
STEP_LIKE = re.compile(r"^\s*(?:[-*|]\s*)?(?:\*\*)?\(?(?:step\s*)?\d+\s*[).:]", re.I)  # any numbered line
JUSTIFICATION = re.compile(r"\[([^\[\]]+)\]\s*$")
STEP_REF = re.compile(r"(?<![A-Za-z_])(?:s|step\s*)?(\d+)(?![A-Za-z_])", re.I)
FENCE = re.compile(r"^\s*(```|~~~).*?^\s*\1\s*$|<!--.*?-->", re.M | re.S)
STRATEGY_SHA = re.compile(r"^\s*[-*]?\s*\**\s*Strategy sha256\s*\**\s*:\s*\**\s*([0-9a-f]{64})\b", re.M | re.I)
VERDICT = re.compile(r"^\s*[-*]?\s*\**\s*Verdict\s*\**\s*:\s*\**\s*(CLEARED|BLOCKED)\b", re.M | re.I)


def strip_fences(text: str) -> str:
    """Drop fenced code blocks and HTML comments: a template, example or hidden note is never a
    field, a step or a verdict."""
    return FENCE.sub("", text)


def nonempty(path: Path) -> bool:
    return path.is_file() and bool(path.read_text(encoding="utf-8", errors="replace").strip())


def card_fields(text: str, dupes: list[str] | None = None) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in strip_fences(text).splitlines():
        m = FIELD.match(line)
        if m and m.group(1).strip().lower() in {f.lower() for f in CARD_FIELDS + ("Reading",)}:
            key = next(f for f in CARD_FIELDS + ("Reading",) if f.lower() == m.group(1).strip().lower())
            if key in out and dupes is not None:
                dupes.append(key)
            out.setdefault(key, m.group(2).strip().strip("*`").strip())
    return out


def registry_ids(root: Path) -> tuple[dict[str, str], set[str], set[str]]:
    logics = {l["id"]: l.get("status", "") for l in json.loads((root / "references" / "object-logics.json").read_text())["logics"]}
    engines = {e["id"] for e in json.loads((root / "references" / "prover-engines.json").read_text())["engines"]}
    schema = json.loads((root / "references" / "schemas" / "prover-engines.schema.json").read_text())
    domains: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            if "suited_domains" in o:
                domains.update(o["suited_domains"]["items"]["enum"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(schema)
    return logics, engines, domains


def check_card(root: Path, slug: str, dossier: Path, errs: list[str]) -> dict[str, str] | None:
    path = dossier / "problem-card.md"
    if not path.exists():
        errs.append(f"{slug}: structure: no problem card (reports/dossiers/{slug}/problem-card.md; DD-1)")
        return None
    dupes: list[str] = []
    card = card_fields(path.read_text(encoding="utf-8"), dupes)
    for f in sorted(set(dupes)):
        errs.append(f"{slug}: structure: problem card states '{f}' more than once")
    for f in CARD_FIELDS:
        if not card.get(f):
            errs.append(f"{slug}: structure: problem card lacks '{f}'")
    logics, engines, domains = registry_ids(root)
    lg = card.get("Object logic")
    if lg:
        if lg not in logics:
            errs.append(f"{slug}: structure: object logic {lg!r} is not an id in references/object-logics.json")
        elif logics[lg] == "planned":
            errs.append(f"{slug}: structure: object logic {lg!r} is registered as planned, not available; "
                        "build its embedding first or declare another logic (D4)")
    for eng in split_list(card.get("Engine", "")):
        if eng not in engines:
            errs.append(f"{slug}: structure: engine {eng!r} is not an id in references/prover-engines.json")
    if card.get("Domain") and card["Domain"] not in domains:
        errs.append(f"{slug}: structure: domain {card['Domain']!r} is not one of {sorted(domains)} (D2)")
    brief = dossier / "interpretation.md"
    if brief.exists():
        readings = set(re.findall(r"^#{2,4}\s+(R\d+)\b", brief.read_text(encoding="utf-8"), re.M))
        rd = split_list(card.get("Reading", ""))
        if not rd:
            errs.append(f"{slug}: structure: an Interpretation Brief exists, so the problem card must name the "
                        "chosen reading(s) ('Reading: R<n>[, R<m>:<variant>]'; DD-2, D30)")
        for r in rd:
            if r.split(":")[0] not in readings:
                errs.append(f"{slug}: structure: reading {r!r} is not a reading of interpretation.md ({sorted(readings)})")
    check_card_vs_preferences(root, slug, card, errs)
    check_card_binding(slug, dossier, errs)
    return card


def intake_digest(dossier: Path) -> str:
    """SHA-256 over the problem card and the dossier's preferences: what a G-FID approval is given against."""
    h = hashlib.sha256()
    for name in ("problem-card.md", "preferences.toml"):
        f = dossier / name
        h.update(name.encode() + b"\0" + (f.read_bytes() if f.exists() else b"") + b"\0")
    return h.hexdigest()


def check_card_binding(slug: str, dossier: Path, errs: list[str]) -> None:
    """D32: in a dossier governed by preferences, the fidelity record names the intake it was approved
    against (`intake_sha256`: the problem card and preferences.toml), so changing either (a reading, a
    logic, an engine, or an advisory G-AX answer) lapses the approval instead of carrying it over."""
    fid, card = dossier / "fidelity.json", dossier / "problem-card.md"
    if not (dossier / "preferences.toml").exists() or not fid.exists() or not card.exists():
        return
    try:
        bound = json.loads(fid.read_text(encoding="utf-8")).get("intake_sha256")
    except ValueError:
        return  # an unparseable record is the G-FID module's finding
    if bound != intake_digest(dossier):
        errs.append(f"{slug}: structure: fidelity.json " + ("does not record intake_sha256" if not bound else
                    "was approved against a different problem card or preferences") +
                    " (D32); re-approve against the current intake (scripts/preferences.py digest <slug>)")


def split_list(value: str) -> list[str]:
    return [x.strip().strip("`") for x in re.split(r"[,;]", value or "") if x.strip()]


def check_card_vs_preferences(root: Path, slug: str, card: dict[str, str], errs: list[str]) -> None:
    """The problem card must agree with the settings in force for the dossier (decision D32), so a
    changed preference cannot silently diverge from the card Stage 1 works from."""
    import preferences
    eff = preferences.effective(root, slug)
    pairs = (("Object logic", "intake.object_logic", lambda v: [v]), ("Engine", "intake.engines", list),
             ("Domain", "intake.domain", lambda v: [v]), ("Reading", "readings.selected", list))
    for field, key, as_list in pairs:
        if key not in eff or not card.get(field):
            continue
        want, source = eff[key]
        if sorted(split_list(card[field])) != sorted(as_list(want)):
            errs.append(f"{slug}: structure: problem card '{field}: {card[field]}' disagrees with {key} = "
                        f"{want!r} in {source}; update one of them (D32)")


def check_derivations(slug: str, path: Path, card_logic: str | None, errs: list[str]) -> None:
    node = None
    have = {"Calculus": False, "Object logic": False}
    steps: set[int] = set()
    seen_nodes = 0

    def close():
        if node is not None:
            for k, v in have.items():
                if not v:
                    errs.append(f"{slug}: derivations.md: node {node!r} does not state its {k} (DD-10)")
            if not steps:
                errs.append(f"{slug}: derivations.md: node {node!r} has no steps")

    for n, line in enumerate(strip_fences(path.read_text(encoding="utf-8")).splitlines(), 1):
        if line.startswith("## Node:"):
            close()
            node, have, steps = line[len("## Node:"):].strip(), {"Calculus": False, "Object logic": False}, set()
            seen_nodes += 1
            continue
        s_like = STEP_LIKE.match(line)
        if node is None:
            if s_like:
                errs.append(f"{slug}: derivations.md:{n}: numbered step outside any '## Node:' section")
            continue
        m = FIELD.match(line)
        if m and m.group(1).strip() in have and m.group(2):
            have[m.group(1).strip()] = True
            if m.group(1).strip() == "Object logic" and card_logic and m.group(2).split()[0] != card_logic:
                errs.append(f"{slug}: derivations.md:{n}: object logic {m.group(2).split()[0]!r} differs from "
                            f"the problem card's {card_logic!r}")
            continue
        st = STEP.match(line)
        if not st:
            if s_like:
                errs.append(f"{slug}: derivations.md:{n}: step not in the '<n>. <formula>  [<rule or lemma>]' form")
            continue
        num, body = int(st.group(1)), st.group(2)
        j = JUSTIFICATION.search(body)
        just = j.group(1).strip() if j else ""
        if not just or just.startswith("?") or re.match(r"(?i)lemma\s*(\?|$)", just) or "not located" in just:
            errs.append(f"{slug}: derivations.md:{n}: step {num} names no rule or lemma (DD-43)")
            continue
        if num in steps:
            errs.append(f"{slug}: derivations.md:{n}: step {num} is numbered twice in node {node!r}")
        words = just.split(None, 2)  # "<rule> <premises>" (premises may be glued: "MP(1,5)") or "lemma <Name> <premises>"
        refs_text = (words[2] if len(words) > 2 else "") if words[0].lower() == "lemma" else just
        for ref in (int(x) for x in STEP_REF.findall(refs_text)):
            if ref >= num:
                errs.append(f"{slug}: derivations.md:{n}: step {num} cites step {ref}, which is not earlier")
            elif ref not in steps:
                errs.append(f"{slug}: derivations.md:{n}: step {num} cites step {ref}, which does not exist")
        steps.add(num)
    close()
    if seen_nodes == 0:
        errs.append(f"{slug}: derivations.md: no '## Node:' section")


def check_snapshot(slug: str, path: Path, record: dict | None, kernel: dict | None, errs: list[str],
                   root: Path | None = None) -> None:
    """DD-19: the snapshot is a copy of a fresh, clean G-KERNEL report for this dossier's namespace, and
    must still agree with the current fresh report (a hand-written or stale snapshot fails)."""
    try:
        snap = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        errs.append(f"{slug}: kernel-snapshot.json unparseable: {exc}")
        return
    for k in ("verdict", "commit", "source_sha256", "lean_version", "declarations"):
        if not snap.get(k):
            errs.append(f"{slug}: kernel-snapshot.json lacks {k} (DD-19)")
    if snap.get("verdict") not in (None, "PASS"):
        errs.append(f"{slug}: kernel-snapshot.json records verdict {snap.get('verdict')!r}, not PASS")
    if snap.get("lean_version") and snap.get("toolchain_pin") \
            and (wrong := lean_pin.toolchain_mismatch(snap["lean_version"], snap["toolchain_pin"])):
        errs.append(f"{slug}: kernel-snapshot.json was taken from a run under another Lean ({wrong})")
    if root is not None and snap.get("commit") and (root / ".git").exists():
        anc = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", "--end-of-options",
                              str(snap["commit"]), "HEAD"], capture_output=True)
        if anc.returncode != 0:
            errs.append(f"{slug}: kernel-snapshot.json commit {snap['commit']!r} is not a commit in this history")
    if snap.get("dirty") is not False:
        errs.append(f"{slug}: kernel-snapshot.json was not taken from a clean, committed lean/ tree")
    if record is None:
        errs.append(f"{slug}: kernel-snapshot.json exists but the dossier has no fidelity record")
        return
    decls = {d.get("decl"): d for d in snap.get("declarations") or []}
    for e in record["declarations"]:
        d = decls.get(e["decl"])
        if d is None:
            errs.append(f"{slug}: kernel-snapshot.json does not contain {e['decl']}")
        elif str(d.get("statement_fingerprint")) != e["statement_fingerprint"]:
            errs.append(f"{slug}: kernel-snapshot.json fingerprint {d.get('statement_fingerprint')} for {e['decl']} "
                        f"differs from the fidelity record's {e['statement_fingerprint']}")
    if kernel is not None:
        for name, d in decls.items():
            k = kernel.get(name)
            if k is None:
                errs.append(f"{slug}: kernel-snapshot.json lists {name}, which the current kernel report lacks")
                continue
            for f in ("status", "statement_fingerprint", "axioms"):
                if (k.get(f) if f != "statement_fingerprint" else str(k.get(f))) != (
                        d.get(f) if f != "statement_fingerprint" else str(d.get(f))):
                    errs.append(f"{slug}: kernel-snapshot.json {f} of {name} differs from the current kernel report; "
                                "re-take the snapshot (scripts/snapshot_kernel.py)")


def check_preferences(root: Path, slug: str, dossier: Path, errs: list[str],
                      record: dict | None = None, kernel: dict | None = None) -> None:
    """D32: a dossier's preferences file is well formed, and `fidelity.kernel_as_judge = never` means no
    waiver record may exist in the dossier's fidelity, G-CX or G-AX records."""
    import preferences
    pref = dossier / "preferences.toml"
    proj = root / "references" / "preferences.toml"
    if proj.exists():
        errs.extend(f"{slug}: preferences: {e}" for e in preferences.check_file(root, proj, None, preferences.charter_ids(root)))
    if pref.exists():
        errs.extend(f"{slug}: preferences: {e}" for e in
                    preferences.check_file(root, pref, slug, preferences.charter_ids(root)))
    choice, source = preferences.effective(root, slug).get("fidelity.kernel_as_judge", ("offer", ""))
    if choice != "never":
        return
    for name, items in (("fidelity.json", "declarations"), ("counterexamples.json", "counterexamples"), ("gax.json", "records")):
        f = dossier / name
        try:
            data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        except ValueError:
            continue  # unparseable records are the record modules' findings
        for e in data.get(items, []) if isinstance(data, dict) else []:
            waived = e.get("waiver") or (e.get("verdict") or {}).get("waiver") or e.get("status") == "waived"
            if waived:
                errs.append(f"{slug}: preferences: {name} holds a kernel-as-judge waiver ({e.get('decl') or e.get('id')}), "
                            f"but fidelity.kernel_as_judge = 'never' in {source}")
    # D26's in-session G-AX extension records allowlist approvals with the operator's directive as approver
    allow = root / "references" / "axiom-allowlist.json"
    try:
        approvals = json.loads(allow.read_text(encoding="utf-8")).get("approvals", []) if allow.exists() else []
    except ValueError:
        errs.append(f"{slug}: preferences: references/axiom-allowlist.json is unparseable; cannot check for in-session approvals")
        approvals = []
    # the allowlist is one global envelope: a `never` dossier may not depend on ANY axiom approved by
    # in-session directive, whichever dossier the approval names
    in_session = {a.get("axiom") for a in approvals if a.get("conversation") is not None}
    if record is not None and kernel is not None and in_session:
        ns = record["lean_namespace"].rstrip(".") + "."
        for name, k in sorted(kernel.items()):
            used = in_session & set(k.get("axioms", []))
            if name.startswith(ns) and used:
                errs.append(f"{slug}: preferences: {name} depends on {', '.join(sorted(used))}, approved by in-session "
                            f"directive, but fidelity.kernel_as_judge = 'never' in {source}")
    for a in approvals:
        # every record carries `conversation` (null unless in-session; enforced by scripts/axiom_allowlist.py)
        if a.get("dossier") == slug and a.get("conversation") is not None:
            errs.append(f"{slug}: preferences: axiom-allowlist approval for {a.get('axiom')} was given by in-session "
                        f"directive, but fidelity.kernel_as_judge = 'never' in {source}")


def check_structure(root: Path, slug: str, dossier: Path, record: dict | None, kernel: dict | None,
                    require_stage: int | None, refuted: set[str] | None = None) -> list[str]:
    errs: list[str] = []
    check_preferences(root, slug, dossier, errs, record, kernel)
    files = {p.name for p in dossier.iterdir() if p.is_file()}
    pre_intake = files <= PRE_INTAKE
    card = None
    if not pre_intake or require_stage is not None:
        card = check_card(root, slug, dossier, errs)
    logic = card.get("Object logic") if card else None
    for f in sorted(files - PRE_INTAKE - {"fidelity.json", "counterexamples.json", "gax.json", "kernel-snapshot.json"}):
        if f.endswith(".md") and not nonempty(dossier / f):
            errs.append(f"{slug}: structure: {f} is empty")
    if "strategy.md" in files and "strategy-review.md" not in files:
        errs.append(f"{slug}: structure: strategy.md has no strategy-review.md (the Stage 2 adversarial review, DD-9)")
    review = None
    if "strategy-review.md" in files:
        text = strip_fences((dossier / "strategy-review.md").read_text(encoding="utf-8"))
        verdicts = [v.upper() for v in VERDICT.findall(text)]
        # the latest round decides; a review counts only for the strategy it reviewed
        review = verdicts[-1] if verdicts else None
        if review is None:
            errs.append(f"{slug}: structure: strategy-review.md states no 'Verdict: CLEARED' or 'Verdict: BLOCKED'")
        shas = STRATEGY_SHA.findall(text)
        if review == "CLEARED" and "strategy.md" in files:
            cur = hashlib.sha256((dossier / "strategy.md").read_bytes()).hexdigest()
            if not shas or shas[-1] != cur:
                errs.append(f"{slug}: structure: strategy-review.md's latest 'Strategy sha256:' does not match the "
                            "current strategy.md; a changed strategy needs a new review round")
                review = "STALE"
    if "strategy.md" in files and "fidelity.json" not in files:
        errs.append(f"{slug}: structure: Stage 2 artifacts exist but there is no fidelity record (DD-33)")
    if "derivations.md" in files:
        check_derivations(slug, dossier / "derivations.md", logic, errs)
        if "strategy.md" not in files:
            errs.append(f"{slug}: structure: derivations.md exists without a Stage 2 strategy.md")
    if "tactic-plan.md" in files and "derivations.md" not in files:
        errs.append(f"{slug}: structure: tactic-plan.md exists without Stage 3 derivations.md")
    if "kernel-snapshot.json" in files:
        check_snapshot(slug, dossier / "kernel-snapshot.json", record, kernel, errs, root)
    if require_stage is not None:
        for stage, arts in STAGE_ARTIFACTS.items():
            if stage < require_stage:
                for a in arts:
                    if a not in files:
                        errs.append(f"{slug}: structure: dispatching stage {require_stage} needs {a} (stage {stage})")
        if require_stage >= 3 and review != "CLEARED":
            errs.append(f"{slug}: structure: dispatching stage {require_stage} needs strategy-review.md with "
                        "'Verdict: CLEARED' (DD-9)")
        if require_stage >= 7 and record is not None:
            for e in record["declarations"]:
                k = (kernel or {}).get(e["decl"])
                if e["decl"] in (refuted or set()):
                    continue  # a refuted statement is narrated as refuted (G-CX checks the label)
                if k is None or k.get("status") != "proved":
                    errs.append(f"{slug}: structure: dispatching stage {require_stage} needs {e['decl']} proved "
                                "in the kernel report, or refuted under G-CX")
    return errs
