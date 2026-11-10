# Methods Literature Review

This component reviews the methods literature on autoformalization, informal-to-formal pipelines, provers, benchmarks, proof-theoretic representations, and non-classical logics only insofar as it justifies, constrains, or warns against design decisions of the mathAgents harness; the Harness Specification cites its final section. Every cited claim is bounded by its source's retrieved abstract, and where abstracts are silent the silence is reported as a gap.

## Scope and Method

The review informs the harness defined in charter §4 to §7: pipeline stages 0 to 8, the gates G-FID, G-AX, G-CX, and G-KERNEL, and the fields of the prover-engine registry. The six topical sections end with labelled findings that the final section turns into implications.

The evidence base is a Phase 1 source inventory of 54 entries, verified for existence and bibliographic metadata, plus an evidence layer with one record per entry. Each record holds the retrieved abstract verbatim (for software and web documentation, the repository description or page excerpt), its retrieval route and timestamp, and quotation-anchored claims; records were retrieved 30 September–1 October 2026 (UTC), and 45 of 54 hold retrievable text. Every cited sentence here is entered in a claim ledger with supporting quotations that a validator checks against the retrieved text, and inferential sentences are marked as the review's own, pointing to the factual sentences they rest on.

Seven entries on the philosophy-of-science pilot theorems belong to the proof dossiers and are excluded, leaving 47 in scope. Systems named in the charter but absent from the inventory, such as Pantograph, Z3, cvc5, Vampire, E, LeanArchitect, or a Lean LSP or MCP server, are labelled (unverified; not in Phase 1 inventory) and receive no capability claim.

Limits: of the 47 works, 26 are arXiv preprints, five published works are represented by their arXiv abstract, five are software or web documentation, and five have no retrievable abstract, of which four are cited only for identity and one is not cited. Existence verification is not content verification, and abstracts are authors' summaries, so results are reported as authors' claims. Figures carry the metric and budget their abstract states, or a note that it states none, and none predicts a local run. Coverage is not claimed to be complete.

## Autoformalization and Statement Fidelity

Autoformalization is defined in an arXiv preprint as the automatic translation of natural-language mathematics into formal specifications and proofs (Wu et al. 2022). An arXiv preprint on process-driven autoformalization observes that existing efforts are limited to formal languages with substantial online corpora and struggle to keep pace with rapidly evolving languages like Lean 4 (Lu et al. 2024a). Two further arXiv preprints cite, respectively, the scarcity of training data in formal languages such as Lean and the lack of parallel datasets that align natural language with formal language proofs (Ying et al. 2024; Gao et al. 2024).

The FormalAlign arXiv preprint states the fidelity problem directly: ensuring semantic alignment between the informal and formalized statements remains challenging, and existing approaches heavily rely on manual verification (Lu et al. 2024b). FormalAlign, which its authors present as the first automated framework for evaluating this alignment, was evaluated on four benchmarks augmented by the authors' own misalignment strategies, and the abstract concludes that this "effective alignment evaluation significantly reduces the need for manual verification" (Lu et al. 2024b). In those experiments FormalAlign is reported to outperform GPT-4 on Alignment-Selection Score, 99.21% against 88.91% on the split the retrieved abstract renders as `\forml-Basic` and 66.39% against 64.34% on MiniF2F-Valid (Lu et al. 2024b). The review reads this as a reported reduction of manual verification, not its removal: the abstract does not claim that FormalAlign replaces human checking, and its figures are for benchmarks the authors augmented themselves.

The ProofNet arXiv preprint introduces two statement autoformalization methods, prompt retrieval and distilled backtranslation (Azerbayev et al. 2023). Herald, an arXiv preprint, works from formal to informal, translating the Mathlib4 corpus into natural language in response to the lack of parallel data (Gao et al. 2024). The Herald Translator, fine-tuned on that dataset, is reported to achieve "a 93.2% accuracy (Pass@128) on formalizing statements in the miniF2F-test" and 22.5% on the authors' internal graduate-level textbook dataset (Gao et al. 2024). The retrieved abstract does not state how a formalization was judged accurate, so the review cannot tell whether these rates measure compilation or meaning (Gao et al. 2024). In the ProofNet and Herald abstracts back-translation produces statements or training data; neither reports using it to certify that a particular formal statement means what its informal source means.

The process-driven preprint introduces a verifier that leverages the precise feedback from Lean 4 compilers to enhance autoformalization, reporting higher accuracy using less filtered training data (Lu et al. 2024a). Compiler feedback here improves accuracy as the authors measure it; the abstract does not claim that a statement which compiles is faithful, so the review treats a Stage 1 stub that elaborates as necessary but not sufficient for G-FID.

Lean Workbook, an arXiv preprint, iteratively generates and filters synthetic data to translate natural-language problems into Lean 4 statements and back (Ying et al. 2024). Goedel-Prover, also an arXiv preprint, trains models to convert natural-language problems into what the authors call equivalent formal statements in Lean 4, producing 1.64 million formal statements (Lin et al. 2025a). FormalMATH, an arXiv preprint, combines statement autoformalization, multi-LLM semantic verification, and negation-based disproof filtering in a human-in-the-loop pipeline which, its authors report, reduces expert annotation costs by retaining 72.09% of statements before manual verification while ensuring fidelity to the original natural-language problems (Yu et al. 2025). The retrieved abstract gives no measured fidelity error rate for the retained statements (Yu et al. 2025). Even this pipeline, the one that names semantic verification, places manual verification after its automated filters; the review reads this as consistent with the charter's policy that the `@fidelity-auditor`'s back-translation is one more filter feeding the human gate, not the gate itself.

Read together, these abstracts report high automated rates on the authors' chosen benchmarks and budgets, 93.2% at Pass@128 for statement formalization and an Alignment-Selection Score of 99.21%, alongside lower rates on other sets, 22.5% and 66.39%; the review infers that the evidence supports automated drafting at Stage 1 and a reduced manual burden at G-FID (Gao et al. 2024; Lu et al. 2024b). No abstract reviewed here claims that automation removes the need for a human fidelity check, nor does any test that claim, so keeping G-FID a human gate is the charter's policy, which this evidence neither forces nor contradicts.

Harness-relevant findings:

- **F2.1**: Automated statement formalization and alignment evaluation are reported at high rates on the authors' benchmarks and budgets and at lower rates on other sets; they are reported to reduce manual verification, no abstract claims they remove it, and keeping their scores advisory input to G-FID is the charter's policy (Gao et al. 2024; Lu et al. 2024b).
- **F2.2**: Lean compiler feedback is reported to improve autoformalization accuracy, but no reviewed abstract equates compiling with fidelity (Lu et al. 2024a).
- **F2.3**: Automated filtering of autoformalized statements is reported by Lean Workbook and FormalMATH, with manual verification after the filters in FormalMATH; the Goedel-Prover abstract describes no filtering (Ying et al. 2024; Lin et al. 2025a; Yu et al. 2025).

## Informal-to-Formal Pipelines and Blueprints

Draft, Sketch, and Prove, an arXiv preprint, maps informal proofs to formal proof sketches and uses the sketches to guide an automated prover by directing its search to easier sub-problems (Jiang et al. 2022a). The informal proofs were written by humans or generated by a language model, and the authors report that large language models produce well-structured formal sketches that follow the same reasoning steps as the informal proofs (Jiang et al. 2022a). By an analogy the source does not draw, the review maps the informal draft onto the Stage 2 skeleton and the formal sketch, whose gaps go to automation, onto the Stage 4 tactic plan.

Countervailing evidence comes from FormalMATH, whose authors report a counterintuitive inverse relationship between natural-language solution guidance and proof success in chain-of-thought reasoning scenarios, "suggesting that human-written informal reasoning introduces noise rather than clarity in the formal reasoning settings" (Yu et al. 2025). The two results come from different settings, sketch-guided automated search in one and chain-of-thought reasoning scenarios in the other, and the review does not reconcile them; whether an informal Stage 2 skeleton helps the Stage 4 plan is therefore an open question for the evaluation, not a finding.

The leanblueprint software repository describes a plasTeX plugin for writing blueprints for Lean 4 projects, originally created in 2020 for the Sphere Eversion Project and since used by many projects (Massot 2021). Its README documents macros that list the Lean declaration names corresponding to a definition or statement, declare that an environment is fully formalized, and list the labels an environment uses, from which the dependency graph is created (Massot 2021). Because the `\leanok` macro, in the README's words, "claims the surrounding environment is fully formalized", the marker is a declaration by the author, and the review infers that the harness must check it against G-KERNEL status; the retrieved README excerpt, which omits parts of the file, describes no check against drift between prose and code. The first paper of the sphere eversion project, in the CPP 2023 proceedings, describes a Lean formalisation of the local h-principle that reproves Smale's sphere eversion theorem (van Doorn, Massot, and Nash 2023). The retrieved abstract does not mention blueprints (van Doorn, Massot, and Nash 2023).

The in-editor copilot pattern is documented by Lean Copilot, an arXiv preprint describing a framework for running LLM inference natively in Lean, on which tools are built that suggest proof steps, complete proof goals, and select relevant premises (Song, Yang, and Anandkumar 2024). The in-context agent pattern is documented by COPRA, an arXiv preprint whose agent asks GPT-4 to propose tactics within a stateful backtracking search, building each prompt from execution feedback, search history, and lemmas retrieved from an external database (Thakur et al. 2023). Whole-proof generation with repair is documented by Baldur, an arXiv preprint whose system generates whole proofs at once rather than one step at a time and adds a fine-tuned repair model (First et al. 2023). Its authors report that giving the model a prior failed proof attempt and the ensuing error message results in proof repair and further improves proof generation, on a benchmark of 6,336 Isabelle/HOL theorems (First et al. 2023). The review maps in-editor suggestion onto the engine hints of `@tactic-planner`, and feedback-driven tactic proposal and error-conditioned repair onto how `@lean-prover` iterates on kernel feedback.

The target system is described at two levels: Lean 4 as a reimplementation of the Lean interactive theorem prover in Lean itself whose users can extend the parser, elaborator, tactics, decision procedures, pretty printer, and code generator, and Mathlib as a community-driven unified library of mathematics formalized in Lean, distinguished by dependently typed foundations, a focus on classical mathematics, and large- and small-scale automation (de Moura and Ullrich 2021; The mathlib Community 2020). Two Lean community resources bear on declaration names in different ways: the Mathlib naming conventions, web documentation written for Lean 4, use descriptive names that often describe the conclusion and, when it is necessary to describe some of the hypotheses, separate them with `of`, so that a theorem A → B → C would be named `C_of_A_of_B`, while the doc-gen4 software repository describes a document generator for Lean 4 that documents an entire library and all files it imports (Lean Mathlib community n.d.; Lean Prover community n.d.). Documentation authoring is represented by the Verso software repository, a Lean documentation authoring tool whose README lists, among the many forms that writing about Lean takes, descriptions of formalization efforts that connect the formal artifact to mathematical text, such as those made with Blueprint (Lean FRO n.d.). For Stage 5 and the Stage 7 name binding, the review infers that each declaration name must be confirmed against generated documentation for the pinned library, because conventions describe how names are formed, not which declarations exist.

Harness-relevant findings:

- **F3.1**: A staged decomposition from informal draft to formal sketch to automated sub-problems is documented and maps by analogy onto Stages 2 and 4, but another abstract reports natural-language guidance inversely related to proof success in chain-of-thought settings, so the value of informal guidance is contested (Jiang et al. 2022a; Yu et al. 2025).
- **F3.2**: Blueprint tooling binds prose to Lean names and derives the dependency graph from declared uses, but its `\leanok` marker is a declaration by the author, to be checked against G-KERNEL (Massot 2021).
- **F3.3**: In-editor copilots, feedback-driven tactic agents, and whole-proof generation with repair are documented interaction patterns (Song, Yang, and Anandkumar 2024; Thakur et al. 2023; First et al. 2023).
- **F3.4**: Name binding should rest on generated documentation, with naming conventions as a guide rather than a source of names (Lean Prover community n.d.; Lean Mathlib community n.d.).

## Provers and Proof Search

Three arXiv preprints apply transformer-based language models to automated theorem proving: GPT-f, an automated prover and proof assistant for the Metamath formalization language whose new short proofs were accepted into the main Metamath library; expert iteration, defined as proof search interleaved with learning, which at the same compute budget is reported to outperform proof search only; and HyperTree Proof Search, which pairs online training of a transformer-based prover with a search algorithm inspired by AlphaZero so that the model learns from previous proof searches (Polu and Sutskever 2020; Polu et al. 2022; Lample et al. 2022).

Three arXiv preprints describe the DeepSeek-Prover systems: the first generates Lean 4 proof data by translating natural-language problems into formal statements and filtering out low-quality statements, reporting whole-proof generation accuracy of 46.3% with 64 samples on the Lean 4 miniF2F test; V1.5 adds reinforcement learning from proof assistant feedback and RMaxTS, a variant of Monte-Carlo tree search that employs an intrinsic-reward-driven exploration strategy; and V2 prompts DeepSeek-V3 to decompose complex problems into a series of subgoals and synthesizes the proofs of resolved subgoals into chain-of-thought data that serves as a cold start for reinforcement learning (Xin et al. 2024a; Xin et al. 2024b; Ren et al. 2025). The V2 abstract reports that DeepSeek-Prover-V2-671B solves 49 out of 658 problems from PutnamBench (Ren et al. 2025). The retrieved abstract does not state a sampling budget for that count (Ren et al. 2025).

Goedel-Prover trains a series of provers, adding each new prover's proofs to the training set for the next, and reports, without reinforcement learning, 57.6% at Pass@32 on miniF2F and 7 PutnamBench problems at Pass@512 (Lin et al. 2025a). Three further arXiv preprints describe models that revise proofs iteratively: Goedel-Prover-V2 builds on the standard expert iteration and reinforcement learning pipeline and adds verifier-guided self-correction that leverages feedback from the Lean compiler; Kimina-Prover Preview, trained with a large-scale reinforcement learning pipeline from Qwen2.5-72B, generates and refines proof steps iteratively; and Seed-Prover, a lemma-style whole-proof reasoning model, refines its proof from Lean feedback, proved lemmas, and self-summarization (Lin et al. 2025b; Wang et al. 2025; Chen et al. 2025). Their abstracts report 84.6% at pass@32 on MiniF2F for Goedel-Prover-V2-8B, 86 PutnamBench problems at pass@184 for Goedel-Prover-V2-32B against a DeepSeek-Prover-V2-671B record, cited in the same abstract, of 47 problems at pass@1024, and 80.7% on miniF2F with pass@8192 for Kimina-Prover Preview (Lin et al. 2025b; Wang et al. 2025). The DeepSeek-Prover-V2 and Goedel-Prover-V2 abstracts thus give different PutnamBench counts for DeepSeek-Prover-V2-671B, 49 and 47, which the review cannot reconcile; every figure should therefore be quoted with source, budget, and date and not compared across papers. Seed-Prover's authors also add a separate geometry reasoning engine to address the lack of geometry support in Lean (Chen et al. 2025). AlphaProof, reported in Nature, learns to find formal proofs through reinforcement learning on millions of auto-formalized problems and, for the hardest problems, learns at inference time from millions of related problem variants; its reported 2024 International Mathematical Olympiad performance, combined with AlphaGeometry 2, was achieved with multi-day computation (Hubert et al. 2025).

A survey in the Journal of Formalized Reasoning calls hammers the methods that automate reasoning over large proof-assistant libraries and names their ingredients as automatic provers that cope with hundreds of axioms, translations of richer logics, relevant-fact selection, and reconstruction of found proofs inside the proof assistant (Blanchette et al. 2016). Two arXiv preprints combine hammers with learned components: LeanHammer joins a neural premise selector trained for use with a hammer in dependent type theory to existing translation and proof reconstruction components, and the selector is reported to let it solve 21% more goals than existing premise selectors, while Thor uses hammers for premise selection, designates all other tasks to language models, and reports solving problems that neither language models nor automated theorem provers solve on their own (Zhu et al. 2025; Jiang et al. 2022b). Premise selection is described as a key bottleneck in theorem proving by LeanDojo, an arXiv preprint presenting an open-source Lean playground that enables programmatic interaction with the proof environment and annotates premises (Yang et al. 2023).

Lean 4 is named explicitly in the abstracts of DeepSeek-Prover, DeepSeek-Prover-V1.5, DeepSeek-Prover-V2, Goedel-Prover, and Kimina-Prover Preview (Xin et al. 2024a; Xin et al. 2024b; Ren et al. 2025; Lin et al. 2025a; Wang et al. 2025). Pantograph and a Lean LSP or MCP server (unverified; not in Phase 1 inventory) are not characterized here; the interaction layers characterized in this review are LeanDojo, above, and Lean Copilot (Yang et al. 2023; Song, Yang, and Anandkumar 2024).

The sources describe language-model proving with search and learning, expert iteration, whole-proof generation with repair or self-correction, and subgoal decomposition with reinforcement learning; the review infers that `@engine-advisor` should record each engine's paradigm and that the paradigm decides whether it needs an interactive proof-state interface or only a compiler. Because the hammer survey counts reconstruction of automatically found proofs inside the proof assistant among a hammer's ingredients, the review takes it as support for recording in `result_trust` that ATP and SMT outputs are hints until they are reconstructed and re-checked by the Lean kernel. Lean Copilot's authors observe that with proof assistants such as Lean the correctness of formal proofs can be rigorously verified, leaving no room for hallucination (Song, Yang, and Anandkumar 2024). Recording LLM-prover outputs as hints until the Lean kernel re-checks them is the charter's policy (§7) rather than a finding of the hammer survey; the review notes only that the policy is consistent with that observation (Song, Yang, and Anandkumar 2024). The stated budgets, from 32 to 8192 samples per problem and multi-day computation, describe published experiments, so `resource_needs` and `local_status` must come from local measurement and no figure here may be transferred to a local run.

Harness-relevant findings:

- **F4.1**: Four generation paradigms are documented, and the review infers that they differ in the interface they need (Polu et al. 2022; Lample et al. 2022; Xin et al. 2024b; Ren et al. 2025; Lin et al. 2025b).
- **F4.2**: Hammers combine premise selection, translation, and proof reconstruction, and both a Lean hammer and a language-model-plus-hammer design are reported; reconstruction supports treating ATP and SMT output as hints, while treating LLM-prover output the same way is charter policy (Blanchette et al. 2016; Zhu et al. 2025; Jiang et al. 2022b; Song, Yang, and Anandkumar 2024).
- **F4.3**: Reported figures are tied to stated budgets that vary widely, and two abstracts report different counts for one system's PutnamBench result, so figures are provenance, not predictions (Ren et al. 2025; Lin et al. 2025a; Lin et al. 2025b; Wang et al. 2025; Hubert et al. 2025).

## Benchmarks

The miniF2F benchmark, introduced in an arXiv preprint, is a cross-system benchmark of formal Olympiad-level problem statements that targets Metamath, Lean, Isabelle (partially), and HOL Light (partially) and consists of 488 statements drawn from the AIME, AMC, and the International Mathematical Olympiad, among other sources (Zheng, Han, and Polu 2021). Prover results are reported on a Lean 4 miniF2F test, but that port is not in the evidence base (unverified; not in Phase 1 inventory), so this review makes no claim about its fidelity to the original statements (Xin et al. 2024a).

PutnamBench, introduced in an arXiv preprint, consists of 1692 hand-constructed formalizations of 640 theorems from the William Lowell Putnam Mathematical Competition, all formalized in Lean 4 and Isabelle and a substantial subset also in Coq (Tsoukalas et al. 2024). The established provers its authors evaluated could only solve a handful of the problems (Tsoukalas et al. 2024). The benchmark paper counts 640 theorems while a later prover abstract reports results out of 658 problems, possibly a different version or counting unit (theorems versus problems), so the evaluation must record which PutnamBench version it samples.

ProofNet, a benchmark for autoformalization and formal proving of undergraduate-level mathematics, consists of 371 examples, each pairing a formal theorem statement in Lean 3 with a natural-language statement and proof (Azerbayev et al. 2023). FormalMATH is described as a large-scale Lean4 benchmark of 5,560 formally verified problems from high-school Olympiad to undergraduate level, built with the human-in-the-loop pipeline described above (Yu et al. 2025). Its evaluation reports limited success for even the strongest models under what the authors call practical sampling budgets, "pronounced domain bias", and an inverse relationship between natural-language solution guidance and proof success in chain-of-thought reasoning scenarios (Yu et al. 2025).

The protocols in these abstracts are success rates under a stated number of samples, written pass@k, and counts of problems solved; the review infers that the evaluation should state metric, split, k, and benchmark version for every figure and never set its own runs beside published figures. No benchmark abstract reviewed here reports a contamination analysis (Zheng, Han, and Polu 2021; Tsoukalas et al. 2024; Azerbayev et al. 2023; Yu et al. 2025). The mis-formalization category rests on FormalMATH alone: it is the only benchmark here whose abstract describes statement validation, and that validation still ends in manual verification after automated filters, so the review keeps mis-formalization in the failure taxonomy for every benchmark the evaluation samples (Yu et al. 2025).

Harness-relevant findings:

- **F5.1**: The benchmarks differ in language, construction, and version: hand-constructed Lean 4, Isabelle, and Coq formalizations in PutnamBench, Lean 3 statements in ProofNet, and pipeline-autoformalized Lean 4 statements in FormalMATH (Tsoukalas et al. 2024; Azerbayev et al. 2023; Yu et al. 2025).
- **F5.2**: Comparable reporting needs metric, split, budget, and version, and published totals for one benchmark already differ across abstracts (Ren et al. 2025; Tsoukalas et al. 2024; Lin et al. 2025b).
- **F5.3**: No reviewed benchmark abstract reports a contamination analysis, and FormalMATH, the only benchmark here describing statement validation, ends that validation in manual verification and reports domain bias and an inverse relationship between natural-language guidance and proof success, all relevant to the failure taxonomy (Yu et al. 2025).

## Proof-Theoretic Representations

The classical primary references for this section are Gentzen's Untersuchungen über das logische Schließen (Gentzen 1935), the chapter Investigations into Logical Deduction in The Collected Papers of Gerhard Gentzen (Gentzen 1969), and Prawitz's Natural Deduction: A Proof-Theoretical Study (Prawitz 1965). None of the three has a retrievable abstract, so no result, including normalization or cut elimination, is attributed to them (Gentzen 1935; Gentzen 1969; Prawitz 1965).

A Cambridge University Press textbook introduces the basic ideas of structural proof theory, with a thorough discussion and comparison of various types of formalization of first-order logic (Troelstra and Schwichtenberg 2000). Its applications include intuitionistic as well as classical first-order logic, modal logic, and linear logic, and its new edition adds sections on cut elimination (Troelstra and Schwichtenberg 2000). Which calculus best suits the named-rule derivations of Stage 3, and which properties a mechanical rule-check would rely on, are not settled by this evidence and are recorded as gaps.

The inventory's TPTP reference is Sutcliffe's article The TPTP Problem Library and Associated Infrastructure: From CNF to TH0, TPTP v6.4.0 in the Journal of Automated Reasoning (Sutcliffe 2017). The SMT-LIB reference is The SMT-LIB Standard: Version 2.6, by Clark Barrett, Pascal Fontaine, and Cesare Tinelli, which the SMT-LIB website lists as the latest official release of version 2.6 (Barrett, Fontaine, and Tinelli 2017). Neither retrieved record states what the standards cover (Sutcliffe 2017; Barrett, Fontaine, and Tinelli 2017). Z3, cvc5, Vampire, and E (unverified; not in Phase 1 inventory) are not characterized. The support that exists is indirect: the hammer survey treats translation into automatic provers' formalisms and reconstruction inside the proof assistant as separate ingredients, which the review takes as the pattern for treating any TPTP or SMT-LIB result as a hint to be reconstructed or re-proved in Lean. For the object-logic-aware `@logic-articulator`, the review infers from a single text spanning intuitionistic, classical, modal, and linear applications only that each Stage 3 derivation record should name its calculus and object logic.

Harness-relevant findings:

- **F6.1**: The retrieved evidence does not establish which calculus suits Stage 3 or what a mechanical rule-check needs; the one grounded reference compares several formalizations (Troelstra and Schwichtenberg 2000).
- **F6.2**: TPTP and SMT-LIB are identified only by title and version, and ATP or SMT output enters the harness as a hint to be reconstructed in Lean, by analogy with hammer reconstruction (Sutcliffe 2017; Barrett, Fontaine, and Tinelli 2017; Blanchette et al. 2016).

## Non-Classical Logics in Proof Assistants

Benzmüller and Paulson present an embedding of quantified multimodal logic in simple type theory, prove its soundness and completeness, and replace modal operators by quantification over a type of possible worlds (Benzmüller and Paulson 2013). Their experiments with existing higher-order theorem provers are reported to demonstrate that the embedding allows automated proofs of statements in these logics, as well as meta properties of them (Benzmüller and Paulson 2013). A later paper verifies the inclusion relations of the modal logic cube in Isabelle/HOL through an embedding of quantified modal logic in classical higher-order logic, with full automation from tools including Sledgehammer and Nitpick (Benzmüller, Claus, and Sultana 2015). Gödel's ontological argument has been formalized and automated with higher-order automated theorem provers, which also confirmed prominent criticism of it (Benzmüller and Woltzenlogel Paleo 2014).

In Lean, Bentzen formalizes a Henkin-style completeness proof for the propositional modal logic S5 that is close to that of Hughes and Cresswell, with source code typechecked with Lean 3.4.2 (Bentzen 2021). The formalized language has false and implication as the only primitive logical connectives and necessity as the only primitive modal operator (Bentzen 2021). The Foundation software repository describes itself as formalizing mathematical logic in Lean 4 (FormalizedFormalLogic contributors n.d.). Its retrieved description does not say which logics it covers, so no coverage claim is made (FormalizedFormalLogic contributors n.d.).

The review classifies the Benzmüller line as shallow semantic embedding, a label none of these abstracts uses, with modal operators turned into quantification over possible worlds inside classical higher-order logic; Bentzen instead fixes an explicit object language and proves a completeness theorem about it, the pattern the charter's deep embedding follows. The review does not infer that automation reported for the higher-order embeddings transfers to a deep embedding in Lean, since none of these abstracts compares the two. For cross-checking a modal-logic pilot, the evidence offers an S5 completeness proof in Lean 3 and a cube-inclusion verification in Isabelle/HOL; neither is in Lean 4, so each can serve as a reference statement to re-prove rather than a library to import.

Harness-relevant findings:

- **F7.1**: Within the inventory, the review distinguishes a semantic embedding in classical higher-order logic, with reported automation, from an explicit object-language formalization with a mechanized completeness proof; the charter's deep embedding follows the second (Benzmüller and Paulson 2013; Bentzen 2021).
- **F7.2**: Mechanized modal metatheory exists in Lean 3 and Isabelle/HOL, and a Lean 4 logic library exists whose coverage is not established by its retrieved description (Bentzen 2021; Benzmüller, Claus, and Sultana 2015; FormalizedFormalLogic contributors n.d.).
- **F7.3**: Deontic, conditional, probabilistic, and relevance logics, all named in the charter, have no embedding source in the inventory, and no retrieved evidence establishes a mechanization of intuitionistic logic as a declared Lean object logic: the one retrieved abstract mentioning intuitionistic logic is a proof-theory textbook's, and the Lean 4 library's coverage is unknown (Troelstra and Schwichtenberg 2000; FormalizedFormalLogic contributors n.d.).

## Implications for Harness Design

Each row is a design inference traceable to a labelled finding; Sources lists only that finding's keys. Claim identifiers for each implication and for the sentences it rests on are recorded in the claim ledger, `reports/01-methods-review.claims.csv`, rather than in the table.

| Implication | Pipeline stage/gate/agent affected | Finding (section ref) | Sources |
|---|---|---|---|
| Charter policy, not a finding: automated alignment scores are advisory inputs to G-FID and do not replace human sign-off; the evidence reports reduced, not removed, manual verification | Stage 1; G-FID; `@fidelity-auditor` | F2.1 (§2) | Gao2024; Lu2024b (preprint evidence) |
| Automated statement formalization may draft Stage 1 stubs, with any reported rate recorded with its benchmark and budget | Stage 1; `@statement-formalizer` | F2.1 (§2) | Gao2024; Lu2024b (preprint evidence) |
| A Stage 1 stub that elaborates is necessary but not sufficient for G-FID | Stage 1; G-FID; `@statement-formalizer` | F2.2 (§2) | Lu2024a (preprint evidence) |
| Charter policy: the fidelity auditor's back-translation, like the reported corpus filters, feeds the human gate and does not replace it | Stage 1; G-FID; `@fidelity-auditor` | F2.3 (§2) | Ying2024; Lin2025a; Yu2025 (preprint evidence) |
| The Stage 2 skeleton may act as an informal draft and each Stage 4 plan as a formal sketch, but because informal guidance is also reported to accompany lower proof success, the evaluation must test whether the skeleton helps | Stage 2; Stage 4; `@proof-strategist`; `@tactic-planner`; Harness Evaluation | F3.1 (§3) | Jiang2022a; Yu2025 (preprint evidence) |
| Blueprint `\leanok` markers are author declarations that must agree with G-KERNEL status | Stage 2; Stage 8; G-KERNEL | F3.2 (§3) | Massot2021 (software) |
| The prover agent iterates on kernel errors, and tactic plans carry in-editor engine hints | Stage 4; Stage 5; `@lean-prover`; `@tactic-planner` | F3.3 (§3) | Song2024; Thakur2023; First2023 (preprint evidence) |
| Every cited Lean name is confirmed against generated documentation for the pinned library | Stage 5; Stage 7; `@lean-informalization` | F3.4 (§3) | LeanFRO_docgen4; Mathlib_naming (software, web documentation) |
| Each engine entry records its generation paradigm and, as the review infers, the interface it requires | `prover-engines.json` `kind`, `strengths`; `@engine-advisor` | F4.1 (§4) | Polu2022; Lample2022; Xin2024b; Ren2025; Lin2025b (preprint evidence) |
| ATP and SMT entries are marked as hints until reconstructed and kernel re-checked; LLM-prover entries are marked the same way as charter policy | `prover-engines.json` `result_trust`; G-KERNEL | F4.2 (§4) | Blanchette2016; Zhu2025; Jiang2022b; Song2024 |
| Resource and installation fields come from local measurement; published budgets are provenance only | `prover-engines.json` `resource_needs`, `local_status`; `@engine-advisor` | F4.3 (§4) | Ren2025; Lin2025a; Lin2025b; Wang2025; Hubert2025 |
| Every evaluation figure states metric, split, budget, and benchmark version | Harness Evaluation | F5.2 (§5) | Ren2025; Tsoukalas2024; Lin2025b (preprint evidence) |
| Mis-formalization remains a failure category for every benchmark sampled, on the strength of FormalMATH's manual verification | Harness Evaluation; G-FID | F5.3 (§5) | Yu2025 (preprint evidence) |
| Stage 3 records name their calculus and object logic; the choice of calculus stays open | Stage 3; `@logic-articulator` | F6.1 (§6) | Troelstra2000 |
| ATP and SMT results are hints to be reconstructed or re-proved in Lean; this concerns result handling only, not counterexample search | `prover-engines.json` `result_trust`; `kind` smt, atp; G-KERNEL | F6.2 (§6) | Sutcliffe2017; Barrett2017; Blanchette2016 |
| Charter decision; evidence neutral: object logics are deeply embedded, and shallow-embedding results and non-Lean-4 metatheory serve as cross-checks and statements to re-prove | `object-logics.json`; `@logic-articulator` | F7.1; F7.2 (§7) | Benzmuller2013; Bentzen2021; Benzmuller2015; FFL_Foundation |

Taken together, the findings support automated checks of meaning, compilation, and search feeding the Lean kernel rather than standing in for it; keeping the human gates alongside those checks is the charter's policy, which these findings neither force nor contradict. The best-supported implications concern Stages 4 and 5 and the prover-engine registry, where several abstracts describe the mechanism. Stage 1 evidence is mixed: automated formalization and alignment are reported at high rates on the authors' benchmarks, no retrieved abstract evaluates back-translation as a fidelity check (the Lean Workbook pipeline translates in both directions, but its abstract presents this as data generation and filtering, not as a fidelity test), and the human G-FID gate rests on charter policy rather than on a finding (Gao et al. 2024; Lu et al. 2024b; Ying et al. 2024). The weakest concern Stage 3 and the handling of TPTP and SMT-LIB results, where the evidence identifies reference works but not their content; the counterexample track has no supporting finding. Because more than half of the cited works are arXiv preprints and all content evidence is abstract-level, each implication should be re-examined when the Harness Specification cites it, and none validates the harness as a whole.

Gaps (harness decisions with no supporting finding):

- Stage 6 and G-CX: no source addresses counterexample search.
- G-AX: no source addresses governance of added axioms, hypotheses, or weakened statements.
- Stage 3: calculus choice and mechanical rule-checking are unsupported by retrieved evidence.
- TPTP and SMT-LIB content, and whether solver output is proof-producing, are not established.
- Non-modal object logics: deontic, conditional, probabilistic, and relevance logics have no source, and no retrieved evidence establishes intuitionistic logic as a declared Lean object logic.
- Informal guidance: whether an informal Stage 2 skeleton helps or hinders Stage 4 is unresolved.
- Interaction layers: LeanDojo and Lean Copilot are documented; Pantograph and a Lean LSP or MCP server are (unverified; not in Phase 1 inventory).
- The fidelity of the Lean 4 port of miniF2F is not assessed.

## References

Azerbayev, Zhangir, Bartosz Piotrowski, Hailey Schoelkopf, Edward W. Ayers, Dragomir Radev, and Jeremy Avigad. 2023. "ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics." arXiv preprint arXiv:2302.12433. https://arxiv.org/abs/2302.12433.

Barrett, Clark, Pascal Fontaine, and Cesare Tinelli. 2017. *The SMT-LIB Standard: Version 2.6*. Technical report, Department of Computer Science, The University of Iowa. https://smt-lib.org/language.shtml.

Bentzen, Bruno. 2021. "A Henkin-Style Completeness Proof for the Modal Logic S5." In *Logic and Argumentation (CLAR 2021)*, 459–67. Lecture Notes in Computer Science. https://doi.org/10.1007/978-3-030-89391-0_25.

Benzmüller, Christoph, Maximilian Claus, and Nik Sultana. 2015. "Systematic Verification of the Modal Logic Cube in Isabelle/HOL." *EPTCS* 186: 27–41. https://doi.org/10.4204/EPTCS.186.5. Also available at https://arxiv.org/abs/1507.08717.

Benzmüller, Christoph, and Lawrence C. Paulson. 2013. "Quantified Multimodal Logics in Simple Type Theory." *Logica Universalis* 7: 7–20. https://doi.org/10.1007/s11787-012-0052-y.

Benzmüller, Christoph, and Bruno Woltzenlogel Paleo. 2014. "Automating Gödel's Ontological Proof of God's Existence with Higher-order Automated Theorem Provers." In *ECAI 2014*. Frontiers in Artificial Intelligence and Applications. https://doi.org/10.3233/978-1-61499-419-0-93.

Blanchette, Jasmin C., Cezary Kaliszyk, Lawrence C. Paulson, and Josef Urban. 2016. "Hammering towards QED." *Journal of Formalized Reasoning* 9. https://doi.org/10.6092/issn.1972-5787/4593. Also available at https://jfr.unibo.it/article/view/4593.

Chen, Luoxin, Jinming Gu, Liankai Huang, Wenhao Huang, Zhicheng Jiang, Allan Jie, Xiaoran Jin, et al. 2025. "Seed-Prover: Deep and Broad Reasoning for Automated Theorem Proving." arXiv preprint arXiv:2507.23726. https://arxiv.org/abs/2507.23726.

de Moura, Leonardo, and Sebastian Ullrich. 2021. "The Lean 4 Theorem Prover and Programming Language." In *Lecture Notes in Computer Science (CADE-28)*, 625–35. https://doi.org/10.1007/978-3-030-79876-5_37.

First, Emily, Markus N. Rabe, Talia Ringer, and Yuriy Brun. 2023. "Baldur: Whole-Proof Generation and Repair with Large Language Models." arXiv preprint arXiv:2303.04910. https://arxiv.org/abs/2303.04910.

FormalizedFormalLogic contributors. n.d. *Foundation: Formalization of Mathematical Logic*. GitHub repository (software). https://github.com/FormalizedFormalLogic/Foundation.

Gao, Guoxiong, Yutong Wang, Jiedong Jiang, Qi Gao, Zihan Qin, Tianyi Xu, and Bin Dong. 2024. "Herald: A Natural Language Annotated Lean 4 Dataset." arXiv preprint arXiv:2410.10878. https://arxiv.org/abs/2410.10878.

Gentzen, Gerhard. 1935. "Untersuchungen über das logische Schließen. I." *Mathematische Zeitschrift* 39: 176–210. https://doi.org/10.1007/BF01201353.

Gentzen, Gerhard. 1969. "Investigations into Logical Deduction." In *The Collected Papers of Gerhard Gentzen*, 68–131. Studies in Logic and the Foundations of Mathematics. https://doi.org/10.1016/s0049-237x(08)70822-x.

Hubert, Thomas, Rishi Mehta, Laurent Sartran, Miklós Z. Horváth, Goran Žužić, Eric Wieser, Aja Huang, et al. 2025. "Olympiad-level formal mathematical reasoning with reinforcement learning." *Nature* 651: 607–13. https://doi.org/10.1038/s41586-025-09833-y.

Jiang, Albert Q., Sean Welleck, Jin Peng Zhou, Wenda Li, Jiacheng Liu, Mateja Jamnik, Timothée Lacroix, Yuhuai Wu, and Guillaume Lample. 2022a. "Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs." arXiv preprint arXiv:2210.12283. https://arxiv.org/abs/2210.12283.

Jiang, Albert Q., Wenda Li, Szymon Tworkowski, Konrad Czechowski, Tomasz Odrzygóźdź, Piotr Miłoś, Yuhuai Wu, and Mateja Jamnik. 2022b. "Thor: Wielding Hammers to Integrate Language Models and Automated Theorem Provers." arXiv preprint arXiv:2205.10893. https://arxiv.org/abs/2205.10893.

Lample, Guillaume, Marie-Anne Lachaux, Thibaut Lavril, Xavier Martinet, Amaury Hayat, Gabriel Ebner, Aurélien Rodriguez, and Timothée Lacroix. 2022. "HyperTree Proof Search for Neural Theorem Proving." arXiv preprint arXiv:2205.11491. https://arxiv.org/abs/2205.11491.

Lean FRO. n.d. *Verso: Lean documentation authoring tool*. GitHub repository (software). https://github.com/leanprover/verso.

Lean Mathlib community. n.d. "Mathlib naming conventions." Lean community website (web documentation). https://leanprover-community.github.io/contribute/naming.html.

Lean Prover community. n.d. *doc-gen4: Document Generator for Lean 4*. GitHub repository (software). https://github.com/leanprover/doc-gen4.

Lin, Yong, Shange Tang, Bohan Lyu, Jiayun Wu, Hongzhou Lin, Kaiyu Yang, Jia Li, et al. 2025a. "Goedel-Prover: A Frontier Model for Open-Source Automated Theorem Proving." arXiv preprint arXiv:2502.07640. https://arxiv.org/abs/2502.07640.

Lin, Yong, Shange Tang, Bohan Lyu, Ziran Yang, Jui-Hui Chung, Haoyu Zhao, Lai Jiang, et al. 2025b. "Goedel-Prover-V2: Scaling Formal Theorem Proving with Scaffolded Data Synthesis and Self-Correction." arXiv preprint arXiv:2508.03613. https://arxiv.org/abs/2508.03613.

Lu, Jianqiao, Yingjia Wan, Zhengying Liu, Yinya Huang, Jing Xiong, Chengwu Liu, Jianhao Shen, et al. 2024a. "Process-Driven Autoformalization in Lean 4." arXiv preprint arXiv:2406.01940. https://arxiv.org/abs/2406.01940.

Lu, Jianqiao, Yingjia Wan, Yinya Huang, Jing Xiong, Zhengying Liu, and Zhijiang Guo. 2024b. "FormalAlign: Automated Alignment Evaluation for Autoformalization." arXiv preprint arXiv:2410.10135. https://arxiv.org/abs/2410.10135.

Massot, Patrick. 2021. *leanblueprint*. GitHub repository (software). https://github.com/PatrickMassot/leanblueprint.

The mathlib Community. 2020. "The Lean Mathematical Library." In *Proceedings of the 9th ACM SIGPLAN International Conference on Certified Programs and Proofs (CPP 2020)*, 367–81. https://doi.org/10.1145/3372885.3373824.

Polu, Stanislas, Jesse Michael Han, Kunhao Zheng, Mantas Baksys, Igor Babuschkin, and Ilya Sutskever. 2022. "Formal Mathematics Statement Curriculum Learning." arXiv preprint arXiv:2202.01344. https://arxiv.org/abs/2202.01344.

Polu, Stanislas, and Ilya Sutskever. 2020. "Generative Language Modeling for Automated Theorem Proving." arXiv preprint arXiv:2009.03393. https://arxiv.org/abs/2009.03393.

Prawitz, Dag. 1965. *Natural Deduction: A Proof-Theoretical Study*. Stockholm Studies in Philosophy 3. Stockholm: Almqvist & Wiksell. https://doi.org/10.2307/2271676.

Ren, Z. Z., Zhihong Shao, Junxiao Song, Huajian Xin, Haocheng Wang, Wanjia Zhao, Liyue Zhang, et al. 2025. "DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition." arXiv preprint arXiv:2504.21801. https://arxiv.org/abs/2504.21801.

Song, Peiyang, Kaiyu Yang, and Anima Anandkumar. 2024. "Lean Copilot: Large Language Models as Copilots for Theorem Proving in Lean." arXiv preprint arXiv:2404.12534. https://arxiv.org/abs/2404.12534.

Sutcliffe, Geoff. 2017. "The TPTP Problem Library and Associated Infrastructure: From CNF to TH0, TPTP v6.4.0." *Journal of Automated Reasoning* 59: 483–502. https://doi.org/10.1007/s10817-017-9407-7.

Thakur, Amitayush, George Tsoukalas, Yeming Wen, Jimmy Xin, and Swarat Chaudhuri. 2023. "An In-Context Learning Agent for Formal Theorem-Proving." arXiv preprint arXiv:2310.04353. https://arxiv.org/abs/2310.04353.

Troelstra, A. S., and H. Schwichtenberg. 2000. *Basic Proof Theory*. Cambridge: Cambridge University Press. https://doi.org/10.1017/CBO9781139168717.

Tsoukalas, George, Jasper Lee, John Jennings, Jimmy Xin, Michelle Ding, Michael Jennings, Amitayush Thakur, and Swarat Chaudhuri. 2024. "PutnamBench: Evaluating Neural Theorem-Provers on the Putnam Mathematical Competition." arXiv preprint arXiv:2407.11214. https://arxiv.org/abs/2407.11214.

van Doorn, Floris, Patrick Massot, and Oliver Nash. 2023. "Formalising the h-Principle and Sphere Eversion." In *Proceedings of the 12th ACM SIGPLAN International Conference on Certified Programs and Proofs (CPP 2023)*. https://doi.org/10.1145/3573105.3575688.

Wang, Haiming, Mert Unsal, Xiaohan Lin, Mantas Baksys, Junqi Liu, Marco Dos Santos, Flood Sung, et al. 2025. "Kimina-Prover Preview: Towards Large Formal Reasoning Models with Reinforcement Learning." arXiv preprint arXiv:2504.11354. https://arxiv.org/abs/2504.11354.

Wu, Yuhuai, Albert Q. Jiang, Wenda Li, Markus N. Rabe, Charles Staats, Mateja Jamnik, and Christian Szegedy. 2022. "Autoformalization with Large Language Models." arXiv preprint arXiv:2205.12615. https://arxiv.org/abs/2205.12615.

Xin, Huajian, Daya Guo, Zhihong Shao, Zhizhou Ren, Qihao Zhu, Bo Liu, Chong Ruan, Wenda Li, and Xiaodan Liang. 2024a. "DeepSeek-Prover: Advancing Theorem Proving in LLMs through Large-Scale Synthetic Data." arXiv preprint arXiv:2405.14333. https://arxiv.org/abs/2405.14333.

Xin, Huajian, Z. Z. Ren, Junxiao Song, Zhihong Shao, Wanjia Zhao, Haocheng Wang, Bo Liu, et al. 2024b. "DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search." arXiv preprint arXiv:2408.08152. https://arxiv.org/abs/2408.08152.

Yang, Kaiyu, Aidan M. Swope, Alex Gu, Rahul Chalamala, Peiyang Song, Shixing Yu, Saad Godil, Ryan Prenger, and Anima Anandkumar. 2023. "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models." arXiv preprint arXiv:2306.15626. https://arxiv.org/abs/2306.15626.

Ying, Huaiyuan, Zijian Wu, Yihan Geng, Zheng Yuan, Dahua Lin, and Kai Chen. 2024. "Lean Workbook: A large-scale Lean problem set formalized from natural language math problems." arXiv preprint arXiv:2406.03847. https://arxiv.org/abs/2406.03847.

Yu, Zhouliang, Ruotian Peng, Keyi Ding, Yizhe Li, Zhongyuan Peng, Minghao Liu, Yifan Zhang, et al. 2025. "FormalMATH: Benchmarking Formal Mathematical Reasoning of Large Language Models." arXiv preprint arXiv:2505.02735. https://arxiv.org/abs/2505.02735.

Zheng, Kunhao, Jesse Michael Han, and Stanislas Polu. 2021. "MiniF2F: a cross-system benchmark for formal Olympiad-level mathematics." arXiv preprint arXiv:2109.00110. https://arxiv.org/abs/2109.00110.

Zhu, Thomas, Joshua Clune, Jeremy Avigad, Albert Qiaochu Jiang, and Sean Welleck. 2025. "Premise Selection for a Lean Hammer." arXiv preprint arXiv:2506.07477. https://arxiv.org/abs/2506.07477.
