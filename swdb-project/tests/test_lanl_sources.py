"""LANL source tables: `source_files`, `executables`, `definitions`, `data_structures`
(LANL-shaped-db ticket 03). Created 2026-10-11 ET.

Built once from the record closure of one source snapshot (LR-03), never the ~1 GB catalog.
Expected values come from the records themselves, read independently of the builder."""

import pytest

from conftest import make_records
from testkit.lanl import (assert_foreign_keys_clean, assert_guessed_listed, assert_lanl_shape, assert_origins,
                          assert_record_fields_resolve, assert_separable, sql)

TABLES = ("source_files", "executables", "definitions", "data_structures")
SNAPSHOT = "typed-library-bfs-scalar-profile-20261003-a2.package.v1.source"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    records = make_records(tmp_path_factory.mktemp("lanl-sources")).copy_closure(SNAPSHOT)
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr
    return records


def test_source_tables_have_exactly_the_slide_columns(built):
    assert_lanl_shape(built, *TABLES)


def test_an_implementation_code_file_is_one_source_files_row(built):
    # gapbs-pr-jacobi keeps its code beside its record (root: records).
    rows = sql(built, "select k.slug as kernel, s.path from source_files s join kernels k on k.id = s.kernel_id "
                      "where s.path like '%pr_spmv.cc'")
    assert {"kernel": "gapbs-pr", "path": "records/implementations/gapbs-pr-jacobi/pr_spmv.cc"} in rows
    assert len([r for r in rows if r["path"] == "records/implementations/gapbs-pr-jacobi/pr_spmv.cc"]) == 1


def test_a_file_named_by_several_code_entries_is_one_row_with_an_origin_per_entry(built):
    # gapbs-bfs-do names src/bfs.cc (application root, local copy apps/gapbs) in six code entries.
    rows = sql(built, "select s.id from source_files s join kernels k on k.id = s.kernel_id "
                      "where k.slug = 'gapbs-bfs' and s.path = 'apps/gapbs/src/bfs.cc'")
    assert len(rows) == 1
    origins = sql(built, f"select record_field from swdb_row_origins where table_name = 'source_files' "
                         f"and row_id = {rows[0]['id']} and record_id = 'gapbs-bfs-do'")
    assert sorted(o["record_field"] for o in origins) == [f"code[{i}]" for i in range(6)]


def test_code_files_take_the_application_language(built):
    # Both files belong to the gapbs application, whose record states `language: C++11`.
    rows = sql(built, "select language from source_files where path in "
                      "('apps/gapbs/src/bfs.cc', 'records/implementations/gapbs-pr-jacobi/pr_spmv.cc')")
    assert [r["language"] for r in rows] == ["C++11", "C++11"]


def test_every_retained_snapshot_file_is_a_source_file_of_the_snapshot_kernel(built):
    snapshot = built.read(f"source_snapshots/{SNAPSHOT}.yaml")
    tree = snapshot["artifact"]["path"]
    rows = sql(built, f"select k.slug as kernel, s.path from source_files s join kernels k on k.id = s.kernel_id "
                      f"where s.path like '{tree}/%'")
    assert sorted(r["path"] for r in rows) == sorted(f"{tree}/{f['path']}" for f in snapshot["artifact"]["files"])
    assert {r["kernel"] for r in rows} == {"gapbs-bfs"}   # its implementation dx100-bfs-scalar implements gapbs-bfs


def test_a_snapshot_file_has_a_language_only_when_the_snapshot_names_it_as_code(built):
    tree = built.read(f"source_snapshots/{SNAPSHOT}.yaml")["artifact"]["path"]
    rows = sql(built, f"select path, language from source_files where path in "
                      f"('{tree}/benchmarks/gapbs/src/bfs.cc', '{tree}/LICENSE')")
    # dx100-gapbs states `language: C++11`; the snapshot's context.code names only bfs.cc.
    assert {r["path"].removeprefix(tree + "/"): r["language"] for r in rows} == {
        "benchmarks/gapbs/src/bfs.cc": "C++11", "LICENSE": None}


def test_each_implementation_build_is_one_executable_without_an_unstated_path_or_kind(built):
    # An implementation's build names one program but no binary file (`-o {binary}`), so the
    # program is named by its implementation and `path` and `kind` are unknown (NULL).
    rows = sql(built, "select k.slug as kernel, e.name, e.kind, e.path from executables e "
                      "join kernels k on k.id = e.kernel_id")
    stated = {data["id"]: data["kernel"] for data in map(built.read, _implementation_files(built))}
    assert sorted(r["name"] for r in rows) == sorted(stated)
    assert {r["name"]: r["kernel"] for r in rows} == stated
    assert {(r["kind"], r["path"]) for r in rows} == {(None, None)}
    origins = sql(built, "select o.record_id, o.record_field from swdb_row_origins o join executables e "
                         "on o.table_name = 'executables' and o.row_id = e.id where e.name = 'gapbs-bfs-do'")
    assert origins == [{"record_id": "gapbs-bfs-do", "record_field": "build"}]


def definitions(records, name):
    """Each `definitions` row called `name`: its file path (None when unknown), kind, and origins."""
    rows = sql(records, f"select d.id, s.path, d.kind from definitions d left join source_files s "
                        f"on s.id = d.source_file_id where d.name = '{name}'")
    for row in rows:
        row["origins"] = sorted((o["record_id"], o["record_field"]) for o in sql(
            records, f"select record_id, record_field from swdb_row_origins "
                     f"where table_name = 'definitions' and row_id = {row.pop('id')}"))
    return rows


def test_an_implementation_function_is_defined_in_its_first_code_file(built):
    # The format puts the kernel function in code[0], the file that is built. Two implementations
    # name DOBFS in the same gapbs file, so it is one definition with both origins.
    [row] = [r for r in definitions(built, "DOBFS") if r["path"] == "apps/gapbs/src/bfs.cc"]
    assert row["kind"] == "function"
    assert ("gapbs-bfs-do", "function") in row["origins"]
    assert ("gapbs-bfs-do", "run.kernel_symbols[0]") in row["origins"]
    assert ("bfs-contract-20260925-a3.independent-reference", "function") in row["origins"]


def test_a_statement_function_is_defined_in_the_file_its_statements_are_in(built):
    # dx100-bfs-scalar's statements are in TDStep, at benchmarks/gapbs/src/bfs.cc of dx100-gapbs.
    [row] = [r for r in definitions(built, "TDStep") if r["path"] == "apps/dx100/benchmarks/gapbs/src/bfs.cc"]
    assert ("dx100-bfs-scalar", "extensions.statements.function") in row["origins"]
    assert ("dx100-bfs-scalar", "run.kernel_symbols[1]") in row["origins"]


def test_a_kernel_symbol_whose_file_no_record_states_has_no_source_file(built):
    # gapbs-tc-ordered lists two code files (tc.cc, builder.h) and never says which holds which symbol.
    assert definitions(built, "RelabelByDegree") == [
        {"path": None, "kind": "function", "origins": [("gapbs-tc-ordered", "run.kernel_symbols[3]")]}]


def test_a_snapshot_function_region_is_defined_in_the_snapshot_file(built):
    snapshot = built.read(f"source_snapshots/{SNAPSHOT}.yaml")
    index, region = next((i, r) for i, r in enumerate(snapshot["regions"]) if r.get("kind") == "function")
    path = f"{snapshot['artifact']['path']}/{region['path']}"
    [row] = [r for r in definitions(built, region["name"]) if r["path"] == path]
    assert (SNAPSHOT, f"regions[{index}]") in row["origins"]


def test_every_definition_is_a_function(built):
    assert sql(built, "select distinct kind from definitions") == [{"kind": "function"}]


def test_each_array_an_access_pattern_step_names_is_one_data_structure_of_its_kernel(built):
    stated = {(data["kernel"], step["array"]["name"])
              for data in map(built.read, _implementation_files(built))
              for pattern in data.get("access_patterns") or [] for step in pattern["steps"]}
    rows = sql(built, "select k.slug as kernel, d.name from data_structures d join kernels k on k.id = d.kernel_id")
    assert sorted((r["kernel"], r["name"]) for r in rows) == sorted(stated)


def test_a_data_structure_kind_is_its_stated_layout(built):
    # gapbs-pr's g.in_index_ is an array of pointers in both PageRank implementations.
    rows = sql(built, "select d.kind from data_structures d join kernels k on k.id = d.kernel_id "
                      "where k.slug = 'gapbs-pr' and d.name = 'g.in_index_'")
    assert rows == [{"kind": "array_of_pointers"}]
    origins = sql(built, "select o.record_id, o.record_field from swdb_row_origins o join data_structures d "
                         "on o.table_name = 'data_structures' and o.row_id = d.id join kernels k on k.id = d.kernel_id "
                         "where k.slug = 'gapbs-pr' and d.name = 'g.in_index_' and o.record_id = 'gapbs-pr-jacobi'")
    assert origins == [{"record_id": "gapbs-pr-jacobi", "record_field": "access_patterns[0].steps[0].array"}]


def test_source_tables_list_no_guessed_column(built):
    assert_guessed_listed(built, *TABLES)


def test_every_source_table_row_names_its_record(built):
    for table in TABLES:
        assert sql(built, f"select count(*) as n from {table}")[0]["n"] > 0, table
    assert_origins(built, *TABLES)


def test_every_record_field_names_a_field_of_its_record(built):
    assert_record_fields_resolve(built)


def test_a_build_passes_the_foreign_key_check(built):
    assert_foreign_keys_clean(built)


def test_deleting_every_swdb_table_leaves_a_consistent_lanl_database(built, tmp_path):
    assert_separable(built, tmp_path)


def test_a_fixture_implementation_code_build_function_and_arrays_each_appear_once(records):
    records.add_stub()
    impl = records.read("implementations/stub-impl.yaml")
    impl["access_patterns"][0]["steps"][2]["array"]["layout"] = "unknown"   # contrib
    records.write("implementations/stub-impl.yaml", impl)
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr

    assert sql(records, "select path, language from source_files") == [
        {"path": "records/implementations/stub-impl/stub_bench.py", "language": "C++11"}]
    assert sql(records, "select name, kind, path from executables") == [{"name": "stub-impl", "kind": None, "path": None}]
    assert sql(records, "select s.path, d.name, d.kind from definitions d join source_files s on s.id = d.source_file_id") == [
        {"path": "records/implementations/stub-impl/stub_bench.py", "name": "StubKernel", "kind": "function"}]
    arrays = {step["array"]["name"] for pattern in impl["access_patterns"] for step in pattern["steps"]}
    rows = sql(records, "select name, kind from data_structures")
    assert sorted(r["name"] for r in rows) == sorted(arrays)
    kinds = {r["name"]: r["kind"] for r in rows}
    assert (kinds["g.in_index_"], kinds["contrib"]) == ("array_of_pointers", None)   # unknown layout is NULL
    assert_origins(records, *TABLES)


def test_language_is_null_when_the_application_states_none(records):
    # The application schema requires `language`, so a validated folder always states one; the
    # builder itself (no validation) still stores an unstated language as NULL, never a default.
    from swdb import db

    records.add_stub()
    application = records.read("applications/gapbs.yaml")
    application["language"] = None
    records.write("applications/gapbs.yaml", application)
    path = records.path.parent / "build" / "unvalidated.sqlite"
    db.build(records.path, path)
    assert db.sql(path, "select path, language from source_files") == [
        {"path": "records/implementations/stub-impl/stub_bench.py", "language": None}]


def test_records_that_disagree_on_a_layout_leave_the_kind_unknown(records):
    records.add_stub()
    other = records.read("implementations/stub-impl.yaml")
    other["id"] = "stub-impl-aos"
    other["access_patterns"][0]["steps"][2]["array"]["layout"] = "array_of_structs"   # contrib
    records.write("implementations/stub-impl-aos.yaml", other)
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr
    assert sql(records, "select kind from data_structures where name = 'contrib'") == [{"kind": None}]
    assert sql(records, "select kind from data_structures where name = 'g.in_index_'") == [{"kind": "array_of_pointers"}]


def test_a_statement_function_already_placed_by_the_implementation_is_that_one_definition(records):
    # stub-impl's `function` StubKernel is in code[0]. Its statements name StubKernel too, from two
    # source files, so they place it nowhere themselves: the implementation's placement holds,
    # and no second, file-less StubKernel row appears. Built without validation: the statements
    # are minimal.
    from swdb import db

    records.add_stub()
    impl = records.read("implementations/stub-impl.yaml")
    impl["extensions"] = {"statements": {"function": "StubKernel", "annotations": [
        {"id": f"s{i}", "source": {"root": "records", "path": f"implementations/stub-impl/part{i}.cc"}}
        for i in range(2)]}}
    records.write("implementations/stub-impl.yaml", impl)
    path = records.path.parent / "build" / "unvalidated.sqlite"
    db.build(records.path, path)
    rows = db.sql(path, "select d.id, s.path from definitions d left join source_files s on s.id = d.source_file_id "
                        "where d.name = 'StubKernel'")
    assert [row["path"] for row in rows] == ["records/implementations/stub-impl/stub_bench.py"]
    origins = db.sql(path, f"select record_field from swdb_row_origins where table_name = 'definitions' "
                           f"and row_id = {rows[0]['id']} order by record_field")
    assert [o["record_field"] for o in origins] == ["extensions.statements.function", "function",
                                                    "run.kernel_symbols[0]"]


def _implementation_files(records):
    return [path.relative_to(records.path) for path in sorted((records.path / "implementations").glob("*.yaml"))]
