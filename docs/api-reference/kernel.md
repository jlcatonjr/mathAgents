# `mathagents.kernel`

G-KERNEL: run the kernel gate and read its report (spec DD-14, DD-19, DD-34).

The report (`reports/kernel/latest.json`) is the only authority on whether a declaration is proved.
`load_kernel_report` applies the same freshness checks as every gate (verdict PASS, source hash
matching the Lean tree, allowlist hash, no duplicate declarations) and refuses a report that fails
them, so a caller can never read a stale status as current.

**CLI surface:** `scripts/check_proof_integrity.sh`

## Public Surface

### class `Declaration`

*frozen dataclass*

One audited declaration. `status` is `proved`, `open` or `failed`.

| Field | Type |
|---|---|
| `name` | `str` |
| `kind` | `str` |
| `module` | `str` |
| `status` | `str` |
| `statement_fingerprint` | `str` |
| `statement_uses` | `tuple[str, ...]` |
| `axioms` | `tuple[str, ...]` |
| `negates_fingerprint` | `str \| None` |
| `private` | `bool` |

### class `KernelGateResult`

*dataclass*

Outcome of `run_kernel_gate`; `report` is the fresh report when the gate passed.

| Field | Type |
|---|---|
| `success` | `bool` |
| `verdict` | `str` |
| `report_path` | `Path \| None` |
| `proved` | `int` |
| `open` | `int` |
| `failed` | `int` |
| `report` | `KernelReport \| None` |
| `output` | `str` |
| `errors` | `list[str]` |
| `notices` | `list[str]` |

### class `KernelReport`

*frozen dataclass*

A G-KERNEL report that passed the freshness checks (unless loaded with `require_fresh=False`).

| Field | Type |
|---|---|
| `path` | `Path` |
| `verdict` | `str` |
| `checked_at` | `str` |
| `lean_version` | `str` |
| `toolchain_pin` | `str` |
| `commit` | `str` |
| `dirty` | `bool` |
| `source_sha256` | `str` |
| `allowlist_sha256` | `str \| None` |
| `findings` | `tuple[str, ...]` |
| `open_markers` | `tuple[str, ...]` |
| `declarations` | `Mapping[str, Declaration]` |

### `declarations_in_namespace(*, root=None, namespace, include_helpers=True)`

Returns `list[Declaration]`.

Declarations under `namespace` in the fresh kernel report, sorted by name.

**Args:**

- `root`: mathAgents checkout.
- `namespace`: e.g. `MathAgents.P3DutchBook`.
- `include_helpers`: include `<ns>.Aux.` helper lemmas and `<ns>.CX.` witnesses.

**Raises:**

- `KernelReportError`: the report is not usable.

### `kernel_report_problem(*, root=None, path=None)`

Returns `str | None`.

Why the kernel report is unusable, or None when it is current and PASS.

**Args:**

- `root`: mathAgents checkout (default: the one this package lives in).
- `path`: report path (default `reports/kernel/latest.json` under `root`).

### `load_kernel_report(*, root=None, path=None, require_fresh=True)`

Returns `KernelReport`.

Load the G-KERNEL report.

**Args:**

- `root`: mathAgents checkout.
- `path`: report path (default `reports/kernel/latest.json`).
- `require_fresh`: refuse a report the gates would refuse (default True). False reads it as-is, for diagnostics only; statuses in a stale report are not current.

**Raises:**

- `FileNotFoundError`: no report at `path`.
- `KernelReportError`: `require_fresh` and the report is not usable.

### `run_kernel_gate(*, root=None, write_report=True, timeout=None)`

Returns `KernelGateResult`.

Build the Lean library and audit every declaration (`scripts/check_proof_integrity.sh`).

Slow: runs `lake build` and a `leanchecker` replay.

**Args:**

- `root`: mathAgents checkout.
- `write_report`: write `reports/kernel/latest.json` (False passes `--no-report`).
- `timeout`: seconds before the subprocess is killed (default: none).
