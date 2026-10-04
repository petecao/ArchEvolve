"""Typed-library JSON schema, SQLite tables and staleness. Created: 2026-10-03 ET (ticket 46)."""

import json
import os
import shutil
import time

import pytest

from conftest import REPO

from swdb import db
from swdb.library import Library, entry_validator
from swdb.store import Store


def out(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.fixture
def repo(records):
    """A records copy with the repository library beside it, as `default_root` expects."""
    records.copy_repo()
    shutil.copytree(REPO / "library", records.path.parent / "library")
    return records


def _sql(records, query):
    return out(records.swdb("sql", query, "--format", "json"))


def test_every_repository_library_entry_matches_the_schema():
    library = Library(REPO / "library", Store(REPO / "records"))
    assert library.validate() == []
    validator = entry_validator()
    assert library.entries and all(not list(validator.iter_errors(data)) for data in library.entries.values())


@pytest.mark.parametrize("change, field", [
    (lambda d: d.update(clauses={"id": "L1"}), "clauses"),
    (lambda d: d["pattern_key"][0].update(roles=["frontier"]), "pattern_key.0.roles.0"),
    (lambda d: d.update(uses_intrinsics=[""]), "uses_intrinsics.0"),
])
def test_schema_shape_errors_are_reported_by_field(tmp_path, change, field):
    root = tmp_path / "library"
    shutil.copytree(REPO / "library", root)
    from swdb import yamlio
    path = root / "rewrite_contracts/bfs_read_offload.yaml"
    data = yamlio.load(path)
    change(data)
    path.write_text(yamlio.dumps(data))
    problems = Library(root, Store(REPO / "records")).validate()
    assert any(problem.field == field for problem in problems), problems


def test_library_entries_clauses_and_dependencies_are_indexed(repo):
    rows = _sql(repo, "select id, kind, tier, status, derived_from from library_entries order by id")
    yaml_files = list((repo.path.parent / "library").rglob("*.yaml"))
    assert len(rows) == len(yaml_files) - 0 and len(rows) > 20
    contract = next(row for row in rows if row["id"] == "contract.bc_read_offload")
    assert contract["kind"] == "rewrite_contract" and contract["derived_from"] == "contract.bfs_read_offload"
    assert contract["tier"] == "experimental"
    parent = next(row for row in rows if row["id"] == "contract.bfs_read_offload")
    assert parent["tier"] == "shared" and parent["status"] == "evaluated_on_target"
    dependencies = {row["dependency"] for row in _sql(
        repo, "select dependency from library_dependencies where entry = 'contract.bc_read_offload'")}
    assert "contract.bfs_read_offload" in dependencies and "intrinsic.dxc_gather" in dependencies
    clause = _sql(repo, "select role, discharge_mode, negative_control from library_clauses "
                        "where entry = 'contract.bc_read_offload' and clause = 'BC-L1'")
    assert clause == [{"role": "legality", "discharge_mode": "differential_test", "negative_control": "stale_depth_hint"}]
    library = Library(repo.path.parent / "library", Store(repo.path))
    hashes = {row["id"]: row["content_sha256"] for row in _sql(repo, "select id, content_sha256 from library_entries")}
    assert hashes == {entry_id: library.content_sha256(entry_id) for entry_id in library.entries}


def test_statements_index_covers_statement_annotations(repo):
    rows = _sql(repo, "select statement, function, path, first_line, last_line, code, agent_claims from statements "
                      "where implementation = 'dx100-bfs-scalar' order by first_line")
    implementation = repo.read("implementations/dx100-bfs-scalar.yaml")
    annotations = implementation["extensions"]["statements"]["annotations"]
    assert len(rows) == len(annotations) == 7
    assert {row["statement"] for row in rows} == {row["id"] for row in annotations}
    assert all(row["function"] == "TDStep" and row["path"] == "benchmarks/gapbs/src/bfs.cc" for row in rows)
    first = next(a for a in annotations if a["id"] == "bfs-td-frontier")
    row = next(r for r in rows if r["statement"] == "bfs-td-frontier")
    assert row["code"] == first["code"] and row["agent_claims"] == len(first["agent_claims"])
    steps = _sql(repo, "select pattern, step from statement_steps where statement = 'bfs-td-frontier'")
    assert steps == [{"pattern": step["pattern"], "step": step["step"]} for step in first["access_pattern_steps"]]


def test_library_changes_make_the_index_stale_and_queries_rebuild(repo):
    database = repo.path.parent / "build" / "swdb.sqlite"
    assert repo.swdb("build").returncode == 0
    assert not db.is_stale(repo.path, database)
    meta = {row["key"]: row["value"] for row in _sql(repo, "select key, value from meta")}
    assert meta["library_dir"] == str((repo.path.parent / "library").resolve())
    entry = repo.path.parent / "library/rewrite_contracts/bc_read_offload.yaml"
    entry.write_text(entry.read_text().replace("experimental until Yan-Ru reviews it", "experimental until reviewed"))
    assert db.is_stale(repo.path, database)
    _sql(repo, "select count(*) from library_entries")  # any query refreshes the stale index
    assert not db.is_stale(repo.path, database)
    # Pinned code outside the YAML counts too, and so does a new file.
    code = repo.path.parent / "library/dx100/bc_read_offload.inc"
    stamp = code.stat()
    os.utime(code, ns=(stamp.st_atime_ns, stamp.st_mtime_ns + 10**9))
    assert db.is_stale(repo.path, database)
    repo.swdb("build")
    (repo.path.parent / "library/dx100/notes.txt").write_text("new file\n")
    assert db.is_stale(repo.path, database)


def test_records_without_a_library_index_no_library_rows(records):
    records.copy_repo("applications")
    assert _sql(records, "select count(*) as n from library_entries") == [{"n": 0}]
    assert _sql(records, "select count(*) as n from statements") == [{"n": 0}]
