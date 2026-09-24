"""Rules read other records only once those passed their schema, so a malformed record is
reported on its own file and never crashes the rules of the records that refer to it.
Created 2026-09-23 (code review of the optimization-strategies branch)."""

import pytest

from test_strategies import edit, rejected


@pytest.fixture
def repo(records):
    return records.copy_repo()


@pytest.mark.parametrize("rel, change, field", [
    ("machines/mbit10.yaml", lambda d: d.update(counters="none"), "counters"),
    ("inputs/urand-u16-k16.yaml", lambda d: d.update(properties="many"), "properties"),
    ("implementations/gapbs-pr-jacobi.yaml", lambda d: d.update(access_patterns="some"), "access_patterns"),
    ("applications/gapbs.yaml", lambda d: d.update(source="github"), "source"),
    ("intrinsics/mm512_i32gather_ps.yaml", lambda d: d.update(isa_extensions="avx512f"), "isa_extensions"),
])
def test_a_malformed_record_is_reported_not_a_crash(repo, rel, change, field):
    edit(repo, rel, change)
    if rel.startswith("intrinsics/"):
        edit(repo, "implementations/gapbs-pr-jacobi.yaml", lambda d: d.update(uses_intrinsics=["mm512_i32gather_ps"]))
    result = repo.validate()
    rejected(result, rel, field)
    assert "Traceback" not in result.stderr
