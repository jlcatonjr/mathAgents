
/-! Appended by scripts/build_name_index.py after `import Mathlib`. Writes every non-internal constant
name of the imported environment (the pinned Mathlib and its dependencies), one per line, to the
path substituted for NAME_INDEX_OUT. G-NAME and G-BLUEPRINT resolve non-project names against it
(spec DD-17, DD-42); project names resolve against the G-KERNEL report. -/
open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let mut out : Array String := #[]
  for (n, _) in env.constants.map₁.toList do
    let u := (privateToUserName? n).getD n
    -- declarations only: no internal, private, matcher or auxiliary-recursor constants, and no
    -- deprecated aliases (a binding must name what the pinned environment actually provides)
    if u.isInternal || isPrivateName n || isAuxRecursor env n || Meta.isMatcherCore env n
        || Linter.isDeprecated env n then continue
    out := out.push u.toString
  IO.FS.writeFile "NAME_INDEX_OUT" (String.intercalate "\n" (out.qsort (· < ·)).toList ++ "\n")
  IO.println s!"NAME-INDEX {out.size}"
