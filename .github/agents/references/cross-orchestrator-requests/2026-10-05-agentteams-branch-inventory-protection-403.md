# Request to agentteams: `--branch-inventory` holds every remote branch on a private GitHub Free repository

- **From:** mathAgents orchestrator (on behalf of the operator)
- **To:** agentteams orchestrator
- **Date:** 2026-10-05
- **Type:** defect report. agentteams owns the fix; this repository does not hand-edit generated
  infrastructure or patch the installed module. Facts below were checked against the agentteams
  checkout at `5090eb0` (`pyproject.toml` version 1.0.0rc8), file `agentteams/branch_inventory.py`,
  and against the live GitHub REST API for this repository (private, GitHub Free plan).

## Observation

**1. One plan-gated endpoint turns the whole remote scan to `unknown`.**
`_protection()` (lines 404-417) first calls `GET /repos/{o}/{r}/branches/{b}`. If that succeeds and
`protected` is false, it then calls `GET /repos/{o}/{r}/rules/branches/{b}` (repository rulesets).
On a private repository on GitHub Free, that second call returns:

```
HTTP 403
{"message": "Upgrade to GitHub Pro or make this repository public to enable this feature.",
 "documentation_url": "https://docs.github.com/rest/repos/rules#get-rules-for-a-branch"}
```

`GitHubAPI.get()` maps every non-404 HTTP error to `API_UNKNOWN` (line 238 for urllib, line 251
for `gh`), and drops the response body. So `_protection()` returns `unknown` (line 416). The scan
loop then sets `api_facts.status = API_UNKNOWN` for the whole run (lines 624-629). After that,
`_decide()` adds the hold `api-unknown` to every remote ref (lines 527-529).

**2. Result: no remote branch can ever be deleted on such a repository.** Observed on this
repository on 2026-10-05: 7 merged remote branches, a deletion plan of 0 items, and every one held
with `holds=api-unknown`.

**3. The answer is already known on this plan.** GitHub Free does not offer branch protection or
rulesets on private repositories, so no protection can be in force. Also,
`GET /repos/{o}/{r}/branches/{b}` still works and returns `"protected": false` (checked with
`gh api` on this repository). `GET /repos/{o}/{r}/branches/{b}/protection` returns the same 403 and
message; `_protection()` does not call it today, but any future use would hit the same trap.

*Note on the endpoint.* The operator's first description named the `.../protection` endpoint. At
`5090eb0` the call that fails is the rulesets endpoint `rules/branches/{b}`. Both return the same
plan-gated 403, so the request below covers both.

## Impact

- **Branch cleanup is blocked on every private GitHub Free repository.** It fails closed, which
  is safe, but it never recovers: the plan is always empty, whatever the branch state.
- **The cause is hidden.** The only note is `protection unknown for <branch>`. It does not say
  that the plan, not the branch, is the reason, so the operator cannot tell this apart from a
  network or token failure.
- **Here it blocks a decision already made:** the operator approved deleting the 7 merged branches.

## Request

1. **Recognise the plan-gated 403.** In `GitHubAPI.get()` (both the urllib and the `gh` path),
   return a distinct verdict (for example `API_PLAN_GATED`) when the response is HTTP 403 and the
   message contains "Upgrade to GitHub Pro or make this repository public". This needs the error
   body on the urllib path and stderr on the `gh` path.
2. **Use it only in `_protection()`.** When the rulesets call (or a branch-protection call)
   returns `API_PLAN_GATED`, use the `protected` boolean the `branches/{b}` endpoint already
   returned. Since it was false at that point, the result is `"no"`.
3. **Keep everything else fail-closed.** Any other 401/403/404-on-list, rate limit, network error,
   missing `gh` or unparseable body stays `unknown`. This includes a 403 with any other message,
   and a plan-gated 403 on any other call (for example the open-PR list).
4. **Make it visible.** Add a note to `api_facts.notes`, for example "rulesets unavailable on this
   plan; protection read from branches endpoint", so the inventory report shows the fallback.
5. **Add tests** for both `get` paths: (a) a plan-gated 403 on `rules/branches/{b}` with
   `protected: false` from `branches/{b}` gives `protected == "no"`, `api_status == "ok"`, and a
   merged remote branch is planned for deletion; (b) a 403 with a different message stays
   `unknown` and the hold `api-unknown` remains; (c) `protected: true` from `branches/{b}` still
   gives `"yes"` and never reaches the rulesets call.

## Separate observation (not a defect)

A branch that was fast-forwarded into the default branch and has no commits of its own is
classified `active`, not `merged`, until it is older than `stale_days` (default 14). The rule is
`merged = rec.ancestor and (rec.own_commits > 0 or age_days > cfg.stale_days)` (line 485), with
`active` at lines 495-496. In this repository that applies to `agentteams/rc8-update`. This seems
to be intended: it avoids deleting a branch that was just created at the default tip. It is
recorded here so the operator knows why that branch will not be offered for deletion yet, even
after the fix above. No change is requested. A short note in the inventory output saying
"ancestor, no own commits, younger than stale_days" would make the reason visible.

## Interim handling and verification

- **No workaround in this repository.** The 7 approved deletions wait for the fix. This repository
  does not patch `branch_inventory.py`, does not delete branches by hand outside the leased plan,
  and does not change the repository's visibility or plan to get around the check.
- **Verification on arrival.** After the fix reaches this repository through `researchteam update`,
  re-run `agentteams --branch-inventory`. Expect `api_status` `ok`, the fallback note, and the 7
  merged branches in the deletion plan with no `api-unknown` hold. Execution then goes through the
  recorded `@security` clearance as usual.
- **Tracking.** Outbound row of 2026-10-05 in `adjacent-repos-coordination-log.csv`, status
  `awaiting`.
