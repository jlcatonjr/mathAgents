#!/usr/bin/env python3
"""Validate the Phase 1 evidence layer (references/phase1-evidence/*.jsonl). Fail-closed.

Checks, per record:
  * required fields present; status in {grounded, no-abstract};
  * every supported_claim carries a `quote` that occurs verbatim in abstract_verbatim
    (whitespace-normalized), so no claim can outrun its retrieved evidence;
  * grounded records have a non-empty abstract; no-abstract records support no claims;
  * every inventory row (verified or metadata-conflict) has exactly one evidence record.
Usage: python3 scripts/validate_evidence.py   (exit 0 = valid)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instance_root import instance_root  # noqa: E402

ROOT = instance_root()
REQUIRED = ("key", "section", "source_url", "retrieved_via", "retrieved_at", "abstract_verbatim",
            "supported_claims", "status")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def main() -> int:
    errors: list[str] = []
    records: dict[str, dict] = {}
    for f in sorted((ROOT / "references" / "phase1-evidence").glob("*.jsonl")):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{f.name}:{n}: invalid JSON ({exc})"); continue
            missing = [k for k in REQUIRED if k not in r]
            if missing:
                errors.append(f"{f.name}:{n}: missing {missing}"); continue
            key = r["key"]
            if key in records:
                errors.append(f"{key}: duplicate evidence record")
            records[key] = r
            abstract = norm(r["abstract_verbatim"])
            if r["status"] not in ("grounded", "no-abstract"):
                errors.append(f"{key}: bad status {r['status']!r}")
            if r["status"] == "grounded" and not abstract:
                errors.append(f"{key}: grounded but abstract empty")
            if r["status"] == "no-abstract" and r["supported_claims"]:
                errors.append(f"{key}: no-abstract record must not support claims")
            for c in r["supported_claims"]:
                q = norm(c.get("quote", "")) if isinstance(c, dict) else ""
                if not q or q not in abstract:
                    errors.append(f"{key}: claim quote not found verbatim in abstract: {q[:70]!r}")
    inv = list(csv.DictReader(open(ROOT / "references" / "phase1-source-inventory.csv", newline="")))
    for row in inv:
        if row["key"] not in records:
            errors.append(f"{row['key']}: inventory source has no evidence record")
    for key in records:
        if key not in {row["key"] for row in inv}:
            errors.append(f"{key}: evidence record for a key not in the inventory")
    grounded = sum(r["status"] == "grounded" for r in records.values())
    claims = sum(len(r["supported_claims"]) for r in records.values())
    for e in errors:
        print(f"FAIL {e}")
    print(f"evidence: {len(records)} records ({grounded} grounded), {claims} quoted claims: "
          + ("FAIL" if errors else "PASS"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
