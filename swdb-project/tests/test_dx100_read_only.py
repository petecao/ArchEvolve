"""Public read-only completion regressions; synthetic gem5 only. 2026-10-03 ET."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from test_bfs_protocol import _workload_request
from test_dx100 import case, reference
from test_dx100_v2 import v2_request
from swdb import dx100, dx100_coverage, read_only_checks


def read_only_request(case, records, *, behavior="normal", observed=True, frontiers=True):
    request = v2_request(case, behavior)
    _, _, folder = case
    repository = Path(__file__).resolve().parents[1]
    kernel = yaml.safe_load((repository / "records/kernels/gapbs-bfs.yaml").read_text())
    kernel["baseline_implementation"] = "dx100-bfs-scalar"
    records.write("kernels/gapbs-bfs.yaml", kernel)
    records.write("implementations/dx100-bfs-scalar.yaml", yaml.safe_load(
        (repository / "records/implementations/dx100-bfs-scalar.yaml").read_text()))
    workload_request = _workload_request(records, folder,
        {"num_vertices": 3, "directed": True, "edges": [[0, 1], [1, 2]]})
    registration = folder / "workload.yaml"
    registration.write_text(yaml.safe_dump(workload_request))
    registered = records.swdb("register-workload", registration, "--format", "json")
    assert registered.returncode == 0, registered.stderr
    workload = json.loads(registered.stdout)
    representation = next(row for row in workload["definition"]["representations"]
                          if row["application"] == "dx100-gapbs")
    request["workload"] = {"id": workload["id"], "source": 0,
                           "representation": {key: representation[key] for key in ("path", "sha256")}}
    source = Path(request["model_root"]) / "benchmarks/gapbs/src/bfs.cc"
    source.write_text(read_only_checks.FRONTIER_TEXT + "\n")
    lines = []
    tick = 110
    for unit, opcode, count in [("S", "STREAM_LD", 2), ("I", "INDIR_LD", 4), ("R", "RANGE_LOOP", 2)]:
        for _ in range(count):
            lines += [f"{tick}: global: {unit}[0] Start [INSTR[opcode({opcode})]]",
                      f"{tick + 1}: global: {unit}[0] End [INSTR]"]
            tick += 2
    if not observed:
        lines += ["150: global: A[0] Start [INSTR[opcode(ALU_SCALAR)]]",
                  "151: global: A[0] End [INSTR]"]
    if frontiers:
        lines += ["Starting TDStep: 1 elements"] * 3
    simulator = Path(request["simulator"]["path"])
    marker = "    tick=[31400]; steps=[]; calls=[0]; enabled=set(); trace_path=[None]"
    simulator.write_text(simulator.read_text().replace(marker,
        f"    print({chr(10).join(lines)!r},flush=True)\n" + marker))
    request["simulator"] = reference(simulator)
    request["verification"].update(coverage=True, read_only=True)
    return request


@pytest.mark.parametrize("observed", [True, False])
def test_completed_public_read_only_execution_requires_its_instruction_mix(case, records, observed):
    request = read_only_request(case, records, observed=observed)
    _, invoke, _ = case
    result = invoke("dx100-execute", request)
    assert result["outcome"]["state"] == ("complete" if observed else "incorrect"), result["outcome"]
    check = result["correctness"]["checks"][0]
    assert check["continuation"]["normal_exit_observed"] is True
    assert check["frontier_sizes"]["state"] == "passed"
    assert check["coverage"]["read_only_executed"]["state"] == ("observed" if observed else "unobserved")
    assert result["correctness"]["state"] == ("passed" if observed else "failed")
    assert check["passed"] is observed
    if not observed:
        assert "read-only execution witness" in result["outcome"]["reason"]
        assert result["timing"] == []
    assert result["gain_claim"] is False


@pytest.mark.parametrize("observed,frontiers", [(True, True), (False, True), (False, False)])
def test_incomplete_public_read_only_execution_stays_unverified(case, records, observed, frontiers):
    request = read_only_request(case, records, behavior="no-exit", observed=observed, frontiers=frontiers)
    _, invoke, _ = case
    result = invoke("dx100-execute", request)
    assert result["outcome"]["state"] == "missing_observation", result["outcome"]
    assert result["correctness"]["state"] == "unverified"
    assert result["correctness"]["checks"][0]["passed"] is False
    assert result["timing"] == [] and result["gain_claim"] is False


def test_public_execution_refuses_an_absent_read_only_witness(case, records, monkeypatch):
    request = read_only_request(case, records)
    _, _, folder = case
    path = folder / "execute.yaml"
    path.write_text(yaml.safe_dump(request))
    original = dx100_coverage.observe
    def without_read_only_case(*args, **kwargs):
        observed = original(*args, **kwargs)
        observed.pop("read_only_executed", None)
        return observed
    monkeypatch.setattr(dx100_coverage, "observe", without_read_only_case)
    result = dx100.execute(SimpleNamespace(file=path, records=records.path,
        runs_dir=folder / "runs", lane="0", db=None))
    assert result["outcome"]["state"] == "incorrect", result["outcome"]
    assert result["correctness"]["state"] == "failed"
    assert result["correctness"]["checks"][0]["passed"] is False
    assert result["timing"] == [] and result["gain_claim"] is False
