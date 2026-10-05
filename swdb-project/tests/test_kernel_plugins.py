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


def test_protocol_freeze_binds_the_verifier_to_the_kernel_plugin(evaluation_setup, tmp_path):
    """Ticket 39: a frozen correctness verifier must belong to the protocol kernel's plug-in."""
    records, _, _, base = evaluation_setup
    request = _workload_request(records, tmp_path, base["workload"]["graph"])
    workload = _command(records, "register-workload", _payload(tmp_path, "register", request))
    settings = _settings(base, workload)
    settings["correctness"]["verifier"] = "swdb.bc.brandes_scores.v1"  # another kernel's check
    freeze = {"message_version": "1.0", "id": "mismatched-verifier", "version": 1, "settings": settings}
    result = records.swdb("freeze-protocol", _payload(tmp_path, "freeze", freeze), "--format", "json")
    assert result.returncode == 1
    assert "does not belong to the BFS kernel plug-in" in result.stderr
    settings["correctness"]["verifier"] = "swdb.bfs.structural.v1"
    freeze["id"] = "matched-verifier"
    _command(records, "freeze-protocol", _payload(tmp_path, "freeze2", freeze))


def test_gem5_seam_selects_bfs_by_checker_and_keeps_its_rules():
    from swdb import kernels
    from swdb.bfs_protocol import accelerator_cases
    assert kernels.by_gem5_checker("dx100.bfs.verifier.v2") is kernels.BFS
    assert kernels.by_gem5_roi("bfs.complete_call.v1") is kernels.BFS
    assert kernels.BFS.gem5_verification_runtime == (
        "scripts/dx100_verify.py", "scripts/dx100_host_memory.py", "swdb/dx100_witness.py")
    observed = {"state": "observed", "stream": 2, "indirect": 7, "range": 3, "alu": 0, "indirect_stores": 0}
    check = {"checker": "dx100.bfs.verifier.v2",
             "coverage": {"instruction_counters": {}, "completed_trace_units": {}, "read_only_executed": observed}}
    assert accelerator_cases(check) == {"read_only_executed"}
    observed["indirect"] = 8
    assert accelerator_cases(check) == set()


# --- code review 2026-10-05 ET: plug-in attributes, shared rules, one graph table ------------------

def test_plugins_name_their_result_and_share_the_read_only_rule():
    from swdb import kernels
    assert (kernels.BFS.result_noun, kernels.BC.result_noun) == ("parent", "score")
    assert kernels.BFS.author_diagnostics and not kernels.BC.author_diagnostics
    # S5: one read-only rule and output bound, inherited by both plug-ins.
    for plugin in (kernels.BFS, kernels.BC):
        assert type(plugin).read_only_rule is kernels.KernelPlugin.read_only_rule
        assert type(plugin).native_output_limit is kernels.KernelPlugin.native_output_limit
        assert plugin.read_only_rule_text == "S>=1,I>=1,R>=1,A=0,indirect_stores=0,I=3*R-S"
        assert plugin.native_output_limit(10) == 10 * 24 + 4096
        assert plugin.read_only_rule(2, 7, 3, 0, 0) and not plugin.read_only_rule(2, 8, 3, 0, 0)
    assert not hasattr(kernels.KernelPlugin, "frontier_oracle")          # S4: the dead base method


def test_gem5_checker_resolution_refuses_unknown_checkers():
    from swdb import kernels
    from swdb.cli import Failure
    assert kernels.for_gem5_checker("dx100.bc.verifier.v2") is kernels.BC
    assert kernels.for_gem5_checker(None) is kernels.BFS        # records from before the kernel seam
    with pytest.raises(Failure, match="no kernel plug-in owns checker"):
        kernels.for_gem5_checker("dx100.tc.verifier.v1")


def test_one_application_graph_table_keeps_the_emitted_contracts():
    """F11: application -> format -> offset width -> CountT lives in swdb.sg_graph; the BC witness
    contract and the BFS evaluator's choices are the values they had before."""
    from swdb import bc_witness, bfs_protocol, bfs_native_scalable, kernels, sg_graph
    assert bc_witness.graph_verification_contract("gapbs")["input_format"] == "gapbs.sg64"
    assert bc_witness.graph_verification_contract("gapbs")["count_type"] == "double"
    assert bc_witness.graph_verification_contract("dx100-gapbs")["input_format"] == "gapbs.sg32"
    assert bc_witness.graph_verification_contract("dx100-gapbs")["count_type"] == "float"
    assert sg_graph.application_offset_bytes("gapbs") == 8 and sg_graph.application_offset_bytes("dx100-gapbs") == 4
    assert sg_graph.count_type_for_offset_bytes(8) == "double" and sg_graph.count_type_for_offset_bytes(4) == "float"
    assert bfs_native_scalable.SG_FORMATS == {"gapbs_sg32le": 4, "gapbs_sg64le": 8}
    assert bfs_protocol._sg_out_degrees is sg_graph.out_degrees
    check = kernels.BC.check_native_trial([[1], []], 0, {"scores": [0.0, 0.0]}, application="unknown")
    assert check["passed"] is False and "CountT" in check["reason"]


def test_evaluator_path_answers_what_follows_from_the_version():
    from swdb import bfs_native, bfs_native_scalable as scalable
    v1, v3 = scalable.path_for(scalable.EVALUATOR_V1), scalable.path_for(scalable.EVALUATOR_V3)
    assert not v1.scalable and v1.limits() == (bfs_native.MAX_VERTICES, bfs_native.MAX_DIRECTED_EDGES)
    assert v3.scalable and v3.keeps_distinct_parents and v3.driver == scalable.DRIVER_V3
    assert v3.limits() == (scalable.MAX_VERTICES, scalable.MAX_DIRECTED_EDGES)

