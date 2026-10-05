"""Extensa campaign structure after the 2026-10-05 code review. Created 2026-10-05 ET.

The speed rule is one object whose verdict is the evaluator's `decision.state` (F1); every target
adapter, the contract fixture included, answers the loop's per-target questions (F13); the C++
lexing helper ignores braces in comments and literals (F12); one campaign-ID pattern; knob ranges
live in the library. Numbers here are fixtures, never evidence.
"""

import copy
import json
import re
from pathlib import Path

import pytest

from conftest import REPO
from swdb import campaign, campaign_targets, cpp_lexical, yamlio
from swdb.store import Store

A8 = REPO / "campaigns/extensa/extensa-native-bfs-20261005-a8.yaml"
GEM5 = REPO / "campaigns/extensa/extensa-gem5-bfs-20261004-a7.yaml"


# --- the speed rule ------------------------------------------------------------------------

@pytest.mark.parametrize("state, verdict", [("gain", "gain"), ("no_gain", "no_gain"),
                                            ("inconclusive", "inconclusive"), ("regression", "no_gain")])
def test_verdict_is_the_evaluators_decision_state(state, verdict):
    rule = campaign.SpeedRule.of(yamlio.load(A8))
    # Numbers that would say `gain` under the rule: the evaluator's state wins.
    numbers = {"ratio": 1.4, "lower": 1.39, "upper": 1.41, "spreads": [0.0], "state": state}
    assert rule.verdict(numbers) == verdict


def test_fixture_comparisons_are_judged_from_their_numbers():
    rule = campaign.SpeedRule.of(yamlio.load(A8))
    wide = {"ratio": 1.4, "lower": 1.2, "upper": 1.5, "spreads": [0.0], "state": "fixture_comparison"}
    assert rule.verdict(wide) == "inconclusive"
    assert campaign.SpeedRule.of(yamlio.load(GEM5)).verdict({"ratio": 1.051, "lower": 1.051, "spreads": [0.0]}) == "gain"


def test_frozen_speed_rule_matches_the_team_protocol_derived_from_a8():
    """apply_speed_rule's output feeds frozen protocol identities: the team protocol that copies a8's fork
    settings (ticket 75) has exactly the profitability and analysis the rule writes."""
    store = Store(REPO / "records")
    team = store.get("bfs-native-scale22-ci-team-20261005.9f1ed533a09ae832", "protocol")["settings"]
    frozen = copy.deepcopy(store.get(campaign_targets.NATIVE_TEMPLATES["fork_scalar_tdstep"], "protocol")["settings"])
    campaign.SpeedRule.apply(frozen, campaign.protocol_settings(yamlio.load(A8)))
    assert json.dumps(frozen["profitability"], sort_keys=True) == json.dumps(team["profitability"], sort_keys=True)
    assert {k: frozen["sampling"][k] for k in ("analysis", "block_length", "collection")} == \
        {k: team["sampling"][k] for k in ("analysis", "block_length", "collection")}


# --- adapters answer the per-target questions --------------------------------------------------

def test_every_adapter_is_a_target_adapter_with_the_loop_hooks(tmp_path):
    from swdb.campaign_fixture import FixtureAdapter
    assert issubclass(FixtureAdapter, campaign_targets.TargetAdapter)
    native, gem5 = campaign_targets.NativeAdapter, campaign_targets.Gem5Adapter
    assert (native.HAS_PILOT, native.SHARED_BASELINE, native.POINT_RATIOS, native.EVIDENCE_BASIS) == \
        (True, False, False, "measured")
    assert (gem5.HAS_PILOT, gem5.SHARED_BASELINE, gem5.POINT_RATIOS, gem5.EVIDENCE_BASIS) == \
        (False, True, True, "simulated")
    for name in ("admit", "reference_files", "restore", "other_gem5", "workspace_region_lines", "protected_regions"):
        assert callable(getattr(FixtureAdapter, name))
    fx = tmp_path / "fixture.yaml"
    fx.write_text("format: swdb.extensa-campaign-fixture.v1\n")
    adapter = FixtureAdapter(fx, yamlio.load(GEM5), tmp_path, tmp_path / "store", tmp_path / "folder")
    assert adapter.SHARED_BASELINE and adapter.POINT_RATIOS and adapter.protected_regions() == []


def test_target_rules_of_a_campaign_file_come_from_its_adapter():
    data = yamlio.load(GEM5)
    data["protocol"]["speed_rule"] = campaign.CI_WIDTH_RULE
    data["approval"]["date"] = str(data["approval"]["date"])
    assert any("CI-width rule is native only" in p for p in campaign.campaign_problems(data))
    data = yamlio.load(A8)
    data["approval"]["date"] = str(data["approval"]["date"])
    data["approval"]["gem5_other_socket"] = True
    assert any(p.startswith("protocol.isolation") for p in campaign.campaign_problems(data))


def test_one_campaign_id_pattern_for_schemas_and_the_child_tag():
    from swdb.schemas import campaign_id_pattern
    pattern = campaign_id_pattern()
    envelope = json.loads((REPO / "schemas/envelope.schema.json").read_text())
    assert envelope["properties"]["campaign"]["$ref"] == "#/$defs/extensa_campaign_id"
    review = json.loads((REPO / "schemas/review.schema.json").read_text())
    assert review["properties"]["origin"]["properties"]["campaign"]["$ref"] == "#/$defs/extensa_campaign_id"
    assert campaign._schema()["$defs"]["extensa_campaign_id"]["pattern"] == pattern
    assert re.fullmatch(pattern, "extensa-native-bfs-20261005-a8") and not re.fullmatch(pattern, "extensa-foo")


def test_knob_ranges_are_checked_by_the_library():
    from swdb.library import Library, knob_problem
    library = Library(REPO / "library")
    assert knob_problem(library, ["contract.bfs_tdstep_frontier_staging"], {"frontier_batch": 16}) is None
    assert "outside its declared range" in knob_problem(library, ["contract.bfs_tdstep_frontier_staging"],
                                                         {"frontier_batch": 4097})
    assert "not declared" in knob_problem(library, ["contract.bfs_tdstep_frontier_staging"], {"other": 1})


# --- C++ lexing (F12) ------------------------------------------------------------------------------

SOURCE = """// int Helper() { a comment with braces }
static const char *banner = "}}} not code {{{";
int Helper(int x) {
  // a closing brace in a comment: }
  const char *s = "}";            /* and here: } */
  char c = '}';
  if (x) {
    return 1;
  }
  return 0;
}

int After() {
  return 2;
}
"""


def test_function_span_ignores_braces_in_comments_and_literals():
    assert cpp_lexical.function_span(SOURCE, "Helper") == (3, 11)
    assert cpp_lexical.function_span(SOURCE, "After") == (13, 15)
    assert cpp_lexical.enclosing_function(SOURCE, 6) == "Helper"
    assert cpp_lexical.enclosing_function(SOURCE, 12) is None
    # The re-exported names stay where the campaign adapters and tests import them.
    assert campaign_targets.function_span is cpp_lexical.function_span


@pytest.mark.parametrize("stage, reason, kind", [
    ("build", "the verifier would have run later", "build_failed"),
    ("correctness", "trial 3 timed out", "correctness_failed"),
    ("execution", "parent output exceeded the limit", "evaluation_failed"),
    (None, "parent vector failed the verifier", "correctness_failed"),      # no record: the reason text
])
def test_failed_native_block_kind_comes_from_the_evaluation_stage(stage, reason, kind):
    """Code review S15 (2026-10-05 ET): the failed stage names the refusal, not a regex over the reason."""
    class Records:
        def get(self, rid, kind=None):
            if stage is None or rid != "cand-eval":
                return None
            return {"outcome": {"state": "failed", "stage": stage, "reason": reason}}

    adapter = campaign_targets.NativeAdapter.__new__(campaign_targets.NativeAdapter)
    adapter._store = Records
    assert adapter._failure_kind(["base-eval", "cand-eval"], reason) == kind


def test_session_begin_check_is_not_fooled_by_braces_in_literals():
    source = ('pvector<NodeID> DOBFS(const Graph &g, NodeID source) {\n  const char *t = "}";\n'
              '  __dxc_session_begin();\n  return parent;\n}\n')
    assert campaign_targets.session_begin_problem(source) is None
