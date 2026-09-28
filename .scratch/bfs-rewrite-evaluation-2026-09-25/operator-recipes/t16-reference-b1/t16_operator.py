#!/usr/bin/env python3
"""T16 reference b1 operator: probe, setup, Linux tests, admission, launch. Created 2026-09-27 ET.

Runs from the immutable runtime checkout that contains it. It reuses the T15
pilot operator shape (one socket_lane.sh job, one batch driver per series, one
gem5 slot) for the T16 reference kind under resume decisions R10-R12. The R12
probe is a separate short lane job that must pass before the protocols that
use the atomic verifier continuation are frozen. No failed ID is resumed;
every mode refuses to overwrite existing output.
"""
import argparse
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
OPERATOR_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/t15-pilot-b1'))
import pilot_operator as pilot  # noqa: E402  (reviewed helpers: environment, refs, host, commit)
from scripts import bfs_simulator_batch as batch  # noqa: E402
from scripts import bfs_owned_execution as own  # noqa: E402
from swdb import artifacts  # noqa: E402
from swdb.store import Store  # noqa: E402

KIND = batch.T16_KIND  # 2026-09-28: main() selects the job (b1, m, s1, s2)
JOBS = {'b1': batch.T16_KIND, **{kind.rsplit('-', 1)[1]: kind for kind in batch.T16_SPLIT}}
PROBE_ID = 'bfs-t16-r12-probe-20260927-b1'
PROBE_WORKLOAD = 'bfs-20260925-kronecker14.d03827828666f7dd'
PROBE_CASES = {
    'maa': ('bfs-author-maa-compile-20260925-a1.candidate', 'bfs_maa',
            {'mode': 'MAA', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384}),
    'scalar': ('bfs-author-scalar-compile-20260925-a1.candidate', 'bfs',
               {'mode': 'BASE', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384})}
# gem5 statistics that describe the host process, not the modeled machine.
HOST_STATS = ('hostSeconds', 'hostTickRate', 'hostMemory', 'hostInstRate', 'hostOpRate')
require, sha, ref, write, host, commit = pilot.require, pilot.sha, pilot.ref, pilot.write, pilot.host, pilot.commit


def plan():
    value = json.loads(batch.plan_path(KIND).read_text())
    batch.validate_plan(value, KIND)
    return value


def roots(value):
    top, lane = batch.pilot_storage_paths(value)
    return top, lane, {row['id'][len(value['id']) + 1:]: top/row['id'] for row in value['series']}


def lane_node():
    """The socket_lane.sh helper exports its lane; refuse anything unconfined."""
    require(os.environ.get('LACT_SOCKET_LANE_PID'), 'must run inside socket_lane.sh')
    name = os.environ.get('LACT_LEASE_NAME', '')
    require(name in {'mbit10-evaluation-node0', 'mbit10-evaluation-node1'}, 'lane helper did not export its socket lease')
    return int(name[-1])


def _stats(path):
    """Modeled statistics only; host counters and blank/banner lines excluded."""
    rows = []
    for line in Path(path).read_text().splitlines():
        name = line.split(None, 1)[0] if line.strip() else ''
        if name and not name.startswith('-') and name not in HOST_STATS:
            rows.append(line.split('#', 1)[0].rstrip())
    return rows


def probe():
    """R12 lane proof: same checkpoint, O3 versus atomic verifier continuation (kron14)."""
    host(); node = lane_node()
    folder = pilot.BASE / PROBE_ID
    require(not folder.exists(), 'probe output exists; fresh ID required')
    folder.mkdir(); (folder/'requests').mkdir(); (folder/'runs').mkdir()
    records = folder/'records'
    shutil.copytree(ROOT/'records', records)
    code = commit()
    store = Store(records)
    model = store.get('bfs-dx100-build-20260925-a2')
    binaries = {Path(row['path']).name: row for row in model['build']['details']['binaries']}
    from swdb import bfs_protocol
    workload = store.get(PROBE_WORKLOAD)
    summary = {'format': 'swdb.bfs.t16-r12-probe.v1', 'created': '2026-09-27', 'id': PROBE_ID,
               'code_commit': code, 'runtime_sha256': artifacts.digest(batch.runtime_identity()),
               'lane_node': node, 'workload': PROBE_WORKLOAD, 'source': workload['definition']['sources'][0],
               'started': batch.now().isoformat(), 'cases': {}, 'evidence_kind': 'execution',
               'scope': 'R12 feasibility probe; not T16 reference evidence'}
    for mode, (candidate_id, binary, configuration) in PROBE_CASES.items():
        candidate = store.get(candidate_id)
        source = store.get(candidate['source_snapshot'])
        graph = bfs_protocol.workload_representation(store, PROBE_WORKLOAD, source['application'])['representation']
        results, manifest = {}, None
        for variant in ('o3', 'atomic'):
            rid = f'{PROBE_ID}.{mode}.{variant}'
            payload = {'message_version': '1.0', 'id': rid, 'machine': 'mbit10', 'hardware_target': 'dx100-e4fc4af-4c',
                'model_root': model['context']['model_root'], 'build_evaluation': model['id'], 'candidate': candidate_id,
                'binary': {key: binaries[binary][key] for key in ('path', 'sha256')},
                'simulator': {key: binaries['gem5.opt'][key] for key in ('path', 'sha256')},
                'workload': {'id': PROBE_WORKLOAD, 'source': summary['source'],
                             'representation': {key: graph[key] for key in ('path', 'sha256')}},
                'protocol_trial': {'source_position': 0, 'repetition': 0 if variant == 'o3' else 1},
                'configuration': configuration,
                'verification': {'checker': 'dx100.bfs.verifier.v2', 'max_ticks': 10**14, 'coverage': mode == 'maa',
                                 'post_roi_trace': 'SyscallBase', 'trace_transport': 'gem5-gzip.v1'},
                'budget': {'total_seconds': 3600, 'checkpoint_seconds': 1200, 'run_seconds': 2300,
                           'memory_gib': 48, 'storage_gib': 4}}
            if variant == 'atomic':
                payload['verification']['post_roi_cpu'] = 'AtomicSimpleCPU'
                payload['checkpoint_manifest'] = manifest
            path = folder/'requests'/(rid + '.json'); write(path, payload)
            command = [sys.executable, '-m', 'swdb', 'dx100-execute', str(path), '--records', str(records),
                       '--db', str(folder/'swdb.sqlite'), '--format', 'json', '--runs-dir', str(folder/'runs'),
                       '--lane', str(node)]
            started = batch.now()
            with (folder/(rid + '.stdout')).open('x') as out, (folder/(rid + '.stderr')).open('x') as err:
                code_ = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err, timeout=3700,
                                       env=pilot.environment()).returncode
            result = json.loads((folder/(rid + '.stdout')).read_text() or '{}')
            stages = {row.get('stage'): row for row in result.get('stages', [])}
            seal = result.get('context', {}).get('sealed_roi', {})
            results[variant] = {'returncode': code_, 'started': started.isoformat(), 'finished': batch.now().isoformat(),
                'outcome': result.get('outcome'), 'correctness': result.get('correctness', {}).get('state'),
                'verdicts': (result.get('correctness', {}).get('checks') or [{}])[0].get('observed_verdicts'),
                'simulation_host_wall_s': stages.get('simulation', {}).get('host_wall_s'),
                'continuation': seal.get('verification'), 'roi_stats': seal.get('statistics')}
            if variant == 'o3':
                manifest = result.get('context', {}).get('checkpoint_manifest')
                require(manifest, 'O3 probe produced no checkpoint manifest; stopping')
        o3, atomic = results['o3'], results['atomic']
        same = None
        if o3['roi_stats'] and atomic['roi_stats']:
            same = _stats(o3['roi_stats']['path']) == _stats(atomic['roi_stats']['path'])
        o3_cont, atomic_cont = o3['continuation'] or {}, atomic['continuation'] or {}
        summary['cases'][mode] = {'runs': results, 'modeled_roi_statistics_identical': same,
            'both_passed': o3['correctness'] == atomic['correctness'] == 'passed',
            'verification_host_seconds': {variant: row['simulation_host_wall_s'] for variant, row in results.items()},
            'continuation_simulated_ticks': {'o3': o3_cont.get('simulated_ticks'), 'atomic': atomic_cont.get('simulated_ticks')},
            'atomic_switch': atomic_cont.get('post_roi_cpu')}
    summary['finished'] = batch.now().isoformat()
    summary['passed'] = all(case['modeled_roi_statistics_identical'] and case['both_passed']
                            and case['atomic_switch'] for case in summary['cases'].values())
    write(folder/'summary.json', summary)
    print(json.dumps(ref(folder/'summary.json')))
    raise SystemExit(0 if summary['passed'] else 1)


def setup():
    host(); value = plan(); top, lane, families = roots(value)
    require(not top.exists() and not lane.exists(), 'T16 roots exist; fresh ID required')
    lane.mkdir(); (lane/'gem5-slots').mkdir(); (lane/'linux-tests').mkdir(); top.mkdir()
    for path in families.values():
        Path(str(path) + '.dispatch').mkdir()
    write(lane/'setup.json', {'created': '2026-09-27', 'at': batch.now().isoformat(), 'code_commit': commit(),
                              'plan_sha256': artifacts.digest(value), 'recipe': ref(__file__)})
    print(json.dumps({'lane_dispatch': str(lane), 'families': {k: str(v) for k, v in families.items()}}))


def run_tests(kind):
    """Same receipts as the T15 pilot, bound to this runtime (run under socket_lane.sh)."""
    host(); lane_node(); value = plan(); _, lane, _ = roots(value)
    folder = lane/'linux-tests'/commit()[:12]/kind
    require(kind in pilot.TESTS and not folder.exists(), 'unknown kind or tests already ran; no retry')
    folder.mkdir(parents=True); (folder/'tmp').mkdir()
    code, runtime = commit(), batch.runtime_identity()
    command = [sys.executable, '-m', 'pytest', *pilot.TESTS[kind], '-q', '-p', 'no:cacheprovider',
               '--junitxml=' + str(folder/'junit.xml'), '--basetemp=' + str(folder/'pytest')]
    started = batch.now()
    with (folder/'stdout').open('x') as out:
        result = subprocess.run(command, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, timeout=240,
                                env=pilot.environment(TMPDIR=str(folder/'tmp')))
    finished = batch.now()
    require(batch.runtime_identity() == runtime and commit() == code, 'runtime changed during tests')
    write(folder/'receipt.json', {'format': 'swdb.bfs.pilot-linux-tests.v1', 'kind': kind, 'host': 'mbit10',
        'platform': 'linux', 'code_commit': code, 'runtime_sha256': runtime, 'command': command,
        'returncode': result.returncode, 'started': started.isoformat(), 'finished': finished.isoformat(),
        'junit': ref(folder/'junit.xml'), 'stdout': ref(folder/'stdout'), 'evidence_kind': 'contract_fixture'})
    print(json.dumps({'kind': kind, 'returncode': result.returncode, 'receipt': ref(folder/'receipt.json')}))
    raise SystemExit(result.returncode)


def prepare(node):
    """Admission only; the allocation clock starts at prepared_at. Frozen protocols bind here."""
    host(); value = plan(); _, lane, families = roots(value)
    require(node in value['lane']['nodes'], 'lane is outside the planned assignment')
    require(not (lane/'admission.json').exists(), 'admission already prepared; no retry')
    code = commit()
    store = Store(ROOT/'records')
    protocols = {}
    for key, request_ref in value['protocol_requests'].items():
        frozen = store.get(request_ref['frozen_id'], 'protocol')
        require(frozen is not None, 'frozen protocol record is missing: ' + key)
        protocols[key] = {'id': frozen['id'], 'sha256': artifacts.digest(frozen)}
    prepared = batch.now()
    available = value['bounds']['batch_seconds'] - sum(r['elapsed_seconds'] for r in batch.preparation_charges(value))
    end = prepared + timedelta(seconds=value['allocation']['total_seconds'])
    tests = [ref(lane/'linux-tests'/code[:12]/kind/'receipt.json') for kind in pilot.TESTS]
    admission = {'format': 'swdb.bfs.simulator-batch-admission.v1', 'created': '2026-09-27',
        'plan_sha256': artifacts.digest(value), 'prepared_at': prepared.isoformat(),
        'clock': {'not_before': prepared.isoformat(), 'latest_start': (end - timedelta(seconds=available)).isoformat(),
                  'absolute_end': end.isoformat()},
        'preparation_charges': batch.preparation_charges(value), 'code_commit': code,
        'runtime_sha256': batch.runtime_identity(), 'python': ref(pilot.PYTHON.resolve()),
        'proofs': {}, 'coverage_commit': pilot.COVERAGE_COMMIT, 'protocols': protocols, 'linux_cleanup_tests': tests,
        'lane_node': node, 'concurrency': value['concurrency'], 'kind': KIND}
    for key, (name, digest) in pilot.PROOFS.items():
        item = ref(pilot.BASE/name); require(item['sha256'] == digest, 'retained prerequisite changed: ' + key)
        admission['proofs'][key] = item
    batch.validate_pilot_tests(value, admission)
    batch.validate_preparation_reservation(value, admission)
    batch.validate_inputs(value, admission, store)
    for row in value['series']:
        require(not any(rid == row['id'] or rid.startswith(row['id'] + '.') for rid in store.by_id),
                'series records already exist')
    for path in families.values():
        require(not path.exists() and Path(str(path) + '.dispatch').is_dir(), 'series roots are not fresh')
    free = shutil.disk_usage(value['raw_root']).free
    require(free >= value['allocation']['free_space_required_at_admission_gib'] * batch.GIB,
            'raw storage lacks the allocation plus its reserve')
    admission['free_bytes_at_admission'] = free
    write(lane/'admission.json', admission)
    print(json.dumps(ref(lane/'admission.json')))


def launch(admission_sha, pane_pid, pane_ticks):
    start = batch.now()
    host(); value = plan(); top, lane, families = roots(value)
    path = lane/'admission.json'
    require(sha(path) == admission_sha and not (lane/'launch.json').exists(), 'admission changed or already launched')
    require(sha(pilot.HELPER) == pilot.HELPER_SHA, 'lane helper differs from the reviewed version')
    ad = json.loads(path.read_text()); node = ad['lane_node']
    require(batch.stamp(ad['clock']['not_before']) <= start <= batch.stamp(ad['clock']['latest_start']),
            'outside the admitted launch window')
    require(ad.get('kind', batch.T16_KIND) == KIND, 'admission belongs to another T16 job')
    remaining = value['bounds']['batch_seconds'] - sum(r['elapsed_seconds'] for r in ad['preparation_charges'])
    end = min(batch.stamp(ad['clock']['absolute_end']), start + timedelta(seconds=remaining))
    pane = own.identity(pane_pid)
    require(pane and pane['start_ticks'] == pane_ticks and os.getppid() == pane_pid, 'exact launching pane required')
    common = ['--admission', str(path), '--admission-sha256', admission_sha, '--lane', str(node),
              '--outer-started', start.isoformat(), '--outer-deadline', end.isoformat(),
              '--pane-pid', str(pane_pid), '--pane-start-ticks', str(pane_ticks)]
    names = {family: 'd' + str(index) for index, family in enumerate(families)}
    lines = []
    for family, runs in families.items():
        argv = [str(pilot.PYTHON), '-s', '-B', str(ROOT/'scripts/bfs_simulator_batch.py'), KIND,
                '--family', family, '--runs-dir', str(runs), *common]
        out = Path(str(runs) + '.dispatch')
        lines.append(f'{shlex.join(argv)} >{shlex.quote(str(out/"driver.stdout"))} '
                     f'2>{shlex.quote(str(out/"driver.stderr"))} & p_{names[family]}=$!')
    wrapper = ('set -u; ' + '; '.join(lines) + '; '
               + '; '.join(f'wait $p_{names[f]}; r_{names[f]}=$?; '
                           f'echo $r_{names[f]} >{shlex.quote(str(Path(str(r) + ".dispatch")/"driver.exit"))}'
                           for f, r in families.items())
               + '; exit $(( ' + ' | '.join(f'r_{names[f]}' for f in families) + ' ))')
    seconds = (end - batch.now()).total_seconds() - 30
    require(seconds >= value['bounds']['series_seconds'] + 30, 'cannot fit a full series allowance')
    argv = ['timeout', '--signal=TERM', '--kill-after=30s', f'{seconds:.3f}s', 'bash', str(pilot.HELPER), str(node),
            value['id'], '--record', str(lane/'lane.json'), '--', 'bash', '-c', wrapper]
    write(lane/'launch.json', {'created': '2026-09-27', 'outer_started': start.isoformat(),
        'outer_deadline': end.isoformat(), 'remaining_seconds': remaining, 'command': argv,
        'pane_identity': pane, 'recipe': ref(__file__), 'capacity': capacity(node)})
    os.execvpe(argv[0], argv, pilot.environment())


def capacity(node):
    from scripts.bfs_simulator_series import capacity_snapshot
    snap = capacity_snapshot(node)
    return {'observed_at': snap['observed_at'], 'result': snap['result']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('probe', 'setup', 'tests', 'prepare', 'launch'))
    p.add_argument('--kind', choices=tuple(pilot.TESTS))
    p.add_argument('--node', type=int, choices=(0, 1))
    p.add_argument('--job', choices=tuple(JOBS), default='b1', help='T16 lane job (2026-09-28 split: m, s1, s2)')
    p.add_argument('--admission-sha256'); p.add_argument('--pane-pid', type=int); p.add_argument('--pane-start-ticks', type=int)
    a = p.parse_args()
    global KIND
    KIND = JOBS[a.job]
    if a.mode == 'probe': probe()
    elif a.mode == 'setup': setup()
    elif a.mode == 'tests': run_tests(a.kind)
    elif a.mode == 'prepare': prepare(a.node)
    else: launch(a.admission_sha256, a.pane_pid, a.pane_start_ticks)


if __name__ == '__main__':
    main()
