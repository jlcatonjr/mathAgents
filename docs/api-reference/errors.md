# `mathagents.errors`

Exception hierarchy for errors the mathagents API raises.

Caller mistakes raise built-in exceptions (`ValueError` for an invalid slug, `FileNotFoundError`
for a missing dossier or checkout). Domain errors derive from `MathAgentsError`; each also inherits
the built-in a caller would otherwise catch, so `except RuntimeError` keeps working.

## Public Surface

### class `KernelReportError`

*exception* (bases: `MathAgentsError, RuntimeError`)

The G-KERNEL report is missing, failing, stale, or otherwise unusable (fail-closed).

### class `MathAgentsError`

*exception* (bases: `Exception`)

Base class for all mathagents-raised errors.

### class `NameIndexError`

*exception* (bases: `MathAgentsError, RuntimeError`)

The pinned-Mathlib name index is missing, stale, or malformed.

### class `RecordError`

*exception* (bases: `MathAgentsError, ValueError`)

A dossier record (fidelity.json, gax.json, counterexamples.json, kernel-snapshot.json) is malformed,
fails its schema, or names another dossier's slug.
