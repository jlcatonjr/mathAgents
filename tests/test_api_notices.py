"""The dossier validator's non-blocking pin-stamp warnings reach the API as ``notices`` (T6, audit finding H3).

The CLI prints them as ``WARN`` lines; ``validate_dossiers`` (and so ``require_stage``, ``require_fidelity`` and
``run_gates``) returns them in ``GateResult.notices``. They never change the verdict. These tests stub the
validator's ``run`` so that they need no kernel report.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api_fixtures import ROOT  # noqa: E402

from mathagents import _scripts, dossiers, fidelity  # noqa: E402

WARN = "demo: fidelity.json: D.t was recorded under toolchain_pin X, not the current Y: it predates a bump"


def _stub(monkeypatch, errs, warns):
    vd = _scripts.gate("validate_dossier")
    seen = {}
    monkeypatch.setattr(vd, "run", lambda r, named, fid, stages, *a, **k: (list(errs), [("demo", bool(fid))]))

    def stamp(root, slugs):
        seen["slugs"] = slugs
        if isinstance(warns, Exception):
            raise warns
        return list(warns)
    monkeypatch.setattr(vd, "stamp_warnings", stamp)
    return seen


def test_warnings_become_notices_and_do_not_change_the_verdict(monkeypatch):
    seen = _stub(monkeypatch, [], [WARN])
    res = dossiers.validate_dossiers(root=ROOT)
    assert res.success and res.notices == [WARN] and seen["slugs"] == ["demo"]
    assert dossiers.require_stage(root=ROOT, slug="demo", stage=2).notices == [WARN]
    assert fidelity.require_fidelity(root=ROOT, slug="demo").notices == [WARN]


def test_a_failing_run_still_carries_its_notices(monkeypatch):
    _stub(monkeypatch, ["demo: something failed"], [WARN])
    res = dossiers.validate_dossiers(root=ROOT)
    assert not res.success and res.errors == ["demo: something failed"] and res.notices == [WARN]


def test_no_warnings_means_no_notices(monkeypatch):
    _stub(monkeypatch, [], [])
    assert dossiers.validate_dossiers(root=ROOT).notices == []


def test_an_unreadable_pin_is_a_notice_not_an_error(monkeypatch):
    _stub(monkeypatch, [], OSError("no lean/"))
    res = dossiers.validate_dossiers(root=ROOT)
    assert res.success and len(res.notices) == 1 and res.notices[0].startswith("pin-stamp check skipped")
