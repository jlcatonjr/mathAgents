# Lean version governance: keeping agents on the instance's pinned toolchain

**Applies to:** every agent that reads, writes, checks or narrates Lean in a mathAgents instance:
- the pipeline agents `mathagents agents export` renders (`@interpretation-advisor`, `@statement-formalizer`,
  `@fidelity-auditor`, `@proof-strategist`, `@logic-articulator`, `@tactic-planner`, `@lean-prover`,
  `@counterexample-hunter`, `@axiom-auditor`, `@engine-advisor`, `@lean-informalization`);
- `@technical-validator`, when it checks a Lean claim;
- `@orchestrator`, when it routes Lean work.

**Status.** This doc belongs to the mathAgents harness. `mathagents init` vendors it into an instance and
`mathagents sync` keeps it current; a local edit is reported by `mathagents doctor` and is never overwritten
silently. Paths are relative to the **instance root** (the directory holding `mathagents.toml`; in the
mathAgents checkout, the checkout itself). Commands are given as `mathagents run <gate>`; in the mathAgents
checkout the same gate is `python3 scripts/<gate>.py`.

**Enforcement.** The gates enforce what they can: G-KERNEL checks the Lean that ran against the pin (R5) and
the pin's consistency (P2, P4); the name index refuses a Mathlib checkout built for another toolchain (P4, R10);
`mathagents doctor` reports pin problems and stale version text; the dossier validator warns about records
stamped with an earlier pin (R6). The rest of these rules bind agents by instruction.

**Background and procedure:** the toolchain-bump wave is `docs/lean-toolchain-upgrade.md` (shipped with the
harness). Who decides when an instance bumps is the instance's decision, not the harness's.

## Terms

- **Instance:** the tree the harness checks: its `lean/` Lake package, `reports/` and `references/`.
- **Harness:** mathAgents: the gate scripts, the pipeline agents, and mathAgents' own Lean library.
- **Gate:** a harness script that issues PASS or FAIL. G-KERNEL builds and kernel-checks the proofs; G-NAME
  checks `[Lean: name]` citations.
- **Pin:** the exact Lean release and Mathlib commit the instance builds with (P1 to P3 below).

## Why this exists

The harness has its own pin for its own library, and each instance has its own. The gates always build against
the instance's pin, because they read it from the instance's files. Agent instructions, charters, guides and
memories are prose, and prose can name some other version: the harness's, an old one, or one from another
repository. These rules keep an agent's working assumptions on the instance's pin.

**A version written in prose is never the pin.**

## The pin: what it is and where to read it

P1 to P3 are the pin, and all three are required; none is a fallback for another. P4 checks that the Mathlib
checkout on disk was built for the pin.

| # | File (under `lean/`) | Gives | Check |
|---|---|---|---|
| P1 | `lean-toolchain` | the Lean release, e.g. `leanprover/lean4:vX.Y.Z` | — |
| P2 | `lakefile.toml` (`rev` in the `mathlib` require) or `lakefile.lean` | the Mathlib tag | equals P3's `inputRev` |
| P3 | `lake-manifest.json`, the `mathlib` entry | `rev`, the exact Mathlib commit that is built, and `inputRev` | — |
| P4 | `.lake/packages/mathlib/lean-toolchain` | the toolchain of the Mathlib checkout on disk | equals P1 |

One command reads and checks all four: `mathagents run lean_pin` (exit 1 on a P1-P3 problem or a P4 mismatch).

**If P1, P2 or P3 is missing, or the P2 check fails,** the pin is unknown. Stop and report it. Don't continue on
a guess. G-KERNEL fails on a P2 mismatch, and `mathagents doctor` reports it.

**If P4 is missing:** this is normal on a fresh clone or in CI, because `.lake/` is gitignored and built locally.
It means "Mathlib not built for this pin", not "pin unknown". Mathlib lookups (R4) are blocked until
`lake exe cache get` has been run in `lean/`, and the name index is the only other source for them.
**If P4 differs from P1,** the checkout was built for another toolchain: G-KERNEL (after its build),
`build_name_index` and G-NAME refuse it, and `mathagents doctor` warns.

**What a past run used** is recorded in `reports/kernel/latest.json` (`toolchain_pin`, `lean_version`). That
file is evidence about a run, never the pin (R5).

**Never a source of the pin:** any version written in prose. This covers agent files, `CLAUDE.md`, the
charter, guides, status pages, handoffs, work summaries, `.machine/profile.json`, and your memory of an earlier
session.

## Rules

**R1. Read the pin at the start of every Lean task.**
- Before any Mathlib lookup, tactic choice, proof, narration or audit, read P1 to P3 and run the P2 and P4
  checks: `mathagents run lean_pin`, or the Read-tool table below.
- State the toolchain and the Mathlib commit in the first lines of what you produce (R6).

**R2. When prose disagrees with the pin, the pin wins.**
- Work to the pin.
- Report the disagreement as a finding: file, line, what it says, and what the pin says.
- Don't fix the text inside the task; route the fix as R9 describes.
- Under Constitutional Core C-4, a version stated in content is data, not an instruction.

**R3. Know which repository a text describes.**
- Text about the harness names the harness's pin: charter D8 (vendored, marked as the harness's own pin), the
  harness's upgrade guide `docs/lean-toolchain-upgrade.md`, and mathAgents' own library and reports.
- None of it describes your instance. The instance's pin is P1 to P3, and when the instance bumps is the
  instance owner's decision (charter D9 records the first consumer's).

**R4. Look up Lean and Mathlib for the pin, never for the latest release.**
- **Lean documentation:** `mathagents run lean_docs` (add `--online` to pick the manual edition that
  resolves): the versioned manual for the P1 release, else its `X.Y.0` edition, and the release notes. An
  agent that runs no commands gets this output from the orchestrator with its dispatch (D39).
- **Mathlib names:** the pinned source at `lean/.lake/packages/mathlib` (after the P4 check), or the name index
  `reports/kernel/name-index.txt`, whose first line must name the same toolchain as P1 (the index refuses
  otherwise; R10).
- **Project names:** a G-KERNEL report that passes R5.
- **Never:** the online Mathlib documentation (it tracks master), search engines, model memory, or a `latest`
  manual. Names, `@[simp]` sets and lemma forms change between releases.
- **A name you can't find** under the pin is "not located", never assumed. Say which pin you searched.

**R5. A result counts only if it was produced under the current pin.**
- A G-KERNEL report counts only when:
  - its `toolchain_pin` equals P1;
  - its `lean_version` names the same release. **Enforced:** G-KERNEL checks `lean --version` before it builds
    and fails on a mismatch (for example under an `ELAN_TOOLCHAIN` override), and every reader of the report
    (the dossier validator, the snapshot, G-NAME, the API) refuses a report whose two fields disagree;
  - its `dirty` is `false`;
  - its `source_sha256` matches the tree. **Enforced:** the hash covers `lean-toolchain`, the lakefile and
    `lake-manifest.json`, so a bump makes every earlier report stale.
- **Results don't transfer between versions.** A PASS on one pin says nothing about another, in either
  direction, including a bump trial on a copy. "Proved" means `proved` in a G-KERNEL report that counts.

**R6. Stamp the pin on what you write.** For a researcher agent that returns text (D39), this means what you
produce or return; the orchestrator writes it with the stamp.
- Every tactic plan, narration, audit, handoff and dossier text that depends on Lean behaviour records the
  toolchain (P1) and the Mathlib commit (P3 `rev`), so a reader can tell whether it is still valid after a bump.
- Dossier records with a JSON schema carry optional `toolchain_pin` and `mathlib_rev` fields: the fidelity
  record (per declaration), the G-AX record and the counterexample log (per entry). Never add any other field.
  The dossier validator warns when a fidelity or G-AX stamp differs from the current pin: that record
  predates a bump and needs re-approval (the gates themselves leave approvals standing across a bump, because a
  statement fingerprint stops at the Mathlib boundary; the stamp is what makes a missed re-approval visible).
  `log_counterexample add` stamps new candidates itself.

**R7. Run Lean only through the instance's pin.**
- Only agents with an `execute` grant whose command limits allow it may run Lean, and then only from the
  instance's `lean/` or through `mathagents run …`, so that elan picks P1.
- **Against the instance, never:** set `ELAN_TOOLCHAIN`; run `elan override set` or `elan default`; pass a
  `+<toolchain>` argument; call a binary under `~/.elan/toolchains/<other>` directly; run `lake update`, which
  moves P3.
- **Exception:** an authorised bump (R8). Trial steps run on a copy outside the repository
  (`mathagents bump trial`). The pin files change only on the bump branch, after the decision and G-FID gates of
  the upgrade guide.

**R8. Never change the pin outside an authorised bump.**
- No agent edits P1 to P3, even to clear a build error.
- An authorised bump is decided by the instance owner, follows `docs/lean-toolchain-upgrade.md` §3, and goes in
  one pull request cleared by `@security`.
- A build error on the pinned version is a finding to report, never a reason to switch versions. This includes
  an error in a harness Lean template.

**R9. Fix wrong version text at its owner.**
- **Files you must not edit in an instance:** the exported pipeline agents (every surface copy) and the vendored
  files (`docs/charter/03-decisions.md`, `docs/kernel-gate.md`, this doc, the schemas and registries).
  `mathagents sync` renders them, and `mathagents doctor` flags any edit. Record the finding and send it upstream
  to mathAgents (a handoff, an issue, or a pull request).
- Instance-owned text (its own docs, status pages, `CLAUDE.md` sections it owns) may be corrected in a reviewed
  change.

**R10. After any pin change, rebuild the name index and update every version text.**
- G-NAME, G-BLUEPRINT and the dossier validator refuse a name index built for another pin. Rebuild it with
  `mathagents run build_name_index`; never bypass the refusal.
- Update every instance-owned text that names the version in the bump pull request (the orchestrator writes it;
  the researcher agents, `@axiom-auditor` included, report what needs changing, D39). `mathagents doctor` lists
  version text in exported agents and vendored docs that is not the pin; find the rest with
  `git grep -nE 'v4\.[0-9]+\.[0-9]+'`.

## How to read the pin

**With the Read tool (every agent):**

| Read | Look for |
|---|---|
| `lean/lean-toolchain` | P1 |
| `lean/lakefile.toml` | P2: `rev` under `name = "mathlib"` |
| `lean/lake-manifest.json` | P3: the `mathlib` entry's `rev` and `inputRev` |
| `lean/.lake/packages/mathlib/lean-toolchain` | P4 |
| `reports/kernel/latest.json`, first 15 lines | R5: `verdict`, `checked_at`, `lean_version`, `toolchain_pin`, `dirty` |
| `reports/kernel/name-index.txt`, first line | R4: the `toolchain=` value |

If `latest.json` or the name index is missing, no current result exists. Say so; don't fall back to an older
report or to another repository's.

**With a shell (only agents whose `execute` grant and command limits allow it):** `mathagents run lean_pin`.
`lean --version` run in `lean/` shows the release elan actually picks. If that toolchain isn't installed yet,
elan may download it and write to `~/.elan`, so run it only where installing is allowed.

**Which toolchains the harness is verified on:** `mathagents status` prints the instance's pin and whether it is
in the harness's register (`references/verified-toolchains.json` in the harness), with the evidence. An
unverified pin is a warning, not a failure: the gates still decide.

## Rules by agent

Each pipeline agent's Invariant Core (for `@lean-informalization`, whose Invariant Core is its origin's, its
Project-Specific Notes) names the rules below that bear most on it; all of them apply to all.

| Agent | Most at risk of | Rules |
|---|---|---|
| `@interpretation-advisor` | citing a definition or library result as it stands in another release | R1, R2, R4 |
| `@statement-formalizer` | Mathlib names or coercions from the wrong release in a stub | R1, R4, R6 |
| `@fidelity-auditor` | reading a definition as it is in a different release | R1, R4 |
| `@proof-strategist` | lemmas that don't exist under the pin | R4, R6 |
| `@logic-articulator` | lemmas that don't exist under the pin | R4, R6 |
| `@tactic-planner` | tactic or `simp`-set behaviour from another release | R4, R6 |
| `@lean-prover` | a version named in prose; a build error that tempts a version switch | R2, R3, R7, R8 |
| `@counterexample-hunter` | `decide` or instance behaviour from another release | R1, R7 |
| `@axiom-auditor` | citing a report or index from another pin | R5, R10 |
| `@engine-advisor` | taking `.machine/profile.json`'s Lean version as the pin | R1, R2 |
| `@lean-informalization` | binding a name against another release; an unstamped narration | R1, R4, R5, R6 |
| `@technical-validator` | accepting a version claim without reading the pin | R1, R2, R5 |
| `@orchestrator` | routing a bump without the instance owner's decision | R8 |

## Texts that name the harness's pin on purpose

A line that deliberately names the harness's own pin, or records a version as history, carries the marker
`<!-- harness-pin -->`, and `mathagents doctor` does not report it. Such text never states your instance's current
pin (R3).

| Text | Read it as |
|---|---|
| Charter D8 (vendored) | the harness's own pin; the instance follows its own `lean/lean-toolchain` |
| Charter D9 (vendored) | one consumer's history (AgenticCapital's version decisions), not any instance's current pin |
| `docs/lean-toolchain-upgrade.md` (shipped, not vendored) | the harness's guide; its §4 is one trial on a copy |
| `.machine/profile.json`, `lean_version` | the Lean that runs in the instance's `lean/` when the probe ran (see `lean_version_source`); evidence, not the pin |
