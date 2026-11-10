-- Appended by scripts/toolchain_bump/statement_drift.py after the project library's import. Writes every external
-- (Mathlib or core) constant that a project theorem's statement reaches, following project definitions
-- (their types and values, never project proofs) and stopping at the first external constant, with its
-- module and declaration line range under the current toolchain, to STATEMENT_DEPS_OUT.
open Lean Elab Command

-- Project constants: declared in a module under the project library.
def isProjectConst (env : Environment) (n : Name) : Bool :=
  match env.getModuleIdxFor? n with
  | some i => "PROJECT_LIB".toName.isPrefixOf env.header.moduleNames[i.toNat]!
  | none => false

run_cmd do
  let env ← getEnv
  let mut seen : NameSet := {}
  let mut ext : NameSet := {}
  let mut todo : Array Name := #[]
  for (n, ci) in env.constants.toList do
    if isProjectConst env n && ci.isTheorem && !n.isInternal then
      for c in ci.type.getUsedConstants do todo := todo.push c
  while h : todo.size > 0 do
    let c := todo.back
    todo := todo.pop
    if seen.contains c then continue
    seen := seen.insert c
    if isProjectConst env c then
      if let some ci := env.find? c then
        for d in ci.type.getUsedConstants do todo := todo.push d
        unless ci.isTheorem do
          if let some v := ci.value? then
            for d in v.getUsedConstants do todo := todo.push d
        if let .inductInfo ii := ci then
          for k in ii.ctors do todo := todo.push k
    else
      ext := ext.insert c
  let mut out : Array String := #[]
  for c in ext.toList do
    let m := match env.getModuleIdxFor? c with
      | some i => env.header.moduleNames[i.toNat]!.toString
      | none => "?"
    let r ← liftCoreM <| findDeclarationRanges? c
    let (a, b) := match r with
      | some r => (r.range.pos.line, r.range.endPos.line)
      | none => (0, 0)
    out := out.push s!"{c}\t{m}\t{a}\t{b}"
  IO.FS.writeFile "STATEMENT_DEPS_OUT" (String.intercalate "\n" out.toList ++ "\n")
  IO.println s!"STATEMENT-DEPS {ext.size}"
