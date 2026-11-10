#!/usr/bin/env python3
"""Append to a dossier's G-CX counterexample log (spec DD-15, DD-16, DD-39, DD-59). Fail-closed.

The only sanctioned way to write `reports/dossiers/<slug>/counterexamples.json`, so that
`@counterexample-hunter` needs commands but no file-edit grant (charter §5 "Read + Bash").

  log_counterexample.py add <slug> --decl NAME --method M --description TEXT [--engine ID] [--namespace NS]
      Appends a candidate with the next CX id. The target's statement_fingerprint is taken from the
      current, fresh G-KERNEL report, never from the caller. Creates the log if absent, with the
      fidelity record's lean_namespace (or --namespace when there is no fidelity record yet).
  log_counterexample.py witness <slug> CX-n WITNESS_DECL
      Records `lean_witness` on an existing entry, only if the witness is proved in the kernel report
      and negates exactly the logged statement (negates_fingerprint). For the orchestrator, once
      @lean-prover reports the witness.

Neither mode writes or changes a verdict, removes an entry, or edits a logged field. Verdicts are
human decisions (DD-29), recorded by hand. Exit 0 = written; 1 = refused; 2 = error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lean_pin  # noqa: E402  (the pin stamped on new entries, R6)
import validate_dossier as vd  # noqa: E402  (kernel freshness check shared with the gate)
from instance_root import instance_root  # noqa: E402


def refuse(msg: str) -> int:
    print(f"log_counterexample: REFUSED: {msg}")
    return 1


def write_atomic(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".counterexamples.", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


METHODS = ("decide", "small-model", "smt", "atp", "manual")


def _open_log(root: Path, slug: str) -> tuple[Path, dict, dict | None, dict | None, str | None]:
    """(log path, schema, existing log or None, kernel or None, refusal or None)."""
    if not vd.SLUG.fullmatch(slug):
        return Path(), {}, None, None, f"invalid slug {slug!r}"
    dossier = root / "reports" / "dossiers" / slug
    if not dossier.is_dir():
        return Path(), {}, None, None, f"dossier {slug} not found"
    schema = json.loads((root / "references" / "schemas" / "counterexample-log.schema.json").read_text(encoding="utf-8"))
    kernel, problem = vd.load_kernel(root, root / "reports" / "kernel" / "latest.json")
    if kernel is None:
        return Path(), {}, None, None, str(problem)
    path = dossier / "counterexamples.json"
    log = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    if log is not None:
        jsonschema.validate(log, schema)
    return path, schema, log, kernel, None


def add_candidate(root: Path, slug: str, decl: str, method: str, description: str, engine: str | None = None,
                  namespace: str | None = None, write: bool = True) -> tuple[str | None, str | None]:
    """Append a candidate (mode `add`): (message, None) or (None, refusal). Never writes a verdict."""
    if method not in METHODS:
        return None, f"unknown method {method!r} (use one of {', '.join(METHODS)})"
    path, schema, log, kernel, refusal = _open_log(root, slug)
    if refusal:
        return None, refusal
    if decl not in kernel:
        return None, f"target {decl} is not in the kernel report (stub it first)"
    if log is None:
        fid = path.parent / "fidelity.json"
        ns = json.loads(fid.read_text(encoding="utf-8"))["lean_namespace"] if fid.exists() else namespace
        if not ns:
            return None, "no fidelity record to take lean_namespace from; pass --namespace"
        log = {"schema_version": 1, "slug": slug, "lean_namespace": ns, "counterexamples": []}
    nums = [int(e["id"].split("-")[1]) for e in log["counterexamples"]]
    entry = {"id": f"CX-{max(nums, default=0) + 1}", "decl": decl,
             "statement_fingerprint": str(kernel[decl]["statement_fingerprint"]),
             "method": method, "description": description,
             "logged_by": "counterexample-hunter",
             "logged_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    if engine:
        entry["engine"] = engine
    pin = lean_pin.read_pin(root / "lean")  # R6: the pin the candidate was found under (kept: the log is append-only)
    entry.update({k: v for k, v in (("toolchain_pin", pin["toolchain"]), ("mathlib_rev", pin["mathlib_rev"])) if v})
    log["counterexamples"].append(entry)
    jsonschema.validate(log, schema)
    if write:
        write_atomic(path, log)
    return f"{'logged' if write else 'would log'} {entry['id']} against {decl} (fingerprint {entry['statement_fingerprint']})", None


def add_witness(root: Path, slug: str, cx_id: str, witness_decl: str, write: bool = True) -> tuple[str | None, str | None]:
    """Record `lean_witness` on an entry (mode `witness`): (message, None) or (None, refusal)."""
    path, schema, log, kernel, refusal = _open_log(root, slug)
    if refusal:
        return None, refusal
    if log is None:
        return None, "no counterexample log"
    entry = next((e for e in log["counterexamples"] if e["id"] == cx_id), None)
    if entry is None:
        return None, f"{cx_id} not in the log"
    if entry.get("lean_witness"):
        return None, f"{cx_id} already records lean_witness {entry['lean_witness']}"
    wk = kernel.get(witness_decl)
    if wk is None or wk.get("status") != "proved":
        return None, f"witness {witness_decl} is not proved in the kernel report"
    if str(wk.get("negates_fingerprint")) != entry["statement_fingerprint"]:
        return None, (f"witness {witness_decl} does not negate the logged statement of {entry['decl']} "
                      "(write it as `theorem cx_<n> : ¬ (type_of% @<target>)`)")
    entry["lean_witness"] = witness_decl
    jsonschema.validate(log, schema)
    if write:
        write_atomic(path, log)
    return f"{'recorded' if write else 'would record'} lean_witness {witness_decl} on {cx_id}", None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=instance_root())
    sub = ap.add_subparsers(dest="mode", required=True)
    a = sub.add_parser("add")
    a.add_argument("slug")
    a.add_argument("--decl", required=True)
    a.add_argument("--method", required=True, choices=METHODS)
    a.add_argument("--description", required=True)
    a.add_argument("--engine")
    a.add_argument("--namespace")
    w = sub.add_parser("witness")
    w.add_argument("slug")
    w.add_argument("cx_id")
    w.add_argument("witness_decl")
    args = ap.parse_args()

    if args.mode == "add":
        msg, refusal = add_candidate(args.root.resolve(), args.slug, args.decl, args.method, args.description,
                                     args.engine, args.namespace)
    else:
        msg, refusal = add_witness(args.root.resolve(), args.slug, args.cx_id, args.witness_decl)
    if refusal:
        return refuse(refusal)
    print(f"log_counterexample: {msg}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed
        print(f"log_counterexample: error: {exc!r}")
        sys.exit(2)
