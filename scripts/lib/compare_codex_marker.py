#!/usr/bin/env python3
"""Compare a fresh Codex team marker with the committed one (render check step 3d).

  compare_codex_marker.py FRESH_BUILD_LOG COMMITTED_BUILD_LOG

The interop team marker (`.codex/agents/references/build-log.json`, agentteams d31d4a0) carries a
per-run `generated_at`, and, when projected into a temp dir outside the repository, an absolute
`source_dir` (agentteams PR #98 makes it team-relative). Both are provenance of the run, not content
of the projection, so they are ignored; every other field must match. Prints a line and exits 1 on
a difference; exits 0 when equal or when neither file exists.
"""
from __future__ import annotations

import json
import sys

IGNORED = ("generated_at", "source_dir")


def load(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    for key in IGNORED:
        data.pop(key, None)
    return data


if __name__ == "__main__":
    fresh, committed = load(sys.argv[1]), load(sys.argv[2])
    if fresh != committed:
        print("Codex team marker references/build-log.json differs beyond generated_at/source_dir"
              + (" (missing in the committed projection)" if committed is None else ""))
        sys.exit(1)
