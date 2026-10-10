"""Format versions: 0.2, 0.3, and 0.4 are accepted, anything else is not. Created 2026-09-23; updated 2026-09-25."""

import pytest

KRON = "inputs/kron-g16-k16.yaml"


@pytest.fixture
def repo(records):
    return records.copy_repo()


def test_every_repo_record_validates_unchanged(repo):
    result = repo.validate()
    assert result.returncode == 0, result.stderr


def test_a_record_at_0_3_passes(repo):
    data = repo.read(KRON)
    data["schema_version"] = "0.3"
    repo.write(KRON, data)
    result = repo.validate()
    assert result.returncode == 0, result.stderr


def test_an_unsupported_version_fails(repo):
    data = repo.read(KRON)
    data["schema_version"] = "99.0"
    repo.write(KRON, data)
    result = repo.validate()
    assert result.returncode == 1
    assert KRON in result.stderr and "schema_version" in result.stderr
