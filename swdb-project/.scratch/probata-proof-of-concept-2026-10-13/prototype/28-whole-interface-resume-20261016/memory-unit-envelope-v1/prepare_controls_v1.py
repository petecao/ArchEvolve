"""2026-10-16 ET. Derive only compiler-free memory-envelope controls."""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'normalized-unit-envelope-v4'


def function(text, name, replacement):
    node = next(n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef) and n.name == name)
    old = ast.get_source_segment(text, node)
    assert text.count(old) == 1
    return text.replace(old, replacement, 1)


text = (BASE / 'test_envelope_v4.py').read_text()
for old, new in (('linux_observation_envelope_v4.py', 'linux_memory_observation_envelope_v1.py'),
    ('prepare_envelope_v4.py', 'prepare_envelope_v1.py'), ('control/envelope-policy-v4.json', 'control/envelope-policy-v1.json'),
    ('source_call_fixture_v2.cpp', 'same_thread_memory_v1.cpp'), ('proof_units/source.cpp', 'proof_units/same_thread_memory_v1.cpp')):
    text = text.replace(old, new)
text = function(text, 'test_reviewed_observer_inventory_is_explicit_V4_successor', '''def test_memory_observer_inventory_and_actual_source_copies(self):
        observer = HERE.parent / 'memory-normalized-ingress-v2/observer'
        fixed = json.loads((observer / 'fixed-memory-modules-v1.json').read_bytes())
        self.assertEqual(len(fixed['modules']), 14)
        self.assertEqual(hashlib.sha256((observer / 'observe_memory_entry_v1.py').read_bytes()).hexdigest(), namespace()['OBSERVER_SHA'])
        self.assertEqual(len(namespace()['OBSERVER_CONTROLS']), 17)
        for row in fixed['modules']:
            raw = (observer / 'modules' / row['file']).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row['bytes'], row['sha256']))''')
text = function(text, 'test_root_metadata_is_literal_five_pin_closed_selection', '''def test_root_node_and_reviewed_guard_selection_are_closed(self):
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
            with self.assertRaises(ValueError): exec(code, ns)''')
text = function(text, 'test_exact_v1_inverse_and_scientific_controls_unchanged', '''def test_exact_reviewed_V4_inverse_and_no_guard_relaxation(self):
        text = SOURCE.read_text()
        inverse = json.loads((HERE / 'exact-envelope-inverse-v1.json').read_bytes())
        for row in reversed(inverse['replacements']):
            self.assertEqual(text.count(row['new']), row['count']); text = text.replace(row['new'], row['old'])
        self.assertEqual(text, Path(inverse['basis']['path']).read_text())
        self.assertIn("'envelope-finalization-refusal.json'", SOURCE.read_text())
        self.assertIn('20 * 1024**3', SOURCE.read_text())
        self.assertEqual(namespace()['WHOLE_SECONDS'], 1200)
        self.assertEqual(namespace()['ENTRY_SECONDS'], 1180)
        self.assertEqual(namespace()['RSS_BYTES'], 4294967296)''')
(HERE / 'test_envelope_v1.py').write_text(text)

text = (BASE / 'test_root_environment_v4.py').read_text()
text = text.replace("'test_envelope_v4.py'", "'test_envelope_v1.py'").replace("'command-v4.json'", "'command-v1.json'")
text = text.replace('linux_observation_envelope_v4.py', 'linux_memory_observation_envelope_v1.py')
text = function(text, 'test_namespace_inventory_inverse_and_stable_functions_exact', '''def test_literal_memory_binding_and_stable_functions_exact(self):
        current = HERE / 'linux_memory_observation_envelope_v1.py'
        source = current.read_text()
        inverse = json.loads((HERE / 'exact-envelope-inverse-v1.json').read_bytes())
        for row in reversed(inverse['replacements']):
            self.assertEqual(source.count(row['new']), row['count']); source = source.replace(row['new'], row['old'])
        before = Path(inverse['basis']['path'])
        self.assertEqual(source, before.read_text())
        for name in ('bind_environment', 'publish_final_result', 'read', 'runtime_helpers', 'check_outputs'):
            def body(path):
                return ast.dump(next(n for n in ast.parse(path.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == name))
            self.assertEqual(body(current), body(before))''')
text = function(text, 'test_root_command_and_explicit_observer_successor_closure', '''def test_root_command_memory_controls_and_pending_selection_are_explicit(self):
        old = json.loads((WHOLE / 'normalized-unit-envelope-v4/command-v4.json').read_bytes())
        self.assertEqual(COMMAND['root_launcher'], old['root_launcher'])
        self.assertEqual(COMMAND['guard'], old['guard'])
        self.assertEqual(COMMAND['root_launch_requirements'], old['root_launch_requirements'])
        self.assertEqual(COMMAND['root_created_directories'], [COMMAND['raw'] + '/control'])
        self.assertLessEqual(COMMAND['root_controls_bytes_including_policy'], 1048576)
        self.assertFalse(COMMAND['root_metadata_complete'])
        policy = json.loads((HERE / 'envelope-policy-v1.json').read_bytes())
        self.assertIsNone(policy['node']); self.assertIsNone(policy['guard_files'])
        self.assertEqual(set(COMMAND['stage_sources']), set(policy['controls']))
        self.assertEqual(len(COMMAND['stage_sources']), 35)
        for row in COMMAND['stage_sources'].values():
            data = Path(row['path']).read_bytes()
            self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (row['bytes'], row['sha256']))
        self.assertIn('no review or execution authority', COMMAND['root_source_provenance_role'])''')
(HERE / 'test_root_environment_v1.py').write_text(text)
