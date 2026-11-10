# Contributing to mathAgents: branches, releases and contributions

The binding rules are in [`docs/release-policy.md`](release-policy.md) and [`docs/release-checklist.md`](release-checklist.md); this guide explains how to work within them. agentteams, researchteam, mathAgents and baseAgent all follow the same model, so what you learn here applies to all four.

mathAgents is licensed under Apache-2.0 (see [`LICENSE`](../LICENSE) and [`NOTICE`](../NOTICE)). By submitting a contribution you agree that it is licensed under the same terms.

## The model in brief

- **`main`** is where development happens. Every change, fixes included, lands there first, through a pull request.
- **Releases are signed tags,** and they are what users install and pin.
- **`release/1.<n>`** collects the reviewed fixes for the next patch release of a maintained line. It changes only when the maintainer copies in a fix that is already on `main` (a *backport*). Between tags its commits are unsigned, so it is not for installing or pinning. A line is cut from a tag on demand (`STABILITY.md`).
- **Each patch tag is cut on its release line** and signed by the maintainer. After each tag, the release line is merged back into `main`.

## Branches and tags

| Ref | What it is | Who changes it |
|---|---|---|
| `main` | Development, the next minor version | Anyone, through a pull request |
| `release/1.<n>` | Reviewed fixes queued for the next patch release; unsigned between tags; not for pinning | The maintainer only, by backport |
| `vX.Y.Z`, `vX.Y.Z-rc.N` | One exact release, signed by the maintainer, never moved; what you install and pin | The maintainer only |
| Your work branch (`feat/…`, `fix/…`, `docs/…`, `chore/…`) | One change, deleted after merge | Its author |

The name `release/<X.Y>` is reserved for maintained lines. Never create a `release/*` branch, locally or on GitHub.

## Using mathAgents

Install a signed release tag. The repository is public, so no SSH key, token or deploy key is needed.

```bash
pip install "mathagents @ git+https://github.com/jlcatonjr/mathAgents.git@<tag>"
```

**Verified install,** for a governed team, an experiment or a paper. Clone the tag into a directory of its own, check its signature with repository config neutralised, then install from that checkout:

```bash
git clone --branch <tag> https://github.com/jlcatonjr/mathAgents.git mathAgents-<tag>
cd mathAgents-<tag>
git -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
    -c gpg.ssh.allowedSignersFile=$HOME/.config/agentteams/allowed_signers \
    -c gpg.program=/usr/bin/gpg -c core.fsmonitor=false -c core.hooksPath=/dev/null \
    tag -v <tag> && pip install .
```

The `&&` stops the install if the signature check fails. The output must also show the release key's full fingerprint, which begins `SHA256:IPdnLwlF`, not just "Good signature"; if it doesn't, stop and uninstall. "Verifying a release" below explains how to set up `allowed_signers` once. For a patch release, repeat this with the new tag in a new directory.

[`module.md`](module.md) covers the Lean and Mathlib requirements.

**A release branch is not an install source.** It holds reviewed fixes queued for the next patch release. Those commits are unsigned between tags, so don't install from the branch or pin it.

**For development,** clone the repository (or your fork) with `git clone https://github.com/jlcatonjr/mathAgents.git`, stay on `main`, and install it with `pip install -e .`.

**Pins between repositories** (`toolchain.lock`, pinned extras) always name the commit of a verified signed tag, never a branch.

## Contributing a change

If you don't have write access, work from a fork. People with write access may push their branch to this repository instead.

1. **Start from an up-to-date `main`:** `git switch main && git pull --ff-only` (in a fork, sync it with `jlcatonjr/mathAgents` `main` first).
2. **Branch:** `git switch -c fix/<short-topic>`. Use `feat/`, `fix/`, `docs/` or `chore/`. Keep one change per branch. Always branch from `main`, never from `release/*`.
3. **Commit and push your branch** with `git push -u origin fix/<short-topic>`, **then open a pull request against `jlcatonjr/mathAgents` `main`.** If GitHub proposes a release branch as the base, change it to `main`.
4. **CI.** `gates.yml` runs the kernel, fidelity, naming and blueprint gates. It runs only when a pull request touches the paths it watches: `lean/`, `mathagents/`, `scripts/`, `tests/`, `references/`, the agent folders, `pyproject.toml`, `toolchain.lock` and a few others. A prose-only change under `docs/` starts no gate checks. **On a pull request from a fork, the workflows wait until a maintainer approves them**, so expect a delay before checks appear. The long suites (`long-suites`, over an hour) run only when your change touches what they test (`scripts/ci_long_suite_inputs.txt`); when they run, wait for them. If CI is down rather than failing, don't merge: ask the maintainer.
5. **Merge.** A maintainer merges once the checks that ran are green. Contributors with write access may merge their own pull request into `main` under the same condition. A pull request that changes code or Lean files and shows no checks is not merged until the checks have run.
6. **Delete your branch after it merges.**

## Getting a fix into a release

1. **Land the fix on `main` first,** as above.
2. **Ask for a backport.** On the merged pull request, add the label `needs-backport`. If you can't add labels, leave a comment instead: "please backport". Either way, say why. Only these qualify:
   - security fixes;
   - correctness fixes;
   - documentation fixes.

   New features wait for the next minor release.
3. **The maintainer does the rest:** copies the fix to the release line in a separate pull request, using `git cherry-pick -x` and never a squash, and at release time signs the patch tag.
4. **Urgent?** Say so in the pull request. Report security issues privately, through GitHub's private vulnerability reporting for this repository (the "Security" tab), not in a public issue.

## What only the maintainer does

- Pushing or merging to any `release/*` branch.
- Creating a `release/*` branch.
- Creating, moving or deleting tags.
- Signing a release.
- Moving a cross-repository pin.
- Signed decision rows and the security-decision logs.
- Re-enabling autosync.

If you work through this repository's agent team (Claude, Copilot, Codex or Goose), the agents will stop and ask before any of these actions. In your own session they are asking *you*: answer no, and open an issue instead.

## Please don't

- Commit straight to `main` or `release/*`. Use a branch and a pull request.
- Force-push `main` or `release/*`, or delete or move a tag. A defect is fixed forward, in a new patch release.
- Put a branch name into `toolchain.lock` or a pinned extra.

## Enforcement

On GitHub, branch protection on `main` and `release/*` and tag protection refuse pushes to release branches, and the moving or deleting of tags, by anyone but the maintainer. The rules above still apply where that protection does not reach.

## How a release happens

You only need this for context:

1. **Fixes accumulate.** They land on `main`, and the ones requested for backport are copied to the release line.
2. **The maintainer releases:** bumps the version on the release line in a pull request, signs `vX.Y.Z` locally, publishes the GitHub release, and merges the release line forward into `main`.
3. **Repositories release in order:** agentteams → researchteam → mathAgents → baseAgent. Each one moves its pins only after verifying the upstream tag's signature.

## Verifying a release

Each tag is SSH-signed with the maintainer's release key. Its fingerprint begins `SHA256:IPdnLwlF`. The full fingerprint and the `allowed_signers` line are in agentteams `SECURITY.md`, under "Release signers". Read them on GitHub, not from a copy inside the repository you are checking.

1. On your own machine, add that line to your own `~/.config/agentteams/allowed_signers`. (Agents never write this file; it's yours.)
2. Run this from a checkout of the tag (the verified install above does this for you):

   ```bash
   git -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
       -c gpg.ssh.allowedSignersFile=$HOME/.config/agentteams/allowed_signers \
       -c gpg.program=/usr/bin/gpg -c core.fsmonitor=false -c core.hooksPath=/dev/null \
       tag -v <tag>
   ```

3. Check that the output shows the full fingerprint from agentteams `SECURITY.md`, not just "Good signature".

## Notes for mathAgents

- **Pins.** `toolchain.lock` pins agentteams and researchteam to the commits of verified tags. Only the maintainer moves them, and the Lean toolchain moves only through `mathagents bump`.
- **Downstream.** baseAgent consumes mathAgents through its `proofs` extra, pinned to a verified tag's commit.
- **Autosync** runs only when the maintainer dispatches it, until the maintainer resumes its schedule.
- **Decisions.** Charter decisions (D1, D2, …) cited in code and docs are summarised in [`charter/decisions-summary.md`](charter/decisions-summary.md).

## Questions

Open an issue on GitHub.
