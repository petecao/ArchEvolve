"""Public simulated collector fixtures, not hardware acceptance. Updated: 2026-09-25."""

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from swdb import artifacts, workflow
from test_dx100 import case, execution_request, reference


@pytest.mark.parametrize("mode", ["normal", "missing-memory", "truncated", "changed-stats", "multiple-intervals", "wrong-clock", "stale-region"])
def test_public_simulated_collector_retains_identity_and_incomplete_attribution(case, records, mode):
    records.copy_repo("applications")
    repository = Path(__file__).resolve().parents[1]
    kernel = yaml.safe_load((repository / "records/kernels/gapbs-bfs.yaml").read_text())
    kernel["baseline_implementation"] = "dx100-bfs-scalar"
    records.write("kernels/gapbs-bfs.yaml", kernel)
    records.write("implementations/dx100-bfs-scalar.yaml", yaml.safe_load(
        (repository / "records/implementations/dx100-bfs-scalar.yaml").read_text()))
    data = execution_request(case)
    _, invoke, folder = case
    source_root = folder / "candidate-source"
    path = source_root / "benchmarks/gapbs/src/bfs.cc"
    path.parent.mkdir(parents=True)
    text = 'void traversal() { while (active) { t.Start(); step(); queue.slide_window(); t.Stop(); PrintStep("td_maa", t.Seconds()); } }\n'
    path.write_text(text)
    model_path = Path(data["model_root"]) / "benchmarks/gapbs/src/bfs.cc"
    model_path.parent.mkdir(parents=True)
    model_path.write_text(text)
    artifact = artifacts.identify(source_root)
    source = workflow.record("source_snapshot", "source", implementation="dx100-bfs-scalar", application="dx100-gapbs",
        revision="fixture", artifact=artifact, context={}, protections=[], regions=[])
    candidate = workflow.record("candidate", "candidate", implementation="dx100-bfs-scalar", source_snapshot="source",
        artifact=artifact, context={}, protections=[], state="unverified", artifact_role="source_baseline")
    records.write("source_snapshots/source.yaml", source)
    records.write("candidates/candidate.yaml", candidate)
    rows = []
    for kind, begin, end in [("function", 0, len(text)-1), ("loop", text.index("while"), text.rindex("}")-1)]:
        fragment = text[begin:end]
        rows.append({"id": kind+":fixture", "kind": kind, "name": kind, "path": "benchmarks/gapbs/src/bfs.cc",
            "lines": [1,1], "byte_range": [begin,end], "source_sha256": hashlib.sha256(fragment.encode()).hexdigest(),
            "text": fragment, "function": "traversal", "metrics": {"inclusive_thread_cpu_seconds": 999}})
    discovery = workflow.record("region_profile", "discovery", candidate="candidate", source_snapshot="source",
        request={"fixture": True}, discovery={"backend": "libclang-cindex"},
        outcome={"state": "complete", "stage": "fixture", "reason": None}, stages=[], regions=rows,
        dynamic_memory=[], executions=[], raw_artifacts=[], reasons=[], gain_claim=False)
    if mode == "stale-region":
        discovery["regions"][0]["source_sha256"] = "0" * 64
    records.write("region_profiles/discovery.yaml", discovery)
    simulator = Path(data["simulator"]["path"])
    program = simulator.read_text().replace("[fixture]\\nkind=contract_fixture\\n",
        "[system.cpu_clk_domain]\\ntype=SrcClockDomain\\nclock=313\\n")
    stats = "---------- Begin Simulation Statistics ----------\nsimTicks 1000\nsimFreq 1000000\n"
    if mode != "missing-memory":
        stats += "system.maa.port_mem_RD_packets 23\n"
    if mode != "truncated":
        stats += "---------- End Simulation Statistics ----------\n"
    if mode == "multiple-intervals":
        stats += "---------- Begin Simulation Statistics ----------\nsimTicks 999999\nsimFreq 1000000\n---------- End Simulation Statistics ----------\n"
    program = program.replace("'---------- Begin Simulation Statistics ----------\\nsimTicks 31300\\nsimFreq 1000000000000\\n'", repr(stats))
    program = program.replace("    print('Exiting @ tick 31400", "    print('ROI started: 1 threads\\n td_maa 0.00040\\nROI End!!!')\n    print('Exiting @ tick 31400")
    if mode == "wrong-clock":
        program = program.replace("clock=313", "clock=unknown")
    simulator.write_text(program)
    data.update(candidate="candidate", simulator=reference(simulator))
    evaluation = invoke("dx100-execute", data)
    assert evaluation["outcome"]["state"] == "complete", evaluation["outcome"]
    if mode == "changed-stats":
        Path(evaluation["context"]["statistics"]["path"]).write_text("different")
    request = {"message_version": "1.0", "id": "profile", "evaluation": evaluation["id"],
        "discovery_profile": "discovery", "budget": {"total_seconds": 60}}
    request_file = folder / "profile.yaml"
    request_file.write_text(yaml.safe_dump(request))
    run = records.swdb("dx100-profile", request_file, "--runs-dir", folder / "runs", "--format", "json")
    assert run.returncode in {0,1}, run.stderr
    profile = json.loads(run.stdout)
    assert json.loads(records.swdb("get", "profile", "--format", "json").stdout) == profile
    retrieved = json.loads(records.swdb("get", evaluation["id"], "--format", "json").stdout)
    assert retrieved["correctness"]["state"] == "unverified"
    assert retrieved["gain_claim"] is False
    if mode in {"truncated", "changed-stats", "wrong-clock", "stale-region"}:
        assert profile["outcome"]["state"] == "failed"
        assert retrieved["timing"] == []
    else:
        assert profile["outcome"]["state"] == "partial"
        assert retrieved["timing"][0]["duration_s"] == 0.001
        assert profile["context"]["roi_observation"]["clocks"]["system.cpu_clk_domain"]["period_ticks"] == [313]
        assert profile["context"]["roi_observation"]["interval_count"] == (2 if mode == "multiple-intervals" else 1)
        assert profile["regions"][0]["metrics"] == {}
        assert profile["regions"][1]["metrics"]["inclusive_simulated_seconds"] == 0.0004
        assert "exclusive_simulated_seconds" not in profile["regions"][1]["metrics"]
        assert bool(profile["dynamic_memory"]) == (mode != "missing-memory")
        assert profile["executions"][0]["evidence_kind"] == "contract_fixture"
