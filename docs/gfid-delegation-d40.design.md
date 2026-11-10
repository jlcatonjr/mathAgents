# Design: standing, revocable G-FID delegation (charter D40), for review before any code

**Status:** design only; **operator chose route A on 2026-10-21 (charter D40): no delegation is built, and this design is kept as the record for routes B and C.** Previously design only, **revision 3** (baseAgent `@security` on revision 2: CONDITIONAL PASS for the design;
fixes B1–B5 applied), revision 2 after mathAgents' own `@security` (CONDITIONAL PASS, cleared for further
design revision only) and `@adversarial` (CONDITIONAL) reviews; their findings are S1–S6 and A1–A6 below. For review
by baseAgent (baseagent-07) and `@security`. Nothing is built. Jim's go
(2026-10-07): build after the write-policy pilot adoption (P5), as mathagents **v0.2.8**.

**Answers:** baseAgent's request revision 2 (`references/handoffs/to-mathagents/2026-10-07-gfid-delegation-request.md`
at baseAgent `a4241cf`, items R1–R5, R3.1–R3.18), `@security`'s re-review of revision 2 (CONDITIONAL PASS; new points
N1–N3 and E10) and the open review points R4 and R7.

**Principle kept:** "the Lean kernel judges validity; a human judges statement fidelity". Under D40 the human
judgement is made **in advance**, as Jim's signed standing decision, for one narrow class of statements. Every use is
checked by the validator against that decision, logged, and reviewed by Jim afterwards. A delegated result never
reads as a human-approved one. The feature is **off by default** (`fidelity.delegation = "never"`), and mathAgents'
own dossiers keep it off.

## 1. Rule 11 classification

A D40 decision is a **constraint-relaxing authorization** (constitutional Rule 11): it relaxes the human G-FID
gate. So it must be traceable, must carry the **operator's Ed25519 signature** (a symmetric signature is
insufficient), must be refused when it targets a trust root, and must be bounded and expiring. The registry, the
revocations and the verify key are themselves trust roots: no D40 entry may name them as its subject, and no agent
may write them.

## 1a. Preconditions outside the repository (S1, S2, S3, A6): without them a decision is inert

The checks in section 4 are only as trustworthy as the code that runs them and the values it is given. A pull request
can change both a repository's workflow and its validator. So D40 requires these platform-side controls, which no
repository content and no agent token can change. A consumer must have **all** of them before any decision takes
effect:

- **P-1. Trusted verifier.** The delegation checks run from code the PR cannot change. Either a required workflow
  or ruleset in an **operator-owned repository**, pinned by commit SHA, or the gate job checking out the **base
  ref** of the protected branch for the validator, the harness and `delegation_evidence.py`, never the PR head.
- **P-2. Protected branch.** No direct and no force pushes to the default branch. The P-1 check is required, and
  CODEOWNERS (the operator) review is required on every trust-root path (section 2a).
- **P-3. Protected values.** The trusted key fingerprint, and a **revocation epoch** (a counter the operator raises
  with each revocation), live in a CI **environment that needs the operator's approval**, not in plain repository
  variables. The consumer confirms that no agent or automation token has admin, variables-write or
  environment-write scope.
- **P-4. Attestation.** The operator records in the signed decision that P-1 to P-3 are in place (`platform`
  field), and the trusted verifier checks what it can (required-check status, the environment name).

**Routes to P-1–P-3 (baseAgent `@security` on revision 2; the operator decides):**
- **(a) Platform route.** A hosting plan with protected branches, rulesets and reviewer-gated environments for
  private repositories (Pro or Team may not suffice for gated environments in private repos; to be confirmed
  against GitHub's docs). Plus a **separate agent token** with no admin, push-to-protected or variables/environment
  scope. Agent sessions running under the operator's admin credentials fail P-3 on any plan.
- **(b) External-verifier route.** An operator-owned verifier repository that agents hold no token for, with the
  trusted fingerprint and revocation epoch pinned in its code. It gates publication: a delegated label counts only
  in output it has certified. This catches problems after the fact, not before, so it needs a Jim-signed acceptance
  of that residual risk.
- **(c) No delegation.**

**Note for the operator:** P-1 and P-2 need protected branches or rulesets on a private repository. GitHub's free
plan doesn't offer that (mathAgents runs on that plan without branch protection today). Before D40 can go live,
the consumer's hosting plan must provide it, or the operator must accept the residual risk explicitly as a signed
decision. `@security` advises against accepting it.

## 2. Files (all in the consumer instance)

| File | Written by | Content |
|---|---|---|
| `references/gfid-delegation.toml` | operator only (signed) | decision entries, each with an Ed25519 signature |
| `references/gfid-delegation.revocations` | operator only (signed) | revocation and re-arm entries, append-only |
| `references/gfid-delegation.log.csv` | orchestrator (use rows); operator (review fields, signed) | one row per use |
| verify key (path in `mathagents.toml`) | operator only | the Ed25519 public key (PEM) |

### 2a. Trust roots (S5): complete list

The trust roots are:
- the four files above;
- `mathagents.toml`;
- the `fidelity.delegation` setting (`references/preferences.toml` and every dossier `preferences.toml`);
- the consumer's gate workflow;
- the validator scripts, the harness and `mathagents.lock.json`;
- `scripts/delegation_evidence.py`;
- `lean/lakefile.toml`;
- the CI settings and environment of P-1 to P-3;
- the `cryptography` dependency, vetted under S-10 and pinned;
- `references/gfid-delegation-cap.toml` and `references/gfid-delegation-traps.json` (B2);
- `CODEOWNERS` itself (B2);
- the operator-owned verifier repository of P-1, when that route is used (B2).

Under the write-policy pilot, all of these go on `protected_paths`, and all are CODEOWNERS-protected (P-2). No D40
decision may name a trust root as its subject (Rule 11(c)).

## 3. The signed decision entry

```toml
[[decision]]
id = "BA-GFID-DELEG-01"
signed_at = "2026-10-10T00:00:00Z"
expires_at = "2027-01-08T00:00:00Z"        # at most 90 days after signed_at
max_uses = 20
max_pending_review = 10
conditions_version = "D40-1"               # the eligibility rules in force (section 5)
exclude_module_prefixes = ["AgenticCapital"]  # matches the bare module, AgenticCapital.* and AgenticCapitalWIP.* (B5)
exclude_decl_prefixes = ["ZIT."]           # by declaration name too: baseAgent's declarations live in namespace ZIT (B5)
exclude_modules = []                       # individual modules besides
exclude_dossiers = ["p2-lewis-triviality", "p3-dutch-book"]
signer_key_id = "jim-operator-2026-10"
domain = "mathagents-gfid-d40/decision"    # every signed payload names its type (S4)
repo = "github.com/jlcatonjr/baseAgent"     # and the one repository it is valid in (S4)
ancestor = "BA-GFID-DELEG-01@security-decisions.log.csv"  # the recorded authorization it derives from (Rule 11(a))
platform = ["P-1", "P-2", "P-3"]           # the operator attests the preconditions of section 1a
[decision.anchors]
harness_sha256 = "<mathagents.lock.json harness_sha256>"
gate_workflow_sha256 = "<sha256 of the consumer's gate workflow file>"
verify_key_sha256 = "<sha256 of the verify-key file>"
lakefile_sha256 = "<sha256 of lean/lakefile.toml>"  # S5
signature = "<base64 Ed25519 signature>"
```

- **Canonical serialization.** The signature covers the UTF-8 bytes of the JSON object of every field except
  `signature`, with keys sorted, no whitespace, and lists in written order (`json.dumps(obj, sort_keys=True,
  separators=(",", ":"), ensure_ascii=False)`). The same function signs (operator tool, never shipped to agents) and
  verifies.
- **Exclusions by module and declaration prefix (S5, B5).** `exclude_module_prefixes` is a plain string prefix on
  module names: "AgenticCapital" matches the bare module, `AgenticCapital.*` and `AgenticCapitalWIP.*`.
  `exclude_decl_prefixes` matches declaration names (baseAgent's live in `ZIT.`). A module later added under the
  prefix is excluded automatically, and moving a module to another lean_lib doesn't escape it.
  **"First addition" (4.7)** means the declaration's first appearance in the kernel-report history (the walk), so a
  declaration that was ever proved before its delegated entry is ineligible. The
  lakefile is anchored too. This answers the request's question about detecting a new proved-library module.
- **Replay (S4).** Every signed payload (decision, revocation, countersignature) carries `domain`, `repo` and a
  signed `date`. The validator refuses one whose domain or repository differs.
- **Rule 11 (S6).**
  - (a) `ancestor` names the recorded authorization the decision derives from, and inherits any HALT along that
    lineage.
  - (d) A git-tracked aggregate cap, `references/gfid-delegation-cap.toml` (itself signed, a trust root), bounds
    live decisions (default 1) and total uses across all decisions (default 40), with a sunset date.
- **Revocation and re-arm** happen only through a new signed entry in the revocations file. Registry entries are
  immutable once committed, and the history walk refuses an edit (section 4.5). A force-push that removes a
  revocation is caught by the **revocation epoch** (P-3): the trusted verifier refuses when the file holds fewer
  revocations than the epoch counts (S3).

## 4. Validator checks, in addition to today's G-FID rules

Each applies to an entry with `approver_kind = "delegation"`, and each failure is an **error**.

1. **Signature (R3.1).** The entry's signature verifies under the key at the configured path. An unsigned or
   badly signed decision authorizes nothing. The key is never read from the environment.
2. **Trusted key, pinned outside the repository (N1, blocking).** The key file's path is in-repository and
   therefore writable in principle, so its own hash can't vouch for it. The trusted verifier (P-1) takes the
   trusted fingerprint from the **reviewer-gated CI environment of P-3** (`MATHAGENTS_GFID_VERIFY_KEY_SHA256`),
   never from a plain repository variable, which an admin token can write (B1). The validator is invoked as
   `validate_dossier --trusted-key-sha256 "$VAR"`. That value, the key file's actual sha256 and the decision's
   `anchors.verify_key_sha256` must all agree. Without the flag (e.g. a local run), every delegated entry
   fails closed as "unverifiable here". The read-only checker (section 6) reports the same.
3. **Anchors (R3.2).** The decision's `harness_sha256` and `gate_workflow_sha256` must equal the computed values.
   CI computes them in a step the validator doesn't control, and passes them as `--anchors <file>`. A
   mismatch makes the decision inert until it is re-signed.
4. **Live by CI's clock (N2, R16; S1).** `--now`, `--anchors` and `--trusted-key-sha256` are supplied only by the
   trusted verifier (P-1), never by a workflow the PR can change.
   - A delegated entry counts only while its decision is live by **the CI run's own clock**: `--now` supplied by CI
     from the runner's time, never a committer date (forgeable through `GIT_COMMITTER_DATE`). Live means
     `signed_at ≤ now < expires_at`, and not revoked at or before `now`.
   - Once the decision expires or is revoked, an entry not yet countersigned is **demoted, not failed (A4)**. Its
     label becomes `open, fidelity-lapsed`, the dossier can no longer claim it as proved, and CI stays green. So
     there's no pressure to batch-sign to unblock CI.
5. **History walk (R15).** The per-commit walk (`check_history`/`history_step`) is extended to the registry, the
   revocations and the log:
   - registry entries are immutable;
   - the revocations file and the log are append-only;
   - in a log row, only the operator-review fields may change, and only from `pending`.
6. **Use count, backlog and stickiness (R3.4, R3.6; R4).**
   - `delegation.use` is unique and ≤ `max_uses`.
   - Each delegated entry has exactly one log row (decl, fingerprint, intake sha, pin, evidence hashes).
   - A new use is refused while `pending` rows number at least `max_pending_review`.
   - A `rejected` row fails its entry until the entry is removed (a G-AX matter, DD-37).
   - Any logged reviewer round on a fingerprint showing drift, a hidden hypothesis, a G-AX candidate or a
     non-CLEARED verdict bars that fingerprint from delegation for good.
   - **R4 resolved:** the security log row that records the signing of a D40 decision is a multi-use authorization
     and is never marked `consumed`. The uses are counted in `gfid-delegation.log.csv`, not in the security log.
   - **Every reviewer round counts (A1).** Under D39 the orchestrator dispatches the reviewers and writes their
     outputs, so it must not be able to keep only a favourable round. D40 therefore requires the write-policy
     pilot (P5) to be live. Each `back-translation.md` and `statement-review.md` round reaches the dossier only
     through the out-of-session runner's **signed ledger** (agentteams `--apply-proposal`), and each evidence
     file's hash must appear there. Every ledgered round for the fingerprint is counted, not just the last one;
     any adverse round bars the fingerprint (above). *Open with agentteams:* the ledger must also record
     submitted-but-not-applied proposals of these two kinds, so a discarded round leaves a trace.
7. **Eligibility of the statement (R3.7–R3.17).**
   - The effective `fidelity.delegation` is `standing`. The default is `never`, which rejects every delegated entry.
   - `intake_sha256` equals the intake digest, even when the dossier has no `preferences.toml`.
   - `toolchain_pin` and `mathlib_rev` equal the current pin (an error here, not the stamp WARN).
   - The evidence files exist and their sha256 match (section 5).
   - The card has positive fields (**E10, R9, R10**):
     - `Readings: one`;
     - `Reading: R<n>` (no `:variant`);
     - `Object logic: classical-hol`;
     - `Statement of record: primary`.

     `interpretation.md` exists with exactly one `R<n>` heading, matching the card. A missing brief is
     ineligible, never "single".
   - The dossier's `preferences.toml` has no `[gax]` table and no `sources.*` or `readings.*` override.
   - The kernel status at first addition is `open`, and now `open` or `proved`. The declaration's axioms are ⊆
     base ∪ {sorryAx}, and ⊆ base once proved. Every constant in `statement_uses` has axioms ⊆ base, with no
     sorryAx. `approved_axioms` never count.
   - Not a re-approval: the declaration held no approval with another fingerprint at any commit in the walk
     (DD-37).
   - No counterexample against the declaration lacks a verdict.
   - The module of the declaration and of every constant in `statement_uses` matches no `exclude_module_prefixes`
     or `exclude_modules`; the declaration's name matches no `exclude_decl_prefixes`; and the slug is outside
     `exclude_dossiers`.
   - **The hypotheses are satisfiable, by the kernel (A2).** A kernel-proved companion
     `<decl>_hyps_satisfiable` must be `proved` in the G-KERNEL report. **Its type is not written by any agent
     (B3).** A harness Lean template derives it mechanically from the declaration's own type (its binders and
     hypotheses, conclusion dropped, as `∃ <binders>, <hypotheses>`). G-KERNEL then checks that the companion's
     elaborated type is exactly that derivation (the same fingerprint mechanism as the statement), so a weakened
     companion fails. Only its proof is lean-prover's. A statement whose hypotheses can
     never hold is not clear-cut, however the reviews read.
   - **No trap constants (A2).** The statement (its type, and every constant in `statement_uses`) uses none of a
     registered list of known formalization traps, which both reviewers tend to miss together:
     - natural-number and integer truncating subtraction and division;
     - division by zero as a total function;
     - `Int.toNat`, `Nat.cast`/`Int.cast`/`↑` coercions in hypotheses;
     - `Classical.choice`-defined terms in the statement;
     - `sSup`/`sInf`/`iSup`/`iInf` (junk values off their domain), `Real.sqrt` and `Real.log` (junk values off
       domain), and big operators over possibly empty index sets (empty sums and products) (B4).

     The list lives in `references/gfid-delegation-traps.json` (a trust root). Any hit makes the statement
     ineligible. **A deny-list is incomplete by nature (B4):** it narrows the class but proves nothing, which is
     why the satisfiability companion, the two reviews and Jim's after-the-fact review all remain.
   - **The reading is human-chosen (A3).** `Readings: one` and the single `R<n>` are signed by Jim at intake: the
     log row carries his Ed25519 signature over `intake_sha256` (domain `mathagents-gfid-d40/intake`), made before
     the use. "One reading" is therefore his statement, not a card field an agent typed.
8. **Label (R20; A5).** A dossier with a delegated entry that isn't countersigned may carry only
   `proved, fidelity-delegated`, never plain `proved`. The label must survive downstream:
   - the kernel snapshot and the fidelity record carry `approver_kind`;
   - G-NAME (`check_lean_bindings`) refuses a narration that calls a delegated, uncountersigned declaration
     plainly "proved";
   - the Stage 7 narration must say "proved, fidelity-delegated".

   Consumers' publication checks (e.g. baseAgent's papers) are asked to apply the same rule (handoff item).
9. **Countersignature (N3).** Jim countersigns a use by adding to its log row `operator_review = "accepted"`, a
   date, and an Ed25519 signature over the canonical serialization of `{decision, use, slug, decl, fingerprint,
   intake_sha256, evidence hashes, operator_review, date, domain="mathagents-gfid-d40/countersign", repo}`. It
   verifies under the trusted key (4.2). **The operator's signing tool shows the Lean statement next to the
   back-translation and the review before it signs (A4)**: the signature attests that he has read the statement,
   not just its hashes. A countersigned
   delegated entry may carry plain `proved`. An entry is **never re-recorded as `approver_kind = "human"`**: that
   would hide the delegation (OI-09). The validator refuses a human entry whose decl and fingerprint appear in the
   delegation log.

## 5. Evidence and strict parsing (R7 resolved)

The two evidence files are the independent back-translation (`back-translation.md`) and the Stage 1 adversarial
statement review (`statement-review.md`, new). Their fixed fields follow one grammar, in a shared parser
(`scripts/delegation_evidence.py`):
- A field is a line `^<Name>: <value>$`: no leading spaces, no markup, no quotes, ASCII name, value trimmed.
- It counts only **outside code fences**.
- Each required field appears **exactly once**. A duplicate, a missing field, or a field in a variant spelling is a
  failure, never a best guess.
- `back-translation.md` requires `Independent: yes`, `Drift: none`, `G-AX candidates: none`, and
  `Statement fingerprint: <fp>` equal to the entry's.
- `statement-review.md`'s **last round** requires `Statement fingerprint: <fp>`, `Hidden hypotheses: none`,
  `G-AX candidates: none` and `Verdict: CLEARED`.

The orchestrator dispatches `@adversarial` with this form, specified in `docs/kernel-gate.md` and the orchestrator
duties (R5). No agentteams change is needed. `@fidelity-auditor`'s Output section says the fields are machine-read.

## 6. API, CLI, wording (R4, R5, R1)

- **Read-only checker (required):** `mathagents run gfid_delegation check <slug> <decl>` prints each condition
  as met or unmet, using the current UTC time. It writes nothing.
- **`mathagents/fidelity.py`** exposes `approver_kind` and `delegation` read-only. No API function or CLI command
  writes a delegated approval; the consumer's orchestrator does (DD-29 for the API stands).
- **Charter:**
  - D40 (as in the request, revised by this design);
  - D5 gains "G-FID may be delegated by a standing operator decision under D40";
  - D14 and DD-27 are amended per revision 2;
  - DD-29 gains the orchestrator's D40 entry as an exception; G-AX and G-CX are unchanged.
- **Agents (at a render):**
  - `@fidelity-auditor`'s Output section: the fields are machine-read;
  - the orchestrator duties: the review form, the log row, and the "never re-record as human" rule.
- **Dependency:** Ed25519 verification needs `cryptography`, shipped as the extra `mathagents[delegation]`. Without
  it, delegated entries fail closed with a message naming the extra.

## 6a. Cost, and what this design asks of others

- **agentteams:**
  - the ledger records submitted-but-not-applied evidence proposals (A1);
  - a required-workflow or ruleset recipe for P-1.
- **The consumer (baseAgent):**
  - P-1 to P-3 on its hosting plan;
  - operator CODEOWNERS on the trust roots;
  - the same "proved, fidelity-delegated" rule in its publication checks;
  - the intake signature in its intake flow.
- **The operator:** signing tools for decision, revocation, intake and countersignature, kept operator-side.
- **Order:** D40 depends on the write-policy pilot (A1) and on P-1 to P-3. It can't go live before both.

## 7. Tests (to be written with the build)

- A refusal case for every check above, including:
  - a PR-supplied `--now`, `--anchors` or fingerprint;
  - a force-push removing a revocation (the epoch);
  - a replayed payload from another repo or domain;
  - a module moved to another lean_lib;
  - an unsatisfiable hypothesis;
  - a trap constant;
  - an evidence file absent from the ledger;
  - an unsigned intake;
  - a forged committer date;
  - a key-path swap with a matching self-anchor (N1);
  - an unsigned countersignature (N3);
  - a duplicate or fenced field (R7);
  - a missing brief (E10);
  - a module added to an excluded library.
- Negative fixture: baseAgent's odd-sum record (`b7fdaec`), which has no intake sha, no brief and no saved reviewer
  outputs.
- Positive fixture: a synthetic extension of it with those added, kept in mathAgents' tests and signed with a test
  key.

## 8. Not covered, and why

- G-AX, G-CX, waivers, re-approvals of changed or lapsed statements, rival readings, added hypotheses, non-classical
  logics and the AgenticCapital owner's results always stay with the operator. The design gives no path to delegate them.
- Signing tools are operator-side only. mathAgents ships verification, never signing, to agents.
