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
    assert settings["standard_library"]["header_macro"] == "_LIBCPP_VERSION=220108"
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




def _wp_ready():
    from swdb import c_lowering, framac
    return not framac.locate().missing and not c_lowering.locate().missing


@pytest.mark.skipif(not _wp_ready(), reason="Frama-C 33.0 or clang 22.1.8 is missing")
def test_a_pair_model_proves_through_the_shared_public_model_interface(seed):
    result = seed.swdb("prove", "--model", "std_pair_int_int_ctor", "--adapter", "wp",
                       "--runs-dir", seed.runs, "--format", "json", env={"SWDB_FRAMA_C": ""})
    assert result.returncode == 0, result.stderr + result.stdout
    record = seed.read(json.loads(result.stdout))
    assert record["subject"] == {"kind": "c_model", "id": "std_pair_int_int_ctor"}
    assert record["verdict"] == "proven", record.get("failure_class")
    assert seed.swdb("validate").returncode == 0


@needs_cbmc
def test_an_unmatched_standard_library_is_refused_before_bounded_proof(seed, tmp_path):
    from swdb import c_lowering
    import sys
    wrapper = tmp_path / "clang-different-stl"
    wrapper.write_text(f"#!{sys.executable}\n"
                       "import os, sys\n"
                       "if '-dM' in sys.argv:\n"
                       "    print('#define __GLIBCXX__ 20240101')\n"
                       "else:\n"
                       f"    os.execv({c_lowering.locate().command[0]!r}, "
                       f"[{c_lowering.locate().command[0]!r}, *sys.argv[1:]])\n")
    wrapper.chmod(0o755)
    record = seed.read(seed.prove("swdb_fixture_vec_max", MAX, {"threads": 1, "n": 1},
                                  env={"SWDB_CLANG": str(wrapper)}))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
    assert "agreement" not in record["settings"]
    assert not any(r["name"] == "cbmc_input" for r in record.get("reports", []))


@pytest.mark.skipif(not _wp_ready(), reason="Frama-C 33.0 or clang 22.1.8 is missing")
@pytest.mark.parametrize("function,contract", [("swdb_fixture_vec_max", MAX),
                                                ("swdb_fixture_vec_stale_data", STALE),
                                                ("swdb_fixture_vec_stale_iterator", STALE)])
def test_wp_refuses_vector_lifetime_obligations_including_stale_aliases(seed, function, contract):
    result = seed.swdb("prove", "--candidate", seed.candidates["safe"], "--function", function,
                       "--contract", contract, "--adapter", "wp", "--runs-dir", seed.runs,
                       "--format", "json", env={"SWDB_FRAMA_C": ""})
    assert result.returncode == 0, result.stderr + result.stdout
    record = seed.read(json.loads(result.stdout))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
    assert seed.swdb("validate").returncode == 0


@pytest.mark.skipif(not _wp_ready(), reason="Frama-C 33.0 or clang 22.1.8 is missing")
def test_wp_refuses_a_growing_model_until_allocation_lifetimes_are_supported(seed):
    result = seed.swdb("prove", "--model", "std_vector_int_grow", "--adapter", "wp",
                       "--runs-dir", seed.runs, "--format", "json", env={"SWDB_FRAMA_C": ""})
    assert result.returncode == 0, result.stderr + result.stdout
    record = seed.read(json.loads(result.stdout))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
    assert seed.swdb("validate").returncode == 0
