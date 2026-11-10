# Stage 1 statement — P3 finite Dutch book

> **Superseded (Stage 8, 2026-10-01):** this is the historical Stage 1 record. The statements are now proved
> in the kernel and live in `lean/MathAgents/P3DutchBook.lean`; see `README.md` and `kernel-snapshot.json`.
>
> **Drafted by:** `@statement-formalizer` · 2026-10-01 · **Status:** draft for the human G-FID review. Nothing here is claimed correct, faithful or proved; every Lean body is `sorry`.
> **Lean stub:** `lean/MathAgentsWIP/P3DutchBook.lean`, namespace `MathAgents.P3DutchBook`, built on the proved library `MathAgents.FiniteProbability` (object logic `finite-probability`, D31).
> **Sources (D29):** de Finetti 1937 (open, French) is primary for the bet, coherence, the forward direction and his partition converse; quotations are verbatim from `sources/definetti-1937-extract.md`, translations marked. The general converse is stated per Vineberg 2022 (survey, flagged), because Kemeny 1955 and Lehman 1955 are paywalled.
> **Readings formalized (D30, `readings.selected`):** R1, R2, R3. R4 and R5 are deferred.

## 0. Source text

**The bet** (de Finetti 1937, p. 6): « Supposons qu'un individu soit obligé d'évaluer le prix *p* pour lequel il serait disposé d'échanger la possession d'une somme quelconque S (positive ou négative) subordonnée à l'arrivée d'un événement donné, E, avec la possession de la somme *p*S ; nous dirons par définition que ce nombre *p* est la mesure du degré de probabilité attribué par l'individu considéré à l'événement E […] »

**A book's gain** (p. 7): « si l'on fixe les enjeux (positifs ou négatifs) S₁, S₂, …, Sₙ, les gains dans les *n* cas possibles seront les différences entre l'enjeu du pari gagné et la somme des *n* mises payées Gₕ = Sₕ − Σᵢ₌₁ⁿ pᵢSᵢ. »

**Coherence** (p. 7): « ou bien il est possible de parier avec lui en s'assurant de gagner à coup sûr, ou bien cette possibilité n'existe pas. Dans le premier cas on doit dire évidemment que l'évaluation de la probabilité donnée par cet individu contient une incohérence, une contradiction intrinsèque ; dans l'autre cas, nous dirons que l'individu est cohérent. »

**Forward direction** (pp. 7–8): « si ce déterminant n'est pas nul, on peut fixer le Sₕ de façon que les Gₕ aient des valeurs arbitraires, en particulier toutes positives, contrairement à la condition de cohérence ; par conséquent, la cohérence oblige à imposer la condition *p*₁ + *p*₂ + … + *p*ₙ = 1. » And (p. 8): « *la probabilité de la somme logique de n événements incompatibles est la somme de leurs probabilités*, n'en est que le corollaire immédiat. »

**Partition converse** (p. 8): « Cette condition nécessaire pour réaliser la cohérence est aussi suffisante, parce que, si elle est satisfaite, on a identiquement (quels que soient les enjeux Sₕ) Σₕ₌₁ⁿ *p*ₕGₕ = 0, et les Gₕ ne peuvent jamais, par conséquent, être tous positifs. » and « toutes les évaluations de probabilité qui attribuent à *p*₁, *p*₂, …, *p*ₙ des valeurs quelconques non négatives et de somme égale à l'unité sont des évaluations admissibles ».

[our translation, p. 8] "If this determinant is non-zero, the Sₕ can be chosen so that the Gₕ take arbitrary values, in particular all positive ones, contrary to the condition of coherence. Hence coherence requires p₁ + … + pₙ = 1. This necessary condition is also sufficient, because when it holds we have identically (whatever the stakes) Σ pₕGₕ = 0, and so the Gₕ can never all be positive."

**Survey statements** (Vineberg 2022, as quoted in `interpretation.md` §1): Dutch Book theorem: "Given a set of betting quotients that fails to satisfy the probability axioms, there is a set of bets with those quotients that guarantees a net loss to one side." Converse, "roughly stated": "For a set of betting quotients that obeys the probability axioms, there is no set of bets (with those quotients) that guarantees a sure loss (win) to one side." Axioms: 0 ≤ pr(A); pr(A) = 1 if A is a tautology; pr(A∨B) = pr(A) + pr(B) for incompatible A, B.

## 1. Common setting and definitions (library `MathAgents.FiniteProbability`)

Fixed and universally quantified at the outermost level of every theorem:

- Ω : a type with `[Fintype Ω]` (finitely many states). No `Nonempty Ω` (see hazard H6).
- Events: all of `Set Ω` (X = the power set of Ω, a finite Boolean algebra).
- q : `Set Ω → ℝ`, the agent's betting quotient for every event.

Definitions used (all from the library; none new in `MathAgents.P3DutchBook`):

- `IsFinitelyAdditiveProb q` ⟺ (∀ A, 0 ≤ q A) ∧ q Ω = 1 ∧ (∀ A B, A ∩ B = ∅ → q (A ∪ B) = q A + q B).
- A bet b = (A, S) with A ⊆ Ω and S ∈ ℝ (either sign). `payoff q b ω = S · (1_A(ω) − q A)`.
- A book is a finite list b₁, …, bₙ; `netPayoff q book ω = Σᵢ payoff q bᵢ ω`.
- `IsDutchBook q book` ⟺ ∀ ω ∈ Ω, netPayoff q book ω < 0 (sure loss to the agent holding q).

## 2. Theorems

### `dutchBook_R1` (reading R1: forward)

For every finite Ω and every q : 𝒫(Ω) → ℝ: if q is not a finitely additive probability, then there exist n ∈ ℕ, events A₁, …, Aₙ ⊆ Ω and stakes S₁, …, Sₙ ∈ ℝ such that for every ω ∈ Ω, Σᵢ Sᵢ(1_{Aᵢ}(ω) − q Aᵢ) < 0.

```lean
theorem dutchBook_R1 {Ω : Type*} [Fintype Ω] (q : Set Ω → ℝ)
    (hq : ¬ IsFinitelyAdditiveProb q) :
    ∃ book : List (Bet Ω), IsDutchBook q book
```

### `converse_R2` (reading R2: the rough converse)

For every finite Ω and every q : 𝒫(Ω) → ℝ: if q is a finitely additive probability, then there is no finite book (A₁, S₁), …, (Aₙ, Sₙ) with Σᵢ Sᵢ(1_{Aᵢ}(ω) − q Aᵢ) < 0 for every ω ∈ Ω.

```lean
theorem converse_R2 {Ω : Type*} [Fintype Ω] (q : Set Ω → ℝ)
    (hq : IsFinitelyAdditiveProb q) :
    ¬ ∃ book : List (Bet Ω), IsDutchBook q book
```

The survey calls this converse rough and reports counterexamples in other formulations; it is stated as worded, without R4/R5 restrictions. In this formulation (finite Ω, q total on `Set Ω`, finitely many bets, strict sure loss) both Stage 1 audits expect it to be **provable**; a G-CX refutation is not anticipated. Vineberg's counterexamples must rely on settings outside the selected choices (weak sure loss, a non-closed X, infinite books, modal normalization). De Finetti asserts the partition case (p. 8); this statement quantifies over books on arbitrary events, which goes beyond his proof (extract, reading of (d)).

### `dutchBook_R3` (reading R3: both directions, one formulation)

For every finite Ω and every q : 𝒫(Ω) → ℝ: (∃ a finite book that is a sure loss at q) ⟺ q is not a finitely additive probability.

```lean
theorem dutchBook_R3 {Ω : Type*} [Fintype Ω] (q : Set Ω → ℝ) :
    (∃ book : List (Bet Ω), IsDutchBook q book) ↔ ¬ IsFinitelyAdditiveProb q
```

All three share one formulation of bet, book, sure loss and axioms, as R3 requires.

## 3. Preference → encoding map (`preferences.toml` `[gax]`)

| Setting | Choice | Encoding |
|---|---|---|
| P3-1 | `S(1_A - q)` | `payoff q b ω = b.stake * (b.event.indicator 1 ω - q b.event)` |
| P3-2 | `either-sign` | `Bet.stake : ℝ`, unrestricted |
| P3-3 | `tautologies` | `univ_eq_one : q Set.univ = 1` (the tautology is the event Ω) |
| P3-4 | `boolean-algebra` | events = all of `Set Ω`; q total on it |
| P3-5 | `finitely-many` | `book : List (Bet Ω)` |
| P3-6 | `negative-in-every-state` | `IsDutchBook q book := ∀ ω, netPayoff q book ω < 0` |
| P3-7 | `finite` | `[Fintype Ω]`, so `Set Ω` is finite |
| P3-8 | `fair-only` | every bet in the book is priced at the agent's own `q b.event`, one price for both stake signs |

## 4. Formalization hazards (checklist)

- **H1 ℕ/ℤ arithmetic, division:** none; all quantities are real. No division.
- **H2 Coercions:** only the indicator value `(1 : ℝ)`; no ℕ→ℝ casts in any statement.
- **H3 Finset vs Set:** events are `Set Ω`; membership enters only through `Set.indicator` (noncomputable, no `DecidablePred` arguments). `Fintype Ω` is the only instance.
- **H4 Quantifier order:** q is fixed before the book; the book may depend on q (R1). In R2, the negated existential ranges over all finite books at that q. No constant depends on ω: a single book must lose in every state.
- **H5 `[Fintype Ω]`** is written in each signature (not a section `variable`, which Lean would drop as unused). It encodes P3-7, not a proof need: the forward direction makes no use of finiteness of Ω, and whether R2 needs it is a Stage 2 matter.
- **H6 Empty Ω:** no `Nonempty Ω`. If Ω is empty, ∅ = Ω, so `univ_eq_one` and additivity on (∅, ∅) contradict: no q is a finitely additive probability, and every book (even `[]`) is vacuously a sure loss. Both directions and R3 are then consistent (both sides true / R2 vacuous). De Finetti's complete class (« dont un (et un seul) doive se vérifier », p. 7) presupposes a state occurs, so `Nonempty Ω` would be faithful too; it was not added because no theorem needs it and the source does not state it as a hypothesis (G-AX-P3-15).
- **H7 Trivially true?** `IsDutchBook` is strict and the book is finite, so the empty book is not a Dutch book when Ω is non-empty (`not_isDutchBook_nil`); R1 is not vacuous for non-empty Ω.
- **H8 Classical choice:** classical object logic; no restriction.

## 5. G-AX candidates

New candidates, numbered from G-AX-P3-10. None is a hypothesis of any theorem.

- **P3-10 Point-mass representation: a proof-route lemma, not a G-AX candidate (reclassified by the Stage 1 audit).** On finite Ω it is provable (Finset induction with `union_of_disjoint` and `empty`), so no operator decision is needed. On a finite Ω, whether every finitely additive q on `Set Ω` equals `pointMass (fun ω => q {ω})` matters for the proof of R2 (via `expected_netPayoff_pointMass`). It is **not** added as a hypothesis; de Finetti (p. 10) asserts that P is determined by its values on the constituents, but that is not stated as a hypothesis of the converse. If it were added, R2 would quantify only over point-mass quotients.
- **G-AX-P3-11 Non-negativity as an axiom of the target.** `IsFinitelyAdditiveProb.nonneg` is in the axioms, so R1 claims a book against negative quotients. De Finetti asserts non-negativity (pp. 8, 10) but derives no betting argument for it in Chapitre I; the survey lists it as an axiom.
- **G-AX-P3-12 Additivity form.** Binary additivity over disjoint pairs on all of `Set Ω`, rather than de Finetti's proved form (sum over a complete class equals 1, p. 8) with n-ary additivity as « corollaire immédiat ». Equivalence under P3-3/P3-4 is assumed, not proved here.
- **G-AX-P3-13 Admissible bet events.** A book may bet on any event, including ∅ and Ω, and may repeat an event. De Finetti's bets in the forward proof are on one complete class only.
- **G-AX-P3-14 Which side loses.** Vineberg says "to one side"; the encoding fixes the loss on the agent. De Finetti states the opponent's sure win (all Gₕ positive). With either-sign stakes (P3-2) negating every stake swaps the sides, so the readings coincide only under P3-2.
- **G-AX-P3-15 Non-empty state space.** Not assumed (H6).
- **G-AX-P3-16 Total quotient function.** q is defined on every event, whereas de Finetti defines coherence on an arbitrary class 𝓔 (p. 9) with P possibly partial. Covered in part by P3-4.

## 6. Open items

- Fidelity to Kemeny 1955 and Lehman 1955 for the general converse stays open (D29).
- The `@adversarial` hidden-hypothesis audit and the independent back-translation have run (`stage1-audit.md`, `back-translation.md`): no theorem needs revision.
- **Load-bearing choices (from the audits), for the G-FID review:**
  - P3-6 *strict* sure loss is required: under weak sure loss (≤ 0 everywhere, < 0 somewhere) R2 is false (Ω = {a, b}, q{a} = 1, q{b} = 0, book [⟨{b}, −1⟩] pays 0 at a and −1 at b), so R3 holds only under the strict notion. De Finetti's "positif" read as strict (extract) is therefore decisive.
  - P3-2 *either-sign* stakes are required: R1 fails under positive-only stakes when some q A < 0.
  - P3-15 `Nonempty Ω` is optional: with Ω empty every q is incoherent and the empty book is a Dutch book (degenerate, consistent); de Finetti's complete class presupposes some state occurs.

## References

- de Finetti, Bruno. "La prévision : ses lois logiques, ses sources subjectives." *Annales de l'institut Henri Poincaré* 7, no. 1 (1937): 1–68. Extract: `sources/definetti-1937-extract.md`.
- Vineberg, Susan. "Dutch Book Arguments." *Stanford Encyclopedia of Philosophy*, 2022. As quoted in `interpretation.md`.
