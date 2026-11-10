# Release checklist

How a `mathagents` release is made. The release policy is [`release-policy.md`](release-policy.md) (the shared
1.0 policy; it wins over this checklist where they differ), the version contract is [`STABILITY.md`](../STABILITY.md), and the history is
[`CHANGELOG.md`](../CHANGELOG.md). Every step that pushes, merges, tags or overwrites carries its own `@security`
row in the three security-decision logs before it runs (constitutional rule C-5).

## Every release

1. **Pick the line.** Every release is tagged on its release branch (`tag-release.sh` refuses anything else): a new
   minor line is first cut from `main` as `release/X.Y`. A fix lands on `main` first; a `1.0.x` fix is then a regular
   merge or a `git cherry-pick -x` PR to `release/1.0` (never a squash): label it
   `backport-1.0` (a collaborator's request for one is the label `needs-backport-1.0` on the merged `main` PR), link the `main` PR, and include fixes only (security, correctness, documentation).
2. **Toolchain.** `toolchain.lock` names the agentteams and researchteam commits the release renders with: for 1.x,
   the peeled commits of verified signed agentteams and researchteam tags (`release-policy.md` §3). Moving it is an `@security` row; then run
   `bash scripts/refresh_agent_surfaces.sh` under its overwrite clearance. `scripts/lib/agentteams_provenance.py`
   refuses a render on any other agentteams. The Lean pin moves only through `mathagents bump`
   (`docs/lean-toolchain-upgrade.md`).
3. **Version.** Set `pyproject.toml` to the release version (`1.0.0rc1`, `1.0.0`, `1.0.1`, …).
4. **CHANGELOG.** Move `[Unreleased]` into a dated `[x.y.z]` section, ending with its **Toolchain** block: agentteams
   (tag and peeled commit), researchteam (tag and peeled commit), Lean, Mathlib. Add the compare link.
5. **Gates and suites.** On the release commit, all of these must pass:
   - CI `gates.yml`: G-KERNEL, G-FID, G-CX, registries, G-NAME, G-BLUEPRINT, and `long-suites` (the push to the
     release line forces it; `tag-release.sh` refuses a commit without it; D46);
   - the full `pytest` suite, with 0 skipped for the review suites;
   - `bash scripts/claude_researchteam_bridge.sh validate`;
   - `agentteams --check-wiring --framework claude` where the write policy is on.
6. **Merge.** PR into the release line, green CI, `@code-hygiene`, `@conflict-auditor`, then the `@security` merge row.
   The operator merges and signs in one run with `scripts/operator/release-merge-and-sign.sh` (plain terminal,
   `/bin/bash -p`): a regular merge at the reviewed head, checked in a fresh clone, then step 7's signer on that merge
   commit, taken from the merge commit and matching the sha256 the operator computed from `origin/release/X.Y`. The
   release PR may not change `tag-release.sh`. Without the wrapper: merge with a regular merge (never a squash) and
   push normally (no force), then step 7.
7. **Tag.** Sign from a plain terminal, never from an agent session:
   `TAGGER_EMAIL=<e-mail> scripts/operator/tag-release.sh <40-hex merge commit> <ssh-signing-key>`, where the commit
   is the head of the release branch right after the release merge, and its version differs from its first parent's.
   The script works only in a fresh clone of the fixed URL (never the working checkout, whose `.git/config` agents
   can write), with global and system git config and every `GIT_*` variable dropped. It refuses unless the key is
   the pinned release key (it signs the 1.0 and 1.1 lines) and `~/.config/agentteams/allowed_signers` holds it, verifies with the neutralised
   command from agentteams SECURITY.md before pushing, and asks y/N before tagging and again before pushing. Tags
   are immutable: never move or delete one; fix forward.
8. **Merge forward.** After the tag, merge `release/X.Y` forward into `main` (a regular merge, under its `@security` row;
   the operator merges the session-prepared PR with `scripts/operator/merge-forward.sh`, `NEXT_DEV` set after `vX.Y.0`),
   so `main` contains every tagged commit. After `vX.Y.0`, `main` moves to the next minor's dev version
   (`1.1.0.dev0`). Any backport to a release line means a new signed RC and another soak before the final tag.
9. **Handoff.** Send baseAgent (and any other instance) the pin-move handoff:
   - the tag, its tag object and its peeled commit;
   - the agentteams render commit;
   - the exact argv of any researcher command that changed;
   - a `scope_goose` re-check against their recipes;
   - the codex-cli version.

## The 1.0 cut (once)

This follows [`release-policy.md`](release-policy.md) §6: the joint cut, in the order agentteams → researchteam →
mathAgents → baseAgent, with Phase R (RC and joint soak) and Phase T (same-day tags). Its steps and operator
actions are listed there. Before Phase R, the operator installs `~/.config/agentteams/allowed_signers` and proves
`git tag -v v1.0.0-rc.9` on agentteams with the neutralised command (agentteams SECURITY.md, Release signers).
