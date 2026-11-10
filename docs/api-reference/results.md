# `mathagents.results`

Result types shared by the mathagents API.

Every gate or command returns one of these instead of printing or exiting: `success` is the verdict,
`errors` the findings (complete sentences, as the gate scripts print them after `FAIL`), and
`notices` the non-blocking remarks.

## Public Surface

### class `CommandResult`

*dataclass*

Outcome of a gate script the API runs as a subprocess (G-KERNEL, the name index, registries...).

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
