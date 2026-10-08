"""Bounded real-record fixture copying regressions. Created 2026-10-08 ET."""

import pytest

from swdb import yamlio
from testkit.record_subset import copy_record_subset


def test_subset_handles_quoted_ids_cycles_and_semantic_evidence_without_loading_unrelated_body(tmp_path, monkeypatch):
    source, destination = tmp_path / "source", tmp_path / "copy"
    source.mkdir()
    root = source / "unrelated-filename.yaml"
    root.write_text('kind: implementation\n"id": "root: quoted # text"\nverification:\n'
                    '  evidence: [proof]\ndefinition:\n  representations:\n'
                    '  - application: upstream\n    format: gapbs_sg64le\n'
                    '  - application: fork\n    format: gapbs_sg32le\n')
    proof = source / "proof.yml"
    proof.write_text("kind: profile\nid: 'proof'\nimplementation: 'root: quoted # text'\n")
    apps = source / "applications"
    apps.mkdir()
    upstream, fork = apps / "unrelated-upstream-name.yaml", apps / "unrelated-fork-name.yaml"
    upstream.write_text("kind: application\nid: upstream\n")
    fork.write_text("kind: application\nid: fork\n")
    # An unrelated malformed body must not be parsed or copied merely to index it.
    (source / "huge.yaml").write_text("kind: estimate\nid: unrelated\npayload: [" + "x" * 100_000)
    loaded, original = [], yamlio.load

    def record_load(path):
        loaded.append(path)
        return original(path)

    monkeypatch.setattr(yamlio, "load", record_load)
    selected = copy_record_subset(source, destination, ["root: quoted # text"])
    assert selected == {"root: quoted # text", "proof", "upstream", "fork"}
    assert set(loaded) == {root, proof, upstream, fork}
    for path in (root, proof, upstream, fork):
        assert (destination / path.relative_to(source)).read_bytes() == path.read_bytes()
    assert not (destination / "huge.yaml").exists()


def test_subset_refuses_missing_roots_and_duplicate_ids_before_copy(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "copy"
    source.mkdir()
    (source / "a.yaml").write_text("id: a\n")
    with pytest.raises(ValueError, match="roots are missing"):
        copy_record_subset(source, destination, ["missing"])
    (source / "b.yaml").write_text("id: a\n")
    with pytest.raises(ValueError, match="duplicate"):
        copy_record_subset(source, destination, ["a"])
    assert not destination.exists()
