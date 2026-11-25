# `mathagents.preferences`

Project and dossier [preferences](index.md#glossary) (charter D32): every operator decision as a
reversible setting.

Each setting has a `choice`, its `alternatives` and the charter `decision` that recorded it, in
`references/preferences.toml` (project defaults) and `reports/dossiers/<slug>/preferences.toml`.
After writing, each writer runs the preference checks on the result. A dry run executes the real writer
on a scratch copy of the files it reads, so the checkout is never touched.

`set_preference` refuses `gax.*` and `fidelity.*` settings: those record the operator's G-AX answers and
kernel-as-judge policy, which the operator changes with `scripts/preferences.py set` in a terminal (see
[the human-decision boundary](index.md#the-human-decision-boundary-dd-29)).

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

**Raises:**

- `FileNotFoundError`: there is no decision charter to check settings against
  (`docs/charter/decisions-summary.md` or `docs/charter/03-decisions.md`).

### `create_dossier(*, root=None, slug, domain, readings=(), dry_run=False)`

Returns `PreferenceChange`.

Start a dossier at intake: its preferences.toml (from the project defaults) and a problem-card
skeleton. Never overwrites an existing file; an existing one is a refusal (`success` False).

A real run creates the dossier directory. If the files it writes then fail the preference checks, they
stay on disk and the result is `success` False with a notice to fix them (unlike `set_preference`,
which restores the file).

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `slug`: new dossier slug.
- `domain`: a D2 domain from the prover-engine registry.
- `readings`: selected readings of the [Interpretation Brief](index.md#glossary), if one exists (a list,
  not a single string).
- `dry_run`: run on a scratch copy; the checkout is not touched.

**Raises:**

- `ValueError`: invalid slug.
- `TypeError`: `readings` is a single string.
- `FileNotFoundError`: no `references/preferences.toml`.
- `KeyError`: the project file lacks a default the new dossier needs.

### `effective_preferences(*, root=None, slug)`

Returns `dict[str, Preference]`.

The settings in force for `slug`: the dossier's own, else the project default.

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier, or no references/preferences.toml.

### `intake_digest(*, root=None, slug)`

Returns `str`.

The `intake_sha256` a G-FID approval binds (problem-card.md + preferences.toml).

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.

### `list_readings(*, root=None, slug)`

Returns `list[Reading]`.

The readings of the dossier's Interpretation Brief (empty when it has none).

**Raises:**

- `ValueError`: invalid slug.
- `FileNotFoundError`: no such dossier.

### `set_preference(*, root=None, target, key, value, dry_run=False)`

Returns `PreferenceChange`.

Change one setting: `value` becomes the choice and the old choice joins the alternatives.
The result is checked and the file restored if any preference check fails.

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `target`: `project` or a dossier slug.
- `key`: dotted setting key, e.g. `readings.selected`.
- `value`: the new choice (a string or a list of strings).
- `dry_run`: apply to a scratch copy and report; the checkout is not touched.

**Raises:**

- `ValueError`: invalid target, or an operator-only key (`gax.*`, `fidelity.*`).
