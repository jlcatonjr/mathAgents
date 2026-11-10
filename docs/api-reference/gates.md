# `mathagents.gates`

Run the automated gates together, in CI order (`.github/workflows/gates.yml`, minus the test suites).

Order: G-KERNEL (rebuilt only with `run_kernel`; otherwise the report's freshness is checked), G-NAME
(Stage 7+ dossiers), G-BLUEPRINT, registries, preferences, then the dossier validator. Every gate runs
even after one fails, so the report is complete.

**CLI surface:** `.github/workflows/gates.yml`

## Public Surface

### `GATES`

Constant: `('G-KERNEL', 'G-NAME', 'G-BLUEPRINT', 'registries', 'preferences', 'dossiers')`

### class `GatesReport`

*dataclass*

Results by gate name (`GATES` order); `success` only when every gate that ran passed.
`errors` and `notices` collect every gate's, prefixed with the gate name.

| Field | Type |
|---|---|
| `success` | `bool` |
| `results` | `dict[str, GateResult \| CommandResult]` |
| `errors` | `list[str]` |
| `notices` | `list[str]` |

### `run_gates(*, root=None, run_kernel=False, base=None, conversation=None)`

Returns `GatesReport`.

Run every automated gate.

**Args:**

- `root`: mathAgents checkout.
- `run_kernel`: rebuild and audit the Lean library first (slow); otherwise the existing report must be current and PASS (G-KERNEL fails when it is not).
- `base`: git ref for the dossier validator's append-only checks.
- `conversation`: current conversation id (waiver scope).
