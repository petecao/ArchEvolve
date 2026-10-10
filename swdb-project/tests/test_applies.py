"""Implementations that apply strategies: the `applies` field, its rules, and
`swdb implementations <kernel> --applies <strategy>`. Created 2026-09-23. Uses a fixture
derived implementation and fixture profiles in a temporary records folder."""

import pytest

from test_strategies import edit, passes, query, rejected

JAC = "implementations/gapbs-pr-jacobi.yaml"
PACKED = "implementations/gapbs-pr-jacobi-packed.yaml"
BASE_PROFILES = "profiles/gapbs-pr-jacobi.{}.mbit10.20260922t{}z.yaml"


@pytest.fixture
def repo(records):
    return records.copy_repo()


def derived(repo, applies=None, **changes):
    """gapbs-pr-jacobi-packed: the Jacobi PageRank implementation marked as applying packing."""
    data = repo.read(JAC)
    data.update(id="gapbs-pr-jacobi-packed", name="PageRank, Jacobi, packed contributions")
    data["origin"] = {"kind": "derived", "description": "Jacobi PageRank with the neighbor contributions packed.",
                      "derived_from": "gapbs-pr-jacobi"}
    data["applies"] = applies if applies is not None else [
        {"strategy": "packing", "target": "gather-contrib", "parameters": {}}]
    data.update(changes)
    repo.write(PACKED, data)
    return data


def test_existing_implementations_validate_without_applies(repo):
    passes(repo.validate())
    assert all("applies" not in repo.read(f"implementations/{p.name}")
               for p in (repo.path / "implementations").glob("*.yaml"))


def test_applies_passes_for_a_matching_target(repo):
    derived(repo)
    passes(repo.validate())


def test_applied_strategy_must_resolve(repo):
    derived(repo, [{"strategy": "packinng", "target": "gather-contrib", "parameters": {}}])
    rejected(repo.validate(), "applies[0].strategy", "refers to strategy 'packinng', which does not exist")


def test_applied_target_must_be_in_the_same_record(repo):
    derived(repo, [{"strategy": "packing", "target": "no-such-pattern", "parameters": {}}])
    rejected(repo.validate(), PACKED, "applies[0].target",
             "targets access_pattern, but 'no-such-pattern' is not an access pattern of this implementation")


def test_applied_target_must_match_the_strategy_target_type(repo):
    derived(repo, [{"strategy": "packing", "target": "sweep", "parameters": {}}])
    rejected(repo.validate(), "applies[0].target", "strategy 'packing' targets access_pattern, but 'sweep' is a loop")
    derived(repo, [{"strategy": "loop_tiling", "target": "gather-contrib", "parameters": {"tile_size": 64}}])
    rejected(repo.validate(), "applies[0].target", "targets loop, but 'gather-contrib' is an access pattern")
    derived(repo, [{"strategy": "vertex_reordering", "target": "sweep", "parameters": {}}])
    rejected(repo.validate(), "applies[0].target", "targets input, so its target is 'input', not 'sweep'")


def test_every_target_type_passes(repo):
    derived(repo, [{"strategy": "vertex_reordering", "target": "input", "parameters": {}},
                   {"strategy": "loop_tiling", "target": "vertex", "parameters": {"tile_size": 4096}},
                   {"strategy": "software_prefetch", "target": "gather-contrib", "parameters": {"distance": 16}}])
    passes(repo.validate())


def test_undeclared_parameter_fails(repo):
    derived(repo, [{"strategy": "software_prefetch", "target": "gather-contrib", "parameters": {"distnace": 16}}])
    rejected(repo.validate(), "applies[0].parameters.distnace",
             "strategy 'software_prefetch' declares no parameter 'distnace' (it declares distance)")
    derived(repo, [{"strategy": "packing", "target": "gather-contrib", "parameters": {"block": 8}}])
    rejected(repo.validate(), "declares no parameter 'block' (it declares none)")


def test_declared_parameters_must_be_given(repo):
    derived(repo, [{"strategy": "software_prefetch", "target": "gather-contrib", "parameters": {}}])
    rejected(repo.validate(), "applies[0].parameters", "declares parameter 'distance'; give the value applied")


def test_a_loop_and_a_pattern_may_share_an_id(repo):
    # gapbs-cc-sv has a loop and an access pattern both called compress-chase: the strategy's
    # target type decides which one an applies entry names
    data = repo.read("implementations/gapbs-cc-sv.yaml")
    assert "compress-chase" in {l["id"] for l in data["loops"]} & {p["id"] for p in data["access_patterns"]}
    data["applies"] = [{"strategy": "loop_tiling", "target": "compress-chase", "parameters": {"tile_size": 64}},
                       {"strategy": "software_prefetch", "target": "compress-chase", "parameters": {"distance": 8}}]
    repo.write("implementations/gapbs-cc-sv.yaml", data)
    passes(repo.validate())


def test_an_invalid_strategy_is_reported_not_a_crash(repo):
    derived(repo)
    edit(repo, "strategies/packing.yaml", lambda d: d.pop("target"))
    result = repo.validate()
    rejected(result, "strategies/packing.yaml", "target")
    assert "Traceback" not in result.stderr


def profile_copy(repo, name, impl, new_stamp):
    """A fixture profile: an existing Jacobi profile, relabeled as `impl` at another time."""
    data = repo.read(name)
    data["implementation"] = impl
    data["id"] = f"{impl}.{data['input']}.{data['machine']}.{new_stamp}"
    data["environment"]["started"] = f"2026-09-23T{new_stamp[9:11]}:{new_stamp[11:13]}:{new_stamp[13:15]}Z"
    repo.write(f"profiles/{data['id']}.yaml", data)
    return data["id"]


def test_implementations_applies_pairs_each_profile_with_the_baseline(repo):
    derived(repo)
    base_u16 = "profiles/gapbs-pr-jacobi.urand-u16-k16.mbit10.20260922t212445z.yaml"
    older = profile_copy(repo, base_u16, "gapbs-pr-jacobi-packed", "20260923t010000z")
    newest = profile_copy(repo, base_u16, "gapbs-pr-jacobi-packed", "20260923t020000z")
    partial = profile_copy(repo, base_u16, "gapbs-pr-jacobi-packed", "20260923t030000z")
    edit(repo, f"profiles/{partial}.yaml", lambda d: d.update(complete=False))    # newer but incomplete
    passes(repo.validate())
    [found] = query(repo, "implementations", "gapbs-pr", "--applies", "packing")
    assert found["implementation"] == "gapbs-pr-jacobi-packed"
    assert found["derived_from"] == "gapbs-pr-jacobi"
    assert found["applies"] == [{"strategy": "packing", "target": "gather-contrib", "parameters": {}, "position": 0}]
    pairs = {(p["input"], p["machine"]): p for p in found["profiles"]}
    assert pairs[("urand-u16-k16", "mbit10")] == {
        "input": "urand-u16-k16", "machine": "mbit10", "profile": newest,
        "baseline_profile": "gapbs-pr-jacobi.urand-u16-k16.mbit10.20260922t212445z"}
    assert older != newest
    # the baseline has profiles on other inputs; the derived implementation's side is null there
    assert pairs[("kron-g22-k16", "mbit10")]["profile"] is None
    assert pairs[("kron-g22-k16", "mbit10")]["baseline_profile"].startswith("gapbs-pr-jacobi.kron-g22-k16")


def test_implementations_applies_without_a_baseline_has_null_baseline_profiles(repo):
    data = derived(repo)
    data["origin"] = {"kind": "collaborator", "description": "written from scratch", "derived_from": None}
    repo.write(PACKED, data)
    [found] = query(repo, "implementations", "gapbs-pr", "--applies", "packing")
    assert found["derived_from"] is None and found["profiles"] == []


def test_implementations_applies_leaves_out_implementations_that_do_not_apply_it(repo):
    derived(repo)
    assert query(repo, "implementations", "gapbs-pr", "--applies", "software_prefetch") == []
    assert query(repo, "implementations", "gapbs-bfs", "--applies", "packing") == []
    rejected(repo.swdb("implementations", "gapbs-pr", "--applies", "nope"), "strategy 'nope' does not exist")


def test_applied_strategies_are_in_the_database(repo):
    derived(repo, [{"strategy": "packing", "target": "gather-contrib", "parameters": {}},
                   {"strategy": "software_prefetch", "target": "gather-contrib", "parameters": {"distance": 16}}])
    rows = query(repo, "sql", "select position, strategy, parameters_json from applied_strategies order by position")
    assert rows == [{"position": 0, "strategy": "packing", "parameters_json": "{}"},
                    {"position": 1, "strategy": "software_prefetch", "parameters_json": '{"distance": 16}'}]


def test_a_database_built_by_an_older_tool_is_rebuilt(repo):
    import sqlite3

    db = repo.path.parent / "build" / "swdb.sqlite"
    passes(repo.swdb("build"))
    con = sqlite3.connect(db)
    con.execute("DROP TABLE applied_strategies")
    con.execute("UPDATE meta SET value = 'old' WHERE key = 'builder'")
    con.commit()
    con.close()
    result = repo.swdb("implementations", "gapbs-pr", "--applies", "packing")
    passes(result)
    assert "built by another swdb version" in result.stderr
