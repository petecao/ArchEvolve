"""Shared checks for the LANL-shaped database (LANL-shaped-db spec). Created 2026-10-11 ET.
Updated 2026-10-11 ET (review fixes): `assert_record_fields_resolve` checks every origin's
`record_field` against the stored record.

The expected shape is transcribed from the spec's appendix (the `DB_current_work` slide) and
its layout rules, independently of the builder. Every LANL table group's test calls the same
helpers with its own table names:

    assert_lanl_shape(records, "source_files", "executables")
    assert_guessed_listed(records, "source_files")
    assert_origins(records, "source_files")
    assert_record_fields_resolve(records)
    assert_foreign_keys_clean(records)
    assert_separable(records, tmp_path)

`records` is a `conftest.make_records` folder that has been built (`records.swdb("build")`).
All reads go through `swdb sql`; only the separability check opens a copy of the file directly,
because `swdb sql` is read-only.
"""

import json
import re
import shutil
import sqlite3

#: Every LANL table (15 slide tables + the guessed `kernel_variants`): `id`, the slide's columns,
#: and the guessed link columns of the spec's layout rules. Slide capitalization is kept
#: (`Validation_definition`, `Validation_results`).
LANL_COLUMNS = {
    "kernels": {"id", "slug", "name", "category"},
    "kernel_variants": {"id", "kernel_id", "slug"},
    "source_files": {"id", "kernel_id", "path", "language"},
    "executables": {"id", "kernel_id", "name", "kind", "path"},
    "definitions": {"id", "source_file_id", "name", "kind"},
    "data_structures": {"id", "kernel_id", "name", "kind"},
    "hardware_profiles": {"id", "cpu_model", "cores", "memory_gb"},
    "run_configs": {"id", "label", "parameters_json", "git_commit", "kernel_variant_id"},
    "performance_runs": {"id", "elapsed_seconds", "throughput_value", "hardware_profile_id", "run_config_id",
                         "kernel_variant_id"},
    "performance_metrics": {"id", "metric_name", "metric_value", "performance_run_id"},
    "Validation_definition": {"id", "kernel_id", "name", "input_json", "expected_output_json"},
    "Validation_results": {"id", "fixture_id", "kernel_variant_id", "passed", "max_abs_error"},
    "physics_assets": {"id", "kernel_id", "asset_type", "name", "format"},
    "kernel_dependencies": {"id", "kernel_id", "depends_on_kernel_id", "dependency_type"},
    "code_chunks": {"id", "source_file_id", "line_start", "line_end", "content"},
    "embeddings": {"id", "code_chunk_id", "vector"},
}

#: Columns the slide does not show, which `swdb_guessed_columns` must list (spec D3 and layout
#: rules). `kernel_variants` is a guessed table, so all of its columns are listed.
GUESSED_COLUMNS = {
    "kernel_variants": {"id", "kernel_id", "slug"},
    "run_configs": {"kernel_variant_id"},
    "performance_runs": {"hardware_profile_id", "run_config_id", "kernel_variant_id"},
    "performance_metrics": {"performance_run_id"},
    "Validation_results": {"fixture_id"},
    "code_chunks": {"id", "source_file_id", "line_start", "line_end", "content"},
    "embeddings": {"id", "code_chunk_id", "vector"},
}


def database(records):
    """The database file `records.swdb(...)` builds and reads."""
    return records.path.parent / "build" / "swdb.sqlite"


def sql(records, query):
    """Rows of one query through `swdb sql`, as dicts."""
    result = records.swdb("sql", query, "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def columns(records, table):
    return {row["name"] for row in sql(records, f"select name from pragma_table_info('{table}')")}


def assert_lanl_shape(records, *tables):
    """Each named LANL table exists with exactly the expected columns."""
    for table in tables:
        assert columns(records, table) == LANL_COLUMNS[table], table


def assert_guessed_listed(records, *tables):
    """`swdb_guessed_columns` lists exactly the guessed columns of each named table, with a reason."""
    rows = sql(records, "select table_name, column_name, reason from swdb_guessed_columns")
    for table in tables:
        listed = {row["column_name"] for row in rows if row["table_name"] == table}
        assert listed == GUESSED_COLUMNS.get(table, set()), table
    assert all(row["reason"] for row in rows)


def assert_origins(records, *tables):
    """Every row of each named table has an origin naming an existing record, and every origin
    of that table names an existing row."""
    for table in tables:
        missing = sql(records, f'select t.id from "{table}" t where not exists (select 1 from swdb_row_origins o '
                               f"join swdb_records r on r.id = o.record_id "
                               f"where o.table_name = '{table}' and o.row_id = t.id)")
        assert missing == [], f"{table} rows without an origin: {missing[:5]}"
        dangling = sql(records, f"select row_id from swdb_row_origins o where table_name = '{table}' "
                                f'and not exists (select 1 from "{table}" t where t.id = o.row_id)')
        assert dangling == [], f"{table} origins without a row: {dangling[:5]}"


#: One step of a `record_field` path: a key, then any number of `[<index>]`.
_STEP = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)((?:\[\d+\])*)")


def resolve(data, path):
    """The value at `path` in a record's JSON, for the one path syntax every LANL group uses:
    dotted keys with bracketed list indexes (`code[0]`, `parts[0].outcome`,
    `access_patterns[1].steps[2].array`). Raises KeyError if `path` does not name a field."""
    value = data
    for step in path.split("."):
        match = _STEP.fullmatch(step)
        if match is None:
            raise KeyError(f"{path!r}: {step!r} is not `key` or `key[<index>]`")
        if not isinstance(value, dict) or match[1] not in value:
            raise KeyError(f"{path!r}: no key {match[1]!r}")
        value = value[match[1]]
        for index in map(int, re.findall(r"\d+", match[2])):
            if not isinstance(value, list) or index >= len(value):
                raise KeyError(f"{path!r}: no index [{index}] under {match[1]!r}")
            value = value[index]
    return value


def assert_record_fields_resolve(records):
    """Every `record_field` of `swdb_row_origins` and of the contract link tables names a field of
    the record JSON stored in `swdb_records`, in the one syntax `resolve` reads."""
    tables = [row["name"] for row in sql(records, "select name from sqlite_master where type = 'table' "
                                                  "and (name = 'swdb_row_origins' or name like 'swdb_contract_%')")]
    fields = {(row["record_id"], row["record_field"]) for table in tables
              for row in sql(records, f"select distinct record_id, record_field from {table}")}
    assert fields, "no record fields to check"
    ids = sorted({record_id for record_id, _ in fields})
    stored = {row["id"]: json.loads(row["json"]) for row in sql(
        records, f"select id, json from swdb_records where id in ({', '.join(repr(i) for i in ids)})")}
    unresolved = []
    for record_id, field in sorted(fields):
        try:
            resolve(stored[record_id], field)
        except KeyError as error:
            unresolved.append((record_id, str(error)))
    assert unresolved == [], f"{len(unresolved)} record fields do not resolve: {unresolved[:5]}"


def assert_foreign_keys_clean(records):
    assert sql(records, "pragma foreign_key_check") == []


def assert_separable(records, scratch):
    """After deleting every `swdb_` table from a copy, the LANL tables remain and
    `PRAGMA foreign_key_check` is clean."""
    copy = scratch / "lanl-only.sqlite"
    shutil.copyfile(database(records), copy)
    con = sqlite3.connect(copy)
    try:
        for (table,) in con.execute("select name from sqlite_master where type = 'table' and name like 'swdb\\_%' "
                                    "escape '\\'").fetchall():
            con.execute(f'DROP TABLE "{table}"')
        con.commit()
        left = {name for (name,) in con.execute("select name from sqlite_master where type = 'table'")}
        assert left and not any(name.startswith("swdb_") for name in left)
        assert left <= set(LANL_COLUMNS), left - set(LANL_COLUMNS)
        assert con.execute("pragma foreign_key_check").fetchall() == []
    finally:
        con.close()
