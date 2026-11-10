# `mathagents.preferences`

Project and dossier preferences (charter D32): every operator decision as a reversible setting.

Each setting has a `choice`, its `alternatives` and the charter `decision` that recorded it, in
`references/preferences.toml` (project defaults) and `reports/dossiers/<slug>/preferences.toml`.
Writers check the result and leave nothing behind on a dry run: a dry run executes the real writer on
a scratch copy of the files it reads.

`set_preference` refuses `gax.*` and `fidelity.*` settings: those record the operator's G-AX
answers and kernel-as-judge policy, which are human decisions (DD-29). The operator changes them with
`scripts/preferences.py set` in a terminal.

**CLI surface:** `scripts/preferences.py`

## Public Surface

### `OPERATOR_ONLY_PREFIXES`

Constant: `('gax.', 'fidelity.')`

### class `Preference`

*frozen dataclass*

A setting in force for a dossier. `enforcement` is `enforced` (checked mechanically) or
`advisory` (followed by agents, checked at the human G-FID review).

| Field | Type |
|---|---|
| `key` | `str` |
| `choice` | `object` |
| `source` | `str` |
| `enforcement` | `str` |
| `alternatives` | `tuple` |
| `decision` | `str \| None` |

### class `PreferenceChange`

*dataclass*

Outcome of `set_preference` or `create_dossier`.

| Field | Type |
|---|---|
| `success` | `bool` |
| `target` | `str` |
| `dry_run` | `bool` |
| `written` | `list[str]` |
| `errors` | `list[str]` |
| `notices` | `list[str]` |

### class `Reading`

*frozen dataclass*

A reading of the dossier's Interpretation Brief (`## R2. title`).

| Field | Type |
|---|---|
| `id` | `str` |
| `title` | `str` |

### `check_preferences(*, root=None)`

Returns `GateResult`.

Check the project file and every dossier's preferences.toml (`preferences.py check`).

### `create_dossier(*, root=None, slug, domain, readings=(), dry_run=False)`

Returns `PreferenceChange`.

Start a dossier at intake: its preferences.toml (from the project defaults) and a problem-card
skeleton. Never overwrites an existing file.

**Args:**

- `root`: mathAgents checkout.
- `slug`: new dossier slug.
- `domain`: a D2 domain from the prover-engine registry.
- `readings`: selected readings of the Interpretation Brief, if one exists.
- `dry_run`: run on a scratch copy; the checkout is not touched.

**Raises:**

- `ValueError`: invalid slug.

### `effective_preferences(*, root=None, slug)`

Returns `dict[str, Preference]`.

The settings in force for `slug`: the dossier's own, else the project default.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier, or no references/preferences.toml.

### `intake_digest(*, root=None, slug)`

Returns `str`.

The `intake_sha256` a G-FID approval binds (problem-card.md + preferences.toml).

### `list_readings(*, root=None, slug)`

Returns `list[Reading]`.

The readings of the dossier's Interpretation Brief (empty when it has none).

### `set_preference(*, root=None, target, key, value, dry_run=False)`

Returns `PreferenceChange`.

Change one setting: `value` becomes the choice and the old choice joins the alternatives.
The result is checked and the file restored if any preference check fails.

**Args:**

- `root`: mathAgents checkout.
- `target`: `project` or a dossier slug.
- `key`: dotted setting key, e.g. `readings.selected`.
- `value`: the new choice (a string or a list of strings).
- `dry_run`: apply to a scratch copy and report; the checkout is not touched.

**Raises:**

- `ValueError`: invalid target, or an operator-only key (`gax.*`, `fidelity.*`).
