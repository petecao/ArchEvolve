"""Kernel plug-in seam through the public CLI. Created: 2026-10-03 ET (ticket 38).

BFS is the first plug-in. These contracts check that kernel-specific evaluator
parts are selected per kernel and that BFS keeps its exact former identities.
Fixture durations never establish performance.
"""

import hashlib
import json

import pytest

from conftest import REPO
from test_proposals import proposal_setup  # noqa: F401  (fixture)
from test_bfs_native import evaluation_setup, evaluate  # noqa: F401  (fixture)
from test_bfs_protocol import _workload_request, _payload, _settings, _command


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _foreign_kernel(records):
    """The repository's TC kernel: a valid kernel record no evaluator plug-in owns."""
    import shutil
    for relative in ("kernels/gapbs-tc.yaml", "implementations/gapbs-tc-ordered.yaml"):
        target = records.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / "records" / relative, target)
    return "gapbs-tc"


def test_bfs_native_evaluation_keeps_its_former_identities(evaluation_setup):
    result, data = evaluate(evaluation_setup)
    assert result.returncode == 0, result.stderr
    context = data["context"]
    assert context["function"] == "DOBFS" and context["roi"] == "bfs.complete_call.v1"
    assert context["verifier"] == "swdb.bfs.structural.v1"
    assert context["verifier_sha256"] == _hash(REPO / "swdb" / "bfs_native.py")
    assert context["instrumentation"]["template_sha256"] == _hash(REPO / "tools/bfs_native/driver.cc.in")
    assert data["build"]["binary"].endswith("/bfs-native")
    assert all(check["verifier"] == "swdb.bfs.structural.v1" for check in data["correctness"]["checks"])


def test_workload_registration_requires_a_kernel_plugin(evaluation_setup, tmp_path):
    records, _, _, base = evaluation_setup
    request = _workload_request(records, tmp_path, base["workload"]["graph"])
    request["kernel"] = _foreign_kernel(records)
    result = records.swdb("register-workload", _payload(tmp_path, "register", request), "--format", "json")
    assert result.returncode == 1
    assert "evaluator plug-in" in result.stderr and "gapbs-bfs" in result.stderr


def test_protocol_freeze_requires_a_kernel_plugin(evaluation_setup, tmp_path):
    records, _, _, base = evaluation_setup
    request = _workload_request(records, tmp_path, base["workload"]["graph"])
    workload = _command(records, "register-workload", _payload(tmp_path, "register", request))
    assert workload["definition"]["kernel"] == "gapbs-bfs"
    settings = _settings(base, workload)
    settings["kernel"] = _foreign_kernel(records)
    freeze = {"message_version": "1.0", "id": "foreign-policy", "version": 1, "settings": settings}
    result = records.swdb("freeze-protocol", _payload(tmp_path, "freeze", freeze), "--format", "json")
    assert result.returncode == 1
    assert "evaluator plug-in" in result.stderr


def test_native_evaluation_refuses_a_candidate_kernel_without_plugin(evaluation_setup):
    records, _, _, base = evaluation_setup
    _foreign_kernel(records)
    path = "candidates/" + base["candidate"] + ".yaml"
    candidate = records.read(path)
    candidate["implementation"] = "gapbs-tc-ordered"
    records.write(path, candidate)
    result, data = evaluate(evaluation_setup, comparison_baseline=None)
    assert result.returncode == 1
    assert "no kernel plug-in" in data["outcome"]["reason"]
    assert data["timing"] == [] and data["correctness"]["state"] == "unverified"


def test_native_evaluation_refuses_an_roi_no_plugin_owns(evaluation_setup):
    result, data = evaluate(evaluation_setup, roi="other.complete_call.v1")
    assert result.returncode == 1
    assert "protected ROI" in data["outcome"]["reason"] and "bfs.complete_call.v1" in data["outcome"]["reason"]

