#!/bin/sh
# Pre-commit guard: refuse to commit anything under tmp/ (pr11 P12, condition (f) of the 2026-11-13 @security row
# p12-l2-local-records-seed). tmp/ is gitignored, but `git add -f` bypasses .gitignore, and tmp/ holds this
# checkout's private records (tmp/private-records/) and plans (tmp/by-week/), which must never reach the public
# repository. Deletions pass, so a path committed by mistake can still be removed with `git rm --cached`.
# Installed into .git/hooks/pre-commit by scripts/install_private_paths_guard.sh.
staged="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMRT)" || {
    echo "mathAgents: private-paths guard could not list staged files; refusing the commit (fail closed)" >&2
    exit 1
}
bad="$(printf '%s\n' "$staged" | grep -E '^tmp/' || true)"
if [ -n "$bad" ]; then
    echo "mathAgents: refusing to commit files under tmp/ (private records and plans stay local):" >&2
    printf '%s\n' "$bad" | sed 's/^/    /' >&2
    echo "  unstage: git restore --staged <path>" >&2
    exit 1
fi
exit 0
