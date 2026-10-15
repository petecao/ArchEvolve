"""Whole private vector copy/scan workflow through prove; created 2026-10-15 ET.

The source is the existing bounded/native fixture. WP's input origin and initializedness
are explicit in this separate contract, not inferred from address validity.
"""
import pytest
import yaml

from conftest import FIXTURES
from test_closed_owner_members import _record
from test_standard_member_contracts import _member_seed
from test_std_models import MAX_POST
from test_wp_adapter import fake, needs_wp
from test_wp_subset import _entry

SOURCE = (FIXTURES / "proof" / "cbmc" / "vector_units.cc").read_text()
CONTRACT = "contract.fixture_vector_pipeline"


def pipeline_seed(root, source=SOURCE):
    seed = _member_seed(root)
    units = root / "library" / "proof_units"
    units.mkdir(exist_ok=True)
    (units / "vector_pipeline.cc").write_text(source)
    entry = _entry(CONTRACT, "swdb_fixture_vec_max", "vector_pipeline.cc", source,
        [("pre", "legality", r"requires 0 <= n && \valid(a+(0..n-1)) && \initialized(a+(0..n-1));"),
         ("post", "postcondition", MAX_POST)], ["a"], {"once": "self"})
    entry["proof_unit"]["array_domains"] = {"a": {"extent": "n"}}
    (root / "library" / "rewrite_contracts" / "fixture_vector_pipeline.yaml").write_text(
        yaml.safe_dump(entry, sort_keys=False))
    return seed


@needs_wp
def test_the_original_vector_size_push_range_and_pair_workflow_has_a_checked_unbounded_view(tmp_path):
    seed = pipeline_seed(tmp_path)
    record = _record(seed, "--summary", CONTRACT,
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unknown", record
    certificate = record["settings"]["vector_ownership"]["certificate"]
    assert certificate["protocol"] == "private-vector-copy-scan-1"
    assert certificate["source_frame"] == certificate["view_frame"] == r"assigns \nothing;"
    assert certificate["original_contract_sha256"] == certificate["view_contract_sha256"]
    assert certificate["input_premises_added"] == []
    assert certificate["allocation_executions"] == "unbounded; projected, never a finite pool"
    assert certificate["origins"]["complete"] is True
    policies = {row["id"]: row for row in certificate["model_eligibility"]}
    for member in ("std_vector_int_push_back", "std_vector_int_size", "std_vector_int_begin",
                   "std_vector_int_end", "std_vector_int_operator_index", "std_pair_int_int_ctor"):
        assert member in policies
        assert policies[member]["standalone_body_proof"] is False
    assert record["pins"].get("models", []) == []


@needs_wp
@pytest.mark.parametrize("change", ["wrong_append", "escaping_alias", "mutating_range", "allocation_override", "extra_global", "missing_window"])
def test_the_pipeline_refuses_unchecked_effects_and_missing_qualified_input_origins(tmp_path, change):
    altered = {
        "wrong_append": SOURCE.replace("v.push_back(a[i]);", "v.push_back(a[i]+1);", 1),
        "escaping_alias": SOURCE.replace("std::pair<int, int> best(0, 0);", "int *escaped=v.data(); std::pair<int,int> best(0,0);", 1),
        "mutating_range": SOURCE.replace("for (int x : v) {", "for (int x : v) { v.push_back(0);", 1),
        "allocation_override": SOURCE + "\nvoid *operator/**/new(std::size_t bytes) { return (void*)0; }\n",
        "extra_global": SOURCE + "\nint extra_global;\n",
        "missing_window": SOURCE,
    }[change]
    seed = pipeline_seed(tmp_path, altered)
    if change == "missing_window":
        path = tmp_path / "library" / "rewrite_contracts" / "fixture_vector_pipeline.yaml"
        entry = yaml.safe_load(path.read_text())
        del entry["proof_unit"]["array_domains"]
        path.write_text(yaml.safe_dump(entry, sort_keys=False))
    record = _record(seed, "--summary", CONTRACT,
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])


@needs_wp
def test_a_changed_comparison_is_preserved_in_the_checked_pipeline_view(tmp_path):
    altered = SOURCE.replace("x > best.second", "x < best.second", 1)
    seed = pipeline_seed(tmp_path, altered)
    record = _record(seed, "--summary", CONTRACT,
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unknown", record
    certificate = record["settings"]["vector_ownership"]["certificate"]
    assert certificate["source_origins"]["source_protocol"]["comparison"] == "<"
    generated = next(row for row in record["evidence"]["reports"] if row["name"] == "wp_input")
    assert "x < best.second" in (seed.records / generated["path"]).read_text()


@needs_wp
def test_the_original_whole_vector_workflow_proves_under_its_explicit_input_contract(tmp_path):
    seed = pipeline_seed(tmp_path)
    record = seed.prove("--summary", CONTRACT)
    assert record["verdict"] == "proven", record
    assert record["settings"]["vector_ownership"]["certificate"]["allocation_executions"].startswith("unbounded")


@needs_wp
def test_the_wrong_maximum_comparison_cannot_prove_after_the_pipeline_transformation(tmp_path):
    seed = pipeline_seed(tmp_path, SOURCE.replace("x > best.second", "x < best.second", 1))
    record = seed.prove("--summary", CONTRACT)
    assert record["verdict"] == "not_proven", record
    assert any(not row.get("smoke") and row["status"] != "valid" for row in record["goals"]), record
