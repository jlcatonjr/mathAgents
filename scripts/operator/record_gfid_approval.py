#!/usr/bin/env python3
"""OPERATOR SCRIPT — run it yourself, in a terminal, outside the agent session (spec DD-29, DD-33).

  python3 scripts/operator/record_gfid_approval.py <slug>

Records YOUR G-FID (statement-fidelity) approvals for a dossier. No agent writes an approval (DD-29):
this script asks you, declaration by declaration, and writes only what you approve.

For every declaration in the dossier's Lean namespace (from the current, fresh G-KERNEL report) it
shows the Lean source and points you to the dossier's statement.md, back-translation.md and
stage1-audit.md, then asks "Approve? [y/N]". Approved entries are written to
reports/dossiers/<slug>/fidelity.json with:
  - the declaration's statement_fingerprint (a later change to the statement lapses the approval);
  - intake_sha256 over problem-card.md + preferences.toml (a later change to either lapses it, D32);
  - you as approver, and today's date.
A declaration you do not approve gets no entry, and the dossier validator then blocks Stage 2.
Re-running replaces fidelity.json with your new answers (approving again is how a lapsed approval is
renewed; if a statement's fingerprint changed since an earlier approval, a G-AX record is required too).

Afterwards:  python3 scripts/validate_dossier.py --require-fid <slug>
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import dossier_structure  # noqa: E402
import validate_dossier as vd  # noqa: E402

NAMESPACES = {"p2-lewis-triviality": "MathAgents.P2LewisTriviality", "p3-dutch-book": "MathAgents.P3DutchBook"}
AUTO = re.compile(r"\.(eq_\d+|eq_def|mk|casesOn|recOn|rec|noConfusion|noConfusionType|ctorIdx|sizeOf_spec|inj|injEq)$")


def lean_source(name: str) -> str:
    short = name.rsplit(".", 1)[-1]
    for f in sorted((ROOT / "lean").glob("MathAgents*/**/*.lean")):
        text = f.read_text(encoding="utf-8")
        m = re.search(rf"^(theorem|def|abbrev|structure|lemma)\s+{re.escape(short)}\b.*?(?=^\S|\Z)", text, re.M | re.S)
        if m and NAMESPACES and any(ns.rsplit(".", 1)[-1] in text for ns in NAMESPACES.values()):
            return f"{f.relative_to(ROOT)}:\n{m.group(0).rstrip()}"
    return "(source not located; see the Lean file)"


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in NAMESPACES:
        print(__doc__)
        return 2
    slug, ns = sys.argv[1], NAMESPACES[sys.argv[1]]
    if not sys.stdin.isatty():
        print("Run this yourself in a terminal: approvals are typed by the operator (DD-29).")
        return 2
    kernel, problem = vd.load_kernel(ROOT, ROOT / "reports" / "kernel" / "latest.json")
    if kernel is None:
        print(f"Cannot record approvals: {problem}. Run: bash scripts/check_proof_integrity.sh")
        return 1
    decls = sorted(n for n in kernel if n.startswith(ns + ".") and not AUTO.search(n)
                   and not n.startswith(tuple(ns + "." + s for s in vd.EXEMPT_SUBNAMESPACES)))
    who = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
    approver = input(f"Approver name [{who or 'operator'}]: ").strip() or who or "operator"
    d = ROOT / "reports" / "dossiers" / slug
    print(f"\nDossier {slug}. Read first: {d.relative_to(ROOT)}/statement.md, back-translation.md, stage1-audit.md\n")
    approved = []
    for n in decls:
        k = kernel[n]
        print("=" * 100)
        print(f"{n}   [{k.get('status')}]   fingerprint {k['statement_fingerprint']}")
        print(lean_source(n))
        if input("Approve this statement as a faithful formalization? [y/N] ").strip().lower() == "y":
            approved.append({"decl": n, "statement_fingerprint": str(k["statement_fingerprint"]), "status": "approved",
                             "approver": approver, "date": datetime.date.today().isoformat()})
    record = {"schema_version": 1, "slug": slug, "lean_namespace": ns,
              "intake_sha256": dossier_structure.intake_digest(d), "declarations": approved}
    if not approved:
        print("\nNothing approved; fidelity.json not written.")
        return 0
    (d / "fidelity.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {len(approved)} approval(s) of {len(decls)} to {(d / 'fidelity.json').relative_to(ROOT)}.")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_dossier.py"), "--require-fid", slug],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
