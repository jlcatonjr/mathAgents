# `mathagents.machine`

This machine's hardware and installed engines (`.machine/profile.json`, never committed).

`@engine-advisor` joins the profile with the prover-engine registry to decide what it may offer.

**CLI surface:** `scripts/probe_machine.py`

## Public Surface

### class `MachineProbe`

*dataclass*

Outcome of `probe_machine`: the profile it wrote, or the reason it failed.

| Field | Type |
|---|---|
| `success` | `bool` |
| `profile` | `dict \| None` |
| `errors` | `list[str]` |
| `notices` | `list[str]` |

### `probe_machine(*, root=None)`

Returns `MachineProbe`.

Probe the machine and (re)write `.machine/profile.json` (machine-local; no dry run: the probe is
the write).

### `read_machine_profile(*, root=None)`

Returns `dict | None`.

The last probed profile, or None when this machine has not been probed.
