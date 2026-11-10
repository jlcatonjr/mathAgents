#!/usr/bin/env python3
"""Proposal gate: a proposed strategy-review.md must name the strategy it reviews (D39; agentteams write_policy).

  check_strategy_sha.py FILE PATH

FILE is the proposed strategy-review.md content (a temporary file); PATH is where it will be written,
`reports/dossiers/<slug>/strategy-review.md`. The review's latest round must carry a `Strategy sha256:` line equal to
the sha256 of the `strategy.md` already beside PATH, whatever its verdict. That is stricter than the dossier
validator (scripts/dossier_structure.py, DD-9), which compares the hash only for a CLEARED round: a proposed round
of either verdict must name the strategy it reviewed, and this is checked before the review lands. Under the write policy the orchestrator writes
returned artifacts verbatim and no longer fills that line itself, so the proposing agent computes it and this gate
verifies it; strategy.md is applied first.
Exit 0 = consistent; 1 = refused (with the reason); 2 = usage error.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dossier_structure import STRATEGY_SHA, VERDICT, strip_fences  # noqa: E402


def check(proposed: str, destination: Path) -> str | None:
    """None when consistent, else the reason for refusal."""
    if destination.name != "strategy-review.md":
        return f"this gate checks strategy-review.md, not {destination.name}"
    text = strip_fences(proposed)
    if not VERDICT.findall(text):
        return "the review states no 'Verdict: CLEARED' or 'Verdict: BLOCKED'"
    shas = STRATEGY_SHA.findall(text)
    if not shas:
        return "the review's latest round carries no 'Strategy sha256:' line"
    strategy = destination.parent / "strategy.md"
    if not strategy.is_file():
        return f"{strategy} does not exist yet: apply strategy.md before its review"
    current = hashlib.sha256(strategy.read_bytes()).hexdigest()
    if shas[-1] != current:
        return (f"the latest 'Strategy sha256:' ({shas[-1][:12]}…) is not the current strategy.md ({current[:12]}…); "
                "a changed strategy needs a new review round")
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    try:
        proposed = Path(argv[0]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"check_strategy_sha: cannot read the proposal ({exc})")
        return 2
    problem = check(proposed, Path(argv[1]))
    print(f"check_strategy_sha: {'REFUSED: ' + problem if problem else 'consistent'}")
    return 1 if problem else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
