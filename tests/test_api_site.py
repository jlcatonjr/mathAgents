"""The documentation site (mkdocs.yml, docs_src/, scripts/build_api_site.py, .github/workflows/docs.yml) stays in step
with the package, the CLI parser, the dossier records and its own security rules."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_api_site as site  # noqa: E402
import check_api_doc_parity as parity  # noqa: E402

DOCS = ROOT / "docs_src"
SITE_URL = "https://jlcatonjr.github.io/mathAgents/"
WORKFLOW = ROOT / ".github" / "workflows" / "docs.yml"


class _TagTolerantLoader(yaml.SafeLoader):
    """mkdocs.yml uses `!!python/name:` tags (the emoji extension); read them as plain strings, never execute them."""


_TagTolerantLoader.add_multi_constructor("tag:yaml.org,2002:python/", lambda loader, suffix, node: suffix)

CONFIG = yaml.load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"), Loader=_TagTolerantLoader)


def _nav_files(node) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, list):
        return [f for item in node for f in _nav_files(item)]
    if isinstance(node, dict):
        return [f for value in node.values() for f in _nav_files(value)]
    return []


NAV = _nav_files(CONFIG["nav"])


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("docs_src")
    site.build(out)
    return out


def test_site_config_matches_the_published_location():
    assert CONFIG["docs_dir"] == "docs_src" and CONFIG["site_dir"] == "_site"
    assert CONFIG["site_url"] == SITE_URL


def test_every_nav_entry_is_hand_written_or_generated(built):
    missing = [f for f in NAV if not (DOCS / f).is_file() and not (built / f).is_file()]
    assert not missing, f"mkdocs nav points at pages that are neither in docs_src/ nor generated: {missing}"


def test_every_public_module_has_an_api_page_in_the_nav(built):
    pages = {f for f in NAV if f.startswith("api-reference/")}
    for mod in parity.public_modules(ROOT / "mathagents"):
        page = f"api-reference/{mod.replace('_', '-')}.md"
        assert page in pages, f"mathagents.{mod} has no API page in mkdocs.yml"
        assert (built / page).is_file()
    assert "api-reference/index.md" in pages


def test_api_pages_are_the_canonical_pages_with_only_links_rewritten(built):
    strip = lambda t: site.LINK.sub(lambda m: f"[{m.group(1)}]()", t)  # noqa: E731
    for src in sorted((ROOT / "docs" / "api-reference").glob("*.md")):
        body = (built / "api-reference" / src.name).read_text(encoding="utf-8").split("\n", 1)[1]  # drop the note
        assert strip(body) == strip(src.read_text(encoding="utf-8")), f"{src.name}: content differs beyond links"


def test_every_relative_link_in_a_generated_page_resolves(built):
    import subprocess

    tracked = set(subprocess.run(["git", "-C", str(ROOT), "ls-files", "docs_src"], capture_output=True,
                                 text=True).stdout.split())
    pages = [p for p in built.rglob("*.md")]
    assert pages
    for page in pages:
        for m in site.LINK.finditer(page.read_text(encoding="utf-8")):
            target = m.group(2).split("#", 1)[0]
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            rel = (page.parent / target).resolve()
            inside = [b for b in (built.resolve(), DOCS.resolve()) if rel.is_relative_to(b)]
            assert inside, f"{page.relative_to(built)}: {m.group(2)} leaves the site"
            r = rel.relative_to(inside[0])
            hand = (DOCS / r).exists() and (f"docs_src/{r.as_posix()}" in tracked or (DOCS / r).is_dir())
            assert (built / r).exists() or hand, f"{page.relative_to(built)}: {m.group(2)} is missing"


def test_links_to_internal_documents_fail_the_build():
    for internal in ("../reports/2026-10-05-letter-to-collaborators.md", "../handoffs/x.md", "../../workSummaries/a.md",
                     "../../tmp/by-week/x.md", "../../.github/agents/references/security-decisions.log.csv"):
        with pytest.raises(site.SiteError):
            site.link_target(internal, "docs/api-reference/index.md", "api-reference/index.md")
    assert site.link_target("../../STABILITY.md", "docs/api-reference/index.md", "api-reference/index.md") == \
        "../stability.md"
    assert site.link_target("../module.md#install", "docs/api-reference/index.md", "api-reference/index.md") == \
        "../getting-started.md#install"
    assert site.link_target("docs/release-policy.md", "STABILITY.md", "stability.md") == \
        site.BLOB + "docs/release-policy.md"


def test_cli_reference_covers_every_command_and_option(built):
    import argparse

    from mathagents.cli import _build_parser

    text = (built / "cli-reference.md").read_text(encoding="utf-8")
    sections = {"": text.split("\n## ", 1)[0]}
    for chunk in text.split("\n## ")[1:]:
        head, _, body = chunk.partition("\n")
        sections[head.strip("`")] = body
    missing = []

    def walk(parser, path):
        own = sections.get(" ".join(path))
        if own is None:
            missing.append(" ".join(path))
            return
        for a in parser._actions:
            if isinstance(a, argparse._SubParsersAction):
                for name, child in a.choices.items():
                    walk(child, path + [name])
            elif not isinstance(a, argparse._HelpAction):
                for o in a.option_strings or [a.dest]:
                    if f"| `{o}`" not in own and f", `{o}`" not in own:
                        missing.append(f"{' '.join(path)}: {o}")

    walk(_build_parser(), [])
    assert not missing, f"cli-reference.md is missing: {missing}"


def test_api_json_lists_exactly_the_public_surface(built):
    data = json.loads((built / "explorer" / "api.json").read_text(encoding="utf-8"))
    got = {(m["module"], n["name"]) for m in data["modules"] for n in m["names"]}
    want = {(f"mathagents.{mod}", name) for mod in parity.public_modules(ROOT / "mathagents")
            for name in parity.module_all(ROOT / "mathagents" / f"{mod}.py") or []}
    assert got == want
    assert all(n["kind"] != "re-export" for m in data["modules"] for n in m["names"]), "a public name was not located"


def test_gfid_check_states():
    assert site.gfid_check("1", "1") == "matches"
    assert site.gfid_check("1", "2") == "differs"
    assert site.gfid_check("1", None) == "unchecked"


def test_library_json_reports_only_what_the_records_hold(built):
    import proof_integrity
    from mathagents.dossiers import list_dossiers, result_labels
    from mathagents.fidelity import read_fidelity_record
    from mathagents.snapshot import read_kernel_snapshot

    libs, _ = proof_integrity.libraries(ROOT / "lean")
    current = proof_integrity.source_digest(ROOT / "lean", libs)
    data = json.loads((built / "explorer" / "library.json").read_text(encoding="utf-8"))
    assert data["built_from"]["commit"] and data["built_from"]["built_at"]
    assert [d["slug"] for d in data["dossiers"]] == list_dossiers(root=ROOT)
    for d in data["dossiers"]:
        slug = d["slug"]
        assert d["result_status"] == [{"file": l.file, "value": l.value} for l in result_labels(root=ROOT, slug=slug)]
        snap = read_kernel_snapshot(root=ROOT, slug=slug)
        rows = {r["name"]: r for r in d["declarations"]}
        if snap is None:
            assert d["snapshot"] is None
        else:
            assert d["snapshot"]["sources_current"] == (snap.source_sha256 == current), slug
            for x in snap.declarations:
                assert rows[x.name]["snapshot_status"] == x.status and rows[x.name]["axioms"] == list(x.axioms)
        fid = read_fidelity_record(root=ROOT, slug=slug)
        approvals = {e.decl: e for e in fid.entries} if fid else {}
        for name, r in rows.items():
            if name not in approvals:
                assert r["gfid"] is None, (slug, name)
                continue
            e = approvals[name]
            assert r["gfid"]["statement_fingerprint"] == e.statement_fingerprint
            assert r["gfid"]["check"] == site.gfid_check(e.statement_fingerprint, r["statement_fingerprint"]), name
        assert "Source" in d["card"]["fields"] or not (ROOT / "reports" / "dossiers" / slug / "problem-card.md").is_file()


def test_pilot_labels_come_from_the_register(built):
    data = json.loads((built / "explorer" / "library.json").read_text(encoding="utf-8"))
    register = {p["dossier"]: p["id"] for p in json.loads((ROOT / "references" / "pilots.json").read_text())["pilots"]
                if p.get("dossier")}
    for d in data["dossiers"]:
        assert d["pilot"] == register.get(d["slug"]), d["slug"]
        if d["pilot"]:
            assert not re.match(r"P\d+\s", d["title"]), f"{d['slug']}: title keeps an old pilot label: {d['title']}"
    assert {d["slug"]: d["pilot"] for d in data["dossiers"]}["p4-thirty-divides-n5-minus-n"] == "P6"


def test_a_register_entry_for_a_missing_dossier_fails_the_build(tmp_path, monkeypatch):
    monkeypatch.setattr(site, "_pilots", lambda: {"no-such-dossier": {"id": "P9", "dossier": "no-such-dossier"}})
    with pytest.raises(site.SiteError):
        site.build_library_json(tmp_path)


def test_explorer_shows_the_caveats():
    js = (DOCS / "explorer" / "app.js").read_text(encoding="utf-8")
    for needle in ("Blueprint + Lean", '"Source"', "sources_current", "not yet checked against a kernel snapshot",
                   '"checked"', "does not mean the stage's gate passed"):
        assert needle in js, needle


def test_explorer_renders_text_only_and_sets_a_csp():
    js = (DOCS / "explorer" / "app.js").read_text(encoding="utf-8")
    code = re.sub(r"//[^\n]*", "", js)
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
        assert sink not in code, f"explorer uses {sink}"
    html = (DOCS / "explorer" / "index.html").read_text(encoding="utf-8")
    assert "Content-Security-Policy" in html and "default-src 'self'" in html and "unsafe-inline" not in html
    assert not re.search(r"<script(?![^>]*\bsrc=)", html), "inline script would need unsafe-inline"
    assert not re.search(r"https?://(?!github\.com\b)", js), "explorer refers to a host other than github.com"


def test_no_page_shadows_the_explorer_app():
    """A docs_src/explorer.md would render to explorer/index.html and replace the app (use_directory_urls)."""
    assert not (DOCS / "explorer.md").exists()
    assert (DOCS / "explorer" / "index.html").is_file()


def test_generated_outputs_are_gitignored_not_tracked():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for path in ("docs_src/api-reference/", "docs_src/cli-reference.md", "docs_src/stability.md", "docs_src/changelog.md",
                 "docs_src/getting-started.md", "docs_src/explorer/api.json", "docs_src/explorer/library.json", "_site/"):
        assert path in ignore, f"{path} is generated and must be gitignored"


def test_docs_workflow_is_pinned_hash_locked_and_deploys_only_when_public():
    wf = WORKFLOW.read_text(encoding="utf-8")
    uses = re.findall(r"uses:\s*(\S+)", wf)
    vetted = {"actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
              "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
              "actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9",
              "actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346"}
    assert uses and set(uses) <= vetted, f"unvetted action pin (a new pin needs a @security row): {set(uses) - vetted}"
    assert "--require-hashes" in wf and "secrets." not in wf
    parsed = yaml.safe_load(wf)
    triggers = parsed.get("on", parsed.get(True))  # PyYAML reads the bare key `on` as True
    assert set(triggers) == {"pull_request", "push", "schedule", "workflow_dispatch"}, triggers
    assert parsed["permissions"] == {"contents": "read"}
    deploy = parsed["jobs"]["deploy"]
    assert "!github.event.repository.private" in deploy["if"] and "refs/heads/main" in deploy["if"]
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
    upload = next(s for s in parsed["jobs"]["build"]["steps"] if "upload-pages-artifact" in str(s.get("uses", "")))
    assert "!github.event.repository.private" in upload["if"]


def test_docs_requirements_are_all_hashed():
    text = (ROOT / ".github" / "ci" / "requirements-docs.txt").read_text(encoding="utf-8")
    reqs = re.findall(r"^([A-Za-z0-9_.-]+)==\S+ \\\n((?:\s+--hash=sha256:[0-9a-f]{64}(?: \\)?\n?)+)", text, re.M)
    names = re.findall(r"^([A-Za-z0-9_.-]+)==", text, re.M)
    assert names and len(reqs) == len(names), "every pinned requirement carries at least one sha256 hash"
    for needed in ("mkdocs", "mkdocs-material", "jsonschema"):
        assert needed in names


def test_readme_links_the_site_at_the_top():
    head = (ROOT / "README.md").read_text(encoding="utf-8").split("\n## ", 1)[0]
    assert SITE_URL in head
