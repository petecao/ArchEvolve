"""`swdb add`: validate, write to the canonical place, rebuild. Created 2026-09-22."""

import json

import pytest
import yaml


@pytest.fixture
def repo(records):
    return records.copy_repo()


def new_input(repo, tmp_path, **changes):
    data = repo.read("inputs/kron-g16-k16.yaml")
    data.update(id="kron-g18-k16", name="Kronecker scale 18")
    data["generator"]["arguments"] = "-g 18 -k 16"
    data["properties"]["num_nodes"]["value"] = 2 ** 18
    data["properties"]["scale"]["value"] = 18
    data.update(changes)
    path = tmp_path / "new.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path, data


def test_add_writes_the_canonical_file_and_the_next_queries_see_it(repo, tmp_path):
    path, _ = new_input(repo, tmp_path)
    result = repo.swdb("add", path)
    assert result.returncode == 0, result.stderr
    assert (repo.path / "inputs" / "kron-g18-k16.yaml").is_file()
    assert repo.validate().returncode == 0
    assert repo.swdb("build").returncode == 0
    rows = json.loads(repo.swdb("sql", "select id from inputs where id = 'kron-g18-k16'", "--format", "json").stdout)
    assert rows == [{"id": "kron-g18-k16"}]
    view = repo.swdb("view", "gapbs-pr-gs", "kron-g18-k16", "mbit10")
    assert view.returncode == 0 and "gapbs-pr-gs@kron-g18-k16@mbit10" in view.stdout


def test_added_implementation_shows_up_in_implementations(repo, tmp_path):
    data = repo.read("implementations/gapbs-pr-jacobi.yaml")
    data["id"] = "gapbs-pr-jacobi-copy"
    path = tmp_path / "impl.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    assert repo.swdb("add", path).returncode == 0
    found = json.loads(repo.swdb("implementations", "gapbs-pr", "--require", "loop_carried_dependencies=false",
                                 "--format", "json").stdout)
    assert [f["implementation"] for f in found] == ["gapbs-pr-jacobi", "gapbs-pr-jacobi-copy"]
    assert (repo.path / "implementations" / "gapbs-pr-jacobi-copy.yaml").is_file()


def test_invalid_record_is_rejected_and_nothing_is_written(repo, tmp_path):
    path, _ = new_input(repo, tmp_path, colour="red")
    result = repo.swdb("add", path)
    assert result.returncode == 1 and "unknown key" in result.stderr and "nothing written" in result.stderr
    assert not (repo.path / "inputs" / "kron-g18-k16.yaml").exists()


def test_duplicate_id_is_rejected_and_nothing_is_written(repo, tmp_path):
    path, _ = new_input(repo, tmp_path, id="kron-g16-k16")
    before = (repo.path / "inputs" / "kron-g16-k16.yaml").read_text()
    result = repo.swdb("add", path)
    assert result.returncode == 1 and "already used" in result.stderr
    assert (repo.path / "inputs" / "kron-g16-k16.yaml").read_text() == before


def test_record_that_breaks_a_cross_record_rule_is_rejected(repo, tmp_path):
    data = repo.read("implementations/gapbs-pr-jacobi.yaml")
    data["id"], data["kernel"] = "orphan", "no-such-kernel"
    path = tmp_path / "orphan.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    result = repo.swdb("add", path)
    assert result.returncode == 1 and "does not exist" in result.stderr
    assert not (repo.path / "implementations" / "orphan.yaml").exists()


def test_agent_records_are_draft_with_an_agent_run_entry(repo, tmp_path):
    path, _ = new_input(repo, tmp_path, status="reviewed")
    result = repo.swdb("add", path, "--agent", "--agent-name", "SW Ensemble Agent")
    assert result.returncode == 0, result.stderr
    written = repo.read("inputs/kron-g18-k16.yaml")
    assert written["status"] == "draft"
    agent = [p for p in written["provenance"] if p["kind"] == "agent_run"]
    assert len(agent) == 1 and "SW Ensemble Agent" in agent[0]["description"]


def test_person_records_keep_their_status(repo, tmp_path):
    path, _ = new_input(repo, tmp_path, status="reviewed")
    assert repo.swdb("add", path).returncode == 0
    written = repo.read("inputs/kron-g18-k16.yaml")
    assert written["status"] == "reviewed"
    assert not [p for p in written["provenance"] if p["kind"] == "agent_run"]


def test_unreadable_file_fails(repo, tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("kind: [unclosed\n")
    assert repo.swdb("add", bad).returncode == 1
