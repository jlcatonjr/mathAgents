# Component Brief — Methods Literature Review (`methods-review`)

- **Target file:** `reports/01-methods-review.md` · **Component:** 1 · **Prepared by:** `@methods-review-expert` · 2026-09-30
- **Thesis:** Survey the methods literature only insofar as it justifies, constrains, or warns against
  specific stages, gates, agents, and engine-registry entries of the mathAgents harness (charter §4–§7),
  so that the Harness Specification can cite a finding for every design decision (charter §8.2).
- **Inputs:** `brief.json` (component `methods-review`), `docs/charter/01-initiating-prompt.md` §4 and §8,
  `docs/charter/02-open-questions-research.md`, `docs/charter/03-decisions.md`,
  `references/phase1-source-inventory.csv` (54 rows).
- **Status:** DRAFT BRIEF — requires `@adversarial` presupposition review and `@reference-manager`
  key verification before hand-off to `@primary-producer`.

## Blocking preconditions (fail-closed)

1. `references/phase1-evidence/*.jsonl` **does not exist yet** (checked 2026-09-30). Drafting may not begin
   until it exists and holds `supported_claims` with verbatim quotes for every key cited.
2. No project `bibliography.bib` exists yet. `@reference-manager` must import every assigned key and
   resolve the two `metadata-conflict` rows (Azerbayev2023 author list; Massot2021 year) before either is cited.
3. Keys marked `verified` in the inventory are verified for *existence and metadata only*; that is not
   evidence for any content claim.

## Global rules (apply to every section)

- **Citation form:** Chicago author-date in-text, `(Author Year)` or `Author (Year)`; multiple works `(A 2022; B 2023)`.
  Keys map to `bibliography.bib`. `n.d.` works cite as `(Organization n.d.)`.
- **Every factual sentence cites ≥1 key.** Synthesis/evaluative sentences must point to the factual
  sentences they rest on (same paragraph) and be phrased as the review's inference, not the source's claim.
- **Grounding:** each cited claim must match a `supported_claims` entry in `references/phase1-evidence/*.jsonl`
  for that key, and the prose must not exceed the quote's scope. No claim from memory, model-card
  pages, or the charter's own summaries unless those are themselves in the evidence file.
- **Status disclosure:** state preprint status at first citation of every arXiv-only work ("an arXiv
  preprint"). Where the inventory notes a venue "not re-checked" (Wu2022, Yang2023), do not name the venue.
  GitHub repositories and web pages are labelled as software/documentation, not scholarship.
- **No ranking:** no "state of the art", "best", or ordering of systems beyond an explicit comparison
  stated in a cited source, attributed to that source and its date.
- **Numbers:** no benchmark scores, pass rates, dataset sizes, or parameter counts unless the number
  appears in a retrieved abstract/quote in the evidence file; always give the metric, the benchmark split,
  and the sampling budget (e.g., pass@k) as the source states them. Never transfer reported numbers to local
  or quantized runs (charter 02 §Q2).
- **Unverified systems:** any system named in the charter but absent from the inventory — e.g.,
  Pantograph, Z3, cvc5, Vampire, E, LeanArchitect, a Lean LSP/MCP server, Kimina-Prover-Distill models,
  the Lean 4 Arrow repo — may be mentioned only with the label **"(unverified; not in Phase 1 inventory)"** and
  with no capability claim.
- **Out of scope for this component:** the seven `philosophy-of-science-pilots` keys (Lewis1976, Kemeny1955,
  deFinetti1937, Nipkow2009, Arrow1950, Arrow1951, Li2025) belong to dossiers/evaluation; do not cite them here
  except Nipkow2009 as a single cross-reference if §7 needs a mechanized-HOL precedent, and only if the evidence file supports it.
- **Voice:** analytic, no promotional adjectives; each section ends with 1–3 "Harness-relevant findings"
  bullets labelled F2.1, F2.2, … (section.number) that §8 cites.

## Section specifications

### 1. Scope and Method
- **Purpose:** Define what the review covers and how sources were selected and verified, so readers can judge the evidence base behind §8.
- **Guiding questions:** Which harness decisions (charter §4 stages 0–8; gates G-FID, G-AX, G-CX, G-KERNEL; §7 engine registry) does the review inform? What was the search/verification procedure (inventory columns `verified_via`, `verification_status`)? What is excluded (pilot-theorem sources; unverified systems)? What are the limits (preprint-heavy corpus; existence-verification ≠ content verification)?
- **Keys:** none required; may describe the inventory by counts only. Cite no source for method description.
- **Must NOT claim:** completeness of coverage; that "verified" means content-checked; any date of search other than the documented one.

### 2. Autoformalization and Statement Fidelity
- **Purpose:** Establish what is known about translating informal statements to formal ones and checking that meaning is preserved — the evidential basis for Stage 1 and G-FID.
- **Guiding questions:** What failure modes of NL→formal statement translation do sources report? What automated fidelity/alignment checks exist (FormalAlign; back-translation, Herald) and what do sources say about their limits — i.e., can any replace the human G-FID gate? How is compiler feedback used during formalization (process-driven), and does compiling imply fidelity? How were large autoformalized datasets filtered, and what does that imply for the `@fidelity-auditor`'s independent back-translation?
- **Keys (7):** Wu2022 (verified; preprint), Azerbayev2023 (**metadata-conflict** — resolve first; also §5), Gao2024 (verified; preprint), Lu2024b (verified; preprint), Lu2024a (verified; preprint), Yang2023 (verified; preprint; may be cross-cited in §3/§4), Ying2024 (verified; preprint).
- **Must NOT claim:** that any automated metric certifies fidelity; accuracy figures not in the evidence file; that type-checking a statement establishes its correctness.

### 3. Informal-to-Formal Pipelines and Blueprints
- **Purpose:** Review staged pipelines (informal draft → sketch → proof) and blueprint methodology — the basis for Stages 2, 4, 7 and the blueprint DAG.
- **Guiding questions:** How does Draft-Sketch-Prove decompose the task, and which intermediate artifact maps to our Stage 2/4 artifacts? What does blueprint practice (leanblueprint; the sphere-eversion project) show about dependency-graph review and drift between prose and code? What interaction patterns (in-editor copilot, in-context agent, whole-proof generation + repair) are documented, and which harness agent (`@proof-strategist`, `@tactic-planner`, `@lean-prover`) each pattern informs? What target-system facts (Lean 4, Mathlib, naming conventions, doc-gen4, Verso) bind Stage 5 and Stage 7 name-binding?
- **Keys (11):** Jiang2022a (verified; preprint), Massot2021 (**metadata-conflict**; software), Song2024 (verified; preprint), Thakur2023 (verified; preprint), First2023 (verified; preprint), vanDoorn2023 (verified; CPP proceedings), Moura2021 (verified; CADE LNCS), mathlib2020 (verified; CPP 2020), LeanFRO_docgen4 (verified; software), LeanFRO_verso (verified; software), Mathlib_naming (verified; web documentation).
- **Must NOT claim:** LeanArchitect behavior (unverified); that blueprints prevent drift (only what sources report); performance numbers for COPRA/Baldur/Lean Copilot absent from evidence.

### 4. Provers and Proof Search
- **Purpose:** Characterize LLM provers, search methods, and hammers as candidate engines — the basis for `@engine-advisor`, `references/prover-engines.json` fields (`strengths`, `unsuited_for`, `result_trust`, `resource_needs`) and Stage 5.
- **Guiding questions:** What proof-generation paradigms exist (step-level search: GPT-f, HTPS, expert iteration; whole-proof generation; subgoal decomposition; RL with proof-assistant feedback)? How do hammers and premise selection (Sledgehammer survey; Thor; LeanHammer) combine with LMs? What sampling/compute budgets do sources state, and what does that imply for per-machine `resource_needs` (D10) and "hints until kernel re-check" (§7)? Which systems target Lean 4 specifically, per source?
- **Keys (14):** Polu2020, Polu2022, Lample2022, Jiang2022b, Zhu2025, Xin2024a, Xin2024b, Ren2025, Lin2025a, Lin2025b, Wang2025, Chen2025 (all verified; arXiv preprints); Blanchette2016 (verified; JFR — DOI not in CrossRef, publisher page); Hubert2025 (verified; *Nature*, online 2025, print 2026 — cite as 2025 per inventory).
- **Must NOT claim:** local fit or throughput of any model (that is a machine fact, D10, not literature); a ranking of provers; benchmark numbers not in evidence; that "Preview"/"V2" results generalize beyond the reported setting.

### 5. Benchmarks
- **Purpose:** Describe the benchmarks the harness evaluation (component 5) will sample, including their construction and known caveats.
- **Guiding questions:** What does each benchmark contain, in which formal languages, and how were statements produced/validated (hand vs. autoformalized)? What evaluation protocols (pass@k, splits) do sources define, so the evaluation reports comparable metrics? What contamination or mis-formalization caveats do sources state, and how should the evaluation's failure taxonomy (mis-formalization, strategy error, tactic failure, false statement) account for them?
- **Keys (3 + 1 cross):** Zheng2021 (verified; preprint), Tsoukalas2024 (verified; preprint), Yu2025 (verified; preprint); cross-cite Azerbayev2023 (ProofNet; metadata-conflict).
- **Must NOT claim:** leaderboard standings; the Lean 4 miniF2F port's fidelity (the `yangky11/miniF2F-lean4` repo is unverified); scores by any system.

### 6. Proof-Theoretic Representations
- **Purpose:** Ground Stage 3 (explicit derivations with named rules) and the interchange formats used by the counterexample track and non-Lean engines.
- **Guiding questions:** Which calculus (natural deduction vs. sequent calculus) suits the named-rule articulation required at Stage 3, and what properties (normalization, cut elimination) matter for a mechanical rule-check? What do TPTP and SMT-LIB standardize, and what does that imply for translating Lean subgoals to ATP/SMT and treating results as hints (§7)? What representation does the `@logic-articulator` need to be object-logic aware?
- **Keys (6):** Sutcliffe2017 (verified; JAR), Barrett2017 (verified; technical report, v2.6 — do not cite v2.7 content), Gentzen1935 (verified), Gentzen1969 (verified; English translation — cite with Gentzen1935 as translation), Prawitz1965 (verified via review record; no DOI), Troelstra2000 (verified; CUP).
- **Must NOT claim:** that solver/ATP output is proof-producing or kernel-checkable unless a source says so; capabilities of Z3/cvc5/Vampire/E (unverified).

### 7. Non-Classical Logics in Proof Assistants
- **Purpose:** Survey embeddings of modal and other non-classical logics, to justify the declared-object-logic policy (§3, D4) and `references/object-logics.json`.
- **Guiding questions:** What distinguishes shallow semantic embeddings (Benzmüller line) from the deep embeddings the charter mandates, and what does each give up (e.g., reasoning *about* the logic vs. *in* it)? What mechanized metatheory (S5 completeness; the modal cube; Foundation library) exists to reuse or cross-check P4? Which logics in the charter's list (deontic, intuitionistic, conditional, probabilistic, relevance) have **no** source in the inventory — state these as gaps.
- **Keys (6):** Benzmuller2013, Benzmuller2014, Benzmuller2015, Benzmuller2019 (verified), Bentzen2021 (verified; CLAR 2021 LNCS), FFL_Foundation (verified; software).
- **Must NOT claim:** coverage or completeness of the Foundation library beyond evidence; that shallow-embedding results transfer to deep embeddings; the `ModalLogic`/`GodExistence` repos' contents (unverified).

### 8. Implications for Harness Design
- **Purpose:** Convert §2–§7 findings into design implications the Harness Specification (component 2) will cite; introduces **no new sources and no new facts**.
- **Required table** (one row per implication; ≥1 row per section §2–§7):

| Implication | Pipeline stage/gate/agent affected | Finding (section ref) | Sources |
|---|---|---|---|
| e.g. "Automated alignment scores are advisory inputs to G-FID, not a substitute" | Stage 1; G-FID; `@fidelity-auditor` | F2.x | keys already cited in that finding |

- **Row rules:** "Finding" must reference a labelled Harness-relevant finding (F2.1 … F7.n) from an earlier section; "Sources" lists only keys cited in that finding; stage/gate/agent names must match charter §4–§7 exactly (`G-FID`, `G-AX`, `G-CX`, `G-KERNEL`, `@statement-formalizer`, … `prover-engines.json` field names). Implications drawn from a preprint-only finding are marked "(preprint evidence)".
- **Also required:** a short "Gaps" list: harness decisions with no supporting finding (e.g., counterexample track Stage 6, G-AX, non-modal object logics) — stated as gaps, not filled by assertion.
- **Must NOT claim:** any implication without a traceable finding; engine recommendations for a specific machine; that the literature validates the harness as a whole.

## Cross-reference map
- **Downstream:** `harness-spec` (component 2) cites §8 rows by implication; `evaluation` uses §5; `prover-engines.json` `sources` and `object-logics.json` `sources` draw on §4 and §7 keys.
- **Upstream:** charter §3–§8; decisions D1, D3–D6, D10, D11.

## Completion checklist (mirrors `brief.json` quality_criteria; all must PASS)

1. **Every source verified by reference-manager**
   - [ ] Every cited key is in `bibliography.bib` and `@reference-manager` returned clear.
   - [ ] Azerbayev2023 and Massot2021 conflicts resolved (or not cited).
   - [ ] Every cited claim matches a `supported_claims` quote in `references/phase1-evidence/*.jsonl`.
   - [ ] Every sentence stating a fact carries ≥1 `(Author Year)` citation; no key outside this brief's assignments without expert approval.
   - [ ] `bash scripts/claude_researchteam_bridge.sh citation-audit` (mechanical) plus the doubled semantic audit both clean.
2. **Each implication is traceable to cited findings**
   - [ ] Every §8 row cites an F-label defined in §2–§7, and its Sources ⊆ that finding's keys.
   - [ ] Each of §2–§7 contributes ≥1 row; a Gaps list is present.
3. **Unverified systems are labelled as such**
   - [ ] Every system not in the inventory carries "(unverified; not in Phase 1 inventory)" and has no capability claim.
   - [ ] Preprint status stated at first citation of each arXiv-only work; software/web sources labelled.
   - [ ] No benchmark numbers without an evidence quote; no ranking beyond source statements.
- [ ] Section headings match `brief.json` exactly, in order (8 sections).
