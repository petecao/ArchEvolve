"""2026-10-16 ET. INERT compiler-observation retention, never a proof run.

The original source validator still executes and retains its refusal. Temporary
paths, compiler arguments, inputs, output and exception behavior are observed;
no predicate, allowed-kind set, proof contract or compiler option is changed.
"""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types


MAX_RETAINED_BYTES = 67108864
EXPECTED_REFUSAL = 'initialized assertion contains an unchecked AST effect'
KNOWN_ASSERT_KINDS = {'ParenExpr', 'ImplicitCastExpr', 'CXXStaticCastExpr', 'CStyleCastExpr',
    'CXXFunctionalCastExpr', 'UnaryOperator', 'BinaryOperator', 'ConditionalOperator', 'CallExpr',
    'DeclRefExpr', 'IntegerLiteral', 'PredefinedExpr', 'StringLiteral'}


def complete_capture(assertions, observations, retained, commands):
    """A copied exception message alone is never completed diagnostic evidence."""
    required = {'preprocessed-original.ii', 'compiler-observed.ll', 'observation-source-pins.json',
                'temporary-probe.ii', 'temporary-original.d', 'compiler-commands.json',
                *('ast-' + name + '.json' for name in ('init_MAA', 'get_new_reg', 'set_reg', 'get_reg', 'trust_fixture'))}
    files = {row['name']: row for row in retained}
    if (len(observations) != 1 or not required <= files.keys() or len(files) != len(retained) or
            not commands or any(row.get('returncode') != 0 or 'exception' in row for row in commands)):
        return {'accepted': False, 'reason': 'complete observation/artifact/zero-exit command census absent'}
    refusals = [row for row in assertions if row.get('original_refusal') ==
                {'type': 'Refused', 'message': EXPECTED_REFUSAL} and row.get('unchecked')]
    if not refusals or any(row['subtree']['name'] not in files for row in refusals):
        return {'accepted': False, 'reason': 'original assertion refusal/subtree is absent'}
    phases = {}
    for family in ('init_MAA', 'get_new_reg', 'set_reg', 'get_reg', 'trust_fixture'):
        matches = [row for row in commands if '-ast-dump-filter=' + family in row['argv']
                   and '-fsyntax-only' in row['argv'] and '-ast-dump=json' in row['argv']
                   and Path(row['argv'][-1]).name == 'probe.ii']
        if len(matches) != 1 or matches[0].get('stdout', {}).get('sha256') != files['ast-' + family + '.json']['sha256']:
            return {'accepted': False, 'reason': 'exact retained AST phase/output differs: ' + family}
        phases[family] = matches[0]['index']
    preprocess = [row for row in commands if '-E' in row['argv'] and '-MD' in row['argv'] and '-MF' in row['argv']
                  and Path(row['argv'][row['argv'].index('-MF') + 1]).name == 'original.d']
    llvm = [row for row in commands if all(flag in row['argv'] for flag in ('-O2', '-S', '-emit-llvm'))
            and Path(row['argv'][-1]).name == 'probe.ii']
    if (len(preprocess) != 1 or len(llvm) != 1 or
            preprocess[0].get('stdout', {}).get('sha256') != files['preprocessed-original.ii']['sha256'] or
            llvm[0].get('stdout', {}).get('sha256') != files['compiler-observed.ll']['sha256'] or
            files['temporary-probe.ii']['sha256'] != observations[0]['frozen_stage_sha256']):
        return {'accepted': False, 'reason': 'exact retained preprocess/LLVM/temporary stage differs'}
    phases.update(preprocess=preprocess[0]['index'], llvm=llvm[0]['index'])
    if len(set(phases.values())) != 7:
        return {'accepted': False, 'reason': 'seven distinct original compiler phases required'}
    return {'accepted': True, 'original_assertion_refusals': len(refusals), 'compiler_phases': phases,
            'scope': 'retained source-form diagnostic only; no proof or repair'}


def main(argv):
    if len(argv) != 5 or not __debug__ or sys.flags.optimize or not sys.dont_write_bytecode:
        raise ValueError('diagnostic requires nonoptimized -B PROJECT PROFILE POLICY SHA')
    project, profile, policy_path = map(Path, argv[1:4])
    policy_bytes = policy_path.read_bytes()
    if hashlib.sha256(policy_bytes).hexdigest() != argv[4]:
        raise ValueError('diagnostic root policy bytes differ')
    policy = json.loads(policy_bytes)
    control = policy_path.parent
    if control != profile.parent / 'control' or profile.name != 'initialized-profile':
        raise ValueError('exact diagnostic raw/control/profile namespace required')
    modules = {}
    for name in ('closed_python_surface.py', 'python_startup_roles_v2.py', 'python_role_observer_v2.py'):
        path = control / name
        data = path.read_bytes()
        if path.is_symlink() or hashlib.sha256(data).hexdigest() != policy['controller_files'][name]['sha256']:
            raise ValueError('diagnostic shared startup helper differs')
        module = types.ModuleType('diagnostic_' + name[:-3])
        exec(compile(data, str(path), 'exec'), module.__dict__)
        modules[name] = module
    roles, observer = modules['python_startup_roles_v2.py'], modules['python_role_observer_v2.py']
    request = roles.role_request_v2(policy['startup_roles'], role='pytest-child', environment=os.environ,
                                    cache=profile / 'source-cache')
    startup = observer.observe_role_v2(request)
    roles.check_role_observation_v2(request, startup)
    (profile / 'diagnostic-child-startup.json').write_text(json.dumps(startup, indent=2, sort_keys=True) + '\n')
    destination = profile / 'retained-observation'
    destination.mkdir()
    retained, command_log, assertions, observations = [], [], [], []
    total = 0

    def save(name, value):
        nonlocal total
        path = destination / name
        data = value if isinstance(value, bytes) else value.encode('utf-8')
        total += len(data)
        if total > MAX_RETAINED_BYTES or path.exists() or path.is_symlink() or path.parent != destination:
            raise ValueError('diagnostic retention budget/name/freshness refused')
        with path.open('xb') as stream:
            stream.write(data)
        pin = {'name': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        retained.append(pin)
        return pin

    fixture = Path(policy['diagnostic_fixture']['library'])
    fixture_pins = policy['diagnostic_fixture']['files']

    def fixture_check():
        wanted_yaml = {name for name in fixture_pins if name.endswith('.yaml')}
        found_yaml = {str(path.relative_to(fixture)) for folder in
                      ('intrinsics', 'lowerings', 'library_operations', 'rewrite_contracts', 'proof_semantics')
                      for path in (fixture / folder).rglob('*.yaml')}
        if found_yaml != wanted_yaml:
            raise ValueError('exact retained fixture YAML selection differs')
        for name, wanted in fixture_pins.items():
            path = fixture / name
            if path.is_symlink() or not path.is_file():
                raise ValueError('retained diagnostic fixture file is not regular')
            data = path.read_bytes()
            if len(data) != wanted['bytes'] or hashlib.sha256(data).hexdigest() != wanted['sha256']:
                raise ValueError('retained diagnostic fixture changed: ' + name)

    fixture_check()
    # The process already has the exact source-only PYTHONPATH and startup gate.
    from swdb import c_lowering, proof_semantics
    from swdb.library import Library
    from swdb import dx100_initialized_register_source as original
    library = Library(fixture)
    if library.problems or set(proof_semantics.current(library)) != {original.SEMANTICS_ID}:
        raise ValueError('diagnostic must select only the original initialized fixture')
    options = proof_semantics.lowering_options(library)
    original_observation, original_assertion = original.observation, original._assertion
    original_run, original_temporary = subprocess.run, tempfile.TemporaryDirectory
    allowed_assign = next(node for node in ast.walk(ast.parse(Path(original.__file__).read_text()))
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'allowed' for target in node.targets)
        and isinstance(node.value, ast.Set) and 'ConditionalOperator' in ast.literal_eval(node.value))
    if ast.literal_eval(allowed_assign.value) != KNOWN_ASSERT_KINDS:
        raise ValueError('exact diagnostic validator kind table differs')
    compiler = policy['linux_clang_components']['command']
    if len(compiler) != 1 or not Path(compiler[0]).is_absolute():
        raise ValueError('diagnostic selected absolute compiler required')

    def child_policy(event, arguments):
        if event == 'subprocess.Popen':
            executable, arguments_list = arguments[:2]
            if (not isinstance(arguments_list, (list, tuple)) or not arguments_list or
                    arguments_list[0] != compiler[0] or executable != compiler[0]):
                raise RuntimeError('diagnostic permits selected Clang children only')
        elif event.startswith(('os.exec', 'os.spawn', 'os.posix_spawn')) or event in {'os.system', 'os.fork', 'os.forkpty'}:
            raise RuntimeError('diagnostic forbids alternate child creation')

    sys.addaudithook(child_policy)

    def observed_run(*args, **kwargs):
        command = args[0] if args else kwargs.get('args')
        if not isinstance(command, (list, tuple)) or not command or command[0] != compiler[0]:
            raise RuntimeError('diagnostic permits selected Clang run only')
        index = len(command_log)
        row = {'index': index, 'argv': list(command), 'cwd': str(kwargs.get('cwd') or Path.cwd()),
               'timeout': kwargs.get('timeout'), 'check': kwargs.get('check', False)}
        supplied = kwargs.get('input')
        if supplied is not None:
            row['stdin'] = save('command-' + str(index) + '-stdin.bin', supplied)
        command_log.append(row)
        try:
            done = original_run(*args, **kwargs)
        except BaseException as error:
            row['exception'] = {'type': type(error).__name__, 'message': str(error)}
            raise
        row['returncode'] = done.returncode
        for name in ('stdout', 'stderr'):
            data = getattr(done, name)
            if data is not None:
                row[name] = save('command-' + str(index) + '-' + name + '.bin', data)
        return done

    class RetainedTemporary:
        def __init__(self, *args, **kwargs):
            self.original = original_temporary(*args, **kwargs)
            self.selected = kwargs.get('prefix') == 'swdb-dx100-initialized-register-'
        def __enter__(self):
            self.path = Path(self.original.__enter__())
            return str(self.path)
        def __exit__(self, kind, value, traceback):
            try:
                if self.selected:
                    for path in sorted(self.path.rglob('*')):
                        if path.is_symlink() or not path.is_file():
                            raise ValueError('diagnostic original compiler stage has an unexpected input')
                        save('temporary-' + path.name, path.read_bytes())
            finally:
                # Always preserve the original cleanup and exception propagation.
                result = self.original.__exit__(kind, value, traceback)
            return result

    def retained_observation(tokens, dumps, llvm, sources):
        save('preprocessed-original.ii', tokens)
        save('compiler-observed.ll', llvm)
        save('observation-source-pins.json', json.dumps(sources, indent=2, sort_keys=True) + '\n')
        if set(dumps) != {'init_MAA', 'get_new_reg', 'set_reg', 'get_reg', 'trust_fixture'}:
            raise ValueError('diagnostic exact five-family census differs')
        for name, text in dumps.items():
            save('ast-' + name + '.json', text)
        observations.append({'frozen_stage_sha256': hashlib.sha256((tokens + original._probe()).encode()).hexdigest()})
        return original_observation(tokens, dumps, llvm, sources)

    def retained_assertion(node, expected, variable):
        index = len(assertions)
        tree = list(original._walk(node))
        unexpected = [item for item in tree if item.get('kind') not in KNOWN_ASSERT_KINDS]
        row = {'index': index, 'expected': expected, 'variable': variable,
               'kind_counts': dict(sorted(Counter(item.get('kind') for item in tree).items())),
               'unchecked': [{'kind': item.get('kind'), 'opcode': item.get('opcode'),
                              'castKind': item.get('castKind'), 'name': item.get('name'),
                              'type': item.get('type'), 'child_kinds': [child.get('kind') for child in original._children(item)]}
                             for item in unexpected],
               'subtree': save('assertion-' + str(index) + '.json', json.dumps(node, indent=2, sort_keys=True) + '\n')}
        assertions.append(row)
        try:
            return original_assertion(node, expected, variable)
        except original.Refused as error:
            row['original_refusal'] = {'type': type(error).__name__, 'message': str(error)}
            raise

    exception = None
    subprocess.run, tempfile.TemporaryDirectory = observed_run, RetainedTemporary
    original.observation, original._assertion = retained_observation, retained_assertion
    try:
        c_lowering.lower(fixture / 'proof_units/trust.cc', 'trust_fixture', **options)
    except Exception as error:
        exception = {'type': type(error).__name__, 'message': str(error)}
    finally:
        subprocess.run, tempfile.TemporaryDirectory = original_run, original_temporary
        original.observation, original._assertion = original_observation, original_assertion
        fixture_check()
        save('compiler-commands.json', json.dumps(command_log, indent=2, sort_keys=True) + '\n')
    completion = complete_capture(assertions, observations, retained, command_log)
    reproduced = completion['accepted'] and exception is not None and EXPECTED_REFUSAL in exception['message']
    result = {'date': '2026-10-16 ET', 'status': 'DIAGNOSTIC_REPRODUCED_SOURCE_REFUSAL' if reproduced else 'DIAGNOSTIC_UNEXPECTED_OUTCOME',
              'diagnostic_only': True, 'public_acceptance': False, 'proof_or_wp_or_solver_requested': False,
              'selected_compiler': compiler, 'original_exception': exception, 'assertions': assertions,
              'retained_files': retained, 'retained_bytes': total, 'retention_cap_bytes': MAX_RETAINED_BYTES,
              'capture_completion': completion,
              'temporary_original_cleanup_preserved': True,
              'instrumentation': 'Pass-through exact subprocess.run arguments/results, original TemporaryDirectory paths/cleanup, observation inputs and assertion node; original validators always called unchanged',
              'scope': 'Clang-only diagnostic leaf; unchanged controller bootstrap also uses Git, OCaml package queries, pytest collection and compiler runtime/provenance workers. No WP/solver, proof, repair, source-body or hardware theorem.'}
    (profile / 'diagnostic-result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return 0 if reproduced else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
