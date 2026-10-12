"""LANL `kernels` and the guessed `kernel_variants` (LANL-shaped-db ticket 02). Created 2026-10-11 ET.

Built once from the record closure (LR-03), never the ~1 GB catalog. The shared checks in
`testkit.lanl` are the pattern later LANL table groups reuse with their own table names."""

import pytest

from conftest import make_records, read_yaml
from testkit.lanl import (assert_foreign_keys_clean, assert_guessed_listed, assert_lanl_shape, assert_origins,
                          assert_record_fields_resolve, assert_separable, sql)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    records = make_records(tmp_path_factory.mktemp("lanl-kernels")).copy_closure()
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr
    return records


def ids_of(records, folder):
    return {read_yaml(path)["id"] for path in (records.path / folder).glob("*.yaml")}


def test_kernels_has_exactly_the_slide_columns(built):
    assert_lanl_shape(built, "kernels")


def test_each_kernel_record_is_one_kernels_row_whose_slug_is_its_id(built):
    rows = sql(built, "select slug, name from kernels")
    assert sorted(r["slug"] for r in rows) == sorted(ids_of(built, "kernels"))
    names = {r["slug"]: r["name"] for r in rows}
    assert names["gapbs-bfs"] == built.read("kernels/gapbs-bfs.yaml")["name"]


def test_kernel_variants_has_the_guessed_columns(built):
    assert_lanl_shape(built, "kernel_variants")


def test_each_implementation_is_one_variant_linked_to_its_kernel(built):
    rows = sql(built, "select v.slug as variant, k.slug as kernel from kernel_variants v "
                      "join kernels k on k.id = v.kernel_id")
    assert sorted(r["variant"] for r in rows) == sorted(ids_of(built, "implementations"))
    stated = {data["id"]: data["kernel"]
              for data in map(read_yaml, (built.path / "implementations").glob("*.yaml"))}
    assert {r["variant"]: r["kernel"] for r in rows} == stated


def test_guessed_columns_list_kernel_variants_and_nothing_of_kernels(built):
    assert_guessed_listed(built, "kernels", "kernel_variants")


def test_every_kernels_and_variants_row_names_its_record(built):
    assert sql(built, "select count(*) as n from kernel_variants")[0]["n"] > 0
    assert_origins(built, "kernels", "kernel_variants")
    rows = sql(built, "select o.record_id, r.kind from swdb_row_origins o join kernel_variants v "
                      "on o.table_name = 'kernel_variants' and o.row_id = v.id join swdb_records r on r.id = o.record_id "
                      "where v.slug = 'gapbs-bfs-do'")
    assert rows == [{"record_id": "gapbs-bfs-do", "kind": "implementation"}]


def test_integer_ids_follow_record_id_order(built):
    for table in ("kernels", "kernel_variants"):
        slugs = [r["slug"] for r in sql(built, f"select slug from {table} order by id")]
        assert slugs == sorted(slugs), table


def test_every_record_field_names_a_field_of_its_record(built):
    assert_record_fields_resolve(built)


def test_a_build_passes_the_foreign_key_check(built):
    assert_foreign_keys_clean(built)


def test_deleting_every_swdb_table_leaves_a_consistent_lanl_database(built, tmp_path):
    assert_separable(built, tmp_path)


def test_category_is_the_application_domain(built):
    rows = sql(built, "select category from kernels where slug = 'gapbs-bfs'")
    assert rows == [{"category": built.read("applications/gapbs.yaml")["domain"]}]


def test_category_is_null_when_the_application_states_no_domain(records):
    # The application schema requires a `domain` string, so a validated folder always states one;
    # the builder itself (no validation) still stores an unstated domain as NULL, never a default.
    from swdb import db

    records.add_stub()
    application = records.read("applications/gapbs.yaml")
    application["domain"] = None
    records.write("applications/gapbs.yaml", application)
    path = records.path.parent / "build" / "unvalidated.sqlite"
    db.build(records.path, path)
    assert db.sql(path, "select slug, category from kernels") == [{"slug": "stub-kernel", "category": None}]
