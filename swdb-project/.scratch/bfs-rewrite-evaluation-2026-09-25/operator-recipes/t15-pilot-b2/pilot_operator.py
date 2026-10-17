#!/usr/bin/env python3
"""T15 pilot b2 operator (b1 recipe, kind t15-pilot-b2): setup, Linux tests, admission, launch. Created 2026-09-27 ET.

Runs from the immutable runtime checkout that contains it. It creates no
simulator lifecycle of its own: two unchanged-contract batch drivers (one per
family) run inside one socket_lane.sh job and share a one-slot gem5 pool.
No failed ID is resumed; every mode refuses to overwrite existing output.
"""
import argparse
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts import bfs_simulator_batch as batch  # noqa: E402
from scripts import bfs_owned_execution as own  # noqa: E402
from swdb import artifacts  # noqa: E402
from swdb.store import Store  # noqa: E402

NODE = 0  # Root lane assignment 2026-09-27 (node1 belongs to Stream B native timing).
KIND = 't15-pilot-b2'  # Fresh relaunch after b1's first-pair profile gate failure.
HELPER = Path('/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh')
HELPER_SHA = '00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
PYTHON = Path('/usr/bin/python3.12')
BASE = Path('/data/yanruj/EvolveSWDB_runs')
PROOFS = {
 'a3': ('bfs-dx100-bringup-20260925/witness-a3-dispatch1/terminal-validation.json', '21ee990e45c9da567579aedbcab2e0554ab457fdcabd69f40c478d78e2d4c3e9'),
 'paired': ('bfs-native-paired-pilot-20260926-a1.dispatch/terminal-validation.json', 'd9979ec1a493de0184f9e4b93fb9fbe2c20d8a6bb029ce28ef43d7c4b66551db'),
 'provider': ('bfs-provider-initial-20260926-a1/terminal-validation.json', '1f455257e4542f67555389195be532de3a131d677083f4e5372c6afcdf02ad1c'),
 'coverage': ('bfs-dx100-coverage-20260926-a2.dispatch/terminal-validation.json', '6df37b96da525b36e79a351096bf8e565550a61050f247d798e8366f9a1f3815')}
COVERAGE_COMMIT = '5a0b15fe666b2d094a2b2b9847ff5a30ef16fb4f'
TESTS = {'owned_cleanup': ['tests/test_bfs_owned_execution.py', '-k', 'linux'],
         'dx100_interruption': ['tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem']}
ENV = {'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
       'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}
REMOVE = ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE', 'PYTHONOPTIMIZE',
          'PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'LD_PRELOAD', 'LD_LIBRARY_PATH')


def environment(**extra):
    """Keep the lane helper's variables (LACT_SOCKET_LANE_PID etc.); drop Python overrides.

    2026-09-27: the first dx100_interruption run used a minimal environment and
    lost LACT_SOCKET_LANE_PID, which the real mbit10 lane guard requires.
    """
    env = {k: v for k, v in os.environ.items() if k not in REMOVE}
    env.update(ENV, **extra)
    return env


def require(ok, why):
    if not ok:
        raise SystemExit('refused: ' + why)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {'path': str(path), 'sha256': sha(path)}


def write(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def plan():
    value = json.loads(batch.plan_path(KIND).read_text())
    batch.validate_plan(value, KIND)
    return value


def roots(value):
    top, lane = batch.pilot_storage_paths(value)
    return top, lane, {row['id'].rsplit('.', 1)[1]: top/row['id'] for row in value['series']}


def commit():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, text=True)
    require(not dirty.strip(), 'runtime checkout has tracked modifications')
    return head


def host():
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10', 'requires mbit10')
    require(Path(sys.executable).resolve() == PYTHON.resolve(), 'requires the pinned /usr/bin/python3.12')


def setup():
    host(); value = plan(); top, lane, families = roots(value)
    require(not top.exists() and not lane.exists(), 'pilot roots exist; fresh ID required')
    lane.mkdir(); (lane/'gem5-slots').mkdir(); (lane/'linux-tests').mkdir(); top.mkdir()
    for path in families.values():
        Path(str(path) + '.dispatch').mkdir()
    write(lane/'setup.json', {'created': '2026-09-27', 'at': batch.now().isoformat(), 'code_commit': commit(),
                              'plan_sha256': artifacts.digest(value), 'recipe': ref(__file__)})
    print(json.dumps({'lane_dispatch': str(lane), 'families': {k: str(v) for k, v in families.items()}}))


def run_tests(kind):
    """Run under socket_lane.sh; the receipt binds the exact runtime identity."""
    host(); value = plan(); _, lane, _ = roots(value)
    folder = lane/'linux-tests'/commit()[:12]/kind
    require(kind in TESTS and not folder.exists(), 'unknown kind or tests already ran; no retry')
    folder.mkdir(parents=True); (folder/'tmp').mkdir()
    code, runtime = commit(), batch.runtime_identity()
    command = [sys.executable, '-m', 'pytest', *TESTS[kind], '-q', '-p', 'no:cacheprovider',
               '--junitxml=' + str(folder/'junit.xml'), '--basetemp=' + str(folder/'pytest')]
    started = batch.now()
    with (folder/'stdout').open('x') as out:
        result = subprocess.run(command, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, timeout=240,
                                env=environment(TMPDIR=str(folder/'tmp')))
    finished = batch.now()
    require(batch.runtime_identity() == runtime and commit() == code, 'runtime changed during tests')
    write(folder/'receipt.json', {'format': 'swdb.bfs.pilot-linux-tests.v1', 'kind': kind, 'host': 'mbit10',
        'platform': 'linux', 'code_commit': code, 'runtime_sha256': runtime, 'command': command,
        'returncode': result.returncode, 'started': started.isoformat(), 'finished': finished.isoformat(),
        'junit': ref(folder/'junit.xml'), 'stdout': ref(folder/'stdout'), 'evidence_kind': 'contract_fixture'})
    print(json.dumps({'kind': kind, 'returncode': result.returncode, 'receipt': ref(folder/'receipt.json')}))
    raise SystemExit(result.returncode)


def prepare():
    """Admission only; the allocation clock (48 h) starts at prepared_at."""
    host(); value = plan(); _, lane, families = roots(value)
    require(not (lane/'admission.json').exists(), 'admission already prepared; no retry')
    code = commit()
    prepared = batch.now()
    available = value['bounds']['batch_seconds'] - sum(r['elapsed_seconds'] for r in batch.preparation_charges(value))
    # b2 keeps the one approved allocation: its absolute end is b1's, and b1's
    # closed attempt is a flat charge, so no time or storage is replenished.
    end = batch.stamp(value['allocation']['absolute_end'])
    require(prepared <= end - timedelta(seconds=available), 'b2 admission window has elapsed')
    tests = [ref(lane/'linux-tests'/code[:12]/kind/'receipt.json') for kind in TESTS]
    admission = {'format': 'swdb.bfs.simulator-batch-admission.v1', 'created': '2026-09-27',
        'plan_sha256': artifacts.digest(value), 'prepared_at': prepared.isoformat(),
        'clock': {'not_before': prepared.isoformat(), 'latest_start': (end - timedelta(seconds=available)).isoformat(),
                  'absolute_end': end.isoformat()},
        'preparation_charges': batch.preparation_charges(value), 'code_commit': code,
        'runtime_sha256': batch.runtime_identity(), 'python': ref(PYTHON.resolve()),
        'proofs': {}, 'coverage_commit': COVERAGE_COMMIT, 'protocols': {}, 'linux_cleanup_tests': tests,
        'lane_node': NODE, 'concurrency': value['concurrency']}
    for key, (name, digest) in PROOFS.items():
        item = ref(BASE/name); require(item['sha256'] == digest, 'retained prerequisite changed: ' + key)
        admission['proofs'][key] = item
    batch.validate_pilot_tests(value, admission)
    batch.validate_preparation_reservation(value, admission)
    store = Store(ROOT/'records')
    batch.validate_inputs(value, admission, store)
    for row in value['series']:
        require(not any(rid == row['id'] or rid.startswith(row['id'] + '.') for rid in store.by_id),
                'series records already exist')
    for path in families.values():
        require(not path.exists() and Path(str(path) + '.dispatch').is_dir(), 'family roots are not fresh')
    write(lane/'admission.json', admission)
    print(json.dumps(ref(lane/'admission.json')))


def launch(admission_sha, pane_pid, pane_ticks):
    start = batch.now()
    host(); value = plan(); top, lane, families = roots(value)
    path = lane/'admission.json'
    require(sha(path) == admission_sha and not (lane/'launch.json').exists(), 'admission changed or already launched')
    require(sha(HELPER) == HELPER_SHA, 'lane helper differs from the reviewed version')
    ad = json.loads(path.read_text())
    require(batch.stamp(ad['clock']['not_before']) <= start <= batch.stamp(ad['clock']['latest_start']),
            'outside the admitted launch window')
    remaining = value['bounds']['batch_seconds'] - sum(r['elapsed_seconds'] for r in ad['preparation_charges'])
    end = min(batch.stamp(ad['clock']['absolute_end']), start + timedelta(seconds=remaining))
    pane = own.identity(pane_pid)
    require(pane and pane['start_ticks'] == pane_ticks and os.getppid() == pane_pid, 'exact launching pane required')
    common = ['--admission', str(path), '--admission-sha256', admission_sha, '--lane', str(NODE),
              '--outer-started', start.isoformat(), '--outer-deadline', end.isoformat(),
              '--pane-pid', str(pane_pid), '--pane-start-ticks', str(pane_ticks)]
    lines = []
    for family, runs in families.items():
        argv = [str(PYTHON), '-s', '-B', str(ROOT/'scripts/bfs_simulator_batch.py'), KIND,
                '--family', family, '--runs-dir', str(runs), *common]
        out = Path(str(runs) + '.dispatch')
        lines.append(f'{shlex.join(argv)} >{shlex.quote(str(out/"driver.stdout"))} '
                     f'2>{shlex.quote(str(out/"driver.stderr"))} & p_{family}=$!')
    wrapper = ('set -u; ' + '; '.join(lines) + '; '
               + '; '.join(f'wait $p_{f}; r_{f}=$?; echo $r_{f} >{shlex.quote(str(Path(str(r) + ".dispatch")/"driver.exit"))}'
                           for f, r in families.items())
               + '; exit $(( ' + ' | '.join(f'r_{f}' for f in families) + ' ))')
    seconds = (end - batch.now()).total_seconds() - 30
    require(seconds >= value['bounds']['series_seconds'] + 30, 'cannot fit a full series allowance')
    argv = ['timeout', '--signal=TERM', '--kill-after=30s', f'{seconds:.3f}s', 'bash', str(HELPER), str(NODE),
            value['id'], '--record', str(lane/'lane.json'), '--', 'bash', '-c', wrapper]
    write(lane/'launch.json', {'created': '2026-09-27', 'outer_started': start.isoformat(),
        'outer_deadline': end.isoformat(), 'remaining_seconds': remaining, 'command': argv,
        'pane_identity': pane, 'recipe': ref(__file__), 'capacity': capacity()})
    os.execvpe(argv[0], argv, environment())


def capacity():
    from scripts.bfs_simulator_series import capacity_snapshot
    snap = capacity_snapshot(NODE)
    return {'observed_at': snap['observed_at'], 'result': snap['result']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('setup', 'tests', 'prepare', 'launch'))
    p.add_argument('--kind', choices=tuple(TESTS))
    p.add_argument('--admission-sha256'); p.add_argument('--pane-pid', type=int); p.add_argument('--pane-start-ticks', type=int)
    a = p.parse_args()
    if a.mode == 'setup': setup()
    elif a.mode == 'tests': run_tests(a.kind)
    elif a.mode == 'prepare': prepare()
    else: launch(a.admission_sha256, a.pane_pid, a.pane_start_ticks)


if __name__ == '__main__':
    main()
