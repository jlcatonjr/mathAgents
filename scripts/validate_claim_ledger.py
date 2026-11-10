#!/usr/bin/env python3
"""Validate a deliverable against its claim ledger and the Phase 1 evidence layer. Fail-closed.

Ledger: reports/<deliverable>.claims.csv with columns
  claim_id, section, kind, claim, keys, evidence_quotes
  kind:   fact | existence | design-inference | policy
  keys:   ';'-separated citation keys (must exist in reports/references/bibliography.bib)
  evidence_quotes: '||'-separated quotes (required for kind=fact)

Checks:
  1. every ledger claim text occurs verbatim (whitespace-normalized) in the deliverable;
  2. every key exists in the bibliography;
  3. fact: >=1 quote; every quote occurs verbatim in the retrieved abstract of one of the
     claim's keys (references/phase1-evidence/*.jsonl), so a fact cannot outrun its evidence;
  4. existence: no quote needed, but the claim may only assert that the cited work exists or what
     it is titled; it must not characterize content (reviewers check; flagged when key has an
     abstract, since then a `fact` with a quote is expected);
  5. design-inference: must cite >=1 ledger claim id via 'from:C12;C14' in evidence_quotes; ids may
     reference another deliverable's ledger as 'MR:C12' (MR = reports/01-methods-review.claims.csv);
     policy: must cite >=1 charter decision via 'charter:D5;D20' that exists as a row in
     docs/charter/03-decisions.md (a decision with NO literature support says so explicitly);
  5b. decision tags: every '[DD-n]' tag in the deliverable must appear in exactly one ledger claim;
  6. every sentence in the deliverable that carries an (Author Year) citation is in the ledger.
Usage: python3 scripts/validate_claim_ledger.py reports/01-methods-review.md
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instance_root import charter_path, instance_root  # noqa: E402

ROOT = instance_root()


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip()


def main(deliverable: str) -> int:
    doc_path = ROOT / deliverable
    ledger_path = doc_path.with_suffix(".claims.csv")
    errors: list[str] = []
    doc = norm(doc_path.read_text(encoding="utf-8"))
    body = doc.split("## References")[0]
    bib = (ROOT / "reports" / "references" / "bibliography.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib))
    evidence: dict[str, str] = {}
    for f in (ROOT / "references" / "phase1-evidence").glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                evidence[r["key"]] = norm(r.get("abstract_verbatim", ""))
    rows = list(csv.DictReader(open(ledger_path, newline="", encoding="utf-8")))
    ids = [r["claim_id"] for r in rows]
    mr_path = ROOT / "reports" / "01-methods-review.claims.csv"
    mr_ids = {r["claim_id"] for r in csv.DictReader(open(mr_path, newline="", encoding="utf-8"))} if mr_path.exists() else set()
    charter = charter_path(ROOT).read_text(encoding="utf-8")
    brief_slugs = {c["slug"] for c in json.loads((ROOT / "brief.json").read_text(encoding="utf-8")).get("components", [])}
    charter_ids = set(re.findall(r"^\|\s*([DC]\d+[a-z]?)\s*\|", charter, re.M))
    if len(ids) != len(set(ids)):
        errors.append("duplicate claim_id values")
    for r in rows:
        cid, kind, claim = r["claim_id"], r["kind"].strip(), norm(r["claim"])
        keys = [k.strip() for k in r["keys"].split(";") if k.strip()]
        quotes = [norm(q) for q in r["evidence_quotes"].split("||") if q.strip()]
        if claim not in doc:
            errors.append(f"{cid}: claim text not found verbatim in {deliverable}: {claim[:60]!r}")
        for k in keys:
            if k not in bib_keys:
                errors.append(f"{cid}: key {k} not in bibliography")
        if kind == "fact":
            if not keys or not quotes:
                errors.append(f"{cid}: fact needs keys and evidence quotes")
            for q in quotes:
                if not any(q in evidence.get(k, "") for k in keys):
                    errors.append(f"{cid}: quote not in any cited key's retrieved abstract: {q[:60]!r}")
        elif kind == "existence":
            if not keys:
                errors.append(f"{cid}: existence claim needs a key")
            if any(evidence.get(k) for k in keys):
                errors.append(f"{cid}: cites a key WITH a retrieved abstract as 'existence'; use 'fact' + quote")
        elif kind == "design-inference":
            refs = re.findall(r"from:([A-Za-z0-9:;,\s]+)", r["evidence_quotes"])
            cited = {x.strip() for grp in refs for x in re.split(r"[;,]", grp) if x.strip()}
            local = {x for x in cited if not x.startswith("MR:")}
            remote = {x[3:] for x in cited if x.startswith("MR:")}
            if not cited or not local <= set(ids) or not remote <= mr_ids:
                errors.append(f"{cid}: design-inference must reference existing ledger claims via from:<ids> "
                              f"(unknown: {sorted((local - set(ids)) | {'MR:' + x for x in remote - mr_ids})})")
        elif kind == "policy":
            refs = re.findall(r"charter:([A-Za-z0-9;,\s]+?)(?=$|;?brief:)", r["evidence_quotes"])
            cited = {x.strip() for grp in refs for x in re.split(r"[;,]", grp) if x.strip()}
            briefs = set(re.findall(r"brief:([a-z0-9-]+)", r["evidence_quotes"]))
            if (not cited and not briefs) or not cited <= charter_ids or not briefs <= brief_slugs:
                errors.append(f"{cid}: policy must cite charter decisions (charter:<ids>) and/or brief components "
                              f"(brief:<slug>) that exist (unknown: {sorted((cited - charter_ids) | (briefs - brief_slugs))})")
        else:
            errors.append(f"{cid}: unknown kind {kind!r}")
    ledger_claims = [norm(r["claim"]) for r in rows]
    for tag in sorted(set(re.findall(r"\[DD-\d+\]", doc))):
        n = sum(tag in lc for lc in ledger_claims)
        if n != 1:
            errors.append(f"decision tag {tag} appears in {n} ledger claims (must be exactly 1)")
    cite = re.compile(r"\((?:[^()]*?\b(?:1[89]|20)\d{2}[a-z]?)(?:[;,][^()]*)?\)")
    for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z(*`\[])", body):
        if cite.search(sent) and not sent.lstrip().startswith(("|", "#")):
            if not any(lc and lc in sent for lc in ledger_claims):
                errors.append(f"cited sentence missing from ledger: {sent.strip()[:80]!r}")
    for e in errors:
        print(f"FAIL {e}")
    kinds = {k: sum(r['kind'].strip() == k for r in rows) for k in ("fact", "existence", "design-inference", "policy")}
    print(f"claim ledger: {len(rows)} claims {kinds}: " + ("FAIL" if errors else "PASS"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "reports/01-methods-review.md"))
