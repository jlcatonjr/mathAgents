# Proof Library

The proof library has two parts:

- the Lean 4 package in [`lean/`](https://github.com/jlcatonjr/mathAgents/tree/main/lean): the proved library
  `MathAgents` and the open-work library `MathAgentsWIP`;
- the dossiers in [`reports/dossiers/`](https://github.com/jlcatonjr/mathAgents/tree/main/reports/dossiers), one per
  problem.

The [explorer's proof-library view](explorer/index.html#library) lists every dossier and declaration as their
records stand at the last site build.

## How to read a result

1. **A dossier's result is its `Result status:` line** (in its `README.md`), and nothing else. A dossier without one
   has an open result.
2. **A declaration is proved only if [G-KERNEL](concepts.md#gates) says so.** The explorer shows the status recorded
   in the dossier's kernel snapshot, with the snapshot's commit and date, and greys it out when the Lean sources
   have changed since. The current status is whatever a fresh `bash scripts/check_proof_integrity.sh` reports.
3. **Proved is not the same as faithful.** A proof is only as good as its statement. Each statement a dossier's
   result rests on carries a person's [G-FID](concepts.md#gates) approval, bound to the statement's fingerprint and
   to a stated source. Auxiliary lemmas are not approved separately. The explorer shows each approval and says when
   its fingerprint differs from the snapshot's, or has not yet been checked against one.
4. **Blueprint + Lean is the standard.** No dossier has a blueprint yet, so no result meets the full standard. What
   is in place is the Lean half.

## The pilot dossiers

Pilot numbers come from the pilot register (`references/pilots.json`). A dossier's slug is fixed once its intake
exists, so `p4-thirty-divides-n5-minus-n` is pilot **P6** (charter D44). P4 is the modal K/S4 pilot, not yet started.

| Pilot | Dossier | Problem |
|---|---|---|
| P2 | `p2-lewis-triviality` | Lewis's triviality theorem for conditional probability. The statement of record is the *Stanford Encyclopedia of Philosophy*'s version, because Lewis 1976 could not be consulted, so fidelity to Lewis's own wording is still open. |
| P3 | `p3-dutch-book` | The finite Dutch Book theorem and its converse, on the `finite-probability` object logic. |
| P6 | `p4-thirty-divides-n5-minus-n` | 30 divides *n*⁵ − *n*, in two readings: over the integers (R1), and over the natural numbers with truncated subtraction (R2). |

Each dossier's current result status and stage are in the [explorer](explorer/index.html#library), which reads them
from the records. Its files are linked from there: the problem card, the interpretation brief, the statement, the
strategy, the derivations, the informalization and the kernel snapshot.
