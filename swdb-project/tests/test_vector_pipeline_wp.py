"""Whole private vector copy/scan workflow through prove; created 2026-10-15 ET.

The source is the existing bounded/native fixture. WP's input origin and initializedness
are explicit in this separate contract, not inferred from address validity.
"""
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
