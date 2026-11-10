#!/usr/bin/env python3
"""Validate references/prover-engines.json and references/object-logics.json.

Fail-closed checks beyond JSON Schema:
  * any capability claim (strengths / suited_domains / unsuited_for) requires >=1 source;
  * evidence_status "verified" requires >=1 source;
  * ids are unique and default_engine / default_logic resolve;
  * every G-AX-approved axiom (fully-qualified name) has a complete approval record;
  * when references/pilots.json exists (the harness's own pilot register; instances have none): pilot ids are
    unique and of the form P<n>, each non-null dossier is a reports/dossiers/<slug>, a slug belongs to at most
    one pilot, and every object-logics.json "pilot" names a registered pilot.
Exit 0 = valid.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))
import axiom_allowlist  # noqa: E402  (DD-38 shared envelope loader)
from instance_root import instance_root  # noqa: E402

ROOT = instance_root()
REGISTRIES = [("prover-engines", "engines", "default_engine"), ("object-logics", "logics", "default_logic")]


def check_pilots(root: Path) -> list[str]:
    """The pilot register (references/pilots.json, D11/D44), checked only where it exists."""
    path = root / "references" / "pilots.json"
    if not path.is_file():
        return []
    try:
        pilots = json.loads(path.read_text())["pilots"]
    except (ValueError, KeyError, TypeError) as exc:
        return [f"unreadable register ({exc!r})"]
    problems: list[str] = [f"entry {i} has no id" for i, p in enumerate(pilots) if not isinstance(p, dict) or "id" not in p]
    pilots = [p for p in pilots if isinstance(p, dict) and "id" in p]
    ids = [p.get("id") for p in pilots]
    if len(ids) != len(set(ids)):
        problems.append("duplicate pilot ids")
    problems += [f"id {i!r} is not of the form P<n>" for i in ids if not (isinstance(i, str) and i[:1] == "P" and i[1:].isdigit())]
    slugs = [p["dossier"] for p in pilots if p.get("dossier")]
    if len(slugs) != len(set(slugs)):
        problems.append("a dossier belongs to more than one pilot")
    problems += [f"{p['id']}: dossier {p['dossier']!r} is not a reports/dossiers/<slug>"
                 for p in pilots if p.get("dossier") and not (root / "reports" / "dossiers" / str(p["dossier"])).is_dir()]
    logics = json.loads((root / "references" / "object-logics.json").read_text())["logics"]
    problems += [f"object-logics: {e['id']}: pilot {e['pilot']!r} is not in references/pilots.json"
                 for e in logics if e.get("pilot") and e["pilot"] not in ids]
    return problems


def main() -> int:
    errors: list[str] = []
    for name, key, default_key in REGISTRIES:
        data = json.loads((ROOT / "references" / f"{name}.json").read_text())
        schema = json.loads((ROOT / "references" / "schemas" / f"{name}.schema.json").read_text())
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{name}: schema: {exc.message}")
            continue
        ids = [e["id"] for e in data[key]]
        if len(ids) != len(set(ids)):
            errors.append(f"{name}: duplicate ids")
        if data[default_key] not in ids:
            errors.append(f"{name}: {default_key} '{data[default_key]}' not in registry")
        for e in data[key]:
            claims = any(e.get(f) for f in ("strengths", "suited_domains", "unsuited_for"))
            if (claims or e.get("evidence_status") == "verified") and not e["sources"]:
                errors.append(f"{name}: {e['id']}: capability claim or verified status without sources")
            # D4 + clarification C3: every non-classical object logic is deeply embedded; a theory
            # inside classical-hol (e.g. finite probability) is registered with family "classical".
            if name == "object-logics" and e.get("family") != "classical" and e.get("embedding") == "shallow":
                errors.append(f"{name}: {e['id']}: non-classical family '{e.get('family')}' must use a deep embedding (D4, C3)")
    _, _, problems = axiom_allowlist.load(ROOT / "references" / "axiom-allowlist.json")  # DD-38 shared loader
    allow = json.loads((ROOT / "references" / "axiom-allowlist.json").read_text())
    for a in allow.get("approvals", []):
        if a.get("dossier") and not (ROOT / "reports" / "dossiers" / str(a["dossier"])).is_dir():
            problems.append(f"{a.get('axiom')}: approval names dossier {a['dossier']!r}, which is not a reports/dossiers/<slug>")
    errors += [f"axiom-allowlist: {msg}" for msg in problems]
    errors += [f"pilots: {msg}" for msg in check_pilots(ROOT)]
    for err in errors:
        print(f"FAIL {err}")
    print("registries: " + ("FAIL" if errors else "PASS"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
