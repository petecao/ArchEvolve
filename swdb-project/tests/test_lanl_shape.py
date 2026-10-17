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

    # 15 slide tables (the appendix lists 5 + 6 + 2 + 2) + the guessed kernel_variants.
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


def test_add_once_inserts_one_row_per_key_and_an_origin_per_call():
    # `Rows.add_once` is the one way a LANL group stores a row several records name.
    import sqlite3

    from swdb import lanl

    con = sqlite3.connect(":memory:")
    con.executescript(lanl.SCHEMA)
    con.execute("CREATE TABLE things (id INTEGER PRIMARY KEY, name TEXT)")
    rows = lanl.Rows(con)
    first = rows.add_once("things", ("a",), {"name": "a"}, "rec-1", "code[0]")
    again = rows.add_once("things", ("a",), {"name": "a"}, "rec-2", "code[3]")
    other = rows.add_once("things", ("b",), {"name": "b"}, "rec-1", "code[1]")
    assert first == again != other
    assert con.execute("SELECT id, name FROM things ORDER BY id").fetchall() == [(first, "a"), (other, "b")]
    assert sorted(con.execute("SELECT row_id, record_id, record_field FROM swdb_row_origins")) == sorted([
        (first, "rec-1", "code[0]"), (first, "rec-2", "code[3]"), (other, "rec-1", "code[1]")])
