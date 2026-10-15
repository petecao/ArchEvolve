"""Proof setup and fresh WP verdicts through swdb prove (ticket 36). Created: 2026-10-15 ET.

Agreed seam: swdb prove -> validated record, with scripted adapters for prelaunch negative
controls and actual WP fact fixtures for verdict independence. No private-helper assertions.
"""
import json
from pathlib import Path

import pytest

from test_proof_records import proof_seed, seed  # public CLI seed


def test_scripted_bounded_job_rejects_unattributed_harness_assume_before_command(seed):
    marker = seed.root / "must-not-run"
    harness = seed.root / "harness.c"
    harness.write_text("void f(int parent) { __CPROVER_assume(parent >= -1); }\n")
    script = seed.script(setup={"tool": "saw", "inputs": [{"path": str(harness)}]},
                         run=["/usr/bin/touch", str(marker)])
    failed = seed.prove(script, ok=False)
    assert "proof setup check" in failed.stderr
    assert "assumption_provenance" in failed.stderr
    assert not marker.exists()
    assert not seed.proof_files()


def test_successful_scripted_proof_records_versioned_setup_and_method_hash(seed):
    record = seed.prove(seed.script())["record"]
    assert record["proof_setup_check"]["verdict"] == "passed"
    assert record["proof_setup_check"]["check"]["version"] == "1"
    assert record["proof_setup_check"]["method_version"] == record["pins"]["method_version"]
    assert len(record["proof_setup_check"]["check"]["sha256"]) == 64
