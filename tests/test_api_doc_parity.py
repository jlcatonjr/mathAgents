"""docs/api-reference/ <-> mathagents parity (agentteams pattern)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("check_api_doc_parity", ROOT / "scripts" / "check_api_doc_parity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # registered before exec so the dataclass resolves
    spec.loader.exec_module(mod)
    return mod


parity = _load()


def test_no_stale_pages_or_missing_symbols():
    res = parity.compute_parity(ROOT / "mathagents", ROOT / "docs" / "api-reference")
    assert res.stale_pages == [] and res.missing_symbols == []


def test_full_coverage():
    res = parity.compute_parity(ROOT / "mathagents", ROOT / "docs" / "api-reference")
    assert res.coverage_gaps == [] and res.undocumented_symbols == []
    assert len(res.documented) >= 15


def test_fake_page_is_stale(tmp_path):
    (tmp_path / "no-such-module.md").write_text("# x\n")
    res = parity.compute_parity(ROOT / "mathagents", tmp_path)
    assert res.stale_pages == ["no-such-module"]


def test_documented_heading_not_in_all_is_missing(tmp_path):
    (tmp_path / "kernel.md").write_text("### `not_a_symbol()`\n")
    res = parity.compute_parity(ROOT / "mathagents", tmp_path)
    assert "kernel.not_a_symbol" in res.missing_symbols


def test_empty_package_makes_every_page_stale(tmp_path):
    res = parity.compute_parity(tmp_path, ROOT / "docs" / "api-reference")
    assert res.documented == [] and len(res.stale_pages) >= 15


def test_main_strict_passes():
    assert parity.main(["--strict"]) == 0


def test_dash_names_map_to_underscored_modules():
    res = parity.compute_parity(ROOT / "mathagents", ROOT / "docs" / "api-reference")
    assert "name_index" in res.documented
