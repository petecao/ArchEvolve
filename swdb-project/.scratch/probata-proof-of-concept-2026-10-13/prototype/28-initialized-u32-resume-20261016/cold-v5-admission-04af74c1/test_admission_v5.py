"""2026-10-16 ET. Exact observed schema and certificate interface controls only."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
INIT = HERE.parent
V4 = INIT / 'cold-v4-admission-04af74c1'
PROJECT = INIT.parents[3]
OLD = (V4 / 'initialized_cold_audit_v4.py').read_text()
NEW = (HERE / 'initialized_cold_audit_v5.py').read_text()
assert hashlib.sha256(OLD.encode()).hexdigest() == '03cc1de3fe010f0686a8e99729ab831a6cbcdd5f1fa7135a56bf0e6d42271b0d'
OBSERVED = json.loads((V4 / 'retained-runtime-schema-20261016.json').read_bytes())
EXPECTED = json.loads((INIT / 'linux_pair_policy_04af74c1_v5.json').read_bytes())
SELECTED = OBSERVED['files']['initialized-project-runtime-provenance.json']['selected_scalars']
COMPILER = {key: SELECTED.get('runtime.' + key, '<unconsumed metadata>')
            for key in OBSERVED['files']['initialized-project-runtime-provenance.json']['schema']['runtime']}
LOWERER = {key: SELECTED['lowering_identity.' + key] for key in ('c_lowering', 'clang', 'naming_rules')}
WRAPPER = {'path': COMPILER['command_executable']['path'], 'bytes': 145, 'sha256': COMPILER['command_executable']['sha256']}


def deny_child(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.fork', 'os.forkpty'}:
        raise RuntimeError('pure certificate seam refuses ' + event)


sys.addaudithook(deny_child)


def helper():
    node = next(node for node in ast.parse(NEW).body if isinstance(node, ast.FunctionDef) and node.name == 'certificate_runtime_descriptor_v5')
    namespace = {'Path': Path}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-V5-certificate-projection>', 'exec'), namespace)
    return namespace[node.name]


class PhysicalStandIn:
    def __init__(self): self.pins = []
    def pinned(self, row):
        assert row == WRAPPER
        self.pins.append(copy.deepcopy(row))


class CertificateTests(unittest.TestCase):
    def test_exact_old_assignment_red_and_new_actual_shape_green(self):
        before = ast.parse(OLD)
        audit = next(node for node in before.body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
        assignment = next(node for node in audit.body if isinstance(node, ast.Assign) and
                          ast.get_source_segment(OLD, node) == "runtime = {name: compiler[name] for name in ('command', 'version', 'driver')}")
        with self.assertRaises(KeyError):
            exec(compile(ast.Module(body=[assignment], type_ignores=[]), '<exact-old-certificate-assignment>', 'exec'), {'compiler': COMPILER})
        physical = PhysicalStandIn(); actual = helper()(copy.deepcopy(COMPILER), LOWERER, physical)
        self.assertEqual(actual, {'command': COMPILER['command'], 'version': '22.1.8', 'driver': WRAPPER})
        self.assertEqual(physical.pins, [WRAPPER])
        self.assertNotIn('version', COMPILER)
        self.assertNotEqual(COMPILER['driver']['path'], actual['driver']['path'])

    def test_descriptor_equals_exact_unchanged_producer_runtime_assignment(self):
        producer = PROJECT / 'swdb/dx100_initialized_register_source.py'
        data = producer.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), '01c043e544e50c30fc3d92b6be5a8b097f4dfef0606f53c29068a2ba008ac145')
        nodes = [node for node in ast.walk(ast.parse(data)) if isinstance(node, ast.Assign) and
            isinstance(node.value, ast.Dict) and {key.value for key in node.value.keys if isinstance(key, ast.Constant)} == {'command', 'version', 'driver'}]
        self.assertEqual(len(nodes), 1)
        self.assertEqual(ast.dump(nodes[0].value), ast.dump(ast.parse("{'command': command, 'version': unit.tool.version, 'driver': _pin(command[0])}", mode='eval').body))
        pinned = []
        def pin(path):
            self.assertEqual(path, WRAPPER['path']); pinned.append(path); return copy.deepcopy(WRAPPER)
        namespace = {'command': COMPILER['command'], 'unit': types.SimpleNamespace(tool=types.SimpleNamespace(version='22.1.8')), '_pin': pin}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-producer-assignment-with-physical-standin>', 'exec'), namespace)
        self.assertEqual(namespace['runtime'], helper()(COMPILER, LOWERER, PhysicalStandIn()))
        self.assertEqual(pinned, [WRAPPER['path']])

    def test_exact_certificate_runtime_equality_seam_rejects_underlying_driver(self):
        text = (INIT / 'passive_initialized_certificate_rechecker_v2.py').read_text()
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), 'd469b5168f4403c36d03fcacee6bce5eb4113ac55670c403b5c4a2a5682dad6e')
        tree = ast.parse(text)
        selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in {'_same', 'Refused'}]
        selected += [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in {'KIND', '_CERT_KEYS'} for target in node.targets)]
        namespace = {'json': json}
        exec(compile(ast.Module(body=selected, type_ignores=[]), '<exact-certificate-shape-and-equality>', 'exec'), namespace)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'verify_certificate')
        self.assertIsInstance(function.body[1], ast.Try)
        seam = function.body[1].body[:3]
        certificate = {key: None for key in namespace['_CERT_KEYS']}
        certificate.update(kind=namespace['KIND'], runtime_identity=helper()(COMPILER, LOWERER, PhysicalStandIn()))
        values = {**namespace, 'certificate': certificate, 'expected_runtime': copy.deepcopy(certificate['runtime_identity'])}
        code = compile(ast.Module(body=seam, type_ignores=[]), '<exact-certificate-runtime-equality-prefix>', 'exec')
        exec(code, values)
        for driver in (COMPILER['driver'], {**WRAPPER, 'bytes': 144}):
            bad = {**values, 'expected_runtime': {**values['expected_runtime'], 'driver': driver}}
            with self.subTest(driver=driver), self.assertRaises(namespace['Refused']): exec(code, bad)

    def test_alias_role_swap_wrong_version_and_wrapper_substitution_refused(self):
        for command in (['clang++'], [COMPILER['driver']['path']]):
            value = copy.deepcopy(COMPILER); value['command'] = command
            with self.subTest(command=command), self.assertRaises(AssertionError): helper()(value, LOWERER, PhysicalStandIn())
        value = copy.deepcopy(COMPILER); value['command_executable'] = copy.deepcopy(value['driver']); value['command'] = [value['driver']['path']]
        with self.assertRaises(AssertionError): helper()(value, LOWERER, PhysicalStandIn())
        for key, val in (('id', 'clang-22.1.9'), ('sha256', '0' * 64)):
            lowerer = copy.deepcopy(LOWERER); lowerer['clang'][key] = val
            with self.subTest(key=key), self.assertRaises(AssertionError): helper()(COMPILER, lowerer, PhysicalStandIn())
        value = copy.deepcopy(COMPILER); value['version'] = '22.1.8'
        with self.assertRaises(AssertionError): helper()(value, LOWERER, PhysicalStandIn())

    def test_complete_ast_inverse_and_downstream_projected_schema_scan(self):
        old, new = ast.parse(OLD), ast.parse(NEW)
        new.body[0] = old.body[0]
        new.body = [node for node in new.body if not isinstance(node, ast.FunctionDef) or node.name != 'certificate_runtime_descriptor_v5']
        before = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
        after = next(node for node in new.body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
        index = next(index for index, node in enumerate(before.body) if isinstance(node, ast.Assign) and
                     ast.get_source_segment(OLD, node) == "runtime = {name: compiler[name] for name in ('command', 'version', 'driver')}")
        after.body[index] = before.body[index]
        self.assertEqual(ast.dump(old, include_attributes=False), ast.dump(new, include_attributes=False))
        for node in ast.walk(ast.parse(NEW)):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in {'runtime', 'compiler'}:
                self.assertFalse(isinstance(node.slice, ast.Constant) and node.slice.value == 'version')
            if isinstance(node, ast.DictComp):
                self.assertNotEqual(ast.dump(node), ast.dump(before.body[index].value))
        for name in ('project_contexts', 'validate_compiler_descriptor_v4', 'original_launch', 'workflow', 'initialized_rules', 'semantic_model', 'audit'):
            a = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == name)
            b = next(node for node in new.body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(ast.get_source_segment(OLD, a), ast.get_source_segment(NEW, b))

    def test_policy_inverse_changes_only_fresh_namespace_reader_pin_and_base_provenance(self):
        old = json.loads((V4 / 'initialized-cold-policy-04af74c1-v4.json').read_bytes())
        new = json.loads((HERE / 'initialized-cold-policy-04af74c1-v5.json').read_bytes())
        def undo(value):
            if isinstance(value, dict): return {key: undo(item) for key, item in value.items()}
            if isinstance(value, list): return [undo(item) for item in value]
            if isinstance(value, str): return value.replace('initialized-cold-04af74c1-v5', 'initialized-cold-04af74c1-v4')
            return value
        new = undo(new); new['reader_sha256'] = old['reader_sha256']; new['provenance'].pop('reader_base_v4_unexecuted')
        self.assertEqual(new, old)
        command = json.loads((HERE / 'initialized-cold-command-04af74c1-v5.json').read_bytes())
        self.assertEqual(len(command['control_files']), 10)
        self.assertLess(command['control_total_bytes'], 1048576)
        self.assertEqual(command['command'][-3].split('/')[-1], 'initialized_cold_audit_v5.py')
        self.assertEqual(command['command'][-1], hashlib.sha256((HERE / 'initialized-cold-policy-04af74c1-v5.json').read_bytes()).hexdigest())


if __name__ == '__main__': unittest.main(verbosity=2)
