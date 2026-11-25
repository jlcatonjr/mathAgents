# `mathagents.results`

Result types shared by the mathagents API.

Every gate or command returns one of these instead of printing or exiting: `success` is the verdict,
`errors` the findings (complete sentences, as the gate scripts print them after `FAIL`), and
`notices` the non-blocking remarks.

Decision IDs, gate codes and terms are defined in the [glossary](index.md#glossary).

**CLI surface:** none.

## Public Surface

### class `CommandResult`

*dataclass*

Outcome of a gate script the API runs as a subprocess: `run_kernel_gate` (G-KERNEL),
`build_name_index`, `validate_registries`, `validate_evidence` and `validate_claim_ledger`.
`probe_machine` runs one too but returns its own `MachineProbe`.

| Field | Type |
|---|---|
| `command` | `list[str]` |
| `returncode` | `int` |
| `success` | `bool` |
| `output` | `str` |
| `errors` | `list[str]` |
| `notices` | `list[str]` |

### class `GateResult`

*dataclass*

Outcome of one automated gate run in-process (fail-closed: any finding means `success` False).

| Field | Type |
|---|---|
| `gate` | `str` |
| `success` | `bool` |
| `checked` | `list[str]` |
| `errors` | `list[str]` |
| `notices` | `list[str]` |
