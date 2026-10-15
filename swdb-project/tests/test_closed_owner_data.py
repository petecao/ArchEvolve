"""Current-owner data() reads through prove; created 2026-10-15 ET.

Admission controls use stand-in WP and cannot establish functional proof acceptance.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from conftest import REPO
from test_closed_owner_members import _record
from test_vector_ownership_wp import _ownership_seed
from test_wp_adapter import fake, method_version, needs_wp


SOURCE = """#include <vector>
#include <cstddef>
int swdb_vector_owner_data_safe(int n) {
  std::vector<int> v((std::size_t)n,7);
  int *p=v.data();
  v.push_back(9);
  return *v.data();
}
"""


@needs_wp
def test_an_immediate_data_read_carries_the_current_live_owner_domain(tmp_path):
    seed = _ownership_seed(tmp_path, source=SOURCE, cases=[("data_safe", 7)])
    record = _record(seed, "--summary", "contract.fixture_vector_owner_data_safe",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unknown", record
    certificate = record["settings"]["vector_ownership"]["certificate"]
    source = certificate["source_origins"]
    access, = [row for row in source["source_accesses"] if row["kind"] == "owner_data_read"]
    assert access["allocation_site"] == "growth"
    call, = [row for row in source["calls"] if "qualified_domain" in row]
    assert call["model"] == "std_vector_int_data"
    domain = call["qualified_domain"]
    assert domain["receiver"] == source["owner"]
    assert domain["producer"]["model"] == "std_vector_int_push_back"
    assert domain["allocation_site"] == "growth"
    assert domain["input_premises_added"] == []
    assert domain["model_relation"]["source_ast"]["return"] == "this->data"
    assert domain["caller_discharge"]["live_prefix_guard"] == access["live_prefix_guard"]
    assert domain["caller_discharge"]["bounds_guard"] == access["bounds_guard"]
    read, = [row for row in certificate["origins"]["view_accesses"] if row["kind"] == "owner_data_read"]
    assert read["allocation_site"] == "growth"
    assert read["bounds_guard"] == access["bounds_guard"]
    assert read["live_prefix_guard"] == access["live_prefix_guard"]


@needs_wp
@pytest.mark.parametrize("expression", ["*(v.data()+n+1)", "*((int *)v.data())"])
def test_current_owner_data_origin_does_not_admit_unchecked_offsets_or_casts(tmp_path, expression):
    source = SOURCE.replace("return *v.data();", "return " + expression + ";")
    seed = _ownership_seed(tmp_path, source=source, cases=[("data_safe", 7)])
    record = _record(seed, "--summary", "contract.fixture_vector_owner_data_safe",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])


@needs_wp
@pytest.mark.parametrize("fault", ["live_guard", "backing_guard", "returned_root", "model_contract"])
def test_a_rehashed_data_renderer_cannot_weaken_range_checks_or_change_the_returned_root(tmp_path, fault):
    from swdb import std_models
    seed = _ownership_seed(tmp_path, source=SOURCE, cases=[("data_safe", 7)])
    runtime = tmp_path / "changed-runtime"
    shutil.copytree(REPO / "swdb", runtime / "swdb", ignore=shutil.ignore_patterns("__pycache__"))
    path = runtime / "swdb" / "vector_ownership.py"
    source = path.read_text()
    if fault == "model_contract":
        path = runtime / "swdb" / "c_lowering.py"
        source = path.read_text()
        original = "    modeled = std_models.model_text(name)\n    if modeled is not None:\n        return modeled\n"
        changed = ("    modeled = std_models.model_text(name)\n    if modeled is not None:\n        return modeled.replace('requires std_vector_int_readable(this);', "
                   "'requires 1 == 1;') if name == 'std_vector_int_data' else modeled\n")
    else:
        original, changed = {
        "live_guard": ("owner_data_live_{ordinal}: 0 < swdb_owner_v.size", "owner_data_live_{ordinal}: 0 <= swdb_owner_v.size"),
        "backing_guard": ("owner_data_storage_{ordinal}: 0 < swdb_owner_bound1", "owner_data_storage_{ordinal}: 0 <= swdb_owner_bound1"),
        "returned_root": ('return "swdb_owner_v.data[0]"', 'return "swdb_owner_alias[0]"'),
        }[fault]
    assert source.count(original) == 1
    path.write_text(source.replace(original, changed))
    env = {**os.environ, **fake("unknown"), "SWDB_HOME": str(REPO), "PYTHONPATH": str(runtime),
           "SWDB_VERIFIER_LOCK": str(tmp_path / "scripted.lock")}
    refreshed = subprocess.run([sys.executable, "-c",
        "import json; from swdb import c_lowering,proof_setup; "
        "print(json.dumps([c_lowering.identity(),proof_setup.identity()]))"],
        cwd=runtime, env=env, capture_output=True, text=True, check=True)
    lowering, checks = json.loads(refreshed.stdout)
    method = method_version(lowering)
    method["checks"].update(checks)
    method["models"]["std_vector"] = std_models.identity()
    (seed.root / "library" / "methods" / "wp-tracer-fixture.yaml").write_text(yaml.safe_dump(method, sort_keys=False))
    result = subprocess.run([sys.executable, "-m", "swdb", "prove", "--records", str(seed.records),
        "--summary", "contract.fixture_vector_owner_data_safe", "--adapter", "wp",
        "--runs-dir", str(seed.runs), "--format", "json"], cwd=runtime, env=env,
        capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((seed.records / json.loads(result.stdout)["path"]).read_text())
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])


@needs_wp
def test_a_current_owner_data_read_does_not_revive_a_stale_captured_alias(tmp_path):
    source = SOURCE.replace("return *v.data();", "return *v.data() + *p;")
    seed = _ownership_seed(tmp_path, source=source, cases=[("data_safe", 14)])
    record = _record(seed, "--summary", "contract.fixture_vector_owner_data_safe",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unknown", record
    certificate = record["settings"]["vector_ownership"]["certificate"]
    current, stale = certificate["source_origins"]["source_accesses"]
    assert current["allocation_site"] == "growth"
    assert stale["allocation_site"] == "initial"
    assert stale["liveness_guard"] == "alias_live_after"
    report = next(row for row in record["evidence"]["reports"] if row["name"] == "wp_input")
    text = (seed.records / report["path"]).read_text()
    assert "ghost swdb_owner_alias_live=0;" in text
    assert "assert alias_live_after: swdb_owner_alias_live == 1;" in text


@needs_wp
def test_a_current_owner_data_value_read_proves_through_the_actual_wp_seam(tmp_path):
    seed = _ownership_seed(tmp_path, source=SOURCE, cases=[("data_safe", 7)])
    record = seed.prove("--summary", "contract.fixture_vector_owner_data_safe")
    assert record["verdict"] == "proven", record
    assert any("owner_data_live" in row.get("goal", "") for row in record["goals"])


@needs_wp
def test_a_fresh_data_value_read_cannot_make_a_stale_alias_prove_in_actual_wp(tmp_path):
    source = SOURCE.replace("return *v.data();", "return *v.data() + *p;")
    seed = _ownership_seed(tmp_path, source=source, cases=[("data_safe", 14)])
    record = seed.prove("--summary", "contract.fixture_vector_owner_data_safe")
    assert record["verdict"] == "not_proven", record
    assert any("alias_live_after" in row.get("property", "") for row in record["unproven_properties"]), record
