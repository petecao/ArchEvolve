"""2026-10-16 ET. Inert Linux envelope for the frozen private unit observer.

The root admits the exact policy/command and existing whole-process guard. This
entry executes no child, compiler, native program, solver or installed project.
The private observer's complete source/ABI admission checks remain unchanged.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import sys
import time
import types

RAW_NAME = 'probata-resume-20261016-t28-unit-observation-2baf722f-v5'
SOURCE_COMMIT = '2baf722fdaa6cba24b859eae3172a6f597417d72'
PROJECT = '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project'
PYTHON = '/data1/yanruj/venvs/swdb-test/bin/python'
OBSERVER_SHA = '7ecdbffea04c87a2c198a17cf7b5fbd872bc4c663cc4d8da42a3c5e7bc1a088e'
RUNTIME_HELPER_SHA = '9f63dbe826ca70f2ceacd37b56753a5f212811a5a377c7baed59da4de60b7721'
RUNTIME_POLICY_SHA = '8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517'
WHOLE_SECONDS, ENTRY_SECONDS, RSS_BYTES = 1200, 1180, 4294967296
OUTPUT_BYTES, FILE_BYTES, CONTROLS_BYTES = 268435456, 4194304, 1048576
STABLE = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
OBSERVER_OUTPUTS = ('whole-unit-preparation.json', 'observed-input-pins.json', 'unit-observation-result.json')
ENVELOPE_OUTPUTS = ('envelope-linux-role.json', 'envelope-python-entry-role.json',
    'envelope-runtime-before.json', 'envelope-runtime-after.json',
    'envelope-source-before.json', 'envelope-source-after.json', 'envelope-result.json', 'envelope-finalization-refusal.json')
OBSERVER_CONTROLS = ('abi_role_transport_v1.py', 'closed_python_surface.py', 'compiler_unit_adapter_v3.py', 'compiler_unit_adapter_v4.py', 'dx100_whole_checked_v2.py', 'fixed-modules-v3.json', 'lossless_gzip_v2.py', 'normalized_capture_ingress_v2.py', 'normalized_compiler_adapter_v1.py', 'normalized_unit_observation_v1.py', 'observation_source_bridge_v1.py', 'observe_entry_v3.py', 'receiver_state_draws_v2.py', 'role_normalized_gzip_v2.py', 'strict_minify_v2.py', 'whole_interface_v4.py')


def need(value, message):
    if not value: raise ValueError(message)


def document(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate envelope metadata key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite envelope metadata')))


def stable(value):
    return tuple(getattr(value, name) for name in STABLE)


def pin(path):
    path = Path(path); before = path.lstat()
    need(path.is_absolute() and path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode),
         'canonical regular envelope input required')
    with path.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    need(stable(path.lstat()) == stable(before), 'envelope input changed while hashing')
    return {'path': str(path), 'bytes': before.st_size, 'sha256': digest}


def read(row, *, limit=CONTROLS_BYTES):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
         and type(row['bytes']) is int and 0 <= row['bytes'] <= limit,
         'closed bounded physical envelope pin required')
    path = Path(row['path']); before = path.lstat()
    need(path.is_absolute() and path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode)
         and before.st_size == row['bytes'], 'bounded canonical physical extent required before reading')
    with path.open('rb') as handle: data = handle.read(limit + 1)
    need(stable(path.lstat()) == stable(before) and len(data) == row['bytes']
         and hashlib.sha256(data).hexdigest() == row['sha256'], 'envelope bytes changed during bounded consumption')
    return data


def recheck(rows):
    for row in rows: need(pin(row['path']) == row, 'physical envelope input changed')


def save(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    need(len(raw) <= FILE_BYTES, 'bounded envelope output required')
    with Path(path).open('xb') as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    return pin(path)


def frames(error):
    rows = []; trace = error.__traceback__
    while trace is not None:
        code = trace.tb_frame.f_code
        rows.append({'filename': code.co_filename, 'function': code.co_name, 'line': trace.tb_lineno})
        trace = trace.tb_next
    return {'type': type(error).__name__, 'frames': rows[-12:]}


def load(raw, path):
    module = types.ModuleType('private_envelope_' + Path(path).stem)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def runtime_helpers(raw):
    need(hashlib.sha256(raw).hexdigest() == RUNTIME_HELPER_SHA, 'exact reviewed Linux helper required')
    names = {'verified_linux_lane', 'physical_runtime'}
    nodes = [node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef) and node.name in names]
    need(len(nodes) == 2 and {node.name for node in nodes} == names, 'exact inherited helper set required')
    namespace = {'Path': Path, 'hashlib': hashlib, 'json': json, 'os': os, 'stat': stat, 'pin': pin, 'recheck': recheck}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<reviewed-no-child-envelope-runtime>', 'exec'), namespace)
    return namespace


def check_launch(raw, policy, argv, live_helper):
    launch_pin = pin(raw / 'launch.json'); launch = document(read(launch_pin))
    need(launch.get('command') == [PYTHON, '-I', '-B', '-X', 'pycache_prefix=' + str(raw / 'entry-source-cache'),
         str(raw / 'control/linux_observation_envelope_v5.py'), str(raw), str(raw / 'control/envelope-policy-v5.json'), argv[3]]
         and launch.get('source') == str(Path(PROJECT).parent) and launch.get('source_commit') == SOURCE_COMMIT,
         'exact root-owned source and command required')
    need(all(launch.get(name) == value for name, value in {'rss_cap_bytes': RSS_BYTES, 'workers': 1,
         'timeout_seconds': WHOLE_SECONDS, 'node': policy['node']}.items()), 'exact whole-process guard required')
    need(type(policy['guard_files']) is dict and set(policy['guard_files']) == {'execute.py', 'watch.py'},
         'exact independently reviewed normal guard pins required')
    for name, digest in policy['guard_files'].items():
        need(type(digest) is str and len(digest) == 64 and pin(raw / name)['sha256'] == digest
             and launch.get('reviewed_wrapper_reuse', {}).get(name) == digest, 'root execute/watch binding differs')
    live = live_helper(policy['node'])
    marker = hashlib.sha256(json.dumps({'launch': launch_pin, 'live': live}, sort_keys=True).encode()).hexdigest()
    return {'launch': launch_pin, 'live': live, 'derived_marker': marker, 'Mac_counted_claim': False}


def stage_layout(raw, policy):
    """Root stages flat controls; copy only these fixed reviewed owned inputs."""
    controls = policy['controls']
    wanted = {'path': str(raw / 'control/observation-policy-v1.json'),
        'bytes': policy['observer_policy']['bytes'], 'sha256': policy['observer_policy']['sha256']}
    need(controls.get('observation-policy-v1.json') == wanted, 'flat observer-policy staging pin differs')
    observer = document(read(wanted))
    need(type(observer['controls']) is dict and set(observer['controls']) == set(OBSERVER_CONTROLS)
         and observer['output_root'] == str(raw / 'observer') and observer['library_root'] == str(raw / 'library_fixture'),
         'exact fixed observer/control/library layout required')
    directories = (raw / 'observer', raw / 'observer/control', raw / 'library_fixture', raw / 'library_fixture/proof_units')
    need(not os.path.lexists(directories[0]) and not os.path.lexists(directories[2]), 'fresh derived roots required')
    copies = []
    for name in OBSERVER_CONTROLS:
        row = controls[name]
        need(row['path'] == str(raw / 'control' / name) and observer['controls'][name] ==
             {**row, 'path': str(raw / 'observer/control' / name)}, 'fixed observer copy role differs')
        copies.append((raw / 'observer/control' / name, read(row)))
    copies.append((raw / 'observer/control/observation-policy-v1.json', read(wanted)))
    source = controls['source_call_fixture_v2.cpp']
    need(source['path'] == str(raw / 'control/source_call_fixture_v2.cpp')
         and policy['library_source'] == {**source, 'path': str(raw / 'library_fixture/proof_units/source.cpp')},
         'fixed proof-buffer copy role differs')
    copies.append((raw / 'library_fixture/proof_units/source.cpp', read(source)))
    for path in directories: path.mkdir()
    for path, data in copies:
        with path.open('xb') as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())


def input_check(raw, policy, policy_pin):
    need(set(policy) == {'schema', 'raw_name', 'source_commit', 'source_project', 'python', 'node', 'budgets',
         'guard_files', 'disk_floor_bytes', 'runtime_policy', 'controls', 'observer_policy', 'library_source',
         'root_admission_receipt'}, 'closed envelope policy required')
    need(policy['schema'] == 'linux-normalized-unit-observation-envelope-1' and policy['raw_name'] == RAW_NAME
         and policy['source_commit'] == SOURCE_COMMIT and policy['source_project'] == PROJECT and policy['python'] == PYTHON
         and type(policy['node']) is int and policy['node'] in (0, 1), 'exact first-source Linux selection required')
    need(policy['budgets'] == {'whole_seconds': WHOLE_SECONDS, 'entry_seconds': ENTRY_SECONDS, 'rss_bytes': RSS_BYTES,
         'total_bytes': OUTPUT_BYTES, 'file_bytes': FILE_BYTES, 'control_bytes': CONTROLS_BYTES}, 'fixed budgets required')
    controls = policy['controls']; need(type(controls) is dict and controls, 'closed root controls required')
    need({p.name for p in (raw / 'control').iterdir()} == set(controls) | {Path(policy_pin['path']).name},
         'root flat control membership differs')
    values = {}; total = policy_pin['bytes']
    for name, row in controls.items():
        need(name == Path(name).name and row['path'] == str(raw / 'control' / name), 'root control basename differs')
        values[name] = read(row); total += len(values[name])
    need(total <= CONTROLS_BYTES, 'entire staged control packet exceeds one MiB')
    recheck([policy_pin, policy['runtime_policy'], policy['root_admission_receipt'], policy['observer_policy'], policy['library_source']])
    need(policy['runtime_policy']['sha256'] == RUNTIME_POLICY_SHA, 'exact existing complete runtime policy required')
    observer = document(read(policy['observer_policy']))
    need(observer['original_project'] == PROJECT and observer['output_root'] == str(raw / 'observer')
         and observer['library_root'] == str(raw / 'library_fixture') and observer['capture']['prepared'] is None
         and observer['root_admission_receipt'] == policy['root_admission_receipt'], 'observer role or unknown output differs')
    need(policy['library_source']['path'] == str(raw / 'library_fixture/proof_units/source.cpp')
         and policy['library_source']['bytes'] == 4524
         and policy['library_source']['sha256'] == '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd',
         'exact captured proof buffer required')
    for name, row in observer['controls'].items():
        need(name in controls and row == {**controls[name], 'path': str(raw / 'observer/control' / name)}
             and read(row) == values[name], 'observer fixed copies differ from root staged controls')
    need(sum(row['bytes'] for row in observer['controls'].values()) <= CONTROLS_BYTES,
         'bounded observer copied controls required')
    need({p.name for p in (raw / 'observer/control').iterdir()} == set(observer['controls']) | {Path(policy['observer_policy']['path']).name},
         'observer exact physical control membership differs')
    return values


def check_outputs(raw, *, complete=False):
    observer = raw / 'observer'
    allowed = set(OBSERVER_OUTPUTS) | {'control'}
    need({path.name for path in observer.iterdir()} <= allowed, 'unknown observer output member')
    rows = []
    for path in sorted(raw.rglob('*')):
        mode = path.lstat().st_mode
        need(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'symlink or special raw artifact refused')
        if stat.S_ISREG(mode):
            need(path.stat().st_size <= (CONTROLS_BYTES if path.is_relative_to(raw / 'control') else OUTPUT_BYTES),
                 'raw artifact extent exceeded')
            rows.append(pin(path))
    need(sum(row['bytes'] for row in rows) <= OUTPUT_BYTES - 8 * FILE_BYTES,
         'aggregate raw retention plus reserved final metadata exceeded')
    for name in OBSERVER_OUTPUTS:
        path = observer / name
        if path.exists(): need(pin(path)['bytes'] <= FILE_BYTES, 'observer metadata file exceeded four MiB')
    if complete:
        result = document((observer / 'unit-observation-result.json').read_bytes())
        need(result.get('observation_complete') is True and result.get('public_admission') is False
             and result.get('compiler_native_solver_executed') is False and not result.get('after_input_errors'),
             'complete non-admitting observation required')
    return rows


def bind_environment(raw, runtime_policy, environment):
    """Bind the known V9 inherited source role before private package imports.

    -I already ignored PYTHONPATH; only its exact root-source literal is an
    admitted compatibility selector. Unknown Python/loader overrides refuse.
    No launcher/loader startup equivalence is inferred from this later check.
    """
    allowed = {'PYTHONPATH', 'PYTHONPYCACHEPREFIX', 'PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE', 'PYTHONSAFEPATH'}
    need(not any(name.startswith('PYTHON') and name not in allowed for name in environment)
         and '__PYVENV_LAUNCHER__' not in environment, 'unbound Python environment selector refused')
    need(environment.get('PYTHONPATH') in (None, PROJECT), 'only known V9 source PYTHONPATH is admitted')
    for name in ('LD_PRELOAD', 'LD_AUDIT', 'LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES'):
        need(not environment.get(name), 'ambient loader/library override refused')
    need(environment.get('LD_LIBRARY_PATH') in (None, '', runtime_policy['native_runtime']['loader_environment']['LD_LIBRARY_PATH']),
         'unadmitted loader search path refused')
    before = {name: environment.get(name) for name in ('PATH', 'HOME', 'PYTHONPATH', 'LD_LIBRARY_PATH')}
    environment.pop('PYTHONPATH', None); environment.pop('LD_LIBRARY_PATH', None)
    environment.update(PATH=runtime_policy['path'], HOME=runtime_policy['home'], LANG='C', LC_ALL='C',
        PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX=str(raw / 'entry-source-cache'),
        PYTHONNOUSERSITE='1', PYTHONSAFEPATH='1', SETUPTOOLS_USE_DISTUTILS='local', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    return {'known_root_environment_before': before, 'selected_environment_after':
        {name: environment[name] for name in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'PYTHONDONTWRITEBYTECODE',
          'PYTHONPYCACHEPREFIX', 'PYTHONNOUSERSITE', 'PYTHONSAFEPATH', 'SETUPTOOLS_USE_DISTUTILS', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD')},
        'boundary': 'post-interpreter-start source-role normalization; actual isolated startup/path/origins independently checked; root owns loader startup'}


def source_inputs(runtime_policy):
    rows = runtime_policy['source_inputs']
    need(type(rows) is list and len(rows) == 3 and {row['relative'] for row in rows} == {
        'apps/dx100/benchmarks/API/MAA.hpp', 'apps/dx100/benchmarks/API/MAA_gem5.hpp',
        'tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json'}, 'exact three original source inputs required')
    result = []
    for row in rows:
        expected = {'path': str(Path(PROJECT) / row['relative']), 'bytes': row['bytes'], 'sha256': row['sha256']}
        need(pin(expected['path']) == expected, 'original source input changed')
        result.append(expected)
    return {'source_commit': SOURCE_COMMIT, 'files': result,
            'boundary': 'physical three-input equality only; root separately verifies immutable checkout and Git readback'}


def publish_final_result(raw, status, started):
    """Success requires zero exit and a settled check after publication/flush."""
    result = dict(status)
    result['completion_requires_zero_exit_and_settled_finalization'] = True
    try:
        need(time.monotonic() - started <= ENTRY_SECONDS, 'prepublication deadline exceeded')
        check_outputs(raw)
        save(raw / 'envelope-result.json', result)
        print(json.dumps(result, sort_keys=True, allow_nan=False)); sys.stdout.flush()
        check_outputs(raw)
        need(time.monotonic() - started <= ENTRY_SECONDS, 'settled post-publication deadline exceeded')
        return bool(result['observation_complete'])
    except Exception as error:
        refusal = {'schema': 'linux-normalized-unit-envelope-finalization-refusal-1',
            'observation_complete': False, 'public_admission': False,
            'error': frames(error), 'wall_seconds': time.monotonic() - started,
            'earlier_result_alone_cannot_establish_completion': True}
        try: save(raw / 'envelope-finalization-refusal.json', refusal)
        except Exception: pass  # Nonzero exit still refuses if quota/IO prevents metadata publication.
        return False


def main(argv=None):
    argv = list(sys.argv if argv is None else argv); started = time.monotonic()
    need(len(argv) == 4 and __debug__ and sys.flags.optimize == 0 and sys.flags.isolated == 1
         and sys.dont_write_bytecode and sys.executable == PYTHON, 'exact selected -I -B interpreter required')
    raw = Path(argv[1]); policy_path = Path(argv[2])
    need(raw.name == RAW_NAME and raw.resolve(strict=True) == raw and raw.is_dir()
         and Path(__file__) == raw / 'control/linux_observation_envelope_v5.py'
         and policy_path == raw / 'control/envelope-policy-v5.json', 'exact fresh raw and envelope paths required')
    policy_pin = {'path': str(policy_path), 'bytes': policy_path.lstat().st_size, 'sha256': argv[3]}
    policy = document(read(policy_pin))
    # No scientific consumer or child is invoked during the fixed copy stage.
    stage_layout(raw, policy)
    values = input_check(raw, policy, policy_pin)
    need(sys.pycache_prefix == str(raw / 'entry-source-cache') and not os.path.lexists(raw / 'entry-source-cache'),
         'explicit -X isolated cache prefix and absent cache required')
    need(all(os.environ.get(name) == value for name, value in {'PROBATA_OUTPUT': str(raw),
         'SWDB_VERIFIER_LOCK': str(raw / 'verifier.lock'), 'SWDB_VERIFIER_RSS_CAP_BYTES': str(RSS_BYTES)}.items()),
         'actual whole-tree output/lock/RSS environment differs')
    need(type(policy['disk_floor_bytes']) is int and policy['disk_floor_bytes'] >= 20 * 1024**3, 'governing twenty-GiB raw-mount floor required')
    need(shutil.disk_usage(raw).free >= policy['disk_floor_bytes'] + OUTPUT_BYTES, 'disk reserve plus quota required')
    runtime_policy = document(read(policy['runtime_policy']))
    environment_binding = bind_environment(raw, runtime_policy, os.environ)
    resource.setrlimit(resource.RLIMIT_AS, (RSS_BYTES, RSS_BYTES))
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_BYTES, FILE_BYTES))
    resource.setrlimit(resource.RLIMIT_CPU, (ENTRY_SECONDS, ENTRY_SECONDS))
    def deadline(_signal, _frame): raise TimeoutError('bounded passive observation deadline')
    signal.signal(signal.SIGALRM, deadline); signal.setitimer(signal.ITIMER_REAL, ENTRY_SECONDS)
    def audit(event, args):
        if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
            raise RuntimeError('envelope child/native/network operation refused')
        if event == 'open':
            path, mode, flags = args
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or flags & (1 | 2 | 64 | 512 | 1024):
                outputs = {str(raw / name) for name in ENVELOPE_OUTPUTS} | {str(raw / 'observer' / name) for name in OBSERVER_OUTPUTS}
                if type(path) is not str or path not in outputs or not flags & 64 or not flags & 128:
                    raise PermissionError('only exclusive fixed observation outputs allowed')
        if event in {'os.mkdir', 'os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.chmod', 'os.chown',
                     'os.link', 'os.symlink', 'os.truncate', 'os.utime', 'os.chdir', 'os.putenv', 'os.unsetenv'}:
            raise PermissionError('passive envelope filesystem/environment mutation refused')
    sys.addaudithook(audit)
    helpers = runtime_helpers(values['linux_native86_entry_v4.py'])
    closed = load(values['closed_python_surface.py'], raw / 'control/closed_python_surface.py')
    roles = load(values['python_startup_roles_v2.py'], raw / 'control/python_startup_roles_v2.py')
    observer = load(values['python_role_observer_v2.py'], raw / 'control/python_role_observer_v2.py')
    before = None; source_before = None; after_errors = []; status = {'schema': 'linux-normalized-unit-envelope-result-1',
        'observation_complete': False, 'public_admission': False, 'compiler_native_solver_executed': False}
    try:
        save(raw / 'envelope-linux-role.json', check_launch(raw, policy, argv, helpers['verified_linux_lane']))
        before = helpers['physical_runtime'](runtime_policy, closed)
        save(raw / 'envelope-runtime-before.json', before)
        source_before = source_inputs(runtime_policy)
        save(raw / 'envelope-source-before.json', source_before)
        roles.validate_role_plan_v2(runtime_policy['startup_roles'], metadata=runtime_policy['python_surface_binding'],
            source_project=Path(PROJECT), root_observer_bytes=values['t28-linux-runtime-observer-v2-actual-20261016.json'], closed=closed)
        request = roles.role_request_v2(runtime_policy['startup_roles'], role='entry-isolated', environment=os.environ,
            cache=raw / 'entry-source-cache')
        actual = observer.observe_role_v2(request); roles.check_role_observation_v2(request, actual)
        save(raw / 'envelope-python-entry-role.json', actual)
        input_check(raw, policy, policy_pin); check_outputs(raw)
        observer_path = raw / 'observer/control/observe_entry_v3.py'
        need(pin(observer_path)['sha256'] == OBSERVER_SHA, 'unchanged reviewed observer entry required')
        module = load(read(pin(observer_path)), observer_path)
        code = module.main([policy['observer_policy']['path'], policy['observer_policy']['sha256']])
        need(type(code) is int and code == 0, 'private observer refused')
        check_outputs(raw, complete=True)
        need(time.monotonic() - started <= ENTRY_SECONDS, 'entry wall budget exceeded')
        status['observation_complete'] = True
    except Exception as error: status['error'] = frames(error)
    finally:
        for check in (lambda: input_check(raw, policy, policy_pin), lambda: check_outputs(raw),
                      lambda: need(not os.path.lexists(raw / 'entry-source-cache'), 'bytecode cache appeared')):
            try: check()
            except Exception as error: after_errors.append(frames(error))
        try:
            after = helpers['physical_runtime'](runtime_policy, closed)
            need(before is not None and after == before, 'final physical runtime closure differs')
            save(raw / 'envelope-runtime-after.json', after)
        except Exception as error: after_errors.append(frames(error))
        try:
            source_after = source_inputs(runtime_policy)
            need(source_before is not None and source_after == source_before, 'final original source input closure differs')
            save(raw / 'envelope-source-after.json', source_after)
        except Exception as error: after_errors.append(frames(error))
        if after_errors or time.monotonic() - started > ENTRY_SECONDS: status['observation_complete'] = False
        status.update(after_input_errors=after_errors, wall_seconds=time.monotonic() - started,
            environment_binding=environment_binding,
            cleanup_boundary='root must separately settle finite lease/process/resource/source observations')
        accepted = publish_final_result(raw, status, started)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if accepted else 1


if __name__ == '__main__': raise SystemExit(main())
