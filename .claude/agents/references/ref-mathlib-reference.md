<!-- AGENTTEAMS:BEGIN content v=1 -->
# Mathlib Reference — mathAgents

> Quick-reference for **Mathlib v4.34.1** (library) in mathAgents.
> This is a lightweight reference file, not an agent. For operational procedures, consult the tool's reference/skill document, or escalate to `@orchestrator`.

---

## Version

`Mathlib` `v4.34.1`

## Configuration

**Config files:** `lean/lakefile.toml, lean/lake-manifest.json`

## Official Documentation

https://leanprover-community.github.io/mathlib4_docs/

## Key API Surface

- API docs by module (e.g. `Mathlib.Tactic`), searchable by declaration name.
- Automation: `simp`, `omega`, `decide`, `aesop`, `linarith`, `nlinarith`, `polyrith`, `norm_num`, `ring`, `positivity`.
- Search: `exact?`, `apply?`, `rw?`; `#check`/`#print` to inspect declarations.
- Naming conventions: https://leanprover-community.github.io/contribute/naming.html

<!-- Document the primary classes, functions, or APIs that project code depends on from Mathlib. -->

## Common Patterns & Pitfalls

- Import the narrowest modules needed (e.g. `Mathlib.Tactic.Ring`), not all of `Mathlib`; this keeps source builds fast when the cache is unavailable.
- Never invent declaration names: confirm each with `#check` or the docs before citing it in a tactic plan or a dossier.
- `exact?`/`apply?` results are suggestions; keep the explicit term they print, not the search call.

<!-- Document common usage patterns, best practices, and known issues for Mathlib v4.34.1. -->

## Key Conventions

- Follow project style rules when using Mathlib
- Refer to authority sources for API contract accuracy
- Validate changes against existing tests before committing

## Related Agents

- `@technical-validator` — verify technical accuracy of Mathlib usage
- `@primary-producer` — implements code that depends on Mathlib
<!-- AGENTTEAMS:END content -->
