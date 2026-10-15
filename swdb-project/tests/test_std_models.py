"""The std::vector and std::pair models through `swdb prove --adapter cbmc` (the bounded verifier at threads = 1).

Created: 2026-10-14 ET (Probata proof of concept ticket 25). Design: formal-verification map 16 items 6 and 7
(modeled types; growth frees the old buffer; `at` out of range is a proof obligation; new assumption entries),
11 item 11 (undefined behavior is a proof obligation). Format: docs/reference/format-v0.4-std-models.md.

Seam 1 (`swdb prove`), with `swdb validate` reading the records. The candidate artifact is GAPBS bfs.cc with the
vector fixture units inserted (tests/fixtures/proof/cbmc/vector_units.cc), built through the public workflow and
certified by a fixture record, as in test_cbmc_adapter.py. Cases skip cleanly without CBMC 6.11 or clang 22.1.8;
`swdb prove` takes the machine-wide verifier lock per job.
"""

import hashlib
import json
import shutil

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records
from test_cbmc_adapter import ANCHOR_BEFORE, ONCE, Seed, _contract, method_version, needs_cbmc
from test_proof_records import _library_roots
from test_wp_adapter import _certify
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

UNITS = (FIXTURES / "proof" / "cbmc" / "vector_units.cc").read_text()
MAX, STALE, AT = "contract.fixture_vec_max", "contract.fixture_vec_stale", "contract.fixture_vec_at"
ARRAY = [{"array": "a", "shared_actions": [], "history_reads": False}]
ARRAY_PRE = "requires 0 <= n && \\valid(a + (0 .. n-1));"
MAX_POST = ("assigns \\nothing;\n"
            "ensures n > 0 ==> \\forall integer k; 0 <= k < n ==> a[k] <= \\result;\n"
            "ensures n > 0 ==> \\exists integer k; 0 <= k < n && a[k] == \\result;\n"
            "ensures n == 0 ==> \\result == 0;")
LIBRARY_SENTENCE = "implements the modeled members of std_pair_int_int, std_vector_int as the C++ standard"


def _vector_contract(cid, function, clauses, frame):
    data = _contract(cid, function, clauses, frame)
    data["proof_unit"]["source"] = {"root": "library", "path": "proof_units/vector_units.cc",
                                    "sha256": hashlib.sha256(UNITS.encode()).hexdigest()}
    return data


def build_vector_seed(path):
    """records/ and library/ under `path`; returns {safe: candidate artifact ID}."""
    from swdb import c_lowering
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       sorted(_library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10"}))
    shutil.copytree(REPO / "library", path / "library")
    methods = path / "library" / "methods"
    methods.mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    (methods / "cbmc-fixture.yaml").write_text(yaml.safe_dump(method_version(c_lowering.identity()), sort_keys=False))
    (path / "library" / "proof_units").mkdir()
    (path / "library" / "proof_units" / "vector_units.cc").write_text(UNITS)
    contracts = {
        "fixture_vec_max": _vector_contract(MAX, "swdb_fixture_vec_max", [
            ("max_pre", "legality", ARRAY_PRE, "per_candidate"),
            ("max_post", "postcondition", MAX_POST, "per_candidate")], ARRAY),
        "fixture_vec_stale": _vector_contract(STALE, "swdb_fixture_vec_stale_data", [
            ("stale_pre", "legality", ARRAY_PRE, "per_candidate"),
            ("stale_post", "postcondition", "assigns \\nothing;\nensures \\result == 7;", "per_candidate")], ARRAY),
        "fixture_vec_at": _vector_contract(AT, "swdb_fixture_vec_at", [
            ("at_pre", "legality", "requires 0 <= n && 0 <= k;", "per_candidate"),
            ("at_post", "postcondition", "assigns \\nothing;\nensures \\result == 5;", "per_candidate")], []),
    }
    for name, data in contracts.items():
        (path / "library" / "rewrite_contracts" / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    submitted = records.swdb("submit", request(ANCHOR_BEFORE, UNITS + "\n" + ANCHOR_BEFORE, id="vector-safe"),
                             "--runs-dir", runs, "--format", "json")
    assert submitted.returncode == 0, submitted.stderr
    candidate = json.loads(submitted.stdout)["candidate"]
    _certify(records.path, path, candidate, MAX)
    return {"safe": candidate}


@pytest.fixture(scope="module")
def vector_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("vector-seed")
    return path, build_vector_seed(path)


@pytest.fixture
def seed(vector_seed, tmp_path):
    source, candidates = vector_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, candidates)


def _model_assumptions(record):
    from swdb import std_models
    model = std_models.identity()
    return [a for a in record["assumptions"] if a["reference"] == model]


# --- the fixture unit: vector members and std::pair ---------------------------------------------------------

@needs_cbmc
def test_a_unit_using_vector_members_and_pair_proves_and_its_c_and_cpp_agree_with_the_model_pinned(seed):
    from swdb import std_models
    record = seed.read(seed.prove("swdb_fixture_vec_max", MAX, {"threads": 1, "n": 3}))
    assert record["verdict"] == "proven", record.get("failure_class")
    settings = record["settings"]
    assert settings["agreement"]["verdict"] == "agree" and settings["agreement"]["undefined_behavior_runs"] == 0
    assert settings["std_models"] == ["std_pair_int_int", "std_vector_int"]
    assert record["pins"]["std_models"] == std_models.identity()          # the model's version, in the hash set
    job_c = open(seed.report(record, "cbmc_input")).read()
    assert "std_vector_int_push_back(&v, a[i]);" in job_c and "static void std_vector_int_grow(" in job_c
    cut = open(seed.report(record, "differential_cxx")).read()
    assert "std::vector<int> v;" in cut                                   # the C++ side runs libc++ itself
    entries = _model_assumptions(record)
    assert [e["kind"] for e in entries] == ["trusted_tool", "trusted_tool"]
    assert LIBRARY_SENTENCE in entries[0]["sentence"] and entries[1]["sentence"].startswith("Allocation succeeds")
    assert seed.swdb("validate").returncode == 0


# --- what the model catches ------------------------------------------------------------------------------------

@needs_cbmc
@pytest.mark.parametrize("function", ["swdb_fixture_vec_stale_data", "swdb_fixture_vec_stale_iterator"])
def test_a_pointer_or_iterator_kept_across_a_growing_push_back_is_refuted_with_a_counterexample(seed, function):
    record = seed.read(seed.prove(function, STALE, {"threads": 1, "n": 1}))
    assert record["verdict"] == "refuted", (record.get("failure_class"), record.get("unreplayed_counterexample"))
    example = record["counterexample"]
    assert example["inputs"]["n"] == 1 and example["replay"]["replayed"] is True
    assert ".assertion." not in example["check"] and example["replay"]["sanitizer"]   # a memory check; the C++ too
    assert record["settings"]["agreement"]["undefined_behavior_runs"] > 0  # those inputs are no agreement evidence
    assert seed.swdb("validate").returncode == 0


@needs_cbmc
def test_at_with_an_index_that_may_reach_size_is_refuted_and_the_same_call_behind_a_bounds_check_proves(seed):
    from swdb import std_models
    refuted = seed.read(seed.prove("swdb_fixture_vec_at", AT, {"threads": 1, "n": 2}))
    assert refuted["verdict"] == "refuted"
    example = refuted["counterexample"]
    assert example["property"] == std_models.OUT_OF_RANGE and example["replay"]["replayed"] is True
    assert example["inputs"]["k"] >= example["inputs"]["n"] >= 0           # k reaches size()
    proven = seed.read(seed.prove("swdb_fixture_vec_at_checked", AT, {"threads": 1, "n": 2}))
    assert proven["verdict"] == "proven"
    assert seed.swdb("validate").returncode == 0


# --- assumption entries: units without the model -----------------------------------------------------------------

def test_a_lowering_with_neither_model_nor_new_lists_neither_entry_and_new_lists_allocation_only():
    from swdb import c_lowering, std_models
    tool = {"id": "swdb-c-lowering-3", "sha256": "0" * 64}
    neither = c_lowering.Lowering("f", "", (), "", (), "0" * 64)
    assert std_models.assumptions(neither, "22.1.8", tool) == [] and std_models.pins(neither) == {}
    new_only = c_lowering.Lowering("f", "", (), "", (), "0" * 64, allocation=True)
    (entry,) = std_models.assumptions(new_only, "22.1.8", tool)
    assert entry["reference"] == tool and entry["sentence"].startswith("Allocation succeeds")
    both = c_lowering.Lowering("f", "", (), "", (), "0" * 64, std_models=("std_vector_int",), allocation=True)
    library, allocation = std_models.assumptions(both, "22.1.8", tool)
    assert library["reference"] == allocation["reference"] == std_models.identity()
    assert "libc++ of clang 22.1.8" in library["sentence"] and "[vector]" not in library["sentence"]


def test_a_method_version_that_pins_another_model_version_admits_no_job_on_a_unit_using_the_model():
    from types import SimpleNamespace
    from swdb import c_lowering, std_models
    both = c_lowering.Lowering("f", "", (), "", (), "0" * 64, std_models=("std_pair_int_int", "std_vector_int"),
                               allocation=True)
    current = {"std_vector": std_models.identity(), "std_pair": std_models.identity()}
    assert std_models.method_problem(SimpleNamespace(id="m", data={"models": current}), both) is None
    stale = {**current, "std_vector": {"id": "swdb-std-models-1", "sha256": "7" * 64}}
    problem = std_models.method_problem(SimpleNamespace(id="m", data={"models": stale}), both)
    assert problem and "models.std_vector" in problem
    neither = c_lowering.Lowering("f", "", (), "", (), "0" * 64)
    assert std_models.method_problem(SimpleNamespace(id="m", data={"models": stale}), neither) is None


# --- WP: model proof records (swdb.models) and the unit-level runs ---------------------------------------------------

WP_ENV = {"SWDB_FRAMA_C": ""}             # the seed's helper disables Frama-C for swdb validate; WP needs it back
MAX_HINTS = [
    ("swdb_fixture_vec_max.loop1.head", "loop_invariant", "loop invariant 0 <= i <= n;"),
    ("swdb_fixture_vec_max.loop1.head", "loop_invariant", "loop invariant std_vector_int_valid(&v) && v.size == i;"),
    ("swdb_fixture_vec_max.loop1.head", "loop_invariant",
     "loop invariant \\forall integer k; 0 <= k < i ==> v.data[k] == a[k];"),
    ("swdb_fixture_vec_max.loop1.head", "loop_assigns", "loop assigns i, v, v.data[0 .. n - 1];"),
    ("swdb_fixture_vec_max.loop1.head", "loop_variant", "loop variant n - i;"),
]


def _wp_ready():
    from swdb import c_lowering, framac
    return not framac.locate().missing and not c_lowering.locate().missing


needs_wp = pytest.mark.skipif(not _wp_ready(), reason="Frama-C 33.0 or clang 22.1.8 is missing")


def _prove_model(seed, name, ok=True):
    result = seed.swdb("prove", "--summary", f"model.{name}", "--adapter", "wp", "--runs-dir", seed.runs,
                       "--format", "json", env=WP_ENV)
    assert (result.returncode == 0) is ok, result.stderr + result.stdout
    return seed.read(json.loads(result.stdout)) if ok else result


def _prove_wp(seed, function, contract, hints=None):
    args = ["--candidate", seed.candidates["safe"], "--function", function, "--contract", contract, "--adapter", "wp",
            "--runs-dir", seed.runs, "--format", "json", "--budget-minutes", "6"]   # under run_swdb's 600 s limit;
    if hints:                                                                     # the full runs are in the Answer
        path = seed.root / f"hints-{function}.yaml"
        path.write_text(yaml.safe_dump({"hints": [{"anchor": a, "kind": k, "text": t, "provenance": {"source": "human"}}
                                                  for a, k, t in hints]}, sort_keys=False))
        args += ["--hint-file", path]
    result = seed.swdb("prove", *args, env=WP_ENV)
    assert result.returncode == 0, result.stderr + result.stdout
    return seed.read(json.loads(result.stdout))


def test_every_model_a_lowering_defines_is_rebuilt_by_name_with_a_hash_that_follows_the_contracts_it_calls():
    from swdb import c_lowering, models
    lowering = c_lowering.lower(FIXTURES / "proof" / "lowering" / "vector_pair.cc", "swdb_vector_unit")
    names = [m.name for m in models.provable(lowering)]
    assert "std_vector_int_push_back" in names and "std_vector_int_grow" in names and "std_pair_int_int_ctor" in names
    assert not any(n.startswith(("swdb_alloc_", "swdb_free", "SWDB_")) or n.endswith("_valid") for n in names)
    push = models.unit("model.std_vector_int_push_back")
    assert "static void std_vector_int_grow(" in push.text and push.id == "model.std_vector_int_push_back"
    assert models.unit("std_min_int").text.count("static int std_min_int(") == 1          # ticket 24's models too
    assert models.unit("std_vector_bool_size") is None and models.unit("not_a_model") is None


@needs_wp
def test_a_model_is_proven_once_by_name_and_a_unit_that_uses_it_pins_that_record(seed):
    pair = _prove_model(seed, "std_pair_int_int_ctor")
    assert pair["verdict"] == "proven"
    assert pair["subject"] == {"kind": "library_summary", "id": "model.std_pair_int_int_ctor"}
    assert pair["pins"]["code"]["id"] == "model.std_pair_int_int_ctor" and pair["pins"]["std_models"]
    assert _prove_model(seed, "std_min_int")["verdict"] == "proven"                  # ticket 24's model, same mechanism
    unit = seed.read(seed.prove("swdb_fixture_vec_max", MAX, {"threads": 1, "n": 1}))
    pinned = {p["id"]: p for p in unit["pins"]["summaries"]}
    assert pinned["model.std_pair_int_int_ctor"]["proof_record"] == pair["id"]
    unproven = {a["reference"]["id"] for a in unit["assumptions"] if a["kind"] == "summary"}
    assert "model.std_vector_int_push_back" in unproven and "model.std_pair_int_int_ctor" not in unproven
    assert seed.swdb("validate").returncode == 0


@needs_wp
def test_a_growing_member_is_not_proven_and_its_open_goals_are_the_allocation_ones(seed):
    record = _prove_model(seed, "std_vector_int_grow")
    assert record["verdict"] == "not_proven"
    open_goals = {g["goal"] for g in record["goals"] if g["status"] not in ("valid", "qed")}
    assert open_goals and all("grow" in g for g in open_goals), open_goals
    assert len([a for a in record["assumptions"] if a["sentence"].startswith("Allocation succeeds")]) == 1


@needs_wp
@pytest.mark.skip(reason="paused 2026-10-14 (ticket 25 Progress): two WP jobs take over 20 min; see the ticket")
def test_wp_on_the_vector_unit_and_on_the_stale_pointer_never_proves_and_never_refutes(seed):
    unit = _prove_wp(seed, "swdb_fixture_vec_max", MAX, MAX_HINTS)
    assert unit["verdict"] == "not_proven" and unit["pins"]["std_models"]
    stale = _prove_wp(seed, "swdb_fixture_vec_stale_data", STALE)
    assert stale["verdict"] == "not_proven"                                          # WP never refutes
