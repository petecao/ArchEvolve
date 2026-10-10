"""Proposal fixtures: a records copy, a source snapshot, a fixture package and a
proposal-request writer. Created 2026-10-05 ET (code review T1), from tests/test_proposals.py."""

import difflib
import json

import pytest
import yaml

from conftest import REPO


def build_proposal_setup(records, tmp_path, *, copy_all=True):
    if copy_all:
        records.copy_repo()
    runs = tmp_path / "runs"
    created = records.swdb("source-snapshot", "gapbs-bfs-do", "--runs-dir", runs,
                           "--id", "test-source", "--format", "json")
    assert created.returncode == 0, created.stderr
    snapshot = json.loads(created.stdout)
    result = records.swdb("fixture-package", "test-source", "--id", "test-package", "--format", "json")
    assert result.returncode == 0, result.stderr
    original = (REPO / "apps/gapbs/src/bfs.cc").read_text()

    def request(before="int alpha = 15", after="int alpha = 14", **changes):
        patch = "".join(difflib.unified_diff(original.splitlines(keepends=True),
                                            original.replace(before, after).splitlines(keepends=True),
                                            fromfile="a/src/bfs.cc", tofile="b/src/bfs.cc"))
        data = {"message_version": "1.0", "id": "test-proposal",
                "producer": {"name": "proposal-test", "role": "sw", "test_client": True},
                "profile_package": "test-package", "source_snapshot": "test-source",
                "implementation": "gapbs-bfs-do", "source_sha256": snapshot["artifact"]["sha256"],
                "intent": "Change the direction-switch parameter; contract test only.",
                "regions": [snapshot["regions"][0]["id"]],
                "constraints": {"editable_files": ["src/bfs.cc"], "preserve_correctness": True, "preserve_roi": True},
                "payload": {"kind": "patch", "content": patch}, "required_operations": []}
        data.update(changes)
        path = tmp_path / f"{data['id']}.yaml"
        path.write_text(yaml.safe_dump(data))
        return path
    return records, runs, snapshot, request


@pytest.fixture
def proposal_setup(records, tmp_path):
    return build_proposal_setup(records, tmp_path)
