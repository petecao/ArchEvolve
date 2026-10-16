"""2026-10-16 ET. Inert pass-through controls; no compiler/project import."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure diagnostic control refuses ' + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent
TREE = ast.parse((HERE / 'initialized_ast_diagnostic_v1.py').read_text())
MAIN = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
NESTED = {node.name: node for node in MAIN.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


class DiagnosticControls(unittest.TestCase):
    def test_compiler_run_keeps_exact_arguments_keywords_result_and_failure(self):
        captured, saved, log = [], [], []
        answer = types.SimpleNamespace(returncode=1, stdout='same stdout', stderr='same stderr')
        def original(*args, **kwargs):
            captured.append((args, kwargs))
            return answer
        context = {'compiler': ['/inert/clang++'], 'command_log': log, 'Path': Path,
                   'original_run': original, 'save': lambda name, value: saved.append((name, value))}
        exec(compile(ast.Module(body=[NESTED['observed_run']], type_ignores=[]), '<inert-run-observer>', 'exec'), context)
        arguments = ['/inert/clang++', '-fsyntax-only', '/inert/input.ii']
        environment = {'ONLY': 'inert'}
        result = context['observed_run'](arguments, env=environment, timeout=4.5, capture_output=True, text=True, input='source')
        self.assertIs(result, answer)
        self.assertIs(captured[0][0][0], arguments)
        self.assertIs(captured[0][1]['env'], environment)
        self.assertEqual(captured[0][1], {'env': environment, 'timeout': 4.5, 'capture_output': True, 'text': True, 'input': 'source'})
        self.assertEqual([value for name, value in saved], ['source', 'same stdout', 'same stderr'])
        failure = RuntimeError('retained exact compiler failure')
        context['original_run'] = lambda *args, **kwargs: (_ for _ in ()).throw(failure)
        with self.assertRaises(RuntimeError) as error:
            context['observed_run'](arguments)
        self.assertIs(error.exception, failure)
        with self.assertRaises(RuntimeError): context['observed_run'](['/inert/frama-c', '-wp'])

    def test_observation_inputs_retained_then_exact_original_refusal_propagates(self):
        saved, called = [], []
        failure = ValueError('unchanged validator refusal')
        def original(*arguments):
            called.append(arguments)
            raise failure
        context = {'original_observation': original, 'json': json, 'hashlib': hashlib,
                   'original': types.SimpleNamespace(_probe=lambda: 'same probe'), 'observations': [],
                   'save': lambda name, value: saved.append((name, value))}
        exec(compile(ast.Module(body=[NESTED['retained_observation']], type_ignores=[]), '<inert-observation>', 'exec'), context)
        dumps = {name: 'inert ' + name for name in ('init_MAA', 'get_new_reg', 'set_reg', 'get_reg', 'trust_fixture')}
        sources = [{'path': '/inert/header.hpp', 'sha256': '0' * 64}]
        with self.assertRaises(ValueError) as error:
            context['retained_observation']('same tokens', dumps, 'same LLVM', sources)
        self.assertIs(error.exception, failure)
        self.assertIs(called[0][1], dumps)
        self.assertIs(called[0][3], sources)
        self.assertEqual(len(saved), 8)
        self.assertEqual(saved[0], ('preprocessed-original.ii', 'same tokens'))

    def test_completion_requires_original_assertion_all_artifacts_and_seven_healthy_phases(self):
        expected = 'initialized assertion contains an unchecked AST effect'
        context = {'Path': Path, 'EXPECTED_REFUSAL': expected}
        function = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'complete_capture')
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<inert-complete-capture>', 'exec'), context)
        families = ('init_MAA', 'get_new_reg', 'set_reg', 'get_reg', 'trust_fixture')
        names = ['preprocessed-original.ii', 'compiler-observed.ll', 'observation-source-pins.json',
                 'temporary-probe.ii', 'temporary-original.d', 'compiler-commands.json', 'assertion-0.json',
                 *('ast-' + name + '.json' for name in families)]
        retained = [{'name': name, 'sha256': hashlib.sha256(name.encode()).hexdigest()} for name in names]
        files = {row['name']: row for row in retained}
        commands = [{'index': index, 'returncode': 0, 'argv': ['/inert/clang++', '-fsyntax-only', '-ast-dump=json',
                    '-ast-dump-filter=' + family, '/inert/probe.ii'], 'stdout': files['ast-' + family + '.json']}
                    for index, family in enumerate(families)]
        commands += [{'index': 5, 'returncode': 0, 'argv': ['/inert/clang++', '-E', '-MD', '-MF', '/inert/original.d', '/inert/caller.cc'],
                      'stdout': files['preprocessed-original.ii']},
                     {'index': 6, 'returncode': 0, 'argv': ['/inert/clang++', '-O2', '-S', '-emit-llvm', '/inert/probe.ii'],
                      'stdout': files['compiler-observed.ll']}]
        assertions = [{'original_refusal': {'type': 'Refused', 'message': expected},
                       'unchecked': [{'kind': 'InertUnknownKind'}], 'subtree': files['assertion-0.json']}]
        observations = [{'frozen_stage_sha256': files['temporary-probe.ii']['sha256']}]
        check = context['complete_capture']
        self.assertTrue(check(assertions, observations, retained, commands)['accepted'])
        for missing in names:
            self.assertFalse(check(assertions, observations, [row for row in retained if row['name'] != missing], commands)['accepted'])
        self.assertFalse(check([], observations, retained, commands)['accepted'])
        self.assertFalse(check(assertions, [], retained, commands)['accepted'])
        for index in range(7):
            broken = [{**row, 'returncode': 1} if position == index else row for position, row in enumerate(commands)]
            self.assertFalse(check(assertions, observations, retained, broken)['accepted'])

    def test_original_temporary_path_cleanup_and_exception_arguments_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='t28-inert-retention-') as temporary:
            path = Path(temporary)
            (path / 'probe.ii').write_bytes(b'inert preprocessed data')
            events, saved = [], []
            class Original:
                def __enter__(self): return temporary
                def __exit__(self, *arguments): events.append(arguments)
            context = {'original_temporary': lambda *args, **kwargs: Original(), 'Path': Path,
                       'save': lambda name, value: saved.append((name, value))}
            exec(compile(ast.Module(body=[NESTED['RetainedTemporary']], type_ignores=[]), '<inert-temp-retention>', 'exec'), context)
            retained = context['RetainedTemporary'](prefix='swdb-dx100-initialized-register-')
            self.assertEqual(retained.__enter__(), temporary)
            exception = ValueError('same observation failure')
            self.assertIsNone(retained.__exit__(ValueError, exception, None))
            self.assertEqual(events, [(ValueError, exception, None)])
            self.assertEqual(saved, [('temporary-probe.ii', b'inert preprocessed data')])

    def test_exact_v4_controller_inverse_and_complete_pinned_staging(self):
        base = (HERE / 'linux_pair_entry_v4.py').read_text()
        new = (HERE / 'linux_initialized_ast_diagnostic_entry_v1.py').read_text()
        prefix = '"""DIAGNOSTIC ONLY: original source validation retained; no public test/proof/solver.\n"""\n'
        old_leaf = "command=['/bin/bash',str(project/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-initialized-u32-resume-20261016/run_initialized_register_acceptance.sh'),EXPECTED['source_commit'],'pair']"
        new_leaf = "profile.mkdir();(profile/'tmp').mkdir();(profile/'cache').mkdir()\ncommand=[sys.executable,'-B',str(output/'control/initialized_ast_diagnostic_v1.py'),str(project),str(profile),str(policy_path),sys.argv[4]]"
        self.assertEqual(new.removeprefix(prefix).replace(new_leaf, old_leaf), base)
        packet = json.loads((HERE / 'linux_initialized_ast_diagnostic_command_v1.json').read_text())
        self.assertTrue(packet['diagnostic_only'])
        self.assertFalse(packet['proof_acceptance'])
        self.assertEqual(packet['node'], 0)
        self.assertEqual(len(packet['controller_inputs']), 7)
        self.assertLess(sum(row['bytes'] for row in packet['controller_inputs']), 1048576)
        for row in packet['controller_inputs']:
            data = Path(row['path']).read_bytes()
            self.assertEqual(len(data), row['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
        source = (HERE / 'initialized_ast_diagnostic_v1.py').read_text()
        self.assertNotIn('library.validate(', source)
        self.assertNotIn('pytest.main(', source)
        self.assertIn('return original_assertion(node, expected, variable)', source)
        self.assertIn("raise RuntimeError('diagnostic permits selected Clang children only')", source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
