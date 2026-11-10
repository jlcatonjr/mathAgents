# mathAgents — Research Responses to the Five Open Questions

> Companion to `01-initiating-prompt.md`. Researched 2026-09-30. Evidence is from primary
> sources (GitHub API, Hugging Face API, CrossRef, arXiv) and local machine inspection. Every item
> is a **recommendation** until the operator accepts it. Bibliographic entries marked ✔ were
> confirmed against CrossRef or arXiv on the research date; `@reference-manager` must still import
> and verify them before they are cited in a deliverable.

---

## Q1. Lean/Mathlib pin: match AgenticCapital (v4.32.1) or use the latest stable?

**Recommendation: pin mathAgents to the latest stable pair, Lean `v4.34.1` + Mathlib tag `v4.34.1`.
Get library sharing by moving AgenticCapital forward in a later wave, not by holding mathAgents
back.**

Evidence:
| Fact | Source |
|---|---|
| Lean `v4.34.1` is the newest non-prerelease (2026-09-24); `v4.35.0-rc3` is the current RC | GitHub releases API, `leanprover/lean4` |
| Mathlib has a `v4.34.1` tag (2026-09-24). Mathlib `master` is already on `v4.35.0-rc3`. | GitHub API, `leanprover-community/mathlib4` |
| AgenticCapital pins Lean + Mathlib `v4.32.1` (Mathlib tag dated 2026-07-23), two monthly releases behind | `baseAgent/Projects/AgenticCapital/lean/lean-toolchain`, `lakefile.toml` |
| Lean ships a new release roughly monthly, and Mathlib migrates promptly | Lean community docs on tags and branches |
| Likely upstream dependencies are already past 4.32: FormalizedFormalLogic/Foundation is on `v4.34.0`; the Lean 4 Arrow formalization is on `v4.35.0-rc2` | GitHub API |

Reasoning:
- Lake builds a dependency tree against **one** toolchain and one Mathlib revision. "Sharing a
  library" therefore means both projects must be on the *same* pin. Freezing mathAgents at
  v4.32.1 would make it incompatible with every current external library it may want to import
  (Foundation, the social-choice formalizations) and would start the project already two releases
  stale.
- The cost of upgrading AgenticCapital (≈3.9k lines, 4.32.1 → 4.34.1) is bounded, and it is a
  good first **cross-repo handoff** test. It happens in baseAgent under its own plan, never by
  editing baseAgent from mathAgents.

Policy to write into the harness:
1. Pin to **stable tags only**: no `-rc`, no `master`.
2. Hold a scheduled **toolchain-bump wave** (suggested: whenever the pin is two stable releases
   behind). Each bump re-runs G-KERNEL on the entire library and records the result in the wave
   manifest.
3. Record the pin in each dossier's kernel report, which carries `toolchain_pin` and the running
   `lean_version`, so every "proved" claim names the exact toolchain. *(The engine registry
   schema has no pin field; `lean/lean-toolchain` is the single source of truth.)*
4. Adopting Foundation as a *Lake dependency* couples the Mathlib revision to theirs. Until
   Phase 2 decides otherwise, treat it as a **reference and cross-check**, not a dependency.

---

## Q2. Is there a local GPU? Can open prover models be installed?

**Finding: yes, but a small one.** An NVIDIA GeForce RTX 4050 Laptop GPU, **6 GB VRAM** (driver
595.91), alongside an Intel iGPU. Also 16 CPU threads, 61 GB RAM, ~1.5 TB free disk. `ollama` is
already installed at `/usr/local/bin/ollama`.

**Recommendation: registry status `installable-limited`. Use local models for occasional
single-attempt hints, not for benchmark-style sampling.**

| Model | Params (HF API) | Local fit on 6 GB |
|---|---|---|
| Kimina-Prover-Distill-1.7B | 2.03 B | Fits fully on the GPU (≈4 GB at 16-bit); the most practical local option |
| DeepSeek-Prover-V2-7B | 6.91 B | Q4_K_M GGUF = **4.22 GB**; loads, but the headroom for KV cache is small. Q8_0 = 7.35 GB does **not** fit. |
| Goedel-Prover-V2-8B | 8.19 B | Quantized only, with CPU offload (61 GB RAM makes offload possible, but slow) |
| Kimina-Prover-Distill-8B | 8.19 B | Same as above |

Caveats that belong in the engine registry:
- These provers emit **long chain-of-thought** outputs. On 6 GB, long contexts push the KV cache
  onto the CPU, which cuts throughput sharply.
- Published results use **pass@k sampling** (k = 32 and up). That many samples per theorem is
  impractical locally.
- **Quantized accuracy is unmeasured.** Benchmark numbers reported in the papers must not be
  transferred to local Q4 runs. The harness must measure them in Phase 4.
- Document a **cloud-GPU path** (a rented ≥24 GB card) as a separate `resource_needs` tier for
  when the operator wants real benchmark runs.
- Every model output remains a hint until the Lean kernel re-checks it (already in §7 of the
  prompt).

---

## Q3. Which 3–5 pilot theorems?

**Selection criteria:**
- cover ≥ 3 domains;
- include ≥ 1 non-classical object logic;
- include ≥ 1 philosophy-of-science result;
- include one easy calibration item;
- include one genuinely open target;
- where possible, pick theorems that have an **independent existing formalization** to cross-check
  the harness against.

**Recommended pilot set (run in this order):**

| # | Theorem | Domain | Why it is in the pilot | Cross-check / source |
|---|---|---|---|---|
| P1 | **IMO 1959 P1**: for all n, (21n+4)/(14n+3) is irreducible | Competition (calibration) | Short, and its derivation is explicit (Euclidean-algorithm steps). It exercises every pipeline stage end to end cheaply. | Present in `yangky11/miniF2F-lean4` as `MiniF2F/Test/imo_1959_p1.lean`; benchmark: Zheng, Han & Polu, *miniF2F*, arXiv:2109.00110 ✔ |
| P2 | **Lewis's triviality result**: no conditional connective can have probability equal to conditional probability across all conditionalized probability functions, except in trivial models | Philosophy of science | A short proof that is almost entirely *logical articulation*. It tests Stage 1 (statement fidelity is subtle here) and Stage 3 (explicit derivations). | Lewis 1976, *Philosophical Review* 85: 297–315, DOI 10.2307/2184045 ✔. No Lean formalization was located in this pass; confirm in Phase 1. |
| P3 | **Dutch book theorem (finite, both directions)**: credences over finitely many propositions avoid a sure loss iff they satisfy the probability axioms | Philosophy of science / research-level mathematics | Brings in real mathematics: the converse direction is a convex-duality (Farkas-type) argument. It tests Stage 4 lemma search against Mathlib. | Kemeny 1955, *Journal of Symbolic Logic* 20: 263–273, DOI 10.2307/2268222 ✔. Mathlib has convex-cone duality in `Mathlib/Analysis/Convex/Cone/Dual.lean`. |
| P4 | **Soundness of modal logic K (then S4) w.r.t. Kripke frames**, via a deep embedding | Logic/foundations, **non-classical object logic** | The first entry in `references/object-logics.json`. It proves out the declared-object-logic policy. | Cross-check against FormalizedFormalLogic (`ModalLogic` repo, split out of Foundation; Foundation is Apache-2.0, 285★, active 2026-09-30) |
| P5 | **AgenticCapital `count_optimality` (A2b)**, currently open at `ZITCallAuction.lean:640` | Applied/modeling (**open target**) | A real unsolved item. It may be false (as the upstream `greedy-optimal` postulate was), so it exercises the counterexample track and the G-AX/G-CX human gates. | Start it only after the Q1 toolchain alignment; results return to baseAgent via a handoff. |

**Swap-in alternatives:**
- **Arrow's impossibility theorem.** A strong calibration item for the philosophy/social-choice
  side, because two independent formalizations exist to compare against: Nipkow's Isabelle/HOL
  development (*Journal of Automated Reasoning* 43 (2009): 289–304, DOI 10.1007/s10817-009-9147-4 ✔)
  and a zero-`sorry` Lean 4 version (`Arthur742Ramos/arrow-impossibility-lean`, BSD-3, 1★, so treat
  it as unvetted). The Lean 3 `lean-social-choice` library (last pushed 2021) is obsolete for our
  toolchain.
- **Gödel's ontological argument** in modal logic (the FFL `GodExistence` repo). It is a
  philosophy result on the same modal infrastructure as P4.
- The **vNM utility theorem**, which has recent mechanized proofs (arXiv:2506.07066; not yet
  verified).

---

## Q4. Write-up format and citation style

**Recommendation:**
1. **Canonical proof dossiers: Markdown with Chicago author-date (17th ed.)**, which is the repo
   convention and the format the existing citation-audit tooling expects. Each dossier cites
   Lean declarations as `[Lean: Namespace.name]` together with the toolchain pin and commit.
2. **The proof library also gets a generated blueprint** (web and PDF, with a dependency graph).
   The blueprint's dependency graph *is* the Stage 2 lemma DAG, so it doubles as the review
   surface. Use `leanblueprint` (plasTeX-based; 378★), and **evaluate `LeanArchitect`** (87★, active
   2026-09-25) in Phase 1. LeanArchitect extracts blueprint data from annotations in the Lean
   source, which avoids hand-maintaining a parallel LaTeX document that would drift from the code.
   That drift is the "no paraphrase drift" failure AgenticCapital's doctrine warns about.
3. **One citation style everywhere: Chicago author-date.** Mathematics usually uses AMS numeric
   styles, but running two styles over one `bibliography.bib` doubles the audit surface. For the
   LaTeX blueprint, use `biblatex-chicago` (authordate) so that the blueprint matches the dossiers.
4. **Always cite the platform:** The mathlib Community, "The Lean Mathematical Library," *CPP
   2020*, 367–381, DOI 10.1145/3372885.3373824 ✔.

**Local tooling gaps found:**
- `lualatex` is present.
- **`pandoc`, graphviz (`dot`, needed by leanblueprint's dependency graph), `xelatex`, and
  `biblatex-chicago` are not installed.** Add them to the Phase 0 bootstrap checklist.

---

## Q5. GitHub remote: public or private?

**Recommendation: create the `mathAgents` remote as private now. Later, split the reusable Lean
proof library into its own public, Apache-2.0 repository once it is stable.**

Evidence and reasoning:
- **Your existing pattern.** Framework and tooling repos are public (`researchteam`,
  `agentteams`); research and content repos are private (`baseAgent`, `SocialScienceHumanities`,
  `legalResearch`, `agentteams-research`, …). mathAgents is a research instance.
- **P5 draws on AgenticCapital, which lives in the private `baseAgent`.** A public mathAgents
  would expose that work.
- **Unverified claims.** Early dossiers will contain unverified or open claims. Private status
  allows the G-FID, G-AX and G-CX gates to mature before anything is presented publicly.
- **Public release of the library.** A public library repo under Apache-2.0 (the license used by
  Mathlib and Foundation) makes the proofs reusable and indexable by the Lean package registry
  (Reservoir). *Check Reservoir's current inclusion criteria at split time; they were not verified
  in this pass.*
- **CI cost.** Private repos consume GitHub Actions minutes, and every Lean CI run downloads the
  Mathlib cache. Keep CI to kernel-gate runs on push to `main` plus a weekly run, rather than
  running on every commit.

---

## Summary of recommended decisions

| Q | Decision |
|---|---|
| 1 | Lean + Mathlib `v4.34.1` (stable tags only), with a scheduled bump wave; AgenticCapital upgrade via handoff |
| 2 | RTX 4050 6 GB → LLM provers `installable-limited` (Kimina-1.7B, DeepSeek-V2-7B Q4); cloud tier documented |
| 3 | P1 IMO 1959 P1 · P2 Lewis triviality · P3 finite Dutch book · P4 modal K/S4 soundness · P5 `count_optimality` |
| 4 | Markdown + Chicago author-date dossiers; generated blueprint (leanblueprint, evaluate LeanArchitect); install pandoc/graphviz/biblatex-chicago |
| 5 | Private `mathAgents` now; later a public Apache-2.0 proof-library repo |

## Sources

- Lean releases: https://github.com/leanprover/lean4/releases
- Mathlib releases: https://github.com/leanprover-community/mathlib4/releases
- Lean tags/branches policy: https://leanprover-community.github.io/contribute/tags_and_branches.html
- Model cards: https://huggingface.co/deepseek-ai/DeepSeek-Prover-V2-7B ·
  https://huggingface.co/Goedel-LM/Goedel-Prover-V2-8B · https://huggingface.co/AI-MO/Kimina-Prover-Distill-1.7B
- GGUF sizes: https://huggingface.co/mradermacher/DeepSeek-Prover-V2-7B-GGUF
- DeepSeek-Prover-V2: https://arxiv.org/abs/2504.21801 · Goedel-Prover-V2: https://arxiv.org/abs/2508.03613
- miniF2F: https://arxiv.org/abs/2109.00110 · Lean 4 port: https://github.com/yangky11/miniF2F-lean4
- Lewis 1976: https://doi.org/10.2307/2184045 · Kemeny 1955: https://doi.org/10.2307/2268222
- Nipkow 2009: https://doi.org/10.1007/s10817-009-9147-4 · Lean 4 Arrow: https://github.com/Arthur742Ramos/arrow-impossibility-lean
- FormalizedFormalLogic: https://github.com/FormalizedFormalLogic
- mathlib paper: https://doi.org/10.1145/3372885.3373824
- leanblueprint: https://github.com/PatrickMassot/leanblueprint · LeanArchitect: https://github.com/hanwenzhu/LeanArchitect
