"""2026-10-16 ET. Scripted guard controls; no child/project/native execution.

Extract function definitions with stdlib AST. Every process/OS signal/watchdog
boundary is fake. File-size controls use disposable small local text fixtures.
"""
import ast
import hashlib
import json
import os
import re
import signal
import stat
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE/'entry-template-v2.py'
NAMES = {'guarded_generation', 'raw_bytes', 'bounded_bytes', 'bounded_json', 'task_census'}
tree = ast.parse(TEMPLATE.read_bytes())
definitions = ast.Module(body=[node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name in NAMES], type_ignores=[])
assert {node.name for node in definitions.body} == NAMES


def namespace():
    def pin(path):
        return {'path': str(path), 'bytes': path.stat().st_size,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    values = {'Path': Path, 'json': json, 'os': os, 'stat': stat, 'signal': signal,
              're': re, 'pin': pin, 'write': lambda p, v: p.write_text(json.dumps(v))}
    exec(compile(definitions, str(TEMPLATE), 'exec'), values)
    return values


class GuardControls(unittest.TestCase):
    def run_case(self, fault):
        values = namespace(); events = []; original = RuntimeError('scripted '+fault)

        class Process:
            pid = 1234
            returncode = None
            waits = 0

            def poll(self):
                events.append('poll')
                if fault == 'poll':
                    raise original
                if fault == 'raw':
                    return None
                self.returncode = 0
                return 0

            def wait(self, **kwargs):
                self.waits += 1; events.append(('wait', kwargs))
                if fault == 'wait' and self.waits == 1:
                    raise original
                self.returncode = 0
                return 0

        process = Process()

        class Watch:
            error = None
            peak = 64
            tripped = False

            def __enter__(self):
                events.append('watch-enter')
                if fault == 'enter':
                    raise original
                return self

            def __exit__(self, *_args):
                events.append('watch-exit')
                if fault == 'exit':
                    raise original

        def popen(*_args, **_kwargs):
            events.append('spawn')
            return process

        def size(_root):
            if fault == 'raw' and 'spawn' in events:
                raise original
            return 0

        values.update(subprocess=types.SimpleNamespace(Popen=popen, STDOUT='combined'),
            resource=types.SimpleNamespace(RLIMIT_FSIZE=1, setrlimit=lambda *_a: None),
            time=types.SimpleNamespace(monotonic=lambda: 0, sleep=lambda _seconds: None),
            os=types.SimpleNamespace(killpg=lambda pid, sig: events.append(('killpg', pid, sig)),
                                     kill=lambda pid, sig: events.append(('kill', pid, sig))),
            raw_bytes=size)
        watchdog = types.SimpleNamespace(tree=lambda _pid: {1234: 1, 1235: 1},
                                         TreeWatch=lambda *_a: Watch())
        with tempfile.TemporaryDirectory(prefix='t25-scripted-guard-v2-') as temporary:
            root = Path(temporary)
            policy = {'cap_bytes': 1024, 'output_budget_bytes': 4096, 'metadata_reserve_bytes': 512}
            if fault == 'normal-stragglers':
                result = values['guarded_generation'](['fake-never-executed'], root, {}, policy, 30, watchdog, root)
                self.assertEqual(result['exit_code'], 0)
            else:
                with self.assertRaises(RuntimeError) as caught:
                    values['guarded_generation'](['fake-never-executed'], root, {}, policy, 30, watchdog, root)
                self.assertIs(caught.exception, original)
            self.assertIn(('killpg', 1234, signal.SIGKILL), events)
            self.assertIn(('kill', 1235, signal.SIGKILL), events)
            self.assertIn(('wait', {'timeout': 10}), events)
        return events

    def test_raw_size_failure_after_spawn_kills_and_reaps_preserving_exception(self):
        self.run_case('raw')

    def test_watch_enter_failure_kills_and_reaps_preserving_exception(self):
        self.run_case('enter')

    def test_watch_exit_failure_kills_and_reaps_preserving_exception(self):
        self.run_case('exit')

    def test_poll_failure_kills_and_reaps_preserving_exception(self):
        self.run_case('poll')

    def test_wait_failure_kills_and_retries_reap_preserving_exception(self):
        self.run_case('wait')

    def test_normal_root_exit_still_cleans_known_stragglers_and_reaps(self):
        self.run_case('normal-stragglers')

    def test_raw_size_tolerates_only_disappearance(self):
        values = namespace()

        class FakeFile:
            def __init__(self, exception):
                self.exception = exception

            def stat(self):
                raise self.exception

        class FakeDirectory:
            def __init__(self, exception):
                self.exception = exception

            def __truediv__(self, _name):
                return FakeFile(self.exception)

        values['os'] = types.SimpleNamespace(walk=lambda *_a, **_k: [('root', [], ['file'])])
        values['Path'] = lambda _directory: FakeDirectory(FileNotFoundError('concurrent disappearance'))
        self.assertEqual(values['raw_bytes']('root'), 0)
        values['Path'] = lambda _directory: FakeDirectory(PermissionError('must fail'))
        with self.assertRaises(PermissionError):
            values['raw_bytes']('root')

    def test_census_projected_aggregate_budget_refuses_before_fragment_copy(self):
        values = namespace()
        with tempfile.TemporaryDirectory(prefix='t25-scripted-census-v2-') as temporary:
            directory = Path(temporary)
            inventory = {'complete': True, 'goals': [
                {'goal': 'typed_x', 'function': 'f', 'smoke': False, 'results': []},
                {'goal': 'typed_smoke', 'function': 'f', 'smoke': True, 'results': ['valid']}],
                'properties': []}
            (directory/'wp-inventory.json').write_text(json.dumps(inventory))
            for name in ('wp-normalized.c', 'wp-properties.csv', 'wp-goals.json'):
                (directory/name).write_text('scripted fixture only\n')
            segment = b'EXPORT GOAL x\ntheory WP\ngoal g: true\nend\n'
            (directory/'frama-c.log').write_bytes(segment)
            before = values['raw_bytes'](directory)
            policy = {'output_budget_bytes': before+len(segment)-1, 'metadata_reserve_bytes': 0}
            with self.assertRaisesRegex(ValueError, 'projected aggregate'):
                values['task_census'](directory, 'f', directory, policy)
            self.assertEqual(list((directory/'common-tasks').iterdir()), [])
            self.assertEqual(values['raw_bytes'](directory), before)

    def test_census_metadata_budget_refuses_before_metadata_write(self):
        values = namespace()
        with tempfile.TemporaryDirectory(prefix='t25-scripted-json-v2-') as temporary:
            root = Path(temporary); path = root/'census.json'
            policy = {'output_budget_bytes': 10, 'metadata_reserve_bytes': 0}
            with self.assertRaisesRegex(ValueError, 'projected aggregate'):
                values['bounded_json'](path, {'synthetic': 'metadata'}, root, policy)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GuardControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {'created': '2026-10-16 ET', 'scope': __doc__,
        'template': {'path': str(TEMPLATE), 'sha256': hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()},
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'all_passed': result.wasSuccessful(), 'real_child_processes_started': 0,
        'real_os_signals_sent': 0, 'project_imports': 0, 'compiler_native_or_verifier_calls': 0,
        'resource_or_generation_or_proof_acceptance': False}
    (HERE/'guard-controls-v2.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
