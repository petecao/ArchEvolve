"""`swdb build`, `sql`, `find`, and `implementations` (ADR 0002). Created 2026-09-22."""

import json
import re
import subprocess

import pytest

from conftest import REPO


@pytest.fixture
def repo(records):
    return records.copy_repo()


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
    repo.swdb("build")
    assert any(r["id"] == "kron-g22-k16" for r in out(repo.swdb("sql", "select id from inputs", "--format", "json")))
    (repo.path / "inputs" / "kron-g22-k16.yaml").unlink()
    assert repo.swdb("build").returncode == 0
    ids = [r["id"] for r in out(repo.swdb("sql", "select id from inputs", "--format", "json"))]
    assert "kron-g22-k16" not in ids


def test_build_refuses_invalid_records(repo):
    data = repo.read("kernels/gapbs-pr.yaml")
    data["application"] = "nope"
    repo.write("kernels/gapbs-pr.yaml", data)
    result = repo.swdb("build")
    assert result.returncode == 1 and "does not exist" in result.stderr


def test_find_by_address_shape(repo):
    found = out(repo.swdb("find", "--shape", "ranged_indirect", "--format", "json"))
    assert {(f["implementation"], f["pattern"]) for f in found} == {
        ("gapbs-pr-gs", "gather-contrib"), ("gapbs-pr-jacobi", "gather-contrib")}


def test_find_by_update_kind_and_semantic_value(repo):
    found = out(repo.swdb("find", "--update", "write", "--semantic", "loop_carried_dependencies=true",
                          "--format", "json"))
    assert [(f["implementation"], f["pattern"]) for f in found] == [("gapbs-pr-gs", "contrib-update")]


def test_find_yaml_output(repo):
    result = repo.swdb("find", "--shape", "single_valued_indirect")
    assert result.returncode == 0 and "pattern_class:" in result.stdout


def test_find_with_unknown_semantic_field_is_a_usage_error(repo):
    assert repo.swdb("find", "--semantic", "colour=red").returncode == 2


def test_implementations_meeting_a_requirement(repo):
    found = out(repo.swdb("implementations", "gapbs-pr", "--require", "loop_carried_dependencies=false",
                          "--format", "json"))
    assert [f["implementation"] for f in found] == ["gapbs-pr-jacobi"]


def test_implementations_without_requirements(repo):
    found = out(repo.swdb("implementations", "gapbs-pr", "--format", "json"))
    assert [f["implementation"] for f in found] == ["gapbs-pr-gs", "gapbs-pr-jacobi"]
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
    rows = out(repo.swdb("sql", "select pattern, address_shape from steps where implementation = 'gapbs-pr-gs' "
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
    rows = out(repo.swdb("sql", "select id from inputs where id = 'kron-g16-k16-copy'", "--format", "json"))
    assert rows == [{"id": "kron-g16-k16-copy"}]


def test_every_table_and_column_is_documented(repo):
    repo.swdb("build")
    tables = out(repo.swdb("sql", "select name from sqlite_master where type = 'table'", "--format", "json"))
    doc = (REPO / "docs" / "database.md").read_text()
    for table in (t["name"] for t in tables):
        assert f"`{table}`" in doc, f"table {table} is not documented"
        columns = out(repo.swdb("sql", f"select name from pragma_table_info('{table}')", "--format", "json"))
        for column in (c["name"] for c in columns):
            assert f"`{column}`" in doc, f"column {table}.{column} is not documented"
