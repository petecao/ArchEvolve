"""LANL `Validation_definition`, `Validation_results` and the four empty tables
(LANL-shaped-db ticket 05). Created 2026-10-11 ET.

Built once from a small record closure (LR-03), never the ~1 GB catalog. The roots give one
correctness outcome of each kind: profiles that passed and one whose check timed out, and
evaluations of one fixture workload that passed, failed and stayed unverified."""

import json

import pytest

from conftest import make_records
from testkit.lanl import (assert_foreign_keys_clean, assert_guessed_listed, assert_lanl_shape, assert_origins,
                          assert_separable, sql)

VALIDATION = ("Validation_definition", "Validation_results")
EMPTY = ("physics_assets", "kernel_dependencies", "code_chunks", "embeddings")

PASSED_PROFILE = "gapbs-bfs-do.kron-g16-k16.mbit10.20260922t221109z"
TIMED_OUT_PROFILE = "gapbs-tc-ordered.kron-g22-k16.mbit10.20260922t233432z"
FIXTURE = "bfs-contract-20260925-a3.workload.584a833b37d4d8a1"
PASSED_EVALUATION = "bfs-contract-20260925-a3.candidate.evaluation"
FAILED_EVALUATION = "bfs-contract-20260925-a3.incorrect"
UNVERIFIED_EVALUATION = "bfs-contract-20260925-a3.timeout"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    records = make_records(tmp_path_factory.mktemp("lanl-validation")).copy_closure(
        PASSED_PROFILE, TIMED_OUT_PROFILE, PASSED_EVALUATION, FAILED_EVALUATION, UNVERIFIED_EVALUATION)
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr
    return records


def test_all_six_tables_have_exactly_the_expected_columns(built):
    assert_lanl_shape(built, *VALIDATION, *EMPTY)


def test_fixture_id_and_the_search_table_columns_are_listed_as_guessed(built):
    assert_guessed_listed(built, *VALIDATION, *EMPTY)


def results(built):
    """Each `Validation_results` row by the profile or evaluation it came from."""
    rows = sql(built, "select o.record_id, d.name as fixture, v.slug as variant, r.passed, r.max_abs_error "
                      "from Validation_results r join swdb_row_origins o on o.table_name = 'Validation_results' "
                      "and o.row_id = r.id join Validation_definition d on d.id = r.fixture_id "
                      "join kernel_variants v on v.id = r.kernel_variant_id")
    by_record = {row.pop("record_id"): row for row in rows}
    assert len(by_record) == len(rows), "one outcome record per result row"
    return by_record


def test_a_passing_and_a_failing_fixture_outcome_have_the_right_passed_value(built):
    found = results(built)
    assert found[PASSED_EVALUATION] == {"fixture": f"gapbs-bfs/{FIXTURE}", "variant": "gapbs-bfs-do",
                                        "passed": 1, "max_abs_error": None}
    assert found[FAILED_EVALUATION] == {"fixture": f"gapbs-bfs/{FIXTURE}", "variant": "gapbs-bfs-do",
                                        "passed": 0, "max_abs_error": None}
    assert found[PASSED_PROFILE] == {"fixture": "gapbs-bfs/kron-g16-k16", "variant": "gapbs-bfs-do",
                                     "passed": 1, "max_abs_error": None}


def test_an_outcome_whose_correctness_was_not_established_is_null_never_false(built):
    found = results(built)
    assert found[TIMED_OUT_PROFILE]["passed"] is None
    assert found[UNVERIFIED_EVALUATION]["passed"] is None


def test_an_outcome_without_a_kernel_variant_or_an_input_record_has_no_result_row(built):
    # The closure holds this dx100 smoke evaluation; it names no implementation, and its
    # workload is not a workload record.
    assert (built.path / "evaluations" / "bfs-dx100-smoke-20260925-a4.yaml").exists()
    assert "bfs-dx100-smoke-20260925-a4" not in results(built)


def test_a_fixture_is_the_kernel_check_with_the_input_its_outcomes_ran(built):
    rows = {row["name"]: row for row in sql(built, "select d.name, k.slug as kernel, d.input_json "
                                                   "from Validation_definition d join kernels k on k.id = d.kernel_id")}
    profile_input = rows["gapbs-bfs/kron-g16-k16"]
    assert profile_input["kernel"] == "gapbs-bfs"
    assert json.loads(profile_input["input_json"]) == built.read("inputs/kron-g16-k16.yaml")["generator"]
    workload = rows[f"gapbs-bfs/{FIXTURE}"]
    assert json.loads(workload["input_json"]) == built.read(f"workloads/{FIXTURE}.yaml")["definition"]
    assert rows["gapbs-tc/kron-g22-k16"]["kernel"] == "gapbs-tc"


def test_expected_output_and_max_abs_error_are_null_when_records_do_not_state_them(built):
    assert sql(built, "select count(*) as n from Validation_definition where expected_output_json is not null") \
        == [{"n": 0}]
    assert sql(built, "select count(*) as n from Validation_results where max_abs_error is not null") == [{"n": 0}]


def test_the_four_tables_without_sources_have_no_rows(built):
    for table in EMPTY:
        assert sql(built, f"select count(*) as n from {table}") == [{"n": 0}], table


def test_every_validation_row_names_its_records(built):
    assert_origins(built, *VALIDATION)
    rows = sql(built, "select o.record_id, o.record_field from swdb_row_origins o join Validation_definition d "
                      "on o.table_name = 'Validation_definition' and o.row_id = d.id "
                      "where d.name = 'gapbs-bfs/kron-g16-k16'")
    assert {"record_id": "gapbs-bfs", "record_field": "correctness_check"} in rows
    assert {"record_id": "kron-g16-k16", "record_field": "generator"} in rows
    assert {"record_id": PASSED_PROFILE, "record_field": "input"} in rows


def test_the_search_tables_link_to_source_files_and_code_chunks(built):
    links = {(table, row["from"]): (row["table"], row["to"])
             for table in ("code_chunks", "embeddings")
             for row in sql(built, f"select * from pragma_foreign_key_list('{table}')")}
    assert links == {("code_chunks", "source_file_id"): ("source_files", "id"),
                     ("embeddings", "code_chunk_id"): ("code_chunks", "id")}


def test_every_link_target_table_exists(built):
    tables = {row["name"] for row in sql(built, "select name from sqlite_master where type = 'table'")}
    assert "source_files" in tables   # built by swdb/lanl_sources.py, which runs before this group
    for table in (*VALIDATION, *EMPTY):
        targets = {row["table"] for row in sql(built, f"select * from pragma_foreign_key_list('{table}')")}
        assert targets <= tables, (table, targets - tables)


def test_a_build_passes_the_foreign_key_check(built):
    assert_foreign_keys_clean(built)


def test_deleting_every_swdb_table_leaves_a_consistent_lanl_database(built, tmp_path):
    assert_separable(built, tmp_path)
