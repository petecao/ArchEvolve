"""`testkit.record_ids`: the record ID of a YAML file, read from its `id:` line without
parsing the record. Created 2026-10-11 ET (LANL-shaped-db review fixes, finding 9)."""

import pytest

from testkit.record_ids import record_id, record_ids


def test_a_record_id_is_its_top_level_id_line(tmp_path):
    path = tmp_path / "a.yaml"
    path.write_text("kind: kernel\nid:  gapbs-bfs \nname: BFS\n  id: nested\n", encoding="utf-8")
    assert record_id(path) == "gapbs-bfs"


def test_a_file_without_one_top_level_id_line_fails_naming_the_file(tmp_path):
    path = tmp_path / "no-id.yaml"
    path.write_text("kind: kernel\nname: BFS\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no-id.yaml.*one top-level `id:` line"):
        record_id(path)


def test_record_ids_of_folders_are_in_path_order(tmp_path):
    (tmp_path / "kernels").mkdir()
    for name, rid in (("b.yaml", "second"), ("a.yaml", "first")):
        (tmp_path / "kernels" / name).write_text(f"id: {rid}\n", encoding="utf-8")
    assert record_ids(tmp_path, "kernels", "missing-folder") == ["first", "second"]
