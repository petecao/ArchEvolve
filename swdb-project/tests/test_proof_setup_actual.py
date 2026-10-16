"""Actual ticket-36 production admission control; created 2026-10-15 ET.

Run only after coordinator admission of the exact reviewed source and command.
The wrapper preserves the real frontend trace and compilation; only its optional
libclang discovery is made unavailable in an isolated empty LLVM directory.
"""
import hashlib
import json
import shlex

import pytest
import yaml

from conftest import run_swdb
from test_proof_setup import wp_setup


def test_actual_wp_keeps_the_real_driver_when_optional_libclang_is_unavailable(tmp_path, monkeypatch, wp_setup):
    from swdb import c_lowering, framac
    if framac.locate().missing:
        pytest.skip(framac.locate().missing)
    real = c_lowering.locate().command
    resource = tmp_path / "empty-llvm" / "lib" / "clang" / "22"
    resource.mkdir(parents=True)
    wrapper = tmp_path / "clang-without-optional-parser"
    wrapper.write_text('#!/bin/sh\nif [ "$1" = "-print-resource-dir" ]; then\n'
                       + "  printf '%s\\n' " + shlex.quote(str(resource)) + '\n  exit 0\nfi\nexec '
                       + shlex.join(real) + ' "$@"\n')
    wrapper.chmod(0o755)
    monkeypatch.setenv("SWDB_CLANG", str(wrapper))
    wp_setup.method["evidence_kind"] = "contract_fixture"
    wp_setup.method["c_lowering"]["translators"] = [c_lowering.identity()["c_lowering"]]
    wp_setup.method_path.write_text(yaml.safe_dump(wp_setup.method, sort_keys=False))
    result = run_swdb("prove", "--records", wp_setup.records, "--summary", "contract.setup_helper",
                      "--adapter", "wp", "--method-version", wp_setup.method["id"],
                      "--runs-dir", tmp_path / "actual-runs", "--format", "json")
    assert result.returncode == 0, result.stderr + result.stdout
    record = json.loads(result.stdout)["record"]
    assert record["evidence_kind"] == "contract_fixture"
    assert record["verdict"] == "proven" and record["settings"]["verifier_launched"]
    assert record["proof_setup_check"]["runs"][-1]["verdict"] == "passed"
    runtime = record["settings"]["compiler_runtime"]
    assert "matching libclang" in runtime["unavailable"]
    assert runtime["driver"]["path"] != str(wrapper)
    assert runtime["command_executable"] == {
        "path": str(wrapper), "sha256": hashlib.sha256(wrapper.read_bytes()).hexdigest()}
    ordinary = [goal for goal in record["goals"] if not goal.get("smoke")]
    smoke = [goal for goal in record["goals"] if goal.get("smoke")]
    assert ordinary and smoke and all(goal["status"] == "valid" for goal in ordinary + smoke)
    assert not wp_setup.marker.exists()  # The external report stand-in was never invoked.
