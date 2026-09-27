#!/usr/bin/env python3
"""Stream B native acceptance operator for T18/T19. Created: 2026-09-27 ET.

Operational glue around the existing reviewed runners only. It never edits the
runtime, retries a run ID, invokes a provider, or chooses an optimization.

Modes (all on mbit10, from the pinned runtime checkout's Python 3.12):
  proof CONFIG      run the fixed native_campaign_owned_cleanup Linux fixture in
                    the assigned lane (90 s), then its independent 60 s audit
  admit CONFIG      create .dispatch, the record view, reassessment and sealed
                    admission for one route (no lane, no measurement)
  launch CONFIG     body of the named tmux pane: original clock, pane identity,
                    timeout -> socket_lane.sh -> bfs_native_campaign.py
  close CONFIG      after outer exit: independent process/lease closure,
                    terminal-validation.json and storage recount
Stdlib only until the runtime inventory is checked.
"""
import argparse
from datetime import datetime, timedelta
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ET = ZoneInfo('America/New_York')
BASE = Path('/data/yanruj/EvolveSWDB_runs')
LEASES = Path('/data1/yanruj/lact-host-lease')
HELPER = '/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh'
HELPER_SHA = '00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
PROOF_ID = 'bfs-native-campaign-owned-linux-20260926-a1'
ENV_REMOVE = ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE', 'PYTHONOPTIMIZE',
              'PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'LD_PRELOAD', 'LD_LIBRARY_PATH')


def require(value, reason):
    if not value: raise RuntimeError(reason)


def now(): return datetime.now(ET)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path): return {'path': str(Path(path).absolute()), 'sha256': sha(path)}
def read(path): return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def environment(pytest=False):
    env = {k: v for k, v in os.environ.items() if k not in ENV_REMOVE}
    env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PATH='/usr/bin:/bin')
    if pytest: env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    return env


def config(path):
    c = read(path)
    for key in ('runtime', 'commit', 'python', 'python_sha256', 'node'):
        require(c.get(key) is not None, 'unresolved configuration: ' + key)
    require(c['node'] in (0, 1) and Path(c['runtime']).is_absolute(), 'invalid node/runtime')
    return c


def guard(c):
    root = Path(c['runtime'])
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True, timeout=10).strip()
    dirty = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain', '--ignored'], text=True, timeout=30)
    require(head == c['commit'] and not dirty.strip(), 'runtime HEAD differs or checkout is not pristine: ' + dirty[:500])
    require(sha(Path(c['python']).resolve()) == c['python_sha256'], 'Python changed')
    require(sha(HELPER) == HELPER_SHA, 'socket_lane.sh bytes changed')


def leases(c, *, require_free=True):
    rows = {}
    for name in ('mbit10-evaluation', 'mbit10-evaluation-node0', 'mbit10-evaluation-node1'):
        meta = read(LEASES/(name+'.meta.json'))
        with (LEASES/(name+'.lease')).open('r') as stream:
            try: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB); held = False; fcntl.flock(stream, fcntl.LOCK_UN)
            except BlockingIOError: held = True
        require(read(LEASES/(name+'.meta.json')) == meta, 'lease metadata changed during observation')
        rows[name] = {'metadata': meta, 'kernel_held': held}
        if require_free and name in ('mbit10-evaluation', 'mbit10-evaluation-node%d' % c['node']):
            require(not held and meta['state'] == 'released', name + ' is not free')
    return rows


def disks():
    out = {}
    for path, reserve in ((BASE, 30*1024**3), (Path('/data1'), 10*1024**3)):
        fs = os.statvfs(path); out[str(path)] = fs.f_bavail*fs.f_frsize
        require(out[str(path)] >= reserve, 'free-space reserve violated: ' + str(path))
    return out


def host_record():
    def run(*cmd):
        try: return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout
        except Exception as exc: return repr(exc)
    return {'observed_at': now().isoformat(), 'uptime': run('uptime'), 'users': sorted(set(run('who').split()[0::5])),
            'df': run('df', '-h', '/data1', '/data'), 'loadavg': Path('/proc/loadavg').read_text(),
            'governor': run('cat', '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'),
            'no_turbo': run('cat', '/sys/devices/system/cpu/intel_pstate/no_turbo'),
            'uname': run('uname', '-a'), 'numactl': run('numactl', '--hardware')}


def ticks(pid):
    return int(Path('/proc/%d/stat' % pid).read_text().rsplit(')', 1)[1].split()[19])


# ---------------------------------------------------------------- proof
def proof(c, path):
    guard(c); lease_rows = leases(c); disks()
    raw, dispatch = BASE/PROOF_ID, BASE/(PROOF_ID+'.dispatch')
    require(not raw.exists() and not dispatch.exists(), 'proof root exists; no retry')
    dispatch.mkdir()
    write(dispatch/'preflight.json', {'created': '2026-09-27', 'config': ref(path), 'leases': lease_rows,
                                      'host': host_record(), 'commit': c['commit']})
    probe = subprocess.check_output([c['python'], '-I', '-B', '-c',
        'import pytest,hashlib,json;print(json.dumps([pytest.__version__,hashlib.sha256(open(pytest.__file__,"rb").read()).hexdigest()]))'],
        text=True, env=environment(True))
    version, pytest_sha = json.loads(probe)
    session = 'bfs-native-routes-proof-b1'
    body = shlex.join([c['python'], '-I', '-B', str(Path(__file__).resolve()), 'proof-stage', str(path),
                       version, pytest_sha]) + ' "$BASHPID"'
    body += ' >' + shlex.quote(str(dispatch/'pane.stdout')) + ' 2>' + shlex.quote(str(dispatch/'pane.stderr'))
    subprocess.run(['tmux', 'new-session', '-d', '-s', session, 'bash -c ' + shlex.quote(body)], check=True, env=environment(True))
    end = time.monotonic()+100
    while subprocess.run(['tmux', 'has-session', '-t', session], capture_output=True).returncode == 0:
        require(time.monotonic() < end, 'proof pane exceeded its bound; retained for recovery'); time.sleep(.2)
    require(read(dispatch/'outer.exit') == 0, 'fixture helper failed; retained, no retry')
    lane = dispatch/'lane.json'
    args = ['standard', 'native_campaign_owned_cleanup', '--expected-supervisor-commit', c['commit'],
            '--node', str(c['node']), '--generation', str(read(lane)['socket_lane']['lease_generation'])]
    for name, item in (('pending', raw/'proof.pending.json'), ('lane', lane), ('outer-exit', dispatch/'outer.exit'),
                       ('ledger', raw/'cleanup-ledger.json')):
        args += ['--'+name, str(item), '--'+name+'-sha256', sha(item)]
    with (dispatch/'audit.stdout').open('xb') as out, (dispatch/'audit.stderr').open('xb') as err:
        code = subprocess.run(['timeout', '--signal=TERM', '--kill-after=1s', '59s', c['python'], '-I', '-B',
                               str(Path(c['runtime'])/'scripts/bfs_linux_fixture_audit.py'), *args],
                              stdout=out, stderr=err, env=environment(True), cwd=c['runtime']).returncode
    write(dispatch/'audit.exit', code)
    require(code == 0, 'independent fixture audit failed; retained')
    print(json.dumps(ref(raw/'proof.json')))


def proof_stage(c, path, version, pytest_sha, pane):
    dispatch = BASE/(PROOF_ID+'.dispatch')
    begin = now(); end = begin+timedelta(seconds=90)
    write(dispatch/'launch.json', {'outer_started': begin.isoformat(), 'outer_deadline': end.isoformat(),
                                   'pane_identity': {'pid': pane, 'start_ticks': ticks(pane)}})
    remaining = (end-now()).total_seconds()-30
    command = ['timeout', '--signal=TERM', '--kill-after=30s', '%.3fs' % remaining, 'bash', HELPER, str(c['node']),
               PROOF_ID, '--lease-timeout-s', '0', '--record', str(dispatch/'lane.json'), '--',
               c['python'], '-I', '-B', str(Path(c['runtime'])/'scripts/bfs_linux_fixture.py'),
               'native_campaign_owned_cleanup', '--expected-commit', c['commit'], '--python-sha256', c['python_sha256'],
               '--pytest-version', version, '--pytest-sha256', pytest_sha, '--outer-started', begin.isoformat(),
               '--outer-deadline', end.isoformat(), '--pane-pid', str(pane), '--pane-start-ticks', str(ticks(pane)),
               '--lane', str(c['node'])]
    with (dispatch/'outer.stdout').open('xb') as out, (dispatch/'outer.stderr').open('xb') as err:
        code = subprocess.run(command, stdout=out, stderr=err, env=environment(True), cwd=c['runtime']).returncode
    write(dispatch/'outer.exit', code)


# ---------------------------------------------------------------- campaign
FULL_KINDS = {'application', 'kernel', 'implementation', 'operation', 'intrinsic', 'hardware_target',
              'machine', 'workload', 'input', 'strategy'}


def _strings(value):
    if isinstance(value, str): yield value
    elif isinstance(value, dict):
        for key, item in value.items(): yield key; yield from _strings(item)
    elif isinstance(value, list):
        for item in value: yield from _strings(item)


def minimal_view(store, source, target, roots):
    """Copy the reference closure of the campaign roots (2026-09-27 ET, b2).

    Small catalog kinds are kept whole; every other record is kept only when a
    kept record mentions its exact ID. Non-YAML files (record-root sources) are
    copied unchanged. The b1 view carried unrelated records and the other
    source's 3 MB protocol, which made every harness persist slower."""
    keep = {rec.id for rec in store.records if rec.kind in FULL_KINDS}
    queue = [*roots, *keep]
    while queue:
        rid = queue.pop(); rec = store.by_id.get(rid)
        if rec is None: continue
        keep.add(rid)
        for text in _strings(rec.data):
            if text in store.by_id and text not in keep:
                keep.add(text); queue.append(text)
    require(all(rid in keep and rid in store.by_id for rid in roots), 'campaign root record missing from view')
    written = set()
    for rec in store.records:
        if rec.id in keep and store.by_id.get(rec.id) is rec:
            path = Path(target)/rec.rel; path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(source)/rec.rel, path); written.add(rec.rel)
    for path in Path(source).rglob('*'):
        rel = path.relative_to(source)
        if (path.is_file() and path.suffix not in {'.yaml', '.yml'}
                and not any(part.startswith('.') for part in rel.parts)):
            (Path(target)/rel).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, Path(target)/rel)
    return sorted(keep)


def route_paths(r):
    runs = BASE/r['id']
    return {'runs': runs, 'dispatch': Path(str(runs)+'.dispatch'),
            'sources': Path('/data1/yanruj/EvolveSWDB_sources')/r['id'],
            'builds': Path('/data1/yanruj/EvolveSWDB_builds')/r['id']}


def driver_argv(c, r, admission_sha, started, deadline, pane, pane_ticks):
    p = route_paths(r); d = p['dispatch']
    return [c['python'], '-s', '-B', str(Path(c['runtime'])/'scripts/bfs_native_campaign.py'),
            '--id', r['id'], '--existing-candidate', r['candidate'],
            '--proposal', str(d/'proposal.json'), '--reassessment', str(d/'reassessment.json'),
            '--packages', *r['packages'], '--protocol', r['protocol'],
            '--records', str(d/'records'), '--runs-dir', str(p['runs']), '--source-runs-dir', str(p['sources']),
            '--build-root', str(p['builds']), '--lane', 'mbit10-evaluation-node%d' % c['node'],
            '--total-seconds', '14400', '--supervision-admission', str(d/'admission.json'),
            '--supervision-sha256', admission_sha, '--expected-commit', c['commit'],
            '--outer-started', started, '--outer-deadline', deadline,
            '--pane-pid', str(pane), '--pane-start-ticks', str(pane_ticks)]


def admit(c, path):
    """Seal the admission; imports runtime code only after guard()."""
    guard(c); disks(); r = c['route']; p = route_paths(r)
    require(not any(x.exists() for x in p.values()), 'route roots exist; run IDs are never reused')
    sys.path.insert(0, c['runtime'])
    from scripts import bfs_native_campaign as campaign
    from swdb import artifacts
    from swdb.store import Store
    from swdb.validate import _validate_store
    d = p['dispatch']; d.mkdir()
    manifest = read(Path(c['runtime'])/r['reassessment_template'])
    proposal = read(Path(c['runtime'])/r['proposal'])
    roots = [proposal['id'], r['candidate'], *r['packages'], r['protocol'], 'mbit10',
             *(manifest['origin'][k]['id'] for k in ('proposal', 'candidate', 'profile_package', 'source_snapshot')),
             *(row['id'] for row in manifest['origin']['baseline_packages'])]
    kept = minimal_view(Store(Path(r['record_view'])), r['record_view'], d/'records', roots)
    shutil.copyfile(Path(c['runtime'])/r['proposal'], d/'proposal.json')
    store = Store(d/'records')
    checked = _validate_store(store, extra=[], replace={})
    require(not store.problems and not checked.problems, 'minimal record view is invalid: '
            + str((store.problems + checked.problems)[:3]))
    write(d/'record-view.json', {'created': '2026-09-27', 'source': r['record_view'], 'roots': roots,
                                 'records': kept, 'count': len(kept)})
    frozen = store.get(r['protocol'], 'protocol'); require(frozen is not None, 'frozen protocol missing')
    manifest['assessment'] = {'protocol': {'id': frozen['id'], 'sha256': artifacts.digest(frozen)},
        'packages': [{'id': rid, 'sha256': artifacts.digest(store.get(rid, 'profile_package'))} for rid in r['packages']]}
    write(d/'reassessment.json', manifest)
    args = argparse.Namespace(id=r['id'], existing_candidate=r['candidate'], proposal=(d/'proposal.json').resolve(),
        reassessment=(d/'reassessment.json').resolve(), packages=r['packages'], protocol=r['protocol'],
        lane='mbit10-evaluation-node%d' % c['node'], records=(d/'records').resolve(), runs_dir=p['runs'],
        source_runs_dir=p['sources'], build_root=p['builds'])
    proof_ref = ref(BASE/PROOF_ID/'proof.json')
    admission = {'format': 'swdb.bfs.native-campaign-admission.v1', 'id': r['id'], 'code_commit': c['commit'],
                 'bounds': campaign.NATIVE_BOUNDS, 'inputs': campaign.campaign_inputs(args),
                 'runtime': campaign.campaign_runtime(c['commit'], root=Path(c['runtime'])),
                 'linux_proof': proof_ref, 'host': host_record(), 'leases': leases(c, require_free=False),
                 'prepared_at': now().isoformat()}
    campaign.validate_linux_proof(proof_ref, admission)
    write(d/'admission.json', admission)
    print(json.dumps({'admission': ref(d/'admission.json'), 'reassessment': ref(d/'reassessment.json')}))


def launch(c, path, admission_sha, pane):
    """Runs as the named tmux pane body. The original clock precedes every guard."""
    begin = now(); end = begin+timedelta(seconds=14400)
    r = c['route']; d = route_paths(r)['dispatch']
    pane_ticks = ticks(pane)
    remaining = (end-now()).total_seconds()-30
    require(remaining > 0, 'exhausted interval')
    argv = driver_argv(c, r, admission_sha, begin.isoformat(), end.isoformat(), pane, pane_ticks)
    command = ['timeout', '--signal=TERM', '--kill-after=30s', '%.3fs' % remaining, 'bash', HELPER, str(c['node']),
               r['id'], '--lease-timeout-s', '0', '--record', str(d/'lane.json'), '--', *argv]
    write(d/'launch.json', {'outer_started': begin.isoformat(), 'outer_deadline': end.isoformat(),
                            'pane_identity': {'pid': pane, 'start_ticks': pane_ticks}, 'command': command})
    with (d/'outer.stdout').open('xb') as out, (d/'outer.stderr').open('xb') as err:
        code = subprocess.run(command, stdout=out, stderr=err, env=environment(), cwd=c['runtime']).returncode
    write(d/'outer.exit', code)


def close(c, path):
    r = c['route']; p = route_paths(r); d = p['dispatch']
    require((d/'outer.exit').exists(), 'outer exit not yet retained')
    sys.path.insert(0, c['runtime'])
    from scripts import bfs_native_campaign as campaign
    from scripts.dx100_witness_continuation import verify_terminal_processes
    driver_path = p['runs']/(r['id']+'.driver')/'driver.json'; driver = read(driver_path)
    lane = read(d/'lane.json')['socket_lane'] if (d/'lane.json').exists() else {}
    launch_value = read(d/'launch.json'); pane = launch_value['pane_identity']
    obs = driver.get('process_observations', {})
    rows = list(obs.get('ancestry', [])) + list(obs.get('owned_processes', []))
    samples = driver.get('resource_samples')
    if samples:
        for line in Path(samples['path']).read_text().splitlines():
            if line.strip(): rows += json.loads(line).get('processes', [])
    for stage in driver.get('stages', []):
        if stage.get('identity'): rows.append(stage['identity'])
        rows += stage.get('cleanup', {}).get('observed', [])
    rows += (driver.get('cleanup') or {}).get('observed', [])
    union = {}
    for row in rows: union[(row['pid'], row['start_ticks'])] = row
    union[(pane['pid'], pane['start_ticks'])] = {**pane, 'role': 'tmux_launcher'}
    declared = []
    for (pid, start), row in sorted(union.items()):
        try:
            fields = Path('/proc/%d/stat' % pid).read_text().rsplit(')', 1)[1].split()
            live = int(fields[19]) == start
        except FileNotFoundError: live = False
        if not live: declared.append({'pid': pid, 'start_ticks': start, 'state': 'absent', 'current_identity': None})
        else:
            require(fields[0] == 'Z' and fields[21] == '0' and (pid, start) == (pane['pid'], pane['start_ticks']),
                    'owned process still live: %d' % pid)
            declared.append({'pid': pid, 'start_ticks': start, 'state': 'Z', 'rss_bytes': 0, 'role': 'tmux_launcher'})
    zombie = any(row['state'] == 'Z' for row in declared)
    verify_terminal_processes(declared, launcher_identity=(pane['pid'], pane['start_ticks']) if zombie else None)
    lease_rows = leases(c, require_free=False)
    node = lease_rows['mbit10-evaluation-node%d' % c['node']]
    released = (lane.get('lease_generation') is not None and node['metadata']['state'] == 'released'
                and not node['kernel_held'] and node['metadata']['lease']['generation'] == lane['lease_generation'])
    snapshot = d/'lease-snapshot.json'; write(snapshot, node['metadata'])
    audit = {'id': r['id'], 'state': driver['state'], 'repository_commit': c['commit'],
             'driver': ref(driver_path), 'lane': ref(d/'lane.json') if (d/'lane.json').exists() else None,
             'outer_exit': ref(d/'outer.exit'), 'lease_snapshot': ref(snapshot),
             'observed_at': now().isoformat(), 'lease_released': released, 'owned_processes': declared,
             'cleanup_state': 'terminal_no_live_owned_processes' if zombie else 'terminal_and_reaped',
             'owned_processes_absent': not zombie, 'owned_processes_nonrunning': True,
             'leases': lease_rows, 'host': host_record()}
    write(d/'terminal-validation.json', audit)
    require(released, 'lane lease not released at the retained generation')
    storage = campaign.validate_storage_accounting(ref(driver_path), ref(d/'terminal-validation.json'),
        admission_ref=ref(d/'admission.json'), current=now().isoformat())
    write(d/'storage-readback.json', storage)
    final = campaign.validate_storage_accounting(ref(driver_path), ref(d/'terminal-validation.json'),
        admission_ref=ref(d/'admission.json'), current=now().isoformat())
    outside = BASE/(r['id']+'.final-storage.json'); write(outside, final)
    print(json.dumps({'state': driver['state'], 'terminal': ref(d/'terminal-validation.json'), 'storage': ref(outside)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('proof', 'proof-stage', 'admit', 'launch', 'close'))
    parser.add_argument('config', type=Path)
    parser.add_argument('rest', nargs='*')
    args = parser.parse_args(); c = config(args.config)
    if args.mode == 'proof': proof(c, args.config.resolve())
    elif args.mode == 'proof-stage': proof_stage(c, args.config.resolve(), args.rest[0], args.rest[1], int(args.rest[2]))
    elif args.mode == 'admit': admit(c, args.config.resolve())
    elif args.mode == 'launch': launch(c, args.config.resolve(), args.rest[0], int(args.rest[1]))
    else: close(c, args.config.resolve())


if __name__ == '__main__':
    main()
