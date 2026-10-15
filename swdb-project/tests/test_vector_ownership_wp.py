"""Unbounded vector ownership through swdb prove; created 2026-10-15 ET.

The source contract keeps assigns nothing. A private-region proof view must separately justify
its source-frame projection; merely proving a broader frame is not acceptance.
"""
import shutil

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records
from test_proof_records import _library_roots
from test_wp_adapter import method_version, needs_wp
from test_wp_subset import Seed, _entry
from testkit.record_subset import copy_record_subset

REFUSALS = {
    "pointer_comparison": "return p == v.data();",
    "second_append": "v.push_back(11); return 0;",
    "copied_alias": "int *q=p; return *q;",
    "write_alias": "*p=4; return 0;",
    "clear_alias": "v.clear(); return *p;",
    "pointer_cast": "return *((int *)p);",
    "local_address": "int x=1; int *q=&x; return *q;",
}

SOURCE = """#include <vector>
#include <cstddef>
int swdb_vector_owner_safe(int n) {
  std::vector<int> v((std::size_t)n, 7);
  int *p = v.data();
  int old_value = *p;
  v.push_back(9);
  return old_value + v[0] + v[(std::size_t)n];
}
int swdb_vector_owner_stale(int n) {
  std::vector<int> v((std::size_t)n, 7);
  int *p = v.data();
  v.push_back(9);
  return *p;
}
"""
for _name, _tail in REFUSALS.items():
    SOURCE += (f"int swdb_vector_owner_{_name}(int n) {{ std::vector<int> v((std::size_t)n,7); "
               f"int *p=v.data(); v.push_back(9); {_tail} }}\n")


@pytest.fixture(scope="module")
def ownership_subset(tmp_path_factory):
    from swdb import c_lowering, std_models
    root = tmp_path_factory.mktemp("wp-vector-ownership")
    records = make_records(root)
    copy_record_subset(REPO / "records", records.path, sorted(_library_roots()))
    shutil.copytree(REPO / "library", root / "library")
    methods = root / "library" / "methods"
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    method = method_version(c_lowering.identity())
    method["models"]["std_vector"] = std_models.identity()
    (methods / "wp-tracer-fixture.yaml").write_text(yaml.safe_dump(method, sort_keys=False))
    units = root / "library" / "proof_units"
    units.mkdir(exist_ok=True)
    (units / "vector_ownership.cc").write_text(SOURCE)
    for label, value in (("safe", 23), ("stale", 7), *((name, 0) for name in REFUSALS)):
        cid = f"contract.fixture_vector_owner_{label}"
        data = _entry(cid, f"swdb_vector_owner_{label}", "vector_ownership.cc", SOURCE,
                      [("pre", "legality", "requires n >= 1;"),
                       ("post", "postcondition", f"assigns \\nothing; ensures \\result == {value};")],
                      [], {"once": "self"})
        (root / "library" / "rewrite_contracts" / f"fixture_vector_owner_{label}.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False))
    return Seed(root, {})


@needs_wp
def test_a_local_vector_grows_and_preserves_a_value_read_before_invalidation(ownership_subset):
    record = ownership_subset.prove("--summary", "contract.fixture_vector_owner_safe")
    assert record["verdict"] == "proven", record
    assert record["settings"]["vector_ownership"]["source_frame"] == "assigns \\nothing;"
    assert record["settings"]["vector_ownership"]["source_frame_preservation"] == "checked"


@needs_wp
def test_a_retained_data_pointer_fails_a_checked_liveness_obligation_after_growth(ownership_subset):
    record = ownership_subset.prove("--summary", "contract.fixture_vector_owner_stale")
    assert record["verdict"] == "not_proven", record
    assert any("alias_live" in row.get("property", "") for row in record["unproven_properties"]), record


@needs_wp
@pytest.mark.parametrize("control", sorted(REFUSALS))
def test_untracked_vector_observations_and_protocols_refuse_before_verification(ownership_subset, control):
    record = ownership_subset.prove("--summary", f"contract.fixture_vector_owner_{control}")
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"]), record
