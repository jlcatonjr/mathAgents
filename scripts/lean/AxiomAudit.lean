
/-! Appended by scripts/proof_integrity.py after an `import` line for every MathAgents module.
Prints one line `GKERNEL-JSON [...]`: each theorem/def/opaque and each inductive or structure type
(kind `inductive` / `structure`, so prose can bind `[Lean: Ns.MyStructure]`; public or private) declared
in a module of a gated library (the roots are substituted from lakefile.toml's lean_lib names), with
- `axioms`: the axioms it transitively depends on;
- `statement_uses`: the project constants its statement reaches — its type, then transitively the
  types, definition bodies and constructor types of project constants (never into Mathlib);
- `statement_fingerprint`: a hash of its type combined with the type and, for definitions, the body
  of every constant in `statement_uses` (spec DD-34; for a type row, of the type constant itself, so its
  constructors' and fields' types are covered; a field's default value is not), so changing a definition a statement relies on
  changes the fingerprint and lapses its G-FID approval. Theorem proofs are not hashed (proof
  irrelevance: re-proving a lemma does not change what a statement means);
- `negates_fingerprint`, for a theorem of type `¬ X` (or `X → False`): the same fingerprint computed
  for `X`, which G-CX uses to bind a counterexample witness to exactly its target. -/

open Lean in
/-- Is `c` declared in a module of a gated (project) library? -/
def gkernelGated (env : Environment) (c : Name) : Bool :=
  match env.getModuleIdxFor? c with
  | some i => match env.header.moduleNames[i.toNat]? with
    | some m => [GKERNEL_ROOTS].any (·.isPrefixOf m)
    | none => false
  | none => false

open Lean in
/-- Project constants reachable from `e`, sorted by name; `none` if the walk ran out of fuel (the
caller fails closed rather than fingerprint a truncated closure). -/
def gkernelClosure (env : Environment) (e : Expr) : Option (Array Name) := Id.run do
  let mut seen : NameSet := {}
  let mut out : Array Name := #[]
  let mut todo : List Name := e.getUsedConstants.toList
  let mut fuel := 1000000
  while fuel > 0 do
    fuel := fuel - 1
    match todo with
    | [] => fuel := 0
    | c :: rest =>
      todo := rest
      unless seen.contains c || !gkernelGated env c do
        seen := seen.insert c
        out := out.push c
        match env.find? c with
        | some (.defnInfo d) => todo := d.value.getUsedConstants.toList ++ d.type.getUsedConstants.toList ++ todo
        | some (.opaqueInfo o) => todo := o.value.getUsedConstants.toList ++ o.type.getUsedConstants.toList ++ todo
        | some (.inductInfo i) => todo := i.ctors ++ i.type.getUsedConstants.toList ++ todo
        | some info => todo := info.type.getUsedConstants.toList ++ todo
        | none => pure ()
  if !todo.isEmpty then return none
  return some (out.qsort (fun a b => a.toString < b.toString))

open Lean in
/-- DD-34 fingerprint of a statement `e`: its hash mixed with the name, type and (for definitions
and opaques) body hash of every project constant it reaches. -/
def gkernelFingerprint (env : Environment) (e : Expr) : Option UInt64 :=
  (gkernelClosure env e).map fun cs => cs.foldl (init := e.hash) fun h c =>
    match env.find? c with
    | some (.defnInfo d) => mixHash h (mixHash (hash c) (mixHash d.type.hash d.value.hash))
    | some (.opaqueInfo o) => mixHash h (mixHash (hash c) (mixHash o.type.hash o.value.hash))
    | some info => mixHash h (mixHash (hash c) info.type.hash)
    | none => h

open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let mods := env.header.moduleNames
  let mut rows : Array Json := #[]
  for (n, ci) in env.constants.map₁.toList do
    let userName := (privateToUserName? n).getD n
    if userName.isInternal then continue
    -- compiler-generated pattern matchers and auxiliary recursors are not statements: their axioms
    -- are still collected through every declaration that uses them, so they need no row of their own
    if Meta.isMatcherCore env n || isAuxRecursor env n then continue
    let some idx := env.getModuleIdxFor? n | continue
    let some modName := mods[idx.toNat]? | continue
    unless [GKERNEL_ROOTS].any (·.isPrefixOf modName) do continue
    let kind ← match ci with
      | .thmInfo _ => pure "theorem"
      | .defnInfo _ => pure "def"
      | .opaqueInfo _ => pure "opaque"
      | .inductInfo _ => pure (if isStructure env n then "structure" else "inductive")
      | _ => continue
    -- what a type row means is its constructors' and fields' types, reached from the constant itself
    let subject : Expr := if kind == "structure" || kind == "inductive"
      then .const n (ci.levelParams.map Level.param) else ci.type
    let axs ← liftCoreM <| collectAxioms n
    -- A theorem of type `¬ X` (or `X → False`) also reports the fingerprint of `X`, so G-CX can
    -- check that a counterexample witness negates exactly its target (`theorem w : ¬ type_of% @t`).
    let negated : Option Expr :=
      let t := ci.type.consumeMData
      if t.isAppOfArity ``Not 1 then some t.appArg!
      else match t with
        | .forallE _ x b _ => if b.consumeMData.isConstOf ``False && !b.hasLooseBVars then some x else none
        | _ => none
    let some closure := gkernelClosure env subject
      | throwError "G-KERNEL audit: dependency closure of {userName} exceeded its bound; refusing to fingerprint"
    let some fp := gkernelFingerprint env subject
      | throwError "G-KERNEL audit: fingerprint of {userName} could not be computed"
    let uses := closure.map (fun c => toString ((privateToUserName? c).getD c))
    let fields := [("decl", toJson userName), ("private", toJson (isPrivateName n)),
      ("kind", toJson kind), ("module", toJson modName),
      ("statement_fingerprint", toJson (toString fp)),
      ("statement_uses", toJson uses),
      ("axioms", toJson (axs.map toString |>.qsort (· < ·)))]
    let negFp : Option UInt64 := match kind, negated with
      | "theorem", some x => gkernelFingerprint env x
      | _, _ => none
    let fields := match negFp with
      | some h => fields ++ [("negates_fingerprint", toJson (toString h))]
      | none => fields
    rows := rows.push <| Json.mkObj fields
  IO.println s!"GKERNEL-JSON {(Json.arr rows).compress}"
