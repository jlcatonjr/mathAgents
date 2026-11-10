# `mathagents.blueprint`

G-BLUEPRINT: leanblueprint `\lean{}` names and `\leanok` markers against the kernel (DD-42).

With no blueprint in the checkout the gate does not apply and passes with a notice, as in CI and at
Stage 8 assembly (both run it only when a blueprint exists). The bare CLI
(`check_blueprint_consistency.py` with no blueprint) fails instead; `check_blueprint(blueprint=...)`
on a missing directory fails the same way.

**CLI surface:** `scripts/check_blueprint_consistency.py`

## Public Surface

### `check_blueprint(*, root=None, blueprint=None)`

Returns `GateResult`.

Run G-BLUEPRINT on `blueprint` (default: every blueprint `find_blueprints` returns).

### `find_blueprints(*, root=None)`

Returns `list[Path]`.

Existing blueprint directories among the gate's defaults (`lean/blueprint/`, `blueprint/`).
