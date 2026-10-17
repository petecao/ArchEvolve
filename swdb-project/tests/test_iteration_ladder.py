"""The iteration ladder renderer: rows from campaign state, its closed-field check and the leakage controls.

Created: 2026-10-14 ET (Probata proof of concept, ticket 17). Design: formal-verification map decision 28
(items 2-4 and 7, build items); D8's leakage rules. The renderer is the seam: campaign state plus the
levels known now in, `LADDER.json` text out. The campaign-level placement tests (`swdb campaign --fixture`)
are in test_iteration_ladder_campaign.py. Every record ID and number here is made up for the test.
"""

import copy
import json

import pytest

from swdb import campaign as campaign_module
from swdb import iteration_ladder as ladder
from swdb.extensa import search as S

READ = "contract.bfs_read_offload"
BASE = "fork_scalar_tdstep"


def comparisons(ratio, lower, spread, other_spread=0.3):
    """The base-source comparison first, then another baseline whose spread must never reach the row."""
    return [{"baseline_role": "upstream_do_bfs", "comparison": "cmp.other", "ratio": 0.9, "lower": 0.89,
             "spread": other_spread, "verdict": "no_gain", "baseline_evaluation": "eval.base.other"},
            {"baseline_role": BASE, "comparison": "cmp.base", "ratio": ratio, "lower": lower, "spread": spread,
             "verdict": "gain", "baseline_evaluation": "eval.base"}]


def certified(cid, cls, ratio, lower, spread, jobs=None, refuted=False, **extra):
    entry = {"id": cid, "class": cls, "patch_sha256": "0" * 64, "knobs": {"chunk": 4}, "contracts": [READ],
             "certification": {"record": f"cert.{cid}", "records": [{"contract": READ, "record": f"cert.{cid}"}],
                               "outcome": "certified", "level_at_summary": "certified"},
             "comparisons": [] if refuted else comparisons(ratio, lower, spread), "level": "certified",
             "selection": None if refuted else {"lower": lower, "verdict": "gain", "ratio": ratio},
             "artifact_sha256": "1" * 64}
    if jobs is not None:
        entry["bounded_gate"] = {"refuted": refuted, "jobs": jobs, "refutations": ["proof.r"] if refuted else []}
    entry.update(extra)
    return entry


PROVEN = [{"contract": READ, "rung": "threads_1", "verdict": "proven"},
          {"contract": READ, "rung": "threads_k", "verdict": "proven"}]
TIMEOUT_K = [{"contract": READ, "rung": "threads_1", "verdict": "proven"},
             {"contract": READ, "rung": "threads_k", "verdict": "not_proven", "failure_class": "timeout"}]
REFUTED_1 = [{"contract": READ, "rung": "threads_1", "verdict": "refuted"},
             {"contract": READ, "rung": "threads_k", "verdict": "proven"}]


def state():
    """Three iterations: a gain and a pre-build rejection; an empty rewrite call; a refuted candidate artifact,
    its counterexample repair and a certification failure with a surviving negative control."""
    one = [certified("c1.k", "kronecker", 1.2, 1.19, 0.05, jobs=TIMEOUT_K),
           {"id": None, "class": "uniform_random", "patch_sha256": "2" * 64, "knobs": {}, "contracts": ["contract.x"],
            "certification": None, "comparisons": [], "level": "rejected", "selection": None,
            "rejection": "contract contract.x is outside the campaign's contracts",
            "rejection_reason": "provider_output_invalid"}]
    three = [certified("c3.k", "kronecker", None, None, None, jobs=REFUTED_1, refuted=True,
                       counterexample_repair={"state": "repaired", "repairs": ["c3.k.r1"]}),
             certified("c3.k.r1", "kronecker", 1.5, 1.48, 0.04, jobs=PROVEN,
                       repaired_from={"candidate": "c3.k", "round": 1, "proposal": "p.r1", "trigger": "proof.r",
                                      "reverted_repair": False}),
             {"id": "c3.u", "class": "uniform_random", "patch_sha256": "3" * 64, "knobs": {"chunk": 8},
              "contracts": [READ], "comparisons": [], "level": "rejected", "selection": None,
              "certification": {"record": "cert.c3.u", "records": [], "outcome": "failed",
                                "level_at_summary": "failed", "failed_checks": ["verifier", "control:fixture_control"]},
              "rejection": "named", "rejection_reason": "certification_failed",
              "rejection_failed_checks": ["verifier", "negative_controls_not_rejected"]}]
    return {"rewrite_workspace": "v2", "iterations": [
        {"index": 1, "candidates": one, "feedback_reasons": ["certified", "provider_output_invalid", "verdict_gain"],
         "winners": [{"class": "kronecker", "candidate": "c1.k", "winner": "both"}]},
        {"index": 2, "candidates": [], "feedback_reasons": ["provider_output_invalid"],
         "winners": [{"class": "kronecker", "candidate": "c1.k", "winner": "both"}]},
        {"index": 3, "candidates": three, "feedback_reasons": ["certification_failed", "certified", "refuted"],
         "winners": [{"class": "kronecker", "candidate": "c3.k.r1", "winner": "both"}]}]}


LEVELS = {"c1.k": {"level": "proven_within_bounds_threads_1", "refuted": {"flag": False}},
          "c3.k": {"level": "certified", "refuted": {"flag": True}},
          "c3.k.r1": {"level": "proven_within_bounds_threads_k", "refuted": {"flag": False}},
          "c3.u": {"level": "uncertified", "refuted": {"flag": False}}}


def rendered(st=None, levels=None):
    return json.loads(ladder.render(st or state(), LEVELS if levels is None else levels, BASE))


# --- rows from state ---------------------------------------------------------------------------------------

def test_one_row_per_earlier_candidate_artifact_with_the_decided_columns_and_no_gaps():
    found = rendered()
    assert found["format"] == ladder.FORMAT == "swdb.iteration-ladder.v1"     # the renderer's version, in the file
    assert found["rows"] == [
        {"row": 1, "iteration": 1, "class": "kronecker", "contracts": [READ], "knobs": {"chunk": 4},
         "level": "proven_within_bounds_threads_1", "verdict": "gain", "ratio": 1.2, "lower": 1.19, "spread": 0.05,
         "reason_codes": ["certified", "proof_timeout", "verdict_gain"], "failed_checks": [], "winner": "",
         "repair_of": None},
        {"row": 2, "iteration": 1, "class": "uniform_random", "contracts": ["contract.x"], "knobs": {},
         "level": "rejected", "verdict": None, "ratio": None, "lower": None, "spread": None,
         "reason_codes": ["provider_output_invalid"], "failed_checks": [], "winner": "", "repair_of": None},
        {"row": 3, "iteration": 2, "class": "-", "contracts": [], "knobs": {}, "level": "rejected", "verdict": None,
         "ratio": None, "lower": None, "spread": None, "reason_codes": ["provider_output_invalid"],
         "failed_checks": [], "winner": "", "repair_of": None},
        {"row": 4, "iteration": 3, "class": "kronecker", "contracts": [READ], "knobs": {"chunk": 4},
         "level": "refuted", "verdict": None, "ratio": None, "lower": None, "spread": None,
         "reason_codes": ["certified", "refuted"], "failed_checks": ["bounded_threads_1"], "winner": "",
         "repair_of": None},
        {"row": 5, "iteration": 3, "class": "kronecker", "contracts": [READ], "knobs": {"chunk": 4},
         "level": "proven_within_bounds_threads_k", "verdict": "gain", "ratio": 1.5, "lower": 1.48, "spread": 0.04,
         "reason_codes": ["certified", "verdict_gain"], "failed_checks": [], "winner": "both", "repair_of": 4},
        {"row": 6, "iteration": 3, "class": "uniform_random", "contracts": [READ], "knobs": {"chunk": 8},
         "level": "rejected", "verdict": None, "ratio": None, "lower": None, "spread": None,
         "reason_codes": ["certification_failed"], "failed_checks": ["verifier", "negative_controls_not_rejected"],
         "winner": "", "repair_of": None}]


def test_no_row_cap():
    st = state()
    st["iterations"] = [dict(copy.deepcopy(st["iterations"][1]), index=i) for i in range(1, 41)]
    assert [r["iteration"] for r in rendered(st)["rows"]] == list(range(1, 41))


def test_levels_are_those_known_now_and_proven_unbounded_never_appears():
    levels = {**LEVELS, "c3.k.r1": {"level": "proven_unbounded", "refuted": {"flag": False}}}
    rows = rendered(levels=levels)["rows"]
    assert {r["level"] for r in rows} <= set(ladder.LEVELS)
    assert "proven_unbounded" not in ladder.LEVELS
    # Assumption (ticket 17 Notes): a proven-unbounded level during the loop shows the highest bounded rung.
    assert rows[4]["level"] == "proven_within_bounds_threads_k"
    # A level the rule no longer reads (no record) falls back to the entry's own level; certified stays certified.
    assert rendered(levels={})["rows"][0]["level"] == "certified"


def test_winner_marks_follow_the_last_iterations_winner_rows():
    st = state()
    st["iterations"][-1]["winners"] = [{"class": "kronecker", "candidate": "c1.k", "winner": "fastest"},
                                       {"class": "kronecker", "candidate": "c3.k.r1", "winner": "best_proven"}]
    marks = {r["row"]: r["winner"] for r in rendered(st)["rows"]}
    assert marks == {1: "fastest", 2: "", 3: "", 4: "", 5: "best_proven", 6: ""}


def test_the_file_is_deterministic_from_state():
    assert ladder.render(state(), LEVELS, BASE) == ladder.render(state(), LEVELS, BASE)


# --- workspace version ------------------------------------------------------------------------------------

def test_workspace_version_reads_v1_when_absent_and_only_v2_from_iteration_2_has_a_ladder():
    assert ladder.version_of({}) == "v1" and ladder.version_of({"rewrite_workspace": "v2"}) == "v2"
    assert not ladder.shown({"rewrite_workspace": "v2"}, 1)
    assert ladder.shown({"rewrite_workspace": "v2"}, 2)
    assert not ladder.shown({}, 5)                                   # a v1 campaign never gains one


def test_a_campaign_file_naming_rewrite_workspace_is_refused():
    from testkit.extensa import campaign_file
    import yaml
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        team = {"root": Path(tmp), "machine": "native-testhost", "baseline": "b", "candidate": "c",
                "kronecker": "w.k", "uniform": "w.u"}
        data = yaml.safe_load(campaign_file(team).read_text())
    assert not campaign_module.campaign_problems(copy.deepcopy(data))      # control: the file is otherwise fine
    problems = campaign_module.campaign_problems({**data, "rewrite_workspace": "v1"})
    assert problems and any("rewrite_workspace" in p for p in problems)


# --- reason codes ----------------------------------------------------------------------------------------

def test_refuted_and_proof_timeout_join_the_closed_feedback_reasons():
    for code in ("refuted", "proof_timeout"):
        assert code in S.FEEDBACK_REASONS
        S.Feedback(code, "The bounded gate result for this class.", {"class": "kronecker",
                                                                     "failed_checks": ["bounded_threads_1"]})
    with pytest.raises(S.FeedbackError):                           # control: the set stays closed
        S.Feedback("proven_unbounded", "The bounded gate result for this class.")


# --- leakage: planted in campaign state, kept out by the closed-field check -----------------------------------

CEX = "SECRET-COUNTEREXAMPLE parent[2] differs"
PATCH_BODY = "--- a/src/bfs.cc\n+++ b/src/bfs.cc\n@@ -1 +1 @@\n-SECRET-PATCH\n"


def planted():
    st = state()
    entry = st["iterations"][0]["candidates"][0]
    entry["bounded_gate"]["counterexample"] = CEX                       # counterexample text
    entry["counterexample"] = {"format": "swdb.counterexample.v1", "witness": CEX}
    entry["comparisons"][1]["duration_s"] = 12.3456789                   # a raw timing
    entry["timing"] = [{"source_position": 0, "duration_s": 98.7654321}]
    entry["_patch"] = PATCH_BODY                                         # a patch body
    entry["patch"] = PATCH_BODY
    entry["certification"]["failed_checks"] = ["control:secret_control_7"]   # a detailed surviving control
    entry["secret_unknown_field"] = "SECRET-UNKNOWN"                     # an unknown field
    return st


LEAKS = ("SECRET-COUNTEREXAMPLE", "swdb.counterexample.v1", "12.3456789", "98.7654321", "SECRET-PATCH",
         "secret_control_7", "control:", "SECRET-UNKNOWN", "secret_unknown_field", "duration", "timing")


def test_planted_leaks_never_reach_the_file():
    st = planted()
    text = ladder.render(st, LEVELS, BASE)
    # Negative control: each planted value really is in the state the renderer reads.
    raw = json.dumps(st)
    assert all(leak in raw for leak in LEAKS)
    assert not [leak for leak in LEAKS if leak in text]
    # The surviving control is shown only as the one aggregate category.
    assert json.loads(text)["rows"][0]["failed_checks"] == ["negative_controls_not_rejected"]


def good_row():
    return json.loads(ladder.render(state(), LEVELS, BASE))["rows"][4]


@pytest.mark.parametrize("change", [
    {"counterexample": CEX},                                              # counterexample field
    {"class": "kronecker " + json.dumps({"format": "swdb.counterexample.v1"})},   # counterexample text in a value
    {"duration_s": 12.3},                                                 # a raw timing
    {"timing": [1.0]},
    {"patch": PATCH_BODY},                                                # a patch body
    {"failed_checks": ["control:secret_control_7"]},                      # a detailed surviving control
    {"secret_unknown_field": 1},                                          # an unknown field
    {"reason_codes": ["counterexample_text"]},                            # a reason code outside the closed set
    {"level": "proven_unbounded"},                                        # never in the loop
    {"winner": "promote"},
    {"ratio": "1.2 seconds"},
])
def test_the_closed_field_check_refuses_each_leak(change):
    row = good_row()
    ladder.check_row(row)                                                  # control: the row passes as built
    with pytest.raises(ladder.LadderError):
        ladder.check_row({**row, **change})


def test_a_patch_body_in_a_knob_value_is_refused():
    row = good_row()
    with pytest.raises(ladder.LadderError):
        ladder.check_row({**row, "knobs": {"chunk": PATCH_BODY}})


def test_the_rewrite_prompt_names_the_ladder_only_when_the_workspace_holds_it():
    files = {"source/bfs.cc": "", "REGIONS.json": "{}", "FEEDBACK.json": "{}"}
    without = campaign_module.rewrite_prompt("c", 2, ["kronecker"], files)
    with_ladder = campaign_module.rewrite_prompt("c", 2, ["kronecker"], {**files, "LADDER.json": "{}"})
    assert "LADDER.json" not in without                                 # control
    assert "`LADDER.json` is the iteration ladder" in with_ladder
