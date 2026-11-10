#!/usr/bin/env bash
# SUPERSEDED (CA-163, 2026-11-09): applied once by the operator on 2026-09-30 (D21) and kept only as D21's record.
# Do not run it. Its render steps predate the one update procedure (scripts/refresh_agent_surfaces.sh, CLAUDE.md
# "mathAgents: How Agent Infrastructure Is Updated"): it skips Codex as "frozen for 1.0" and renders Goose with a bare
# --update --merge. Since MA-6 (agentteams and researchteam v1.1.0) Codex and Goose are unfrozen, and any render runs
# through refresh_agent_surfaces.sh under an operator-signed overwrite row (docs/release-policy.md section 7).
echo "[pause-signing] REFUSED: superseded (CA-163); use scripts/refresh_agent_surfaces.sh" >&2; exit 1
# OPERATOR-ONLY (run from a plain terminal): apply the operator's 2026-09-30 rulings, then re-render.
#   (a) Regenerating git-tracked generated agent files is not destructive under C-5.
#   (b) Key-signed clearances are paused, so enforce_decision_signing is set to false.
# Rationale: docs/reports/2026-09-30-operator-signing-layering-review.md §3. HMAC env-key
# signing does not prevent agent self-clearance.
#
#   bash scripts/operator/pause_signing_and_render.sh
#
# Steps:
#   1. flip the brief flag and propagate it with non-destructive --merge updates (3 surfaces);
#   2. rotate each decisions log per the @security conditions: archive byte-identical, record
#      sha256, carry forward any pending clearance, and cite the rulings and the restore trigger;
#   3. record @security overwrite PASS rows and render all three surfaces;
#   4. run the read-only consistency check. Nothing is committed; hand back to the orchestrator.
# Idempotent: if signing is already paused and the logs are rotated, steps 1-2 are skipped.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
SURFACES=(".github/agents" ".claude/agents" ".goose/recipes")
ARCHIVE_NAME="security-decisions.signed-archive-2026-09-30.csv"
die()  { echo "[pause-signing] ERROR: $*" >&2; exit 1; }
step() { echo; echo "[pause-signing] === $* ==="; }

for v in CLAUDECODE CLAUDE_CODE_SESSION_ID GOOSE_SESSION_ID GOOSE_TERMINAL; do
  [[ -z "${!v:-}" ]] || die "agent session detected (\$$v). This is an operator decision; run it from a plain terminal."
done
command -v researchteam >/dev/null && command -v agentteams >/dev/null || die "researchteam/agentteams CLI missing"
[[ -z "$(git status --porcelain -- brief.json '*/references/security-decisions.log.csv' | grep -v '^??' || true)" ]] \
  || echo "[pause-signing] note: brief.json or a decisions log already has uncommitted edits (expected if staged work is pending)."

DESC="$(mktemp --suffix=.json)"; trap 'rm -f "$DESC"' EXIT

step "1/4 enforce_decision_signing -> false (merge updates, no clearance needed)"
python3 - <<'PY'
import json
b = json.load(open("brief.json"))
if b.get("enforce_decision_signing") is not False:
    b["enforce_decision_signing"] = False
    open("brief.json", "w").write(json.dumps(b, indent=2, ensure_ascii=False) + "\n")
    print("brief.json: enforce_decision_signing set to false")
else:
    print("brief.json: already false")
PY
G="$(mktemp -d)"; trap 'rm -f "$DESC"; rm -rf "$G"' EXIT
# One list: the refresh script's BESPOKE_AGENTS (scripts/tests/test_stage_agents.sh reads the same line).
read -r -a BESPOKE <<< "$(sed -n 's/^BESPOKE_AGENTS=(\(.*\))$/\1/p' scripts/refresh_agent_surfaces.sh)"
[[ ${#BESPOKE[@]} -gt 0 ]] || die "cannot read BESPOKE_AGENTS from scripts/refresh_agent_surfaces.sh"
bash scripts/lib/guard_bespoke_canonical.sh snapshot "$G" "${BESPOKE[@]}"
researchteam update --yes --no-codex >/dev/null || die "researchteam update failed"  # Codex frozen for 1.0 (release policy §5)
bash scripts/lib/guard_bespoke_canonical.sh verify "$G" "${BESPOKE[@]}"
python3 - "$DESC" <<'PY'
import json, sys
b = json.load(open("brief.json")); b.pop("layer2_profile", None)
json.dump(b, open(sys.argv[1], "w"))
PY
for fw in claude goose; do
  agentteams --description "$DESC" --framework "$fw" --project . --update --merge --materialize-native --yes >/dev/null \
    || die "$fw merge update failed"
done
for s in "${SURFACES[@]}"; do
  grep -q '"enforce_decision_signing": false' "$s/references/agent-privilege.json" || die "$s still enforces signing"
done
echo "agent-privilege.json: false on all three surfaces"

step "2/4 rotate decisions logs (archive byte-identical; carry forward pending clearances)"
python3 - "$ARCHIVE_NAME" "${SURFACES[@]}" <<'PY'
import csv, datetime, hashlib, os, sys
archive_name, surfaces = sys.argv[1], sys.argv[2:]
LEGACY = ["timestamp", "requesting_agent", "action_reviewed", "verdict", "conditions", "conditions_verified"]
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
for s in surfaces:
    log, arc = f"{s}/references/security-decisions.log.csv", f"{s}/references/{archive_name}"
    if os.path.exists(arc):
        print(f"{s}: already rotated"); continue
    rows = list(csv.DictReader(open(log, newline="")))
    if any((r.get("verdict") or "").strip().upper().startswith("HALT") for r in rows):
        sys.exit(f"{s}: HALT row present, refusing to rotate (C-2)")
    pending = [r for r in rows if (r.get("verdict") or "").strip().upper() == "CONDITIONAL PASS"
               and (r.get("conditions_verified") or "").strip().lower() == "pending"]
    os.rename(log, arc)                                   # byte-identical archive
    digest = hashlib.sha256(open(arc, "rb").read()).hexdigest()
    with open(log, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LEGACY); w.writeheader()
        w.writerow(dict(timestamp=now, requesting_agent="security", action_reviewed="log-rotation", verdict="PASS",
            conditions=(f"Operator rulings 2026-09-30: (a) regenerating git-tracked generated files is not destructive "
                        f"under C-5; (b) key-signed clearances paused (enforce_decision_signing=false). Basis: "
                        f"docs/reports/2026-09-30-operator-signing-layering-review.md sec.3. Prior log archived unchanged as "
                        f"{archive_name} sha256={digest}. Restore signing when agentteams resolves trust anchoring "
                        f"(request 2026-09-30 F-1). No HALT rows existed."),
            conditions_verified="verified"))
        for r in pending:                                  # carry forward open clearances, still pending
            w.writerow({k: (r.get(k) or "") for k in LEGACY})
    print(f"{s}: rotated (sha256 {digest[:12]}...), carried forward {len(pending)} pending row(s)")
PY

step "3/4 record @security overwrite clearances and render all surfaces"
python3 - "${SURFACES[@]}" <<'PY'
import csv, datetime, sys
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
for s in sys.argv[1:]:
    p = f"{s}/references/security-decisions.log.csv"
    header = next(csv.reader(open(p, newline="")))
    row = {k: "" for k in header}
    row.update(timestamp=now, requesting_agent="security", action_reviewed="overwrite", verdict="PASS",
               conditions="Re-render of git-tracked generated agent files (non-destructive per operator ruling (a)); "
                          "roster union + orphan cleanup; @security CONDITIONAL PASS 2026-09-30 conditions 1-3 applied",
               conditions_verified="verified")
    with open(p, "a", newline="") as fh:
        csv.DictWriter(fh, fieldnames=header).writerow(row)
print("overwrite PASS recorded on all three surfaces")
PY
researchteam materialize --yes >/dev/null || die "copilot materialize failed"
if ! researchteam materialize --help 2>/dev/null | grep -q -- "--copilot-only"; then
  # Installed CLI predates multi-surface materialize: render the native surfaces explicitly.
  for fw in claude goose; do
    agentteams --description "$DESC" --framework "$fw" --project . --update --overwrite --materialize-native --yes >/dev/null \
      || die "$fw render failed"
  done
fi

step "4/4 consistency check"
if bash scripts/check_render_consistency.sh; then
  echo; echo "[pause-signing] DONE and consistent. Hand back to the orchestrator to verify and commit."
else
  die "render is inconsistent; hand back to the orchestrator before committing"
fi
