# mathAgents

Develop, verify, and explain mathematical and logical proofs across applied/modeling mathematics, research-level mathematics, competition problems, logic and foundations, and proofs used in the philosophy of science. Every proof is articulated through an explicit symbolic-logic pipeline (formal statement with fidelity check, proof-strategy blueprint, named-rule derivations, tactic plans) and is accepted only as Blueprint + Lean: a blueprint whose nodes are name-linked to Lean 4 declarations that build with no sorry, admit, or unapproved axiom. The Lean kernel judges validity; a human judges statement fidelity. Harness design decisions are derived from, and cited to, research on automated and LLM-assisted theorem proving, with Chicago author-date citations to verified sources.

**Documentation** (not yet published; it goes live when the repository is public): [jlcatonjr.github.io/mathAgents](https://jlcatonjr.github.io/mathAgents/): getting started, concepts, the [CLI](https://jlcatonjr.github.io/mathAgents/cli-reference/) and [API reference](https://jlcatonjr.github.io/mathAgents/api-reference/), and an [interactive explorer](https://jlcatonjr.github.io/mathAgents/explorer/) of the API and the proof library. The site is published only while the repository is public; its source is `docs_src/`, `mkdocs.yml` and `scripts/build_api_site.py` ([how it is built](docs/api-site.md)).

## Deliverables

- Proof dossiers (Markdown, Chicago author-date)
- Lean 4 proof library (Lake package)
- Generated proof blueprint (web and PDF)
- Methods literature review
- Harness specification
- Harness evaluation report
- BibTeX bibliography

- **Output format:** Markdown with Chicago author-date citations; Lean 4 sources; generated blueprint
- **Primary output directory:** `reports/`

## Repository layout

| Path | Purpose |
|---|---|
| `reports/` | Primary deliverables authored by this project |
| `Projects/` | Working project deliverables (active) |
| `references/` | Bibliography, registries, and shared references |
| `.github/agents/` | Agent team infrastructure (generated from `brief.json`) |
| `.claude/` | Claude bridge templates and checklists |
| `docs/` | Project + framework documentation |
| `tmp/by-week/` | Weekly plan and step artifacts |

## Working with the agent team

- **Claude users:** start from [`CLAUDE.md`](CLAUDE.md).
- **Copilot / agentteams users:** start from [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

The agent team is generated from [`brief.json`](brief.json). Edit `brief.json` to describe this
project, then regenerate the team (see below). Do not hand-edit files under `.github/agents/**` —
they are generated and the next sync discards manual edits.

## Keeping the team in sync with the brief

This repository was scaffolded with the **researchteam** framework and receives infrastructure
updates without touching your research content.

- `researchteam update` — sync framework files from upstream and merge agent infrastructure.
- `researchteam materialize` — **re-render** the agent team from `brief.json` after you change
  the project's identity or domain (a plain `update` deliberately preserves enriched bodies and
  will not re-brand them).
- `researchteam personalize` — regenerate this `README.md` and `CLAUDE.md`'s project header from
  `brief.json`.

Full command reference, installation, the two-layer update model, and CI details live in
[`docs/researchteam-framework.md`](docs/researchteam-framework.md).

`brief.json`, `Projects/`, and `references/` are user-owned and are never overwritten by an
update.
<!-- researchteam:generated sha256=beb0a897fad2c313ed6fe99f7807bb0e8096d4c01e02acf1baff35038e836df9 — regenerate with `researchteam personalize`; edits to generated regions are overwritten -->
