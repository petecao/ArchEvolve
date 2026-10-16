"""2026-10-16 ET. Passive settled memory53 reader; no compiler/project imports.

Root must bind fresh guard/resource admission separately. Successful reading
establishes private preparation controls only, with first-after-preprocessing
header timing and sampled process-ownership boundaries retained explicitly.
"""
import hashlib
import json
from pathlib import Path
import sys


def deny_children(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('passive audit prohibits child execution')


sys.addaudithook(deny_children)
ROOT = Path('/private/tmp/probata-resume-20261016-t28-memory53-native-v2')
FOLDER = Path(__file__).resolve().parent
EXPECTED = {'preparation_controls': 53, 'memory_effects_checked': False, 'public_proof': False}


def pin(path):
    path = Path(path)
    assert path.is_absolute() and not path.is_symlink() and path.resolve() == path
    with path.open('rb') as stream:
        sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha}


def read(path):
    return json.loads(Path(path).read_text())


def audit():
    """Root invokes only after the actual producer and guard have settled."""
    out = ROOT / 'component'
    command = read(FOLDER / 'command_v2.json')
    assert command['entry']['sha256'] == 'fab5fab5fe7e3149c3c6c961c1bd97ac8e83a54cd7f4c89b133eda4ca2b11a29'
    assert pin(command['entry']['path']) == command['entry']
    for key in ('source_policy', 'runtime_policy'):
        assert pin(command[key]['path']) == command[key]
    result = read(out / 'result.json')
    assert result['accepted'] is True and result['error'] is None
    assert result['controls_by_language'] == {'c11': 53, 'cpp17': 53}
    assert result['input_pin_differences'] == result['used_dependency_differences'] == []
    assert result['bytecode_cache_present'] is False
    assert all(result[key] is False for key in (
        'actual_formal_acceptance', 'source_body_proof', 'hardware_acceptance',
        'actual_pair_acceptance', 'current_0_2', 'full_ticket28'))
    policy = read(command['source_policy']['path'])
    assert result['scope'] == policy['scope']
    assert result['header_dependency_timing_tcb'] == policy['header_dependency_timing_tcb']
    assert not any(p.exists() or p.is_symlink() for p in (ROOT / 'entry-cache', out / 'source-cache'))
    manifest = read(out / 'artifact-manifest.json')
    expected = {row['relative']: row for row in manifest}
    assert len(expected) == len(manifest)
    physical = {str(p.relative_to(out)): p for p in out.rglob('*') if p.is_file() and p.name != 'artifact-manifest.json'}
    assert physical.keys() == expected.keys()
    for relative, path in physical.items():
        assert {k: expected[relative][k] for k in ('path', 'bytes', 'sha256')} == pin(path)
    inputs = read(out / 'inputs-before.json')
    assert len(inputs) == 7628
    for row in inputs:
        assert pin(row['path']) == row
    entry = read(out / 'entry-and-policies.json')
    assert entry['entry'] == command['entry'] and entry['guard_run_token_present'] is True
    assert 'SWDB_VERIFIER_RUN_TOKEN' not in entry['environment']
    assert entry['environment']['SWDB_VERIFIER_RSS_CAP_BYTES'] == '4294967296'
    stages = read(out / 'commands.json')
    assert [r['name'] for r in stages] == [language + '-' + stage
        for language in ('c11', 'cpp17') for stage in ('preprocess', 'compile', 'run')]
    observations = read(out / 'observations.json')
    assert [r['language'] for r in observations] == ['c11', 'cpp17']
    for row in observations:
        assert row['controls'] == 53 and row['result'] == EXPECTED
        assert pin(row['binary']['path']) == row['binary']
        assert read(out / (row['language'] + '-run.stdout')) == EXPECTED
        assert (out / (row['language'] + '-run.stderr')).stat().st_size == 0
    groups = read(out / 'used-header-dependencies.json')
    assert [g['language'] for g in groups] == ['c11', 'cpp17']
    for group in groups:
        assert group['capture_order'] == 'first physical hashes after preprocessing'
        assert len({p['path'] for p in group['pins']}) == len(group['pins'])
        for row in [*group['pins'], group['frozen']]:
            assert pin(row['path']) == row
    guard = read(ROOT / 'guard.log.summary.json')
    assert guard['cmd'] == command['entry_argv'] and guard['exit_code'] == 0
    assert guard['cap_gb'] == 4 and guard['timeout_s'] == 180
    assert guard['peak_rss_mb'] <= 4096
    assert not any(guard[k] for k in ('killed_by_watchdog', 'timed_out', 'queue_timed_out',
                                    'inspection_failure', 'primary_inspection_failure',
                                    'cleanup_inspection_failure', 'cleanup_inspection_failures',
                                    'unconfirmed_children', 'error'))
    return {'status': 'PASS_PRIVATE_PREPARATION_CONTROLS', 'controls_by_language': {'c11': 53, 'cpp17': 53},
            'physical_input_pins': len(inputs), 'raw_artifacts': len(manifest),
            'dependency_counts': {g['language']: len(g['pins']) for g in groups},
            'guard_exit': guard['exit_code'], 'guard_wall_s': guard['wall_s'],
            'guard_peak_rss_mib': guard['peak_rss_mb'], 'inspection_events': len(guard['inspection_events']),
            'header_dependency_timing_tcb': result['header_dependency_timing_tcb'],
            'process_boundary': guard['cleanup_boundary'],
            'actual_formal_acceptance': False, 'source_body_proof': False,
            'hardware_acceptance': False, 'current_0_2': False, 'full_ticket28': False}


if __name__ == '__main__':
    assert not sys.flags.optimize, 'passive reader assertions must be active'
    print(json.dumps(audit(), sort_keys=True, indent=2))
