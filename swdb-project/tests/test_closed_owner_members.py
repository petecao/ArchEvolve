"""Qualified read-only member calls through prove; created 2026-10-15 ET.

The callsite relation supplies typed owner provenance; validity alone is insufficient.
Stand-in WP controls test admission/reporting and never claim a member was proved.
"""
import json

import yaml

from conftest import run_swdb
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
