# Explorer

[Open the explorer :material-arrow-right:](explorer/index.html){ .md-button .md-button--primary }

The explorer is a single page that runs entirely in your browser. Its data is written by
`scripts/build_api_site.py` when the site is built, in the same build that writes the
[API reference](api-reference/index.md). The explorer has three views.

**API.** Every public name in the `mathagents` package, searchable and filterable by module and kind. Each name
shows its signature, the first paragraph of its docstring, a link to its reference page and a link to its source.
"Public" has the same meaning as in the API-parity gate: a name in the `__all__` of a module whose name has no
leading underscore.

**Proof library.** Every dossier, with these details:

- its problem card (including its source);
- its readings;
- which stages' files are present;
- its `Result status:` line, word for word;
- each declaration, with the [G-KERNEL](concepts.md#gates) status and axioms recorded in the dossier's kernel
  snapshot, and its [G-FID](concepts.md#gates) approval.

The dossier data comes from the documented API: `list_dossiers`, `dossier_status`, `result_labels`,
`list_readings`, `read_fidelity_record` and `read_kernel_snapshot`. A few things come from other sources:

- the problem-card fields, read with the dossier gate's own reader (`scripts/dossier_structure.py`);
- the axiom allowlist and the Lean and Mathlib pins, read from their files;
- whether a snapshot is still current, from the G-KERNEL gate's own source hash (`scripts/proof_integrity.py`).

**Pipeline & registries.** The pipeline stages (`STAGES`), the automated gates (`GATES`), the object-logic and
prover-engine registries, and the axiom allowlist.

!!! info "Limits"
    The explorer runs no gate and re-derives nothing. It shows what a tracked record holds, labelled with the record
    it came from.

    - A kernel status is the one in the dossier's snapshot, taken at the commit and date shown. It is not a fresh
      kernel check, which needs a Lean build.
    - When the Lean sources have changed since a snapshot, its statuses are greyed out.
    - A declaration with no snapshot yet shows as such, and so does an approval whose fingerprint has not yet been
      checked against a snapshot.
    - The data is as fresh as the last site build, whose commit and time the proof-library view shows.
    - The proof standard is Blueprint + Lean, and no dossier has a blueprint yet (see
      [how to read a result](proof-library.md#how-to-read-a-result)).

    To check a result yourself, clone the repository and run `bash scripts/check_proof_integrity.sh` (the G-KERNEL
    gate).
