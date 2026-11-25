# `mathagents.errors`

Exception hierarchy for errors the mathagents API raises.

Caller mistakes and missing inputs raise built-in exceptions; the full list is under
[Fail-closed](index.md#conventions) in the conventions. Domain errors derive from `MathAgentsError`;
each also inherits the built-in a caller would otherwise catch, so `except RuntimeError` keeps working.

Decision IDs, gate codes and terms are defined in the [glossary](index.md#glossary).

**CLI surface:** none.

## Public Surface

### class `KernelReportError`

*exception* (bases: `MathAgentsError, RuntimeError`)

The G-KERNEL report is missing, failing, stale, or otherwise unusable (fail-closed).

### class `MathAgentsError`

*exception* (bases: `Exception`)

Base class for all mathagents-raised errors.

It is also raised directly in one case: when a module of the same name as a harness gate script (such as
`validate_dossier` or `preferences`) was imported from somewhere else first, so the API would otherwise
run the wrong code. Import `mathagents` before that module, or rename it.

### class `NameIndexError`

*exception* (bases: `MathAgentsError, RuntimeError`)

The pinned-Mathlib name index is missing, stale, or malformed.

### class `RecordError`

*exception* (bases: `MathAgentsError, ValueError`)

A dossier record (fidelity.json, gax.json, counterexamples.json, kernel-snapshot.json) is malformed,
fails its schema, or names another dossier's slug.
