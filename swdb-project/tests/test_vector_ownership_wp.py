"""Unbounded vector ownership through swdb prove; created 2026-10-15 ET.

The source contract keeps assigns nothing. A private-region proof view must separately justify
its source-frame projection; merely proving a broader frame is not acceptance.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
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


def _ownership_seed(root):
    from swdb import c_lowering, std_models
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


@pytest.fixture(scope="module")
def ownership_subset(tmp_path_factory):
    return _ownership_seed(tmp_path_factory.mktemp("wp-vector-ownership"))


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


@needs_wp
def test_the_closed_owner_view_reports_typed_origins_for_all_source_and_generated_accesses(ownership_subset):
    from test_wp_adapter import fake
    result = run_swdb("prove", "--records", ownership_subset.records, "--summary",
        "contract.fixture_vector_owner_safe", "--adapter", "wp", "--runs-dir", ownership_subset.runs,
        "--format", "json", env=fake("unknown"))
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((ownership_subset.records / json.loads(result.stdout)["path"]).read_text())
    assert record["failure_class"] == "unknown", record
    origins = record["settings"]["vector_ownership"]["certificate"]["origins"]
    assert origins["complete"] is True
    assert {row["site"] for row in origins["allocations"]} == {"initial", "growth"}
    assert all(row["element_type"] == "int" for row in origins["allocations"])
    assert origins["aliases"][0]["allocation_site"] == "initial"
    assert origins["aliases"][0]["invalidated_by"] == "growth"
    assert origins["source_accesses"] and origins["view_accesses"]
    assert all(row["bounds_guard"] for row in origins["view_accesses"])
    assert all(row["liveness_guard"] for row in origins["view_accesses"] if row.get("alias"))


@needs_wp
@pytest.mark.parametrize("fault", ["alias_offset", "liveness_guard", "range_guard_position"])
def test_a_rehashed_renderer_cannot_hide_wrong_alias_origins_or_weakened_liveness(tmp_path, fault):
    from test_wp_adapter import fake
    seed = _ownership_seed(tmp_path)
    runtime = tmp_path / "changed-runtime"
    shutil.copytree(REPO / "swdb", runtime / "swdb", ignore=shutil.ignore_patterns("__pycache__"))
    target = runtime / "swdb" / "vector_ownership.py"
    source = target.read_text()
    if fault == "range_guard_position":
        guard = "/*@ assert owner_initial_range: 0 <= swdb_owner_k0 < swdb_owner_bound0; */"
        old = 'f"  for(swdb_owner_k0=0;swdb_owner_k0<swdb_owner_bound0;++swdb_owner_k0) {{",'
        assert source.count(old) == source.count(guard) == 1
        source = source.replace('"    '+guard+'",', '')
        source = source.replace(old, '"  '+guard+'",'+old)
    else:
        old, new = (("int *swdb_owner_alias=swdb_owner_v.data;", "int *swdb_owner_alias=swdb_owner_v.data+1;")
                    if fault == "alias_offset" else
                    ("assert alias_live_after: swdb_owner_alias_live == 1", "assert alias_live_after: 1 == 1"))
        assert source.count(old) == 1
        source = source.replace(old, new)
    target.write_text(source)
    env = {**os.environ, **fake("unknown"), "SWDB_HOME": str(REPO), "PYTHONPATH": str(runtime)}
    refreshed = subprocess.run([sys.executable, "-c",
        "import json; from swdb import c_lowering,proof_setup; "
        "print(json.dumps([c_lowering.identity(),proof_setup.identity()]))"],
        cwd=runtime, env=env, capture_output=True, text=True, check=True)
    lowering, checks = json.loads(refreshed.stdout)
    method = method_version(lowering)
    method["checks"].update(checks)
    from swdb import std_models
    method["models"]["std_vector"] = std_models.identity()
    (seed.root / "library" / "methods" / "wp-tracer-fixture.yaml").write_text(yaml.safe_dump(method, sort_keys=False))
    label = "stale" if fault == "liveness_guard" else "safe"
    result = subprocess.run([sys.executable, "-m", "swdb", "prove", "--records", str(seed.records),
        "--adapter", "wp", "--summary", "contract.fixture_vector_owner_"+label,
        "--runs-dir", str(seed.runs), "--format", "json"],
        cwd=runtime, env=env, capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((seed.records / json.loads(result.stdout)["path"]).read_text())
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])
