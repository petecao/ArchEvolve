"""Initialization obligations through public swdb prove. Created: 2026-10-15 ET.

Seam: the existing ticket-24 summary proof command; deliberately ignored read values
must still generate initialization obligations. No private adapter calls or fake WP.
"""
import json
import shutil

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_proof_records import _library_roots
from test_wp_adapter import method_version, needs_wp
from test_wp_subset import _entry
from testkit.record_subset import copy_record_subset


@needs_wp
@pytest.mark.parametrize("source,pre,expected", [
    ("int init_control(void) { int x; int observed = x; return 0; }", "", "not_proven"),
    ("int init_control(void) { int x = 7; int observed = x; return 0; }", "", "proven"),
    ("int helper(void) { int x; int observed = x; return 0; }\n"
     "int init_control(void) { return helper(); }", "", "not_proven"),
    ("int init_control(int *p) { int observed = *p; return 0; }",
     "requires \\valid(p);", "not_proven"),
    ("int init_control(int *p) { int observed = *p; return 0; }",
     "requires \\valid(p) && \\initialized(p);", "proven"),
    ("int init_control(void) { int *p = new int[1]; int observed = p[0]; return 0; }",
     "", "not_proven"),
], ids=["uninitialized-local", "initialized-local", "inlined-uninitialized-local",
        "valid-pointer-only", "initialized-pointer", "uninitialized-new-array"])
def test_every_unit_read_requires_initialization_even_when_its_value_is_unused(tmp_path, source, pre, expected):
    from swdb import c_lowering
    records = make_records(tmp_path)
    copy_record_subset(REPO / "records", records.path, sorted(_library_roots()))
    shutil.copytree(REPO / "library", tmp_path / "library")
    methods = tmp_path / "library" / "methods"
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    method = method_version(c_lowering.identity())
    method["budgets"]["wp_seconds_per_solver"] = 2
    (methods / "wp-tracer-fixture.yaml").write_text(yaml.safe_dump(method))
    source += "\n"
    unit = tmp_path / "library" / "proof_units" / "initialization.cc"
    unit.parent.mkdir(exist_ok=True)
    unit.write_text(source)
    cid = "contract.fixture_initialization"
    entry = _entry(cid, "init_control", "initialization.cc", source,
                   ([("pre", "legality", pre)] if pre else []) +
                   [("post", "postcondition", "assigns \\nothing; ensures \\result == 0;")],
                   ["p"] if "init_control(int *p)" in source else [], {"once": "self"})
    (tmp_path / "library" / "rewrite_contracts" / "initialization.yaml").write_text(yaml.safe_dump(entry))
    result = run_swdb("prove", "--records", records.path, "--summary", cid, "--adapter", "wp",
                      "--runs-dir", tmp_path / "runs", "--format", "json")
    assert result.returncode == 0, result.stderr
    record = yaml.safe_load((records.path / json.loads(result.stdout)["path"]).read_text())
    assert record["verdict"] == expected, record
    if expected == "not_proven":
        assert any("initializ" in str(g).lower() and g["status"] != "valid"
                   for g in record["goals"]), record["goals"]
