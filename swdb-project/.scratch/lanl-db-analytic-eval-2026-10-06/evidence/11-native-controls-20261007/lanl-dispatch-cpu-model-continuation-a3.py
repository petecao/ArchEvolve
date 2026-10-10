"""Conditional metadata-only model continuation. Import is inert; parent dispatches only after failed a1 custody."""
import argparse
import ctypes
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time

C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
BUNDLE = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
SOURCE = Path('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1')
FAILED = Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a2')
RAW = Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a3')
CLEANUP = Path('/data1/yanruj/lanl17-control-20261006.py')
CLEANUP_SHA = '31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
PROCESS_SHA = 'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
TARGET = 'mbit10.cpu.lanl20261006.t1.services.v1'
CALIBRATIONS = ['mbit10.cpu.lanl20261006.' + name for name in (
    'service.clock.a2', 'resource.allocator.a1', 'resource.allocator-extra.a1',
    'resource.memory.a1', 'resource.float-memory.a1', 'service.byte-read.a1',
    'resource.bulk-total.a1', 'resource.bulk-total.a2', 'service.openmp.a1')]
CHARS = {(k, g): k + '.kron-g' + str(g) + '.t1.characterization.objects.a1'
         for g in (16, 17) for k in ('bfs', 'bc')}
CHAR_HASHES = {
    CHARS['bfs', 16]: '535d43719d2e9269dc557e900886c625b80c5aa686e7682861a4f6d045e143bc',
    CHARS['bc', 16]: '8561948088366aa18409da1db1f204ac2579cdb8ee90f1a2c76079a96e2eb4fd',
    CHARS['bfs', 17]: '49b5c58f3551b065c91c49c1fb09f54de2d2d71f08b6a4e1eedf3aad5ec415c5',
    CHARS['bc', 17]: '6b8d515b3f38a13bfd302993f8ac5e88bd77615da171c710b4ecd81d058c67db'}
ESTIMATES = {(k, g): 'lanl.cpu.' + k + '.g' + str(g) + '.t1.estimate.v1' for k, g in CHARS}
INNER_S, OUTER_S, META_S, VALIDATE_S = 15000, 15200, 1800, 1400
ALLOWED = {'freeze-protocol', 'estimate', 'validate'}
ORIGINAL_A1_RAW = Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a1')
ORIGINAL_A1_IDENTITY = '8ddb9825fb7ccefff7088ea550af290379f8ea48744065b9d156196b7947db5a'
ACTIVE_A2_SHA = '181f6c9d4000e6a85d5686afe2e6487d6c78908b1e8c0d47faae49c2fa04b4ee'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def sealed(value):
    assert value['identity_sha256'] == digest({k: v for k, v in value.items() if k != 'identity_sha256'}), 'custody seal changed'
    return value


def inventory(folder):
    return {p.relative_to(folder).as_posix(): sha(p) for p in sorted(Path(folder).rglob('*.yaml'))}


def preserve(folder, manifest):
    assert all((Path(folder) / rel).is_file() and sha(Path(folder) / rel) == value for rel, value in manifest.items()), 'completed canonical bytes changed'


def metadata_argv(args):
    args = list(map(str, args))
    assert args[:3] == ['python3', '-m', 'swdb'] and len(args) > 3 and args[3] in ALLOWED, 'only metadata public commands allowed'
    assert '--fixture' not in args and '--baseline' not in args and '--cpu-error-band' not in args
    return args


def request(kernel, chars):
    selected = [chars[CHARS[kernel, g]] for g in (16, 17)]
    assert len({c['subject']['id'] for c in selected}) == 1
    argv = {c['input']: c['source']['run_arguments'] for c in selected}
    assert len(argv) == 2
    return {'message_version': '1.0', 'id': 'lanl.cpu.' + kernel + '.t1.native-model.v1', 'version': 1,
        'settings': {'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1', 'target_description': TARGET,
            'inputs': list(argv), 'input_run_arguments': argv, 'sources': [selected[0]['subject']['id']],
            'roi': 'gapbs.trial_lambda.v1', 'threads': 1}}


def select_protocol(kernel, records, wanted):
    matches = [r for r in records if r['kind'] == 'protocol' and r.get('requested_id') == wanted['id']]
    assert len(matches) <= 1, 'ambiguous completed protocol'
    if not matches:
        return None
    p = matches[0]
    assert p['version'] == 1 and p['supersedes'] is None and p['state'] == 'frozen'
    assert p['id'] == wanted['id'] + '.' + p['identity_sha256'][:16]
    for key, value in wanted['settings'].items():
        if key != 'target_description':
            assert p['settings'][key] == value, 'completed protocol scope/argv changed: ' + key
    assert p['settings']['estimator_sha256'] == BUNDLE
    assert 'cpu_error_band' not in p['settings'], 'outcome-free model cannot pin a band'
    return p


def estimate_guard(e, char, protocol, target):
    assert e['kind'] == 'estimate' and e['format'] == 'swdb.estimate.v1'
    expected = {'characterization': char['id'], 'characterization_sha256': digest(char),
        'protocol': protocol['id'], 'protocol_sha256': protocol['identity_sha256'],
        'target_description': TARGET, 'target_description_sha256': digest(target),
        'estimator_sha256': BUNDLE, 'threads': 1, 'evidence_kind': 'execution',
        'input': char['input'], 'subject': char['subject'], 'target': target['target']}
    assert all(e.get(k) == v for k, v in expected.items()), 'completed estimate pins changed'
    assert e.get('target_description_snapshot') == target and e.get('binding') == char['binding']
    assert e.get('error_band') is None
    assert type(e.get('seconds')) in (int, float) and math.isfinite(e['seconds']) and e['seconds'] > 0, 'complete failed/null estimate is not recoverable processing work'


def estimate_command(existing, char, protocol, target, records):
    if existing is not None:
        estimate_guard(existing, char, protocol, target)
        return None
    pair = next(pair for pair, rid in CHARS.items() if rid == char['id'])
    return metadata_argv(['python3', '-m', 'swdb', 'estimate', '--records', records,
        '--characterization', char['id'], '--target-description', TARGET,
        '--protocol', protocol['id'], '--id', ESTIMATES[pair], '--format', 'json'])


def freeze_command(existing, path, records):
    if existing is not None:
        return None
    return metadata_argv(['python3', '-m', 'swdb', 'freeze-protocol', path,
        '--records', records, '--format', 'json'])


def failure_guard(receipt, failed=None):
    failed = FAILED if failed is None else Path(failed)
    sealed(receipt)
    assert receipt['source_commit'] == C and receipt['raw_directory'] == str(failed) and receipt['phase'] == 'model'
    assert receipt['cause'] == 'metadata_processing_cap' and receipt['application_performance_timings_collected'] is False
    assert not (failed / 'acceptance.json').exists(), 'successful a2 must not be resumed'
    pre = json.loads((failed / 'preregistration.json').read_text())
    assert pre['phase'] == 'model' and pre['source_commit'] == C and pre['source_clean'] is True
    # Conditional a3 requires the actual failed a2 and its unchanged original a1 custody.
    assert receipt['original_a1_failure_custody_identity'] == ORIGINAL_A1_IDENTITY
    original = sealed(json.loads((failed / 'failure-custody.json').read_text()))
    assert original['identity_sha256'] == ORIGINAL_A1_IDENTITY
    assert original['source_commit'] == C and original['raw_directory'] == str(ORIGINAL_A1_RAW) and original['phase'] == 'model'
    assert original['cause'] == 'metadata_processing_cap' and original['application_performance_timings_collected'] is False
    sealed(pre)
    assert pre['continuation_helper_sha256'] == ACTIVE_A2_SHA == receipt['runner_py_sha256']
    assert pre['failure_custody_identity'] == ORIGINAL_A1_IDENTITY
    assert pre['scientific_recipe_changed'] is False and pre['native_or_provider_commands'] == 0
    assert pre['limits'] == {'runner_s':8000,'outer_s':8200,'metadata_stage_s':1100,'final_validate_s':1000,'scientific_collector_s_unchanged':900}
    preserve(failed / 'records', original['completed_record_files'])
    assert all(receipt['completed_record_files'].get(path)==sha for path,sha in original['completed_record_files'].items())
    error = (failed / 'runner-error.txt').read_text()
    assert sha(failed / 'runner-error.txt') == receipt['runner_error_sha256']
    assert sha(failed / 'runner.py') == receipt['runner_py_sha256']
    code = (failed / 'runner-exit-code.txt').read_text().strip()
    outer = (failed / 'exit-code.txt').read_text().strip()
    assert code != '0' and outer != '0', 'a2 must have ended unsuccessfully'
    late = False
    if error.startswith('AssertionError:'):
        began = datetime.datetime.fromisoformat((failed / 'started.txt').read_text().strip())
        ended = datetime.datetime.fromisoformat((failed / 'completed.txt').read_text().strip())
        late = error.strip() == 'AssertionError:' and (ended - began).total_seconds() >= pre['limits']['runner_s'] - 50
    assert error.startswith('TimeoutExpired:') or late or (outer in {'124', '137', '143'} and error.startswith('RuntimeError: runner signal ')), 'failure is not a documented processing cap'
    assert json.loads((failed / 'final-cleanup.json').read_text())['survivors'] == {}
    preserve(failed / 'records', receipt['completed_record_files'])
    assert inventory(failed / 'records') == receipt['completed_record_files'], 'a2 inventory changed since custody'
    return receipt


def command(args, **kwargs):
    return subprocess.check_output(list(map(str, args)), text=True, timeout=120, **kwargs).strip()


def git(*args):
    return command(['git', '-C', SOURCE, *args])


def clean():
    assert git('rev-parse', 'HEAD') == C and not git('status', '--porcelain')


def cleanup_module():
    assert sha(CLEANUP) == CLEANUP_SHA and sha(SOURCE / 'swdb-project/swdb/processes.py') == PROCESS_SHA
    proof = json.loads((SOURCE / 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-linux-cleanup-smoke-mbit10-20261006-a1.json').read_text())['receipt']
    assert proof['passed'] is True and proof['helper_sha256'] == CLEANUP_SHA and proof['processes_py_sha256'] == PROCESS_SHA and proof['cleanup']['survivors'] == {}
    spec = importlib.util.spec_from_file_location('cpu_model_a2_cleanup', CLEANUP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def admitted(store):
    from swdb import estimate_protocol
    assert estimate_protocol.estimator_identity() == BUNDLE
    chars = {rid: store.get(rid, 'workload_characterization') for rid in CHAR_HASHES}
    assert all(c and digest(c) == CHAR_HASHES[rid] for rid, c in chars.items()), 'frozen four-characterization allowlist changed'
    target = store.get(TARGET, 'target_description')
    assert target, 'completed binder target required; do not repeat binder'
    b = target['extensions']['cpu_services_binding']
    assert b['base']['id'] == 'mbit10.cpu.lanl20261006a2.v2.t1'
    assert b['base']['sha256'] == digest(store.get(b['base']['id'], 'target_description'))
    assert {r['id']: r['sha256'] for r in b['characterization_allowlist']} == CHAR_HASHES
    assert {r['id'] for r in b['calibrations']} == set(CALIBRATIONS) and len(b['calibrations']) == 9
    assert all(digest(store.get(r['id'])) == r['sha256'] for r in b['calibrations'])
    assert not [r for r in b['compatibility'] if r['missing'] or any(s['missing'] for s in r.get('scopes', []))]
    assert b['memory_selection']['footprint_bytes'] == 8388608 and b['memory_selection']['cas_policy'] == 'max_constructed_success_failure_median'
    assert b['bulk_selection']['profile_policy'] == 'max_constructed_profiles_median'
    assert b['bulk_selection']['copy_calibration'] == 'mbit10.cpu.lanl20261006.resource.bulk-total.a1'
    assert b['allocator_resource_selection'] == {'recipe': 'gross_allocator_loop_resource_v1', 'composition': 'max_with_counted_compute_resource', 'paired_rates_used': False}
    assert b['transfer_basis'] == 'inferred' and b['timings_rerun'] is False
    # The frozen target byte manifest preserves exact OpenMP selection/projection and every other recipe.
    return chars, target, b


def run_model():
    assert socket.gethostname().split('.')[0] == 'mbit10' and sys.platform == 'linux'
    clean()
    sys.dont_write_bytecode = True
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(RAW / 'compiler-temp'))
    sys.path.insert(0, str(SOURCE / 'swdb-project'))
    from swdb import artifacts, estimate_protocol, bfs_protocol
    from swdb.profile import _verified_lane
    from swdb.processes import stop_group
    from swdb.store import Store
    assert digest({'check': 1}) == artifacts.digest({'check': 1})
    cleanup = cleanup_module()
    assert ctypes.CDLL(None).prctl(36, 1, 0, 0, 0) == 0
    assert sha(Path(__file__)) == json.loads((RAW / 'preregistration.json').read_text())['continuation_helper_sha256']
    receipt = failure_guard(json.loads((RAW / 'failure-custody.json').read_text()))
    deadline = time.monotonic() + INNER_S
    child = None
    invocations, reused = [], []
    status = 0
    def interrupt(signum, frame):
        raise RuntimeError('runner signal ' + str(signum))
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, interrupt)
    def run(args, name, cap=META_S):
        nonlocal child
        args = metadata_argv(args)
        remaining = min(cap, deadline - time.monotonic() - 45)
        assert remaining > 0
        started = time.monotonic()
        with (RAW / (name + '.stdout')).open('w') as out, (RAW / (name + '.stderr')).open('w') as err:
            child = subprocess.Popen(args, cwd=SOURCE / 'swdb-project', stdout=out, stderr=err, start_new_session=True)
            try:
                code = child.wait(timeout=remaining)
            finally:
                stop_group(child, grace_seconds=15)
                child = None
                cleaned = cleanup.cleanup_owned()
                dump(RAW / (name + '.cleanup.json'), cleaned)
                assert cleaned['survivors'] == {}
        invocations.append({'stage': name, 'argv': args, 'seconds': time.monotonic() - started, 'exit_code': code})
        dump(RAW / 'metadata-invocations.json', invocations)
        assert code == 0, name + ' failed (not a native command)'
        return (RAW / (name + '.stdout')).read_text()
    try:
        (RAW / 'started.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n')
        shutil.copytree(FAILED / 'records', RAW / 'records')
        (RAW / 'library').symlink_to(SOURCE / 'swdb-project/library', target_is_directory=True)
        original = inventory(SOURCE / 'swdb-project/records')
        preserve(RAW / 'records', original)
        store = Store(RAW / 'records')
        assert not store.problems
        assert _verified_lane(store.get('mbit10', 'machine'), 'mbit10-evaluation-node0').startswith('mbit10-evaluation-node0 (verified:')
        chars, target, binding = admitted(store)
        reused.append({'kind': 'target_description', 'id': TARGET, 'sha256': digest(target)})
        protocols = {}
        for kernel in ('bfs', 'bc'):
            wanted = request(kernel, chars)
            path = RAW / (kernel + '-protocol-request.json')
            dump(path, wanted)
            p = select_protocol(kernel, [r.data for r in store.of_kind('protocol')], wanted)
            if p is None:
                out = json.loads(run(freeze_command(p, path, RAW / 'records'), 'freeze-' + kernel))
                store = Store(RAW / 'records')
                p = select_protocol(kernel, [r.data for r in store.of_kind('protocol')], wanted)
                assert p and digest(p) == digest(out)
            else:
                reused.append({'kind': 'protocol', 'id': p['id'], 'sha256': digest(p)})
            bfs_protocol.verify_immutable(p)
            estimate_protocol.validate_frozen(p, store)
            assert p['settings']['target_description'] == {'id': TARGET, 'sha256': digest(target), 'snapshot': target}
            for g in (16, 17):
                estimate_protocol.bind(store, p['id'], chars[CHARS[kernel, g]], target)
            protocols[kernel] = p
        rows = []
        for (k, g), rid in ESTIMATES.items():
            char = chars[CHARS[k, g]]
            e = store.get(rid, 'estimate')
            args = estimate_command(e, char, protocols[k], target, RAW / 'records')
            if args is not None:
                out = json.loads(run(args, 'estimate-' + k + '-g' + str(g)))
                store = Store(RAW / 'records')
                e = store.get(rid, 'estimate')
                assert e and digest(e) == digest(out)
            else:
                reused.append({'kind': 'estimate', 'id': rid, 'sha256': digest(e)})
            assert e['id'] == rid
            estimate_guard(e, char, protocols[k], target)
            rows.append({'id': rid, 'sha256': digest(e), 'seconds': e['seconds'], 'evidence_kind': e['evidence_kind'], 'protocol': e['protocol'], 'estimator_sha256': e['estimator_sha256'], 'target_description_sha256': e['target_description_sha256'], 'characterization_sha256': e['characterization_sha256']})
        validation = run(['python3', '-m', 'swdb', 'validate', '--records', RAW / 'records'], 'validate', VALIDATE_S).strip()
        assert validation.startswith('OK: ')
        preserve(RAW / 'records', original)
        preserve(RAW / 'records', receipt['completed_record_files'])
        added = [r.data for r in store.records if str(r.rel) not in original]
        assert sorted(r['kind'] for r in added) == ['estimate'] * 4 + ['protocol'] * 2 + ['target_description']
        assert {r['id'] for r in added} == {TARGET, *[p['id'] for p in protocols.values()], *ESTIMATES.values()}
        clean()
        summary = {'format': 'swdb.prospective-native-model-acceptance.v1', 'updated': '2026-10-07 ET', 'phase': 'model', 'source_commit': C, 'source_clean': True, 'raw_transferred': False, 'application_performance_timings_collected': False, 'ready_for_development': True, 'target_sha256': digest(target), 'estimator_sha256': BUNDLE, 'estimates': rows, 'protocols': {k: {'id': p['id'], 'sha256': digest(p)} for k, p in protocols.items()}, 'calibrations': binding['calibrations'], 'characterizations': binding['characterization_allowlist'], 'validation': validation, 'prior_record_bytes_preserved': len(original), 'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'continuation': {'failed_raw': str(FAILED), 'failure_custody_identity': receipt['identity_sha256'], 'original_a1_failure_custody_identity': ORIGINAL_A1_IDENTITY, 'preserved_complete_record_files': receipt['completed_record_files'], 'reused_complete_records': reused, 'metadata_invocations': invocations, 'scientific_recipe_changed': False, 'native_or_provider_commands': 0}}
        summary['identity_sha256'] = digest(summary)
        dump(RAW / 'acceptance.json', summary)
    except BaseException as exc:
        status = 1
        (RAW / 'runner-error.txt').write_text(type(exc).__name__ + ': ' + str(exc) + '\n')
    finally:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, signal.SIG_IGN)
        stop_group(child, grace_seconds=15)
        final = cleanup.cleanup_owned()
        dump(RAW / 'final-cleanup.json', final)
        if final['survivors']:
            status = 1
        (RAW / 'runner-exit-code.txt').write_text(str(status) + '\n')
        (RAW / 'completed.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n')
    return status


def dispatch(failure_path):
    assert socket.gethostname().split('.')[0] == 'mbit10' and sys.platform == 'linux' and os.getuid() != 0
    assert not RAW.exists()
    clean()
    cleanup = cleanup_module()
    lease = cleanup.all_free()
    wrapper = cleanup.wrapper_identity(fetch=True)
    capacity = cleanup.capacity()
    receipt = failure_guard(json.loads(Path(failure_path).read_text()))
    RAW.mkdir(parents=True)
    (RAW / 'compiler-temp').mkdir()
    dump(RAW / 'failure-custody.json', receipt)
    runner = RAW / 'runner.py'
    shutil.copyfile(Path(__file__), runner)
    facts = {'format': 'swdb.cpu-model-continuation-dispatch.v1', 'phase': 'model', 'source_commit': C, 'source_clean': True, 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'leases': lease, 'capacity': capacity, 'wrapper': wrapper, 'failure_custody_identity': receipt['identity_sha256'], 'original_a1_failure_custody_identity': ORIGINAL_A1_IDENTITY, 'continuation_helper_sha256': sha(runner), 'scientific_recipe_changed': False, 'native_or_provider_commands': 0, 'limits': {'runner_s': INNER_S, 'outer_s': OUTER_S, 'metadata_stage_s': META_S, 'final_validate_s': VALIDATE_S, 'scientific_collector_s_unchanged': 900}}
    facts['identity_sha256'] = digest(facts)
    dump(RAW / 'preregistration.json', facts)
    parts = ['timeout', '--signal=TERM', '--kill-after=20s', str(OUTER_S) + 's', 'bash', wrapper['path'], '0', 'swdb-lanl-cpu-model-20261006-a3', '--record', RAW / 'lane.json', '--', 'python3', runner, '--run']
    shell = ' '.join(shlex.quote(str(x)) for x in parts) + ' > ' + shlex.quote(str(RAW / 'dispatch.log')) + ' 2> ' + shlex.quote(str(RAW / 'dispatch-error.log')) + '; lanl_exit=$?; printf "%s\\n" "$lanl_exit" > ' + shlex.quote(str(RAW / 'exit-code.txt'))
    command(['tmux', 'new-session', '-d', '-s', 'swdb-lanl-cpu-model-20261006-a3', shell])
    print(json.dumps({'source_commit': C, 'phase': 'model', 'raw': str(RAW), 'preregistration_identity': facts['identity_sha256']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--failure-receipt', type=Path)
    group.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.run:
        return run_model()
    dispatch(args.failure_receipt)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
