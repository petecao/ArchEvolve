"""2026-10-16 ET. Exact CLI/adapter/compose argument seams; no project imports."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
V1 = WHOLE / 'public-profile-builder-v1'
V3 = WHOLE / 'production-route-v3/proposed/swdb'


def no_child(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'socket.connect', 'socket.bind'}:
        raise AssertionError('child/network forbidden in pure controls')
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise AssertionError('project imports forbidden in pure controls')


sys.addaudithook(no_child)
OLD = runpy.run_path(str(V1 / 'pair_plan_v1.py'))
NEW = runpy.run_path(str(HERE / 'pair_plan_v2.py'))


def tree(path):
    return ast.parse(path.read_text())


def function(module, name):
    rows = [node for node in ast.walk(module) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(rows) != 1:
        raise AssertionError('one exact source function required: ' + name)
    return copy.deepcopy(rows[0])


def expression(node, namespace):
    return eval(compile(ast.Expression(body=node), '<exact-source-expression>', 'eval'), namespace)


def parser():
    """The real complete prove parser, minus only unrelated ArchEvolve registration.

    All add_argument calls, defaults and --define append behavior are unchanged.
    Two exact nodes are omitted so no project module is imported or executed.
    """
    proof = tree(HERE / 'base-source/proof.py')
    registration = function(proof, 'register_cli')
    removed = []
    kept = []
    for node in registration.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'swdb' and [item.name for item in node.names] == ['archevolve_proof']:
            removed.append(ast.unparse(node)); continue
        if isinstance(node, ast.Expr) and ast.unparse(node.value) == 'archevolve_proof.register_options(sub)':
            removed.append(ast.unparse(node)); continue
        kept.append(node)
    if removed != ['from swdb import archevolve_proof', 'archevolve_proof.register_options(sub)']:
        raise AssertionError('unrelated registration removal differs')
    registration.body = kept
    namespace = {'Path': Path, 'paths': SimpleNamespace(RECORDS=Path('/original/records')),
        'ADAPTERS': {'cbmc': None, 'wp': None}, 'prove': lambda _args: None}
    exec(compile(ast.Module(body=[function(proof, '_bounds_argument'), registration], type_ignores=[]),
        '<real-proof-cli-without-archevolve-registration>', 'exec'), namespace)
    root = argparse.ArgumentParser()
    namespace['register_cli'](root.add_subparsers(dest='command'))
    return root


def source_gate(args):
    """Real from_args keyword -> constructor assignment -> compose gate."""
    adapter = tree(V3 / 'cbmc_adapter.py')
    adapter_class = next(node for node in adapter.body if isinstance(node, ast.ClassDef) and node.name == 'CbmcAdapter')
    from_args = function(adapter_class, 'from_args')
    returns = [node for node in from_args.body if isinstance(node, ast.Return)
               and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'cls']
    if len(returns) != 1:
        raise AssertionError('exact real adapter return required')
    keywords = [row.value for row in returns[0].value.keywords if row.arg == 'defines']
    if len(keywords) != 1:
        raise AssertionError('exact define forwarding required')
    defines = expression(keywords[0], {'args': args})
    constructor = function(adapter_class, '__init__')
    assignments = [node for node in constructor.body if isinstance(node, ast.Assign)
                   and any(ast.unparse(target) == 'self.defines' for target in node.targets)]
    if len(assignments) != 1:
        raise AssertionError('one real constructor define assignment required')
    receiver = SimpleNamespace()
    exec(compile(ast.Module(body=assignments, type_ignores=[]), '<real-cbmc-constructor-define-assignment>', 'exec'),
         {'self': receiver, 'defines': defines})
    source = tree(V3 / 'dx100_checked_source.py')
    compose = function(source, 'compose')
    gates = [node for node in compose.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
             and any(isinstance(arg, ast.Constant) and arg.value == 'unsupported function/build configuration'
                     for arg in node.value.args)]
    if len(gates) != 1:
        raise AssertionError('one exact source build gate required')
    function_value = next(node.value.value for node in source.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'FUNCTION' for target in node.targets))
    # This literal is taken from the real source-policy checker, rather than a test-only gate.
    policy_literals = [node for node in ast.walk(function(source, 'source_policy')) if isinstance(node, ast.List)
        and [item.value for item in node.elts if isinstance(item, ast.Constant)] == ['NUM_CORES=4', 'TILE_SIZE=16384']]
    if len(policy_literals) != 1:
        raise AssertionError('one source-derived exact define policy required')
    need_node = function(source, 'need'); refused = next(node for node in source.body
        if isinstance(node, ast.ClassDef) and node.name == 'Refused')
    namespace = {'FUNCTION': function_value, 'function': function_value, 'defines': receiver.defines,
                 'policy': {'defines': ast.literal_eval(policy_literals[0])}}
    exec(compile(ast.Module(body=[refused, need_node, gates[0]], type_ignores=[]), '<real-source-compose-build-gate>', 'exec'), namespace)
    return receiver.defines


def selected_method(args):
    """Real summary forwarding and real named/current selector over inert metadata."""
    proof = tree(HERE / 'base-source/proof.py')
    summary = function(proof, '_prove_summary')
    forwarded = next(node.value for node in summary.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'method' for target in node.targets))
    selector = tree(HERE / 'base-source/method_version.py')
    checked = SimpleNamespace(id='method.dx100-whole-checked-source-v1', data={'status': 'frozen', 'sequence': 1})
    unrelated = SimpleNamespace(id='method.unrelated-higher-sequence', data={'status': 'frozen', 'sequence': 999999})
    namespace = {'Path': Path, 'FOLDER': 'methods',
        'load': lambda _root: ({checked.id: checked, unrelated.id: unrelated}, [])}
    exec(compile(ast.Module(body=[function(selector, name) for name in ('current', 'named', 'select')], type_ignores=[]),
        '<real-method-version-select-over-inert-metadata>', 'exec'), namespace)
    current = function(proof, '_current_method')
    imports = [node for node in current.body if isinstance(node, ast.ImportFrom)]
    if [ast.unparse(node) for node in imports] != ['from swdb import method_version', 'from swdb.library import default_root']:
        raise AssertionError('exact method imports differ')
    current.body = [node for node in current.body if not isinstance(node, ast.ImportFrom)]
    namespace.update(method_version=SimpleNamespace(select=namespace['select']),
        default_root=lambda records: Path(records).parent / 'library', Failure=ValueError)
    exec(compile(ast.Module(body=[current], type_ignores=[]), '<real-proof-method-forwarding>', 'exec'), namespace)
    return expression(forwarded, {**namespace, 'args': args})


def sample():
    profile = {'contracts': [{'id': 'contract.result' + str(value), 'sha256': str(value)[0] * 64, 'expected_result': value}
                             for value in (79, 80)], 'semantics_content_sha256': 's' * 64,
               'method_content_sha256': 'm' * 64, 'producer_manifest_sha256': 'p' * 64}
    selection = {name: '/admitted/' + name for name in ('python', 'original_project', 'producer_project', 'records',
        'runs', 'verifier_lock', 'pycache', 'compiler_wrapper', 'cbmc')}
    selection.update(library_root='/admitted/library', root_admission_receipt={'path': '/root/receipt', 'bytes': 1, 'sha256': 'a' * 64})
    return profile, selection


class PlannerControls(unittest.TestCase):
    def test_exact_single_span_inverse(self):
        old = "'--summary', row['id'], '--adapter', 'cbmc', '--bounds', '{\"threads\":1}',"
        new = "'--summary', row['id'], '--method-version', 'method.dx100-whole-checked-source-v1',\n            '--define', 'NUM_CORES=4', '--define', 'TILE_SIZE=16384',\n            '--adapter', 'cbmc', '--bounds', '{\"threads\":1}',"
        source = (HERE / 'pair_plan_v2.py').read_text()
        self.assertEqual(source.count(new), 1)
        self.assertEqual(source.replace(new, old), (V1 / 'pair_plan_v1.py').read_text())

    def test_real_cli_old_red(self):
        profile, selection = sample(); arguments = parser()
        for job in OLD['plan'](profile, selection)['jobs']:
            args = arguments.parse_args(job['argv'][5:])
            self.assertEqual(args.define, []); self.assertIsNone(args.method_version)
            self.assertEqual(args.bounds, {'threads': 1})
            with self.assertRaisesRegex(ValueError, 'unsupported function/build configuration'):
                source_gate(args)
            self.assertEqual(selected_method(args).id, 'method.unrelated-higher-sequence')

    def test_real_cli_both_jobs_green(self):
        profile, selection = sample(); arguments = parser()
        for job in NEW['plan'](profile, selection)['jobs']:
            args = arguments.parse_args(job['argv'][5:])
            self.assertEqual(source_gate(args), ('NUM_CORES=4', 'TILE_SIZE=16384'))
            self.assertEqual(args.method_version, 'method.dx100-whole-checked-source-v1')
            self.assertEqual(selected_method(args).id, args.method_version)
            self.assertEqual(args.bounds, {'threads': 1}); self.assertEqual(args.summary, job['contract']['id'])

    def test_real_compose_gate_keeps_exact_defines(self):
        profile, selection = sample()
        args = parser().parse_args(NEW['plan'](profile, selection)['jobs'][0]['argv'][5:])
        for changed in ([], ['NUM_CORES=4'], ['TILE_SIZE=16384'], ['NUM_CORES=8', 'TILE_SIZE=16384'],
                        ['NUM_CORES=4', 'TILE_SIZE=16384', 'EXTRA=1'], ['NUM_CORES=4', 'NUM_CORES=4', 'TILE_SIZE=16384']):
            with self.subTest(defines=changed):
                candidate = copy.deepcopy(args); candidate.define = changed
                with self.assertRaisesRegex(ValueError, 'unsupported function/build configuration'):
                    source_gate(candidate)
        args.define.reverse()
        self.assertEqual(source_gate(args), ('NUM_CORES=4', 'TILE_SIZE=16384'))

    def test_plan_inverse_keeps_all_other_inputs_identical(self):
        profile, selection = sample()
        old = OLD['plan'](profile, selection); new = NEW['plan'](profile, selection)
        for job in new['jobs']:
            tokens = job['argv']; index = tokens.index('--method-version')
            self.assertEqual(tokens[index:index + 6], ['--method-version', 'method.dx100-whole-checked-source-v1',
                '--define', 'NUM_CORES=4', '--define', 'TILE_SIZE=16384'])
            del tokens[index:index + 6]
        self.assertEqual(new, old)
        self.assertEqual(profile, sample()[0]); self.assertEqual(selection, sample()[1])

    def test_unknown_explicit_method_still_refuses(self):
        profile, selection = sample()
        args = parser().parse_args(NEW['plan'](profile, selection)['jobs'][0]['argv'][5:])
        args.method_version = 'method.not-present'
        with self.assertRaisesRegex(ValueError, 'no method-version file'):
            selected_method(args)

    def test_every_frozen_v1_member_unchanged(self):
        packet = V1 / 'source-packet-v1.json'
        self.assertEqual(hashlib.sha256(packet.read_bytes()).hexdigest(), 'b15802108dc91302210f432a48348b78f26e387503cb2e9faa27497144814da1')
        for row in json.loads(packet.read_bytes())['files']:
            raw = (V1 / row['relative']).read_bytes()
            self.assertEqual(len(raw), row['bytes']); self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
