# Request to agentteams: absolute skill paths in the claude build-log

- **From:** mathAgents orchestrator (on behalf of the operator)
- **To:** agentteams orchestrator
- **Date:** 2026-09-30
- **Type:** defect report. agentteams owns the fix; this repository does not hand-edit generated
  infrastructure.

## Observation

`agentteams --framework claude --update --overwrite --materialize-native` (1.0.0rc7) writes the
`front_matter_baseline` keys for skill files in `.claude/agents/references/build-log.json` as
**absolute** paths (`/<home>/<user>/…/.claude/skills/<tool>/SKILL.md`). Agent keys in the same map
are relative (`methods-review-expert.md`), and the copilot-vscode build-log has no absolute keys.

## Impact

- **Security (S-8).** Committing the build-log leaks the operator's OS username and directory
  layout. The researchteam template's own build-log shows the same defect from a macOS machine, and
  it propagates into every instance created with `init`.
- **Portability.** The keys differ between machines and collaborators, so front-matter drift
  detection is keyed to one checkout.

## Request

Key skill baselines relative to the output directory (e.g. `../skills/<tool>/SKILL.md`), matching
the agent keys. On read, migrate or ignore any legacy absolute keys.

Until the fix lands, this repository keeps `build-log.json` out of commits for the claude surface.
