# The documentation site

**Owner of:** `scripts/build_api_site.py`, `mkdocs.yml`, `docs_src/` and `.github/workflows/docs.yml`.
Status: long-lived utility.

The site is built in two steps:

```bash
python3 scripts/build_api_site.py                        # generate (gitignored outputs under docs_src/)
python3 -m mkdocs build --strict --site-dir _site        # build; fails on a broken link or nav entry
```

Install the build dependencies with `pip install --require-hashes --no-deps -r .github/ci/requirements-docs.txt`.

## What is generated

These files are gitignored and rebuilt by `docs.yml`:

- `docs_src/api-reference/*.md`, from the canonical `docs/api-reference/*.md`. Edit those, not the generated copies.
- `docs_src/cli-reference.md`, from `mathagents.cli._build_parser()`.
- `docs_src/{stability,changelog,getting-started}.md`, from `STABILITY.md`, `CHANGELOG.md` and `docs/module.md`.
- `docs_src/explorer/api.json` and `docs_src/explorer/library.json`, the explorer's data.

Every link that leaves a source page is rewritten. It becomes a site page if the site carries the target, or a
GitHub link if the target is public documentation (`PUBLIC_PREFIXES` in the generator). Anything else fails the
build, so an internal document (`docs/reports/`, `docs/handoffs/`, `workSummaries/`, `tmp/`, the security logs)
cannot be linked from the site by accident.

## Hand-written

`docs_src/index.md`, `concepts.md`, `interactive-explorer.md` and `proof-library.md`, and the explorer app,
`docs_src/explorer/{index.html,app.js,style.css}`. Keep the explorer free of HTML sinks: it renders every value as
text, under a strict CSP. `tests/test_api_site.py` checks this, along with the nav, the API and CLI coverage, the
data and the workflow's pins.

## README

`README.md` is generated from `brief.json` by `researchteam personalize`. After a personalize run, re-add the
Documentation paragraph under the opening description. `tests/test_api_site.py` fails until you do.

## Publishing

`docs.yml` deploys only on main, and only while the repository is public. Before the first deploy, enable Pages
with source "GitHub Actions". Making the repository public is the operator's decision. It is currently HALTed by
@security: see the charter, and the security log row `repo-visibility-public`.
