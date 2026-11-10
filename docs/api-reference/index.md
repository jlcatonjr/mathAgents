# mathagents API reference

`mathagents` is the Python API of the mathAgents harness. It follows the agentteams API pattern: one
public module per capability, keyword-only entry points, dataclass results, no printing. A module or
symbol is **public only if it is documented here** (see [`STABILITY.md`](../../STABILITY.md)).

```python
from mathagents.dossiers import require_stage
from mathagents.kernel import load_kernel_report

result = require_stage(slug="p3-dutch-book", stage=8)
if not result.success:
    print("\n".join(result.errors))
print(load_kernel_report().status("MathAgents.P3DutchBook.converse_R2"))  # "proved"
```

Install from the checkout with `pip install -e .` (Python ≥ 3.11), or into another repository from git
(see [`docs/module.md`](../module.md)). Without installing, put the checkout on `sys.path`.

## Conventions

- **Keyword-only arguments.** Every function takes `root: Path | None = None`: a mathAgents checkout or
  an instance (`mathagents.toml`, D35; default: `MATHAGENTS_ROOT`, else the checkout an editable install
  lives in; an installed wheel has no default). Dossiers are named by slug (`[a-z0-9][a-z0-9-]*`).
- **Results, not output.** Gates return `GateResult` or `CommandResult` (see [`results`](results.md)),
  `run_kernel_gate` returns `KernelGateResult` and `run_gates` returns `GatesReport`. Writers return a
  result with `success`, `errors` and `notices`. The API never prints, logs or exits.
- **Fail-closed.** A finding, a stale kernel report or an unreadable record makes `success` False.
  Loaders raise `KernelReportError` or `RecordError` (see [`errors`](errors.md)). Caller mistakes raise
  `ValueError` or `FileNotFoundError`, `TypeError` (a single string where a list of slugs is expected) or
  `PermissionError` (a real snapshot write into a tree that is neither the package's checkout nor a
  declared instance).
- **Dry runs.** Every writer of dossier or settings files (`log_counterexample`, `record_lean_witness`,
  `snapshot_kernel`, `set_preference`, `create_dossier`) takes `dry_run`. A dry run performs every gate
  check the real run would and writes nothing to the checkout. The one check it skips is
  `snapshot_kernel`'s write-target check (`PermissionError`), since a dry run writes nothing. Three functions write only generated,
  machine-local output and have no dry run: `run_kernel_gate` (the kernel report; `write_report=False`
  skips it), `build_name_index` and `probe_machine`.
- **Verbs.** `check_*` runs a gate in-process, `validate_*` runs a validator, `require_*` checks a stage
  precondition, `load_*` reads a project-wide input (the kernel report and name index raise when
  unusable; `load_axiom_envelope` reports `problems`; the registry loaders do not validate, which is
  `validate_registries`' job), and `read_*` reads one optional record (None when it is absent).
- **One source of gate logic.** The scripts under `scripts/` remain the CLI. The API calls their
  functions in-process, or runs them as subprocesses where a script has only a `main`, so the API and
  the CLI cannot disagree. The scripts always come from the package's harness (the checkout, or the
  copy inside the wheel), never from `root`: an instance holds data, not gate code (`docs/module.md`).

## The human-decision boundary (DD-29)

No API function writes a G-FID approval or waiver, a G-AX record or allowlist entry, or a G-CX verdict.
The modules that read these records (`fidelity`, `axioms`, `counterexamples`) are read-only for them.
`set_preference` refuses the operator-only `gax.*` and `fidelity.*` settings. The operator records these
decisions in a terminal (`scripts/operator/record_gfid_approval.py`, `scripts/preferences.py set`, and
hand edits to the allowlist and verdicts). `tests/test_api_boundary.py` enforces the boundary.

## Modules

| Role | Module | What it covers |
|---|---|---|
| Kernel | [`kernel`](kernel.md) | G-KERNEL: run the gate, load the report, declarations by namespace |
| Kernel | [`name_index`](name-index.md) | Pinned-Mathlib name index; resolve a Lean name |
| Pipeline | [`dossiers`](dossiers.md) | Stages, dossier status, the dossier validator, stage preconditions, result labels |
| Pipeline | [`snapshot`](snapshot.md) | Stage 8 kernel snapshot |
| Human gates (read) | [`fidelity`](fidelity.md) | G-FID records, a coverage summary, the G-FID gate |
| Human gates (read) | [`axioms`](axioms.md) | G-AX envelope, statement-change records, axiom usage |
| Human gates (read) | [`counterexamples`](counterexamples.md) | G-CX log; the sanctioned candidate and witness writer |
| Prose gates | [`bindings`](bindings.md) | G-NAME bindings |
| Prose gates | [`blueprint`](blueprint.md) | G-BLUEPRINT |
| Settings | [`preferences`](preferences.md) | D32 settings: effective values, readings, intake digest, changes |
| Settings | [`registries`](registries.md) | Object-logic and prover-engine registries |
| Settings | [`machine`](machine.md) | Machine profile for engine availability |
| Sources | [`evidence`](evidence.md) | Evidence layer and claim ledgers |
| All | [`gates`](gates.md) | Every automated gate, in CI order (G-KERNEL, G-NAME, G-BLUEPRINT, registries, preferences, dossiers) |
| Types | [`results`](results.md), [`errors`](errors.md) | Shared result types and the exception hierarchy |
| Command | [`cli`](cli.md) | The `mathagents` command: run gates on an instance, init, sync, agent export, status, doctor |
| Settings | [`config`](config.md) | The per-machine on/off switch (`MATHAGENTS_ENABLED` in a gitignored `.env`) |

Not in the API (CLI or operator only): `scripts/operator/*`, `scripts/refresh_agent_surfaces.sh`,
decision signing, and the shell test suites.
