# Concepts

This page summarizes how the harness works. The authorities are the harness specification
([`reports/02-harness-spec.md`](https://github.com/jlcatonjr/mathAgents/blob/main/reports/02-harness-spec.md)) and the
decision charter, published as a summary
([`docs/charter/decisions-summary.md`](https://github.com/jlcatonjr/mathAgents/blob/main/docs/charter/decisions-summary.md)).
Where this page and those documents differ, those documents are right. Identifiers such as DD-29 refer to design
decisions in the specification, and identifiers such as D13 refer to decisions in the charter.

## Terms

- **Operator:** the person who runs a mathAgents instance and makes its human decisions.
- **Dossier:** everything the pipeline produces for one problem, kept in `reports/dossiers/<slug>/`.
- **Reading:** one interpretation of an informal statement that admits more than one. Each reading the operator
  selects becomes its own formal statement.
- **Object logic:** the logic a problem is stated and proved in. Every problem declares one at intake; classical
  higher-order logic is the default.
- **Fingerprint:** a hash of a declaration's Lean statement. An approval records the fingerprint it approved, so
  changing the statement voids the approval.
- **Kernel snapshot:** a dossier's frozen copy of the G-KERNEL report for its declarations, taken at Stage 8.
- **Blueprint:** a dependency graph of a proof's lemmas, each node naming the Lean declaration that proves it.

## Results

A dossier's result is declared only by the `Result status:` line in its `README.md`. The possible values are:

- `open`
- `conjectured`
- `proved`
- `proved, fidelity-waived`
- `refuted (<decl>)`
- `refuted, verdict-waived (<decl>)`

A result may be called *proved* only when the declaration's status in the G-KERNEL report is `proved`.

## Pipeline stages

The stages, the agents that run them and the files they produce are listed in `mathagents.dossiers.STAGES`, and
`require_stage()` checks that a dossier is ready for a given stage.

| Stage | Name | What happens |
|---|---|---|
| 0 | Intake | The operator and `@orchestrator` write the problem card. It records the source, the informal statement, the domain, the object logic and the engines. When the statement admits rival readings, `@interpretation-advisor` commissions an Interpretation Brief that lists them without ranking them. |
| 1 | Formal statement and fidelity | `@statement-formalizer` drafts a Lean statement as a stub. `@fidelity-auditor` reads it cold and translates it back into prose. The operator then approves the statement at **G-FID**. |
| 2 | Proof-strategy skeleton | `@proof-strategist` writes the informal strategy (`strategy.md`) and `@adversarial` reviews it. The specification also has this stage produce a blueprint dependency graph whose nodes are bound to Lean names, but no blueprint exists yet. |
| 3 | Explicit derivations | `@logic-articulator` writes natural-deduction or sequent derivations, naming a rule or lemma at every step. It uses only rules the declared logic has. |
| 4 | Tactic-level plans | `@tactic-planner` lists candidate tactics and Mathlib lemmas, each verified to exist under the pinned toolchain. |
| 5 | Formalization | `@lean-prover` writes the proof and iterates on kernel feedback. A declaration moves from the open-work library (`MathAgentsWIP`) to the proved library (`MathAgents`) only once it is proved. |
| 6 | Counterexample track | `@counterexample-hunter` runs in parallel with stages 2–5 and tries to falsify the statement. Its candidates go into an append-only log for a human verdict at **G-CX**. |
| 7 | Informalization | `@lean-informalization` narrates what the kernel checked, binding each claim to a Lean name. It adds no claim the kernel did not check. |
| 8 | Dossier assembly | `@axiom-auditor` runs the checks: G-NAME, and G-BLUEPRINT when a blueprint exists. `@orchestrator` then freezes the kernel report into `kernel-snapshot.json`. |

## Gates

The automated gates run in CI on pushes to `main`, on pull requests that touch the gated files, weekly, and on
demand. The human gates record a person's decision, and no agent can make that decision. No result counts as proved
or faithful until the relevant gate has passed.

| Gate | Kind | What it checks |
|---|---|---|
| **G-KERNEL** | automated | It builds the Lean library, replays it through the kernel, and reports each declaration's status (`proved`, `open` or `failed`) and its axioms. It also enforces the axiom envelope (no `sorry`, `admit`, `native_decide` or unapproved axiom) and checks the toolchain pin. It is the ground truth for "proved". |
| **G-NAME** | automated | Every Lean name a dossier cites resolves, either to a library declaration or to a name in the pinned Mathlib. |
| **G-BLUEPRINT** | automated | A blueprint's nodes agree with the Lean declarations. |
| Dossier structure | automated | Each stage's files are present and well-formed. The problem card agrees with the dossier's preferences, and each record is bound to the statements it approves. |
| Registries, preferences | automated | The object-logic and prover-engine registries and the preference files are valid. |
| **G-FID** | human | The formal statement says what the informal one means. An approval is bound to the statement's fingerprint. |
| **G-AX** | human | Any added hypothesis, extra axiom or weakened statement is approved explicitly. |
| **G-CX** | human | A verdict on a logged counterexample. A statement is labelled refuted only on a human `refutes` verdict that carries the statement's current fingerprint. A counterexample found by `decide`, an SMT solver or an automated theorem prover counts only through a kernel-proved Lean witness. |

`mathagents.gates.run_gates()` runs the automated gates in the order of `GATES`. See the
[`gates`](api-reference/gates.md) page.

## Who decides what

- **The Lean kernel decides validity.** Output from other engines (SMT solvers, automated theorem provers, LLM
  provers) is only a hint until the kernel re-checks it.
- **A person decides fidelity and verdicts.** The Python API reads and checks fidelity records, axiom approvals and
  counterexample verdicts, but has no function that writes one. This boundary, design decision DD-29, is part of
  the stability contract and is enforced by tests.
- **The pins decide the toolchain.** An agent works to the instance's Lean and Mathlib pins (`lean/lean-toolchain`,
  `lean/lake-manifest.json`), never to a version named in prose.

## Object logics and engines

The object-logic registry (`references/object-logics.json`) says which logics are available and how each is
embedded in Lean. A logic that is only planned cannot be declared. The prover-engine registry
(`references/prover-engines.json`) lists the engines that can supply hints. The
[explorer](explorer/index.html#pipeline) shows both registries as they currently stand.
