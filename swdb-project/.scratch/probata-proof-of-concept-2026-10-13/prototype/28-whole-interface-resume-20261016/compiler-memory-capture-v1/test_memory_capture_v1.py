"""2026-10-16 ET. Pure original-recipe, refusal and finalization controls."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

EVENTS = []
def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('memory capture controls refuse ' + event)
sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OLD = WHOLE / 'compiler-capture-v10'
def load(path):
    namespace = {'__name__': 'inert_memory_capture', '__file__': str(path)}
    exec(compile(path.read_bytes(), str(path), 'exec'), namespace)
    return namespace
N = load(HERE / 'linux_memory_capture_v1.py')
A = load(WHOLE / 'streaming-minify-v1/compiler_unit_adapter_v4.py')
D = json.loads((HERE / 'memory-capture-v1-inverse.json').read_bytes())
P = json.loads((HERE / 'linux_memory_capture_policy_v1.json').read_bytes())
C = json.loads((HERE / 'linux_memory_capture_command_v1.json').read_bytes())
def functions(raw):
    return {item.name: ast.dump(item) for item in ast.parse(raw).body if isinstance(item, (ast.FunctionDef, ast.ClassDef))}
def inverse(value, edits):
    value = copy.deepcopy(value)
    for edit in reversed(edits):
        parent = value
        for key in edit['path'][:-1]: parent = parent[key]
        key = edit['path'][-1]
        if edit.get('added'): del parent[key]
        elif edit.get('removed'): parent[key] = edit['old']
        else: parent[key] = edit['old']
    return value
class Controls(unittest.TestCase):
    def test_exact_entry_inverse_and_common_gates(self):
        text = (HERE / 'linux_memory_capture_v1.py').read_text()
        for edit in reversed(D['entry_edits']):
            at = edit['offset']
            self.assertEqual(text[at:at + len(edit['new'])], edit['new'])
            text = text[:at] + edit['old'] + text[at + len(edit['new']):]
        old = Path(D['predecessor']['path']).read_text()
        self.assertEqual(text, old)
        before, after = functions(old), functions((HERE / 'linux_memory_capture_v1.py').read_bytes())
        for name in D['unchanged_functions']: self.assertEqual(before[name], after[name], name)
    def test_recipe_changes_only_two_original_caller_inputs_and_transport_scope(self):
        adapter = types.SimpleNamespace(capture_recipe=A['capture_recipe'])
        kw = {'compiler': P['compiler']['command'][0], 'project': P['source_project'], 'raw': C['raw_root']}
        old = N['lossless_recipe'](adapter, **kw)
        new = N['memory_observation_recipe'](adapter, **kw)
        self.assertEqual(new, P['capture_recipe'])
        self.assertEqual(new, C['recipe'])
        self.assertEqual(new['commands'][2:], old['commands'][2:])
        for before, after in zip(old['commands'][:2], new['commands'][:2]):
            repaired = copy.deepcopy(after)
            repaired['argv'] = [item.replace('/same_thread_memory_v1.cpp', '/source_call_fixture_v2.cpp') for item in repaired['argv']]
            self.assertEqual(before, repaired)
            self.assertEqual(after['argv'].count(C['raw_root'] + '/control/same_thread_memory_v1.cpp'), 1)
        self.assertNotIn('-ast-dump-filter', ' '.join(new['commands'][1]['argv']))
        for key in old:
            if key not in {'commands', 'lossless_caller_stdout'}: self.assertEqual(old[key], new[key])
    def test_wrong_recipe_source_refuses(self):
        def changed(**kw):
            recipe = A['capture_recipe'](**kw)
            recipe['commands'][0]['argv'][-3] = '/some/other.cpp'
            return recipe
        with self.assertRaisesRegex(ValueError, 'original-source caller recipe'):
            N['memory_observation_recipe'](types.SimpleNamespace(capture_recipe=changed), compiler='/clang', project='/project', raw='/raw')
    def test_complete_phase_census_requires_real_zero_exits_and_both_groups(self):
        rows = [{'phase': name, 'returncode': 0} for name in ['caller-preprocess', 'caller-ast', 'abi-preprocess', 'abi-ast']]
        groups = [{'label': 'caller'}, {'label': 'abi'}]
        self.assertTrue(N['complete_observation'](rows, groups))
        for index in range(4):
            for status in [1, -9, None, False]:
                changed = copy.deepcopy(rows); changed[index]['returncode'] = status
                self.assertFalse(N['complete_observation'](changed, groups))
        self.assertFalse(N['complete_observation'](rows[:-1], groups))
        self.assertFalse(N['complete_observation'](list(reversed(rows)), groups))
        self.assertFalse(N['complete_observation'](rows, groups[:1]))
        self.assertFalse(N['complete_observation'](rows, list(reversed(groups))))
    def test_dependency_changes_refuse(self):
        rows = [{'path': '/a'}, {'path': '/b'}]
        N['compare_dependencies'](rows, ['/a', '/b'], {'/a'})
        for after, required in [(['/b', '/a'], {'/a'}), (['/a'], {'/a'}), (['/a', '/b'], {'/c'})]:
            with self.assertRaises(ValueError): N['compare_dependencies'](rows, after, required)
    def test_stable_stat_retains_all_identity_fields_except_atime(self):
        fields = dict(st_dev=1, st_ino=2, st_mode=3, st_nlink=4, st_uid=5, st_gid=6, st_size=7, st_mtime_ns=8, st_ctime_ns=9, st_atime_ns=10)
        stable = N['_stable_capture_stat'](types.SimpleNamespace(**fields))
        changed = dict(fields, st_atime_ns=11)
        self.assertEqual(stable, N['_stable_capture_stat'](types.SimpleNamespace(**changed)))
        for name in fields:
            if name == 'st_atime_ns': continue
            changed = dict(fields); changed[name] += 1
            self.assertNotEqual(stable, N['_stable_capture_stat'](types.SimpleNamespace(**changed)))
    def test_budget_and_late_finalization_refuse_without_raising_caps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'component'; out.mkdir()
            good = {'accepted': True, 'compiler_observation_complete': True, 'source_call_admitted': False}
            late, _, _ = N['finalization_payloads'](root, out, good, used_bytes=0, elapsed=165.001)
            self.assertFalse(late['accepted']); self.assertFalse(late['source_call_admitted'])
            large, _, _ = N['finalization_payloads'](root, out, good, used_bytes=268435456, elapsed=1)
            self.assertFalse(large['accepted']); self.assertFalse(large['source_call_admitted'])
    def test_policy_command_complete_inverses_and_exact_staging(self):
        old_policy = json.loads(Path(D['predecessor_policy']['path']).read_bytes())
        old_command = json.loads(Path(D['predecessor_command']['path']).read_bytes())
        self.assertEqual(inverse(P, D['policy_edits']), old_policy)
        self.assertEqual(inverse(C, D['command_edits']), old_command)
        for key in ['budgets', 'compiler', 'native_runtime', 'startup_roles', 'python_surface_binding', 'guard_files', 'zlib_binding', 'source_inputs']:
            self.assertEqual(P[key], old_policy[key])
        self.assertEqual(C['root_guard'], old_command['root_guard'])
        self.assertEqual(C['node'], 1)
        self.assertLess(sum(row['bytes'] for row in C['controller_inputs']), 1048576)
        for row in C['controller_inputs']:
            data = Path(row['path']).read_bytes()
            self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (row['bytes'], row['sha256']))
        self.assertEqual(C['argv'][-1], hashlib.sha256((HERE / 'linux_memory_capture_policy_v1.json').read_bytes()).hexdigest())
        names = [Path(row['path']).name for row in C['controller_inputs']]
        self.assertEqual(names.count('same_thread_memory_v1.cpp'), 1)
        self.assertNotIn('whole_interface_v4.py', names)
        self.assertNotIn('strict_minify_v2.py', names)
    def test_main_has_no_AST_or_ABI_or_source_interpreter(self):
        main = next(item for item in ast.parse((HERE / 'linux_memory_capture_v1.py').read_bytes()).body if isinstance(item, ast.FunctionDef) and item.name == 'main')
        called = {ast.unparse(item.func) for item in ast.walk(main) if isinstance(item, ast.Call)}
        for name in ['adapter.prepare_unit', 'binder.inventory', 'minifier.minify', 'codec.DecodeReader', 'check_prepared']:
            self.assertNotIn(name, called)
        self.assertIn('complete_observation', called)
    def test_no_child_events(self): self.assertEqual(EVENTS, [])
if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date': '2026-10-16 ET', 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
        'child_events': EVENTS, 'entry_sha256': hashlib.sha256((HERE / 'linux_memory_capture_v1.py').read_bytes()).hexdigest(),
        'controls_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'scope': 'Pure recipe/inverse/phase/refusal/finalization controls only; no compiler/source/API acceptance'}))
    sys.exit(not result.wasSuccessful())
