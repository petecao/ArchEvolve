"""2026-10-16 ET. Error formatting/inverse controls only; no actual audit."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
V1 = TRACE / 'trace-cold-audit-v1'
V2 = TRACE / 'trace-cold-admission-04af74c1-v2'
INITIALIZED = TRACE.parent / '28-initialized-u32-resume-20261016/cold-v6-admission-04af74c1/initialized_cold_audit_v6.py'
OLD = (V1 / 'trace_cold_audit_v1.py').read_text()
NEW = (HERE / 'trace_cold_audit_v3.py').read_text()
assert hashlib.sha256(OLD.encode()).hexdigest() == '3cefa1c4eb7c05371afcdaf8b43d6f46927dfe80aed0be90e652bac0cf0157ee'


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.fork', 'os.forkpty'}:
        raise RuntimeError('trace frame control refuses ' + event)


sys.addaudithook(deny)


class TraceFrameControls(unittest.TestCase):
    def test_all_prior_functions_byte_unchanged_and_complete_ast_inverse(self):
        old, new = ast.parse(OLD), ast.parse(NEW)
        new.body = [node for node in new.body if not isinstance(node, ast.FunctionDef) or node.name != 'refusal_frame_report_v6']
        new.body[-1].body[-1].handlers[0].body[0] = old.body[-1].body[-1].handlers[0].body[0]
        self.assertEqual(ast.dump(old, include_attributes=False), ast.dump(new, include_attributes=False))
        for before in old.body:
            if isinstance(before, (ast.FunctionDef, ast.ClassDef)):
                after = next(node for node in new.body if isinstance(node, type(before)) and node.name == before.name)
                self.assertEqual(ast.get_source_segment(OLD, before), ast.get_source_segment(NEW, after))

    def test_exact_initialized_formatter_copy_and_actual_trace_refusal_expression(self):
        origin = INITIALIZED.read_text()
        self.assertEqual(hashlib.sha256(origin.encode()).hexdigest(), '02744c321c9bc60535f374d0b47b4d634b54e02c9786a31351c77859c3d8b598')
        node = next(node for node in ast.parse(NEW).body if isinstance(node, ast.FunctionDef) and node.name == 'refusal_frame_report_v6')
        expected = next(node for node in ast.parse(origin).body if isinstance(node, ast.FunctionDef) and node.name == 'refusal_frame_report_v6')
        self.assertEqual(ast.get_source_segment(NEW, node), ast.get_source_segment(origin, expected))
        captured = []
        namespace = {'json': json, 'print': captured.append}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-shared-frame-formatter>', 'exec'), namespace)
        def simulated_assertion(): raise AssertionError('PRIVATE_PAYLOAD_SENTINEL')
        try: simulated_assertion()
        except AssertionError as error:
            namespace['error'] = error
            statement = ast.parse(NEW).body[-1].body[-1].handlers[0].body[0]
            exec(compile(ast.Module(body=[statement], type_ignores=[]), '<exact-trace-refusal-expression>', 'exec'), namespace)
        self.assertEqual(len(captured), 1)
        self.assertNotIn('PRIVATE_PAYLOAD_SENTINEL', captured[0])
        report = json.loads(captured[0])
        self.assertEqual(report['error_type'], 'AssertionError')
        self.assertFalse(report['scientific_acceptance'])
        self.assertEqual(report['frames'][-1]['function'], 'simulated_assertion')
        self.assertTrue(all(set(frame) == {'filename', 'function', 'line'} for frame in report['frames']))
        self.assertNotIn('failure', report)

    def test_policy_inverse_and_complete_local_control_manifest(self):
        old = json.loads((V2 / 'trace-cold-policy-04af74c1-v2.json').read_bytes())
        new = json.loads((HERE / 'trace-cold-policy-04af74c1-v3.json').read_bytes())
        def undo(value):
            if isinstance(value, dict): return {key: undo(item) for key, item in value.items()}
            if isinstance(value, list): return [undo(item) for item in value]
            if isinstance(value, str): return value.replace('trace-cold-04af74c1-v3', 'trace-cold-04af74c1-v2')
            return value
        new = undo(new); new['reader_sha256'] = old['reader_sha256']; new['provenance'].pop('frame_only_diagnostics')
        self.assertEqual(new, old)
        command = json.loads((HERE / 'trace-cold-command-04af74c1-v3.json').read_bytes())
        manifest = json.loads((HERE / 'trace-cold-control-manifest-v3.json').read_bytes())
        self.assertEqual(command['control_file_count'], 17)
        self.assertEqual(manifest['payload_file_count'], 16)
        self.assertEqual(manifest['expected_control_basenames'], sorted(command['control_files']))
        self.assertLess(command['control_total_bytes'], 1048576)
        for row in command['control_files'].values():
            data = Path(row['source']).read_bytes()
            self.assertEqual(len(data), row['bytes']); self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
        self.assertEqual(command['command'][-1], hashlib.sha256((HERE / 'trace-cold-policy-04af74c1-v3.json').read_bytes()).hexdigest())
        self.assertEqual(command['process_environment_mode'], 'replace')
        self.assertEqual(set(command['process_environment']), {'PATH', 'LANG', 'LC_ALL', 'PYTHONPATH', 'PYTHONPYCACHEPREFIX', 'PYTHONDONTWRITEBYTECODE'})

    def test_previous_staged_context_and_false_admission_template_preserved(self):
        receipt = (V2 / 'staging-receipt-20261016.json').read_bytes()
        self.assertEqual(hashlib.sha256(receipt).hexdigest(), 'e1a75dc16afdcde062cf79910b3fbf1adfb727d5e7a24a506e5a1db9f78cc42a')
        self.assertFalse(json.loads(receipt)['reader_executed'])
        template = (V1 / 'trace-cold-policy-template-04af74c1-v1.json').read_bytes()
        self.assertEqual(hashlib.sha256(template).hexdigest(), 'f292d4e3158859869ef59697bcf9d777a4e8859923e949b3d396a35c2b58b6fb')
        self.assertFalse(json.loads(template)['admitted'])
        self.assertEqual(hashlib.sha256((V2 / 'trace-cold-policy-04af74c1-v2.json').read_bytes()).hexdigest(),
                         'ee3b56886af7a9c257309b1acd6cd3077b1308652a39c8a794a6f32644ece8b7')


if __name__ == '__main__': unittest.main(verbosity=2)
