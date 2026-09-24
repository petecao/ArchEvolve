"""Optimization strategies: schema, rules, `swdb add`, and the legality queries
(`swdb strategies`, `swdb find --strategy`). Created 2026-09-23. Each rule has a passing
case and a failing case; every test runs swdb as a separate process."""

import copy
import json

import pytest
import yaml

PACKING = "strategies/packing.yaml"
JAC = "implementations/gapbs-pr-jacobi.yaml"


def rejected(result, *fragments):
    assert result.returncode == 1, result.stdout + result.stderr
    for fragment in fragments:
        assert fragment in result.stderr, f"{fragment!r} not in stderr:\n{result.stderr}"


def passes(result):
    assert result.returncode == 0, result.stderr


@pytest.fixture
def repo(records):
    return records.copy_repo()


def edit(records, rel, change):
    data = records.read(rel)
    change(data)
    records.write(rel, data)


def pattern(data, pid):
    return next(p for p in data["access_patterns"] if p["id"] == pid)


def query(repo, *args):
    result = repo.swdb(*args, "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def other_strategy(repo, **changes):
    """A second strategy, different from packing, to vary."""
    data = repo.read(PACKING)
    data.update(id="gather-hoist", name="Gather hoisting")
    data["effect"] = [{"kind": "add_pattern", "address_shapes": ["stream"], "update_kind": "read"}]
    data.update(changes)
    return data


# --- schema and rules ---------------------------------------------------------------

def test_packing_seed_passes(repo):
    passes(repo.validate())
    data = repo.read(PACKING)
    assert data["target"] == "access_pattern"
    assert [e["kind"] for e in data["effect"]] == ["reshape", "add_pattern", "add_pattern"]


def test_effect_kind_must_be_in_the_vocabulary(repo):
    edit(repo, PACKING, lambda d: d["effect"][0].update(kind="teleport"))
    rejected(repo.validate(), "effect[0].kind", "not in vocabulary effect_kinds")


def test_reshape_needs_its_fields(repo):
    edit(repo, PACKING, lambda d: d["effect"][0].pop("shape_after"))
    rejected(repo.validate(), "effect[0].shape_after", "a reshape effect needs step, shape_before, shape_after")


def test_effect_item_takes_no_field_of_another_kind(repo):
    edit(repo, PACKING, lambda d: d["effect"][0].update(update_kind="read"))
    rejected(repo.validate(), "effect[0]", "a reshape effect has only kind, step, shape_before, shape_after, and note")


def test_add_pattern_needs_known_shapes(repo):
    edit(repo, PACKING, lambda d: d["effect"][1].update(address_shapes=["stream", "zigzag"]))
    rejected(repo.validate(), "effect[1].address_shapes[1]", "not in vocabulary address_shapes")


def test_add_pattern_needs_its_update_kind(repo):
    edit(repo, PACKING, lambda d: d["effect"][1].pop("update_kind"))
    rejected(repo.validate(), "effect[1].update_kind", "an add_pattern effect needs address_shapes, update_kind")


def test_reshape_must_change_the_shape(repo):
    edit(repo, PACKING, lambda d: d["effect"][0].update(shape_after="single_valued_indirect"))
    rejected(repo.validate(), "effect[0].shape_after", "shape_after equals shape_before")


def test_precondition_field_must_exist(repo):
    edit(repo, PACKING, lambda d: d["preconditions"]["requires_semantics"].append(
        {"field": "loop_carried_dependency", "value": False}))
    rejected(repo.validate(), "requires_semantics[2].field", "'loop_carried_dependency' is not a semantic field")


def test_precondition_value_must_fit_the_field(repo):
    edit(repo, PACKING, lambda d: d["preconditions"]["requires_semantics"][0].update(value="no"))
    rejected(repo.validate(), "requires_semantics[0].value", "is true or false")


def test_precondition_vocabulary_value_must_exist(repo):
    edit(repo, PACKING, lambda d: d["preconditions"]["requires_semantics"].append({"field": "ordering", "value": "any"}))
    rejected(repo.validate(), "requires_semantics[2].value", "not in vocabulary orderings")
    edit(repo, PACKING, lambda d: d["preconditions"]["requires_semantics"][2].update(value="any_order"))
    passes(repo.validate())


def test_precondition_shape_must_exist(repo):
    edit(repo, PACKING, lambda d: d["preconditions"]["requires_shapes"].append("zigzag"))
    rejected(repo.validate(), "requires_shapes[1]", "not in vocabulary address_shapes")


def test_benefit_basis_must_be_reported(repo):
    edit(repo, PACKING, lambda d: d["benefits_when"][0].update(basis="measured"))
    rejected(repo.validate(), "benefits_when[0].basis", "only reported benefit")


def test_benefit_needs_a_source(repo):
    edit(repo, PACKING, lambda d: d["benefits_when"][0].pop("source"))
    rejected(repo.validate(), "benefits_when[0].source", "names its source")


def test_benefit_source_must_be_a_provenance_entry(repo):
    edit(repo, PACKING, lambda d: d["benefits_when"][0].update(source="someone"))
    rejected(repo.validate(), "benefits_when[0].source", "not a provenance entry of this record")


def test_benefit_source_must_be_a_paper_or_a_person(repo):
    def change(d):
        d["provenance"].append({"id": "run", "kind": "measurement", "description": "a run", "uri": None})
        d["benefits_when"][0]["source"] = "run"
    edit(repo, PACKING, change)
    rejected(repo.validate(), "benefits_when[0].source", "is a measurement entry")


def test_benefit_terms_must_be_metrics_properties_or_cache_sizes(repo):
    edit(repo, PACKING, lambda d: d["benefits_when"][0]["terms"].append("vibes"))
    rejected(repo.validate(), "benefits_when[0].terms[1]", "not a metric, an input property, or a machine cache size")
    edit(repo, PACKING, lambda d: d["benefits_when"][0].update(terms=["llc_bytes", "num_nodes", "speedup"]))
    passes(repo.validate())


def test_strategy_must_cite_a_source(repo):
    def change(d):
        for p in d["provenance"]:
            p["kind"] = "source_code"
        d.pop("benefits_when")
    edit(repo, PACKING, change)
    rejected(repo.validate(), PACKING, "cites at least one source")


def test_duplicate_strategy_fails_and_names_the_existing_one(repo):
    data = repo.read(PACKING)
    data.update(id="packing-again", name="Packing, again")
    data["parameters"] = [{"name": "block", "meaning": "elements per packed block", "unit": "elements"}]
    repo.write("strategies/packing-again.yaml", data)
    rejected(repo.validate(), "strategies/packing-again.yaml", "duplicate strategy: 'packing'")


def test_different_effect_is_not_a_duplicate(repo):
    repo.write("strategies/gather-hoist.yaml", other_strategy(repo))
    passes(repo.validate())


def test_access_pattern_strategy_takes_only_pattern_effects(repo):
    # loop and input effects arrive with their target types; add_pattern suits every target
    edit(repo, PACKING, lambda d: d.update(target="nowhere"))
    rejected(repo.validate(), "target", "not in vocabulary strategy_targets")


# --- swdb add ------------------------------------------------------------------------

def test_add_writes_a_strategy_to_its_folder(repo, tmp_path):
    path = tmp_path / "s.yaml"
    path.write_text(yaml.safe_dump(other_strategy(repo), sort_keys=False))
    passes(repo.swdb("add", path))
    assert (repo.path / "strategies" / "gather-hoist.yaml").is_file()
    rows = query(repo, "sql", "select id, target from strategies order by id")
    assert rows == [{"id": "gather-hoist", "target": "access_pattern"}, {"id": "packing", "target": "access_pattern"}]


def test_add_agent_marks_a_strategy_draft_with_an_agent_run(repo, tmp_path):
    data = other_strategy(repo)
    data["status"] = "reviewed"
    path = tmp_path / "s.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    passes(repo.swdb("add", path, "--agent"))
    written = repo.read("strategies/gather-hoist.yaml")
    assert written["status"] == "draft" and any(p["kind"] == "agent_run" for p in written["provenance"])


def test_add_agent_duplicate_is_rejected_with_the_existing_id(repo, tmp_path):
    data = repo.read(PACKING)
    data.update(id="pack-it")
    path = tmp_path / "s.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    result = repo.swdb("add", path, "--agent")
    rejected(result, "duplicate strategy: 'packing'", "nothing written")
    assert not (repo.path / "strategies" / "pack-it.yaml").exists()


# --- legality queries ---------------------------------------------------------------

def test_legal_for_a_read_only_gather_without_loop_carried_dependencies(repo):
    [found] = query(repo, "strategies", "--pattern", "gapbs-pr-jacobi/gather-contrib")
    assert found["strategy"] == "packing" and found["outcome"] == "legal"
    assert found["reasons"] == [] and found["unknown_fields"] == []
    assert len(found["check_by_hand"]) == len(repo.read(PACKING)["preconditions"]["unchecked"]) > 0
    assert [b["source"] for b in found["benefits_when"]] == ["goto-2008"] * 3
    assert all(b["basis"] == "reported" for b in found["benefits_when"])


def test_illegal_when_a_known_semantic_value_differs(repo):
    [found] = query(repo, "strategies", "--pattern", "gapbs-pr-gs/gather-contrib")
    assert found["outcome"] == "illegal"
    assert found["reasons"] == ["loop_carried_dependencies is true (code_reading), needs false"]
    assert found["check_by_hand"]     # prose is listed with every outcome


def test_illegal_when_a_required_shape_is_absent(repo):
    [found] = query(repo, "strategies", "--pattern", "gapbs-pr-jacobi/score-update")
    assert found["outcome"] == "illegal"
    assert "no step has address shape single_valued_indirect" in found["reasons"]


def test_illegal_when_the_reshaped_step_has_another_shape(repo):
    # bc's pbfs-succ-set ends in a ranged_indirect step, so step -1 cannot be reshaped
    edit(repo, PACKING, lambda d: d["preconditions"].update(requires_update_kinds=[]))
    [found] = query(repo, "strategies", "--pattern", "gapbs-bc-brandes/pbfs-succ-set")
    assert found["outcome"] == "illegal"
    assert "reshape needs step -1 to be single_valued_indirect, but it is ranged_indirect" in found["reasons"]


def test_illegal_when_the_update_kind_is_not_allowed(repo):
    [found] = query(repo, "strategies", "--pattern", "gapbs-bfs-do/td-parent-claim")
    assert found["outcome"] == "illegal"
    assert found["reasons"] == ["update kind is compare_and_swap, needs read"]


def unknown_loop_dependencies(repo):
    def change(d):
        pattern(d, "gather-contrib")["semantics"]["loop_carried_dependencies"] = {"value": None, "basis": "unknown"}
    edit(repo, JAC, change)


def test_undetermined_when_a_required_value_is_unknown(repo):
    unknown_loop_dependencies(repo)
    [found] = query(repo, "strategies", "--pattern", "gapbs-pr-jacobi/gather-contrib")
    assert found["outcome"] == "undetermined"
    assert found["unknown_fields"] == ["loop_carried_dependencies"] and found["reasons"] == []
    assert found["check_by_hand"]


def test_known_contradiction_beats_unknown(repo):
    def change(d):
        sem = pattern(d, "gather-contrib")["semantics"]
        sem["loop_carried_dependencies"] = {"value": None, "basis": "unknown"}
        sem["index_modified_during_loop"] = {"value": True, "basis": "code_reading"}
    edit(repo, JAC, change)
    [found] = query(repo, "strategies", "--pattern", "gapbs-pr-jacobi/gather-contrib")
    assert found["outcome"] == "illegal" and found["unknown_fields"] == []


def test_strategies_query_prints_yaml_by_default(repo):
    result = repo.swdb("strategies", "--pattern", "gapbs-pr-jacobi/gather-contrib")
    passes(result)
    assert yaml.safe_load(result.stdout)[0]["outcome"] == "legal"


def test_strategies_query_names_a_missing_pattern(repo):
    rejected(repo.swdb("strategies", "--pattern", "gapbs-pr-jacobi/nope"), "access pattern 'gapbs-pr-jacobi/nope' does not exist")
    result = repo.swdb("strategies", "--pattern", "no-slash")
    assert result.returncode == 2 and "expected <implementation>/<pattern>" in result.stderr


def test_find_strategy_lists_legal_and_undetermined_patterns_only(repo):
    unknown_loop_dependencies(repo)
    found = query(repo, "find", "--strategy", "packing", "--kernel", "gapbs-pr")
    assert found == [{"implementation": "gapbs-pr-jacobi", "pattern": "gather-contrib", "outcome": "undetermined",
                      "unknown_fields": ["loop_carried_dependencies"]}]   # gapbs-pr-gs's gather is illegal


def test_find_strategy_across_kernels(repo):
    found = query(repo, "find", "--strategy", "packing")
    kernels = {f["implementation"].rsplit("-", 1)[0] for f in found}
    assert {"implementation": "gapbs-pr-jacobi", "pattern": "gather-contrib", "outcome": "legal",
            "unknown_fields": []} in found
    assert len(kernels) > 1 and all(f["outcome"] in {"legal", "undetermined"} for f in found)


def test_find_strategy_names_a_missing_strategy(repo):
    rejected(repo.swdb("find", "--strategy", "nope"), "strategy 'nope' does not exist")
