"""INERT 2026-10-16 ET. Root-only Mac C11/C++17 memory53 preparation controls.

No project imports. Root must independently admit the exact source/runtime/guard
and one 180-second/4-GiB tree before execution. This is not public call support.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


PYTHON = '/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12'
CLANG = '/opt/homebrew/opt/llvm/bin/clang++'
CLANG_SHA = '305697d3868243dca6e4aabf4f628df7de135d701eb4fd78f6a5d7528fef4395'
RUNTIME_SHA = '4171556ed48f8612eb364a88741831a3bfc9259d34c25750e8717dadeab408a1'
SOURCE_SHA = 'a9630edaf8586c22ba4f9896e618eae5548df20c8659d95fc447eb346644080a'
RAW_ROOT = Path('/private/tmp/probata-resume-20261016-t28-memory53-native-v2')
STAGE_BYTES, TOTAL_BYTES = 128 * 1024**2, 256 * 1024**2
FLAGS = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-fno-sanitize-recover=all']
EXPECTED_RESULT = {'preparation_controls': 53, 'memory_effects_checked': False, 'public_proof': False}


def pin(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}


def save(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def check_pins(rows):
    differences = []
    for row in rows:
        try:
            if pin(row['path']) != row:
                differences.append({'path': row['path'], 'reason': 'physical bytes/path changed'})
        except OSError as error:
            differences.append({'path': row['path'], 'reason': str(error)})
    return differences


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


def main():
    started = time.monotonic()
    deadline = started + 165
    parser = argparse.ArgumentParser()
    for key in ['output', 'source-policy', 'runtime-policy']:
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    folder = Path(__file__).resolve().parent
    if sys.executable != PYTHON or sys.flags.optimize or not sys.flags.dont_write_bytecode:
        raise ValueError('exact selected nonoptimized Python with -B required')
    if out != RAW_ROOT / 'component' or out.exists() or args.output.is_symlink():
        raise ValueError('exact fresh root raw component required')
    if pin(args.source_policy)['sha256'] != SOURCE_SHA or pin(args.runtime_policy)['sha256'] != RUNTIME_SHA:
        raise ValueError('reviewed source/runtime policy bytes differ')
    if not os.environ.get('SWDB_VERIFIER_RUN_TOKEN'):
        raise ValueError('actual c6 inherited ownership token required; root admits guard bounds')
    if any(os.environ.get(key) for key in ['CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'OBJC_INCLUDE_PATH', 'INCLUDE', 'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'DEVELOPER_DIR']):
        raise ValueError('ambient compiler/SDK overrides require separate review')
    if shutil.disk_usage(out.parent).free < 50 * 1024**3 + TOTAL_BYTES:
        raise ValueError('50GiB free floor plus256MiB allowance required')
    entry_cache = RAW_ROOT / 'entry-cache'
    if entry_cache.exists() or entry_cache.is_symlink() or sys.pycache_prefix != str(entry_cache):
        raise ValueError('root entry must use fresh exact private bytecode prefix')
    policy = json.loads(args.source_policy.read_text())
    runtime = json.loads(args.runtime_policy.read_text())
    if set(runtime) != {'pins', 'clang_command', 'ocamlfind_command', 'path', 'opam_switch_prefix'} or len(runtime['pins']) != 7605:
        raise ValueError('exact augmented public-V3 runtime policy required')
    if (runtime['clang_command'] != CLANG or pin(CLANG)['sha256'] != CLANG_SHA
            or pin(CLANG) not in runtime['pins'] or pin(PYTHON) not in runtime['pins']):
        raise ValueError('exact LLVM22 compiler identity required')
    sources = policy['source_pins']
    extras = policy['extra_sanitizer_runtime_pins']
    if len(sources) != 14 or len(extras) != 3:
        raise ValueError('closed source/sanitizer input counts differ')
    controls = [pin(__file__), pin(args.source_policy), pin(args.runtime_policy)]
    guards = policy['guard_source_pins']
    if len(guards) != 3:
        raise ValueError('exact B/c6/staged-search source pins required')
    all_pins = sources + runtime['pins'] + extras + guards + controls
    differences = check_pins(all_pins)
    if differences:
        raise ValueError('physical input pins differ: ' + json.dumps(differences))
    required = {str((folder / name).resolve()) for name in ['native_prepare_cases.c', 'backend_for_prepare.h', 'interface_memory_prepare.h']}
    if not required.issubset({row['path'] for row in sources}):
        raise ValueError('original C and both generated headers must be pinned')
    out.mkdir()
    (out / 'tmp').mkdir()
    pycache = out / 'source-cache'
    if pycache.exists() or pycache.is_symlink():
        raise ValueError('fresh child bytecode prefix required')
    environment = {'PATH': runtime['path'], 'HOME': '/Users/yanrujhou', 'LANG': 'C', 'LC_ALL': 'C',
                   'TMPDIR': str(out / 'tmp'), 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPYCACHEPREFIX': str(pycache),
                   'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1:abort_on_error=0:symbolize=0:exitcode=86',
                   'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=0'}
    for key in ['SWDB_VERIFIER_RUN_TOKEN', 'SWDB_WATCHDOG_TAG', 'SWDB_VERIFIER_LOCK', 'SWDB_VERIFIER_RSS_CAP_BYTES']:
        if key in os.environ:
            environment[key] = os.environ[key]
    save(out / 'inputs-before.json', all_pins)
    retained_environment = {key: value for key, value in environment.items() if key != 'SWDB_VERIFIER_RUN_TOKEN'}
    save(out / 'entry-and-policies.json', {'entry': pin(__file__), 'source_policy': pin(args.source_policy), 'runtime_policy': pin(args.runtime_policy),
                                        'environment': retained_environment, 'guard_run_token_present': bool(environment.get('SWDB_VERIFIER_RUN_TOKEN'))})
    commands, observations, dependency_groups = [], [], []
    error = None
    def raw_bytes():
        return sum(path.stat().st_size for path in out.rglob('*') if path.is_file())
    def run_stage(name, argv, maximum):
        remaining = min(maximum, deadline - time.monotonic() - 12)
        if remaining <= 0 or raw_bytes() > STAGE_BYTES:
            raise ValueError('remaining time or128MiB stage output allowance exhausted')
        commands.append({'name': name, 'argv': argv, 'cwd': str(out), 'timeout_s': remaining})
        save(out / 'commands.json', commands)
        with (out / (name + '.stdout')).open('wb') as stdout, (out / (name + '.stderr')).open('wb') as stderr:
            completed = subprocess.run(argv, cwd=out, env=environment, stdout=stdout, stderr=stderr, timeout=remaining, check=False)
        if completed.returncode != 0:
            raise ValueError(name + ' failed with exit' + str(completed.returncode))
        if raw_bytes() > STAGE_BYTES:
            raise ValueError('128MiB stage output postcheck failed')
    try:
        for label, language, frozen_language, standard, suffix in [('c11', 'c', 'cpp-output', '-std=c11', '.i'), ('cpp17', 'c++', 'c++-cpp-output', '-std=c++17', '.ii')]:
            frozen, depfile, binary = out / (label + suffix), out / (label + '.d'), out / (label + '.native')
            flags = [standard, *FLAGS]
            run_stage(label + '-preprocess', [CLANG, '-x', language, *flags, '-E', '-MD', '-MF', str(depfile), '-MT', label,
                                            str(folder / 'native_prepare_cases.c'), '-o', str(frozen)], 60)
            # First physical dependency capture happens AFTER original preprocessing.
            dependencies = [pin(path) for path in make_dependencies(depfile.read_text(), label, out)]
            if not required.issubset({row['path'] for row in dependencies}):
                raise ValueError('used dependency set omits original C/generated headers')
            frozen_pin = pin(frozen)
            dependency_groups.append({'language': label, 'capture_order': 'first physical hashes after preprocessing', 'pins': dependencies, 'frozen': frozen_pin})
            save(out / 'used-header-dependencies.json', dependency_groups)
            if check_pins(dependencies) or check_pins([frozen_pin]) or check_pins(sources):
                raise ValueError('source/dependency changed after capture/before frozen compilation')
            run_stage(label + '-compile', [CLANG, '-x', frozen_language, *flags, str(frozen), '-o', str(binary)], 90)
            if check_pins(dependencies) or check_pins([frozen_pin]):
                raise ValueError('captured dependency/frozen input changed during compile')
            binary_pin = pin(binary)
            run_stage(label + '-run', [str(binary)], 30)
            stdout = out / (label + '-run.stdout')
            stderr = out / (label + '-run.stderr')
            if stdout.stat().st_size > 65536 or stderr.stat().st_size != 0 or json.loads(stdout.read_text()) != EXPECTED_RESULT:
                raise ValueError('native result differs from exact53-control/no-memory-effects result')
            if check_pins([binary_pin, frozen_pin]) or check_pins(dependencies):
                raise ValueError('binary/frozen/dependency changed during native observation')
            observations.append({'language': label, 'controls': 53, 'binary': binary_pin, 'result': EXPECTED_RESULT, 'scope': 'private preparation controls only'})
            save(out / 'observations.json', observations)
    except Exception as failure:
        error = type(failure).__name__ + ': ' + str(failure)
    finally:
        after_differences = check_pins(all_pins)
        dependency_differences = [difference for group in dependency_groups for difference in check_pins(group['pins'] + [group['frozen']])]
        cache_present = any(path.exists() or path.is_symlink() for path in [entry_cache, pycache])
        total = raw_bytes()
        accepted = error is None and len(observations) == 2 and not after_differences and not dependency_differences and not cache_present and total <= TOTAL_BYTES
        save(out / 'result.json', {'accepted': accepted, 'error': error, 'wall_s': time.monotonic() - started,
                                 'controls_by_language': {row['language']: row['controls'] for row in observations},
                                 'input_pin_differences': after_differences, 'used_dependency_differences': dependency_differences,
                                 'bytecode_cache_present': cache_present, 'raw_bytes_before_receipt': total,
                                 'header_dependency_timing_tcb': policy['header_dependency_timing_tcb'],
                                 'scope': policy['scope'], 'actual_formal_acceptance': False, 'source_body_proof': False,
                                 'hardware_acceptance': False, 'actual_pair_acceptance': False, 'current_0_2': False, 'full_ticket28': False})
        save(out / 'artifact-manifest.json', [{'relative': str(path.relative_to(out)), **pin(path)} for path in sorted(out.rglob('*')) if path.is_file() and path.name != 'artifact-manifest.json'])
    return 0 if accepted and raw_bytes() <= TOTAL_BYTES else 1


if __name__ == '__main__':
    raise SystemExit(main())
