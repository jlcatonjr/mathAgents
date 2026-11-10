"""The G-AX axiom envelope, loaded from its single home (spec DD-38). Fail-closed.

`references/axiom-allowlist.json` defines both the base envelope (`base_axioms`) and the axioms a
human approved beyond it (`approved_axioms`, each with a record in `approvals`). G-KERNEL
(scripts/proof_integrity.py) and the registry validator (scripts/validate_registries.py) both load it
through `load`, so they cannot disagree about the envelope.

The base envelope may name only Lean's standard axioms. Anything else is a G-AX decision and belongs
in `approved_axioms` with a complete record; a widened `base_axioms` is refused, not silently honoured.
"""
from __future__ import annotations

import json
from pathlib import Path

LEAN_STANDARD_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
RECORD_FIELDS = ("axiom", "approver", "date", "reason", "dossier")
# `conversation` is required too: null for an ordinary human approval, the conversation id when the
# operator approved by in-session directive under D26 (so `kernel_as_judge = never` can see it)


def load(path: Path) -> tuple[set[str], set[str], list[str]]:
    """Return (base envelope, approved axioms, problems). Problems are complete sentences; any
    problem makes the envelope unusable, and callers report it as a finding."""
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    base = set(data.get("base_axioms") or [])
    if not base:
        problems.append(f"{path.name}: no base_axioms; the envelope must be stated explicitly")
    for ax in sorted(base - LEAN_STANDARD_AXIOMS):
        problems.append(f"{path.name}: base_axioms widens the envelope with {ax}; an axiom beyond Lean's "
                        "standard three needs an approved_axioms entry with a G-AX record")
    approved = set(data.get("approved_axioms") or [])
    records = {a.get("axiom"): a for a in data.get("approvals") or []}
    for ax in sorted(approved):
        rec = records.get(ax)
        if rec is None:
            problems.append(f"{ax} is approved without an approval record")
            continue
        missing = [k for k in RECORD_FIELDS if not rec.get(k)]
        if missing:
            problems.append(f"{ax}: approval record missing {', '.join(missing)}")
        if "conversation" not in rec or not (rec["conversation"] is None or (isinstance(rec["conversation"], str) and rec["conversation"].strip())):
            problems.append(f"{ax}: approval record needs `conversation`: null, or the conversation id of an in-session directive (D26)")
    return base & LEAN_STANDARD_AXIOMS, approved, problems
