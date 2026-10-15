"""Conservative DX100 ordinary-memory admission through swdb prove; created 2026-10-15 ET.

Ticket 27 admits only the currently modeled CPU interactions. Ticket 28 must supply the ordinary-memory
hazard probes before these CPU writes or reads after a device store can reach a real verifier.
"""

import json

import pytest

from conftest import run_swdb
from test_proof_semantics import dx, dx_seed, needs_cbmc, needs_wp, prove, prove_wp


@needs_cbmc
@pytest.mark.parametrize("wait", [False, True])
def test_store_must_be_covered_before_return_in_the_bounded_model(dx, wait):
    record = prove(dx, "store_exit", *(["SWDB_STORE_EXIT_WAIT"] if wait else []))
    if wait:
        assert record["verdict"] == "proven", record
    else:
        assert record["verdict"] == "not_proven" and record["failure_class"] == "memory_domain" and "counterexample" not in record, record
        assert any(g["property"] == "swdb.dx100_memory_domain" and g["status"] == "failure"
                   for g in record["goals"])


@needs_wp
@pytest.mark.parametrize("wait", [False, True])
def test_store_must_be_covered_before_return_in_wp(dx, wait):
    record = prove_wp(dx, "store_exit", *(["SWDB_STORE_EXIT_WAIT"] if wait else []), hints=[
        {"anchor": "dxf_store_exit.entry", "kind": "ghost", "text": "ghost dx_store_bound = n;",
         "provenance": {"source": "agent"}},
        {"anchor": "dxf_store_exit.s5.before", "kind": "assert",
         "text": "assert \\forall integer k; 0 <= k < dx_tile_size[0] && k < DX_TS ==> "
                 "0 <= (unsigned int)dx_tile_data[0][k] < n;", "provenance": {"source": "agent"}}])
    if wait:
        assert record["verdict"] == "proven", record.get("unproven_properties")
    else:
        assert record["verdict"] == "not_proven" and "counterexample" not in record
        assert any("memory_domain_exit" in g["goal"] and g["status"] != "valid" for g in record["goals"])


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


@needs_cbmc
@pytest.mark.parametrize("gather", [False, True])
@pytest.mark.parametrize("wait_between", [False, True])
def test_device_memory_domain_requires_a_covering_wait_in_the_bounded_model(dx, gather, wait_between):
    defines = (["SWDB_DEVICE_GATHER_AFTER_STORE"] if gather else []) + \
              (["SWDB_DEVICE_WAIT_BETWEEN"] if wait_between else [])
    record = prove(dx, "device_memory_overlap", *defines)
    if wait_between:
        assert record["verdict"] == "proven", record
    else:
        assert record["verdict"] == "not_proven" and record["failure_class"] == "memory_domain", record
        assert "counterexample" not in record
        assert any(g["property"] == "swdb.dx100_memory_domain" and g["status"] == "failure" for g in record["goals"])


@needs_wp
@pytest.mark.parametrize("gather", [False, True])
@pytest.mark.parametrize("wait_between", [False, True])
def test_device_memory_domain_requires_a_covering_wait_in_wp(dx, gather, wait_between):
    defines = (["SWDB_DEVICE_GATHER_AFTER_STORE"] if gather else []) + \
              (["SWDB_DEVICE_WAIT_BETWEEN"] if wait_between else [])
    record = prove_wp(dx, "device_memory_overlap", *defines, hints=[
        {"anchor": "dxf_device_memory_overlap.entry", "kind": "ghost", "text": "ghost dx_store_bound = n;",
         "provenance": {"source": "agent"}},
        {"anchor": "dxf_device_memory_overlap.s5.before", "kind": "assert",
         "text": "assert \\forall integer k; 0 <= k < dx_tile_size[0] && k < DX_TS ==> "
                 "0 <= (unsigned int)dx_tile_data[0][k] < n;", "provenance": {"source": "agent"}}])
    assert record["hint_check"]["verdict"] == "accepted", record["hint_check"]
    if wait_between:
        assert record["verdict"] == "proven", record.get("unproven_properties")
    else:
        assert record["verdict"] == "not_proven" and "counterexample" not in record
        assert any("memory_domain" in g["goal"] and g["status"] != "valid" for g in record["goals"])
