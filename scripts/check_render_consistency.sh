#!/usr/bin/env bash
# Post-render consistency check across the three agent surfaces (read-only; safe in any session).
#   1. every surface's build-log records the same archetype roster;
#   2. no live generated file references a removed agent;
#   3. every Goose orchestrator sub-recipe path exists;
#   4. no operator home paths in files that will be committed;
#   5. G-KERNEL, validate, and registry checks still pass.
# Exit 0 = consistent. Usage: bash scripts/check_render_consistency.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
source "$ROOT/scripts/lib/frozen_surfaces.sh"  # after cd: a frozen check must never fall through to the live one
fail=0
ok()  { echo "  ok   $*"; }
bad() { echo "  FAIL $*"; fail=1; }

echo "[render-check] 1/5 roster parity"
rosters="$(for d in .github/agents .claude/agents .goose/recipes; do
  python3 -c "import json,sys;print(sorted(json.load(open(sys.argv[1]))['archetypes']))" "$d/references/build-log.json"; done | sort -u)"
[[ $(wc -l <<<"$rosters") -eq 1 ]] && ok "identical roster: $rosters" || bad "rosters differ:"$'\n'"$rosters"

echo "[render-check] 2/5 references to removed agents"
REMOVED='topic-scoping-expert|literature-review-expert|main-analysis-expert|conclusion-expert|ref-bibtex-reference|tool-pandoc\.yaml'
# interpretation-advisor is hand-maintained and awaits retargeting (Phase 1); reports are historical.
hits="$(grep -rlE "$REMOVED" .github .claude .goose AGENTS.md CLAUDE.md .goosehints .vscode 2>/dev/null \
  | grep -vE '\.agentteams-backups|build-log\.json|memory-index|security-decisions|defaults-audit|interpretation-advisor|recipe-check\.report\.md|cross-orchestrator-requests' || true)"
[[ -z "$hits" ]] && ok "none" || bad "stale references in:"$'\n'"$hits"

echo "[render-check] 3/5 goose sub-recipes"
missing="$(grep -E 'path: "\./' .goose/recipes/orchestrator.yaml | sed 's/.*path: "\.\///;s/"//' \
  | while read -r f; do [[ -f ".goose/recipes/$f" ]] || echo "$f"; done)"
[[ -z "$missing" ]] && ok "all present" || bad "dangling:"$'\n'"$missing"

echo "[render-check] 3b/5 codex projection"
if [[ -d .codex/agents ]]; then
  codex_out="$(python3 - <<'PY'
import pathlib, tomllib
canon = {p.name[:-len(".agent.md")] for p in pathlib.Path(".github/agents").glob("*.agent.md")}
tomls = {p.stem: p for p in pathlib.Path(".codex/agents").glob("*.toml")}
problems = [f"missing {n}.toml" for n in sorted(canon - set(tomls))] + [f"extra {n}.toml" for n in sorted(set(tomls) - canon)]
for n, p in tomls.items():
    try:
        d = tomllib.loads(p.read_text())
        if not (d.get("developer_instructions") or "").strip(): problems.append(f"{n}: empty developer_instructions")
    except tomllib.TOMLDecodeError as e:
        problems.append(f"{n}: {e}")
print("\n".join(problems))
PY
)"
  [[ -z "$codex_out" ]] && ok "one parseable TOML per canonical agent" || bad "codex projection:"$'\n'"$codex_out"
else
  ok "no codex surface"
fi

echo "[render-check] 3d/5 codex freshness (re-project into a temp dir and diff)"
if is_frozen codex; then
  if git diff --quiet HEAD -- .codex .agents/skills && [[ -z "$(git status --porcelain -- .codex .agents/skills)" ]]; then
    ok "codex is frozen (brief.json frozen_surfaces, D43): byte-identical to HEAD"
  else
    bad "codex is frozen but differs from HEAD:"$'\n'"$(git status --short -- .codex .agents/skills)"
  fi
elif [[ -d .codex/agents ]]; then
  FRESH="$(mktemp -d)"
  if [[ -f .codex/agents/references/build-log.json && -f .agentteams/bin/codex-role-gate.py ]]; then
    # Native Codex team (write_policy covering codex, CX-3; agentteams #319): agentteams refuses an interop-only
    # projection, so re-run refresh step 3a (native render, then the bespoke import) on a copy of the tree.
    FRESH_SRC="$FRESH"; FRESH="$FRESH/tree"
    rsync -a --exclude .git --exclude .venv --exclude lean/.lake --exclude node_modules ./ "$FRESH/" \
      && ( cd "$FRESH" \
           && "$(python3 scripts/lib/agentteams_provenance.py --interpreter-of researchteam)" -c \
                "from pathlib import Path; from researchteam._update_cmd import _refresh_codex; _refresh_codex(Path('.'), dry_run=False)" \
           && bash scripts/lib/project_bespoke_codex.sh ) >"$FRESH_SRC/render.log" 2>&1 \
      || bad "codex freshness: temp projection failed:"$'\n'"$(tail -20 "$FRESH_SRC/render.log")"
  else
    # mirror the repository layout: AGENTS.md is Goose-owned and interop leaves an existing one alone,
    # so a temp dir without it would make interop write it and list it in the team marker
    [[ -f AGENTS.md ]] && cp AGENTS.md "$FRESH/"
    agentteams --interop-from .github/agents --framework codex --output "$FRESH" --yes >/dev/null 2>&1 \
      && agentteams --interop-from .claude/agents --interop-source-framework claude --framework codex \
           --interop-skills-only --output "$FRESH" --yes >/dev/null 2>&1 \
      || bad "codex freshness: temp projection failed"
  fi
  if [[ -n "${FRESH_SRC:-}" ]]; then
    # a native render stamps run provenance into what it writes; compare with that removed (compare_codex_tree.py)
    stale="$(python3 scripts/lib/compare_codex_tree.py "$FRESH" . 2>&1 || true)"
  else
    # the interop team marker is compared with its per-run fields ignored (scripts/lib/compare_codex_marker.py)
    stale="$( { diff -rq -x build-log.json -x .agentteams-backups "$FRESH/.codex/agents" .codex/agents; diff -rq "$FRESH/.agents/skills" .agents/skills
                python3 scripts/lib/compare_codex_marker.py "$FRESH/.codex/agents/references/build-log.json" \
                  .codex/agents/references/build-log.json; } 2>&1 | sed "s#$FRESH/##g" || true)"
  fi
  rm -rf "${FRESH_SRC:-$FRESH}"; unset FRESH_SRC
  [[ -z "$stale" ]] && ok "committed projection matches a fresh projection" \
    || bad "codex projection is stale (run: bash scripts/refresh_agent_surfaces.sh, or, if .codex is write-protected in the session, bash scripts/operator/refresh_codex_projection.sh):"$'\n'"$stale"
else
  ok "no codex surface"
fi

echo "[render-check] 3c/5 skills"
skills_out="$(python3 - <<'PY'
import pathlib, re
problems = []
claude = {p.parent.name: p for p in pathlib.Path(".claude/skills").glob("*/SKILL.md")}
flat = [p.name for p in pathlib.Path(".claude/skills").glob("*.md")]
if flat: problems.append(f"flat (never-loaded) skill files in .claude/skills: {flat}")
for name, p in claude.items():
    fm = re.match(r"^---\n(.*?)\n---", p.read_text(), re.S)
    if not fm or not re.search(r"^name:\s*\S", fm.group(1), re.M) or not re.search(r"^description:\s*\S", fm.group(1), re.M):
        problems.append(f"{name}: SKILL.md lacks name/description front matter")
if pathlib.Path(".codex/agents").is_dir():
    codex = {p.parent.name for p in pathlib.Path(".agents/skills").glob("*/SKILL.md")}
    for n in sorted(set(claude) - codex): problems.append(f"codex missing skill {n} (.agents/skills)")
    for n in sorted(codex - set(claude)): problems.append(f"codex has extra skill {n}")
refs = set()
for f in [*pathlib.Path(".claude/agents").glob("*.md"), *pathlib.Path(".codex/agents").glob("*.toml")]:
    refs |= set(re.findall(r"skills/([a-z0-9-]+)/SKILL\.md", f.read_text()))
for n in sorted(refs - set(claude)): problems.append(f"agents reference missing skill {n}")
print("\n".join(problems))
PY
)"
[[ -z "$skills_out" ]] && ok "claude/codex skill parity; all referenced skills exist" || bad "skills:"$'\n'"$skills_out"

echo "[render-check] 4/5 home paths in committable files"
paths="$(git ls-files -mo --exclude-standard | grep -v '^\.claude/agents/references/build-log\.json$' \
  | xargs -r grep -lE '/(Users|home)/[^/[:space:]"<]+/' 2>/dev/null || true)"
[[ -z "$paths" ]] && ok "none (build-log.json excluded by policy)" || bad "home paths in:"$'\n'"$paths"

echo "[render-check] 5/5 gates"
bash scripts/check_proof_integrity.sh --no-report >/dev/null 2>&1 && ok "G-KERNEL" || bad "G-KERNEL"
bash scripts/claude_researchteam_bridge.sh validate >/dev/null 2>&1 && ok "validate" || bad "validate"
python3 scripts/validate_registries.py >/dev/null 2>&1 && ok "registries" || bad "registries"

[[ $fail -eq 0 ]] && echo "[render-check] CONSISTENT" || echo "[render-check] INCONSISTENT"
exit $fail
