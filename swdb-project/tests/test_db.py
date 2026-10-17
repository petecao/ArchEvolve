"""`swdb build`, `sql`, `find`, and `implementations` (ADR 0002). Updated 2026-10-11 ET: tables carry
the `swdb_` prefix (LANL-shaped-db ticket 01); the fixture copies the record closure, not the
~1 GB catalog (LR-03, Yan-Ru's ticket 01 decision). LANL tables: tests/test_lanl_*.py."""

import json
import re
import subprocess

import pytest

from conftest import REPO


@pytest.fixture
def repo(records):
    return records.copy_closure()


def out(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_build_regenerates_quickly(repo):
    result = repo.swdb("build")
    assert result.returncode == 0, result.stderr
    seconds = float(re.search(r"in ([0-9.]+) s", result.stdout).group(1))
    assert seconds < 2.0
    assert (repo.path.parent / "build" / "swdb.sqlite").is_file()


def test_database_file_is_ignored_by_git():
    done = subprocess.run(["git", "check-ignore", "-q", "build/swdb.sqlite"], cwd=REPO)
    assert done.returncode == 0


def test_build_starts_from_scratch(repo):
    data = repo.read("inputs/kron-g16-k16.yaml")
    data["id"] = "extra-input"
    repo.write("inputs/extra.yaml", data)
    repo.swdb("build")
    assert any(r["id"] == "extra-input" for r in out(repo.swdb("sql", "select id from swdb_inputs", "--format", "json")))
    (repo.path / "inputs" / "extra.yaml").unlink()
    assert repo.swdb("build").returncode == 0
    ids = [r["id"] for r in out(repo.swdb("sql", "select id from swdb_inputs", "--format", "json"))]
    assert "extra-input" not in ids


def test_build_refuses_invalid_records(repo):
    data = repo.read("kernels/gapbs-pr.yaml")
    data["application"] = "nope"
    repo.write("kernels/gapbs-pr.yaml", data)
    result = repo.swdb("build")
    assert result.returncode == 1 and "does not exist" in result.stderr


def test_find_by_address_shape(repo):
    found = out(repo.swdb("find", "--shape", "ranged_indirect", "--kernel", "gapbs-pr", "--format", "json"))
    # 2026-10-11 ET: gapbs-pr-jacobi-analytic-v1 is a gapbs-pr variant since 728fea38 (2026-10-06)
    assert {(f["implementation"], f["pattern"]) for f in found} == {
        ("gapbs-pr-gs", "gather-contrib"), ("gapbs-pr-jacobi", "gather-contrib"),
        ("gapbs-pr-jacobi-analytic-v1", "gather-contrib")}


def test_find_by_update_kind_and_semantic_value(repo):
    found = out(repo.swdb("find", "--update", "write", "--semantic", "loop_carried_dependencies=true",
                          "--kernel", "gapbs-pr", "--format", "json"))
    assert [(f["implementation"], f["pattern"]) for f in found] == [("gapbs-pr-gs", "contrib-update")]


def test_find_yaml_output(repo):
    result = repo.swdb("find", "--shape", "single_valued_indirect")
    assert result.returncode == 0 and "pattern_class:" in result.stdout


def test_find_with_unknown_semantic_field_is_a_usage_error(repo):
    assert repo.swdb("find", "--semantic", "colour=red").returncode == 2


def test_implementations_meeting_a_requirement(repo):
    found = out(repo.swdb("implementations", "gapbs-pr", "--require", "loop_carried_dependencies=false",
                          "--format", "json"))
    # 2026-10-11 ET: gapbs-pr-jacobi-analytic-v1 is a gapbs-pr variant since 728fea38 (2026-10-06)
    assert [f["implementation"] for f in found] == ["gapbs-pr-jacobi", "gapbs-pr-jacobi-analytic-v1"]


def test_implementations_without_requirements(repo):
    found = out(repo.swdb("implementations", "gapbs-pr", "--format", "json"))
    # 2026-10-11 ET: gapbs-pr-jacobi-analytic-v1 is a gapbs-pr variant since 728fea38 (2026-10-06)
    assert [f["implementation"] for f in found] == ["gapbs-pr-gs", "gapbs-pr-jacobi", "gapbs-pr-jacobi-analytic-v1"]
    assert found[0]["baseline"] is True


def test_unknown_never_meets_a_requirement(records):
    records.add_stub()   # stub-impl's loop_carried_dependencies is unknown
    for value in ("true", "false"):
        found = out(records.swdb("implementations", "stub-kernel", "--require", f"loop_carried_dependencies={value}",
                                 "--format", "json"))
        assert found == []


def test_implementations_of_missing_kernel_fails(repo):
    result = repo.swdb("implementations", "no-such-kernel")
    assert result.returncode == 1 and "does not exist" in result.stderr


def test_sql_runs_own_queries(repo):
    rows = out(repo.swdb("sql", "select pattern, address_shape from swdb_steps where implementation = 'gapbs-pr-gs' "
                                "and pattern = 'gather-contrib' order by position", "--format", "json"))
    assert [r["address_shape"] for r in rows] == ["stream", "ranged_indirect", "single_valued_indirect"]


def test_bad_sql_fails(repo):
    result = repo.swdb("sql", "select nothing from nowhere")
    assert result.returncode == 1 and "SQL error" in result.stderr


def test_queries_rebuild_a_stale_database(repo):
    repo.swdb("build")
    data = repo.read("inputs/kron-g16-k16.yaml")
    data["id"], data["name"] = "kron-g16-k16-copy", "copy"
    repo.write("inputs/copy.yaml", data)
    rows = out(repo.swdb("sql", "select id from swdb_inputs where id = 'kron-g16-k16-copy'", "--format", "json"))
    assert rows == [{"id": "kron-g16-k16-copy"}]


def test_every_table_and_column_is_documented(repo):
    repo.swdb("build")
    tables = out(repo.swdb("sql", "select name from sqlite_master where type = 'table'", "--format", "json"))
    doc = (REPO / "docs" / "reference" / "database.md").read_text()
    for table in (t["name"] for t in tables):
        assert f"`{table}`" in doc, f"table {table} is not documented"
        columns = out(repo.swdb("sql", f"select name from pragma_table_info('{table}')", "--format", "json"))
        for column in (c["name"] for c in columns):
            assert f"`{column}`" in doc, f"column {table}.{column} is not documented"


#: The tables before LANL-shaped-db ticket 01 (2026-10-11 ET), which renamed each to swdb_<name>.
UNPREFIXED = {
    "meta", "records", "applications", "kernels", "implementations", "implementation_contexts", "inputs",
    "input_properties", "machines", "machine_flags", "profiles", "metrics", "access_patterns", "steps",
    "intrinsics", "intrinsic_extensions", "strategies", "strategy_effects", "strategy_intrinsics",
    "applied_strategies", "implementation_intrinsics", "library_entries", "library_dependencies",
    "library_clauses", "statements", "statement_steps", "statement_facts", "library_pattern_keys",
    "library_pattern_key_steps"}


def table_names(repo):
    return {t["name"] for t in out(repo.swdb("sql", "select name from sqlite_master where type = 'table'",
                                             "--format", "json"))}


def test_a_fresh_build_names_every_table_with_the_swdb_prefix(repo):
    # 2026-10-11 ET (ticket 02): the LANL core tables are the only unprefixed ones
    from testkit.lanl import LANL_COLUMNS

    assert repo.swdb("build").returncode == 0
    tables = table_names(repo)
    assert {f"swdb_{name}" for name in UNPREFIXED} <= tables
    assert sorted(t for t in tables if not t.startswith("swdb_") and t not in LANL_COLUMNS) == []


def test_a_database_file_from_before_the_swdb_prefix_is_rebuilt(repo):
    import sqlite3

    assert repo.swdb("build").returncode == 0
    # turn the fresh file into the old layout: same stamps in meta, tables without the prefix
    # (and, since ticket 02, without the LANL tables, whose names the old tables used)
    con = sqlite3.connect(repo.path.parent / "build" / "swdb.sqlite")
    for table in [r[0] for r in con.execute("select name from sqlite_master where type = 'table' order by rowid desc")]:
        if not table.startswith("swdb_") or table.removeprefix("swdb_") not in UNPREFIXED:
            con.execute(f'DROP TABLE "{table}"')
    for table in [r[0] for r in con.execute("select name from sqlite_master where type = 'table'")]:
        con.execute(f'ALTER TABLE "{table}" RENAME TO "{table.removeprefix("swdb_")}"')
    con.commit()
    con.close()
    result = repo.swdb("sql", "select id from swdb_applications order by id", "--format", "json")
    assert "built by another swdb version" in result.stderr
    assert out(result) == [{"id": "dx100-gapbs"}, {"id": "gapbs"}]


def test_sibling_records_folders_never_share_results(tmp_path):
    # the review's reproduction: query folder a, then folder b; b must answer with b's records
    from conftest import run_swdb, REPO
    import shutil

    for name in ("a", "b"):
        destination = tmp_path / name / "applications"
        destination.mkdir(parents=True)
        shutil.copy(REPO / "records" / "applications" / "gapbs.yaml", destination / "gapbs.yaml")
    b_app = tmp_path / "b" / "applications" / "gapbs.yaml"
    b_app.write_text(b_app.read_text().replace("id: gapbs", "id: gapbs-b"))
    first = out(run_swdb("sql", "select id from swdb_applications", "--records", tmp_path / "a", "--format", "json"))
    second = out(run_swdb("sql", "select id from swdb_applications", "--records", tmp_path / "b", "--format", "json"))
    assert first == [{"id": "gapbs"}] and second == [{"id": "gapbs-b"}]
    # the same file, forced for both folders, is rebuilt for whichever folder asks
    shared = tmp_path / "shared.sqlite"
    assert out(run_swdb("sql", "select id from swdb_applications", "--records", tmp_path / "a", "--db", shared,
                        "--format", "json")) == [{"id": "gapbs"}]
    assert out(run_swdb("sql", "select id from swdb_applications", "--records", tmp_path / "b", "--db", shared,
                        "--format", "json")) == [{"id": "gapbs-b"}]


def test_a_changed_record_is_seen_even_with_an_older_timestamp(repo):
    repo.swdb("build")
    path = repo.path / "inputs" / "kron-g16-k16.yaml"
    before = path.stat()
    path.write_text(path.read_text().replace("name: ", "name: Renamed ", 1))
    import os
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns - 10**9))   # pretend it is older
    rows = out(repo.swdb("sql", "select name from swdb_inputs where id = 'kron-g16-k16'", "--format", "json"))
    assert rows[0]["name"].startswith("Renamed")


def test_unknown_counter_availability_stays_null(repo):
    # 2026-09-27 ET: frozen native protocols, and the comparisons that reference
    # them, bind the exact mbit10 record digest. Editing mbit10 in place would
    # invalidate that retained chain, so the unknown case is a separate synthetic
    # machine record; the real mbit10 record and its dependents stay unchanged.
    data = repo.read("machines/mbit10.yaml")
    data["id"] = "unknown-counters-probe"
    data["hostname"] = "unknown-counters-probe"
    data["counters"]["hardware_counters_available"] = {"value": None, "basis": "unknown", "evidence_refs": []}
    repo.write("machines/unknown-counters-probe.yaml", data)
    rows = out(repo.swdb("sql", "select id, counters_available from swdb_machines "
                         "where id in ('mbit10', 'unknown-counters-probe') order by id", "--format", "json"))
    assert rows == [{"id": "mbit10", "counters_available": 0},
                    {"id": "unknown-counters-probe", "counters_available": None}]


def test_known_counter_availability_is_zero_or_one(repo):
    rows = out(repo.swdb("sql", "select counters_available from swdb_machines where id = 'mbit10'", "--format", "json"))
    assert rows == [{"counters_available": 0}]
