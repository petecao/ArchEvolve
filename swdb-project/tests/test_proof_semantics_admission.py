"""Conservative DX100 ordinary-memory admission through swdb prove; created 2026-10-15 ET.

Ticket 27 admits only the currently modeled CPU interactions. Ticket 28 must supply the ordinary-memory
hazard probes before these CPU writes or reads after a device store can reach a real verifier.
"""

import json

import pytest

from conftest import run_swdb
from test_proof_semantics import dx, dx_seed, needs_wp


@needs_wp
@pytest.mark.parametrize("adapter", ["cbmc", "wp"])
@pytest.mark.parametrize("unit,define", [
    ("cpu_memory_overlap", None),
    ("cpu_memory_overlap", "SWDB_CPU_OVERLAP_CALLEE"),
    ("cpu_memory_overlap", "SWDB_CPU_OVERLAP_ATOMIC"),
    ("cpu_memory_overlap", "SWDB_CPU_OVERLAP_AFTER_COVER"),
    ("store_source_wait", "SWDB_CPU_READ_AFTER_STORE"),
])
def test_unmodeled_cpu_memory_effects_are_refused_before_a_verifier(dx, adapter, unit, define):
    from test_cbmc_adapter import fake as fake_cbmc
    from test_wp_adapter import fake as fake_wp
    extra = ["--define", define] if define else []
    if adapter == "cbmc":
        extra += ["--bounds", json.dumps({"threads": 1, "n": 2})]
    result = run_swdb("prove", "--records", dx.records, "--candidate", dx.candidates["dx"],
        "--function", f"dxf_{unit}", "--contract", f"contract.fixture_dx_{unit}", "--adapter", adapter,
        "--runs-dir", dx.runs, "--format", "json", *extra,
        env=fake_cbmc("unknown") if adapter == "cbmc" else fake_wp("unknown"), timeout=180)
    assert result.returncode == 0, result.stderr + result.stdout
    record = dx.read(json.loads(result.stdout))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct", record
    assert record["settings"]["proof_semantics_admission"]["refused"]
    assert not any(r["name"] in {"wp_log", "cbmc_json", "differential"} for r in record["evidence"]["reports"])
