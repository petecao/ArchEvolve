"""Isolated provider-workspace records (`workspace_proposal_setup`, renamed from the
second `proposal_setup`). Created 2026-10-05 ET (code review T1), from
tests/test_provider_workspace.py."""

import difflib
import json
from pathlib import Path

import pytest
import yaml

from conftest import REPO


@pytest.fixture
def workspace_proposal_setup(records, tmp_path):
    # Retain the real BFS contract, without unrelated historical evaluations.
    for name in ("applications/gapbs.yaml", "kernels/gapbs-bfs.yaml", "implementations/gapbs-bfs-do.yaml",
                 "machines/mbit10.yaml", "strategies/software_prefetch.yaml", "intrinsics/mm_prefetch.yaml"):
        data = yaml.safe_load((REPO / "records" / name).read_text())
        if data["kind"] == "implementation":
            data["verification"] = {"status": "unchecked", "evidence": [], "scope": "Isolated workspace contract fixture."}
        records.write(name, data)
    runs = tmp_path / "runs"
    result = records.swdb("source-snapshot", "gapbs-bfs-do", "--runs-dir", runs, "--id", "test-source", "--format", "json")
    assert result.returncode == 0, result.stderr
    snapshot = json.loads(result.stdout)
    result = records.swdb("fixture-package", "test-source", "--id", "test-package", "--format", "json")
    assert result.returncode == 0, result.stderr
    original = (Path(snapshot["artifact"]["path"]) / "src/bfs.cc").read_text()
    patch = "".join(difflib.unified_diff(original.splitlines(keepends=True),
        original.replace("int alpha = 15", "int alpha = 14").splitlines(keepends=True),
        fromfile="a/src/bfs.cc", tofile="b/src/bfs.cc"))

    def request(**changes):
        data = {"message_version": "1.0", "id": "test-proposal",
                "producer": {"name": "workspace-test", "role": "sw", "test_client": True},
                "profile_package": "test-package", "source_snapshot": "test-source",
                "implementation": "gapbs-bfs-do", "source_sha256": snapshot["artifact"]["sha256"],
                "intent": "Direction-switch parameter change, workspace contract fixture only.",
                "regions": [snapshot["regions"][0]["id"]], "required_operations": [],
                "constraints": {"editable_files": ["src/bfs.cc"], "preserve_correctness": True, "preserve_roi": True},
                "payload": {"kind": "patch", "content": patch}, **changes}
        path = tmp_path / f"{data['id']}.yaml"
        path.write_text(yaml.safe_dump(data))
        return path
    return records, runs, snapshot, request
