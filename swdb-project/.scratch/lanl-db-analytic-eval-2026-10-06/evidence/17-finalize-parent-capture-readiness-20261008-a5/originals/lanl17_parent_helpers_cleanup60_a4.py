"""Parent-owned prospective freeze/dispatch/report/export helpers, 2026-10-06 ET.

Importing performs no remote operation. Execute only on mbit10 after parent review.
No credential content is read; application timing occurs only in dispatched campaign.
"""
import argparse
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time

GIB = 1024 ** 3
PRIMARY = Path('/data1/yanruj/ArchEvolve')
MEMACC = Path('/data1/yanruj/Memacc-repro-20260925')
WRAPPER_REL = 'AgenticRefiner/scripts/host/socket_lane.sh'
LEASE_ROOT = Path('/data1/yanruj/lact-host-lease')
LOGIN_HOME = Path('/data1/yanruj/.codex')
HOME_TOKEN = 'SWDB_LANL17_ORIGINAL_CODEX_HOME'
ENTRY = Path('/data1/yanruj/.npm-global/bin/codex')
ENTRY_SHA = '61b0194f3bb6534439c8d26a3ed57d0805f84b884588b761795323eeb92fcf70'
NATIVE_SHA = 'fce635028842bfe9257140e8b7d53162732945e2f356fc35225be0702b4974be'
CLI_VERSION = 'codex-cli 0.153.0'
LINUX_SMOKE_SHA = '4d0bdf1d4c8d2ce96d948085a785cde15c389a4c50413962bc7db14df57cf9d6'
EVIDENCE = Path('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence')
CONFIGS = EVIDENCE / '17-prospective-configs'
CIDS = [f'extensa-gem5-bfs-20261006-p{i}' for i in range(1, 5)]
CAMPAIGN_S = 24 * 3600 + 600
OUTER_S = CAMPAIGN_S + 1200


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def json_digest(value):
    # Same canonical form as SWDB artifacts.digest; verify through the frozen module.
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def seal(value):
    return {**value, 'identity_sha256': json_digest(value)}


def checked_json(path):
    value = json.loads(Path(path).read_text())
    if 'identity_sha256' in value:
        assert value['identity_sha256'] == json_digest({k: v for k, v in value.items() if k != 'identity_sha256'}), 'Receipt seal differs'
    return value


def command(args, *, cwd=None, cap=120, env=None):
    return subprocess.check_output(list(map(str, args)), cwd=cwd, env=env, text=True, timeout=cap).strip()


def git(root, *args):
    return command(['git', '-C', root, *args])


def host():
    assert socket.gethostname().split('.')[0] == 'mbit10', 'Parent executes these helpers on mbit10 only'
    assert sys.platform == 'linux' and os.getuid() != 0


def login_home(value):
    assert isinstance(value, str) and Path(value).is_absolute()
    resolved = Path(value).resolve(strict=True)
    assert resolved == LOGIN_HOME.resolve(strict=True) and resolved.is_dir()
    for root in (pwd.getpwuid(os.getuid()).pw_dir, os.environ.get('HOME')):
        if root:
            account = Path(root).resolve()
            assert resolved != account and account not in resolved.parents
    assert (resolved / 'auth.json').is_file(), 'Auth existence only; contents remain unread'
    return {'configured_value': value, 'resolved_path': str(resolved), 'auth_file_exists': True,
            'authentication_bytes_read_by_helper': False, 'outside_account_home': True}


def leases():
    return {name: json.loads((LEASE_ROOT / (name + '.meta.json')).read_text()) for name in
            ('mbit10-evaluation-node0', 'mbit10-evaluation-node1', 'mbit10-evaluation')}


def all_free():
    rows = leases()
    assert all(row['state'] == 'released' for row in rows.values()), 'Wait for native services and both socket/legacy leases'
    return rows


def wrapper_identity(*, fetch=False):
    if fetch:
        git(MEMACC, 'fetch', 'origin', 'yanrujhou_main')
    expected = subprocess.check_output(['git', '-C', str(MEMACC), 'show', 'origin/yanrujhou_main:' + WRAPPER_REL], timeout=120)
    actual = MEMACC / WRAPPER_REL
    assert actual.read_bytes() == expected, 'Wrapper differs from freshly fetched upstream'
    return {'path': str(actual), 'sha256': sha(actual), 'upstream_commit': git(MEMACC, 'rev-parse', 'origin/yanrujhou_main')}


def capacity(other_active=False):
    values = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(values['MemAvailable'].split()[0]) * 1024
    disks = {mount: os.statvfs(mount).f_bavail * os.statvfs(mount).f_frsize for mount in ('/data1', '/data')}
    # Reserve both full guest budgets even when the first has not allocated its pages yet.
    assert available >= 80 * GIB, 'Two prospective 36 GiB guest budgets need reserved headroom'
    assert disks['/data1'] >= 21 * GIB and disks['/data'] >= (44 if other_active else 24) * GIB
    return {'memory_available_bytes': available, 'free_disk_bytes': disks, 'load_average': os.getloadavg(),
            'disk_snapshot': command(['df', '-h', '/data1', '/data']),
            'process_snapshot': command(['ps', '-eo', 'pid,ppid,pcpu,psr,etime,comm', '--sort=-pcpu'])}


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(Path(root).rglob('*'))
            if p.is_file() and p.suffix not in ('.lock', '.pyc') and '__pycache__' not in p.parts}


def modules(source):
    sys.dont_write_bytecode = True
    root = Path(source) / 'swdb-project'
    sys.path.insert(0, str(root))
    from swdb import artifacts, provider_adapters, provider_guard
    from swdb.estimate_protocol import estimator_identity
    from swdb.store import Store
    assert artifacts.digest({'a': 'ascii', 'b': 1}) == json_digest({'a': 'ascii', 'b': 1})
    return artifacts, provider_adapters, provider_guard, estimator_identity, Store


def clean(source, revision):
    assert git(source, 'rev-parse', 'HEAD') == revision
    assert not git(source, 'status', '--porcelain'), 'Frozen source changed; never update live W'


def provider_identity(adapters):
    assert sha(ENTRY) == ENTRY_SHA, 'Official configured entrypoint changed'
    config = {'kind': 'codex', 'command': [str(ENTRY)]}
    selected = adapters.get(config).launch_command(config)
    assert len(selected) == 1
    native = Path(selected[0])
    assert sha(native) == NATIVE_SHA and native.name == 'codex', 'Official architecture-selected native changed'
    version = command([ENTRY, '--version'], cap=10)
    assert version == CLI_VERSION, 'CLI version changed; review before fresh freeze'
    return {'entrypoint': str(ENTRY), 'entrypoint_sha256': ENTRY_SHA, 'native': str(native),
            'native_sha256': NATIVE_SHA, 'cli_version': version, 'pins': adapters.PINS['codex']}


def environment(source, raw):
    return {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(Path(source) / 'swdb-project'),
            'TMPDIR': str(Path(raw) / 'temporary')}


def run_cli(source, raw, name, argv, cap, env=None):
    raw = Path(raw)
    dump(raw / (name + '.argv.json'), list(map(str, argv)))
    with (raw / (name + '.stdout')).open('w') as out, (raw / (name + '.stderr')).open('w') as err:
        child = subprocess.Popen(list(map(str, argv)), cwd=Path(source) / 'swdb-project', env=env or environment(source, raw),
                                 stdout=out, stderr=err, start_new_session=True)
        try:
            result = child.wait(timeout=cap)
        finally:
            from swdb.processes import stop_group
            stop_group(child, grace_seconds=15)
    (raw / (name + '.exit-code.txt')).write_text(str(result) + '\n')
    if result:
        raise RuntimeError(f'{name} exited {result}; preserve stopped raw attempt')
    return (raw / (name + '.stdout')).read_text()


def metadata_pins(store, configs):
    from swdb import artifacts, bfs_protocol, campaign_targets, sg_graph
    baseline_ids = {row['candidate'] for data in configs for row in data['baselines']}
    inputs = {row['workload'] for data in configs for row in data['workload_classes']}
    baselines = []
    for rid in sorted(baseline_ids):
        source = store.get(rid, 'candidate')
        assert source is not None
        bfs_protocol.validate_baseline_source(store, source)
        baselines.append({'id': rid, 'record_sha256': artifacts.digest(source), 'artifact_sha256': source['artifact']['sha256']})
    graphs = []
    for rid in sorted(inputs):
        data = store.get(rid, 'workload')
        assert data and data['definition']['sources'] == [0]
        representations = []
        for app in ('dx100-gapbs', 'gapbs'):
            selected = bfs_protocol.workload_representation(store, rid, app)
            rep = selected['representation']
            degree = sg_graph.out_degrees(rep, [0])[0]
            assert degree > 0 and rep['canonical_sha256'] == data['definition']['canonical_sha256']
            representations.append({'application': app, 'path': rep['path'], 'sha256': rep['sha256'],
                                    'format': rep['format'], 'source0_out_degree': degree})
        graphs.append({'id': rid, 'record_sha256': artifacts.digest(data), 'identity_sha256': data['identity_sha256'],
                      'canonical_sha256': data['definition']['canonical_sha256'], 'generator': data['definition'].get('generator'),
                      'representations': representations})
    assert len(graphs) == 8 and len({row['canonical_sha256'] for row in graphs}) == 8
    template = store.get(campaign_targets.GEM5_TEMPLATE, 'protocol')
    assert template and template['settings']['threads'] == 4
    model = bfs_protocol._simulation_identity(template['settings'], store, required=True, check_files=True)
    assert model['evidence_kind'] == 'execution' and model['outcome']['stage'] == 'build'
    companion = template['settings']['correctness']['companion_cases']['parent_gather_race']['workload']
    companion_record = store.get(companion, 'workload')
    selected = bfs_protocol.workload_representation(store, companion, 'dx100-gapbs')
    return {'baselines': baselines, 'inputs': graphs, 'template': {'id': template['id'], 'sha256': artifacts.digest(template)},
            'simulation_identity': template['settings']['simulation_identity'],
            'model_build': {'id': model['id'], 'sha256': artifacts.digest(model)},
            'companion': {'id': companion, 'record_sha256': artifacts.digest(companion_record),
                          'representation': selected['representation'], 'prior_exposure': 'not_certified_fresh'},
            'numeric_bridge': 'unsupported; no SG/MMIO complete-call numeric adapter',
            'dependency_policy': 'connected shared generator seed/artifact/trajectory/baseline outcome; no fake independence'}


def export_records(manifest, records, receipt, suffix, *, include_configs=False):
    source, root = Path(manifest['source']), Path(manifest['raw'])
    branch = 'codex/lanl17-' + suffix + '-evidence-' + manifest['tag']
    checkout = Path('/data1/yanruj/ArchEvolve-lanl17-' + suffix + '-evidence-' + manifest['tag'])
    assert not checkout.exists()
    git(source, 'worktree', 'add', '-b', branch, checkout, manifest['source_commit'])
    paths = []
    for file in sorted(Path(records).rglob('*.yaml')):
        rel = file.relative_to(records)
        destination = checkout / 'swdb-project/records' / rel
        if destination.exists():
            assert sha(destination) == sha(file), 'Never replace historical canonical record bytes'
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, destination)
        paths.append(destination.relative_to(checkout).as_posix())
    evidence = checkout / EVIDENCE
    path = evidence / ('17-' + suffix + '-mbit10-' + manifest['tag'] + '.json')
    assert not path.exists()
    dump(path, receipt)
    paths.append(path.relative_to(checkout).as_posix())
    if include_configs:
        destination = evidence / ('17-frozen-configs-' + manifest['tag'])
        shutil.copytree(root / 'configs', destination)
        paths.extend(file.relative_to(checkout).as_posix() for file in sorted(destination.rglob('*')) if file.is_file())
    assert paths and all(path.startswith('swdb-project/') for path in paths)
    git(checkout, 'add', '--', *paths)
    git(checkout, 'diff', '--cached', '--check')
    git(checkout, 'commit', '-m', 'Retain prospective agreement ' + suffix + ' metadata')
    git(checkout, 'push', '-u', 'origin', branch)
    assert not git(checkout, 'status', '--porcelain')
    return {'branch': branch, 'commit': git(checkout, 'rev-parse', 'HEAD'), 'paths': paths, 'raw_transferred': False}


def cleanup_proof(path, *, source=None):
    path = Path(path).resolve(strict=True)
    assert str(path).startswith('/data/yanruj/EvolveSWDB_runs/') and path.is_file()
    receipt = checked_json(path)
    assert receipt['format'] == 'swdb.lanl17-linux-cleanup-smoke.v1' and receipt['passed'] is True
    assert receipt['helper_sha256'] == sha(__file__) and receipt['smoke_script_sha256'] == LINUX_SMOKE_SHA
    assert receipt['platform'] == 'linux' and receipt['host'] == 'mbit10'
    assert receipt['unrelated_sibling_survived'] is True and receipt['cleanup']['survivors'] == {}
    assert receipt['provider_calls'] == receipt['application_outcomes'] == 0
    assert set(receipt['owned_before']) == {'same_group', 'escaped_session'}
    assert re.fullmatch('[0-9a-f]{64}', receipt['processes_py_sha256'])
    if source is not None:
        assert receipt['processes_py_sha256'] == sha(Path(source) / 'swdb-project/swdb/processes.py'), 'Final source stop_group bytes differ from tested Linux cleanup proof'
    return {'path': str(path), 'sha256': sha(path), 'receipt': receipt}


def prepare(args):
    host()
    assert re.fullmatch('[0-9a-f]{40}', args.source_sha)
    assert re.fullmatch('[a-z0-9-]+', args.tag)
    source, raw = Path(args.source), Path(args.raw)
    assert str(source).startswith('/data1/yanruj/') and str(raw).startswith('/data/yanruj/EvolveSWDB_runs/')
    assert not source.exists() and not raw.exists(), 'Fresh source/raw only; preserve earlier attempts'
    cleanup = cleanup_proof(args.cleanup_proof)
    login = login_home(os.environ.get('CODEX_HOME'))
    original_home = os.environ.get('HOME')
    lease_rows = all_free()
    resource = capacity()
    wrapper = wrapper_identity(fetch=True)
    for executable in ('tmux', 'numactl', 'strace', 'timeout'):
        assert shutil.which(executable), executable
    git(PRIMARY, 'fetch', 'origin', args.source_ref)
    assert git(PRIMARY, 'rev-parse', args.source_sha + '^{commit}') == args.source_sha
    git(PRIMARY, 'worktree', 'add', '--detach', source, args.source_sha)
    clean(source, args.source_sha)
    assert cleanup_proof(args.cleanup_proof, source=source) == cleanup
    artifacts, adapters, guard, estimator, Store = modules(source)
    assert guard.abi() >= 4
    provider = provider_identity(adapters)
    raw.mkdir()
    (raw / 'temporary').mkdir()
    base = raw / 'base'
    base.mkdir()
    shutil.copytree(source / 'swdb-project/records', base / 'records')
    shutil.copytree(source / 'swdb-project/library', base / 'library')
    before = inventory(base / 'records')
    library = inventory(base / 'library')
    from swdb import campaign, yamlio
    config_dir = raw / 'configs'
    config_dir.mkdir()
    configs = []
    for cid in CIDS:
        data = yamlio.load(source / CONFIGS / (cid + '.yaml'))
        assert data['id'] == cid and data['budgets'] == {'max_iterations': 8, 'plateau_iterations': 4, 'lane_hours': 24,
            'provider_calls_per_iteration': 3, 'provider_calls_setup': 1, 'disk_gb': 20, 'lanes': 1}
        assert data['paired_estimates'] == {'enabled': True} and data['protocol']['sources'] == [0]
        data['runs_root'] = str(raw / 'campaign-runs')
        assert not campaign.campaign_problems(data)
        (config_dir / (cid + '.yaml')).write_text(yamlio.dumps(data))
        configs.append(data)
    shutil.copyfile(source / CONFIGS / 'provider-codex.yaml', config_dir / 'provider-codex.yaml')
    pins = metadata_pins(Store(base / 'records'), configs)
    manifest = seal({'format': 'swdb.lanl17-parent-population.v1', 'created_utc': now(), 'tag': args.tag,
        'source': str(source), 'source_commit': args.source_sha, 'source_clean': True, 'raw': str(raw),
        'estimator_sha256': estimator(), 'original_environment_home': original_home, 'provider_login_home': login,
        'provider': provider, 'wrapper': wrapper, 'leases_before_freeze': lease_rows, 'capacity_before_freeze': resource,
        'configuration_files': inventory(config_dir), 'input_model_baseline_pins': pins,
        'initial_record_files': before, 'initial_library_files': library, 'helper_sha256': sha(__file__),
        'linux_cleanup_proof': cleanup,
        'scope': 'Prospective population; no application outcomes before public policy and Git export. Numeric bridge unsupported.'})
    dump(raw / 'manifest-before-freeze.json', manifest)
    env = environment(source, raw)
    run_cli(source, raw, 'validate-before-freeze', ['python3', '-m', 'swdb', 'validate', '--records', base / 'records'], 3600, env)
    argv = ['python3', '-m', 'swdb', 'agreement-freeze']
    for cid in CIDS:
        argv.extend(['--campaign-file', config_dir / (cid + '.yaml')])
    argv.extend(['--provider-config', config_dir / 'provider-codex.yaml', '--records', base / 'records',
                 '--mode', 'extensa', '--campaign', CIDS[0], '--format', 'json'])
    policy = json.loads(run_cli(source, raw, 'population-freeze', argv, 6000, env))
    assert policy['estimator_sha256'] == manifest['estimator_sha256']
    after = inventory(base / 'records')
    assert all(after.get(key) == value for key, value in before.items())
    additions = {key: value for key, value in after.items() if key not in before}
    assert len([key for key in additions if key.endswith('.yaml')]) == 1
    manifest = seal({**{k: v for k, v in manifest.items() if k != 'identity_sha256'},
                     'policy': {'id': policy['id'], 'identity_sha256': policy['identity_sha256'], 'frozen_at': policy['frozen_at']},
                     'frozen_base_record_files': after})
    freeze_receipt = seal({'format': 'swdb.lanl17-freeze-receipt.v1', 'checked_utc': now(), 'manifest': manifest,
                          'public_policy': policy, 'application_outcomes_opened': 0, 'population_frozen': True,
                          'scope': 'Exact source-only source/input/model/provider population and unchanged D30 policy; no numeric admission.'})
    exported = export_records(manifest, base / 'records', freeze_receipt, 'freeze', include_configs=True)
    manifest = seal({**{k: v for k, v in manifest.items() if k != 'identity_sha256'}, 'freeze_export': exported})
    dump(raw / 'manifest.json', manifest)
    for cid in CIDS:
        catalog = raw / 'catalogs' / cid
        catalog.mkdir(parents=True)
        shutil.copytree(base / 'records', catalog / 'records')
        shutil.copytree(base / 'library', catalog / 'library')
    clean(source, args.source_sha)
    all_free()
    print(json.dumps({'manifest': str(raw / 'manifest.json'), 'source_commit': args.source_sha,
                      'policy': manifest['policy'], 'freeze_export': exported, 'dispatches': 0}))


def load_manifest(path):
    host()
    data = checked_json(path)
    assert sha(__file__) == data['helper_sha256'], 'Frozen launcher recipe changed; preserve the original helper'
    source, raw = Path(data['source']), Path(data['raw'])
    assert cleanup_proof(data['linux_cleanup_proof']['path'], source=source) == data['linux_cleanup_proof'], 'Actual bounded Linux cleanup proof or final stop_group source changed'
    assert Path(path).resolve(strict=True) == (raw / 'manifest.json').resolve(strict=True), 'Use the retained canonical manifest path'
    clean(source, data['source_commit'])
    artifacts, adapters, guard, estimator, Store = modules(source)
    assert estimator() == data['estimator_sha256'] and inventory(raw / 'configs') == data['configuration_files']
    assert provider_identity(adapters) == data['provider']
    current_wrapper = wrapper_identity(fetch=True)
    assert all(current_wrapper[key] == data['wrapper'][key] for key in ('path', 'sha256')), 'Wrapper bytes changed; parent reviews before resumption'
    assert inventory(raw / 'base/library') == data['initial_library_files']
    base_records = inventory(raw / 'base/records')
    # Later final report adds only typed metadata, while policy/source/input pins remain immutable.
    assert all(base_records.get(key) == value for key, value in data['frozen_base_record_files'].items())
    policy = Store(raw / 'base/records').get(data['policy']['id'], 'agreement_policy')
    assert policy and policy['identity_sha256'] == data['policy']['identity_sha256']
    assert data['freeze_export']['commit'] and data['freeze_export']['branch']
    from swdb import yamlio
    configs = [yamlio.load(raw / 'configs' / (cid + '.yaml')) for cid in CIDS]
    live_pins = metadata_pins(Store(raw / 'base/records'), configs)
    assert live_pins == data['input_model_baseline_pins'], 'Live SG/baseline/model/runtime/config files differ from frozen pins'
    return data


def own_other(manifest, row, node, *, proc_root=None, node_file=None, lease_root=None):
    """Verify the actual bash socket_lane holder, its recorded child and this population's attempt."""
    if row['state'] == 'released':
        return False
    assert row['state'] == 'held'
    lease = row['lease']
    pid = lease['daemon_pid']
    assert type(pid) is int and pid > 1 and lease['lease_name'] == f'mbit10-evaluation-node{node}'
    proc = Path(proc_root or '/proc') / str(pid)
    assert proc.stat().st_uid == os.getuid()
    stamp = (proc / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    argv = proc.joinpath('cmdline').read_bytes().decode().rstrip('\0').split('\0')
    assert argv[:3] == ['bash', manifest['wrapper']['path'], str(node)]
    assert argv.count('--record') == 1 and argv.count('--') == 1
    record_path = Path(argv[argv.index('--record') + 1])
    attempt = record_path.parent.resolve(strict=True)
    relative = attempt.relative_to(Path(manifest['raw']).resolve(strict=True) / 'attempts')
    assert len(relative.parts) == 2 and relative.parts[0] in CIDS
    assert re.fullmatch(r'attempt-[1-9][0-9]*', relative.parts[1]) and record_path.name == 'lane.json'
    registration = checked_json(attempt / 'dispatch-preregistration.json')
    assert registration['manifest_sha256'] == manifest['identity_sha256'] and registration['node'] == node
    assert registration['campaign'] == relative.parts[0] and registration['attempt'] == int(relative.parts[1].split('-')[1])
    session = 'swdb-lanl17-' + manifest['tag'] + '-p' + registration['campaign'][-1] + '-a' + str(registration['attempt'])
    assert argv[3] == session
    helper = attempt / 'helper.py'
    assert sha(helper) == manifest['helper_sha256']
    child_argv = ['env', HOME_TOKEN + '=' + manifest['provider_login_home']['configured_value'],
        'python3', str(helper), 'run-campaign', '--manifest', str(Path(manifest['raw']) / 'manifest.json'),
        '--attempt-root', str(attempt)]
    assert argv[argv.index('--') + 1:] == child_argv
    lane = json.loads(record_path.read_text())['socket_lane']
    cpus = Path(node_file or f'/sys/devices/system/node/node{node}/cpulist').read_text().strip()
    assert lane['job'] == session and lane['node'] == node and lane['lease_name'] == lease['lease_name']
    assert lane['lease_generation'] == lease['generation'] and lane['exit_code'] == -1
    assert lane['command'] == child_argv and lane['cpus_allowed_list'] == cpus and lane['numa_memory_policy'] == f'bind:{node}'
    root = Path(lease_root or LEASE_ROOT)
    assert os.readlink(proc / 'fd/9') == str(root / (f'mbit10-evaluation-node{node}.lease'))
    status = dict(line.split(':', 1) for line in (proc / 'status').read_text().splitlines() if ':' in line)
    assert status['Cpus_allowed_list'].strip() == cpus
    assert (proc / 'numa_maps').read_text().splitlines()[0].split()[1] == f'bind:{node}'
    assert (proc / 'stat').read_text().rsplit(')', 1)[1].split()[19] == stamp, 'Holder PID identity changed'
    return True


def dispatch(args):
    manifest = load_manifest(args.manifest)
    raw, source = Path(manifest['raw']), Path(manifest['source'])
    cid = args.campaign
    rows = leases()
    assert rows['mbit10-evaluation']['state'] == rows[f'mbit10-evaluation-node{args.node}']['state'] == 'released'
    active = own_other(manifest, rows[f'mbit10-evaluation-node{1 - args.node}'], 1 - args.node)
    resources = capacity(active)
    original_login = login_home(os.environ.get('CODEX_HOME'))
    assert original_login == manifest['provider_login_home'] and os.environ.get('HOME') == manifest['original_environment_home']
    assert args.attempt >= 1
    attempt = raw / 'attempts' / cid / f'attempt-{args.attempt}'
    assert not attempt.exists(), 'Never overwrite stopped attempts'
    attempt.mkdir(parents=True)
    (attempt / 'temporary').mkdir()
    existing = raw / 'campaign-runs/extensa' / cid / 'state.json'
    assert existing.exists() == args.resume, 'Fresh dispatch/resume must match retained campaign state'
    session = 'swdb-lanl17-' + manifest['tag'] + '-p' + cid[-1] + '-a' + str(args.attempt)
    checked = seal({'format': 'swdb.lanl17-campaign-dispatch.v1', 'checked_utc': now(), 'manifest_sha256': manifest['identity_sha256'],
        'source_commit': manifest['source_commit'], 'estimator_sha256': manifest['estimator_sha256'], 'policy': manifest['policy'],
        'campaign': cid, 'node': args.node, 'resume': args.resume, 'baselines_only': args.baselines_only,
        'attempt': args.attempt, 'leases': rows, 'capacity': resources, 'original_environment_home': manifest['original_environment_home'],
        'provider_login_home': original_login, 'limits': {'child_s': CAMPAIGN_S, 'outer_s': OUTER_S,
                                                       'iterations': 8, 'plateau': 4, 'lane_hours': 24, 'disk_gb': 20},
        'scope': 'Actual Extensa flow A; estimate unknowns are not eligible pairs; timing-only selection unchanged.'})
    dump(attempt / 'dispatch-preregistration.json', checked)
    # External inspected helper is preserved byte-identically with each stopped attempt.
    shutil.copyfile(__file__, attempt / 'helper.py')
    argv = ['timeout', '--signal=TERM', '--kill-after=60s', str(OUTER_S) + 's', 'bash', manifest['wrapper']['path'],
            str(args.node), session, '--record', str(attempt / 'lane.json'), '--lease-timeout-s', '30']
    if not active:
        argv.append('--no-align')
    argv.extend(['--', 'env', HOME_TOKEN + '=' + original_login['configured_value'], 'python3', str(attempt / 'helper.py'),
                 'run-campaign', '--manifest', str(args.manifest), '--attempt-root', str(attempt)])
    shell = ' '.join(shlex.quote(value) for value in argv)
    shell += ' > ' + shlex.quote(str(attempt / 'wrapper.stdout')) + ' 2> ' + shlex.quote(str(attempt / 'wrapper.stderr'))
    shell += '; lanl17_exit=$?; printf "%s\\n" "$lanl17_exit" > ' + shlex.quote(str(attempt / 'wrapper.exit-code.txt'))
    # Recheck immediately before the wrapper acquires its authoritative lock.
    live = leases()
    assert live['mbit10-evaluation']['state'] == live[f'mbit10-evaluation-node{args.node}']['state'] == 'released'
    own_other(manifest, live[f'mbit10-evaluation-node{1 - args.node}'], 1 - args.node)
    command(['tmux', 'new-session', '-d', '-s', session, shell])
    print(json.dumps({'campaign': cid, 'attempt_root': str(attempt), 'session': session,
                      'source_commit': manifest['source_commit'], 'policy': manifest['policy'], 'node': args.node}))


def own_processes():
    """Only descendants/adopted orphans of this isolated subreaper, with UID/start-time identity."""
    rows = {}
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            rest = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
            rows[int(proc.name)] = {'ppid': int(rest[1]), 'start_time': rest[19]}
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    found, roots = {}, {os.getpid()}
    while True:
        additions = {pid: row for pid, row in rows.items() if pid not in roots and row['ppid'] in roots}
        if not additions:
            return found
        found.update(additions)
        roots.update(additions)


def cleanup_owned():
    terminated = []
    for sig, wait_s in ((signal.SIGTERM, 15), (signal.SIGKILL, 5)):
        remaining = own_processes()
        for pid, row in remaining.items():
            try:
                current = own_processes().get(pid)
                if current and current['start_time'] == row['start_time']:
                    os.kill(pid, sig)
                    terminated.append({'pid': pid, 'start_time': row['start_time'], 'signal': sig.name})
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            while True:
                try:
                    pid, _ = os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    break
                if not pid:
                    break
            if not own_processes():
                break
            time.sleep(0.1)
    return {'subreaper': True, 'terminated_owned_processes': terminated, 'survivors': own_processes()}


def run_campaign(args):
    host()
    root = Path(args.attempt_root)
    registration = checked_json(root / 'dispatch-preregistration.json')
    # Restore only the verified provider configuration path, never account HOME.
    token = os.environ.pop(HOME_TOKEN, None)
    assert token == registration['provider_login_home']['configured_value']
    assert login_home(token) == registration['provider_login_home']
    assert os.environ.get('HOME') == registration['original_environment_home']
    os.environ['CODEX_HOME'] = token
    manifest = load_manifest(args.manifest)
    assert registration['manifest_sha256'] == manifest['identity_sha256']
    from swdb import provider_guard, provider_login
    assert provider_login.provider_home('codex').resolve() == LOGIN_HOME.resolve(strict=True)
    assert provider_guard.verified_lane().startswith(f"mbit10-evaluation-node{registration['node']} (verified:")
    assert ctypes.CDLL(None).prctl(36, 1, 0, 0, 0) == 0, 'Require isolated launcher subreaper'
    source, raw = Path(manifest['source']), Path(manifest['raw'])
    cid = registration['campaign']
    argv = ['python3', '-m', 'swdb', 'campaign', raw / 'configs' / (cid + '.yaml'),
            '--records', raw / 'catalogs' / cid / 'records', '--library', raw / 'catalogs' / cid / 'library',
            '--provider-config', raw / 'configs/provider-codex.yaml', '--runs-root', raw / 'campaign-runs', '--format', 'json']
    for name in ('resume', 'baselines_only'):
        if registration[name]:
            argv.append('--' + name.replace('_', '-'))
    dump(root / 'campaign.argv.json', list(map(str, argv)))
    status, error, child = 1, None, None
    started = now()
    def interrupted(signum, frame):
        raise InterruptedError('Owned launcher signal ' + str(signum))
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, interrupted)
    try:
        with (root / 'campaign.stdout').open('w') as out, (root / 'campaign.stderr').open('w') as err:
            child = subprocess.Popen(list(map(str, argv)), cwd=source / 'swdb-project', env=environment(source, root),
                                     stdout=out, stderr=err, start_new_session=True)
            status = child.wait(timeout=CAMPAIGN_S)
        clean(source, manifest['source_commit'])
    except BaseException as exc:
        error = type(exc).__name__ + ': ' + str(exc)
        status = 1
    finally:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, signal.SIG_IGN)
        from swdb.processes import stop_group
        stop_group(child, grace_seconds=15)
        cleanup = cleanup_owned()
        if cleanup['survivors']:
            status = 1
        from swdb.estimate_protocol import estimator_identity
        stopped = seal({'format': 'swdb.lanl17-stopped-attempt.v1', 'started_utc': started, 'ended_utc': now(),
            'campaign': cid, 'source_commit': manifest['source_commit'], 'policy': manifest['policy'],
            'manifest_sha256': manifest['identity_sha256'], 'dispatch_sha256': registration['identity_sha256'],
            'argv_sha256': sha(root / 'campaign.argv.json'), 'runner_exit_code': status,
            'public_exit_code': child.returncode if child is not None else None, 'infrastructure_error': error,
            'process_cleanup': cleanup, 'original_codex_home_restored': True, 'account_home_unchanged': True,
            'source_clean_after': not git(source, 'status', '--porcelain'), 'estimator_sha256_after': estimator_identity(),
            'raw_transferred': False, 'scope': 'Actual stopped attempt; no inferred completion, unique pairs or D30 success.'})
        dump(root / 'stopped-receipt.json', stopped)
        (root / 'runner.exit-code.txt').write_text(str(status) + '\n')
    return status


def finalize(args):
    manifest = load_manifest(args.manifest)
    source, raw = Path(manifest['source']), Path(manifest['raw'])
    all_free()
    artifacts, adapters, guard, estimator, Store = modules(source)
    stopped = []
    for cid in CIDS:
        rows = sorted((raw / 'attempts' / cid).glob('attempt-*/stopped-receipt.json'))
        assert rows, 'Need actual stopped attempt receipts for all four prospective campaigns'
        stopped.extend(checked_json(path) for path in rows)
        folder = raw / 'campaign-runs/extensa' / cid / 'records'
        assert folder.is_dir(), 'Do not substitute fixtures or old stores for a failed setup'
        assert Store(folder).get(cid + '.summary', 'campaign_summary'), 'Resume incomplete actual trajectory; never manufacture a summary'
        run_cli(source, raw, 'validate-' + cid, ['python3', '-m', 'swdb', 'validate', '--records', folder], 3600)
        summary = Store(folder).get(cid + '.summary', 'campaign_summary')
        assert summary['evidence_kind'] == 'execution' and summary['target'] == 'dx100_gem5'
        # Export named non-rejected candidate closures through the public command.
        from swdb.extensa_boundary import certification_level
        ids = {row['id'] for iteration in summary['iterations'] for row in iteration['candidates'] if row.get('id')}
        ids = sorted(rid for rid in ids if certification_level(Store(folder), rid)['level'] != 'rejected')
        if ids:
            argv = ['python3', '-m', 'swdb', 'campaign-export', raw / 'configs' / (cid + '.yaml'),
                    '--records', raw / 'base/records', '--runs-root', raw / 'campaign-runs', '--format', 'json']
            for rid in ids:
                argv.extend(['--candidate', rid])
            run_cli(source, raw, 'export-' + cid, argv, 6000)
    argv = ['python3', '-m', 'swdb', 'agreement-report', '--policy', manifest['policy']['id'],
            '--records', raw / 'base/records', '--mode', 'extensa', '--campaign', CIDS[0], '--format', 'json']
    for cid in CIDS:
        argv.extend(['--campaign-records', raw / 'campaign-runs/extensa' / cid / 'records'])
    report = json.loads(run_cli(source, raw, 'final-agreement-report', argv, 14400))
    assert report['counts']['unique_eligible_dx100_pairs'] == 0 and report['gate']['state'] == 'unsupported'
    assert report['recommendation'] == 'do_not_switch_to_flow_b' and report['selection_policy'] == 'unchanged_timing_only'
    assert report['counts']['observed_campaigns'] == 4
    run_cli(source, raw, 'validate-final-export', ['python3', '-m', 'swdb', 'validate', '--records', raw / 'base/records'], 3600)
    receipt = seal({'format': 'swdb.lanl17-actual-agreement-compact.v1', 'checked_utc': now(),
                    'manifest': manifest, 'stopped_attempts': stopped, 'public_report': report,
                    'raw_transferred': False, 'source_clean': not git(source, 'status', '--porcelain'),
                    'scope': 'Four actual validated fresh campaign stores; unavailable numeric agreement and unchanged flow-A policy. No-switch recommendation; Yan-Ru final decision remains human.'})
    result = export_records(manifest, raw / 'base/records', receipt, 'actual-report')
    dump(raw / 'final-export.json', result)
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    p = commands.add_parser('prepare')
    p.add_argument('--source-sha', required=True)
    p.add_argument('--cleanup-proof', required=True)
    p.add_argument('--source-ref', required=True)
    p.add_argument('--source', required=True)
    p.add_argument('--raw', required=True)
    p.add_argument('--tag', required=True)
    p = commands.add_parser('dispatch')
    p.add_argument('--manifest', required=True)
    p.add_argument('--campaign', choices=CIDS, required=True)
    p.add_argument('--node', choices=(0, 1), type=int, required=True)
    p.add_argument('--attempt', type=int, required=True)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--baselines-only', action='store_true')
    p = commands.add_parser('run-campaign')
    p.add_argument('--manifest', required=True)
    p.add_argument('--attempt-root', required=True)
    p = commands.add_parser('finalize')
    p.add_argument('--manifest', required=True)
    args = parser.parse_args()
    if args.action == 'run-campaign':
        sys.exit(run_campaign(args))
    {'prepare': prepare, 'dispatch': dispatch, 'finalize': finalize}[args.action](args)


if __name__ == '__main__':
    main()
