"""Contract link tables: `swdb_contract_definitions`, `swdb_contract_data_structures`,
`swdb_contract_kernels`, `swdb_contract_kernel_variants` (LANL-shaped-db ticket 06). Created 2026-10-11 ET.

Built once from the record closure of two certifications (LR-03), never the ~1 GB catalog, with
the repository library beside it. The closure holds `dx100-bfs-scalar`, whose statements carry
`legality:contract.bfs_read_offload:<clause>` facts. Expected values are read from the records,
or written out from them, independently of the builder."""

import shutil

import pytest

from conftest import REPO, make_records
from testkit.lanl import assert_foreign_keys_clean, assert_record_fields_resolve, assert_separable, sql

#: contract.bfs_read_offload and contract.bfs_tdstep_frontier_staging, each certified on the
#: scalar-only BFS snapshot of dx100-bfs-scalar.
CERTIFICATIONS = ("certification.1e4397e31d594245bc10bd80ff2107f5", "certification.ac33f5548c154caba9adbf0e4abb8925")
LINKS = {"swdb_contract_definitions": "definition_id", "swdb_contract_data_structures": "data_structure_id",
         "swdb_contract_kernels": "kernel_id", "swdb_contract_kernel_variants": "kernel_variant_id"}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    records = make_records(tmp_path_factory.mktemp("lanl-contracts")).copy_closure(*CERTIFICATIONS)
    shutil.copytree(REPO / "library", records.path.parent / "library")
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr
    return records


def test_link_tables_name_the_contract_the_lanl_row_the_clause_and_the_stating_record(built):
    for table, target in LINKS.items():
        columns = {row["name"] for row in sql(built, f"select name from pragma_table_info('{table}')")}
        assert columns == {"contract", target, "clause", "record_id", "record_field"}, table


def test_a_certified_contract_links_to_the_variant_its_snapshot_is_of_and_that_variant_kernel(built):
    expected = set()
    for certification in CERTIFICATIONS:
        candidate = built.read(f"certifications/{certification}.yaml")["candidate"]
        snapshot = built.read(f"source_snapshots/{candidate['snapshot']}.yaml")
        expected.add((candidate["contract"], snapshot["implementation"], certification))
    assert expected == {("contract.bfs_read_offload", "dx100-bfs-scalar", CERTIFICATIONS[0]),
                        ("contract.bfs_tdstep_frontier_staging", "dx100-bfs-scalar", CERTIFICATIONS[1])}

    variants = sql(built, "select l.contract, v.slug, l.clause, l.record_id, l.record_field "
                          "from swdb_contract_kernel_variants l join kernel_variants v on v.id = l.kernel_variant_id "
                          "where l.record_id like 'certification.%'")
    assert {(r["contract"], r["slug"], r["record_id"]) for r in variants} == expected
    assert {(r["clause"], r["record_field"]) for r in variants} == {(None, "candidate")}
    kernels = sql(built, "select l.contract, k.slug, l.record_id from swdb_contract_kernels l "
                         "join kernels k on k.id = l.kernel_id where l.record_id like 'certification.%'")
    # dx100-bfs-scalar implements gapbs-bfs (its record's `kernel`).
    assert {(r["contract"], r["slug"], r["record_id"]) for r in kernels} == {
        (contract, "gapbs-bfs", record) for contract, _, record in expected}


def legality_facts(records, implementation="dx100-bfs-scalar"):
    """(contract, clause, statement index, record field) of each `legality:` fact the
    implementation's statements carry, read from its record."""
    statements = records.read(f"implementations/{implementation}.yaml")["extensions"]["statements"]
    facts = []
    for i, annotation in enumerate(statements["annotations"]):
        for j, fact in enumerate(annotation.get("annotation_facts") or []):
            prefix, contract, clause = fact["field"].split(":")
            assert prefix == "legality"
            facts.append((contract, clause, i, f"extensions.statements.annotations[{i}].annotation_facts[{j}]"))
    return facts


def test_a_clause_tied_to_a_statement_links_to_the_statements_function(built):
    facts = legality_facts(built)
    assert {(contract, clause) for contract, clause, _, _ in facts} == {
        ("contract.bfs_read_offload", clause)
        for clause in ("L1", "L2", "L3", "L4", "L5", "frontier_threshold", "chunk_size", "schedule")}
    # The matching definition: TDStep, the row dx100-bfs-scalar's `extensions.statements.function` produced.
    [tdstep] = sql(built, "select d.id from definitions d join swdb_row_origins o on o.table_name = 'definitions' "
                          "and o.row_id = d.id where o.record_id = 'dx100-bfs-scalar' "
                          "and o.record_field = 'extensions.statements.function' and d.name = 'TDStep'")
    rows = sql(built, "select contract, definition_id, clause, record_id, record_field from swdb_contract_definitions")
    assert sorted((r["contract"], r["clause"], r["record_field"]) for r in rows) == sorted(
        (contract, clause, field) for contract, clause, _, field in facts)
    assert {(r["definition_id"], r["record_id"]) for r in rows} == {(tdstep["id"], "dx100-bfs-scalar")}


def test_a_clause_tied_to_a_statement_links_to_the_arrays_of_the_steps_that_statement_names(built):
    # bfs-td-frontier (L5, frontier_threshold, chunk_size, schedule) names td-frontier-read step 0,
    # queue.shared; bfs-td-row-bounds (L1) names step 1 of two patterns, VertexOffsets both times;
    # bfs-td-parent-read (L2, L3, L4) names td-parent-read step 3, parent.
    expected = {"L5": "queue.shared", "frontier_threshold": "queue.shared", "chunk_size": "queue.shared",
                "schedule": "queue.shared", "L1": "VertexOffsets", "L2": "parent", "L3": "parent", "L4": "parent"}
    rows = sql(built, "select l.contract, l.clause, d.name, k.slug as kernel, l.record_id from swdb_contract_data_structures l "
                      "join data_structures d on d.id = l.data_structure_id join kernels k on k.id = d.kernel_id")
    assert sorted((r["clause"], r["name"]) for r in rows) == sorted(expected.items())
    assert {(r["contract"], r["kernel"], r["record_id"]) for r in rows} == {
        ("contract.bfs_read_offload", "gapbs-bfs", "dx100-bfs-scalar")}


def test_a_clause_tied_to_a_statement_links_to_its_implementation_and_kernel(built):
    facts = legality_facts(built)
    for table, join in (("swdb_contract_kernel_variants", "kernel_variants t on t.id = l.kernel_variant_id"),
                        ("swdb_contract_kernels", "kernels t on t.id = l.kernel_id")):
        rows = sql(built, f"select l.contract, l.clause, t.slug, l.record_field from {table} l join {join} "
                          f"where l.record_id = 'dx100-bfs-scalar'")
        slug = "dx100-bfs-scalar" if table == "swdb_contract_kernel_variants" else "gapbs-bfs"
        assert sorted((r["contract"], r["clause"], r["slug"], r["record_field"]) for r in rows) == sorted(
            (contract, clause, slug, field) for contract, clause, _, field in facts), table


def linked_contracts(records):
    return {row["contract"] for table in LINKS for row in sql(records, f"select distinct contract from {table}")}


def test_a_contract_with_no_stated_link_has_no_link_rows(built):
    # contract.bc_read_offload is in the library, but no record in this closure ties it to code;
    # lowerings, intrinsics and library operations are not contracts and never link.
    entries = {r["id"]: r["kind"] for r in sql(built, "select id, kind from swdb_library_entries")}
    assert entries["contract.bc_read_offload"] == "rewrite_contract"
    assert linked_contracts(built) == {"contract.bfs_read_offload", "contract.bfs_tdstep_frontier_staging"}


def test_without_the_library_no_contract_is_linked(tmp_path):
    # The same records with no library beside them: the contracts they name have no entry row,
    # so no link is made and the build still passes the foreign-key check.
    records = make_records(tmp_path).copy_closure(*CERTIFICATIONS)
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr
    assert linked_contracts(records) == set()
    assert_foreign_keys_clean(records)


def test_every_record_field_names_a_field_of_its_record(built):
    assert_record_fields_resolve(built)


def test_a_build_passes_the_foreign_key_check(built):
    assert_foreign_keys_clean(built)


def test_deleting_every_swdb_table_leaves_a_consistent_lanl_database(built, tmp_path):
    assert_separable(built, tmp_path)
