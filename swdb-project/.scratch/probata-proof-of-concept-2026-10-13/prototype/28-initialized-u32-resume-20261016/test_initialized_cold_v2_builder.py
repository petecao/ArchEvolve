"""2026-10-16 ET. Pure cold V2 provenance/inverse/refusal controls.

No actual cold audit, certificate, raw proof evidence, project import, tool,
compiler, native child or SSH is executed. Inherited controls use tiny synthetic
fixtures and the exact V2 modules; their original V1 files remain unchanged.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
PUBLISHED = '04af74c121a733589fbe1a2087ad602deaef598b'
EVENTS = []


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event == 'os.system':
        EVENTS.append(event)
        raise RuntimeError('cold successor pure controls refuse ' + event)


sys.addaudithook(deny)


def load(path, source=None):
    context = {'__name__': 'inert_' + path.stem, '__file__': str(path)}
    exec(compile(source if source is not None else path.read_text(), str(path), 'exec'), context)
    return context


builder = load(HERE / 'prepare_initialized_cold_v2.py')


class ColdV2Builder(unittest.TestCase):
    def test_deterministic_bound_outputs_and_fixed_v1_inputs(self):
        first, metadata = builder['build'](PUBLISHED, 4)
        second, repeated = builder['build'](PUBLISHED, 4)
        self.assertEqual(first, second); self.assertEqual(metadata, repeated)
        self.assertEqual(metadata, json.loads((HERE / 'initialized-cold-v2-provenance.json').read_text()))
        for name, source in first.items(): self.assertEqual((HERE / name).read_bytes(), source.encode())
        for name, expected in builder['BASES'].items(): self.assertEqual(builder['pin'](HERE / name)['sha256'], expected)
        self.assertEqual(metadata['source_commit'], PUBLISHED)
        self.assertEqual(metadata['runtime_controller_version'], 4)
        self.assertFalse(metadata['actual_audit_or_certificate_checked'])
        physical = builder['PRODUCER']; raw = physical.read_bytes()
        class ChangedProducer:
            def read_bytes(self): return raw.replace(b'\n', b'\r\n')
            def read_text(self): raise AssertionError('physical byte hashing must precede text decoding')
        try:
            builder['PRODUCER'] = ChangedProducer()
            with self.assertRaisesRegex(ValueError, 'physical bytes changed'): builder['build'](PUBLISHED, 4)
        finally:
            builder['PRODUCER'] = physical

    def test_pending_and_invalid_origin_binding_refuse_before_inputs(self):
        for commit, version in ((PUBLISHED, None), (None, 4), (builder['OLD_COMMIT'], 4),
                                 ('not-a-commit', 4), (PUBLISHED, True), (PUBLISHED, 5)):
            with self.subTest(commit=commit, version=version), self.assertRaises(ValueError): builder['build'](commit, version)
        files, metadata = builder['build']()
        self.assertIsNone(metadata['source_commit'])
        namespace = load(HERE / 'passive_initialized_certificate_rechecker_v2.py', files['passive_initialized_certificate_rechecker_v2.py'])
        with self.assertRaisesRegex(namespace['Refused'], 'pending root binding'):
            namespace['verify_origin_freeze']('/must-not-be-read')
        reader = load(HERE / 'initialized_cold_audit_v2.py', files['initialized_cold_audit_v2.py'])
        with self.assertRaisesRegex(AssertionError, 'source commit pending'):
            reader['audit']('/must-not-be-read', '0' * 64)

    def test_complete_copied_node_bytes_and_unaffected_adapters(self):
        old = (HERE / 'passive_initialized_certificate_rechecker_v1.py').read_text()
        new = (HERE / 'passive_initialized_certificate_rechecker_v2.py').read_text()
        production = builder['PRODUCER'].read_text()
        old_nodes, new_nodes, source_nodes = (builder['named_nodes'](text) for text in (old, new, production))
        changes, added, removed = builder['changed_definitions'](old, new)
        self.assertEqual(added, builder['OBSERVER_ADDED']); self.assertEqual(removed, set())
        self.assertEqual(changes, builder['OBSERVER_CHANGED'] | {'ORIGIN_SOURCE_COMMIT', 'ORIGIN_PINS', 'COPIED_SOURCE_NODES', 'verify_origin_freeze'})
        copied = builder['literal'](new, 'COPIED_SOURCE_NODES')
        self.assertEqual(len(copied), 40)
        for row in copied:
            name = row['name']; actual = builder['segment'](new, new_nodes[name]); origin = builder['segment'](production, source_nodes[name])
            self.assertEqual(actual, origin)
            self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(), row['sha256'])
            self.assertEqual((row['line_start'], row['line_end']), (source_nodes[name].lineno, source_nodes[name].end_lineno))
        for name in ('verify_certificate', 'verify_record_scope', 'verify_partial_wp_scope', 'verify_initialized_record', '_recipe', 'recheck', '_flow', '_clean'):
            self.assertEqual(builder['segment'](old, old_nodes[name]), builder['segment'](new, new_nodes[name]))

    def test_reader_inverse_keeps_all_v1_checks(self):
        old = ast.parse((HERE / 'initialized_cold_audit_v1.py').read_text())
        new = ast.parse((HERE / 'initialized_cold_audit_v2.py').read_text())
        old_nodes = builder['named_nodes']((HERE / 'initialized_cold_audit_v1.py').read_text())
        class Inverse(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str):
                    value = node.value
                    for name in ('passive_initialized_certificate_rechecker', 'initialized_cold_obligations', 'initialized_cold_identities', 'initialized_cold_audit'):
                        value = value.replace(name + '_v2.py', name + '_v1.py')
                    return ast.copy_location(ast.Constant(value=value), node)
                return node
            def visit_Name(self, node):
                if node.id == 'RUNTIME_CONTROLLER_VERSION': return ast.copy_location(ast.Constant(value=4), node)
                return node
            def visit_Assign(self, node):
                names = [target.id for target in node.targets if isinstance(target, ast.Name)]
                if names == ['RUNTIME_CONTROLLER_VERSION']: return None
                if names in (['SOURCE_COMMIT'], ['MODULE_PINS']): return copy.deepcopy(old_nodes[names[0]])
                return self.generic_visit(node)
            def visit_Assert(self, node):
                if isinstance(node.msg, ast.Constant) and node.msg.value in ('V2 published source commit pending', 'V2 reviewed runtime controller version4 pending'): return None
                return self.generic_visit(node)
        self.assertEqual(ast.dump(Inverse().visit(new)), ast.dump(old))

    def test_obligations_byte_identical_and_module_pins_closed(self):
        self.assertEqual((HERE / 'initialized_cold_obligations_v1.py').read_bytes(), (HERE / 'initialized_cold_obligations_v2.py').read_bytes())
        text = (HERE / 'initialized_cold_audit_v2.py').read_text()
        module_pins = builder['literal'](text, 'MODULE_PINS')
        trace = HERE.parent / '28-public-memory-trace-resume-20261016'
        for name, expected in module_pins.items():
            path = HERE / name if (HERE / name).exists() else trace / name
            self.assertEqual(builder['pin'](path)['sha256'], expected)
        self.assertEqual(set(module_pins), {'passive_initialized_certificate_rechecker_v2.py',
            'initialized_cold_obligations_v2.py', 'initialized_cold_identities_v2.py',
            'closed_python_surface.py', 'python_startup_roles_v2.py'})

    def test_exact_default_bounds_old_red_new_green_and_mutations(self):
        old = load(HERE / 'initialized_cold_identities_v1.py')
        new = load(HERE / 'initialized_cold_identities_v2.py')
        project = builder['PROJECT']
        with self.assertRaises(AssertionError): old['fixture_job_bounds'](project)
        self.assertEqual(new['fixture_job_bounds'](project), {'threads': 1, 'input_size': 1})
        raw = (project / 'tests/testkit/dx100_trust.py').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); target = root / 'tests/testkit/dx100_trust.py'; target.parent.mkdir(parents=True)
            target.write_bytes(raw); self.assertEqual(new['fixture_job_bounds'](root), {'threads': 1, 'input_size': 1})
            for changed in (raw + b'\n', raw.replace(b"'input_size': 1", b"'input_size': 2"), raw.replace(b'bounds=None', b'bounds={}')):
                self.assertNotEqual(changed, raw)
                target.write_bytes(changed)
                with self.assertRaises(AssertionError): new['fixture_job_bounds'](root)

    def test_copied_assertion_helper_positive_and_effectful_refusal(self):
        reader = load(HERE / 'passive_initialized_certificate_rechecker_v2.py')
        fixture = json.loads((HERE / 'source-location-repair-proposal-v1/synthetic-source-location-fixture.json').read_text())
        for row in fixture['cases']:
            self.assertIsNone(reader['_assertion'](row['ast'], row['expected'], row['variable'], row['tokens']))
            changed = copy.deepcopy(row)
            leaf = next(node for node in reader['_walk'](changed['ast']) if node.get('kind') == 'SourceLocExpr')
            leaf['inner'] = [{'kind': 'UnaryOperator', 'opcode': '++'}]
            with self.assertRaises(reader['Refused']): reader['_assertion'](changed['ast'], changed['expected'], changed['variable'], changed['tokens'])

    def test_stdlib_top_imports_and_no_runtime_audit_in_controls(self):
        for name in ('passive_initialized_certificate_rechecker_v2.py', 'initialized_cold_obligations_v2.py',
                     'initialized_cold_identities_v2.py', 'initialized_cold_audit_v2.py'):
            for node in ast.parse((HERE / name).read_text()).body:
                if isinstance(node, ast.Import): self.assertFalse(any(alias.name.startswith(('swdb', 'yaml')) for alias in node.names))
                if isinstance(node, ast.ImportFrom): self.assertFalse((node.module or '').startswith(('swdb', 'yaml')))
        self.assertEqual(EVENTS, [])


def inherited(path, old, new, class_name):
    source = path.read_text()
    class Rebind(ast.NodeTransformer):
        def visit_Constant(self, node):
            if node.value == old: return ast.copy_location(ast.Constant(value=new), node)
            return node
    module = Rebind().visit(ast.parse(source)); context = {'__name__': 'inert_inherited_' + class_name, '__file__': str(path)}
    exec(compile(ast.fix_missing_locations(module), str(path), 'exec'), context)
    return context[class_name]


if __name__ == '__main__':
    classes = [ColdV2Builder,
        inherited(HERE / 'test_initialized_cold_obligations.py', 'initialized_cold_obligations_v1.py', 'initialized_cold_obligations_v2.py', 'ColdObligations'),
        inherited(HERE / 'test_initialized_cold_audit_composition_v1.py', 'initialized_cold_audit_v1.py', 'initialized_cold_audit_v2.py', 'CompositionControls')]
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(kind) for kind in classes)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun == 23 and not result.skipped and not EVENTS else 1)
