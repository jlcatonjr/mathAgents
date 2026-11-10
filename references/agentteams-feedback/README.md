# agentteams feedback drafts

Draft requests to agentteams that this repository's own checks generate. Today the only source is
`scripts/codex_preflight.py`, which Codex sessions run under the rule in `AGENTS.md` (IA-02). This
folder is user-owned, so updates never overwrite it.

- **Forwarding:** `@repo-liaison` reviews each draft and forwards it as a request under
  `.github/agents/references/cross-orchestrator-requests/`. The fix arrives through an agentteams or
  researchteam update; nobody hand-edits the generated agent surfaces.
- **Deduplication:** a finding's `fingerprint` line keeps the preflight from reporting it twice. That
  works for both drafts here and forwarded requests.
- **Append-only:** keep drafts after they are forwarded.
