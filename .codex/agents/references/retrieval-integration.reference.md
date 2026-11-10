<!-- AGENTTEAMS:BEGIN content v=1 -->
# Retrieval Integration Reference

Project: mathAgents

## Retrieval Mode

- Mode: sparse-vector
- Trigger contract version: v1

## Query Entrypoints

- scripts/query_literature_library.py
- bash scripts/claude_researchteam_bridge.sh library-query reports "<terms>"

## Maintenance Entrypoints

- scripts/build_literature_library.py
- scripts/check_literature_library_integrity.sh

## Source of Truth

- reports/references/bibliography.bib
- reports/references/library/literature.jsonl
- reports/references/library/library-manifest.json

## Freshness

- Staleness SLO (minutes): 60
<!-- AGENTTEAMS:END content -->
