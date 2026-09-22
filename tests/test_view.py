"""`swdb view`: the workload view in the HW Ensemble format (Josh's sparta-sort.input.yaml).
Created 2026-09-22."""

import json

import pytest
import yaml

from conftest import REPO

JOSH = yaml.safe_load((REPO / "archevolve" / "hw_ensemble" / "sparta-sort.input.yaml").read_text())


def view(records, *args, fmt="json"):
    result = records.swdb("view", *args, "--format", fmt)
    return result, (json.loads(result.stdout) if result.returncode == 0 and fmt == "json" else None)


@pytest.fixture
def repo(records):
    return records.copy_repo()


def same_shape(reference, actual, where="view"):
    """Every key of the reference exists in actual with the same nesting (mappings, and the
    first element of lists when both have one). Extra keys in actual are allowed."""
    if isinstance(reference, dict):
        assert isinstance(actual, dict), f"{where} should be a mapping"
        for key, sub in reference.items():
            assert key in actual, f"{where}.{key} missing"
            if sub is not None and actual[key] is not None:
                same_shape(sub, actual[key], f"{where}.{key}")
    elif isinstance(reference, list):
        assert isinstance(actual, list), f"{where} should be a list"
        if reference and actual:
            same_shape(reference[0], actual[0], f"{where}[0]")


def test_view_has_joshs_field_names_and_nesting(repo):
    result, data = view(repo, "gapbs-pr-gs", "kron-g16-k16", "mbit10")
    assert result.returncode == 0, result.stderr
    same_shape({k: v for k, v in JOSH.items() if k != "metrics"}, data)
    assert set(JOSH) <= set(data)
    assert data["schema_version"] == JOSH["schema_version"]


def test_view_yaml_output_parses(repo):
    result, _ = view(repo, "gapbs-pr-gs", "kron-g16-k16", "mbit10", fmt="yaml")
    assert result.returncode == 0, result.stderr
    assert yaml.safe_load(result.stdout)["workload_id"] == "gapbs-pr-gs@kron-g16-k16@mbit10"


def test_workload_id(repo):
    _, data = view(repo, "gapbs-pr-jacobi", "urand-u22-k16", "mbit10")
    assert data["workload_id"] == "gapbs-pr-jacobi@urand-u22-k16@mbit10"
    assert data["function"] == "PageRankPull()"


def test_element_counts_are_evaluated_and_unknown_stays_null(repo):
    _, data = view(repo, "gapbs-pr-gs", "kron-g16-k16", "mbit10")
    gather = next(p for p in data["patterns"] if p["id"] == "gather-contrib")
    arrays = {a["name"]: a for a in gather["arrays"]}
    assert arrays["g.in_index_"]["element_count"] == 65537
    assert arrays["outgoing_contrib"]["element_count"] == 65536
    edges = repo.read("inputs/kron-g16-k16.yaml")["properties"]["num_edges_directed"]
    assert arrays["g.in_neighbors_"]["element_count"] == edges["value"]   # null while unknown
    assert arrays["g.in_neighbors_"]["element_count_formula"] == "num_edges_directed"


def test_unknown_edge_count_is_null_not_guessed(repo):
    def forget(d):
        d["properties"]["num_edges_directed"] = {"value": None, "basis": "unknown", "evidence_refs": []}
    data = repo.read("inputs/kron-g16-k16.yaml")
    forget(data)
    repo.write("inputs/kron-g16-k16.yaml", data)
    _, view_data = view(repo, "gapbs-pr-gs", "kron-g16-k16", "mbit10")
    gather = next(p for p in view_data["patterns"] if p["id"] == "gather-contrib")
    assert {a["name"]: a["element_count"] for a in gather["arrays"]}["g.in_neighbors_"] is None


def test_symbol_the_input_does_not_define_fails_naming_it(repo):
    data = repo.read("inputs/kron-g16-k16.yaml")
    del data["properties"]["num_edges_directed"]
    repo.write("inputs/kron-g16-k16.yaml", data)
    result, _ = view(repo, "gapbs-pr-gs", "kron-g16-k16", "mbit10")
    assert result.returncode == 1
    assert "num_edges_directed" in result.stderr and "does not define" in result.stderr


def test_semantics_come_with_their_basis_and_evidence(repo):
    _, data = view(repo, "gapbs-pr-gs", "kron-g16-k16", "mbit10")
    gather = next(p for p in data["patterns"] if p["id"] == "gather-contrib")
    assert gather["semantics"]["loop_carried_dependencies"] is True
    ev = gather["semantics_evidence"]["loop_carried_dependencies"]
    assert ev["basis"] == "code_reading"
    ids = {p["id"] for p in data["provenance"]}
    assert ev["evidence_refs"] and set(ev["evidence_refs"]) <= ids
    assert set(gather["evidence_refs"]) <= ids
    assert gather["pattern_class"] == "stream > ranged_indirect > single_valued_indirect : read"


def test_unknown_semantics_stay_unknown(records):
    records.add_stub()
    _, data = view(records, "stub-impl", "tiny-sym", "testhost")
    sem = data["patterns"][0]["semantics"]
    assert sem["loop_carried_dependencies"] is None       # Josh's format: null, never false
    assert sem["ordering"] == "unknown"                  # Josh's format writes ordering: unknown
    assert data["patterns"][0]["semantics_evidence"]["ordering"]["basis"] == "unknown"


def test_no_profile_means_explicitly_unknown_counts_metrics_bottleneck(repo):
    _, data = view(repo, "gapbs-pr-gs", "kron-g22-k16", "mbit10")
    if any((repo.path / "profiles").glob("gapbs-pr-gs.kron-g22-k16.mbit10.*")):
        pytest.skip("a real profile exists for this triple")
    assert data["counts"]["iterations"] == {"value": None, "scope": "unknown", "evidence_refs": []}
    assert data["counts"]["repetitions"] == {"value": None, "meaning": "unknown", "evidence_refs": []}
    assert data["bottleneck"] == {"classification": "unknown", "basis": "unknown", "memory_limit": "unknown",
                                  "evidence_refs": []}
    assert data["metrics"] == []
    assert any("No profile" in n for n in data["notes"])


def test_missing_record_fails(repo):
    result, _ = view(repo, "gapbs-pr-gs", "no-such-input", "mbit10")
    assert result.returncode == 1 and "input 'no-such-input' does not exist" in result.stderr
