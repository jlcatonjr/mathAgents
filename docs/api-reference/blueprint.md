# `mathagents.blueprint`

[G-BLUEPRINT](index.md#glossary): leanblueprint `\lean{}` names and `\leanok` markers against the kernel
(DD-42).

With no blueprint in the checkout the gate does not apply, and `check_blueprint` passes with a notice.
CI and Stage 8 assembly behave the same way: each runs the gate only when a blueprint exists. Two cases
fail instead: the bare CLI (`check_blueprint_consistency.py` with no blueprint), and
`check_blueprint(blueprint=...)` naming a directory that does not exist.

**CLI surface:** `scripts/check_blueprint_consistency.py`

## Public Surface

### `check_blueprint(*, root=None, blueprint=None)`

Returns `GateResult`.

Run G-BLUEPRINT on `blueprint` (default: every blueprint `find_blueprints` returns).

**Args:**

- `root`: the checkout or instance root (see [conventions](index.md#conventions)).
- `blueprint`: one blueprint directory to check. A relative path resolves against the current working
  directory, not `root`.

### `find_blueprints(*, root=None)`

Returns `list[Path]`.

Existing blueprint directories among the gate's defaults (`lean/blueprint/`, `blueprint/`).
