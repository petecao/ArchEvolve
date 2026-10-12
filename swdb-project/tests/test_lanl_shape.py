"""The whole LANL core in one place (LANL-shaped-db ticket 07). Created 2026-10-11 ET.

The per-group tests (tests/test_lanl_*.py) each check their own tables. This one checks all 15
slide tables plus the guessed `kernel_variants` together, so a table that goes missing or gains,
loses or renames a column fails here whichever group built it. The expected shape is
`testkit.lanl`, transcribed from the spec's appendix, not from the builder.

Built from the smallest record closure (LR-03), never the ~1 GB catalog."""

from conftest import make_records
from testkit.lanl import GUESSED_COLUMNS, LANL_COLUMNS, columns, sql


def test_the_lanl_core_is_exactly_the_slide_tables_and_kernel_variants_with_their_columns(tmp_path):
    records = make_records(tmp_path).copy_closure()
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr

    # The slide's appendix lists 15 tables (5 + 6 + 2 + 2); the spec's "16 slide tables" counts
    # the guessed kernel_variants with them.
    assert len(LANL_COLUMNS) == 16 and "kernel_variants" in LANL_COLUMNS
    tables = {row["name"] for row in sql(records, "select name from sqlite_master where type = 'table'")}
    assert {table for table in tables if not table.startswith("swdb_")} == set(LANL_COLUMNS)
    wrong = {table: columns(records, table) for table in LANL_COLUMNS
             if columns(records, table) != LANL_COLUMNS[table]}
    assert wrong == {}, {table: (sorted(got), sorted(LANL_COLUMNS[table])) for table, got in wrong.items()}

    listed = {}
    for row in sql(records, "select table_name, column_name from swdb_guessed_columns"):
        listed.setdefault(row["table_name"], set()).add(row["column_name"])
    assert listed == GUESSED_COLUMNS
