# `mathagents.dossiers`

Dossiers and the pipeline's [stages 0-8](index.md#glossary): status, stage preconditions, validation,
result labels.

A dossier is `reports/dossiers/<slug>/`. `validate_dossiers` runs the dossier validator
(structure, [G-FID, G-AX, G-CX](index.md#glossary)) exactly as `scripts/validate_dossier.py` does;
`require_stage` is the precondition for dispatching stage N (spec DD-43), which at N = 8 also runs
G-NAME and, when a blueprint exists, G-BLUEPRINT.

**CLI surface:** `scripts/validate_dossier.py`

## Public Surface

### `STAGES`

Constant: a tuple of nine `Stage` entries, one per pipeline stage. Stage 0 is intake, before any Lean
work. The artifacts mirror `scripts/dossier_structure.py` (`STAGE_ARTIFACTS`).

| # | Name | Agents | Artifacts |
|---|---|---|---|
| 0 | Intake | orchestrator, interpretation-advisor | `problem-card.md` |
| 1 | Formal statement and fidelity | statement-formalizer, fidelity-auditor | `statement.md`, `fidelity.json`, `back-translation.md` |
| 2 | Proof-strategy skeleton | proof-strategist, adversarial | `strategy.md`, `strategy-review.md` |
| 3 | Explicit derivations | logic-articulator | `derivations.md` |
| 4 | Tactic-level plans | tactic-planner | `tactic-plan.md` |
| 5 | Formalization | lean-prover | (none; the Lean library) |
| 6 | Counterexample track | counterexample-hunter | (none; `counterexamples.json` when a candidate is logged) |
| 7 | Informalization | lean-informalization | `informalization.md` |
| 8 | Dossier assembly | orchestrator, axiom-auditor | `kernel-snapshot.json` |

### class `DossierStatus`

*frozen dataclass*

What a dossier holds. `stages_with_artifacts` lists the stages whose artifacts all exist;
whether a stage may be dispatched is decided by `require_stage`, never by this summary.

| Field | Type |
|---|---|
| `slug` | `str` |
| `path` | `Path` |
| `artifacts` | `tuple[str, ...]` |
| `stages_with_artifacts` | `tuple[int, ...]` |
| `lean_namespace` | `str \| None` |
| `result_labels` | `tuple[ResultLabel, ...]` |
| `has_fidelity_record` | `bool` |
| `has_counterexample_log` | `bool` |
| `has_gax_record` | `bool` |
| `has_kernel_snapshot` | `bool` |

### class `ResultLabel`

*frozen dataclass*

A result label found in a dossier file (`Result status: proved` and the like).

| Field | Type |
|---|---|
| `file` | `str` |
| `value` | `str` |

### class `Stage`

*frozen dataclass*

One pipeline stage: the agents that run it and the dossier artifacts it produces.

| Field | Type |
|---|---|
| `number` | `int` |
| `name` | `str` |
| `agents` | `tuple[str, ...]` |
| `artifacts` | `tuple[str, ...]` |

### `dossier_status(*, root=None, slug)`

Returns `DossierStatus`.

Summarize a dossier's artifacts and labels (no gate is run).

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.

### `list_dossiers(*, root=None)`

Returns `list[str]`.

Slugs of every dossier directory, sorted.

### `require_stage(*, root=None, slug, stage, conversation=None, base=None)`

Returns `GateResult`.

Precondition for dispatching `stage` on `slug` (spec DD-43). It is `validate_dossiers` with
`require_stages={slug: stage}`, so its `notices` and its handling of `base` are the same.

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `slug`: the dossier.
- `stage`: the stage to be dispatched, 0-8 (N >= 2 also requires current G-FID approvals).
- `conversation`: current conversation id, the scope of kernel-as-judge waivers.
- `base`: git ref for the append-only checks (see `validate_dossiers`).

`notices` carries the validator's non-blocking pin-stamp warnings, which the CLI prints as `WARN`
lines: a fidelity entry or G-AX record stamped with a `toolchain_pin` or `mathlib_rev` other than the
instance's current pin predates a bump and needs re-approval. They never change `success`. A missing or
unreadable Lean pin file gives no warning (the pin's fields are empty and no comparison is made); only an
error while reading it (for example a lakefile that is not UTF-8) makes `notices` say the check was
skipped, where the CLI exits with an error.

**Raises:**

- `ValueError`: invalid slug or stage.
- `RuntimeError`: git itself failed while resolving the base or reading history (fail-closed).

### `result_labels(*, root=None, slug)`

Returns `list[ResultLabel]`.

Every result label in the dossier's text files (records excluded), as the validator sees them.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.

### `validate_dossiers(*, root=None, slugs=(), require_fid=(), require_stages=None, kernel_report=None, conversation=None, base=None)`

Returns `GateResult`.

Run the dossier validator (structure, G-FID, G-AX, G-CX); fail-closed.

`notices` carries the validator's non-blocking pin-stamp warnings, which the CLI prints as `WARN`
lines: a fidelity entry or G-AX record stamped with a `toolchain_pin` or `mathlib_rev` other than the
instance's current pin predates a bump and needs re-approval. They never change `success`. A missing or
unreadable Lean pin file gives no warning (the pin's fields are empty and no comparison is made); only an
error while reading it (for example a lakefile that is not UTF-8) makes `notices` say the check was
skipped, where the CLI exits with an error.

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `slugs`: dossiers to check; none named (and no requirements) checks every dossier.
- `require_fid`: dossiers that must hold a current G-FID approval for every claim (Stage 2 gate).
- `require_stages`: `{slug: N}` preconditions for dispatching stage N (N >= 2 implies require_fid).
- `kernel_report`: report path (default `reports/kernel/latest.json`).
- `conversation`: current conversation id, the scope of kernel-as-judge waivers.
- `base`: git ref for the append-only checks (default: merge base of HEAD with origin/HEAD). With no
  `origin/HEAD` and no `base`, the check fails closed with a finding. Every commit in `base..HEAD` is
  checked too; the API has no equivalent of the CLI's `--no-history`.

**Raises:**

- `ValueError`: an invalid slug or stage number.
- `TypeError`: a single string passed where a list of slugs is expected.
- `RuntimeError`: git itself failed while resolving the base or reading history (fail-closed).
