<!--
SECTION MANIFEST
| section_id       | designation  |
|------------------|--------------|
| tool_api_surface | FENCED       |
| key_api_surface  | FENCED       |
| output_interpretation| FENCED       |
-->

# leanblueprint — CLI Reference — mathAgents

> Operational reference for the **leanblueprint ** command-line tool in mathAgents.
> leanblueprint is a tool the team *uses* — not an agent. Configuration and execution
> should follow the procedures below; route security-rule changes through `@security`.

**Tool:** `leanblueprint` ``
**Configuration files:** `N/A`

---

## Official Documentation

Consult the official leanblueprint documentation at: https://github.com/PatrickMassot/leanblueprint

Verify CLI flags, configuration options, and rule/plugin behavior against this documentation.

<!-- AGENTTEAMS:BEGIN key_api_surface v=1 -->
## Key API Surface
<!-- AGENTTEAMS:END key_api_surface -->

<!-- AGENTTEAMS:BEGIN tool_api_surface v=1 -->
- `leanblueprint new`: scaffold `blueprint/` in a Lake project.
- `leanblueprint pdf` / `web` / `checkdecls` / `all` / `serve`: build the PDF and web versions, check that every `\lean{}` name exists in Lean, and serve locally.
- LaTeX macros: `\lean{decl}`, `\leanok`, `\uses{label,...}`, `\notready`, `\mathlibok`.
<!-- AGENTTEAMS:END tool_api_surface -->

<!-- Document the primary CLI commands, configuration file format, rule/plugin system, and output formats for leanblueprint. -->

## Common Patterns & Pitfalls

- Pinned to 0.0.20 via `environment.yml`; needs graphviz (dependency graph) and a TeX installation (PDF).
- Run `leanblueprint pdf` before `web`.
- `\leanok` claims full formalization. In mathAgents it must agree with the G-KERNEL `proved` status for the named declaration, and `checkdecls` must pass.
- The blueprint's dependency graph is the Stage 2 lemma DAG; keep `\uses` in sync with the actual Lean dependencies.

<!-- Document common configurations, integration patterns, and known issues for leanblueprint . -->

---

## Config Management

Current configuration lives in: `N/A`

Before any configuration change:
1. Read the current configuration file
2. Verify the proposed change is compatible with ``
3. If the change disables security-related rules or checks, request clearance from `@security`
4. Back up the existing config by saving as `<filename>.backup` before writing
5. Apply the change and verify the tool runs successfully

## Command-Line Usage

1. Run `leanblueprint` with the project's standard flags and configuration
2. Capture stdout and stderr
3. Check exit code — non-zero exit indicates findings or errors
4. Parse output to identify actionable items vs informational messages

<!-- AGENTTEAMS:BEGIN output_interpretation v=1 -->
## Output Interpretation

After every execution:
- Categorise findings by severity (error, warning, info)
- Identify auto-fixable issues vs those requiring manual intervention
- For auto-fixable issues, apply the fix and re-run to verify
- Report remaining issues with file paths and line numbers
<!-- AGENTTEAMS:END output_interpretation -->

## Integration

- Pre-commit hooks: verify leanblueprint runs on staged files before commit
- CI pipeline: ensure leanblueprint runs in CI with the same configuration as local development
- Editor plugins: confirm real-time feedback is configured where supported

## When to Involve the Team

Raise with `@orchestrator` (and `@security` for rule changes) when:
- leanblueprint exits with an unexpected error (not a findings report)
- Configuration conflicts with another tool in the project
- Security-related rules need to be disabled
