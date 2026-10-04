"""Coverage driver contract fixtures only. Created: 2026-09-26 ET."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from scripts import bfs_dx100_coverage_execution as case
from swdb import artifacts, dx100_coverage
from swdb.store import Store


def write_ref(path, value):
    path.write_text(json.dumps(value) if not isinstance(value, str) else value)
    return case.reference(path)


def test_window_does_not_extend_a3_or_run_with_partial_outer_allowance():
    assert case.a3.DEADLINE.isoformat() == '2026-09-26T15:40:00-04:00'
    latest = case.DEADLINE - timedelta(seconds=3600)
    assert latest.isoformat() == '2026-09-26T15:45:00-04:00'
    assert case.launch_budget(latest) == 3570
    for value in (latest + timedelta(microseconds=1), latest.replace(tzinfo=None)):
        with pytest.raises(ValueError, match='complete 3600-second window'):
            case.launch_budget(value)


def test_real_public_registration_of_fixed_fixture_graph_and_fresh_get(records, tmp_path):
    records.copy_repo()
    # Fixture isolation only: the real a1 evidence is now in the copied catalog.
    # Remove its three temporary copies; canonical/host evidence stays untouched.
    for relative in (
        'evaluations/bfs-dx100-coverage-20260926-a1.compile.yaml',
        'evaluations/bfs-dx100-coverage-20260926-a1.execute.yaml',
        'workloads/bfs-dx100-coverage-20260926-a1.workload.241d37f1ee522c01.yaml',
    ):
        (records.path / relative).unlink(missing_ok=True)
    graph = case.graph_case.generate(tmp_path / 'synthetic-graph')
    request = case.registration_request(graph)
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(request))
    result = records.swdb('register-workload', path, '--format', 'json')
    assert result.returncode == 0, result.stderr
    workload = json.loads(result.stdout)
    assert workload['definition']['realized']['num_vertices'] == 8212
    assert workload['definition']['realized']['num_directed_edges'] == 147492
    assert workload['definition']['canonical_sha256'] == graph['canonical_sha256']
    fetched = records.swdb('get', workload['id'], '--format', 'json')
    assert json.loads(fetched.stdout) == workload
    assert workload['definition']['family'] == 'fixed_dx100_correctness_coverage'
    with pytest.raises(ValueError, match='record already exists'):
        case.fresh_paths(Store(records.path), tmp_path / 'runs', tmp_path / 'builds')


def compiled_fixture():
    return {'id': case.RUN_ID + '.compile', 'evidence_kind': 'execution',
        'outcome': {'state': 'complete', 'stage': 'candidate_build',
                    'reason': 'Identified candidate compiled; no simulated correctness or timing inferred.'},
        'candidate': case.CANDIDATE, 'context': {'candidate_sha256': case.SOURCE_SHA},
        'build': {'adapter': 'dx100.complete_call.v2', 'binary': '/fixture/bfs', 'binary_sha256': 'a'*64},
        'request': case.compile_request()}


def test_requests_use_fresh_original_graph_wrapper_and_fixed_bounds(tmp_path):
    graph = case.graph_case.generate(tmp_path / 'graph')
    workload = {'id': 'registered.fixture', 'requested_id': case.RUN_ID + '.workload',
                'definition': {'canonical_sha256': graph['canonical_sha256'], 'sources': [0]}}
    compiled = compiled_fixture()
    request = case.execution_request(compiled, workload, graph)
    assert request['candidate'] == case.CANDIDATE
    assert request['candidate_build'] == case.RUN_ID + '.compile'
    assert request['binary']['sha256'] == 'a'*64
    assert request['verification']['coverage'] is True
    assert request['configuration']['tile_elements'] == 16384
    assert request['budget'] == {'total_seconds': 3100, 'memory_gib': 48, 'storage_gib': 4,
                                  'checkpoint_seconds': 300, 'run_seconds': 2700}
    assert 'checkpoint_manifest' not in request
    assert compiled['request']['roi'] == 'bfs.complete_call.v1'
    assert compiled['request']['function'] == 'DOBFSMAA'
    for mutation in ('fixture', 'wrong_roi', 'legacy_wrapper', 'changed_source'):
        bad = deepcopy(compiled)
        if mutation == 'fixture': bad['evidence_kind'] = 'contract_fixture'
        if mutation == 'wrong_roi': bad['request']['roi'] = 'bfs.dx100.traversal.v1'
        if mutation == 'legacy_wrapper': bad['build']['adapter'] = 'dx100.complete_call.v1'
        if mutation == 'changed_source': bad['context']['candidate_sha256'] = 'f'*64
        with pytest.raises(ValueError, match='fresh exact author'):
            case.execution_request(bad, workload, graph)


def coverage_fixture(tmp_path):
    # Explicit synthetic trace: exercises parser/admission, never empirical proof.
    log = tmp_path / 'coverage.log'
    log.write_text('''110: system.maa: I[0] Start [INSTR[opcode(INDIR_ST_VECTOR) datatype(INT32) baseAddr(0x4000)]]
120: system.maa: I[0] recvData: 2 entries received for addr(0x8000), grow(x0) from T[0]!
121: system.maa: I[0] recvData: new_data[2] = SPD[0][0] = 7/7/0.0!
122: system.maa: I[0] recvData: new_data[2] = SPD[0][1] = 9/9/0.0!
125: system.maa: R[0] executeInstruction: my_idx_j: 16384, tile size: 16384
126: system.maa: R[0] executeInstruction: my_idx_j: 2048, tile size: 2048
130: system.maa: I[0] End [INSTR]
131: system.maa: S[0] End [INSTR]
132: system.maa: R[0] End [INSTR]
133: system.maa: A[0] End [INSTR]
SWDB_BFS_PARENT_STORAGE address=4000 count=8212 element_bytes=4
''')
    stats = write_ref(tmp_path / 'stats', 'Begin Simulation Statistics\nsimTicks 100\nfinalTick 200\nsystem.maa.numInst 4\nEnd Simulation Statistics\n')
    observed = dx100_coverage.observe(log, {'simTicks': '100', 'finalTick': '200'}, 16384)
    graph = case.graph_case.generate(tmp_path / 'graph')
    request = {'id': case.RUN_ID + '.execute',
        'binary': write_ref(tmp_path / 'binary', 'fixture compiled binary'),
        'simulator': write_ref(tmp_path / 'simulator', 'fixture simulator'),
        'workload': {'source': 0, 'representation': {key: graph['representation'][key] for key in ('path', 'sha256')}}}
    data = {'id': request['id'], 'request': request, 'evidence_kind': 'execution', 'gain_claim': False,
        'context': {'statistics': stats}, 'correctness': {'checks': [{'graph_sha256': graph['canonical_sha256'],
            'source': 0, 'parent_results': [{'vertices': 8212, 'parent_count': 8212}],
            'output': case.reference(log), 'coverage': {**observed, 'accelerator_executed': True}}]}}
    return data, request, graph, log


def test_coverage_reopens_actual_trace_and_requires_all_cases(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(case.dx100_witness, 'validate_completed_witness',
        lambda result, **kw: calls.append(kw))
    data, request, graph, log = coverage_fixture(tmp_path)
    assert case.validate_coverage(data, request, graph)['full_tiles']['count'] == 1
    assert calls == [{'verify_artifacts': True}]
    original = log.read_text()
    for missing in ('tile size: 16384', 'tile size: 2048', 'new_data[2] = SPD[0][1]'):
        log.write_text('\n'.join(line for line in original.splitlines() if missing not in line) + '\n')
        bad = deepcopy(data)
        bad['correctness']['checks'][0]['output'] = case.reference(log)
        # Reseal the summary consistently; coverage still must be observed.
        observed = dx100_coverage.observe(log, {'simTicks': '100', 'finalTick': '200'}, 16384)
        bad['correctness']['checks'][0]['coverage'] = {**observed, 'accelerator_executed': True}
        with pytest.raises(ValueError, match='coverage is incomplete'):
            case.validate_coverage(bad, request, graph)
    log.write_text(original)
    bad = deepcopy(data)
    bad['correctness']['checks'][0]['coverage']['full_tiles']['count'] += 1
    with pytest.raises(ValueError, match='reopened raw trace'):
        case.validate_coverage(bad, request, graph)


def test_witness_failure_cannot_be_overridden_by_complete_coverage(tmp_path, monkeypatch):
    data, request, graph, _ = coverage_fixture(tmp_path)
    def reject(*args, **kwargs):
        raise ValueError('protected original-adjacency verification failed')
    monkeypatch.setattr(case.dx100_witness, 'validate_completed_witness', reject)
    with pytest.raises(ValueError, match='original-adjacency'):
        case.validate_coverage(data, request, graph)


@pytest.mark.parametrize('changed', ['binary', 'simulator', 'graph', 'reidentified_graph'])
def test_coverage_reopens_binary_simulator_and_prospective_graph(tmp_path, monkeypatch, changed):
    data, request, graph, _ = coverage_fixture(tmp_path)
    monkeypatch.setattr(case.dx100_witness, 'validate_completed_witness', lambda *a, **kw: None)
    if changed in ('binary', 'simulator'):
        Path(request[changed]['path']).write_text('changed fixture bytes')
    elif changed == 'graph':
        Path(graph['representation']['path']).write_bytes(b'changed graph bytes')
    else:
        # A different valid graph, consistently reidentified throughout the receipt,
        # must still fail the prospectively fixed topology rather than its old hash.
        import struct
        path = Path(graph['representation']['path'])
        path.write_bytes(struct.pack('<Biiiiii', 0, 2, 2, 0, 1, 2, 1) + struct.pack('<i', 0))
        graph['representation']['sha256'] = artifacts.file_hash(path)
        graph['canonical_sha256'] = artifacts.digest(case.bfs_protocol._canonical(case.bfs_protocol._sg_graph(path.read_bytes(), 4)))
        request['workload']['representation']['sha256'] = graph['representation']['sha256']
        data['correctness']['checks'][0]['graph_sha256'] = graph['canonical_sha256']
    with pytest.raises(ValueError, match='bytes differ|hash changed|fixed topology'):
        case.validate_coverage(data, request, graph)


@pytest.mark.parametrize('path_kind', ['driver', 'build', 'broken_symlink'])
def test_old_attempts_are_never_overwritten(tmp_path, path_kind):
    runs, builds = tmp_path / 'runs', tmp_path / 'builds'
    runs.mkdir(); builds.mkdir()
    path = builds / (case.RUN_ID + '.compile') if path_kind == 'build' else runs / case.RUN_ID
    if path_kind == 'broken_symlink': path.symlink_to(tmp_path / 'absent')
    else: path.write_text('retained failure')
    with pytest.raises(ValueError, match='no retry/overwrite'):
        case.fresh_paths(SimpleNamespace(records=[]), runs, builds)
    assert path.is_symlink() or path.read_text() == 'retained failure'


def a3_fixture(tmp_path):
    evaluation = {'id': case.a3.PROBE_ID, 'evidence_kind': 'execution',
                  'request': case.yamlio.load(case.a3.REQUEST)}
    driver = {'id': case.a3.PROBE_ID, 'state': 'complete', 'evaluation_sha256': artifacts.digest(evaluation),
              'started': '2026-09-26T15:00:01-04:00', 'finished': '2026-09-26T15:01:00-04:00', 'host_wall_s': 59,
              'outer_seconds': case.a3.OUTER_SECONDS, 'cleanup_reserve_seconds': case.a3.CLEANUP_SECONDS,
              'deadline_et': case.a3.DEADLINE.isoformat(), 'runtime_sha256': case.a3.RUNTIME,
              'repository_commit': case.A3_COMMIT,
              'lane': 'mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 321)',
              'request': {**write_ref(tmp_path / 'a3-request.json', evaluation['request']), 'canonical_sha256': case.a3.REQUEST_SHA256},
              'stages': [{'state': 'complete', 'returncode': 0}]}
    lane = {'socket_lane': {'host': 'mbit10', 'node': 0, 'lease_name': 'mbit10-evaluation-node0',
        'lease_generation': 321, 'exit_code': 0, 'started_utc': '2026-09-26T19:00:00Z', 'ended_utc': '2026-09-26T19:01:01Z'}}
    audit = {'id': case.a3.PROBE_ID, 'state': 'passed', 'observed_at': '2026-09-26T15:02:00-04:00',
        'evaluation': write_ref(tmp_path / 'evaluation.json', evaluation), 'evaluation_sha256': artifacts.digest(evaluation),
        'driver': write_ref(tmp_path / 'driver.json', driver), 'lane': write_ref(tmp_path / 'lane.json', lane),
        'driver_exit': write_ref(tmp_path / 'driver-exit', '0\n'), 'observer_exit': write_ref(tmp_path / 'observer-exit', '0\n'),
        'outer_exit': write_ref(tmp_path / 'exit', '0\n'), 'cleanup_state': 'terminal_and_reaped',
        'owned_processes_absent': True, 'owned_processes': [{'pid': 101, 'start_ticks': 300}, {'pid': 102, 'start_ticks': 301}],
        'process_observations': write_ref(tmp_path / 'identities.json', {'driver_pid': 101,
            'state': 'driver_terminated', 'sampling_complete': True, 'cleanup_verified': False,
            'driver_identity': {'pid': 101, 'start_ticks': 300}, 'observer_identity': {'pid': 102, 'start_ticks': 301},
            'pane_pid': 101, 'launcher_identity': {'pid': 101, 'start_ticks': 300},
            'ancestry': [{'pid': 101, 'start_ticks': 300}], 'owned_processes': [{'pid': 101, 'start_ticks': 300}],
            'resource_samples': write_ref(tmp_path / 'samples.jsonl', {'processes': [
                {'pid': 101, 'start_ticks': 300}, {'pid': 102, 'start_ticks': 301}]})}),
        'lease_snapshot': write_ref(tmp_path / 'lease.json', {'state': 'released',
            'lease': {'generation': 321, 'lease_name': 'mbit10-evaluation-node0'}, 'released_at': '2026-09-26T19:01:02Z'})}
    store = SimpleNamespace(get=lambda rid, kind: evaluation)
    proc = tmp_path / 'proc'; proc.mkdir()
    return audit, store, proc


def test_a3_requires_passed_bound_actual_result_and_terminal_owned_processes(tmp_path, monkeypatch):
    audit, store, proc = a3_fixture(tmp_path)
    calls = []
    monkeypatch.setattr(case.dx100_witness, 'validate_completed_witness', lambda *a, **kw: calls.append(kw))
    current = case.a3.stamp('2026-09-26T15:10:00-04:00')
    ref = write_ref(tmp_path / 'audit.json', audit)
    assert case.validate_a3(ref, store, current, proc)['evaluation_sha256'] == audit['evaluation_sha256']
    assert calls == [{'verify_artifacts': True}]
    for mutation in ('failed', 'omit_sampled_pid', 'bad_lease', 'bad_digest', 'future', 'active_stage'):
        bad = deepcopy(audit)
        if mutation == 'failed': bad['state'] = 'failed'
        if mutation == 'omit_sampled_pid': bad['owned_processes'] = bad['owned_processes'][:1]
        if mutation == 'bad_lease': bad['lease_snapshot'] = write_ref(tmp_path / 'held.json', {'state': 'held'})
        if mutation == 'bad_digest': bad['evaluation_sha256'] = 'f'*64
        if mutation == 'future': bad['observed_at'] = '2026-09-26T17:00:00-04:00'
        if mutation == 'active_stage':
            driver = json.loads(Path(bad['driver']['path']).read_text())
            driver['stages'][0]['state'] = 'running'
            bad['driver'] = write_ref(tmp_path / 'active-driver.json', driver)
        ref = write_ref(tmp_path / 'audit.json', bad)
        with pytest.raises(ValueError): case.validate_a3(ref, store, current, proc)
    fields = ['S', '1'] + ['0']*17 + ['300', '0', '1']
    (proc / '101').mkdir(); (proc / '101/stat').write_text('101 (fixture) ' + ' '.join(fields))
    with pytest.raises(ValueError, match='still exists'):
        case.validate_a3(write_ref(tmp_path / 'audit.json', audit), store, current, proc)


@pytest.mark.parametrize('changed', ['late_start', 'wall_duration', 'runtime', 'request', 'bounds', 'commit'])
def test_a3_resealed_receipt_preserves_prospective_window_runtime_and_request(tmp_path, monkeypatch, changed):
    audit, store, proc = a3_fixture(tmp_path)
    monkeypatch.setattr(case.dx100_witness, 'validate_completed_witness', lambda *a, **kw: None)
    driver = json.loads(Path(audit['driver']['path']).read_text())
    if changed == 'late_start':
        driver.update(started='2026-09-26T15:25:00-04:00', finished='2026-09-26T15:26:00-04:00', host_wall_s=60)
        lane = json.loads(Path(audit['lane']['path']).read_text())
        lane['socket_lane'].update(started_utc='2026-09-26T19:25:00Z', ended_utc='2026-09-26T19:26:01Z')
        audit['lane'] = write_ref(tmp_path / 'resealed-lane.json', lane)
    elif changed == 'wall_duration': driver['host_wall_s'] = 2
    elif changed == 'runtime': driver['runtime_sha256']['swdb/dx100_witness.py'] = 'f'*64
    elif changed == 'bounds': driver['outer_seconds'] = 1300
    elif changed == 'commit': driver['repository_commit'] = 'f'*40
    else:
        request = deepcopy(store.get(case.a3.PROBE_ID, 'evaluation')['request'])
        request['verification']['max_ticks'] += 1
        driver['request'] = {**write_ref(tmp_path / 'changed-request.json', request), 'canonical_sha256': case.a3.REQUEST_SHA256}
    audit['observed_at'] = '2026-09-26T15:30:00-04:00'
    audit['driver'] = write_ref(tmp_path / 'resealed-driver.json', driver)
    with pytest.raises(ValueError, match='latest launch|duration|runtime|request'):
        case.validate_a3(write_ref(tmp_path / 'audit.json', audit), store, case.a3.stamp('2026-09-26T15:35:00-04:00'), proc)


@pytest.mark.parametrize('name', ['driver_exit', 'observer_exit'])
@pytest.mark.parametrize('value', [None, '1\n'])
def test_a3_requires_both_successful_exit_receipts(tmp_path, monkeypatch, name, value):
    audit, store, proc = a3_fixture(tmp_path)
    monkeypatch.setattr(case.dx100_witness, 'validate_completed_witness', lambda *a, **kw: None)
    if value is None:
        audit.pop(name)
    else:
        audit[name] = write_ref(tmp_path / ('changed-' + name), value)
    with pytest.raises(ValueError, match='both retain successful exit'):
        case.validate_a3(write_ref(tmp_path / 'audit.json', audit), store,
                         case.a3.stamp('2026-09-26T15:10:00-04:00'), proc)


def test_runtime_uses_prospective_git_bytes_not_new_live_hashes(tmp_path, monkeypatch):
    # Local throwaway Git repository; no project commit or external transfer.
    runtime = tmp_path / 'runtime.py'; runtime.write_text('# fixture runtime\n')
    def git(*args):
        return subprocess.check_output(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', *args], cwd=tmp_path, text=True)
    git('init', '-q'); git('add', 'runtime.py'); git('commit', '-qm', 'fixture')
    commit = git('rev-parse', 'HEAD').strip()
    monkeypatch.setattr(case, 'RUNTIME_FILES', ('runtime.py',))
    assert case.validate_runtime(commit, tmp_path)['runtime.py']['sha256'] == artifacts.file_hash(runtime)
    runtime.write_text('# changed after prospective pin\n')
    with pytest.raises(ValueError, match='runtime differs'):
        case.validate_runtime(commit, tmp_path)
    with pytest.raises(ValueError, match='prospective commit'):
        case.validate_runtime('f'*40, tmp_path)


def test_active_other_or_legacy_lease_blocks_coverage(tmp_path):
    for name in ('mbit10-evaluation-node1', 'mbit10-evaluation'):
        write_ref(tmp_path / (name + '.meta.json'), {'state': 'released'})
    case.require_other_leases_idle(tmp_path)
    write_ref(tmp_path / 'mbit10-evaluation.meta.json', {'state': 'held'})
    with pytest.raises(ValueError, match='legacy lease'):
        case.require_other_leases_idle(tmp_path)


def completed_coverage_fixture(tmp_path, monkeypatch):
    """Synthetic run packet; real file hashes/parsers/Git pins, no guest execution."""
    raw = tmp_path / 'raw'; folder = raw / case.RUN_ID; folder.mkdir(parents=True)
    root = tmp_path / 'checkout'; root.mkdir()
    for name in case.RUNTIME_FILES:
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((case.ROOT / name).read_bytes())
    def git(*args):
        return subprocess.check_output(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', *args], cwd=root, text=True)
    git('init', '-q'); git('add', 'scripts', 'swdb'); git('commit', '-qm', 'fixture runtime')
    commit = git('rev-parse', 'HEAD').strip()
    data, _, graph, _ = coverage_fixture(folder)
    template = case.yamlio.load(case.a3.REQUEST)
    template['simulator'] = case.reference(folder / 'simulator')
    template_path = tmp_path / 'template.json'; write_ref(template_path, template)
    monkeypatch.setattr(case.a3, 'REQUEST', template_path)
    compiled = compiled_fixture()
    compiled['build'].update(binary=str(folder / 'binary'), binary_sha256=artifacts.file_hash(folder / 'binary'))
    workload = {'id': 'fixture.registered', 'requested_id': case.RUN_ID + '.workload',
                'definition': {'canonical_sha256': graph['canonical_sha256'], 'sources': [0]}}
    request = case.execution_request(compiled, workload, graph)
    data['request'] = request
    driver = {'id': case.RUN_ID, 'state': 'complete', 'started': '2026-09-26T15:00:00-04:00',
        'finished': '2026-09-26T15:00:10-04:00', 'host_wall_s': 10, 'deadline_et': case.DEADLINE.isoformat(),
        'bounds': case.BOUNDS, 'repository_commit': commit, 'gain_claim': False, 'profiling': False,
        'automatic_retry_allowed': False, 'driver_pid': 101, 'graph': graph,
        'final_accounting': {'observed_at': '2026-09-26T15:00:10-04:00', 'elapsed_seconds': 10,
            'artifact_bytes': 1000000, 'raw_free_bytes': 40*1024**3, 'build_free_bytes': 20*1024**3},
        'lane': 'mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 322)',
        'runtime': {name: case.reference(root / name) for name in case.RUNTIME_FILES},
        'prerequisites': {key: {'audit': {'fixture': key}} for key in ('a3', 'paired', 'provider')},
        'evaluation': data['id'], 'evaluation_sha256': artifacts.digest(data),
        'coverage': dx100_coverage.observe(folder / 'coverage.log', {'simTicks': '100', 'finalTick': '200'}, 16384)}
    processes = [{'pid': 101, 'parent_pid': 104, 'start_ticks': 300, 'rss_bytes': 100},
                 {'pid': 102, 'parent_pid': 101, 'start_ticks': 301, 'rss_bytes': 100}]
    samples = []
    for second in (0, 5, 10):
        stamp = f'2026-09-26T15:00:{second:02d}-04:00'
        samples.append({'sampled_at': stamp, 'guard_started': stamp, 'guard_finished': stamp, 'guard_seconds': 0,
            'rss_bytes': 200, 'artifact_bytes': 200, 'raw_free_bytes': 40*1024**3, 'build_free_bytes': 20*1024**3,
            'lane': driver['lane'], 'processes': processes})
    driver['rss'] = {'sampled_peak_bytes': 200, 'samples': write_ref(folder / 'rss-samples.jsonl',
        '\n'.join(json.dumps(row) for row in samples)+'\n')}
    driver['artifact_peak_bytes'] = 200
    identity = {'pid': 101, 'start_ticks': 300}; pane = {'pid': 104, 'start_ticks': 304}
    observations = {'driver_pid': 101, 'pane_pid': 104, 'driver_identity': identity,
        'observer_identity': identity, 'observer_kind': 'in_process_driver', 'launcher_identity': pane,
        'state': 'driver_sampling_finished', 'sampling_complete': True, 'cleanup_verified': False,
        'ancestry': [identity, pane], 'owned_processes': processes, 'resource_samples': driver['rss']['samples']}
    driver['process_observations'] = write_ref(folder / 'process-observations.json', observations)
    inputs = {'node': '\n'.join(f'Node 0 {key}: {value} kB' for key, value in {
        'MemFree': 60*1024**2, 'Active(file)': 0, 'Inactive(file)': 0, 'Dirty': 0, 'Writeback': 0, 'SReclaimable': 0}.items()),
        'zones': 'Node 0, zone Normal\n low 0\n high 0\n managed 20000000\n protection: (0)\n',
        'global': f'MemAvailable: {80*1024**2} kB\n'}
    capacity = case.dx100_capacity.capacity(inputs['node'], inputs['zones'], inputs['global'], 0, 4096)
    capacity_ref = write_ref(folder / 'capacity.json', {'format': 'swdb.dx100.capacity.v1', 'observed': samples[0]['sampled_at'],
        'observer_sha256': driver['runtime']['scripts/dx100_capacity.py']['sha256'], 'inputs': inputs,
        'result': capacity, 'evidence_kind': 'execution'})
    requests = {'register-workload': case.registration_request(graph), 'dx100-compile': case.compile_request(), 'dx100-execute': request}
    driver['requests'] = {name: write_ref(folder / (name+'.request.json'), value) for name, value in requests.items()}
    outputs = {'capacity': {**capacity_ref, 'result': capacity}, 'generate': graph, 'register-workload': workload,
               'dx100-compile': compiled, 'dx100-execute': data, 'fresh-get': data}
    python = '/fixture/python3'
    driver['stages'] = []
    for name, value in outputs.items():
        out = write_ref(folder / (name+'.stdout'), value)
        err = write_ref(folder / (name+'.stderr'), '')
        if name == 'capacity': command = [python, str(root / 'scripts/dx100_capacity.py'), '--node', '0', '--output', str(folder / 'capacity.json')]
        elif name == 'generate': command = [python, str(root / 'scripts/bfs_dx100_coverage_graph.py'), '--output-directory', str(folder / 'graph'), '--records', str(root / 'records'), '--lane', 'mbit10-evaluation-node0']
        elif name == 'fresh-get': command = [python, '-m', 'swdb', 'get', data['id'], '--records', str(root / 'records'), '--format', 'json']
        else: command = [python, '-m', 'swdb', name, driver['requests'][name]['path'], '--records', str(root / 'records'), *(['--runs-dir', str(folder), '--lane', '0'] if name.startswith('dx100-') else []), '--format', 'json']
        driver['stages'].append({'command': command, 'output': out['path'], 'stdout_sha256': out['sha256'],
            'stderr': err['path'], 'stderr_sha256': err['sha256'], 'state': 'complete', 'returncode': 0,
            'host_wall_s': .1, 'timeout_s': 1})
    audit = {'id': case.RUN_ID, 'state': 'passed', 'observed_at': '2026-09-26T15:01:00-04:00',
        'evaluation': write_ref(folder / 'evaluation.json', data), 'evaluation_sha256': artifacts.digest(data),
        'driver': write_ref(folder / 'driver.json', driver), 'process_observations': driver['process_observations'],
        'lane': write_ref(folder / 'lane.json', {'socket_lane': {'host': 'mbit10', 'node': 0,
            'lease_name': 'mbit10-evaluation-node0', 'lease_generation': 322, 'exit_code': 0,
            'started_utc': '2026-09-26T19:00:00Z', 'ended_utc': '2026-09-26T19:00:11Z'}}),
        'outer_exit': write_ref(folder / 'exit', '0\n'), 'cleanup_state': 'terminal_and_reaped', 'owned_processes_absent': True,
        'owned_processes': processes+[pane], 'lease_snapshot': write_ref(folder / 'lease.json', {'state': 'released',
            'lease': {'generation': 322, 'lease_name': 'mbit10-evaluation-node0'}, 'released_at': '2026-09-26T19:00:12Z'})}
    store = SimpleNamespace(get=lambda rid, kind: {data['id']: data, compiled['id']: compiled, workload['id']: workload}[rid])
    monkeypatch.setattr(case, 'ROOT', root); monkeypatch.setattr(case, 'RAW_ROOT', raw)
    # These prerequisites are independently exercised above; this packet exercises
    # the new reader's actual raw file/graph/trace/resource/stage/terminal bindings.
    monkeypatch.setattr(case, 'validate_a3', lambda *a, **kw: {})
    monkeypatch.setattr(case.a3, 'validate_completion', lambda *a, **kw: {})
    monkeypatch.setattr(case, 'validate_source', lambda *a: {})
    monkeypatch.setattr(case.dx100_witness, 'validate_completed_witness', lambda *a, **kw: None)
    proc = tmp_path / 'proc'; proc.mkdir()
    return audit, driver, store, proc, commit


def test_completed_coverage_reopens_complete_fixture_packet(tmp_path, monkeypatch):
    audit, driver, store, proc, commit = completed_coverage_fixture(tmp_path, monkeypatch)
    result = case.validate_completed(write_ref(tmp_path / 'audit.json', audit), store,
        case.a3.stamp('2026-09-26T15:02:00-04:00'), commit, proc)
    assert result['coverage']['full_tiles']['count'] == 1
    assert result['evaluation_sha256'] == audit['evaluation_sha256']


@pytest.mark.parametrize('changed', ['commit', 'stage', 'request', 'gap', 'rss', 'ownership', 'omitted_pid', 'capacity', 'extra_attempt'])
def test_completed_coverage_rejects_resealed_admission_gaps(tmp_path, monkeypatch, changed):
    audit, driver, store, proc, commit = completed_coverage_fixture(tmp_path, monkeypatch)
    if changed == 'commit': driver['repository_commit'] = 'f'*40
    elif changed == 'stage': driver['stages'][4]['command'][3] = 'different-command'
    elif changed == 'request':
        ref = driver['requests']['dx100-execute']; request = json.loads(Path(ref['path']).read_text())
        request['budget']['run_seconds'] += 1
        driver['requests']['dx100-execute'] = write_ref(Path(ref['path']), request)
    elif changed in ('gap', 'rss', 'ownership'):
        ref = driver['rss']['samples']; rows = [json.loads(line) for line in Path(ref['path']).read_text().splitlines()]
        if changed == 'gap': rows[1]['sampled_at'] = '2026-09-26T15:02:00-04:00'
        if changed == 'rss': rows[1]['rss_bytes'] += 1
        if changed == 'ownership': rows[0]['processes'][1]['parent_pid'] = 999
        driver['rss']['samples'] = write_ref(Path(ref['path']), '\n'.join(json.dumps(row) for row in rows)+'\n')
    elif changed == 'omitted_pid': audit['owned_processes'] = [p for p in audit['owned_processes'] if p['pid'] != 102]
    elif changed == 'capacity':
        row = driver['stages'][0]; data = json.loads(Path(row['output']).read_text())
        data['result']['eligible'] = False
        row['stdout_sha256'] = write_ref(Path(row['output']), data)['sha256']
    else: driver['stages'].append(deepcopy(driver['stages'][4]))
    audit['driver'] = write_ref(Path(audit['driver']['path']), driver)
    with pytest.raises(ValueError):
        case.validate_completed(write_ref(tmp_path / 'audit.json', audit), store,
            case.a3.stamp('2026-09-26T15:02:00-04:00'), commit, proc)


@pytest.mark.parametrize('fault', [None, 'sample_hash', 'observation_hash', 'last_write_time', 'last_write_absolute', 'last_write_storage'])
def test_coverage_final_hashes_and_last_write_remain_inside_original_bounds(tmp_path, monkeypatch, fault):
    folder = tmp_path / 'run'; folder.mkdir()
    (folder / 'rss-samples.jsonl').write_text('{}\n')
    receipt = {'state': 'complete', 'rss': {}}
    observations = {'cleanup_verified': False}
    clock, raw, absolute, writes = [0], [1000], [False], []
    original_hash, original_save = case.artifacts.file_hash, case.save_receipt
    def file_hash(path):
        result = original_hash(path)
        if fault == 'sample_hash' and Path(path).name == 'rss-samples.jsonl': clock[0] = 51
        if fault == 'observation_hash' and Path(path).name == 'process-observations.json': clock[0] = 51
        return result
    def save(folder, value):
        original_save(folder, value); writes.append(value['state'])
        if len(writes) == 2:
            if fault == 'last_write_time': clock[0] = 51
            if fault == 'last_write_absolute': absolute[0] = True
            if fault == 'last_write_storage': raw[0] = case.BOUNDS['artifact_bytes'] + 1
    monkeypatch.setattr(case.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(case, 'now', lambda: case.DEADLINE + timedelta(seconds=1) if absolute[0]
                        else case.DEADLINE - timedelta(seconds=100-clock[0]))
    monkeypatch.setattr(case.artifacts, 'file_hash', file_hash)
    monkeypatch.setattr(case, 'save_receipt', save)
    monkeypatch.setattr(case, 'artifact_bytes', lambda _: raw[0])
    monkeypatch.setattr(case.os, 'statvfs', lambda _: SimpleNamespace(f_bavail=100*1024**3, f_frsize=1))
    if fault:
        with pytest.raises(ValueError, match='fixed deadline|retained storage'):
            case.finalize_receipt(receipt, folder, 0, 50, observations, {101: 300})
        saved = json.loads((folder / 'driver.json').read_text())
        observed = json.loads((folder / 'process-observations.json').read_text())
        assert saved['state'] == writes[-1] == 'failed'
        assert observed['state'] == 'failed' and observed['sampling_complete'] is False
    else:
        case.finalize_receipt(receipt, folder, 0, 50, observations, {101: 300})
        saved = json.loads((folder / 'driver.json').read_text())
        assert saved['state'] == 'complete' and saved['final_accounting']['artifact_bytes'] == 1000
        assert saved['process_observations']['sha256'] == original_hash(folder / 'process-observations.json')
