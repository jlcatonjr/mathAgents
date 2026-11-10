# P3 finite Dutch book: informalization (Stage 7)

> **Written by:** `@lean-informalization` · 2026-10-01; bindings re-checked 2026-10-23; provenance re-pointed 2026-11-10 to the public history (commit `e760f696`).
> **Target reader:** working mathematicians and philosophers of science who know finite probability and
> the Dutch Book literature, and who want to know exactly what was kernel-checked and under which
> choices. This is statement-level narration. It does not narrate proof internals.
> **Ground truth:** `lean/MathAgents/P3DutchBook.lean` (namespace `MathAgents.P3DutchBook`) and the library
> `lean/MathAgents/FiniteProbability.lean` (namespace `MathAgents.FiniteProbability`). Statuses and axioms
> for the twelve `MathAgents.P3DutchBook` declarations are from the G-KERNEL run frozen in
> `reports/dossiers/p3-dutch-book/kernel-snapshot.json` (verdict PASS, checked 2026-11-10T19:11:05Z,
> Lean 4.34.1, commit `e760f696`, `dirty: false`, `source_sha256` `aec56891…796289`). That snapshot covers
> only the `MathAgents.P3DutchBook` namespace, not the library. Statuses and axioms for the
> `MathAgents.FiniteProbability` bindings are from the G-KERNEL report `reports/kernel/latest.json` (verdict
> PASS, checked 2026-11-10T19:11:05+00:00, Lean 4.34.1, `dirty: false`, `source_sha256` `aec56891…796289`).
> Re-checked 2026-10-23 against that date's report (private history): every binding below has status `proved` and the same three axioms in that report,
> and the twelve `MathAgents.P3DutchBook` declarations have the same statuses, axioms and statement
> fingerprints there as in the snapshot. The orchestrator's G-NAME run (`scripts/check_lean_bindings.py`)
> and `validate_dossier.py --require-stage p3-dutch-book 7` both passed on 2026-10-23.
> **Binding convention:** every narrated statement carries a Lean binding tag with the fully-qualified
> declaration name and a status, and the status is the kernel report's. For a `def` or a `structure` field, the report's `proved` means
> that the declaration was elaborated and kernel-checked with no open marker. It does not mean that the
> definition is the right one; that is the G-FID question, recorded in `statement.md` and `back-translation.md`.

## 1. Setting and notation

Throughout, Ω is a type with finitely many elements (`[Fintype Ω]`). Ω may be empty: no `Nonempty Ω`
is assumed anywhere in the three theorems (G-AX-P3-15, `allow-empty`). Events are all subsets of Ω
(`Set Ω`), so the event space is the whole power set. A betting-quotient function is any
q : 𝒫(Ω) → ℝ, defined on every event (P3-16, `total`). For an event A, 1_A(ω) denotes Mathlib's
`A.indicator (fun _ => 1) ω`, which is 1 if ω ∈ A and 0 otherwise.

| Lean name | Notation in this document |
|---|---|
| `MathAgents.FiniteProbability.IsFinitelyAdditiveProb q` | q is a finitely additive probability |
| `MathAgents.FiniteProbability.Bet Ω`, fields `event`, `stake` | a bet (A, S) |
| `MathAgents.FiniteProbability.payoff q b ω` | payoff of bet b in state ω |
| `MathAgents.FiniteProbability.netPayoff q book ω` | net payoff of a book in state ω |
| `MathAgents.FiniteProbability.IsDutchBook q book` | the book is a Dutch book against q |

## 2. Library definitions

**Finitely additive probability.** A function pr : 𝒫(Ω) → ℝ is a finitely additive probability when
it satisfies three conditions:

- non-negativity: 0 ≤ pr(A) for every event A [Lean: MathAgents.FiniteProbability.IsFinitelyAdditiveProb.nonneg | proved];
- normalization on the whole space: pr(Ω) = 1 [Lean: MathAgents.FiniteProbability.IsFinitelyAdditiveProb.univ_eq_one | proved];
- additivity on disjoint pairs: pr(A ∪ B) = pr(A) + pr(B) whenever A and B are disjoint [Lean: MathAgents.FiniteProbability.IsFinitelyAdditiveProb.union_of_disjoint | proved].

The library also derives pr(∅) = 0 from these three [Lean: MathAgents.FiniteProbability.IsFinitelyAdditiveProb.empty | proved].
The "tautology" of the survey's normalization axiom is rendered extensionally as the event Ω (P3-3).
Non-negativity is a separate axiom (P3-11). Additivity is binary, on disjoint pairs (P3-12).

**Bet.** A bet is a pair (A, S): an event A [Lean: MathAgents.FiniteProbability.Bet.event | proved] and a
real stake S [Lean: MathAgents.FiniteProbability.Bet.stake | proved]. The stake is unrestricted: positive,
negative or zero (P3-2, `either-sign`).

**Payoff.** The payoff to the agent of the bet (A, S) at quotients q in state ω is
S · (1_A(ω) − q(A)) [Lean: MathAgents.FiniteProbability.payoff | proved]. The agent pays S·q(A) and receives
S if A occurs, at the single price q(A) for both signs of S (P3-1, P3-8 `fair-only`). Reversing the sign
of the stake negates the payoff: the payoff of (A, −S) is minus the payoff of (A, S) in every state
[Lean: MathAgents.FiniteProbability.payoff_neg_stake | proved].

**Book and net payoff.** A book is a finite list of bets (P3-5); repeated events, bets on ∅ or Ω and zero
stakes are allowed (P3-13). Its net payoff in state ω is the sum of the payoffs of its bets
[Lean: MathAgents.FiniteProbability.netPayoff | proved].

**Dutch book.** A book is a Dutch book against q when its net payoff to the agent is strictly negative
in every state ω ∈ Ω [Lean: MathAgents.FiniteProbability.IsDutchBook | proved]. This is the strict notion
of sure loss (P3-6), and the loss falls on the agent who holds q (P3-14). When Ω is non-empty the empty
book is not a Dutch book against any q [Lean: MathAgents.FiniteProbability.not_isDutchBook_nil | proved];
that lemma carries the hypothesis `[Nonempty Ω]`, which the three theorems below do not.

**Point masses (used in the proof of R2 only).** For a weighting w : Ω → ℝ, pointMass w (A) is the sum of
w over the states in A [Lean: MathAgents.FiniteProbability.pointMass | proved]. If w ≥ 0 and the weights sum
to 1, it is a finitely additive probability
[Lean: MathAgents.FiniteProbability.pointMass_isFinitelyAdditiveProb | proved]. If the weights sum to 1
(non-negativity is not assumed here), every finite book has w-expected net payoff 0 at the quotients
pointMass w [Lean: MathAgents.FiniteProbability.expected_netPayoff_pointMass | proved].

## 3. The theorems

All three theorems quantify universally, at the outermost level, over a finite type Ω (`[Fintype Ω]`,
possibly empty) and an arbitrary q : 𝒫(Ω) → ℝ. The book may depend on q. No constant depends on the
state: a single book must lose in every state.

### R1, the forward direction

**Theorem.** Let Ω be finite and q : 𝒫(Ω) → ℝ. If q is **not** a finitely additive probability, then
there is a finite book that is a Dutch book against q: some list of bets (A₁, S₁), …, (Aₙ, Sₙ) with
Σᵢ Sᵢ(1_{Aᵢ}(ω) − q(Aᵢ)) < 0 for every ω ∈ Ω [Lean: MathAgents.P3DutchBook.dutchBook_R1 | proved].

Author's docstring (exposition, attributed to the docstring of `dutchBook_R1`): "Reading R1 (forward):
quotients that are not a finitely additive probability admit a Dutch book."

Remarks.
- The book in the proof has at most three bets, one case per failed axiom: one bet against a negative
  quotient [Lean: MathAgents.P3DutchBook.Aux.book_neg | proved], one bet on Ω when q(Ω) ≠ 1
  [Lean: MathAgents.P3DutchBook.Aux.book_univ | proved], and three bets on A ∪ B, A, B when additivity
  fails for a disjoint pair [Lean: MathAgents.P3DutchBook.Aux.book_additivity | proved]. The case split is
  [Lean: MathAgents.P3DutchBook.Aux.not_fap_cases | proved]. The theorem itself asserts only existence.
- **[needs human check] (G6/G7, ignored binder).** The signature carries `[Fintype Ω]`, but the R1 proof
  makes no use of finiteness of Ω, as `statement.md` H5 anticipated. The hypothesis is part of the
  statement (it encodes P3-7) and the narration keeps it; the result does not show that finiteness is
  needed for R1.
- If Ω is empty the conclusion is trivially met by any book, the empty one included (`statement.md` H6).

### R2, the converse

**Theorem.** Let Ω be finite and q : 𝒫(Ω) → ℝ. If q **is** a finitely additive probability, then no
finite book is a Dutch book against q: for every finite list of bets there is at least one state ω
(which may depend on the book) in which the agent's net payoff is ≥ 0
[Lean: MathAgents.P3DutchBook.converse_R2 | proved].

Author's docstring (exposition, attributed to the docstring of `converse_R2`): "Reading R2 (the rough
converse): finitely additive probability quotients admit no Dutch book."

Remarks.
- The proof route represents q as the point-mass probability of its singleton values on finite Ω
  [Lean: MathAgents.P3DutchBook.Aux.represent | proved], uses that the singleton values sum to 1
  [Lean: MathAgents.P3DutchBook.Aux.weights_sum | proved], and that a non-negative weighting summing to 1
  gives a strictly negative weighted sum of a strictly negative function
  [Lean: MathAgents.P3DutchBook.Aux.weighted_neg | proved]. The representation lemma is a proof step, not a
  hypothesis: R2 quantifies over every finitely additive q, not only point-mass ones (P3-10).
- The books range over **arbitrary events**, not over one partition.
- If Ω is empty the hypothesis cannot hold (∅ = Ω forces q(∅) = 0 and q(∅) = 1), and R2 is vacuous.

### R3, both directions in one formulation

**Theorem.** Let Ω be finite and q : 𝒫(Ω) → ℝ. There exists a finite Dutch book against q **if and only
if** q is not a finitely additive probability [Lean: MathAgents.P3DutchBook.dutchBook_R3 | proved].

Author's docstring (exposition, attributed to the docstring of `dutchBook_R3`): "Reading R3 (both
directions, one formulation)." Bets, books, sure loss and the axioms are the same definitions in R1, R2
and R3. When Ω is empty both sides of the equivalence are true.

## 4. Sources and attribution

**De Finetti 1937 (primary, open, French).** Quotations are verbatim from
`sources/definetti-1937-extract.md`, with printed page numbers. English renderings are ours and are not
de Finetti's words.

- The bet, stakes of either sign (p. 6): « […] une somme quelconque S (positive ou négative)
  subordonnée à l'arrivée d'un événement donné, E, avec la possession de la somme *p*S […] ».
  [our translation] "an arbitrary sum S (positive or negative), conditional on the occurrence of a given
  event E, for possession of the sum *p*S". This supports the payoff S(1_A − q(A)) and P3-2.
- Coherence (p. 7): « ou bien il est possible de parier avec lui en s'assurant de gagner à coup sûr, ou
  bien cette possibilité n'existe pas. » [our translation] "either it is possible to bet with him so as to
  be sure of winning, or no such possibility exists." De Finetti states the opponent's sure win; R1–R3
  state the agent's sure loss. With either-sign stakes the two are interchangeable by negating every stake.
- Forward direction on a complete class (pp. 7–8): « si ce déterminant n'est pas nul, on peut fixer le Sₕ
  de façon que les Gₕ aient des valeurs arbitraires, en particulier toutes positives, contrairement à la
  condition de cohérence ». [our translation] "If this determinant is non-zero, the Sₕ can be chosen so
  that the Gₕ take arbitrary values, in particular all positive ones, contrary to the condition of
  coherence." His argument yields normalization over one partition, with additivity called
  « le corollaire immédiat » (p. 8). He gives no betting argument for non-negativity (asserted, pp. 8, 10).
  R1 covers non-negativity and pairwise additivity as well, so it goes beyond his text.
- Converse on one partition (p. 8): « Cette condition nécessaire pour réaliser la cohérence est aussi
  suffisante, parce que, si elle est satisfaite, on a identiquement (quels que soient les enjeux Sₕ)
  Σₕ₌₁ⁿ *p*ₕGₕ = 0, et les Gₕ ne peuvent jamais, par conséquent, être tous positifs. » [our translation]
  "This condition, necessary for coherence, is also sufficient, because when it holds we have
  identically (whatever the stakes Sₕ) Σ pₕGₕ = 0, and so the Gₕ can never all be positive." This is
  partial primary support for R2 (D33): his proof covers books on one partition only, and R2 quantifies
  over books on arbitrary events.

**Vineberg 2022 (survey, flagged per D29).** The general converse is formalized per Vineberg 2022 (the
*Stanford Encyclopedia of Philosophy* entry "Dutch Book Arguments", as quoted in `interpretation.md` §1),
because Kemeny 1955 and Lehman 1955 are paywalled. The entry states the converse, "roughly stated", as:
"For a set of betting quotients that obeys the probability axioms, there is no set of bets (with those
quotients) that guarantees a sure loss (win) to one side" (Vineberg 2022). Fidelity to the original
authors' wording of the general converse is an open item.

## 5. Load-bearing choices

- **Strict sure loss (P3-6) is required for R2 and R3.** Under weak sure loss (≤ 0 in every state, < 0 in
  some) R2 would be false: with Ω = {a, b}, q{a} = 1, q{b} = 0, the book consisting of the single bet
  ({b}, −1) pays 0 at a and −1 at b (`stage1-audit.md`, finding 1). This is a paper counterexample from
  the audit, not a kernel-checked statement. De Finetti's « positives » is read as strict (extract,
  reading of (b)); he does not state the distinction in words.
- **Either-sign stakes (P3-2) are required for R1.** With positive-only stakes the agent can only buy,
  and a negative quotient q(A) < 0 cannot be exploited (`statement.md` §6). The R1 book against a
  negative quotient uses stake −1.

## 6. What these results do not establish

- **R4 and R5 are deferred** (D30): no converse with strengthened axioms and no converse with a
  restricted notion of sure loss is stated or checked.
- **Kemeny 1955 and Lehman 1955 were not consulted** (paywalled, D29). Nothing here is claimed to match
  their formulations.
- **Partition versus arbitrary books.** De Finetti proves both directions for bets on one finite complete
  class. R1–R3 quantify over finite books on arbitrary events of a finite power set. These are different
  statements, and neither the narration nor the Lean code claims that the results are his theorem as he
  stated it.
- **Settings outside the formulation.** Nothing is claimed for infinite Ω, infinitely many bets,
  quotients defined on a class not closed under the connectives (P3-4, P3-16), weak sure loss, bets
  accepted at favourable as well as fair prices (P3-8), or modal normalization (P3-3). The survey's
  reported counterexamples to the rough converse are not engaged.
- The Stage 6 z3 searches (`stage6-search.md`) are hints only. The truth of R1–R3 rests on the kernel
  check.

## 7. Axiom envelope and open items (G4)

- **Axioms.** Every declaration narrated above depends on exactly `propext`, `Classical.choice` and
  `Quot.sound`: for the `MathAgents.P3DutchBook` declarations per the snapshot `kernel-snapshot.json`, and
  for the `MathAgents.FiniteProbability` declarations per the 2026-11-10 G-KERNEL report
  `reports/kernel/latest.json`. These are the base axioms of `references/axiom-allowlist.json`, whose
  `approved_axioms` list is empty.
- **No `sorry`, no `axiom` declaration, no `native_decide`** in either source file. The 2026-11-10 G-KERNEL
  report (`reports/kernel/latest.json`) has `findings: []`, and none of its `open_markers` is in
  `lean/MathAgents/P3DutchBook.lean` or `lean/MathAgents/FiniteProbability.lean`.
- **Provenance.** The `MathAgents.P3DutchBook` statuses and axioms come from the G-KERNEL run produced on a
  clean tree at commit `e760f696` (checked 2026-11-10T19:11:05Z) and frozen in `kernel-snapshot.json`, which
  covers only that namespace; its `source_sha256` (`aec56891…796289`) identifies the checked sources. The
  `MathAgents.FiniteProbability` statuses and axioms come from `reports/kernel/latest.json`, a G-KERNEL run
  on a clean tree at commit `e760f696` (checked 2026-11-10T19:11:05+00:00, `source_sha256`
  `aec56891…796289`). That report is untracked and regenerated by each recording run; it is not frozen.
- **Open items.**
  - Fidelity of the general converse to Kemeny 1955 and Lehman 1955 (D29; `statement.md` §6).
  - The `[needs human check]` on R1's unused `[Fintype Ω]` binder (§3), for `@technical-validator`.
  - External citations (de Finetti 1937, Vineberg 2022) go to `@reference-manager` before any compiled
    deliverable.

## References

- de Finetti, Bruno. "La prévision : ses lois logiques, ses sources subjectives." *Annales de l'institut
  Henri Poincaré* 7, no. 1 (1937): 1–68. Extract: `sources/definetti-1937-extract.md`.
- Vineberg, Susan. "Dutch Book Arguments." *Stanford Encyclopedia of Philosophy*, 2022. As quoted in
  `interpretation.md`.
