"""No-child stdlib controls; never execute the envelope or scientific observer."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
import types
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'linux_memory_observation_envelope_v1.py'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('no child/native/network in envelope controls')


sys.addaudithook(audit)


def namespace():
    tree = ast.parse(SOURCE.read_bytes())
    wanted = [node for node in tree.body if isinstance(node, (ast.Assign, ast.FunctionDef))]
    result = {'Path': Path, 'hashlib': hashlib, 'json': json, 'os': os, 'stat': stat, 'sys': sys,
              'ast': ast, 'types': types}
    exec(compile(ast.Module(body=wanted, type_ignores=[]), '<exact-envelope-pure-controls>', 'exec'), result)
    return result


def fixture(ns, root):
    raw = root / ns['RAW_NAME']; (raw / 'control').mkdir(parents=True)
    controls = {}
    for name in ns['OBSERVER_CONTROLS']:
        path = raw / 'control' / name; path.write_bytes(('inert stand-in for ' + name).encode())
        controls[name] = ns['pin'](path)
    source = raw / 'control/same_thread_memory_v1.cpp'; source.write_bytes(b'inert proof-buffer stand-in')
    controls[source.name] = ns['pin'](source)
    observer = {'output_root': str(raw / 'observer'), 'library_root': str(raw / 'library_fixture'),
        'controls': {name: {**row, 'path': str(raw / 'observer/control' / name)} for name, row in controls.items()
                     if name in ns['OBSERVER_CONTROLS']}}
    policy_path = raw / 'control/observation-policy-v1.json'
    policy_path.write_text(json.dumps(observer)); controls[policy_path.name] = ns['pin'](policy_path)
    policy = {'controls': controls, 'observer_policy': {**ns['pin'](policy_path), 'path': str(raw / 'observer/control' / policy_path.name)},
              'library_source': {**ns['pin'](source), 'path': str(raw / 'library_fixture/proof_units/same_thread_memory_v1.cpp')}}
    return raw, policy


class Controls(unittest.TestCase):
    def test_memory_observer_inventory_and_actual_source_copies(self):
        observer = HERE.parent / 'memory-normalized-ingress-v2/observer'
        fixed = json.loads((observer / 'fixed-memory-modules-v1.json').read_bytes())
        self.assertEqual(len(fixed['modules']), 14)
        self.assertEqual(hashlib.sha256((observer / 'observe_memory_entry_v1.py').read_bytes()).hexdigest(), namespace()['OBSERVER_SHA'])
        self.assertEqual(len(namespace()['OBSERVER_CONTROLS']), 17)
        for row in fixed['modules']:
            raw = (observer / 'modules' / row['file']).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row['bytes'], row['sha256']))

    def test_actual_copy_stage_and_complete_thirteen_control_membership(self):
        ns = namespace()
        with tempfile.TemporaryDirectory() as directory:
            raw, policy = fixture(ns, Path(directory).resolve()); ns['stage_layout'](raw, policy)
            self.assertEqual({p.name for p in (raw / 'observer/control').iterdir()}, set(ns['OBSERVER_CONTROLS']) | {'observation-policy-v1.json'})
            for name in ns['OBSERVER_CONTROLS']:
                self.assertEqual((raw / 'control' / name).read_bytes(), (raw / 'observer/control' / name).read_bytes())
            self.assertEqual((raw / 'library_fixture/proof_units/same_thread_memory_v1.cpp').read_bytes(), (raw / 'control/same_thread_memory_v1.cpp').read_bytes())
            with self.assertRaises(ValueError): ns['stage_layout'](raw, policy)

    def test_copy_stage_refuses_changed_hash_wrong_role_and_extra_control(self):
        ns = namespace()
        for mutation in ('hash', 'role', 'extra'):
            with tempfile.TemporaryDirectory() as directory:
                raw, policy = fixture(ns, Path(directory).resolve())
                if mutation == 'hash': policy['controls']['whole_interface_v4.py']['sha256'] = '0' * 64
                elif mutation == 'role': policy['library_source']['path'] = str(raw / 'escape.cpp')
                else:
                    file = raw / 'control/observation-policy-v1.json'; value = json.loads(file.read_bytes())
                    value['controls']['extra.py'] = value['controls']['whole_interface_v4.py']; file.write_text(json.dumps(value))
                    policy['controls'][file.name] = ns['pin'](file)
                    policy['observer_policy'] = {**ns['pin'](file), 'path': str(raw / 'observer/control' / file.name)}
                with self.assertRaises(ValueError): ns['stage_layout'](raw, policy)
                self.assertFalse((raw / 'observer').exists())

    def test_physical_reader_atime_pass_and_alias_hash_extent_refusal(self):
        ns = namespace()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'data'; path.write_bytes(b'closed bytes'); row = ns['pin'](path)
            before = path.stat(); os.utime(path, ns=(before.st_atime_ns + 1000000, before.st_mtime_ns))
            self.assertEqual(ns['read'](row), b'closed bytes')
            link = Path(directory).resolve() / 'alias'; link.symlink_to(path)
            with self.assertRaises(ValueError): ns['read']({**row, 'path': str(link)})
            with self.assertRaises(ValueError): ns['read']({**row, 'sha256': '0' * 64})
            with self.assertRaises(ValueError): ns['read']({**row, 'bytes': 1})

    def test_root_node_and_reviewed_guard_selection_are_closed(self):
        source = (HERE / 'prepare_envelope_v1.py').read_bytes()
        tree = ast.parse(source)
        build = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build')
        validation = next(n for n in build.body if isinstance(n, ast.If))
        assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('ROOT_SELECTION_KEYS', 'KNOWN_GUARDS') for t in n.targets)]
        ns = {}; exec(compile(ast.Module(assignments, type_ignores=[]), 'closed-root-guard-constants', 'exec'), ns)
        value = {'guard_files': copy.deepcopy(ns['KNOWN_GUARDS']), 'node': 0}
        ns['root_selection'] = value
        code = compile(ast.Module([validation], type_ignores=[]), 'exact-memory-root-selection', 'exec')
        exec(code, ns)
        for mutation in ('missing', 'unknown', 'bool-node', 'extra-guard', 'wrong-guard'):
            changed = copy.deepcopy(value)
            if mutation == 'missing': changed.pop('guard_files')
            elif mutation == 'unknown': changed['authority'] = True
            elif mutation == 'bool-node': changed['node'] = True
            elif mutation == 'extra-guard': changed['guard_files']['other.py'] = 'a' * 64
            else: changed['guard_files']['execute.py'] = 'a' * 64
            ns['root_selection'] = changed
            with self.assertRaises(ValueError): exec(code, ns)

    def test_actual_launch_guard_seam_and_inverses(self):
        ns = namespace(); ns['PYTHON'] = '/selected/python'
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve(); digest = 'd' * 64
            for name in ('execute.py', 'watch.py'): (raw / name).write_bytes(name.encode())
            guards = {name: ns['pin'](raw / name)['sha256'] for name in ('execute.py', 'watch.py')}
            argv = ['entry', str(raw), 'policy', digest]
            launch = {'command': [ns['PYTHON'], '-I', '-B', '-X', 'pycache_prefix=' + str(raw / 'entry-source-cache'),
                str(raw / 'control/linux_memory_observation_envelope_v1.py'), str(raw), str(raw / 'control/envelope-policy-v1.json'), digest],
                'source': str(Path(ns['PROJECT']).parent), 'source_commit': ns['SOURCE_COMMIT'], 'rss_cap_bytes': 4294967296,
                'workers': 1, 'timeout_seconds': 1200, 'node': 0, 'reviewed_wrapper_reuse': guards}
            def selected(node): self.assertEqual(node, 0); return {'fixed-live-stand-in': True}
            path = raw / 'launch.json'; path.write_text(json.dumps(launch))
            policy = {'node': 0, 'guard_files': guards}
            self.assertFalse(ns['check_launch'](raw, policy, argv, selected)['Mac_counted_claim'])
            for key, value in [('rss_cap_bytes', 8589934592), ('workers', 2), ('timeout_seconds', 180), ('source_commit', '0' * 40), ('node', 1)]:
                bad = {**launch, key: value}; path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError): ns['check_launch'](raw, policy, argv, selected)

    def test_exact_inherited_runtime_nodes_and_stable_guard_preserved(self):
        ns = namespace(); old = HERE.parent / 'linux_native86_entry_v4.py'
        real = ns['runtime_helpers'](old.read_bytes())
        for name in ('verified_linux_lane', 'physical_runtime'): self.assertTrue(callable(real[name]))
        with self.assertRaises(ValueError): ns['runtime_helpers'](old.read_bytes() + b'\n')
        source = SOURCE.read_text()
        self.assertIn('signal.setitimer(signal.ITIMER_REAL, ENTRY_SECONDS)', source)
        self.assertIn("module.main([policy['observer_policy']['path'], policy['observer_policy']['sha256']])", source)
        self.assertIn("before is not None and after == before", source)
        self.assertNotIn('subprocess', ''.join(ast.unparse(node) for node in ast.parse(source).body if isinstance(node, (ast.Import, ast.ImportFrom))))

    def test_outputs_and_bounded_refusal_frames(self):
        ns = namespace()
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve(); (raw / 'observer/control').mkdir(parents=True)
            ns['check_outputs'](raw)
            (raw / 'observer/unknown').write_bytes(b'bad')
            with self.assertRaises(ValueError): ns['check_outputs'](raw)
        try: raise AssertionError('must not be emitted')
        except AssertionError as error:
            value = ns['frames'](error)
        self.assertEqual(set(value), {'type', 'frames'})
        self.assertEqual(set(value['frames'][0]), {'filename', 'function', 'line'})
        self.assertNotIn('must not be emitted', json.dumps(value))

    def test_exact_known_root_environment_projection_and_unknown_selector_refusal(self):
        ns = namespace(); runtime = {'path': '/usr/bin:/bin', 'home': '/pinned/home',
            'native_runtime': {'loader_environment': {'LD_LIBRARY_PATH': '/pinned/llvm/lib'}}}
        raw = Path('/fixed/raw')
        base = {'PATH': '/root/known/tool-path', 'HOME': '/root/home', 'PYTHONPATH': ns['PROJECT'],
                'LD_LIBRARY_PATH': '/pinned/llvm/lib', 'LACT_SOCKET_LANE_PID': '42'}
        environment = dict(base); result = ns['bind_environment'](raw, runtime, environment)
        self.assertEqual(environment['PATH'], runtime['path']); self.assertEqual(environment['HOME'], runtime['home'])
        self.assertNotIn('PYTHONPATH', environment); self.assertNotIn('LD_LIBRARY_PATH', environment)
        self.assertEqual(environment['LACT_SOCKET_LANE_PID'], '42')
        self.assertEqual(result['known_root_environment_before']['PYTHONPATH'], ns['PROJECT'])
        for name, value in [('PYTHONPATH', '/unadmitted/project'), ('PYTHONOPTIMIZE', '1'), ('PYTHONHOME', '/evil'),
                            ('LD_PRELOAD', '/evil.so'), ('LIBRARY_PATH', '/evil'), ('LD_LIBRARY_PATH', '/evil'),
                            ('__PYVENV_LAUNCHER__', '/evil')]:
            with self.assertRaises(ValueError): ns['bind_environment'](raw, runtime, {**base, name: value})

    def test_closed_metadata_and_no_project_child_native_actions(self):
        ns = namespace()
        with self.assertRaises(ValueError): ns['document'](b'{"x":1,"x":2}')
        with self.assertRaises(ValueError): ns['document'](b'{"x":NaN}')
        self.assertEqual(EVENTS, [])

    def test_bounded_reader_refuses_actual_oversize_before_open_or_hash(self):
        ns = namespace(); calls = []
        class NoOpenPath(type(Path())):
            def open(self, *args, **kwargs):
                calls.append('open')
                raise RuntimeError('unbounded consumption was attempted')
        ns['Path'] = NoOpenPath
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'oversized'; path.write_bytes(b'long actual contents')
            row = {'path': str(path), 'bytes': 1, 'sha256': '0' * 64}
            with self.assertRaises(ValueError): ns['read'](row)
            self.assertEqual(calls, [])
            old = HERE.parent / 'normalized-unit-envelope-v1/linux_observation_envelope_v1.py'
            function = next(node for node in ast.parse(old.read_bytes()).body if isinstance(node, ast.FunctionDef) and node.name == 'read')
            old_ns = dict(ns); exec(compile(ast.Module(body=[function], type_ignores=[]), '<old-unbounded-reader>', 'exec'), old_ns)
            # V1 RED at the actual leaf read seam, before its selected extent check.
            old_ns['pin'] = lambda _path: (_ for _ in ()).throw(RuntimeError('hash before extent'))
            with self.assertRaisesRegex(RuntimeError, 'hash before extent'): old_ns['read'](row)

    def test_postpublication_deadline_flush_and_extent_refuse_with_zero_exit_required(self):
        def run(clock, *, fail_post=False, fail_flush=False):
            ns = namespace(); saved = {}; printed = []; moments = iter(clock); checks = []
            ns['time'] = types.SimpleNamespace(monotonic=lambda: next(moments))
            def save(path, value): saved[path.name] = copy.deepcopy(value)
            def check(_raw):
                checks.append(True)
                if fail_post and len(checks) == 2: raise ValueError('settled quota')
            def flush():
                if fail_flush: raise TimeoutError('during flush')
            ns.update(save=save, check_outputs=check, print=lambda value: printed.append(value),
                      sys=types.SimpleNamespace(stdout=types.SimpleNamespace(flush=flush)))
            accepted = ns['publish_final_result'](Path('/exact/raw'), {'observation_complete': True, 'public_admission': False}, 0)
            return accepted, saved, printed
        accepted, saved, printed = run([1179.0, 1179.9])
        self.assertTrue(accepted); self.assertEqual(set(saved), {'envelope-result.json'})
        self.assertTrue(saved['envelope-result.json']['completion_requires_zero_exit_and_settled_finalization'])
        for times, options in [([1180.1, 1180.2], {}), ([1179.9, 1180.1, 1180.2], {}),
                               ([1179.9, 1179.9], {'fail_post': True}), ([1179.9, 1179.9], {'fail_flush': True})]:
            accepted, saved, printed = run(times, **options)
            self.assertFalse(accepted)
            self.assertFalse(saved['envelope-finalization-refusal.json']['observation_complete'])
            self.assertTrue(saved['envelope-finalization-refusal.json']['earlier_result_alone_cannot_establish_completion'])
            if 'envelope-result.json' in saved: self.assertTrue(saved['envelope-result.json']['observation_complete'])

    def test_exact_reviewed_V4_inverse_and_no_guard_relaxation(self):
        text = SOURCE.read_text()
        inverse = json.loads((HERE / 'exact-envelope-inverse-v1.json').read_bytes())
        for row in reversed(inverse['replacements']):
            self.assertEqual(text.count(row['new']), row['count']); text = text.replace(row['new'], row['old'])
        self.assertEqual(text, Path(inverse['basis']['path']).read_text())
        self.assertIn("'envelope-finalization-refusal.json'", SOURCE.read_text())
        self.assertIn('20 * 1024**3', SOURCE.read_text())
        self.assertEqual(namespace()['WHOLE_SECONDS'], 1200)
        self.assertEqual(namespace()['ENTRY_SECONDS'], 1180)
        self.assertEqual(namespace()['RSS_BYTES'], 4294967296)


if __name__ == '__main__': unittest.main(verbosity=2)
