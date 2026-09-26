"""Public simulated collector fixtures, not hardware acceptance. Updated: 2026-09-25."""

import hashlib
import copy
import json
from pathlib import Path

import pytest
import yaml

from swdb import artifacts, workflow
from test_dx100 import case, execution_request, reference


@pytest.mark.parametrize("mode", ["normal", "missing-memory", "truncated", "changed-stats", "multiple-intervals", "wrong-clock", "stale-region",
    "diagnostic", "diagnostic-source-mismatch", "diagnostic-invalid-counters", "diagnostic-outside-roi",
    "diagnostic-report-list", "diagnostic-counter-list", "diagnostic-boolean-errors",
    "pinned-cache-totals", "pinned-region-only"])
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
    if mode in {'pinned-cache-totals', 'pinned-region-only'}:
        data['configuration'].update(mode='BASE', l3_size_mb=10, l3_assoc=20)
        stats += 'system.cpu0.dcache.overallAccesses_7::total 99\n'
        if mode == 'pinned-cache-totals':
            stats += 'system.cpu0.dcache.overallAccesses_T::total 23\n'
    elif mode != "missing-memory":
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
    if mode.startswith('diagnostic'):
        evaluation['context']['workload'] = {'canonical_sha256': 'a' * 64}
        evaluation['context']['protocol_trial'] = {'source_position': 2, 'repetition': 1}
        records.write('evaluations/' + evaluation['id'] + '.yaml', evaluation)
        diagnostic = copy.deepcopy(evaluation)
        diagnostic['id'] = 'diagnostic'
        diagnostic['context']['candidate_build'] = 'diagnostic-build'
        if mode == 'diagnostic-source-mismatch':
            diagnostic['context']['candidate_sha256'] = 'b' * 64
        binary = folder / 'diagnostic-binary'; binary.write_bytes(b'fixture diagnostic binary')
        diagnostic['build'].update(binary=str(binary), binary_sha256=artifacts.file_hash(binary))
        log = folder / 'diagnostic-log'
        values = {'format': 'swdb.dx100.regions.v1', 'clock': 'm5_rpns', 'errors': 0,
                  'regions': [{'index': i, 'inclusive_ns': 300 - i * 100, 'exclusive_ns': 100,
                               'invocations': 2} for i in range(len(rows))]}
        if mode == 'diagnostic-invalid-counters': values['regions'][0]['exclusive_ns'] = 900
        if mode == 'diagnostic-report-list': values = []
        if mode == 'diagnostic-counter-list': values['regions'][0] = []
        if mode == 'diagnostic-boolean-errors': values['errors'] = False
        if mode == 'diagnostic-outside-roi':
            values['regions'][0].update(inclusive_ns=0, exclusive_ns=0, invocations=0)
        log.write_text('SWDB_DX100_ROI_SEALED\nSWDB_DX100_REGIONS ' + json.dumps(values) + '\n')
        diagnostic['stages'] = [{'stage': 'simulation', 'state': 'complete', 'started': evaluation['stages'][0]['started'],
                                 'log': str(log), 'log_sha256': artifacts.file_hash(log)}]
        build = copy.deepcopy(diagnostic); build['id'] = 'diagnostic-build'
        build['outcome']['stage'] = 'candidate_build'
        build['context']['diagnostic'] = {'regions': rows, 'discovery': {'backend': 'libclang-cindex', 'unresolved': []},
            'instrumented_source': reference(path), 'runtime': reference(binary),
            'quantity': 'per-thread simulated elapsed, summed; includes waits', 'difference': 'explicit source-scope fixture instrumentation'}
        records.write('evaluations/diagnostic-build.yaml', build)
        records.write('evaluations/diagnostic.yaml', diagnostic)
        request.pop('discovery_profile')
        request['diagnostic_evaluation'] = 'diagnostic'
    request_file = folder / "profile.yaml"
    request_file.write_text(yaml.safe_dump(request))
    run = records.swdb("dx100-profile", request_file, "--runs-dir", folder / "runs", "--format", "json")
    assert run.returncode in {0,1}, run.stderr
    assert run.stdout, run.stderr
    profile = json.loads(run.stdout)
    if mode == 'pinned-cache-totals':
        assert [row['metric'] for row in profile['dynamic_memory']] == ['system.cpu0.dcache.overallAccesses_T::total']
        assert profile['dynamic_memory'][0]['value'] == 23
    elif mode == 'pinned-region-only':
        assert profile['dynamic_memory'] == []
    assert json.loads(records.swdb("get", "profile", "--format", "json").stdout) == profile
    retrieved = json.loads(records.swdb("get", evaluation["id"], "--format", "json").stdout)
    assert retrieved["correctness"]["state"] == "unverified"
    assert retrieved["gain_claim"] is False
    if mode in {"truncated", "changed-stats", "wrong-clock", "stale-region", 'diagnostic-source-mismatch', 'diagnostic-invalid-counters',
                'diagnostic-report-list', 'diagnostic-counter-list', 'diagnostic-boolean-errors'}:
        assert profile["outcome"]["state"] == "failed"
        assert retrieved["timing"] == []
    else:
        assert profile["outcome"]["state"] == ('complete' if mode == 'diagnostic' else "partial")
        assert retrieved["timing"][0]["duration_s"] == 0.001
        assert profile["context"]["roi_observation"]["clocks"]["system.cpu_clk_domain"]["period_ticks"] == [313]
        assert profile["context"]["roi_observation"]["interval_count"] == (2 if mode == "multiple-intervals" else 1)
        if mode == 'diagnostic':
            assert profile['regions'][0]['metrics']['inclusive_simulated_seconds'] == 300 / 1e9
            assert profile['regions'][0]['metrics']['exclusive_simulated_seconds'] == 100 / 1e9
            assert profile['executions'][1]['correctness']['state'] == 'unverified'
            assert profile['artifacts']['region_binary']['sha256'] != profile['artifacts']['memory_binary']['sha256']
            assert profile['dynamic_memory'][0]['raw_sha256'] == evaluation['context']['statistics']['sha256']
            assert all(run['source_position'] == 2 and run['repetition'] == 1 for run in profile['executions'])
            assert retrieved['timing'][0]['source_position'] == 2 and retrieved['timing'][0]['repetition'] == 1
        elif mode == 'diagnostic-outside-roi':
            assert profile['regions'][0]['metrics'] == {'invocations': 0}
            assert profile['regions'][0]['observation_state'] == 'unobserved'
            assert 'not entered' in profile['regions'][0]['unavailable_reason']
            assert profile['regions'][1]['metrics']['inclusive_simulated_seconds'] == 200 / 1e9
        else:
            assert profile["regions"][0]["metrics"] == {}
            assert profile["regions"][1]["metrics"]["inclusive_simulated_seconds"] == 0.0004
            assert "exclusive_simulated_seconds" not in profile["regions"][1]["metrics"]
        assert bool(profile["dynamic_memory"]) == (mode not in {'missing-memory', 'pinned-region-only'})
        assert profile["executions"][0]["evidence_kind"] == "contract_fixture"
