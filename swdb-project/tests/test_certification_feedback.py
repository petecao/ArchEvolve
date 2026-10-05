"""Campaign feedback names the failing certification check (ticket 64).

Created: 2026-10-04 ET. Campaign a6 (ticket 57) told the provider only "Certification failed a
named check" while every edit hit the strict layer's `range_bounds`. The feedback and the repair
workspace now name the check and its public precondition, never run output; the rewrite
workspace carries the non-normative intrinsic usage notes.
"""

import json

import pytest

from swdb import campaign, campaign_targets, certification_feedback as F
from swdb.extensa import search as S
from swdb.library import Library
from conftest import REPO
from test_extensa_campaign import knob_rows, provider
from test_extensa_targets import (CONTRACT, FakeHost, FakeRunner, base_source, gem5_campaign,  # noqa: F401
                                  inside_patch, run, team, team_template)

SECRET = "SWDB trusted_frontier=12345 graph=/data1/secret.sg"


def failed_cell(name):
    return {"tile_size": 1024, "status": "failed", "reason": "strict_layer_assertion",
            "run": {"stdout": SECRET + "\n", "stderr": f"SWDB_STRICT_ASSERT:{name}\n", "returncode": 86}}


def failing_record(name="range_bounds"):
    return {"id": "certification.fixture.failed", "verdict": "failed",
            "matrix": [failed_cell(name), failed_cell(name), {"tile_size": 16384, "status": "passed"}],
            "negative_controls": [{"id": "dropped_wait", "status": "invalid"},
                                  {"id": "index_wrap", "status": "rejected"}]}


def test_matrix_checks_name_the_strict_check_from_its_own_assertion_line():
    names, counts, cells = F.matrix_checks(failing_record())
    assert names == ["strict_layer_assertion:range_bounds"] and counts[names[0]] == 2 and cells == 3
    # a strict failure without an assertion line keeps the generic reason
    bare = {"matrix": [{"status": "failed", "reason": "strict_layer_assertion", "run": {"stdout": "", "stderr": ""}}]}
    assert F.matrix_checks(bare)[0] == ["strict_layer_assertion"]


def test_explanation_names_range_bounds_and_the_continuation_convention():
    text = F.explanation(["control:dropped_wait", "strict_layer_assertion:range_bounds"])
    assert text.startswith("Certification failed. range_bounds: __dxc_range_loop")
    assert "last_i_reg = 0" in text and "last_j_reg = -1" in text
    assert "Negative controls not rejected (1): dropped_wait." in text and len(text) <= 400


def test_a_passing_matrix_with_a_surviving_control_names_the_control():
    assert F.explanation(["control:forged_frontier"]) == \
        "Certification failed. Negative controls not rejected (1): forged_frontier."


@pytest.mark.parametrize("check", sorted(F.STRICT_MESSAGES))
def test_every_strict_message_is_valid_closed_feedback(check):
    text = F.explanation([f"strict_layer_assertion:{check}", "control:shared_context"])
    S.Feedback("certification_failed", text, {"class": "kronecker", "failed_checks": [check]})


def test_long_check_lists_stay_within_the_feedback_limit():
    checks = [f"strict_layer_assertion:{c}" for c in F.STRICT_MESSAGES] + ["control:x"] * 3
    text = F.explanation(checks)
    assert len(text) <= 400 and "range_bounds" in text
    S.Feedback("certification_failed", text, {})


def test_strict_messages_cover_every_check_the_strict_layer_and_header_name():
    import re
    sources = (REPO / "library/dx100/strict/MAA_functional.hpp").read_text() + \
        (REPO / "library/dx100/dxc_lowering.hpp").read_text()
    named = set(re.findall(r'check\([^;]*?"([a-z_]+)"\)', sources))
    assert named and named <= set(F.STRICT_MESSAGES)


def test_target_adapter_reports_the_named_strict_check(tmp_path):
    adapter = campaign_targets.TargetAdapter.__new__(campaign_targets.TargetAdapter)
    adapter._certify = lambda store, contract, **kw: failing_record()
    adapter.store_dir, adapter.folder, adapter.library_root = tmp_path, tmp_path, REPO / "library"
    outcome = adapter.certify({"id": "candidate.fixture"}, [CONTRACT], 1, "kronecker", 0)
    assert outcome["outcome"] == "failed"
    assert outcome["failed_checks"] == ["control:dropped_wait", "strict_layer_assertion:range_bounds"]


def test_usage_notes_are_outside_the_normative_entries():
    library = Library(REPO / "library")
    notes = sorted((REPO / "library/intrinsics/notes").glob("*.md"))
    assert {n.stem for n in notes} >= {"dxc_range_loop", "dxc_stream_load", "dxc_const_i32"}
    assert not any(str(path).endswith(".md") for path in library.files.values())
    text = (REPO / "library/intrinsics/notes/dxc_range_loop.md").read_text()
    assert "`last_i_reg` to **0** and `last_j_reg` to **-1**" in text
    # the notes never carry the authors' accelerated code names
    from swdb.provider_roles import FORBIDDEN_SOURCE
    assert not any(FORBIDDEN_SOURCE.search(n.read_text()) for n in notes)


def test_gem5_campaign_feedback_and_repair_name_the_check_without_run_output(team, base_source, monkeypatch):
    patch = inside_patch(base_source)
    answer = {"patch": patch, "contracts": [CONTRACT], "knobs": knob_rows({}), "unresolved": []}
    config = provider(team, {"rewriting": [answer], "repair": [answer]})
    monkeypatch.setattr("test_extensa_targets.fake_certify", lambda store, contract, **kw: failing_record())
    seen = []
    original = campaign.Campaign._call

    def spy(self, kind, files, prompt, row):
        seen.append({"kind": kind, "files": dict(files), "prompt": prompt})
        return original(self, kind, files, prompt, row)
    monkeypatch.setattr(campaign.Campaign, "_call", spy)
    _, summary = run(team, gem5_campaign(team, max_iterations=2), config, FakeRunner({}), FakeHost())
    rows = [c for it in summary["iterations"] for c in it["candidates"]]
    assert rows and all(r["level"] == "rejected" for r in rows)
    assert all("range_bounds" in r["rejection"] and "last_i_reg = 0" in r["rejection"] for r in rows)
    assert all("strict_layer_assertion:range_bounds" in r["certification"]["failed_checks"] for r in rows)
    repairs = [s for s in seen if s["kind"] == "repair"]
    assert repairs
    report = json.loads(repairs[0]["files"]["CERTIFICATION.json"])
    # Ticket 76 (2026-10-05 ET): matrix checks first; the surviving control (dropped_wait) reaches
    # the provider only as the aggregate category, last; the campaign record keeps its name.
    assert report["failed_checks"] == ["strict_layer_assertion:range_bounds", "negative_controls_not_rejected"]
    assert [m["check"] for m in report["messages"]] == report["failed_checks"]
    assert all("control:dropped_wait" in r["certification"]["failed_checks"] for r in rows)
    assert not any("dropped_wait" in r["rejection"] for r in rows)
    # (The contract file in the workspace lists every control; which one survived is never said.)
    assert not any("dropped_wait" in s["files"].get(name, "") or "dropped_wait" in s["prompt"]
                   for s in seen for name in ("FEEDBACK.json", "CERTIFICATION.json"))
    rewrites = [s for s in seen if s["kind"] == "rewriting"]
    assert "library/intrinsics/notes/dxc_range_loop.md" in rewrites[0]["files"]
    assert "`last_i_reg` = 0 and `last_j_reg` = -1" in rewrites[0]["prompt"]
    feedback = json.loads(rewrites[1]["files"]["FEEDBACK.json"])["feedback"]
    assert any("range_bounds" in f["explanation"] for f in feedback)
    # nothing from the run output reaches the provider
    for s in seen:
        assert not any("trusted_frontier" in text or "secret.sg" in text for text in s["files"].values())
