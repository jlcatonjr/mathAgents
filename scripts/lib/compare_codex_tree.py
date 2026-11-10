#!/usr/bin/env python3
"""Compare a fresh native Codex render with the committed one (render check step 3d, native case).

  compare_codex_tree.py FRESH_ROOT COMMITTED_ROOT

Under write_policy covering codex (CX-3; agentteams #319) refresh step 3a renders .codex natively and then imports
the bespoke agents. A native render is not byte-reproducible: it stamps run provenance into what it writes (a
`Generated at:` line in the security agent's threat-intelligence fence, `generated_at`/`delivered_at`/`built_at`
times, run fingerprints, the build-log's per-run write records, and the memory index's build id). This compares
.codex/agents and .agents/skills, and the native team files (.codex/hooks.json, .codex/confined-run.example.sh,
.agentteams/bin/codex-role-gate.py), with that provenance removed and nothing else:
  - text files: lines matching `Generated at: `<ISO time>`` are dropped;
  - JSON files: the keys in RUN_KEYS are dropped at any depth;
  - the memory index (memory-index.json, memory-index.vcache) and the delivery receipt are skipped (derived run
    records; the files they describe are compared themselves);
  - .agentteams-backups/ is skipped (gitignored).
Prints one line per difference and exits 1 if any; exits 0 when equal.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TREES = (".codex/agents", ".agents/skills")
FILES = (".codex/hooks.json", ".codex/confined-run.example.sh", ".agentteams/bin/codex-role-gate.py")
SKIP_NAMES = {"memory-index.json", "memory-index.vcache", "delivery-receipt.json"}
SKIP_DIRS = {".agentteams-backups"}
RUN_KEYS = {"generated_at", "delivered_at", "built_at", "manifest_fingerprint", "output_dir", "source_dir",
            "index_build_id", "files_written", "file_hashes", "prompt_root_hashes", "front_matter_baseline"}
STAMP = re.compile(r"^Generated at: `\d{4}-\d\d-\d\dT[\d:.]+Z`\s*$")


def strip(obj):
    if isinstance(obj, dict):
        return {k: strip(v) for k, v in obj.items() if k not in RUN_KEYS}
    if isinstance(obj, list):
        return [strip(v) for v in obj]
    return obj


def normal(path: Path):
    data = path.read_bytes()
    if path.suffix == ".json":
        try:
            return strip(json.loads(data))
        except ValueError:
            return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return [line for line in text.splitlines() if not STAMP.match(line)]


def listing(root: Path) -> set[str]:
    out = set()
    for tree in TREES:
        base = root / tree
        if base.is_dir():
            for p in base.rglob("*"):
                rel = p.relative_to(root)
                if p.is_file() and p.name not in SKIP_NAMES and not SKIP_DIRS & set(rel.parts):
                    out.add(rel.as_posix())
    out |= {f for f in FILES if (root / f).is_file()}
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    fresh, committed = Path(argv[1]), Path(argv[2])
    a, b = listing(fresh), listing(committed)
    problems = [f"only in the fresh render: {p}" for p in sorted(a - b)]
    problems += [f"only in the committed tree: {p}" for p in sorted(b - a)]
    problems += [f"differs beyond run provenance: {p}" for p in sorted(a & b)
                 if normal(fresh / p) != normal(committed / p)]
    if problems:
        print("\n".join(problems))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
