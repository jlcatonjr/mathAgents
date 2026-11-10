# Stability policy

`mathagents` 1.0.0 is built on agentteams 1.0 final (decision D43). From **1.0.0** the project follows
[Semantic Versioning 2.0.0](https://semver.org/). This page states what that contract covers. The 0.x rules at the end
applied before 1.0.0.

## What SemVer covers from 1.0.0

A change is **breaking** (a major release) if it removes, renames or changes the meaning of any of these.

### 1. The `mathagents` command line
- The subcommands `run`, `init`, `sync`, `agents export`, `status`, `bump` and `doctor`, and their documented flags
  (`docs/api-reference/cli.md`).
- The exit codes: 0 done or in sync, 1 findings, 2 usage error, 3 switched off on this machine. `status` keeps its
  exit-code meaning; the lines it adds (such as the Lean pin) never change it.

### 2. The Python API
- The modules and symbols documented in `docs/api-reference/`, and nothing else. Covered: function names, keyword
  parameters and their order, result and record field names, and the exception hierarchy.
- The **DD-29 boundary**: the API writes no human approval or verdict (G-FID approvals, G-CX verdicts, G-AX
  approvals). Narrowing that boundary is never a breaking change; widening it is not permitted.
- `scripts/check_api_doc_parity.py` and `tests/test_api_doc_*.py` keep the pages and the code in step.

### 3. Instance files
- `mathagents.toml` (the instance marker and its documented keys) and `mathagents.lock.json` (its fields).
- Adding an optional key is minor. Removing or renaming a key, or changing a key's meaning, is major.

### 4. Schemas and dossier records
- The JSON schemas in `references/schemas/` (counterexample log, fidelity record, G-AX record, object logics,
  prover engines). Additive changes (a new optional field; a new enum value readers are expected to pass through)
  are minor. Removing a required field, changing a type or narrowing an enum is major.
- The dossier record grammar: the `Result status:` line and its values (`open`, `conjectured`, `proved`,
  `proved, fidelity-waived`, `refuted (<decl>)`, `refuted, verdict-waived (<decl>)`), the append-only
  `counterexamples.json`, and the G-FID and G-CX record fields.

### 5. Proved Lean declaration names
- A declaration in the `MathAgents.*` namespace that the G-KERNEL report shows `proved` keeps its name through 1.x:
  dossiers and blueprints cite it as `[Lean: Namespace.name]`. Renaming or removing one is major.
- `MathAgentsWIP.*` is internal and may change in any release.
- The `MathAgents` Lake package is **not** a dependency target for other Lean projects; requiring it from another
  package is unsupported.

### 6. The Lean toolchain, by contract
- **Major:** dropping a toolchain from `references/verified-toolchains.json`, or changing the lakefile rules an
  instance must follow (`docs/module.md`).
- **Minor:** moving the harness's own pin (`lean/lean-toolchain`, the Mathlib `rev`), or adding a verified toolchain.
- **Outside SemVer:** proof results. A toolchain move can lapse a G-FID approval (statement drift); that is reported
  by `mathagents bump statement-drift` and the dossier validator, not encoded in the version number. Instances own
  their own Lean pins, behind the consumer decision gate in `docs/lean-toolchain-upgrade.md`.

### 7. agentteams
- Each release records the agentteams it renders with in `toolchain.lock` and in its CHANGELOG toolchain block.
- mathagents 1.x supports agentteams 1.x. Raising the minimum supported agentteams minor is a minor release.
  Requiring agentteams 2.x is a major release.

## What SemVer does not cover

These may change in any release:
- the wording of agent prose, gate `errors` and `notices`, and other human-readable output (they quote the gate
  scripts), and the order of findings;
- undocumented modules (any name starting with `_`) and the `scripts/` internals the API calls;
- the generated agent files' internal phrasing (their existence and declared `tools:` are governed by the charter
  decisions, not by SemVer);
- `tmp/`, `docs/reports/`, `workSummaries/`, the test fixtures, and the security-decision log layout (agentteams'
  format);
- the documentation site: its pages, the generated CLI reference (the CLI's behaviour is documented in
  `docs/api-reference/cli.md`), and the explorer's data files `api.json` and `library.json`, whose `schema` field
  versions them for the explorer alone.

## Deprecation

A deprecated symbol, flag or key:
1. lands in a minor release;
2. emits a `DeprecationWarning` (`warnings.warn(..., stacklevel=2)`) or a CLI notice when used;
3. is listed in that release's CHANGELOG section with its planned removal;
4. survives at least one full minor cycle.

Its removal is a major release, unless the change closes a gate hole: a gate that let an unproved result, an
unapproved statement or an unapproved axiom through may be closed in a minor or patch release.

## Release lines

- **Public repository (D45):** from the public release, this repository is canonical. Its first signed tag,
  `v1.1.0`, continues the 1.x line: `release/1.1` is cut from the public `main` for it, the tag is signed on that
  branch, and `release/1.1` then takes backports only (`1.1.N`) while `main` moves to the next `.dev0`. A later line
  `release/1.<n>` is cut the same way. The
  earlier `release/1.0` and `release/v0.2.8-agentteams-conformance` branches and tags `v0.x` through `v1.0.1`
  remain in the archived private repository.
- **1.x (before the public release):** `release/1.0` was the maintained 1.x line. It was cut at `1.0.0rc1`, on agentteams' release candidate (D43). From the cut it takes backports
  only (cherry-picks of fixes already merged to `main`), and under the freeze `main` takes fixes only as well. `v1.0.0` is tagged on that
  branch once it renders with agentteams `v1.0.0`; `main` then moves to `1.1.0.dev0` and reopens for features. Patch releases (`1.0.x`) carry fixes only: no new
  public surface and no behaviour change for any documented input.
- **0.2.8:** `release/v0.2.8-agentteams-conformance` folded into the 1.0 line without a tag (D43).
- **0.x:** only the latest minor receives fixes. `v0.2.7` is the last 0.x release; if an instance pinned to it needs
  a fix before it can move, a `release/0.2` branch is cut from `v0.2.7` on demand.
- Tags are SSH-signed by the operator (`scripts/operator/tag-release.sh`), from a plain terminal, never from an agent
  session, and verified against `~/.config/agentteams/allowed_signers`. Tags are immutable. The release policy,
  shared with agentteams, researchteam and baseAgent, is [`docs/release-policy.md`](docs/release-policy.md); the
  procedure is `docs/release-checklist.md`.

## Reporting

A documented behaviour that changed silently across a minor release, or an undocumented internal that became
load-bearing, is a stability issue: file it at <https://github.com/jlcatonjr/mathAgents/issues>.
