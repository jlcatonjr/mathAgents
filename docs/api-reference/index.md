# mathagents API reference

`mathagents` is the Python API of the mathAgents harness. It follows the agentteams API pattern: one
public module per capability, keyword-only entry points, dataclass results, no printing. A module or
symbol is **public only if it is documented here** (see [`STABILITY.md`](../../STABILITY.md)). Decision IDs,
gate codes and harness terms used on these pages are defined in the [glossary](#glossary) below.

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

- **Keyword-only arguments.** Every function except `cli.main` and `config.switch` takes
  `root: Path | None = None`: the root of the mathAgents checkout or of an [instance](#glossary) that the
  call works on (default: `MATHAGENTS_ROOT`, else the checkout an editable install lives in; an installed
  wheel has no default). Every page's `root` parameter means this. Dossiers are named by slug
  (`[a-z0-9][a-z0-9-]*`).
- **The on/off switch.** The Python API does not consult the per-machine switch (`MATHAGENTS_ENABLED`,
  see [`config`](config.md)); only the `mathagents run`, `bump` and `status` commands honour it.
- **Results, not output.** Gates return `GateResult` or `CommandResult` (see [`results`](results.md)),
  `run_kernel_gate` returns `KernelGateResult` and `run_gates` returns `GatesReport`. Writers return a
  result with `success`, `errors` and `notices`. The API never prints, logs or exits; the one exception
  is [`cli.main`](cli.md), the command's entry point, which prints and can raise `SystemExit`.
- **Fail-closed.** A finding, a stale kernel report or an unreadable record makes `success` False.
  Loaders raise `KernelReportError` or `RecordError` (see [`errors`](errors.md)). Caller mistakes and
  missing inputs raise one of these built-in exceptions:
  - `ValueError`: an invalid slug, stage number or argument value;
  - `FileNotFoundError`: no such dossier, or a required input file (such as the kernel report) is absent;
  - `TypeError`: a single string where a list of slugs is expected;
  - `PermissionError`: a real snapshot write into a tree that is neither the package's checkout nor a
    declared instance.

  Each function's Raises list names the ones it can raise, including any others (for example
  `json.JSONDecodeError` from an unparseable input file).
- **Dry runs.** Every writer of dossier or settings files (`log_counterexample`, `record_lean_witness`,
  `snapshot_kernel`, `set_preference`, `create_dossier`) takes `dry_run`. A dry run performs every check
  the real run would except `snapshot_kernel`'s write-target check (`PermissionError`), and writes nothing
  to the checkout. Three functions write only generated,
  machine-local output and have no dry run: `run_kernel_gate` (the kernel report; `write_report=False`
  skips it), `build_name_index` and `probe_machine`. `run_gates(run_kernel=True)` writes the kernel
  report too, through `run_kernel_gate`.
- **Verbs.** `check_*` runs a gate in-process, `validate_*` runs a validator, `require_*` checks a stage
  precondition, `load_*` reads a project-wide input (the kernel report and name index raise when
  unusable; `load_axiom_envelope` reports content problems in `problems` but raises when the allowlist is
  missing or unparseable; the registry loaders do not validate, which is `validate_registries`' job), and
  `read_*` reads one optional record (None when it is absent).
- **One source of gate logic.** The scripts under `scripts/` remain the CLI. The API calls their
  functions in-process, or runs them as subprocesses where a script has only a `main`, so the API and
  the CLI cannot disagree. The scripts always come from the package's harness (the checkout, or the
  copy inside the wheel), never from `root`: an instance holds data, not gate code (`docs/module.md`).

## The human-decision boundary (DD-29)

This section is the boundary's full statement; module pages link here rather than repeat it.

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
| Settings | [`config`](config.md) | The per-machine on/off switch (`MATHAGENTS_ENABLED` in a gitignored `.env`) |
| Sources | [`evidence`](evidence.md) | Evidence layer and claim ledgers |
| All | [`gates`](gates.md) | Every automated gate, in CI order (G-KERNEL, G-NAME, G-BLUEPRINT, registries, preferences, dossiers) |
| Types | [`results`](results.md), [`errors`](errors.md) | Shared result types and the exception hierarchy |
| Command | [`cli`](cli.md) | The `mathagents` command: run gates on an instance, init, sync, agent export, status, doctor |

Not in the API (CLI or operator only): `scripts/operator/*`, `scripts/refresh_agent_surfaces.sh`,
decision signing, and the shell test suites.

## Glossary

IDs on these pages come from two documents. `DD-n` is a design decision of the harness specification,
[`reports/02-harness-spec.md`](../../reports/02-harness-spec.md) ("spec DD-n" on a page means that
entry). `Dn` is a decision of the project charter, summarized row by row in
[`docs/charter/decisions-summary.md`](../charter/decisions-summary.md).

| Term | Meaning | Source |
|---|---|---|
| G-KERNEL | The automated proof-integrity gate: builds the Lean library, replays it in the kernel, checks each declaration's axiom envelope, and writes `reports/kernel/latest.json`. A result counts as proved only when that report says `proved`. | spec "G-KERNEL", DD-14; D1 |
| G-FID | The human statement-fidelity gate: a person approves that a Lean statement says what the informal problem says. | spec "G-FID"; D5 |
| G-AX | The human gate for axioms, added hypotheses and weakened statements, recorded in `gax.json` and the axiom allowlist. | spec "G-AX"; D5 |
| G-CX | The human gate for counterexample verdicts, over the append-only `counterexamples.json` log. | spec "G-CX"; D5 |
| G-NAME | The automated check that every Lean name a dossier's prose cites resolves (kernel report or pinned Mathlib name index). | spec "G-NAME" |
| G-BLUEPRINT | The automated marker-consistency check between a blueprint and the Lean library. | spec "G-BLUEPRINT" |
| Instance | A repository that consumes the installed harness: it holds the data (`mathagents.toml`, dossiers, `lean/`), while the gate code comes from the package. | D35; [`docs/module.md`](../module.md) |
| Fresh (current) report | A kernel report that passes the freshness checks every gate applies; see [`kernel`](kernel.md). | spec "G-KERNEL" |
| Kernel-as-judge | An operator directive, for one conversation only, that lets the kernel's verdict stand in for a human gate; it covers G-FID and G-CX by default and G-AX only when the operator extends it. Records made under it carry a waiver label. | D5, D26; DD-30 |
| Interpretation Brief | A brief, commissioned from `@interpretation-advisor` when an informal statement admits rival readings, that lists the readings (R-ids) before Stage 1. | spec Stage 0, DD-2 |
| Stage 0-8 | The nine pipeline stages, from intake (0) to dossier assembly (8); see [`dossiers.STAGES`](dossiers.md). | spec "Pipeline Stages" |
| P1-P4 | The parts of the Lean pin: P1 `lean/lean-toolchain`, P2 the lakefile's Mathlib `rev`, P3 the manifest's Mathlib entry, P4 the toolchain of the Mathlib checkout on disk. | [`docs/lean-version-governance.md`](../lean-version-governance.md) |
| Preferences | Operator settings, each with its choice, alternatives and decision, in `references/preferences.toml` and per dossier. | D32 |

