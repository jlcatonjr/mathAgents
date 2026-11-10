# CI fallback runner (retired)

D37 set up an operator-only, self-hosted fallback runner on the operator's Mac for GitHub runner outages.
**D45 retired it** when mathAgents became public: a workflow in a fork's pull request could name a
self-hosted label, and GitHub advises against self-hosted runners on public repositories.

Now:
- every Gates job runs on the pinned GitHub-hosted image `ubuntu-24.04`;
- every job starts with a hosted-runner guard that fails on any self-hosted runner;
- `scripts/tests/test_ci_workflow.py` rejects any route back, whether a `runs-on` expression, a label list, a
  `runner` dispatch input or a weakened guard.

If GitHub's hosted runners are down, wait for them, or run the gates locally (`bash scripts/check_proof_integrity.sh`
and the steps in `.github/workflows/gates.yml`) and record the result in the PR. Never merge on a local run alone.
