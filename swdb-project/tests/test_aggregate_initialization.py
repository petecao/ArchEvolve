"""Implicit aggregate-copy initialization through swdb prove; created 2026-10-15 ET.

The source is parsed as C++17. CWG2264 leaves the treatment of indeterminate members under discussion;
this proof subset conservatively requires initialized memberwise-copy sources. It does not diagnose every
C++ implementation's behavior as undefined. Public seam: summary proof with a real WP initializedness setup.
"""
import shutil

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records
from test_proof_records import _library_roots
from test_wp_adapter import method_version, needs_wp
from test_wp_subset import Seed, _entry
from testkit.record_subset import copy_record_subset
from test_c_lowering import lower

SOURCE = """struct SwdbAggregate { int first; int second; };
struct SwdbOuter {
  SwdbAggregate value;
  SwdbOuter(const SwdbAggregate &source) : value(source) {}
};
int swdb_aggregate_uninitialized() {
  SwdbAggregate source;
  SwdbAggregate copied = source;
  return 0;
}
int swdb_aggregate_initialized() {
  SwdbAggregate source = {1, 2};
  SwdbAggregate copied = source;
  return copied.first + copied.second;
}
int swdb_aggregate_member_uninitialized() {
  SwdbAggregate source;
  SwdbOuter copied(source);
  return 0;
}
int swdb_aggregate_member_initialized() {
  SwdbAggregate source = {1, 2};
  SwdbOuter copied(source);
  return copied.value.first + copied.value.second;
}
"""


@pytest.fixture(scope="module")
def aggregate_subset(tmp_path_factory):
    from swdb import c_lowering
    root = tmp_path_factory.mktemp("wp-aggregate-initialization")
    records = make_records(root)
    copy_record_subset(REPO / "records", records.path, sorted(_library_roots()))
    shutil.copytree(REPO / "library", root / "library")
    methods = root / "library" / "methods"
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    (methods / "wp-tracer-fixture.yaml").write_text(yaml.safe_dump(method_version(c_lowering.identity()), sort_keys=False))
    units = root / "library" / "proof_units"
    units.mkdir(exist_ok=True)
    (units / "aggregate_initialization.cc").write_text(SOURCE)
    for label, value in (("uninitialized", 0), ("initialized", 3),
                         ("member_uninitialized", 0), ("member_initialized", 3)):
        cid = f"contract.fixture_aggregate_{label}"
        data = _entry(cid, f"swdb_aggregate_{label}", "aggregate_initialization.cc", SOURCE,
                      [("pre", "legality", "requires \\true;"),
                       ("post", "postcondition", f"assigns \\nothing; ensures \\result == {value};")],
                      [], {"once": "self"})
        (root / "library" / "rewrite_contracts" / f"fixture_aggregate_{label}.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False))
    return Seed(root, {})


@needs_wp
@pytest.mark.parametrize("member", [False, True])
@pytest.mark.parametrize("initialized", [False, True])
def test_implicit_memberwise_copy_requires_an_initialized_source_even_when_its_value_is_ignored(
        aggregate_subset, initialized, member):
    label = ("member_" if member else "") + ("initialized" if initialized else "uninitialized")
    record = aggregate_subset.prove("--summary", f"contract.fixture_aggregate_{label}")
    _assert_copy_result(record, initialized)


def _assert_copy_result(record, initialized):
    assert record["verdict"] == ("proven" if initialized else "not_proven"), record
    if not initialized:
        assert any(row.get("kind") == "user assertion" and "\\initialized" in row.get("property", "")
                   for row in record["unproven_properties"]), record["unproven_properties"]


def test_an_implicit_assignment_is_refused_until_its_expression_order_is_checked(tmp_path):
    source = tmp_path / "assignment.cc"
    source.write_text("struct SwdbAggregate { int first; int second; };\n"
                      "int swdb_copy() { SwdbAggregate source; SwdbAggregate dest={1,2}; "
                      "dest=source; return 0; }\n")
    result = lower(source, "swdb_copy", tmp_path / "out", ok=False)
    assert "implicit memberwise assignment" in result.stderr


@pytest.mark.parametrize("body,reason", [
    ("SwdbAggregate source={1,2}; for(SwdbAggregate copy=source;copy.first<2;++copy.first) {}",
     "implicit memberwise copy in a for initializer"),
    ("SwdbAggregate source=source;", "without a simple source lvalue"),
])
def test_unchecked_copy_contexts_fail_closed_at_the_public_lowering_seam(tmp_path, body, reason):
    source = tmp_path / "unchecked.cc"
    source.write_text("struct SwdbAggregate { int first; int second; };\n"
                      f"int swdb_copy() {{ {body} return 0; }}\n")
    result = lower(source, "swdb_copy", tmp_path / "out", ok=False)
    assert reason in result.stderr


def test_multiple_declarations_check_each_copy_after_its_source_is_in_scope(tmp_path):
    source = tmp_path / "multiple.cc"
    source.write_text("struct SwdbAggregate { int first; int second; };\n"
                      "int swdb_copy() { SwdbAggregate source={1,2}, copy=source; return copy.first; }\n")
    lower(source, "swdb_copy", tmp_path / "out")
    text = (tmp_path / "out" / "swdb_copy.c").read_text()
    assert text.index("SwdbAggregate source = {1, 2};") < text.index("\\initialized(&source)")
    assert text.index("\\initialized(&source)") < text.index("SwdbAggregate copy = source;")


@pytest.mark.parametrize("body", ["++counter; return 0;", "return counter;"])
def test_an_omp_named_source_definition_cannot_hide_effects_in_a_copy_address(tmp_path, body):
    source = tmp_path / "effect.cc"
    source.write_text("struct SwdbAggregate { int first; int second; };\n"
                      f"int counter=0; int omp_get_thread_num() {{ {body} }}\n"
                      "int swdb_copy() { SwdbAggregate cells[1]={{1,2}}; "
                      "SwdbAggregate copy=cells[omp_get_thread_num()]; return copy.first; }\n")
    result = lower(source, "swdb_copy", tmp_path / "out", ok=False)
    assert "without a simple source lvalue" in result.stderr
