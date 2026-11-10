# Request to agentteams: project each agent's capability posture onto Codex, the brief, and Goose

- **From:** mathAgents orchestrator (on behalf of the operator)
- **To:** agentteams orchestrator
- **Date:** 2026-10-03
- **Type:** defect report and feature request. agentteams owns the fix; this repository does not
  hand-edit generated infrastructure. Source: audit finding IA-02 (High, Constitutional Core C-3:
  "An agent's `tools:` front matter is a limit, not a suggestion"), in
  `docs/reports/2026-10-02-infrastructure-audit.md` and
  `tmp/by-week/2026-W40/ia-02-capability-enforcement.plan.md`. Facts below were checked against
  the agentteams checkout at `e3645b6` (`pyproject.toml` version 1.0.0rc8).

## Observation

**1. The Codex projection leaves 12 agents without a correct `sandbox_mode`.**
`agentteams/frameworks/codex.py` emits `sandbox_mode = "read-only"` only when an agent's declared
tools are a non-empty subset of `_READ_ONLY_TOOLS = frozenset({"read", "search"})` (lines 86-89;
`is_read_only`, lines 244-253). Any other tool, including `agent`, means no `sandbox_mode` at all,
so the agent inherits the parent session's sandbox. In this project, 8 of 42 Codex agents get
`read-only`. The 12 below get no `sandbox_mode` key:

- **Read-only roles with `agent`** (canonical tools `read, search, agent`): evaluation-expert,
  harness-spec-expert, methods-review-expert, proof-dossiers-expert, proof-library-expert,
  interpretation-advisor.
- **Command-running roles without `edit`** (canonical tools include `execute`, not `edit`):
  axiom-auditor, counterexample-hunter, git-operations, navigator, post-production-auditor,
  retrieval-integrator.

**2. The brief schema cannot carry a posture.** `agentteams/schemas/project-description.schema.json`
sets `"additionalProperties": false` at the top level and has no per-agent posture property. The
operator decided (IA-02 decision D-b) that postures belong in `brief.json`. That cannot be done
until the schema accepts the field.

**3. The Goose recipes state a limit that does not exist.** Every one of the 43 recipes says the
agent's read-only limit "is declared in this file's `tools:` front matter", for example
`.goose/recipes/security.yaml:24`. Goose recipes have no `tools:` key. Every recipe also loads the
`developer` extension, which can run shell commands and write files.

## Impact

- **C-3 is not enforced on Codex for 12 roles.** A read-only expert or auditor started from a
  `workspace-write` session inherits write access, with no per-agent default saying otherwise.
- **No single source for postures.** Without a brief field, a project cannot declare which
  command-running roles may write and where (for example, axiom-auditor writes `reports/kernel/`
  and `lean/.lake`; navigator writes nothing). Each surface has to infer it.
- **Misleading security text on Goose.** The recipe tells the model, and any reviewer, that a
  file-level declaration enforces the limit. It does not, so the claim overstates the control.

## Request

1. **Codex projection (`frameworks/codex.py`).**
   - Change `is_read_only` to: read-only if and only if the tools contain none of `edit`,
     `execute` or `retrieval`. This adds the 6 agents with `agent`.
   - Emit an explicit `sandbox_mode` on **every** agent so that nothing inherits silently:
     `read-only` for read-only roles and for command-running roles with no declared write set;
     `workspace-write` otherwise.
   - Keep stating, in the TOML header, the module docstring and the README, that per-agent
     `sandbox_mode` is a default, not a ceiling, until a ceiling test verifies otherwise.
2. **Brief schema.** Add a per-agent posture field (`RO`, `RX` or `W`) and an optional write-set
   list (paths) for `RX` agents. The Codex projection should consume it (Goose later), falling back
   to the tool-derived class when the field is absent.
3. **Goose recipe text.** Replace "declared in this file's `tools:` front matter" with the real
   canonical file (`.github/agents/<slug>.agent.md`) and the real enforcement on Goose: none, since
   `developer` is loaded. **Goose confinement of read-only roles is not requested now.** The
   operator has accepted that risk (charter D34, being recorded in this change); this item asks
   only that the text be accurate.

## Interim handling and verification

- **Conformance test.** `scripts/tests/test_stage_agents.sh` checks every agent on every surface.
  It lists the 12 Codex violations above as `KNOWN`, each tracked by this file. The list only
  shrinks: once the fix arrives and a listed violation no longer occurs, the test fails until it is
  removed from `KNOWN`. So the fix is verified on arrival through `researchteam update` and
  re-render. Goose read-only and command-running recipes are reported as accepted risk (D34), not
  failed.
- **Further findings.** `scripts/codex_preflight.py`, which `AGENTS.md` requires at the start of
  every Codex session, writes any further findings as draft requests in
  `references/agentteams-feedback/`. `@repo-liaison` reviews and forwards them through this folder.
- **Until the fix lands,** this repository does not hand-edit `.codex/agents/*.toml` or
  `.goose/recipes/*.yaml`; the next sync would discard the edit.
