# Source extract — de Finetti 1937 (P3 primary source)

> **Purpose:** primary-source passages for P3's forward direction and the bet/payoff definitions, per charter D29.
> **Status:** extract only. It does not select a reading and does not approve a statement; those are G-FID decisions.
> **Language rule (D29):** the French text is the source. Each English rendering is marked **[our translation]** and must never be quoted as de Finetti's words.

## Provenance

| Field | Value |
|---|---|
| Work (key) | `deFinetti1937`: de Finetti, Bruno. "La prévision : ses lois logiques, ses sources subjectives." *Annales de l'institut Henri Poincaré* 7, no. 1 (1937): 1–68 |
| Landing page | http://www.numdam.org/item/AIHP_1937__7_1_1_0/ |
| PDF retrieved | https://www.numdam.org/item/AIHP_1937__7_1_1_0.pdf |
| Retrieval date | 2026-10-01 |
| File | 69 PDF pages, 6,129,774 bytes, SHA-256 `d85e2715e95b21de430dd2cdbd0b890489bcd821fe5bf5ac0f6eff338615bff2`; PDF metadata: producer pdfTeX-1.40.16, NUMDAM, created 2024-11-04 |
| Text extraction | `pdftotext -layout` (poppler) on the NUMDAM OCR text layer |
| Page mapping | PDF page 1 is the NUMDAM cover sheet. **Printed page = PDF page − 1** (PDF p. 2 = printed p. 1; PDF p. 69 = printed p. 68). Verified by the running page numbers on PDF pp. 3, 4, 7–11, 14, 15 and 69. |
| Location | Every key passage is in Chapitre I, "La logique du probable", printed pp. 4–16. Chapitre II begins on printed p. 16. |

**How the quotations were checked.** The NUMDAM text layer is OCR and is badly damaged in formulas and subscripts. Each quotation below was therefore checked against the page image, which was rendered with `pdftoppm -r 110` for PDF pp. 7–11, 14 and 15. The quotation gives the printed page as the scan shows it. Where the text layer differs from the scan, an **[OCR: …]** note records what the text layer reads. Line breaks are joined and end-of-line hyphenation is rejoined ("proba-|bilités" becomes "probabilités"). Italics in the original are shown as `*…*`, and displayed formulas are transcribed in plain notation. Nothing else is changed.

---

## (a) The bet and its payoff, including the stake and its sign

**A1 — printed p. 6** (the operational idea):

> « Il s'agit simplement de préciser mathématiquement l'idée banale et évidente que le degré de probabilité attribué par un individu à un événement donné est révélé par les conditions dans lesquelles il serait disposé de parier sur cet événement (¹). »

[our translation] "It is simply a matter of stating mathematically the commonplace and evident idea that the degree of probability an individual attributes to a given event is revealed by the conditions under which he would be willing to bet on that event."

**A2 — printed p. 6** (the definition):

> « Supposons qu'un individu soit obligé d'évaluer le prix *p* pour lequel il serait disposé d'échanger la possession d'une somme quelconque S (positive ou négative) subordonnée à l'arrivée d'un événement donné, E, avec la possession de la somme *p*S ; nous dirons par définition que ce nombre *p* est la mesure du degré de probabilité attribué par l'individu considéré à l'événement E, ou, plus simplement, que *p* est la probabilité de E (selon l'individu considéré ; cette précision pourra d'ailleurs être sous-entendue s'il n'y a pas d'ambiguïté). »

[OCR: the text layer reads "la somme p S" and puts a stray "’" mark in the parenthesis; the scan reads "pS".]

[our translation] "Suppose an individual is obliged to evaluate the price *p* at which he would be willing to exchange possession of an arbitrary sum S (positive or negative), conditional on the occurrence of a given event E, for possession of the sum *p*S. We say by definition that this number *p* is the measure of the degree of probability the individual attributes to the event E, or more simply that *p* is the probability of E (according to that individual; this qualification may be left implicit when nothing is ambiguous)."

**A3 — printed p. 7** (the gain of a combination of bets on a complete class):

> « si l'on fixe les enjeux (positifs ou négatifs) S₁, S₂, …, Sₙ, les gains dans les *n* cas possibles seront les différences entre l'enjeu du pari gagné et la somme des *n* mises payées
>
> Gₕ = Sₕ − Σᵢ₌₁ⁿ pᵢSᵢ. »

[OCR: the text layer reads the stakes as "S~, S~, S,i" with the "…" displaced to the next line, and the formula as "Gh .= Sh- l pi Si". The scan shows Gₕ = Sₕ − Σ_{i=1}^{n} pᵢSᵢ.]

[our translation] "If the stakes S₁, S₂, …, Sₙ (positive or negative) are fixed, the gains in the *n* possible cases will be the differences between the stake of the winning bet and the sum of the *n* payments made: Gₕ = Sₕ − Σ pᵢSᵢ."

**A4 — printed p. 14** (the conditional bet, given for completeness; it is not needed for P3's unconditional statement):

> « si S est l'enjeu, la mise à verser sera *p*S, et le gain (1 − *p*)S, − *p*S ou 0 selon que E′/E″ sera vrai, faux ou nul, car dans le premier cas on gagne l'enjeu et on perd la mise, dans le deuxième on perd la mise, dans le dernier la mise est remboursée (si S < 0 ces considérations demeurent inchangées ; il n'y a qu'à échanger la terminologie de débit et crédit). »

[OCR: the text layer drops "(1 − p)S", reads "- p S ou o", and loses "< 0" in "si S o ces". The scan is as transcribed. "E′/E″" stands for de Finetti's stacked notation for E′ conditional on E″.]

[our translation] "If S is the stake, the payment due is *p*S, and the gain is (1 − *p*)S, −*p*S or 0 according as E′ given E″ is true, false or void: in the first case one wins the stake and loses the payment, in the second one loses the payment, and in the last the payment is refunded (if S < 0 nothing changes; one need only swap the terms debit and credit)."

**Reading of (a)** [editors' inference from A2–A4]: the individual pays *p*S and receives S if E occurs, so the individual's net gain on one bet is S·(1_E − *p*). A combination of bets on E₁, …, Eₙ gives Σᵢ Sᵢ(1_{Eᵢ} − pᵢ), which in the state where Eₕ occurs is A3's Gₕ. De Finetti writes the sign explicitly twice ("positive ou négative", p. 6; "positifs ou négatifs", p. 7), and on p. 14 says that a negative S only swaps debit and credit. Because one price *p* serves both signs of S, the individual takes either side of the bet at the same quotient.

---

## (b) Coherence and the sure-loss notion

**B1 — printed p. 7:**

> « Ceci posé, lorsqu'un individu a évalué les probabilités de certains événements, deux cas peuvent se présenter : ou bien il est possible de parier avec lui en s'assurant de gagner à coup sûr, ou bien cette possibilité n'existe pas. Dans le premier cas on doit dire évidemment que l'évaluation de la probabilité donnée par cet individu contient une incohérence, une contradiction intrinsèque ; dans l'autre cas, nous dirons que l'individu est cohérent. C'est précisément cette condition de *cohérence* qui constitue le seul principe d'où l'on puisse déduire tout le calcul des probabilités : ce calcul apparaît alors comme l'ensemble des règles auxquelles l'évaluation subjective des probabilités de divers événements par un même individu doive être assujettie si l'on ne veut pas qu'il y ait entre elles une contradiction fondamentale. »

[our translation] "This said, once an individual has evaluated the probabilities of certain events, two cases can arise: either it is possible to bet with him so as to be sure of winning, or no such possibility exists. In the first case we must clearly say that the individual's evaluation of probability contains an incoherence, an intrinsic contradiction; in the other case we shall say that the individual is coherent. It is precisely this condition of *coherence* that is the only principle from which the whole calculus of probability can be deduced. The calculus then appears as the set of rules to which one individual's subjective evaluation of the probabilities of various events must be subject if there is to be no fundamental contradiction among them."

**B2 — printed p. 8** (sure win stated through the sign of all the Gₕ):

> « si ce déterminant n'est pas nul, on peut fixer le Sₕ de façon que les Gₕ aient des valeurs arbitraires, en particulier toutes positives, contrairement à la condition de cohérence »

[OCR: the text layer reads "les Glz" for "les Gₕ".]

[our translation] "If this determinant is non-zero, the Sₕ can be chosen so that the Gₕ take arbitrary values, in particular all positive ones, contrary to the condition of coherence."

**B3 — printed p. 9** (coherence on an arbitrary class and its extensions):

> « calculer la valeur qu'on est obligé d'attribuer à l'événement E, si l'on veut rester dans le domaine de la cohérence, après avoir évalué d'une façon déterminée les probabilités des événements constituant une certaine classe 𝓔. Mathématiquement, on suppose la fonction **P** connue sur l'ensemble 𝓔, et l'on demande quelle est la valeur unique, ou quelles sont les valeurs que l'on peut attribuer à **P**(E) sans que ce prolongement de **P** fasse apparaître une incohérence. »

[OCR: the text layer renders the script class letter 𝓔 as "&#x26;" (an HTML entity for "&") and once as "~", and reads "calcule~°" for *calculer* in the preceding sentence.]

[our translation] "…compute the value one is obliged to give to the event E, if one wants to stay within coherence, after having evaluated in a definite way the probabilities of the events forming a certain class 𝓔. Mathematically, the function **P** is supposed known on the set 𝓔, and one asks for the unique value, or the values, that can be given to **P**(E) without this extension of **P** revealing an incoherence."

**Reading of (b)** [editors' inference]:
- Coherence is defined as the absence of a book that wins for the opponent "à coup sûr" (B1). The derivation states it through Gₕ, which is the *individual's* gain (A3): a book in which all the Gₕ are positive violates coherence (B2). Because stakes may take either sign (A2, A3), "all Gₕ > 0" and "all Gₕ < 0" are interchangeable by negating every Sₕ. P3's "sure loss for the agent" is therefore de Finetti's notion with the sign convention reversed.
- **Strictness.** In French usage "positif" can mean ≥ 0. The p. 8 sufficiency argument (C2) reads "positif" as strict: if Σ pₕGₕ = 0 with pₕ ≥ 0, the Gₕ can all be ≥ 0, for instance all equal to 0, but they cannot all be > 0. De Finetti never states the strict/weak distinction in words.
- **Domain.** Coherence is defined for "certains événements" (B1) or "une certaine classe 𝓔" (B3), an arbitrary class that need not be closed under any connective.

---

## (c) The forward direction: coherence implies the probability laws

**C1 — printed p. 7** (the setting, a finite complete class):

> « Voyons comment on démontre, par cette voie, le théorème des probabilités totales : c'est un résultat important par lui-même et aussi pour éclaircir le point de vue suivi. Soient E₁, E₂, …, Eₙ des événements incompatibles dont un (et un seul) doive se vérifier (nous dirons : une classe *complète* d'événements incompatibles), et soient *p*₁, *p*₂, …, *p*ₙ leurs probabilités évaluées par un individu donné »

[OCR: the text layer reads "E,, E2" for "E₁, E₂".]

[our translation] "Let us see how the theorem of total probability is proved this way: it is an important result in itself, and it also clarifies the point of view adopted. Let E₁, E₂, …, Eₙ be incompatible events of which one (and only one) must occur (we shall say: a *complete* class of incompatible events), and let *p*₁, …, *p*ₙ be their probabilities as evaluated by a given individual…"

**C2 — printed pp. 7–8** (the determinant argument; necessity, then sufficiency):

> « En considérant les Sₕ comme inconnues, on a un système d'équations linéaires de déterminant [ | 1−*p*₁ −*p*₂ … −*p*ₙ ; −*p*₁ 1−*p*₂ … −*p*ₙ ; … ; −*p*₁ −*p*₂ … 1−*p*ₙ | ] = 1 − (*p*₁ + *p*₂ + … + *p*ₙ) ; [p. 8] si ce déterminant n'est pas nul, on peut fixer le Sₕ de façon que les Gₕ aient des valeurs arbitraires, en particulier toutes positives, contrairement à la condition de cohérence ; par conséquent, la cohérence oblige à imposer la condition *p*₁ + *p*₂ + … + *p*ₙ = 1. Cette condition nécessaire pour réaliser la cohérence est aussi suffisante, parce que, si elle est satisfaite, on a identiquement (quels que soient les enjeux Sₕ) Σₕ₌₁ⁿ *p*ₕGₕ = 0, et les Gₕ ne peuvent jamais, par conséquent, être tous positifs. »

[OCR: the text layer reads the condition as "P1 + /?2 -~-...-~-~,z = i" and garbles the determinant and "Σ pₕGₕ = o". The scan shows "p₁ + p₂ + … + pₙ = 1" and "Σ_{h=1}^{n} pₕGₕ = 0". The determinant is a displayed n×n matrix in the original, given here row by row in brackets.]

[our translation] "Treating the Sₕ as unknowns gives a system of linear equations whose determinant is 1 − (p₁ + … + pₙ). If this determinant is non-zero, the Sₕ can be chosen so that the Gₕ take arbitrary values, in particular all positive ones, contrary to the condition of coherence. Hence coherence requires the condition p₁ + p₂ + … + pₙ = 1. This condition, necessary for coherence, is also sufficient, because when it holds we have identically (whatever the stakes Sₕ) Σ pₕGₕ = 0, and so the Gₕ can never all be positive."

**C3 — printed p. 8** (the theorem and finite additivity as its corollary):

> « On a ainsi le théorème des probabilités totales sous la forme suivante : *dans une classe complète d'événements incompatibles, la somme des probabilités doit être égale à* 1. La forme plus générale : *la probabilité de la somme logique de n événements incompatibles est la somme de leurs probabilités*, n'en est que le corollaire immédiat. »

[our translation] "We thus have the theorem of total probability in the following form: *in a complete class of incompatible events, the sum of the probabilities must equal 1*. The more general form, *the probability of the logical sum of n incompatible events is the sum of their probabilities*, is only its immediate corollary."

**C4 — printed p. 10** (non-negativity and normalization through the constituents):

> « On a vu qu'une fonction de probabilité **P**(E) est complètement déterminée lorsqu'on en donne les valeurs relatives aux constituants, *c*₁ = **P**(C₁), *c*₂ = **P**(C₂), …, *c*ₛ = **P**(Cₛ), valeurs qui doivent être non négatives et de somme égale à l'unité. »

[OCR: the text layer is close to the scan here, apart from spacing and "C1 = P (C1)" for *c*₁ = **P**(C₁).]

[our translation] "We have seen that a probability function **P**(E) is completely determined once its values on the constituents are given, c₁ = P(C₁), …, cₛ = P(Cₛ), values which must be non-negative and sum to one."

**C5 — printed p. 9** (the constituents: at most 2ⁿ cases from n events):

> « Soient E₁, E₂, …, Eₙ les événements de 𝓔 ; parmi ces *n* événements, certains pourront se produire, d'autres non ; les sous-classes d'une classe de *n* éléments étant au nombre de 2ⁿ (la classe totale et la classe vide incluses), il y aura, au plus, 2ⁿ cas possibles C₁, C₂, …, Cₛ (*s* ≤ 2ⁿ) qu'on appelle, d'après Boole, les « constituants ». (« au plus », car un certain nombre de combinaisons pourraient s'avérer impossibles) »

[OCR: the text layer reads "21l" and "2n" for 2ⁿ, "Cs(s ~ 2n)" for Cₛ (s ≤ 2ⁿ), and "E1’ E?" for E₁, E₂.]

[our translation] "Let E₁, …, Eₙ be the events of 𝓔. Among these n events some may occur and others not. Since a class of n elements has 2ⁿ subclasses (including the whole class and the empty class), there will be at most 2ⁿ possible cases C₁, …, Cₛ (s ≤ 2ⁿ), which, following Boole, are called the 'constituents' ('at most' because some combinations may turn out to be impossible)."

**C6 — printed p. 13** (finiteness: infinite classes are handled through their finite subclasses, and countable additivity is not obtained):

> « Lorsque les événements considérés sont en nombre infini, notre définition n'introduit aucune difficulté nouvelle : **P** est une fonction de probabilité pour la classe infinie d'événements 𝓔 lorsqu'elle l'est pour toute sous-classe finie de 𝓔. Cette conclusion implique que le théorème des probabilités totales ne peut être étendu au cas d'une infinité, même dénombrable, d'événements (¹) ; une discussion sur ce sujet nous entraînerait trop loin. »

[OCR: the text layer reads "dévouements &#x26;" for "d'événements 𝓔".] Footnote (¹), p. 13: « *Voir* [16], [24], [X], [28], [XI], [64]. »

[our translation] "When infinitely many events are considered, our definition raises no new difficulty: **P** is a probability function on the infinite class of events 𝓔 when it is one on every finite subclass of 𝓔. This conclusion implies that the theorem of total probability cannot be extended to the case of infinitely many events, even countably many; discussing this would take us too far."

The same position is repeated on **printed p. 32**: « …car ils supposent essentiellement l'extension du théorème des probabilités totales au cas d'une infinité d'événements, et cette extension n'est pas admissible, du moins selon mon point de vue (voir p. 13). » [Checked against the text layer only; the page image was not rendered.]

[our translation] "…because they essentially presuppose extending the theorem of total probability to infinitely many events, and that extension is not admissible, at least in my view (see p. 13)."

**Reading of (c)** [editors' inference]:
- **What is proved.** The forward direction is proved in the text only for a finite complete class E₁, …, Eₙ, with one bet on each member (C1–C2). The conclusion is normalization over a partition (Σ pₕ = 1). Finite additivity is called an "immediate corollary" (C3), but that step is not written out.
- **Non-negativity.** Non-negativity (0 ≤ p) is **not derived by a betting argument** in Chapter I. It is asserted for admissible evaluations (C2's following paragraph, quoted in (d), and C4).
- **Finiteness.** Finiteness is built in: there are *n* events and *n* stakes, and every infinite class is reduced to its finite subclasses (C6).
- **Normalization.** De Finetti states normalization for a complete class. "L'événement certain" is the sum of all constituents (printed p. 10, scan). On printed p. 11 the text layer reads « Le centre 0 correspondant à l'événement certain, on a enparticulier I = f(s . 0 ) » [OCR: "0" for O, "I" for 1, "enparticulier" for "en particulier"; the page image was not rendered], which gives the certain event value 1. He does not distinguish tautologies, logical truths and necessary truths.

---

## (d) The converse

**D1 — printed p. 8** (sufficiency on a complete class; the sentence "Cette condition … aussi suffisante" is quoted in C2):

> « Cependant, avons-nous ajouté, la condition est aussi suffisante ; il est utile d'éclaircir quelque peu le sens de cette affirmation […]. En disant que la condition est suffisante, on entend que, une classe complète d'événements incompatibles E₁, E₂, …, Eₙ étant donnée, toutes les évaluations de probabilité qui attribuent à *p*₁, *p*₂, …, *p*ₙ des valeurs quelconques non négatives et de somme égale à l'unité sont des évaluations admissibles : chacune de ces évaluations correspond à une opinion cohérente, à une opinion légitime en soi, et chaque individu est libre d'adopter celle de ces opinions qu'il préfère, ou, pour mieux dire, celle qu'il *sent*. »

[OCR: the text layer reads "dévouements" for "d'événements", "p1, ~~, ..., ~"" for p₁, p₂, …, pₙ, and "Get arbitraire" for "Cet arbitraire" later in the paragraph. The elision […] is ours.]

[our translation] "However, as we added, the condition is also sufficient; it is useful to clarify the meaning of this claim a little. […] In saying that the condition is sufficient, we mean that, given a complete class of incompatible events E₁, …, Eₙ, every evaluation of probability that gives p₁, …, pₙ arbitrary non-negative values summing to one is admissible: each such evaluation corresponds to a coherent opinion, an opinion legitimate in itself, and each individual is free to adopt whichever of these opinions he prefers, or rather the one he *feels*."

**D2 — printed p. 12** (linear dependence and bets equivalent to a bet on the certain event):

> « L'autre condition dit que des événements sont linéairement dépendants lorsque l'on peut attribuer à chacun d'eux un coefficient, de telle façon que, dans tous les cas possibles, la somme des coefficients des événements vérifiés ait toujours la même valeur. Si, en effet, les points correspondants aux événements donnés et le point O sont linéairement dépendants, il est possible d'exprimer O linéairement au moyen des autres, et cela signifie qu'il existe une combinaison de paris sur ces événements équivalente à un pari sur un événement certain, comme l'exprime la condition énoncée. »

[Checked against the text layer only; the page image was not rendered. The text layer reads "le point 0" and "exprimer 0", and the scan of p. 10 shows that the centre is the letter O.]

[our translation] "The other condition says that events are linearly dependent when a coefficient can be assigned to each of them so that, in every possible case, the sum of the coefficients of the events that occur always has the same value. Indeed, if the points corresponding to the given events and the point O are linearly dependent, O can be expressed linearly in terms of the others, which means that there is a combination of bets on these events equivalent to a bet on a certain event, as the stated condition says."

**D3 — printed p. 15** (the same necessary-and-sufficient claim for compound probability):

> « La condition n'est pas seulement nécessaire, mais aussi suffisante, dans le même sens que dans le cas du théorème des probabilités totales. »

[Checked against the text layer only; it is clean at this point.]

[our translation] "The condition is not only necessary but also sufficient, in the same sense as for the theorem of total probability."

**Reading of (d)** [editors' inference]:
- **What de Finetti asserts.** He does assert a converse: on a finite complete class, non-negative values summing to 1 cannot be booked. The proof sentence (C2) relies on Σ pₕGₕ = 0. That inference ("so the Gₕ can never all be positive") also needs pₕ ≥ 0, a condition the sentence does not state but D1 makes explicit.
- **What his proof covers.** The converse proof covers only books whose bets are on the members of that one partition. For an arbitrary finite class 𝓔, the characterization of admissible P (non-negative constituent values summing to 1; C4, and the convex set of p. 12) is stated rather than proved by a betting argument in Chapter I.
- **Infinite books.** He does not consider infinite books, and he rejects countable additivity (C6).
- **Counterexamples and restricted notions.** Nothing in Chapter I addresses Vineberg's counterexamples to the rough converse, strengthened axioms (R4), or restricted sure loss (R5).

---

## Mapping to P3 G-AX candidates and preference choices

"Supports" means the passage states or directly entails the choice. "Consistent" means the passage fits the choice without stating it. "Differs" means de Finetti's own setting is different, even where the choice is a special case of it. "Silent" means the passage does not address the choice.

### G-AX candidates (interpretation.md) and `[gax]` choices (preferences.toml)

| Candidate | Preference choice | de Finetti 1937 | Assessment | Passage(s) |
|---|---|---|---|---|
| P3-1 canonical bet and payoff | `S(1_A - q)` | The individual exchanges S conditional on E for *p*S, so the net gain is S(1_E − *p*); a book gains Gₕ = Sₕ − Σ pᵢSᵢ | **Supports** (the formula is our algebraic restatement) | A2 p. 6; A3 p. 7; A4 p. 14 |
| P3-2 direction and sign of the stake | `either-sign` | "somme quelconque S (positive ou négative)"; "enjeux (positifs ou négatifs)"; S < 0 only swaps debit and credit | **Supports** | A2 p. 6; A3 p. 7; A4 p. 14 |
| P3-3 normalization | `tautologies` | The sum over a complete class is 1, and the certain event (sum of all constituents) has value 1 (p. 11). There is no tautology/logical-truth/necessary-truth distinction | **Consistent; silent on the distinction** | C2–C3 pp. 7–8; C4 p. 10; p. 11 |
| P3-4 structure of X | `boolean-algebra` | Coherence is defined on an arbitrary class 𝓔, with extension to logically dependent events (sums of constituents) | **Differs (more general).** The Boolean-algebra setting is a special case and does not conflict | B1 p. 7; B3 p. 9; C5 p. 9 |
| P3-5 number of bets | `finitely-many` | n stakes S₁…Sₙ; infinite classes are reduced to their finite subclasses | **Supports** | A3, C1–C2 p. 7; C6 p. 13 |
| P3-6 sure loss | `negative-in-every-state` | "gagner à coup sûr"; a book violates coherence when all Gₕ are "positives". This is the opponent's sure win, which is the agent's loss under either-sign stakes. The sufficiency proof needs the strict reading | **Supports, with caveats:** (i) the sign convention is reversed; (ii) strictness is implied, not stated | B1 p. 7; B2, C2 p. 8 |
| P3-7 size of X | `finite` | The derivations use n events; an infinite 𝓔 is allowed through its finite subclasses | **Supports for the proved results.** De Finetti also admits infinite classes (finitary condition) | C1, C5 pp. 7, 9; C6 p. 13 |
| P3-8 accepted bets | `fair-only` | A single price *p* at which the individual is willing to exchange either way. Favourable bets are not discussed | **Consistent with fair-only; silent on fair-or-favorable** | A2 p. 6 |
| P3-9 strengthened axioms (R4) | not a gax setting (R4 deferred) | Not addressed | **Silent** | — |

### Other preference choices

| Setting | Choice | de Finetti 1937 | Assessment |
|---|---|---|---|
| `readings.selected` R1 (forward) | selected | Proved for a finite complete class: coherence forces Σ pₕ = 1, with finite additivity as a corollary. Non-negativity is asserted, not proved by a bet | **Supports** (partition normalization; additivity by corollary) — C1–C3 pp. 7–8 |
| `readings.selected` R2 (rough converse) | selected | Sufficiency is claimed and proved for books on one complete class with non-negative pₕ summing to 1. The general characterization is stated, not proved | **Partial primary support** — C2, D1 p. 8; D3 p. 15; C4 p. 10 |
| `readings.selected` R3 (both directions) | selected | Necessity and sufficiency are stated together under one definition of bet and coherence | **Supports a shared formulation** — C2 pp. 7–8; D1 p. 8 |
| R4, R5 | not selected | Not addressed | **Silent** |
| `sources.primary_unavailable` | `survey-statement-flagged` | Since de Finetti does state a converse (D1), the survey is not the only source for R2 on partitions | **Bears on the choice:** Kemeny/Lehman remain unavailable for the general converse |
| `sources.translation` | `verbatim-plus-our-translation` | Applied throughout this file | **Followed** |
| `intake.object_logic` | `finite-probability` | Finite classes, finite additivity, no countable additivity | **Consistent** — C3 p. 8; C6 p. 13 |
| `intake.domain`, `intake.engines`, `fidelity.kernel_as_judge`, `readings.selection` | — | Not addressed by the source | **Silent** |
