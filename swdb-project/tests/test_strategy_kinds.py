"""The remaining effect kinds and target types, the seed strategies, common intrinsics, the
prefetch update kind, and the loop and input strategy queries. Created 2026-09-23."""

import json

import pytest

from test_strategies import edit, other_strategy, passes, pattern, query, rejected

SEEDS = ["dx100_read_offload", "loop_tiling", "packing", "simd_gather", "software_prefetch", "vertex_reordering"]
GATHER = "strategies/simd_gather.yaml"
TILING = "strategies/loop_tiling.yaml"
REORDER = "strategies/vertex_reordering.yaml"
PREFETCH = "strategies/software_prefetch.yaml"
JAC = "implementations/gapbs-pr-jacobi.yaml"
GS = "implementations/gapbs-pr-gs.yaml"


@pytest.fixture
def repo(records):
    return records.copy_repo()


def test_all_five_seeds_validate_and_are_not_duplicates(repo):
    passes(repo.validate())
    rows = query(repo, "sql", "select id, target from strategies order by id")
    assert [r["id"] for r in rows] == SEEDS
    assert {r["id"]: r["target"] for r in rows}["loop_tiling"] == "loop"
    assert {r["id"]: r["target"] for r in rows}["vertex_reordering"] == "input"


# --- effect kinds: one passing (the seeds) and one failing fixture each ---------------

def test_hint_needs_a_step(repo):
    edit(repo, PREFETCH, lambda d: d["effect"][0].pop("step"))
    rejected(repo.validate(), "effect[0].step", "a hint effect needs step")


def test_widen_lanes_is_a_number_or_a_declared_parameter(repo):
    edit(repo, GATHER, lambda d: d["effect"][0].update(lanes="width"))
    rejected(repo.validate(), "effect[0].lanes", "'width' is not a parameter of this strategy")
    edit(repo, GATHER, lambda d: d["effect"][0].update(lanes=1))
    rejected(repo.validate(), "effect[0].lanes", "lanes is a number of at least 2")
    edit(repo, GATHER, lambda d: d["effect"][0].update(lanes=16))
    passes(repo.validate())


def test_widen_lanes_value_is_not_part_of_the_identity(repo):
    data = repo.read(GATHER)
    data.update(id="gather-8", parameters=[])
    data["effect"][0]["lanes"] = 8
    repo.write("strategies/gather-8.yaml", data)
    rejected(repo.validate(), "strategies/gather-8.yaml", "duplicate strategy: 'simd_gather'")


def test_software_prefetch_and_simd_gather_differ(repo):
    # same target, different effects: a hint is not a widen
    edit(repo, GATHER, lambda d: d.update(preconditions=repo.read(PREFETCH)["preconditions"]))
    passes(repo.validate())


def test_reorder_needs_input_properties(repo):
    edit(repo, REORDER, lambda d: d["effect"][0].update(properties=["colour"]))
    rejected(repo.validate(), "effect[0].properties[0]", "not in vocabulary input_properties")


def test_reorder_index_locality_must_be_listed_and_known(repo):
    edit(repo, REORDER, lambda d: d["effect"][0].update(properties=["degree_distribution"]))
    rejected(repo.validate(), "effect[0].index_locality", "lists index_locality in properties")
    edit(repo, REORDER, lambda d: d["effect"][0].update(properties=["index_locality"], index_locality="tidy"))
    rejected(repo.validate(), "effect[0].index_locality", "not in vocabulary index_localities")


def test_restructure_loop_needs_a_known_restructure(repo):
    edit(repo, TILING, lambda d: d["effect"][0].update(restructure="unroll"))
    rejected(repo.validate(), "effect[0].restructure", "not in vocabulary loop_restructures")


@pytest.mark.parametrize("rel, effect", [
    (TILING, {"kind": "hint", "step": 0}),
    (PREFETCH, {"kind": "restructure_loop", "restructure": "tile"}),
    (REORDER, {"kind": "widen", "lanes": 4}),
])
def test_effect_must_suit_the_target(repo, rel, effect):
    edit(repo, rel, lambda d: d.update(effect=[effect]))
    rejected(repo.validate(), rel, "does not apply to target")


def test_loop_and_input_targets_pass(repo):
    passes(repo.validate())
    assert repo.read(TILING)["target"] == "loop" and repo.read(REORDER)["target"] == "input"


def test_input_strategy_preconditions_are_prose(repo):
    edit(repo, REORDER, lambda d: d["preconditions"].update(
        requires_semantics=[{"field": "loop_carried_dependencies", "value": False}]))
    rejected(repo.validate(), REORDER, "an input strategy's preconditions are prose")


# --- common intrinsics and the prefetch update kind ---------------------------------

def test_common_intrinsics_must_resolve(repo):
    edit(repo, GATHER, lambda d: d.update(common_intrinsics=["mm512_i32gather_pd"]))
    rejected(repo.validate(), "common_intrinsics[0]", "refers to intrinsic 'mm512_i32gather_pd', which does not exist")
    edit(repo, GATHER, lambda d: d.update(common_intrinsics=["packing"]))
    rejected(repo.validate(), "common_intrinsics[0]", "'packing', which is a strategy")


def test_common_intrinsics_are_in_the_database(repo):
    rows = query(repo, "sql", "select strategy, intrinsic from strategy_intrinsics order by strategy")
    assert rows == [{"strategy": "simd_gather", "intrinsic": "mm512_i32gather_ps"},
                    {"strategy": "software_prefetch", "intrinsic": "mm_prefetch"}]


def test_prefetch_update_kind(repo):
    def add_prefetch(d):
        p = json.loads(json.dumps(pattern(d, "gather-contrib")))
        p.update(id="prefetch-contrib", update_kind="prefetch", expression="_mm_prefetch(&contrib[neigh[e + d]])")
        d["access_patterns"].append(p)
    edit(repo, JAC, add_prefetch)
    passes(repo.validate())
    edit(repo, JAC, lambda d: pattern(d, "prefetch-contrib").update(update_kind="prefetch_ish"))
    rejected(repo.validate(), "update_kind", "not in vocabulary update_kinds")


# --- queries -------------------------------------------------------------------------

def loop_rule(repo):
    """A loop strategy whose precondition some patterns fail, to exercise the loop query."""
    data = repo.read(TILING)
    data["preconditions"]["requires_semantics"] = [{"field": "loop_carried_dependencies", "value": False}]
    repo.write(TILING, data)


def by_id(found):
    return {e["strategy"]: e for e in found}


def test_pattern_query_lists_every_access_pattern_strategy(repo):
    found = by_id(query(repo, "strategies", "--pattern", "gapbs-pr-jacobi/gather-contrib"))
    assert sorted(found) == ["dx100_read_offload", "packing", "simd_gather", "software_prefetch"]
    assert all(e["outcome"] == "legal" for e in found.values())


def test_loop_query_is_legal_when_every_pattern_passes(repo):
    loop_rule(repo)
    [found] = query(repo, "strategies", "--loop", "gapbs-pr-jacobi/sweep")
    assert (found["strategy"], found["outcome"], found["reasons"]) == ("loop_tiling", "legal", [])
    assert found["check_by_hand"] == repo.read(TILING)["preconditions"]["unchecked"]


def test_loop_query_one_failing_pattern_in_a_child_loop_makes_it_illegal(repo):
    loop_rule(repo)
    # gapbs-pr-gs: sweep > vertex > edge; gather-contrib in the edge loop carries a dependency
    [found] = query(repo, "strategies", "--loop", "gapbs-pr-gs/sweep")
    assert found["outcome"] == "illegal"
    assert "gather-contrib: loop_carried_dependencies is true (code_reading), needs false" in found["reasons"]
    [init] = query(repo, "strategies", "--loop", "gapbs-pr-gs/init")   # a sibling loop is unaffected
    assert init["outcome"] == "legal"


def test_loop_query_names_pattern_and_field_when_undetermined(repo):
    loop_rule(repo)
    edit(repo, JAC, lambda d: pattern(d, "gather-contrib")["semantics"].update(
        loop_carried_dependencies={"value": None, "basis": "unknown"}))
    [found] = query(repo, "strategies", "--loop", "gapbs-pr-jacobi/sweep")
    assert found["outcome"] == "undetermined"
    assert found["unknown_fields"] == ["gather-contrib.loop_carried_dependencies"]


def test_loop_query_names_a_missing_loop(repo):
    rejected(repo.swdb("strategies", "--loop", "gapbs-pr-jacobi/nope"), "loop 'gapbs-pr-jacobi/nope' does not exist")


def test_input_query_lists_input_strategies_to_check_by_hand(repo):
    [found] = query(repo, "strategies", "--input", "gapbs-pr-gs")
    assert found["strategy"] == "vertex_reordering" and found["outcome"] == "undetermined"
    assert found["check_by_hand"] == repo.read(REORDER)["preconditions"]["unchecked"]
    assert found["benefits_when"][0]["source"] == "balaji-2018"
    rejected(repo.swdb("strategies", "--input", "nope"), "implementation 'nope' does not exist")


def test_find_strategy_takes_only_access_pattern_strategies(repo):
    result = repo.swdb("find", "--strategy", "loop_tiling")
    assert result.returncode == 2 and "targets loop, not access_pattern" in result.stderr


def test_strategies_needs_exactly_one_target(repo):
    assert repo.swdb("strategies").returncode == 2
    assert repo.swdb("strategies", "--input", "gapbs-pr-gs", "--loop", "gapbs-pr-gs/sweep").returncode == 2
