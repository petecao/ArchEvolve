"""2026-10-16 ET. Passive settled memory53 reader; no compiler/project imports.

Root must bind fresh guard/resource admission separately. Successful reading
establishes private preparation controls only, with first-after-preprocessing
header timing and sampled process-ownership boundaries retained explicitly.
"""
import hashlib
import json
import math
from pathlib import Path
import sys


def deny_children(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('passive audit prohibits child execution')


sys.addaudithook(deny_children)
ROOT = Path('/private/tmp/probata-resume-20261016-t28-memory53-native-v4')
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


def make_dependencies(text, target, cwd):
    """Closed Make dependency syntax: no expansion/comments or shell parsing."""
    if not text.startswith(target + ':'):
        raise ValueError('dependency target differs')
    text = text[len(target) + 1:]
    result, token, index = [], '', 0
    while index < len(text):
        char = text[index]
        if char == '\\':
            index += 1
            if index >= len(text):
                raise ValueError('truncated dependency escape')
            char = text[index]
            if char == '\n':
                index += 1
                continue
            if char not in ' \t#\\:':
                raise ValueError('unsupported dependency escape')
            token += char
        elif char in '$#':
            raise ValueError('dependency expansion/comments refused')
        elif char.isspace():
            if token:
                result.append(token)
                token = ''
        else:
            token += char
        index += 1
    if token:
        result.append(token)
    if not result:
        raise ValueError('empty dependency set')
    paths = [str((Path(cwd) / value).resolve()) for value in result]
    return sorted(set(paths))


def audit():
    """Root invokes only after the actual producer and guard have settled."""
    out = ROOT / 'component'
    assert pin(FOLDER / 'command_v4.json')['sha256'] == '8d74019083bef17dc0c36a5b675a7e8064144fb8901e6c64beeba8946a6fdc25'
    command = read(FOLDER / 'command_v4.json')
    assert command['entry']['sha256'] == '9368f6ca7afa55b82670dd3c1a55cc5c5dcfa897adb938af59f921d4408ca315'
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
    runtime = read(command['runtime_policy']['path'])
    expected_inputs = (policy['source_pins'] + runtime['pins'] + policy['extra_sanitizer_runtime_pins']
        + policy['guard_source_pins'] + [command['entry'], command['source_policy'], command['runtime_policy']])
    assert inputs == expected_inputs, 'complete source/runtime/guard/control input membership differs'
    for row in inputs:
        assert pin(row['path']) == row
    entry = read(out / 'entry-and-policies.json')
    assert entry['entry'] == command['entry'] and entry['guard_run_token_present'] is True
    assert entry['source_policy'] == command['source_policy'] and entry['runtime_policy'] == command['runtime_policy']
    assert entry['environment'] == {
        'PATH': runtime['path'], 'HOME': '/Users/yanrujhou', 'LANG': 'C', 'LC_ALL': 'C',
        'TMPDIR': str(out / 'tmp'), 'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONPYCACHEPREFIX': str(out / 'source-cache'),
        'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1:abort_on_error=0:symbolize=0:exitcode=86',
        'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=0',
        'SWDB_VERIFIER_RSS_CAP_BYTES': '4294967296'}
    stages = read(out / 'commands.json')
    assert [r['name'] for r in stages] == [language + '-' + stage
        for language in ('c11', 'cpp17') for stage in ('preprocess', 'compile', 'run')]
    flags = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-fno-sanitize-recover=all']
    clang = '/opt/homebrew/opt/llvm/bin/clang++'
    source_folder = Path(command['entry']['path']).parent
    expected_stages = []
    for label, language, frozen_language, standard, suffix in [
            ('c11', 'c', 'cpp-output', '-std=c11', '.i'),
            ('cpp17', 'c++', 'c++-cpp-output', '-std=c++17', '.ii')]:
        frozen, depfile, binary = out / (label + suffix), out / (label + '.d'), out / (label + '.native')
        language_flags = [standard, *flags]
        expected_stages.extend([
            ([clang, '-x', language, *language_flags, '-E', '-MD', '-MF', str(depfile), '-MT', label,
              str(source_folder / 'native_prepare_cases.c'), '-o', str(frozen)], 60),
            ([clang, '-x', frozen_language, *language_flags, str(frozen), '-o', str(binary)], 90),
            ([str(binary)], 30)])
    for stage, (argv, maximum) in zip(stages, expected_stages):
        assert stage['argv'] == argv and stage['cwd'] == str(out)
        assert type(stage['timeout_s']) in (int, float) and math.isfinite(stage['timeout_s']) and 0 < stage['timeout_s'] <= maximum
    observations = read(out / 'observations.json')
    assert [r['language'] for r in observations] == ['c11', 'cpp17']
    for row in observations:
        assert row['controls'] == 53 and row['result'] == EXPECTED
        assert row['binary']['path'] == str(out / (row['language'] + '.native'))
        assert pin(row['binary']['path']) == row['binary']
        assert read(out / (row['language'] + '-run.stdout')) == EXPECTED
        assert (out / (row['language'] + '-run.stderr')).stat().st_size == 0
    groups = read(out / 'used-header-dependencies.json')
    assert [g['language'] for g in groups] == ['c11', 'cpp17']
    for group in groups:
        assert group['capture_order'] == 'first physical hashes after preprocessing'
        assert len({p['path'] for p in group['pins']}) == len(group['pins'])
        dependency_paths = make_dependencies((out / (group['language'] + '.d')).read_text(), group['language'], out)
        assert group['pins'] == [pin(Path(path)) for path in dependency_paths]
        required = {str((source_folder / name).resolve()) for name in
                    ('native_prepare_cases.c', 'backend_for_prepare.h', 'interface_memory_prepare.h')}
        assert required <= set(dependency_paths)
        suffix = '.i' if group['language'] == 'c11' else '.ii'
        assert group['frozen']['path'] == str(out / (group['language'] + suffix))
        for row in [*group['pins'], group['frozen']]:
            assert pin(row['path']) == row
    guard = read(ROOT / 'guard.log.summary.json')
    assert guard['cmd'] == command['entry_argv'] and guard['exit_code'] == 0
    assert guard['cap_gb'] == 4 and guard['timeout_s'] == 180
    assert guard['log'] == str(ROOT / 'guard.log')
    assert guard['log_sha256'] == pin(ROOT / 'guard.log')['sha256']
    assert type(guard['peak_rss_mb']) in (int, float) and math.isfinite(guard['peak_rss_mb']) and 0 <= guard['peak_rss_mb'] <= 4096
    assert type(guard['wall_s']) in (int, float) and math.isfinite(guard['wall_s']) and 0 <= guard['wall_s'] <= 180
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
