"""Public simulated collector fixtures, not hardware acceptance. Updated: 2026-09-26."""

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
    "pinned-cache-totals", "pinned-region-only", "diagnostic-unverified", "diagnostic-incorrect",
    "diagnostic-no-seal", "diagnostic-seal-tamper", "diagnostic-seal-binding", "diagnostic-seal-list",
    "diagnostic-preseal", "diagnostic-unentered-time", "diagnostic-missing-trial",
    "diagnostic-wrong-position", "diagnostic-wrong-repetition", "diagnostic-timing-mismatch", "diagnostic-wrong-source"])
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
        # Diagnostics retain their own global trial, even without a frozen
        # protocol and when context.sources contains only the executed source.
        diagnostic['context']['workload']['sources'] = [1, 2, evaluation['context']['source']]
        diagnostic['context']['candidate_build'] = 'diagnostic-build'
        if mode == 'diagnostic-missing-trial': diagnostic['context'].pop('protocol_trial')
        if mode == 'diagnostic-wrong-position': diagnostic['context']['protocol_trial']['source_position'] = 0
        if mode == 'diagnostic-wrong-repetition': diagnostic['context']['protocol_trial']['repetition'] = 0
        if mode == 'diagnostic-wrong-source': diagnostic['context']['source'] += 1
        if mode == 'diagnostic-timing-mismatch':
            diagnostic['timing'] = [{'source': diagnostic['context']['source'], 'source_position': 0,
                'repetition': 0, 'duration_s': 0.001, 'verified': False, 'evidence_kind': 'contract_fixture',
                'roi': evaluation['context']['roi'], 'basis': 'simulated', 'quantity': 'simulated_roi_seconds',
                'binary_sha256': evaluation['build']['binary_sha256'], 'output': '/fixture/log',
                'output_sha256': 'a' * 64}]
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
        if mode == 'diagnostic-unentered-time': values['regions'][0]['invocations'] = 0
        if mode == 'diagnostic-outside-roi':
            values['regions'][0].update(inclusive_ns=0, exclusive_ns=0, invocations=0)
        log.write_text('SWDB_DX100_ROI_SEALED\nSWDB_DX100_REGIONS ' + json.dumps(values) + '\n')
        if mode == 'diagnostic-preseal':
            log.write_text('SWDB_DX100_REGIONS ' + json.dumps(values) + '\nSWDB_DX100_ROI_SEALED\n')
        diagnostic['stages'] = [{'stage': 'simulation', 'state': 'complete', 'started': evaluation['stages'][0]['started'],
                                 'log': str(log), 'log_sha256': artifacts.file_hash(log)}]
        build = copy.deepcopy(diagnostic); build['id'] = 'diagnostic-build'
        build['outcome']['stage'] = 'candidate_build'
        build['context']['diagnostic'] = {'regions': rows, 'discovery': {'backend': 'libclang-cindex', 'unresolved': []},
            'instrumented_source': reference(path), 'runtime': reference(binary),
            'quantity': 'per-thread simulated elapsed, summed; includes waits', 'difference': 'explicit source-scope fixture instrumentation'}
        diagnostic['context']['execution_binding']['binary'] = reference(binary)
        diagnostic['context']['execution_binding_sha256'] = artifacts.digest(diagnostic['context']['execution_binding'])
        diagnostic['context']['verification_driver'] = reference(binary)
        diagnostic['context']['host_memory_observer'] = reference(binary)
        seal = {'format': 'swdb.dx100.roi-seal.v1', 'roi_exit_cause': 'm5_exit instruction encountered',
            'execution_binding_sha256': diagnostic['context']['execution_binding_sha256'],
            'driver_sha256': artifacts.file_hash(binary), 'host_memory_observer_sha256': artifacts.file_hash(binary),
            'statistics': diagnostic['context']['statistics'], 'verification': {'state': 'finished'}}
        seal_path = folder / 'diagnostic-seal.json'
        seal_path.write_text(json.dumps(seal))
        diagnostic['context']['sealed_roi'] = {**reference(seal_path), **seal}
        if mode == 'diagnostic-no-seal': diagnostic['context'].pop('sealed_roi')
        if mode == 'diagnostic-seal-tamper': seal_path.write_text('{}')
        if mode == 'diagnostic-seal-binding':
            seal['execution_binding_sha256'] = '0' * 64
            seal_path.write_text(json.dumps(seal))
            diagnostic['context']['sealed_roi'] = {**reference(seal_path), **seal}
        if mode == 'diagnostic-seal-list':
            seal_path.write_text('[]')
            diagnostic['context']['sealed_roi'].update(reference(seal_path))
        if mode in {'diagnostic-unverified', 'diagnostic-incorrect'}:
            diagnostic['outcome'] = {'state': 'missing_observation' if mode == 'diagnostic-unverified' else 'incorrect',
                                     'stage': 'simulation', 'reason': 'Retained verifier outcome after completed counters.'}
            diagnostic['correctness']['state'] = 'unverified' if mode == 'diagnostic-unverified' else 'failed'
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
                'diagnostic-report-list', 'diagnostic-counter-list', 'diagnostic-boolean-errors',
                'diagnostic-no-seal', 'diagnostic-seal-tamper', 'diagnostic-seal-binding', 'diagnostic-seal-list',
                'diagnostic-preseal', 'diagnostic-unentered-time', 'diagnostic-missing-trial',
                'diagnostic-wrong-position', 'diagnostic-wrong-repetition', 'diagnostic-timing-mismatch', 'diagnostic-wrong-source'}:
        assert profile["outcome"]["state"] == "failed"
        assert retrieved["timing"] == []
    else:
        assert profile["outcome"]["state"] == ('complete' if mode in {'diagnostic', 'diagnostic-unverified', 'diagnostic-incorrect'} else "partial")
        assert retrieved["timing"][0]["duration_s"] == 0.001
        assert profile["context"]["roi_observation"]["clocks"]["system.cpu_clk_domain"]["period_ticks"] == [313]
        assert profile["context"]["roi_observation"]["interval_count"] == (2 if mode == "multiple-intervals" else 1)
        if mode in {'diagnostic', 'diagnostic-unverified', 'diagnostic-incorrect'}:
            assert profile['regions'][0]['metrics']['inclusive_simulated_seconds'] == 300 / 1e9
            assert profile['regions'][0]['metrics']['exclusive_simulated_seconds'] == 100 / 1e9
            assert profile['executions'][1]['correctness']['state'] == ('failed' if mode == 'diagnostic-incorrect' else 'unverified')
            assert profile['executions'][1]['execution_outcome'] == diagnostic['outcome']
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


@pytest.mark.parametrize('field,value', [
    ('source', True), ('source_position', False), ('repetition', True),
    ('source', -1), ('source_position', -1), ('repetition', -1),
    ('source_position', 1.0), ('repetition', '1')])
def test_trial_identity_rejects_boolean_negative_or_coerced_coordinates(field, value):
    from swdb.cli import Failure
    from swdb.dx100_profile import _trial
    evaluation = {'context': {'source': 7, 'protocol_trial': {'source_position': 2, 'repetition': 1}}}
    target = evaluation['context'] if field == 'source' else evaluation['context']['protocol_trial']
    target[field] = value
    with pytest.raises(Failure, match='trial identity'):
        _trial(evaluation, require_explicit=True)


def test_legacy_discovery_trial_is_not_promoted_to_an_explicit_diagnostic_trial():
    from swdb.cli import Failure
    from swdb.dx100_profile import _trial
    evaluation = {'context': {'source': 7}}
    assert _trial(evaluation) == {'source': 7, 'source_position': 0, 'repetition': 0}
    with pytest.raises(Failure, match='explicit'):
        _trial(evaluation, require_explicit=True)
    assert 'protocol_trial' not in evaluation['context']
    evaluation['context']['protocol_trial'] = None
    with pytest.raises(Failure, match='explicit'):
        _trial(evaluation)
