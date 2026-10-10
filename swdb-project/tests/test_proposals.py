"""Actual patch application and durable public workflow behavior. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-26."""

import json
from pathlib import Path

import pytest


def test_real_patch_creates_unverified_candidate_and_survives_rebuild(proposal_setup):
    records, runs, snapshot, request = proposal_setup
    result = records.swdb("submit", request(), "--runs-dir", runs, "--format", "json")
    assert result.returncode == 0, result.stderr
    submitted = json.loads(result.stdout)
    assert submitted["outcome"]["state"] == "candidate_created"
    assert records.swdb("build").returncode == 0
    later = records.swdb("get", submitted["candidate"], "--chain", "--format", "json")
    assert later.returncode == 0, later.stderr
    chain = json.loads(later.stdout)["records"]
    candidate = chain[submitted["candidate"]]
    assert candidate["state"] == "unverified"
    assert "int alpha = 14" in (Path(candidate["artifact"]["path"]) / "src/bfs.cc").read_text()
    assert "int alpha = 15" in (Path(snapshot["artifact"]["path"]) / "src/bfs.cc").read_text()
    assert chain["test-package"]["completeness"] == "fixture"
    assert set(chain) == {"test-source", "test-package", "test-proposal", candidate["id"],
                          "gapbs-bfs-do", "gapbs", "gapbs-bfs"}


@pytest.mark.parametrize("case", ["stale", "wrong_source", "protected", "conflict", "operation", "scope", "invalid_producer"])
def test_retained_non_success_without_verified_implementation(proposal_setup, case):
    records, runs, _, request = proposal_setup
    if case == "stale":
        path = request(source_sha256="0" * 64)
    elif case == "wrong_source":
        path = request(implementation="gapbs-pr-pull")
    elif case == "protected":
        path = request("bool BFSVerifier", "bool ChangedVerifier")
    elif case == "conflict":
        path = request(payload={"kind": "patch", "content": "--- a/src/bfs.cc\n+++ b/src/bfs.cc\n@@ -1 +1 @@\n-never-present\n+nope\n"})
    elif case == "operation":
        path = request(required_operations=[{"operation": "invented-operation"}])
    elif case == "scope":
        path = request(constraints={"editable_files": ["src/bitmap.h"], "preserve_correctness": True, "preserve_roi": True})
    else:
        path = request(producer={"name": "fixture", "role": "sw", "test_client": True, "extra": "bad"})
    result = records.swdb("submit", path, "--runs-dir", runs, "--format", "json")
    assert result.returncode == 1, result.stderr
    submitted = json.loads(result.stdout)
    assert submitted["outcome"]["state"] in {"rejected", "unresolved", "failed"}
    assert submitted["outcome"]["reason"]
    assert "candidate" not in submitted
    later = records.swdb("get", "test-proposal", "--format", "json")
    assert later.returncode == 0, later.stderr
    assert json.loads(later.stdout)["outcome"] == submitted["outcome"]


def test_snapshot_tampering_is_rejected(proposal_setup):
    records, runs, snapshot, request = proposal_setup
    path = Path(snapshot["artifact"]["path"]) / "src/bfs.cc"
    path.write_text(path.read_text() + "\n// changed since the package\n")
    result = records.swdb("submit", request(), "--runs-dir", runs, "--format", "json")
    assert result.returncode == 1
    assert "identity" in json.loads(result.stdout)["outcome"]["reason"]


def test_duplicate_yaml_keys_remain_a_retrievable_rejection(proposal_setup, tmp_path):
    records, runs, _, _ = proposal_setup
    path = tmp_path / "bad.yaml"
    path.write_text("id: duplicate\nid: overwritten\n")
    result = records.swdb("submit", path, "--runs-dir", runs, "--format", "json")
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert "duplicate key" in data["request"]["parse_error"]
    assert records.swdb("get", data["id"]).returncode == 0
