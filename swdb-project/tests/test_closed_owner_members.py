"""Qualified read-only member calls through prove; created 2026-10-15 ET.

The callsite relation supplies typed owner provenance; validity alone is insufficient.
Stand-in WP controls test admission/reporting and never claim a member was proved.
"""
import json
import os
import shutil
import subprocess
import sys

import yaml

from conftest import REPO, run_swdb
from test_vector_ownership_wp import _ownership_seed
from test_wp_adapter import fake, needs_wp


SOURCE = """#include <vector>
#include <cstddef>
int swdb_vector_owner_at_safe(int n) {
  std::vector<int> v((std::size_t)n, 7);
  int *p=v.data();
  int old_value=*p;
  v.push_back(9);
  return old_value + v.at(0) + v.at((std::size_t)n);
}
"""
BOUNDS_SOURCE = SOURCE + """int swdb_vector_owner_at_bounds(int n) {
  std::vector<int> v((std::size_t)n, 7);
  int *p=v.data();
  v.push_back(9);
  return v.at(2);
}
"""


def _record(seed, *arguments, env=None):
    result = run_swdb("prove", "--records", seed.records, *arguments, "--adapter", "wp",
        "--runs-dir", seed.runs, "--format", "json", env=env)
    assert result.returncode == 0, result.stderr + result.stdout
    return yaml.safe_load((seed.records / json.loads(result.stdout)["path"]).read_text())


def _bounds_seed(root):
    seed = _ownership_seed(root, source=BOUNDS_SOURCE, cases=[("at_safe", 23), ("at_bounds", 0)])
    path = root / "library" / "rewrite_contracts" / "fixture_vector_owner_at_bounds.yaml"
    entry = yaml.safe_load(path.read_text())
    # Set up a fresh original contract that ignores the selected value. For n=1,
    # the at(2) range obligation must fail independently of the postcondition.
    for claim in entry["clauses"]:
        if claim["id"] == "post":
            claim["acsl"]["text"] = "assigns \\nothing; ensures \\result >= 0;"
    path.write_text(yaml.safe_dump(entry, sort_keys=False))
    return seed


@needs_wp
def test_a_closed_at_call_records_its_qualified_live_domain_and_caller_discharge(tmp_path):
    seed = _ownership_seed(tmp_path, source=SOURCE, cases=[("at_safe", 23)])
    result = run_swdb("prove", "--records", seed.records, "--summary",
        "contract.fixture_vector_owner_at_safe", "--adapter", "wp", "--runs-dir", seed.runs,
        "--format", "json", env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((seed.records / json.loads(result.stdout)["path"]).read_text())
    assert record["failure_class"] == "unknown", record
    certificate = record["settings"]["vector_ownership"]["certificate"]
    calls = [row for row in certificate["source_origins"]["calls"] if row["model"] == "std_vector_int_at"]
    assert len(calls) == 2
    for ordinal, call in enumerate(calls, 1):
        domain = call["qualified_domain"]
        assert domain["id"] == "closed-vector-live-array-1"
        assert domain["allocation_site"] == "growth"
        assert domain["producer"]["model"] == "std_vector_int_push_back"
        assert domain["receiver"] == certificate["source_origins"]["owner"]
        assert domain["caller_discharge"]["guard"] == f"owner_at_guard_{ordinal}"
        assert domain["input_premises_added"] == []
    assert certificate["origins"]["qualified_calls"] == calls


@needs_wp
def test_a_standalone_at_model_keeps_its_opaque_incoming_field_refusal(tmp_path):
    seed = _ownership_seed(tmp_path)
    record = _record(seed, "--model", "std_vector_int_at", "--method-version", "method.wp-tracer-fixture",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])


@needs_wp
def test_missing_at_bounds_are_checked_without_adding_an_input_premise(tmp_path):
    seed = _bounds_seed(tmp_path)
    record = _record(seed, "--summary", "contract.fixture_vector_owner_at_bounds",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unknown", record
    call = next(row for row in record["settings"]["vector_ownership"]["certificate"]["source_origins"]["calls"]
                if row["model"] == "std_vector_int_at")
    assert call["qualified_domain"]["input_premises_added"] == []
    reports = record["evidence"]["reports"]
    generated = next(row for row in reports if row["name"] == "wp_input")
    text = (seed.records / generated["path"]).read_text()
    assert "assert owner_at_guard_1: 0 <= 2 < swdb_owner_v.size;" in text
    assert "requires 2 <" not in text


@needs_wp
def test_a_rehashed_renderer_cannot_drop_the_at_guard(tmp_path):
    from swdb import std_models
    from test_wp_adapter import method_version
    seed = _ownership_seed(tmp_path, source=SOURCE, cases=[("at_safe", 23)])
    runtime = tmp_path / "changed-runtime"
    shutil.copytree(REPO / "swdb", runtime / "swdb", ignore=shutil.ignore_patterns("__pycache__"))
    path = runtime / "swdb" / "vector_ownership.py"
    original = path.read_text()
    removed = 'checks.append(f"/*@ assert owner_at_guard_{ordinal}: 0 <= {rendered} < swdb_owner_v.size; */")'
    assert original.count(removed) == 1
    path.write_text(original.replace(removed, "pass"))
    # Fresh runtime pins ensure rejection comes from the independent C-view
    # guard inventory, rather than from an outdated method/source checksum.
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
        "--summary", "contract.fixture_vector_owner_at_safe", "--adapter", "wp",
        "--runs-dir", str(seed.runs), "--format", "json"], cwd=runtime, env=env,
        capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((seed.records / json.loads(result.stdout)["path"]).read_text())
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])


@needs_wp
def test_a_qualified_closed_at_call_proves_under_the_original_scalar_contract(tmp_path):
    seed = _ownership_seed(tmp_path, source=SOURCE, cases=[("at_safe", 23)])
    record = seed.prove("--summary", "contract.fixture_vector_owner_at_safe")
    assert record["verdict"] == "proven", record
    assert any("owner_at_guard" in row.get("goal", "") for row in record["goals"])


@needs_wp
def test_an_out_of_range_qualified_at_call_fails_its_actual_bounds_obligation(tmp_path):
    seed = _bounds_seed(tmp_path)
    record = seed.prove("--summary", "contract.fixture_vector_owner_at_bounds")
    assert record["verdict"] == "not_proven", record
    assert any("owner_at_guard" in row.get("property", "") for row in record["unproven_properties"]), record
