# Uniform, grant-scoped surface projection of the pipeline agents

**Status:** implemented on `feat/uniform-surface-projection` (2026-10-05). Released in
mathagents v0.2.2 (operator-run). **Requested by:** baseAgent (operator Jim), after a test there on 2026-10-05.
**Code:** `mathagents/_learned.py`, `mathagents/_surfaces.py`, `mathagents/cli.py`. **Tests:**
`tests/test_learned_blocks.py`, `tests/test_surfaces.py`.

The operator's requirement has two parts:

1. A change projected from one agent architecture to the others must also apply to the mathAgents
   agents, and the feature must apply uniformly.
2. The mathagents module must handle the Goose-surface over-grant remediation itself.

baseAgent found two defects:

- **D1.** The learned-block projection broke mathagents governance.
- **D2.** The non-Copilot surfaces over-grant tools.

## D1: the AGENTTEAMS-LEARNED block and the lock

**Defect.** `agentteams --sync-agent-docs` copies an agent's `<!-- AGENTTEAMS-LEARNED:BEGIN/END -->`
block to all of that agent's surfaces. On a vendored agent this does two things:

- `mathagents sync` and `doctor` saw a hash mismatch and reported "edited since it was vendored".
- A re-render after an upgrade would have overwritten the block.

**Fix.** The lock digest of a pipeline-agent file is the sha256 of its *governed text*: the file minus
its learned block. If the block was appended where agentteams puts it, the one blank separator line in
front of the block is left out too.

`sync` uses the same rule in each place:

- **The `ok` check.** A file whose governed text matches the new render is in sync, and it is left alone.
- **The `conflict` check.** A file whose governed text no longer matches its lock entry is a conflict.
- **`doctor`.** It checks the same digest. It also reports how many agent files carry a block.
- **`update`.** The block from the file on disk is carried into the new render, under `--overwrite` too.
  If the block cannot be carried (it is unsafe, or the new render has no safe place for it), the file is a
  conflict; under `--overwrite` it is replaced and `sync` says the block was dropped. A block is never
  dropped silently.

**Which files.** Only pipeline-agent files get the exclusion:

- `<name>.agent.md` in the export directory;
- `.claude/agents/<name>.md`;
- `.goose/recipes/<name>.yaml`;
- `.codex/agents/<name>.toml`.

Vendored files are still hashed whole, `.md` files included. Lock entries without a block have the
same digest as before, so existing locks stay valid.

**The grammar is agentteams'** (`agentteams/learned_blocks.py`, 1.0.0rc8). It is re-implemented with the
stdlib, because mathagents does not depend on agentteams:

- **markdown:** the markers are whole lines at column 0, in the body. They are never in the front matter
  and never inside an `AGENTTEAMS:BEGIN/END` fence.
- **recipe:** the block goes inside the single `instructions: |` scalar, with the markers at exactly the
  scalar's indent.
- **toml** (mathagents' extension for Codex): the block goes inside `developer_instructions = '''`, with
  the markers at column 0.

`test_the_grammar_matches_agentteams` composes blocks with agentteams' own module and checks that they
are excluded exactly. It runs only where agentteams is importable.

**Fail-closed.** In each of these cases the file has no excludable block, so its digest is that of the
whole file and it reads as an edit:

- unbalanced, duplicated, out-of-order or indented markers;
- a marker that is not a whole line;
- a block in the front matter or inside a template fence;
- a block outside the recipe scalar, or dedented within it;
- block content holding a fence token, a `\r`, or another line-break character.

**What is screened, and what is reported.** The block's content is agent-written and is not
hash-governed, but the agent reads it as part of its own instructions, and anyone can write a block by
hand. So mathagents does not rely on `agentteams --sync-agent-docs` alone (security review 2026-10-05,
conditions C1 and C4):

- **Screened.** The content is checked against agentteams' learned-block policy denylist (copied word for
  word from 1.0.0rc8; `test_the_policy_denylist_matches_agentteams` keeps the copy honest): instruction
  override, identity change, capability lift, constitutional-tier claim, governance bypass and
  permission/tool widening (`@security` rule S-5). A Unicode format character (a bidi control or a
  zero-width character) is refused too. A block that trips the screen is unsafe, so the file reads as an
  edit.
- **Recorded and reported.** The lock records each agent file's block digest under `learned`. `sync`
  and `doctor` report a block added, changed or removed since the lock; `sync --write` records it. The
  report is a notice, not a failure, because changing the block is what `--sync-agent-docs` is for.

**Harness agents' own blocks.** A block in the harness's own copy of an agent holds notes about
mathAgents, not about the consumer, so `render_agent` strips it before export.

## D2: grant-scoped projection to every surface

### Findings (Goose 1.37.0, at `/opt/homebrew/bin/goose`)

All four findings below come from the Goose 1.37.0 source and the installed binary.

1. **The `developer` extension has four tools: `write`, `edit`, `shell` and `tree`.**
   - *Source:* block/goose tag `v1.37.0`, `crates/goose/src/agents/platform_extensions/developer/mod.rs`.
     `get_tools()` lists the four tools, and the unit test `developer_tools_are_flat` asserts exactly
     `["write", "edit", "shell", "tree"]`.
   - *Binary:* each tool's description string occurs in the installed binary (`strings`).
   - *Consequence:* there is **no file-read or search tool apart from `shell`**. The developer
     instructions themselves tell the model to read with `cat`/`sed` and search with `rg` via `shell`.

2. **`available_tools` is honoured on `builtin` and `platform` extensions, at two points.**
   - *Source:* `ExtensionConfig::is_tool_available` (`crates/goose/src/agents/extension.rs`). An empty
     list means *all* tools, so "no tools" has to be expressed by leaving the extension out.
   - *Where it is applied* (`extension_manager.rs`): when the tools are listed (around line 1294) and
     again when a call is dispatched (around line 1659).

3. **A recipe's `extensions:` replaces the user's default extension set.**
   - *Source:* `resolve_extensions_for_new_session` (`crates/goose/src/config/extensions.rs`).
   - *Exception:* the `analyze` extension is added next to `developer` unless the recipe lists it itself.
     This was observed, and the code path that adds it was not located. The scoped recipes always list
     `analyze` explicitly, switched off with `available_tools: [__none__]`. An empty list (`[]`) means "no
     restriction" in Goose 1.37 (agentteams spike, 2026-10-05, cases A1 and A2).

4. **A subagent can only narrow its parent's extensions.**
   - *Source:* summon's `build_task_config` (`summon.rs`). It starts from the parent session's
     extensions, filtered.
   - *Observed:* a subagent of a scoped recipe had the same scoped tool set, without `delegate`.

**Empirical method.** Recipes were run under `goose run --recipe … --no-session` against a local stub
of the OpenAI chat API (`OPENAI_HOST=http://127.0.0.1:<port>`) with an isolated `HOME`. The stub logged
the tool list that Goose sent the model. It then asked for `shell` with `touch PROBE_EXECUTED` in a
scratch directory, to see whether the call ran. `goose recipe validate` accepts any tool name, including
one that does not exist. Validation therefore shows only that the schema is accepted; the stub runs are
the evidence for enforcement. The runs used the first version of the map, in which `read` also granted
`load`; since the security review `load` needs `agent`, so the scoped `fidelity-auditor` now offers only
`analyze` and `tree`, and the subagent row's `load` comes from its `agent` grant only where it has one.

| Recipe | Tools offered to the model | `shell` call |
|---|---|---|
| agentteams 1.0.0rc8 projection of `fidelity-auditor` (`tools: [read, search]`) | analyze, delegate, edit, load, shell, tree, write | **executed** |
| mathagents-scoped `fidelity-auditor` | analyze, load, tree | refused: `-32002: Tool 'shell' not found` |
| mathagents-scoped `proof-strategist` (`read, search, edit, agent`) | analyze, delegate, edit, load, tree, write | refused |
| mathagents-scoped `lean-prover` (all five tools; positive control) | analyze, delegate, edit, load, shell, tree, write | executed |
| `edit`-scoped recipe → `delegate` → subagent calls `shell` | subagent: analyze, edit, load, tree, write | refused |

These runs predate D39 and the conformance commit, so the tool sets in the table (for example
`proof-strategist` with `edit` and `agent`) are historical. Today none of the nine pipeline agents holds `edit`
or `agent`: in a consumer they get `developer` `[tree]` (with `analyze` switched off). In the mathAgents
checkout, under the D41 write-policy pilot (Claude only since D43; the Goose recipes are frozen as the pilot last
rendered them), agentteams itself (#174, 1.0.0rc9) narrows the bespoke agents to
`read` and `search` and renders their recipes in its grant mode, with the workspace-confined `agentteams_readfs`
extension and no `developer` (D42). The four that keep `execute` (statement-formalizer, lean-prover,
counterexample-hunter, axiom-auditor) get no `shell` on Goose either; they return their commands to the
orchestrator.

### The Goose map (`GOOSE_TOOL_MAP`, pinned to 1.37.0)

| `tools:` token | Goose grant |
|---|---|
| `read` | `developer.tree` |
| `search` | `developer.tree` |
| `edit` | `developer.write`, `developer.edit` |
| `execute` | `developer.shell` |
| `agent` | `summon.delegate`, `summon.load` (`load` reads a named recipe, agent or skill into context, possibly from user-global directories; agentteams 1.0.0rc8 wrote the handoffs of the recipes inspected as `load` calls) |

`analyze` is granted to no agent. No Goose 1.37 path tool is confined to the workspace: `tree`, `analyze` and
`shell` all reach any path the user can read. In the recipes scoped through this map, `analyze` is switched
off and `tree` stays the one read capability of a read-only agent; run them under an OS sandbox (the
`exclusive` profile). The recipes agentteams renders load the workspace-confined `agentteams_readfs`
extension instead (`.agentteams/bin/goose-readfs-mcp.py --root .`, tools `read_file`, `list_dir`, `find`,
`grep`, `stat`); the read-only ones among them load no `developer`, so they have no `tree`.

The map fails closed in two ways:

- **Unmappable tool sets are refused.** That covers an unknown token, or a tool set with neither `read`
  nor `search` (every pipeline agent reads, so such a set is malformed and is refused, not guessed at).
- **Renamed tools are lost.** `available_tools` is an allowlist, so a later Goose release that renames a
  tool removes it from the agent; the agent never gains one.

**Known under-grants.**

- An agent without `agent` cannot follow a handoff on Goose: `load` comes only with `agent` (security
  review 2026-10-05, finding 5). Since the conformance commit and D39 no pipeline agent holds `agent`, so
  this affects all nine (statement-formalizer, fidelity-auditor, proof-strategist, logic-articulator,
  tactic-planner, lean-prover, counterexample-hunter, axiom-auditor, engine-advisor), lean-informalization
  and interpretation-advisor, which declares `agent` canonically but loses it to the D41 write-policy
  narrowing (see "The mathAgents checkout" below). They return to the orchestrator, which dispatches the next stage. The
  `load("orchestrator")` handoff text that agentteams still writes into these recipes is dead on Goose
  (reported to agentteams).
- A read-only agent scoped through this map cannot print a file's contents on Goose, because the only
  Goose 1.37 tool that can is `shell` (the agentteams-rendered recipes read files with `agentteams_readfs`
  `read_file`). Options for the scoped recipes, still open:

  - (a) accept this (the current default, which follows POLA);
  - (b) add a read-only stdio MCP filesystem server, with `available_tools` limited to its read and list
    tools (`agentteams_readfs` is one, already loaded by the agentteams-rendered recipes; not yet
    evaluated for the scoped recipes);
  - (c) ask Goose upstream for a `read` tool in `developer`.

**Other recipe keys.** A projected recipe may carry only `version`, `title`, `description`,
`instructions` and `extensions`. Any other top-level key (`retry`, whose checks can run shell commands;
`sub_recipes`; `mcp_servers`; `settings`...) is refused, so nothing outside `available_tools` can act.

### Claude and Codex

- **Claude.** agentteams' `tools:` mapping is already exact:
  - `read` → Read;
  - `search` → Grep, Glob;
  - `edit` → Edit, Write;
  - `execute` → Bash;
  - `agent` → Task.

  mathagents verifies the mapping and refuses a projection that grants more than the declared tools, or
  one with no `tools:` line (that agent would inherit every tool). The front matter may carry only
  `name`, `description` and one `tools` line; a repeated key, or any other (`permissionMode`,
  `mcpServers`, `hooks`, `model`...), is refused.
- **Codex has no per-tool limit.** `sandbox_mode` is the only lever, and it is a declaration, not a ceiling:
  codex-cli 0.160.1 drops it for a spawned agent, and agentteams labels it "not enforced". Since 0.2.8 (D42)
  mathagents takes agentteams' value (`sandbox_mode_for`: `workspace-write` exactly when the agent declares
  `edit`, else `read-only`) and checks it, never rewrites it. It refuses a projection that differs, and any
  TOML key but `name`, `description`, `sandbox_mode` and `developer_instructions` (`approval_policy`,
  `mcp_servers`...). No pipeline agent declares `edit` (D39, D41), so all of them are `read-only`. The
  former `[agents] codex_workspace_write` opt-in is retired and ignored with a notice. Real per-role limits
  on Codex come from the launcher and, under agentteams' pilot, its role gate. `lake build` writes
  `lean/.lake/` and G-KERNEL writes `reports/kernel/`, so a read-only sandbox may stop them on Codex (not
  verified); the agent then returns the command to the orchestrator, which runs it (D39).
- **`execute` is still a write path on Claude and Goose.** Claude's `Bash` and Goose's `developer.shell`
  are general shells. For the researcher agents (D39), "commands check, never author" is enforced there
  by the agents' instructions and by the orchestrator, which alone writes; only Codex `read-only`
  enforces it in the sandbox.

### How it is wired

`[agents] surfaces = ["claude", "goose", "codex"]` in `mathagents.toml` turns the projection on.
`export_to` must be `<repo>/.github/agents`. On every `sync` (and on `agents export` without `--to`),
mathagents does the following:

1. It renders the Copilot agents as before.
2. It runs `agentteams --interop-from <renders> --framework <surface>` in a temporary directory. The
   executable comes from `MATHAGENTS_AGENTTEAMS`, else `agentteams` on PATH.
3. It scopes each result: Goose `extensions:` is replaced; Claude is checked; Codex is checked and, where
   needed, narrowed, as above.
4. It computes every projection before writing any agent or surface file. If agentteams is missing or
   fails, or a surface cannot be scoped, sync stops with exit 1 and writes no agent or surface file and no
   lock. Vendored contract files are refreshed before the agents, so with `--write` they may already have
   been updated; the lock is not saved, so the next run reports them and still fails closed.
5. It writes each surface file through the same lock as the Copilot file. The D1 learned-block rule
   therefore covers all four surfaces in the same way.
6. It records `surfaces`, the agentteams version, the Goose map version and the Codex opt-ins in the
   lock. `doctor` prints them.

`doctor` itself never needs agentteams; it only compares digests, so it is safe in CI. Removing a
surface from the list untracks its lock entries and leaves the files in place.

**The mathAgents checkout.** Step 2 of `scripts/refresh_agent_surfaces.sh` passes `--description brief.json`
to `agentteams --interop-from`, so agentteams (#174, 1.0.0rc9) applies the brief's write policy to the bespoke
agents (D42). Under the pilot their recipes come out in agentteams' grant mode, and step 3b checks them with
agentteams' own audit (`scripts/lib/check_bespoke_goose.py`; since D43 the switch excludes goose and the recipes are
frozen, so step 3b's scoping output is discarded with the rest of the Goose render: the `AR_GOOSE_*` grant checks, `AR_WRITE_POLICY`,
and the readfs server byte for byte against the copy agentteams ships). With the pilot off for Goose, step 3b
scopes them with `python3 -m mathagents._surfaces scope-goose` instead, which only narrows; each recipe is
replaced atomically, and none is written unless all of them scope.

## The root fix belongs in agentteams (upstream request)

agentteams' interop gives **every** Goose recipe the whole `developer` extension, whatever its `tools:`
says. It also gives `summon` to the agents that have handoffs. That was observed, not read in the code:
`engine-advisor`, which has no handoffs, got no `summon`. This applies to every agentteams team, not only to the
mathAgents agents; baseAgent's own Goose roster is affected in the same way. Requested of agentteams:

1. In the Goose emitter, derive `extensions` and `available_tools` from the canonical `tools:`, using a
   map pinned to a Goose version (the table above). Verify it with the stub-model method; agentteams'
   existing recipe validation cannot catch a wrong tool name.
2. Make `--sync-agent-docs`, `--update --merge` and `materialize --adopt-orphans` keep that scoping. They
   must never re-widen a recipe.
3. For Codex, document that `workspace-write` cannot withhold `execute`. Consider a structured warning
   in the generated TOML.

Once agentteams does this, mathagents' Goose rewrite becomes a no-op check, and it should be kept as a
check.

## Open verification items

- How Goose adds `analyze` next to `developer`. The behaviour was observed and the code was not found;
  the scoped recipes list `analyze` explicitly, so the outcome is deterministic either way.
- Delegation from a Goose session that has no session record. summon falls back to the global default
  extensions (`extensions_or_default`). The `--no-session` run above inherited the scoped set, but other
  entry points (desktop, `goose session`) were not tested.
- Codex `read-only` and `workspace-write` semantics (Codex is not installed here).
- Goose releases after 1.37.0. Re-run the stub-model probe and bump `GOOSE_MAP_VERSION`.
- The Goose findings and the stub-model runs above are recorded here as prose only; no probe script or
  log is committed (conflict audit 2026-10-05, finding 6). Re-running them is the way to re-verify.
