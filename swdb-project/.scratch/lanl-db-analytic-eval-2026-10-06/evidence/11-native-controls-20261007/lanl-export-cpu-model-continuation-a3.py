"""Export only a successfully validated metadata continuation; parent runs after lane release."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import socket
import subprocess
import sys

C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
DISPATCH_SHA = '90f28f9ad2dd65f87e74d194d376e26e4af7bd45d654fdba8c8a633afb33b7bc'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    assert len(sys.argv) == 1 and socket.gethostname().split('.')[0] == 'mbit10' and sys.platform == 'linux'
    dispatcher = Path(__file__).with_name('lanl-dispatch-cpu-model-continuation-a3.py')
    assert sha(dispatcher) == DISPATCH_SHA, 'reviewed continuation helper differs'
    spec = importlib.util.spec_from_file_location('cpu_model_a2', dispatcher)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.clean()
    cleanup = module.cleanup_module()
    cleanup.all_free()
    source, raw = module.SOURCE, module.RAW
    checkout = Path('/data1/yanruj/ArchEvolve-lanl-cpu-model-evidence-20261006-a3')
    branch = 'codex/lanl-cpu-model-evidence-a3'
    assert not checkout.exists()
    assert (raw / 'runner-exit-code.txt').read_text().strip() == '0' and (raw / 'exit-code.txt').read_text().strip() == '0'
    assert json.loads((raw / 'final-cleanup.json').read_text())['survivors'] == {}
    lane = json.loads((raw / 'lane.json').read_text())['socket_lane']
    assert lane['exit_code'] == 0 and lane['ended_utc'] and lane['node'] == 0 and lane['numa_memory_policy'] == 'bind:0'
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / 'swdb-project'))
    from swdb import artifacts, access, bfs_protocol, estimate_protocol
    from swdb.store import Store
    assert artifacts.digest({'check': 1}) == module.digest({'check': 1})
    proof = module.sealed(json.loads((raw / 'acceptance.json').read_text()))
    assert proof['phase'] == 'model' and proof['source_commit'] == C and proof['source_clean'] is True
    assert proof['estimator_sha256'] == module.BUNDLE and proof['ready_for_development'] is True
    assert proof['raw_transferred'] is False and proof['application_performance_timings_collected'] is False
    assert proof['validation'].startswith('OK: ')
    pre = module.sealed(json.loads((raw / 'preregistration.json').read_text()))
    assert pre['source_commit'] == C and pre['source_clean'] is True and pre['continuation_helper_sha256'] == DISPATCH_SHA
    assert pre['native_or_provider_commands'] == 0 and pre['scientific_recipe_changed'] is False
    custody = module.failure_guard(json.loads((raw / 'failure-custody.json').read_text()))
    assert proof['continuation']['failure_custody_identity'] == pre['failure_custody_identity'] == custody['identity_sha256']
    assert proof['continuation']['original_a1_failure_custody_identity'] == pre['original_a1_failure_custody_identity'] == custody['original_a1_failure_custody_identity'] == module.ORIGINAL_A1_IDENTITY
    assert proof['continuation']['preserved_complete_record_files'] == custody['completed_record_files']
    assert proof['continuation']['native_or_provider_commands'] == 0 and proof['continuation']['scientific_recipe_changed'] is False
    module.preserve(raw / 'records', custody['completed_record_files'])
    prior = module.inventory(source / 'swdb-project/records')
    assert len(prior) == proof['prior_record_bytes_preserved']
    module.preserve(raw / 'records', prior)
    invocations = json.loads((raw / 'metadata-invocations.json').read_text())
    assert invocations == proof['continuation']['metadata_invocations']
    assert invocations and invocations[-1]['stage'] == 'validate'
    for row in invocations:
        module.metadata_argv(row['argv'])
        assert row['exit_code'] == 0
        assert json.loads((raw / (row['stage'] + '.cleanup.json')).read_text())['survivors'] == {}
    store = Store(raw / 'records')
    assert not store.problems
    chars, target, binding = module.admitted(store)
    assert artifacts.digest(target) == proof['target_sha256'] and proof['calibrations'] == binding['calibrations']
    assert proof['characterizations'] == binding['characterization_allowlist']
    protocols = {}
    for k in ('bfs', 'bc'):
        p = module.select_protocol(k, [r.data for r in store.of_kind('protocol')], module.request(k, chars))
        assert p and proof['protocols'][k] == {'id': p['id'], 'sha256': artifacts.digest(p)}
        bfs_protocol.verify_immutable(p)
        estimate_protocol.validate_frozen(p, store)
        for g in (16, 17):
            estimate_protocol.bind(store, p['id'], chars[module.CHARS[k, g]], target)
        protocols[k] = p
    assert len(proof['estimates']) == 4 and {r['id'] for r in proof['estimates']} == set(module.ESTIMATES.values())
    for (k, g), rid in module.ESTIMATES.items():
        e = store.get(rid, 'estimate')
        module.estimate_guard(e, chars[module.CHARS[k, g]], protocols[k], target)
        assert next(row for row in proof['estimates'] if row['id'] == rid)['sha256'] == artifacts.digest(e)
    for row in proof['continuation']['reused_complete_records']:
        assert artifacts.digest(store.get(row['id'], row['kind'])) == row['sha256']
    new = []
    for p in sorted((raw / 'records').rglob('*.yaml')):
        rel = p.relative_to(raw / 'records').as_posix()
        if rel in prior:
            continue
        data = access.read_record(p)
        new.append({'id': data['id'], 'kind': data['kind'], 'path': rel, 'sha256': artifacts.digest(data), 'file_sha256': sha(p), 'bytes': p.stat().st_size})
    assert sorted(row['kind'] for row in new) == ['estimate'] * 4 + ['protocol'] * 2 + ['target_description']
    assert {row['id'] for row in new} == {module.TARGET, *[p['id'] for p in protocols.values()], *module.ESTIMATES.values()}
    summary = {'format': 'swdb.prospective-native-model-compact-receipt.v1', 'updated': '2026-10-07 ET', 'phase': 'model', 'source_commit': C, 'source_clean': True, 'raw_directory': str(raw), 'raw_transferred': False, 'acceptance': proof, 'lane': lane, 'preregistration_sha256': sha(raw / 'preregistration.json'), 'new_records': new, 'prior_records_preserved': len(prior), 'matched_native_observations': [], 'continuation_helper_sha256': DISPATCH_SHA, 'failure_custody': custody, 'original_a1_failure_custody': module.sealed(json.loads((module.FAILED / 'failure-custody.json').read_text())), 'scope': 'Metadata-only continuation after sole processing-cap failure. Complete a1 outputs preserved; missing writes only. Scientific/native recipes unchanged; no application performance timings or provider invocation.'}
    summary['identity_sha256'] = artifacts.digest(summary)
    def git(repo, *args):
        return subprocess.check_output(['git', '-C', str(repo), *map(str, args)], text=True, timeout=120).strip()
    git(source, 'worktree', 'add', '-b', branch, checkout, C)
    paths = []
    for row in new:
        src, dst = raw / 'records' / row['path'], checkout / 'swdb-project/records' / row['path']
        assert not dst.exists()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        assert sha(dst) == row['file_sha256']
        paths.append(dst.relative_to(checkout).as_posix())
    evidence = checkout / 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-cpu-model-mbit10-20261006-a3.json'
    assert not evidence.exists()
    module.dump(evidence, summary)
    paths.append(evidence.relative_to(checkout).as_posix())
    assert all(p.startswith('swdb-project/') for p in paths) and len(paths) == 8
    git(checkout, 'add', '--', *paths)
    git(checkout, 'diff', '--cached', '--check')
    git(checkout, 'commit', '-m', 'Record metadata-only CPU model continuation evidence')
    git(checkout, 'push', '-u', 'origin', branch)
    assert not git(checkout, 'status', '--porcelain')
    module.clean()
    print(json.dumps({'commit': git(checkout, 'rev-parse', 'HEAD'), 'branch': branch, 'receipt_identity': summary['identity_sha256'], 'validation': proof['validation'], 'new_records': new, 'raw_transferred': False}))


if __name__ == '__main__':
    main()
