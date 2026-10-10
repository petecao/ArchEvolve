"""Intrinsic records: schema, rules, `swdb add`, and the database. Created 2026-09-23.
Updated: 2026-10-03 ET.
Each rule has a passing case (the seed records) and a failing case."""

import json

import pytest
import yaml

GATHER = "intrinsics/mm512_i32gather_ps.yaml"


def rejected(result, *fragments):
    assert result.returncode == 1, result.stdout + result.stderr
    for fragment in fragments:
        assert fragment in result.stderr, f"{fragment!r} not in stderr:\n{result.stderr}"


@pytest.fixture
def repo(records):
    return records.copy_repo()


def edit(records, rel, change):
    data = records.read(rel)
    change(data)
    records.write(rel, data)


def test_seed_intrinsics_pass(repo):
    result = repo.validate()
    assert result.returncode == 0, result.stderr
    gather = repo.read(GATHER)
    assert (gather["name"], gather["isa_extensions"], gather["memory_kind"]) == ("_mm512_i32gather_ps", ["avx512f"], "gather")
    prefetch = repo.read("intrinsics/mm_prefetch.yaml")
    assert (prefetch["name"], prefetch["isa_extensions"], prefetch["memory_kind"]) == ("_mm_prefetch", ["sse"], "prefetch")


def test_leading_underscore_id_fails_with_the_id_rule(repo):
    edit(repo, GATHER, lambda d: d.update(id="_mm512_i32gather_ps"))
    rejected(repo.validate(), GATHER, "id", "does not match '^[a-z0-9][a-z0-9._-]*$'")


def test_id_must_be_the_c_name_without_underscores(repo):
    edit(repo, GATHER, lambda d: d.update(id="gather16"))
    rejected(repo.validate(), GATHER, "its C name without leading underscores: 'mm512_i32gather_ps'")


def test_unknown_isa_extension_fails(repo):
    edit(repo, GATHER, lambda d: d.update(isa_extensions=["avx1024"]))
    rejected(repo.validate(), "isa_extensions[0]", "not in vocabulary isa_extensions")


def test_unknown_isa_family_fails(repo):
    edit(repo, GATHER, lambda d: d.update(isa_family="mips"))
    rejected(repo.validate(), "isa_family", "not in vocabulary isa_families")


def test_unknown_memory_kind_fails(repo):
    edit(repo, GATHER, lambda d: d.update(memory_kind="teleport"))
    rejected(repo.validate(), "memory_kind", "not in vocabulary intrinsic_memory_kinds")


def test_vendor_reference_is_required(repo):
    def strip(d):
        for p in d["provenance"]:
            if p["kind"] == "vendor_reference":
                p["kind"] = "human_report"
    edit(repo, GATHER, strip)
    rejected(repo.validate(), GATHER, "vendor_reference")


def test_non_memory_intrinsic_has_no_address_shape(repo):
    edit(repo, GATHER, lambda d: d.update(memory_kind="none"))
    rejected(repo.validate(), "address_shape", "touches no memory")
    edit(repo, GATHER, lambda d: d.update(address_shape=None))
    assert repo.validate().returncode == 0


def new_intrinsic(repo, tmp_path):
    data = repo.read(GATHER)
    data.update(id="mm512_i32scatter_ps", name="_mm512_i32scatter_ps", memory_kind="scatter")
    path = tmp_path / "scatter.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def test_add_writes_intrinsics_to_their_folder_and_the_database_lists_them(repo, tmp_path):
    result = repo.swdb("add", new_intrinsic(repo, tmp_path))
    assert result.returncode == 0, result.stderr
    assert (repo.path / "intrinsics" / "mm512_i32scatter_ps.yaml").is_file()
    rows = json.loads(repo.swdb("sql", "select id, memory_kind, lanes from intrinsics order by id", "--format", "json").stdout)
    legacy = [{"id": "mm512_i32gather_ps", "memory_kind": "gather", "lanes": 16},
              {"id": "mm512_i32scatter_ps", "memory_kind": "scatter", "lanes": 16},
              {"id": "mm_prefetch", "memory_kind": "prefetch", "lanes": None}]
    by_id = {row['id']: row for row in rows}
    assert [by_id[row['id']] for row in legacy] == legacy
    # The catalog also contains accelerator intrinsics; the index must include
    # every authoritative YAML record without fixing the seed inventory size.
    expected_ids = {repo.read('intrinsics/' + path.name)['id']
                    for path in (repo.path / 'intrinsics').glob('*.yaml')}
    assert set(by_id) == expected_ids


def test_add_agent_marks_an_intrinsic_draft_with_an_agent_run(repo, tmp_path):
    result = repo.swdb("add", new_intrinsic(repo, tmp_path), "--agent", "--agent-name", "sw-ensemble")
    assert result.returncode == 0, result.stderr
    data = repo.read("intrinsics/mm512_i32scatter_ps.yaml")
    assert data["status"] == "draft"
    assert any(p["kind"] == "agent_run" and "sw-ensemble" in p["description"] for p in data["provenance"])
