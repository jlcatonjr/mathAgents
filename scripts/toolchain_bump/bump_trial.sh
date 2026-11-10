#!/usr/bin/env bash
# Toolchain-bump trial: copy a Lake package to a NEW directory, retarget the copy to another Lean/Mathlib
# tag, optionally apply a patch, and build it. The source tree is only read; the trial directory must not
# exist (nothing is ever overwritten). The build log and a source diff land in the trial directory.
#
#   bump_trial.sh --from LEAN_DIR --to TRIAL_DIR --tag v4.34.1 \
#       [--manifest-from LAKE_MANIFEST] [--packages-from PACKAGES_DIR] [--patch FILE] [--wip-lib NAME]
#
#   --manifest-from   reuse a lake-manifest.json pinned at the same Mathlib tag (else `lake update` runs,
#                     which needs network)
#   --packages-from   symlink an existing .lake/packages built for that manifest (else `lake exe cache get`)
#                     CAUTION: the packages are shared, not copied; a build whose options differ from the
#                     source tree's could rebuild into them. Use it only with a manifest pinned to the same
#                     commit (as --manifest-from does); otherwise let the trial fetch its own cache.
#   --patch           a unified diff (paths relative to the Lake package, `-p1`) applied to the copy
#   --wip-lib         add an open-work lean_lib of this name if the lakefile has none (mathAgents gate rule)
# Exit 0 = the copy builds; 1 = build errors (see TRIAL_DIR/build.log); 2 = usage or setup error.
set -euo pipefail
die() { echo "bump_trial: $*" >&2; exit 2; }
abspath() { python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$1"; }
FROM= TO= TAG= MANIFEST= PACKAGES= PATCH= WIP=
while [[ $# -gt 0 ]]; do
  [[ $# -ge 2 ]] || die "option $1 needs a value"
  case "$1" in
    --from) FROM=$2;; --to) TO=$2;; --tag) TAG=$2;; --manifest-from) MANIFEST=$2;;
    --packages-from) PACKAGES=$2;; --patch) PATCH=$2;; --wip-lib) WIP=$2;; *) die "unknown option $1";;
  esac
  shift 2
done
[[ -n $FROM && -n $TO && -n $TAG ]] || die "--from, --to and --tag are required"
# every path is made absolute before the script changes directory
FROM=$(abspath "$FROM"); TO=$(abspath "$TO")
[[ -z $MANIFEST ]] || { MANIFEST=$(abspath "$MANIFEST"); [[ -f $MANIFEST ]] || die "no manifest $MANIFEST"; }
[[ -z $PACKAGES ]] || { PACKAGES=$(abspath "$PACKAGES"); [[ -d $PACKAGES ]] || die "no packages dir $PACKAGES"; }
[[ -z $PATCH ]] || { PATCH=$(abspath "$PATCH"); [[ -f $PATCH ]] || die "no patch $PATCH"; }
[[ -f $FROM/lakefile.toml ]] || die "$FROM has no lakefile.toml"
[[ -z $PACKAGES || -n $MANIFEST ]] || die "--packages-from needs --manifest-from (the shared build must match the manifest)"
mkdir -p "$(dirname "$TO")"
mkdir "$TO" 2>/dev/null || die "$TO exists; a trial never overwrites (choose a new directory)"   # atomic
export PATH="$HOME/.elan/bin:$PATH"

rsync -a --exclude .lake "$FROM/" "$TO/orig/"          # untouched reference copy
rsync -a --exclude .lake "$FROM/" "$TO/lean/"
cd "$TO/lean"
echo "leanprover/lean4:$TAG" > lean-toolchain
python3 - "$TAG" "$WIP" <<'PY' || die "lakefile retarget failed"
import re, sys, tomllib
from pathlib import Path
tag, wip = sys.argv[1], sys.argv[2]
fail = lambda msg: (print(f"bump_trial: {msg}", file=sys.stderr), sys.exit(2))
p = Path("lakefile.toml"); s = p.read_text()
cfg = tomllib.loads(s)
reqs = [r for r in cfg.get("require", []) if r.get("name") == "mathlib"]
if len(reqs) != 1 or "git" not in reqs[0]:
    fail("expected one git `mathlib` require in lakefile.toml")
s = re.sub(r'(\[\[require\]\][^\[]*?name\s*=\s*"mathlib"[^\[]*?rev\s*=\s*")[^"]*(")', rf"\g<1>{tag}\2", s, count=1)
libs = [l["name"] for l in cfg.get("lean_lib", [])]
real = [l for l in libs if Path(f"{l}.lean").exists() or Path(l).is_dir()]
for ghost in set(libs) - set(real):   # a lean_lib with no sources cannot build
    s = re.sub(rf'\[\[lean_lib\]\]\s*\nname\s*=\s*"{re.escape(ghost)}"\s*\n', "", s)
    print(f"bump_trial: removed lean_lib {ghost!r} (no sources)")
if wip and not any(l.endswith("WIP") for l in real):
    s = s.rstrip() + f'\n\n# Open work (mathAgents gate rule): `sorry` tolerated here only.\n[[lean_lib]]\nname = "{wip}"\n'
    Path(f"{wip}.lean").write_text(f"-- Open work for the {wip[:-3]} library (empty: no open results).\n")
    real.append(wip)
targets = "defaultTargets = [" + ", ".join(f'"{l}"' for l in real) + "]"
s, n = re.subn(r'^defaultTargets\s*=.*$', targets, s, count=1, flags=re.M)
if n == 0:
    s = re.sub(r'^(name\s*=.*\n)', rf"\g<1>{targets}\n", s, count=1, flags=re.M)
p.write_text(s)
# re-parse: every edit must have taken effect, or the trial would silently build something else
new = tomllib.loads(s)
got = [r.get("rev") for r in new.get("require", []) if r.get("name") == "mathlib"]
if got != [tag]:
    fail(f"mathlib rev is {got}, not {tag!r} (lakefile layout not understood)")
if sorted(l["name"] for l in new.get("lean_lib", [])) != sorted(real):
    fail("lean_lib list not as intended after the edit")
if sorted(new.get("defaultTargets", [])) != sorted(real):
    fail("defaultTargets not as intended after the edit")
PY
if [[ -n $PATCH ]]; then patch -p1 --forward --no-backup-if-mismatch < "$PATCH" > /dev/null || die "patch did not apply"; fi
mkdir .lake
if [[ -n $MANIFEST ]]; then
  python3 - "$MANIFEST" "$TAG" <<'PY' || die "manifest check failed"
import json, sys, tomllib
from pathlib import Path
m = json.loads(Path(sys.argv[1]).read_text())
ml = [p for p in m.get("packages", []) if p.get("name") == "mathlib"]
if len(ml) != 1 or ml[0].get("inputRev") != sys.argv[2]:
    print(f"bump_trial: --manifest-from pins mathlib {[p.get('inputRev') for p in ml]}, not {sys.argv[2]!r}", file=sys.stderr)
    sys.exit(2)
m["name"] = tomllib.loads(Path("lakefile.toml").read_text())["name"]
Path("lake-manifest.json").write_text(json.dumps(m, indent=1) + "\n")
PY
else
  lake update > "$TO/update.log" 2>&1 || die "lake update failed (network?); see $TO/update.log"
fi
# CAUTION (see --packages-from above): shared, not copied
if [[ -n $PACKAGES ]]; then ln -s "$PACKAGES" .lake/packages; else lake exe cache get > "$TO/cache.log" 2>&1 || die "cache get failed"; fi
(cd "$TO" && diff -ru --exclude=.lake orig lean > source.diff || true)
if lake build > "$TO/build.log" 2>&1; then
  echo "bump_trial: $TAG build OK ($(grep -c 'deprecated' "$TO/build.log" || true) deprecation warning(s)); diff: $TO/source.diff"
  exit 0
fi
echo "bump_trial: $TAG build FAILED; first errors:"
grep -E '^error: [^ ]+\.lean:' "$TO/build.log" | head -10 || true
exit 1
