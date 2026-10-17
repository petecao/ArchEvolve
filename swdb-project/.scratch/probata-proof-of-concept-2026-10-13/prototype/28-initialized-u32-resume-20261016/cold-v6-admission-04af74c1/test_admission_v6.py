"""2026-10-16 ET. Frame-only refusal controls; never invoke an audit."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
V5 = HERE.parent / 'cold-v5-admission-04af74c1'
OLD = (V5 / 'initialized_cold_audit_v5.py').read_text()
NEW = (HERE / 'initialized_cold_audit_v6.py').read_text()
assert hashlib.sha256(OLD.encode()).hexdigest() == '17fbffb48d689a9c6ead2d15fd6968184fd85d0c78ca46f3287e4d9b90abb894'


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.fork', 'os.forkpty'}:
        raise RuntimeError('frame-only control refuses ' + event)


sys.addaudithook(deny)


def formatter():
    node = next(node for node in ast.parse(NEW).body if isinstance(node, ast.FunctionDef) and node.name == 'refusal_frame_report_v6')
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-V6-frame-only-formatter>', 'exec'), namespace)
    return namespace[node.name]


class FrameControls(unittest.TestCase):
    def test_simulated_assertion_reports_only_exact_frame_identity(self):
        namespace = {}
        exec(compile('def synthetic_leaf():\n    private_payload = "PRIVATE_PAYLOAD_SENTINEL"\n    assert False, private_payload\n',
                     '<synthetic-no-science-frame>', 'exec'), namespace)
        try:
            namespace['synthetic_leaf']()
        except AssertionError as error:
            report = formatter()(error)
        self.assertEqual(set(report), {'classification', 'error_type', 'frames', 'frames_omitted', 'scientific_acceptance'})
        self.assertEqual(report['classification'], 'REFUSED'); self.assertEqual(report['error_type'], 'AssertionError')
        self.assertIs(report['scientific_acceptance'], False)
        self.assertEqual(report['frames'][-1], {'filename': '<synthetic-no-science-frame>', 'function': 'synthetic_leaf', 'line': 3})
        self.assertNotIn('PRIVATE_PAYLOAD_SENTINEL', json.dumps(report))
        self.assertTrue(all(set(frame) == {'filename', 'function', 'line'} for frame in report['frames']))

    def test_exception_message_and_locals_are_never_read(self):
        class OpaqueError(Exception):
            def __str__(self): raise RuntimeError('exception text must never be accessed')
        for error in (OpaqueError('SECRET_MESSAGE'), KeyError('SECRET_KEY')):
            try: raise error
            except Exception as caught: report = formatter()(caught)
            self.assertNotIn('SECRET', json.dumps(report))
            self.assertEqual(report['error_type'], type(error).__name__)
        node = next(node for node in ast.parse(NEW).body if isinstance(node, ast.FunctionDef) and node.name == 'refusal_frame_report_v6')
        attributes = {node.attr for node in ast.walk(node) if isinstance(node, ast.Attribute)}
        self.assertTrue({'__traceback__', 'tb_frame', 'f_code', 'co_filename', 'co_name', 'tb_lineno', 'tb_next'} <= attributes)
        self.assertFalse({'f_locals', 'f_globals', 'co_consts', '__dict__', 'args'} & attributes)
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'str', 'repr', 'format'} for node in ast.walk(node)))

    def test_traceback_is_bounded_and_still_refused(self):
        def descend(level):
            if level: return descend(level - 1)
            raise AssertionError('not exported')
        try: descend(30)
        except AssertionError as error: report = formatter()(error)
        self.assertEqual(len(report['frames']), 16)
        self.assertGreater(report['frames_omitted'], 0)
        self.assertEqual(report['error_type'], 'AssertionError')
        self.assertFalse(report['scientific_acceptance'])

    def test_exact_inverse_and_every_prior_function_byte_unchanged(self):
        old, new = ast.parse(OLD), ast.parse(NEW)
        new.body[0] = old.body[0]
        new.body = [node for node in new.body if not isinstance(node, ast.FunctionDef) or node.name != 'refusal_frame_report_v6']
        new.body[-1].body[-1].handlers[0].body[0] = old.body[-1].body[-1].handlers[0].body[0]
        self.assertEqual(ast.dump(old, include_attributes=False), ast.dump(new, include_attributes=False))
        for before in old.body:
            if isinstance(before, (ast.FunctionDef, ast.ClassDef)):
                after = next(node for node in new.body if isinstance(node, type(before)) and node.name == before.name)
                self.assertEqual(ast.get_source_segment(OLD, before), ast.get_source_segment(NEW, after))

    def test_policy_inverse_and_prior_actual_refusal_preserved(self):
        old = json.loads((V5 / 'initialized-cold-policy-04af74c1-v5.json').read_bytes())
        new = json.loads((HERE / 'initialized-cold-policy-04af74c1-v6.json').read_bytes())
        def undo(value):
            if isinstance(value, dict): return {key: undo(item) for key, item in value.items()}
            if isinstance(value, list): return [undo(item) for item in value]
            if isinstance(value, str): return value.replace('initialized-cold-04af74c1-v6', 'initialized-cold-04af74c1-v5')
            return value
        new = undo(new); new['reader_sha256'] = old['reader_sha256']
        for key in ('reader_base_v5', 'preserved_actual_v5_refusal', 'preserved_actual_v5_stdout'): new['provenance'].pop(key)
        self.assertEqual(new, old)
        original = json.loads((V5 / 'initialized-cold-v5-actual-stdout-20261016.json').read_bytes())
        self.assertEqual(original, {'classification': 'REFUSED', 'error_type': 'AssertionError', 'failure': '', 'scientific_acceptance': False})
        command = json.loads((HERE / 'initialized-cold-command-04af74c1-v6.json').read_bytes())
        self.assertEqual(len(command['control_files']), 10)
        self.assertLess(command['control_total_bytes'], 1048576)
        self.assertEqual(command['command'][-1], hashlib.sha256((HERE / 'initialized-cold-policy-04af74c1-v6.json').read_bytes()).hexdigest())


if __name__ == '__main__': unittest.main(verbosity=2)
