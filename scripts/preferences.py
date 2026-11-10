#!/usr/bin/env python3
"""Project and dossier preferences: load, merge, check (decision D32). Fail-closed.

  preferences.py check            check references/preferences.toml and every dossier's preferences.toml
  preferences.py show <slug>      print the settings in force for a dossier, and where each comes from
  preferences.py digest <slug>    the intake_sha256 a G-FID approval records (problem card + preferences)
  preferences.py readings <slug>  list the readings of the dossier's Interpretation Brief (for intake)
  preferences.py new <slug> --domain D [--readings R1,R2]
                                  start a dossier's preferences.toml from the project defaults, and a
                                  problem-card.md skeleton (intake; never overwrites an existing file)
  preferences.py set <slug|project> <key> <json-value>
                                  change a setting: the new value becomes `choice`, the old one moves
                                  to `alternatives`; the result is checked and reverted if it fails.
                                  gax.* and fidelity.* settings record operator decisions (DD-29): they
                                  are changed only from an interactive terminal, never by an agent

Every operator decision about how the project works is a setting with a `choice`, its
`alternatives` and the charter `decision` that recorded it, in references/preferences.toml (project
defaults) and reports/dossiers/<slug>/preferences.toml (that dossier's overrides and choices).

Checks: each setting is a table with `choice`, a list of `alternatives` and a `decision` naming a
charter row; the choice is not repeated among its alternatives; settings with a closed vocabulary use
a known value (object logics and engines from the registries, domains from D2, readings from the
dossier's Interpretation Brief, G-AX candidates from the brief); a dossier file names its own slug.
Exit 0 = pass; 1 = findings; 2 = error.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instance_root import charter_path, instance_root  # noqa: E402

ROOT = instance_root()

VOCAB = {  # settings whose values are a closed set (others are checked against registries or the brief)
    "sources.primary_unavailable": {"survey-statement-flagged", "two-independent-quotations", "wait-for-primary"},
    "sources.translation": {"verbatim-plus-our-translation", "published-translation"},
    "readings.selection": {"ask-at-intake", "all-formalizable", "recommended-default"},
    "fidelity.kernel_as_judge": {"offer", "never"},
}
DOSSIER_ONLY = {"readings.selected", "intake.domain", "intake.object_logic", "intake.engines"}
PROJECT_KEYS = set(VOCAB) | {"intake.default_object_logic", "intake.default_engines"}
DOSSIER_KEYS = set(VOCAB) | DOSSIER_ONLY  # plus gax.<candidate>
SETTING_FIELDS = {"choice", "alternatives", "decision"}
# How each setting is held to: "enforced" settings are checked mechanically against the dossier
# (problem card, waiver records); "advisory" ones are followed by agents and checked at the human G-FID
# review, where the statement shows whether it honours them.
OPERATOR_ONLY = ("gax.", "fidelity.")  # the operator's G-AX answers and kernel-as-judge policy (DD-29)
ENFORCED = {"readings.selected", "intake.domain", "intake.object_logic", "intake.engines", "fidelity.kernel_as_judge"}


def enforcement(key: str) -> str:
    return "enforced" if key in ENFORCED else "advisory"


def settings(data: dict, prefix: str = "", errs: list[str] | None = None) -> dict[str, dict]:
    """Flatten nested tables into {dotted.key: setting-table} for every table that has a `choice`.
    A table is either a setting (exactly choice, alternatives, decision) or a namespace holding only
    tables; anything else is reported in `errs` (when given), so a typo cannot silently drop a setting."""
    out: dict[str, dict] = {}
    for k, v in data.items():
        key = f"{prefix}{k}"
        if not isinstance(v, dict):
            if prefix and errs is not None:
                errs.append(f"{key}: a value where a setting table was expected")
            continue
        fields = set(v)
        if fields & SETTING_FIELDS or not all(isinstance(x, dict) for x in v.values()):
            if fields != SETTING_FIELDS and errs is not None:
                errs.append(f"{key}: a setting must have exactly choice, alternatives and decision "
                            f"(missing {sorted(SETTING_FIELDS - fields)}, unknown {sorted(fields - SETTING_FIELDS)})")
            if "choice" in v:
                out[key] = v
        else:
            out.update(settings(v, key + ".", errs))
    return out


def registry(root: Path) -> tuple[set[str], set[str], set[str]]:
    logics = {l["id"] for l in json.loads((root / "references" / "object-logics.json").read_text())["logics"]}
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


def brief_ids(root: Path, slug: str) -> tuple[set[str], set[str]]:
    """Readings come from the Interpretation Brief; G-AX candidates from the brief or from the Stage 1
    statement.md, where the formalizer and the audits record the candidates they find."""
    d = root / "reports" / "dossiers" / slug
    brief = (d / "interpretation.md").read_text(encoding="utf-8") if (d / "interpretation.md").exists() else ""
    stmt = (d / "statement.md").read_text(encoding="utf-8") if (d / "statement.md").exists() else ""
    return (set(re.findall(r"^#{2,4}\s+(R\d+)\b", brief, re.M)),
            set(re.findall(r"G-AX-(P\d+-\d+)", brief + stmt)))


def check_values(root: Path, key: str, values: list, where: str, slug: str | None,
                 charter: set[str], errs: list[str], setting: dict) -> None:
    logics, engines, domains = registry(root)
    readings, gax = brief_ids(root, slug) if slug else (set(), set())
    if not re.fullmatch(r"D\d+[a-z]?", str(setting.get("decision", ""))) or setting["decision"] not in charter:
        errs.append(f"{where}: {key}: decision {setting.get('decision')!r} is not a row of the decision charter")
    for v in values:
        items = v if isinstance(v, list) else [v]
        for item in items:
            bad = None
            if key in VOCAB and item not in VOCAB[key]:
                bad = f"not one of {sorted(VOCAB[key])}"
            elif key.endswith("object_logic") and item not in logics:
                bad = "not an id in references/object-logics.json"
            elif key.endswith("engines") and item not in engines:
                bad = "not an id in references/prover-engines.json"
            elif key == "intake.domain" and item not in domains:
                bad = f"not a D2 domain {sorted(domains)}"
            elif key == "readings.selected" and str(item).split(":")[0] not in readings:
                bad = f"not a reading of interpretation.md {sorted(readings)}"
            if bad:
                errs.append(f"{where}: {key}: {item!r} is {bad}")
    if key.startswith("gax.") and slug is not None and key[4:] not in gax:
        errs.append(f"{where}: {key}: G-AX-{key[4:]} is not a candidate in interpretation.md or statement.md")


def check_file(root: Path, path: Path, slug: str | None, charter: set[str]) -> list[str]:
    errs: list[str] = []
    where = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{where}: unreadable: {exc}"]
    if data.get("schema_version") != 1:
        errs.append(f"{where}: schema_version must be 1")
    if slug is not None and data.get("slug") != slug:
        errs.append(f"{where}: slug {data.get('slug')!r} does not match its directory {slug!r}")
    top = {k for k, v in data.items() if not isinstance(v, dict)}
    for k in sorted(top - ({"schema_version", "slug"} if slug else {"schema_version"})):
        errs.append(f"{where}: unknown top-level key {k!r}")
    shape: list[str] = []
    found = settings(data, errs=shape)
    errs.extend(f"{where}: {e}" for e in shape)
    if slug is None:
        for key in sorted(PROJECT_KEYS - set(found)):
            errs.append(f"{where}: {key}: a required project setting is missing")
    for key in found:
        allowed = DOSSIER_KEYS if slug is not None else PROJECT_KEYS
        if key not in allowed and not (slug is not None and key.startswith("gax.")):
            hint = ("a project-only default in a dossier file" if key.startswith("intake.default_") and slug
                    else "a dossier-only setting in the project file" if slug is None and (key in DOSSIER_ONLY or key.startswith("gax."))
                    else "an unknown setting (check its spelling)")
            errs.append(f"{where}: {key}: {hint}")
    for key, s in found.items():
        alts = s.get("alternatives")
        if not isinstance(alts, list):
            errs.append(f"{where}: {key}: alternatives must be a list")
            continue
        choice = s["choice"]
        if choice in alts or (key == "readings.selected" and isinstance(choice, list)
                              and set(choice) & {a for a in alts if isinstance(a, str)}) or (
                isinstance(choice, list) and any(isinstance(a, list) and sorted(a) == sorted(choice) for a in alts)):
            errs.append(f"{where}: {key}: the choice is also listed among its alternatives")
        check_values(root, key, [s["choice"], *alts], where, slug, charter, errs, s)
    return errs


def charter_ids(root: Path) -> set[str]:
    text = charter_path(root).read_text(encoding="utf-8")
    return set(re.findall(r"^\|\s*([DC]\d+[a-z]?)\s*\|", text, re.M))


def effective(root: Path, slug: str) -> dict[str, tuple[object, str]]:
    """{key: (choice, source)}: the dossier's setting if it has one, else the project default."""
    out: dict[str, tuple[object, str]] = {}
    proj = root / "references" / "preferences.toml"
    if not proj.exists():
        raise FileNotFoundError("references/preferences.toml is missing; the project's settings are unknown")
    for key, s in settings(tomllib.loads(proj.read_text(encoding="utf-8"))).items():
        out[key] = (s["choice"], "references/preferences.toml")
    dos = root / "reports" / "dossiers" / slug / "preferences.toml"
    if dos.exists():
        for key, s in settings(tomllib.loads(dos.read_text(encoding="utf-8"))).items():
            out[key] = (s["choice"], f"reports/dossiers/{slug}/preferences.toml")
    # intake.default_* only fill a card field that is absent; they never constrain a dossier's card
    return out


def check_all(root: Path) -> list[str]:
    charter = charter_ids(root)
    proj = root / "references" / "preferences.toml"
    errs = check_file(root, proj, None, charter) if proj.exists() else [f"{proj} missing"]
    for p in sorted((root / "reports" / "dossiers").glob("*/preferences.toml")):
        errs += check_file(root, p, p.parent.name, charter)
    return errs


def toml_value(v) -> str:
    return json.dumps(v, ensure_ascii=False)  # strings and lists of strings are valid TOML in JSON form


def set_setting(root: Path, target: str, key: str, value) -> str | None:
    """Edit one setting in place, keeping comments; returns an error or None."""
    path = root / "references" / "preferences.toml" if target == "project" else root / "reports" / "dossiers" / target / "preferences.toml"
    if not path.exists():
        return f"{path} does not exist"
    text = path.read_text(encoding="utf-8")
    current = settings(tomllib.loads(text)).get(key)
    if current is None:
        return f"{key}: no such setting in {path.name} (add the table first, or set it on the other file)"
    parts = key.split(".")
    header = "[" + ".".join(f'"{x}"' if "-" in x else x for x in parts) + "]"
    lines = text.splitlines(keepends=True)
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == header)
    except StopIteration:
        return f"{key}: table header {header} not found"
    end = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
    old = current["choice"]
    if key == "readings.selected":  # alternatives are the brief's other readings, not other lists
        chosen = {str(v).split(":")[0] for v in (value if isinstance(value, list) else [value])}
        alts = [r for r, _ in readings_of(root, target) if r not in chosen] if target != "project" else []
    else:
        alts = [a for a in current["alternatives"] if a != value]
        if old != value and old not in alts:
            alts = [old] + alts
    for i in range(start + 1, end):
        if lines[i].startswith("choice ="):
            lines[i] = f"choice = {toml_value(value)}\n"
        elif lines[i].startswith("alternatives ="):
            lines[i] = f"alternatives = {toml_value(alts)}\n"
    path.write_text("".join(lines), encoding="utf-8")
    try:
        errs = check_all(root)
    except Exception as exc:  # restore on any failure, then report it
        path.write_text(text, encoding="utf-8")
        return f"rejected, file restored: {exc!r}"
    if errs:
        path.write_text(text, encoding="utf-8")
        return "rejected, file restored: " + "; ".join(errs)
    return None


def readings_of(root: Path, slug: str) -> list[tuple[str, str]]:
    brief = root / "reports" / "dossiers" / slug / "interpretation.md"
    if not brief.exists():
        return []
    return re.findall(r"^#{2,4}\s+(R\d+)\.?\s*(.*)$", brief.read_text(encoding="utf-8"), re.M)


def new_dossier(root: Path, slug: str, domain: str, readings: list[str]) -> str | None:
    d = root / "reports" / "dossiers" / slug
    d.mkdir(parents=True, exist_ok=True)
    pref, card = d / "preferences.toml", d / "problem-card.md"
    if pref.exists() or card.exists():
        return "preferences.toml or problem-card.md already exists; edit it (or use `set`) instead"
    proj = settings(tomllib.loads((root / "references" / "preferences.toml").read_text(encoding="utf-8")))
    logic, engines = proj["intake.default_object_logic"], proj["intake.default_engines"]
    sel = proj["readings.selection"]["choice"]
    all_r = [r for r, _ in readings_of(root, slug)]
    other = [r for r in all_r if r not in readings]
    _, _, domains = registry(root)
    body = [f"# {slug}: dossier preferences (written at intake by scripts/preferences.py new).",
            "# Each setting: choice, alternatives, decision. Change with `scripts/preferences.py set` or by",
            "# editing, then run `scripts/preferences.py check`. See references/preferences.toml for the format.",
            "", "schema_version = 1", f'slug = "{slug}"', ""]
    if all_r:
        body += ["[readings.selected]", f"choice = {toml_value(readings)}", f"alternatives = {toml_value(other)}",
                 'decision = "D30"', ""]
    body += ["[intake.domain]", f"choice = {toml_value(domain)}",
             f"alternatives = {toml_value(sorted(x for x in domains if x != domain))}", 'decision = "D2"', "",
             "[intake.object_logic]", f"choice = {toml_value(logic['choice'])}", f"alternatives = {toml_value(logic['alternatives'])}",
             'decision = "D4"', "",
             "[intake.engines]", f"choice = {toml_value(engines['choice'])}", f"alternatives = {toml_value(engines['alternatives'])}",
             'decision = "D6"', ""]
    pref.write_text("\n".join(body), encoding="utf-8")
    card.write_text("\n".join([
        f"# Problem card: {slug}", "",
        "- **Source:** <quoted statement of record, with its citation and page (D29)>",
        "- **Informal statement:** <verbatim>",
        f"- **Domain:** {domain}",
        f"- **Object logic:** {logic['choice']}",
        f"- **Engine:** {', '.join(engines['choice'])}",
        *([f"- **Reading:** {', '.join(readings)}"] if all_r else []),
        "", f"<!-- readings.selection = {sel}: when it is ask-at-intake, the readings above are the user's choice -->", ""]),
        encoding="utf-8")
    errs = check_all(root)
    return ("written, but: " + "; ".join(errs)) if errs else None


def main(argv: list[str]) -> int:
    root = ROOT
    args = argv[1:]
    if args[:1] == ["--root"]:
        root, args = Path(args[1]).resolve(), args[2:]
    if args[:1] == ["check"]:
        errs = check_all(root)
        for e in errs:
            print(f"FAIL {e}")
        print("preferences: " + ("FAIL" if errs else "PASS"))
        return 1 if errs else 0
    if args[:1] == ["readings"] and len(args) == 2 and re.fullmatch(r"[a-z0-9][a-z0-9-]*", args[1]):
        found = readings_of(root, args[1])
        for r, title in found:
            print(f"{r}\t{title}")
        return 0 if found else 1
    if args[:1] == ["new"] and len(args) >= 4 and re.fullmatch(r"[a-z0-9][a-z0-9-]*", args[1]) and args[2] == "--domain":
        readings = args[5].split(",") if len(args) >= 6 and args[4] == "--readings" else []
        err = new_dossier(root, args[1], args[3], readings)
        print(f"preferences: {err}" if err else f"preferences: wrote reports/dossiers/{args[1]}/preferences.toml and problem-card.md")
        return 1 if err else 0
    if args[:1] == ["set"] and len(args) == 4 and (args[1] == "project" or re.fullmatch(r"[a-z0-9][a-z0-9-]*", args[1])):
        try:
            value = json.loads(args[3])
        except ValueError:
            value = args[3]  # a bare word is a string
        if args[2].startswith(OPERATOR_ONLY) and not sys.stdin.isatty():
            print(f"preferences: REFUSED: {args[2]} records an operator decision (DD-29); "
                  "change it yourself in a terminal")
            return 1
        err = set_setting(root, args[1], args[2], value)
        print(f"preferences: {err}" if err else f"preferences: {args[2]} = {toml_value(value)} in {args[1]}")
        return 1 if err else 0
    if args[:1] == ["digest"] and len(args) == 2 and re.fullmatch(r"[a-z0-9][a-z0-9-]*", args[1]):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import dossier_structure
        print(dossier_structure.intake_digest(root / "reports" / "dossiers" / args[1]))
        return 0
    if args[:1] == ["show"] and len(args) == 2 and re.fullmatch(r"[a-z0-9][a-z0-9-]*", args[1]):
        if not (root / "reports" / "dossiers" / args[1]).is_dir():
            print(f"preferences: no dossier {args[1]!r}")
            return 1
        files = [root / "references" / "preferences.toml", root / "reports" / "dossiers" / args[1] / "preferences.toml"]
        alts = {}
        for f in files:
            if f.exists():
                alts.update({k: v.get("alternatives") for k, v in settings(tomllib.loads(f.read_text(encoding="utf-8"))).items()})
        for key, (value, source) in sorted(effective(root, args[1]).items()):
            print(f"{key:36} = {json.dumps(value, ensure_ascii=False)}\n{'':36}   [{enforcement(key)}] from {source}; "
                  f"alternatives: {json.dumps(alts.get(key), ensure_ascii=False)}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:  # fail closed
        print(f"preferences: FAIL: error: {exc!r}")
        sys.exit(2)
