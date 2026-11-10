---
name: tool-lean-4
description: "Lean 4 operational reference in mathAgents — configuration, API surface, invocation, and verification. Consult when working with Lean 4."
---
<!--
SECTION MANIFEST
| section_id       | designation  |
|------------------|--------------|
| tool_api_surface | FENCED       |
| key_api_surface  | FENCED       |
| verification     | FENCED       |
-->

# Lean 4 — Tool Reference — mathAgents

> Operational reference for **Lean 4 (version pinned in lean/lean-toolchain; generation-time default v4.34.1)** in mathAgents.
> Lean 4 is a tool the team *uses* — not an agent. Any agent may consult this
> document; configuration and invocation changes should follow the procedures below
> and route security-sensitive changes through `@security`.

**Tool:** `Lean 4` `(version pinned in lean/lean-toolchain; generation-time default v4.34.1)`
**Configuration files:** `lean/lean-toolchain, lean/lakefile.toml`
**Invocation target:** ``

---

## Official Documentation

Consult the official Lean 4 documentation at: `https://lean-lang.org/doc/reference/{version}/`

**Version resolution.** The version is not fixed: this project pins it in `lean/lean-toolchain`. Before relying on version-specific behaviour or documentation:

1. Read `lean/lean-toolchain` in this project and apply the pattern `v(?P<version>[0-9]+\.[0-9]+\.[0-9]+(?:-rc[0-9]+)?)`; its `version` group is the pinned version.
2. Run `python3 scripts/lean_docs.py --online`. It prints the resolved version and documentation URLs; when it succeeds, its output takes precedence over step 1.
3. Consult `https://lean-lang.org/doc/reference/{version}/` with `{version}` replaced by the resolved version.

`v4.34.1` is the generation-time default recorded when this document was generated; use it only when the pin file is missing or does not match, and say so.

Verify configuration options, API signatures, and version-specific behavior against this
documentation before making changes.

<!-- AGENTTEAMS:BEGIN key_api_surface v=1 -->
## Key API Surface
<!-- AGENTTEAMS:END key_api_surface -->

<!-- AGENTTEAMS:BEGIN tool_api_surface v=1 -->
- `lake build [targets]`: build the library; the kernel checks every declaration.
- `lake env <cmd>`: run a command in Lake's environment (e.g. `lake env lean File.lean`, `lake env leanchecker Module`).
- `lake update`: resolve dependencies and rewrite `lake-manifest.json`.
- `lake exe cache get [files]`: fetch Mathlib build artifacts, optionally only for the given files' import closure.
- `lean --json`, `lean --deps`, `lean -E <kind>`: machine-readable messages, dependency listing, promote message kinds to errors.
- `leanchecker <Module>` (bundled with the toolchain): replay a module's declarations through the kernel.
- `#print axioms <decl>`: the axioms a declaration depends on (G-KERNEL automates this).
<!-- AGENTTEAMS:END tool_api_surface -->

<!-- Document the primary classes, functions, CLI commands, or configuration keys needed to operate Lean 4 effectively. -->

## Common Patterns & Pitfalls

- Toolchain and Mathlib are pinned together (`lean/lean-toolchain`, `lean/lakefile.toml`); use stable tags only.
- Lean 4.34 reports ``declaration uses `sorry` `` with backticks; older versions used quotes.
- `native_decide` mints auxiliary axioms (`<decl>._native.native_decide.ax_*`); it is forbidden in the library.
- A metaprogram can add an unchecked declaration that "proves" `False` with no axioms, so metaprogramming commands are forbidden and `leanchecker` replay is part of the gate.
- `lake update` on a shallow Mathlib clone fetches all tags; on slow links write the manifest from Mathlib's own manifest instead.
- Open work goes in `MathAgentsWIP`; the proved library `MathAgents` must never import it.

<!-- Document common usage patterns, anti-patterns, and version-specific gotchas for Lean 4 (version pinned in lean/lean-toolchain; generation-time default v4.34.1). -->

---

## Config Management

Current configuration lives in: `lean/lean-toolchain, lean/lakefile.toml`

Before any configuration change:
1. Read the current configuration file
2. Verify the proposed change is backward-compatible with `(version pinned in lean/lean-toolchain; generation-time default v4.34.1)`
3. If the change modifies security-sensitive settings, request clearance from `@security`
4. Back up the existing config by saving as `<filename>.backup` before writing
5. Apply the change and verify the tool starts correctly

## Invocation Procedure

1. Read current config from `lean/lean-toolchain, lean/lakefile.toml` to confirm expected state
2. Run: ``
3. Capture stdout and stderr
4. Check exit code — non-zero exit is a failure; log and escalate
5. Verify output artifacts exist in expected locations

<!-- AGENTTEAMS:BEGIN verification v=1 -->
## Verification

After every invocation, verify:
- All expected output files are present
- Output is not empty (zero-byte output indicates silent failure)
- No error or warning lines appear in the log that weren't present in the previous successful run
<!-- AGENTTEAMS:END verification -->

## Cleanup

After successful verification:
- Remove intermediate/temporary files generated by `Lean 4` (not final outputs)
- Compress large log files if > 10 MB
- Do not remove `lean/lean-toolchain, lean/lakefile.toml`

## When to Involve the Team

Raise with `@orchestrator` (and `@security` for credentials/access) when:
- Lean 4 exits non-zero on two consecutive runs after config review
- Config state is inconsistent with `(version pinned in lean/lean-toolchain; generation-time default v4.34.1)` requirements
- A security-sensitive setting requires modification
