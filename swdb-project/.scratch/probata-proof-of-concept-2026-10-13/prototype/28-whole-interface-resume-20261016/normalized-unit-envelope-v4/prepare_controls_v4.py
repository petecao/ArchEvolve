"""2026-10-16 ET. Derive no-child predecessor controls for explicit V4 roles."""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'normalized-unit-envelope-v3'


def replace_function(text, name, replacement):
    node = next(node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.FunctionDef) and node.name == name)
    old = ast.get_source_segment(text, node)
    assert text.count(old) == 1
    return text.replace(old, replacement, 1)


source = (OLD / 'test_envelope_v3.py').read_text()
for old, new in (('linux_observation_envelope_v3.py', 'linux_observation_envelope_v4.py'),
    ('prepare_envelope_v3.py', 'prepare_envelope_v4.py'), ('control/envelope-policy-v3.json', 'control/envelope-policy-v4.json')):
    source = source.replace(old, new)
source = replace_function(source, 'test_reviewed_observer_and_eleven_modules_unchanged', '''def test_reviewed_observer_inventory_is_explicit_V4_successor(self):
        observer = HERE / 'observer'
        fixed = json.loads((observer / 'fixed-modules-v2.json').read_bytes())
        self.assertEqual(len(fixed['modules']), 13)
        self.assertEqual(hashlib.sha256((observer / 'observe_entry_v2.py').read_bytes()).hexdigest(), namespace()['OBSERVER_SHA'])
        for row in fixed['modules']:
            raw = (observer / 'modules' / row['file']).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row['bytes'], row['sha256']))''')
old = "        for row in reversed(json.loads((HERE / 'entry-inverse-v3.json').read_bytes())['replacements']):"
new = "        for row in reversed(json.loads((HERE / 'exact-inverses-v4.json').read_bytes())['files']['linux_observation_envelope_v4.py']['replacements']):\n" + \
    "            self.assertEqual(text.count(row['new']), row['count']); text = text.replace(row['new'], row['old'])\n" + \
    "        for row in reversed(json.loads((HERE.parent / 'normalized-unit-envelope-v3/entry-inverse-v3.json').read_bytes())['replacements']):"
assert source.count(old) == 1
source = source.replace(old, new)
(HERE / 'test_envelope_v4.py').write_text(source)

source = (OLD / 'test_root_environment_v3.py').read_text()
source = source.replace("'test_envelope_v3.py'", "'test_envelope_v4.py'").replace("'command-v3.json'", "'command-v4.json'")
source = source.replace('linux_observation_envelope_v3.py', 'linux_observation_envelope_v4.py')
source = replace_function(source, 'test_namespace_inverse_and_all_functions_exact', '''def test_namespace_inventory_inverse_and_stable_functions_exact(self):
        selected = HERE / 'linux_observation_envelope_v4.py'
        new = selected.read_text()
        inverse = json.loads((HERE / 'exact-inverses-v4.json').read_bytes())['files']['linux_observation_envelope_v4.py']
        for row in reversed(inverse['replacements']):
            self.assertEqual(new.count(row['new']), row['count']); new = new.replace(row['new'], row['old'])
        before = HERE.parent / 'normalized-unit-envelope-v3/linux_observation_envelope_v3.py'
        self.assertEqual(new, before.read_text())
        for name in ('bind_environment', 'publish_final_result', 'read', 'runtime_helpers', 'check_outputs'):
            def function(path):
                return ast.dump(next(n for n in ast.parse(path.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == name))
            self.assertEqual(function(selected), function(before))''')
source = replace_function(source, 'test_root_command_and_unchanged_science_closure', '''def test_root_command_and_explicit_observer_successor_closure(self):
        self.assertEqual(COMMAND['root_launcher']['sha256'], hashlib.sha256(LOADER.read_bytes()).hexdigest())
        self.assertEqual(COMMAND['root_launch_requirements']['run_environment_unset'], ['LIBRARY_PATH', 'LD_LIBRARY_PATH'])
        self.assertEqual(COMMAND['root_created_directories'], [COMMAND['raw'] + '/control'])
        self.assertLessEqual(COMMAND['root_controls_bytes_including_policy'], 1048576)
        old = json.loads((WHOLE / 'normalized-unit-envelope-v3/command-v3.json').read_bytes())
        replaced = {'linux_observation_envelope_v3.py', 'observe_entry_v1.py',
            'fixed-modules-v1.json', 'normalized_compiler_adapter_v1.py'}
        added = {'linux_observation_envelope_v4.py', 'observe_entry_v2.py',
            'fixed-modules-v2.json', 'normalized_compiler_adapter_v2.py',
            'abi_role_transport_v1.py', 'strict_minify_v2.py'}
        self.assertEqual(set(COMMAND['stage_sources']), (set(old['stage_sources']) - replaced) | added)
        changed = replaced | {'observation-policy-v1.json', 'normalized_capture_ingress_v2.py'}
        observer_files = {row['file'] for row in json.loads((HERE / 'observer/fixed-modules-v2.json').read_bytes())['modules']}
        for name, row in old['stage_sources'].items():
            if name in changed: continue
            self.assertEqual({k: v for k, v in COMMAND['stage_sources'][name].items() if k != 'path'},
                             {k: v for k, v in row.items() if k != 'path'})
            if name not in observer_files | {'selected-zlib-runtime.json'}:
                self.assertEqual(COMMAND['stage_sources'][name]['path'], row['path'])
        self.assertEqual(COMMAND['guard'], old['guard'])''')
(HERE / 'test_root_environment_v4.py').write_text(source)
