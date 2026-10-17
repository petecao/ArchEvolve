"""2026-10-16 ET. Actual schema/selected metadata controls; no reader run."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
INIT = HERE.parent
V3 = INIT / 'cold-v3-admission-04af74c1'
BEFORE = (V3 / 'initialized_cold_audit_v3.py').read_text()
AFTER = (HERE / 'initialized_cold_audit_v4.py').read_text()
assert hashlib.sha256(BEFORE.encode()).hexdigest() == '620e922c24f45c82ce7e7d1888a6acbe6091991702796c71f32dc8d9c86c1e44'
OBSERVED = json.loads((HERE / 'retained-runtime-schema-20261016.json').read_bytes())
EXPECTED = json.loads((INIT / 'linux_pair_policy_04af74c1_v5.json').read_bytes())


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {
            'os.system', 'os.fork', 'os.forkpty'}:
        raise RuntimeError('pure schema controls refuse ' + event)


sys.addaudithook(deny)


def source_function(name):
    node = next(node for node in ast.parse(AFTER).body if isinstance(node, ast.FunctionDef) and node.name == name)
    result = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-V4-descriptor-validator>', 'exec'), result)
    return result[name]


def context_projection(name):
    """Actual observed keys/consumed values, explicitly not the full retained JSON.

    Unconsumed string/list fields have inert placeholders; no scientific source
    or record bytes are fetched, parsed or accepted by these controls.
    """
    observed = OBSERVED['files'][name]
    row = {key: '<unconsumed metadata>' for key in observed['schema']}
    row['runtime'] = {key: '<unconsumed component>' for key in observed['schema']['runtime']}
    for key in row['runtime']:
        if 'runtime.' + key in observed['selected_scalars']:
            row['runtime'][key] = observed['selected_scalars']['runtime.' + key]
    row['lowering_identity'] = {name: observed['selected_scalars']['lowering_identity.' + name]
                                for name in ('c_lowering', 'clang', 'naming_rules')}
    if name == 'runtime-provenance.json': row['tool'] = observed['selected_tool_descriptor']
    else: row['accepted_linux_components'] = observed['selected_accepted_linux_components']
    return copy.deepcopy(row)


class DescriptorTests(unittest.TestCase):
    def test_old_exact_predicate_red_on_both_actual_schemas_new_green(self):
        contexts = next(node for node in ast.parse(BEFORE).body if isinstance(node, ast.FunctionDef) and node.name == 'project_contexts')
        old = next(node for node in ast.walk(contexts) if isinstance(node, ast.Assert) and
                   ast.get_source_segment(BEFORE, node) == "assert runtime['version'] == '22.1.8'")
        function = source_function('validate_compiler_descriptor_v4')
        for name in OBSERVED['files']:
            row = context_projection(name)
            with self.subTest(name=name):
                self.assertNotIn('version', row['runtime'])
                with self.assertRaises(KeyError):
                    exec(compile(ast.Module(body=[old], type_ignores=[]), '<exact-V3-failed-predicate>', 'exec'), {'runtime': row['runtime']})
                components = function(name, row, EXPECTED)
                self.assertEqual(components['command'], ['clang++'] if name == 'runtime-provenance.json' else
                                 EXPECTED['linux_clang_components']['command'])
                self.assertEqual(components['command_executable'], EXPECTED['linux_clang_components']['command_executable'])

    def test_wrong_version_wrapper_tool_selector_and_missing_flag_refused(self):
        function = source_function('validate_compiler_descriptor_v4')
        name = 'runtime-provenance.json'
        for key, value in (('version', '22.1.9'), ('command', ['other-clang++']), ('missing', 'compiler unavailable')):
            row = context_projection(name); row['tool'][key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError): function(name, row, EXPECTED)
        for name in OBSERVED['files']:
            for key, value in (('id', 'clang-22.1.7'), ('sha256', '0' * 64)):
                row = context_projection(name); row['lowering_identity']['clang'][key] = value
                with self.subTest(name=name, key=key), self.assertRaises(AssertionError): function(name, row, EXPECTED)
            for key in ('command_executable', 'driver', 'parser', 'headers'):
                row = context_projection(name); row['runtime'][key]['sha256'] = '0' * 64
                with self.subTest(name=name, component=key), self.assertRaises(AssertionError): function(name, row, EXPECTED)
            row = context_projection(name)
            row['runtime']['command'] = EXPECTED['linux_clang_components']['command'] if name == 'runtime-provenance.json' else ['clang++']
            with self.subTest(name=name, command='wrong_role_selector'), self.assertRaises(AssertionError): function(name, row, EXPECTED)

    def test_project_component_drift_unknown_context_and_extra_version_refused(self):
        function = source_function('validate_compiler_descriptor_v4')
        name = 'initialized-project-runtime-provenance.json'
        row = context_projection(name); row['accepted_linux_components']['parser']['sha256'] = '0' * 64
        with self.assertRaises(AssertionError): function(name, row, EXPECTED)
        row = context_projection(name)
        with self.assertRaises(AssertionError): function('another-context.json', row, EXPECTED)
        for name in OBSERVED['files']:
            row = context_projection(name); row['runtime']['version'] = '22.1.8'
            with self.subTest(name=name), self.assertRaises(AssertionError): function(name, row, EXPECTED)

    def test_complete_ast_inverse_and_scientific_bytes_unchanged(self):
        old, new = ast.parse(BEFORE), ast.parse(AFTER)
        new.body[0] = old.body[0]
        new.body = [node for node in new.body if not isinstance(node, ast.FunctionDef) or node.name != 'validate_compiler_descriptor_v4']
        before = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == 'project_contexts')
        after = next(node for node in new.body if isinstance(node, ast.FunctionDef) and node.name == 'project_contexts')
        index = next(index for index, node in enumerate(before.body[1].body) if isinstance(node, ast.Assert) and
                     ast.get_source_segment(BEFORE, node) == "assert runtime['version'] == '22.1.8'")
        after.body[1].body[index] = before.body[1].body[index]
        index = next(index for index, node in enumerate(before.body[1].body) if isinstance(node, ast.Assert) and
                     ast.get_source_segment(BEFORE, node).startswith('assert all(runtime[key]'))
        after.body[1].body[index] = before.body[1].body[index]
        self.assertEqual(ast.dump(old, include_attributes=False), ast.dump(new, include_attributes=False))
        for name in ('audit_record', 'initialized_rules', 'semantic_model', 'workflow', 'audit',
                     'validate_original_lane_v3', 'original_launch', 'complete_source', 'runtime_closure'):
            a = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == name)
            b = next(node for node in new.body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(ast.get_source_segment(BEFORE, a), ast.get_source_segment(AFTER, b))

    def test_schema_observation_pins_match_original_immutable_manifest(self):
        policy = json.loads((V3 / 'initialized-cold-policy-04af74c1-v3.json').read_bytes())
        for name, observation in OBSERVED['files'].items():
            self.assertEqual(observation['pin']['path'], policy['raw'] + '/' + name)
            self.assertEqual({key: observation['pin'][key] for key in ('bytes', 'sha256')}, policy['raw_manifest']['files'][name])
        stdout = json.loads((V3 / 'initialized-cold-v3-actual-stdout-20261016.json').read_bytes())
        self.assertEqual(stdout['classification'], 'REFUSED')
        self.assertEqual(stdout['error_type'], 'KeyError')
        self.assertEqual(stdout['failure'], "'version'")

    def test_policy_inverse_is_only_namespace_reader_pins_and_provenance(self):
        old = json.loads((V3 / 'initialized-cold-policy-04af74c1-v3.json').read_bytes())
        new = json.loads((HERE / 'initialized-cold-policy-04af74c1-v4.json').read_bytes())
        def undo(value):
            if isinstance(value, dict): return {key: undo(item) for key, item in value.items()}
            if isinstance(value, list): return [undo(item) for item in value]
            if isinstance(value, str): return value.replace('initialized-cold-04af74c1-v4', 'initialized-cold-04af74c1-v3')
            return value
        new = undo(new)
        for key in ('reader_base_v3', 'retained_runtime_schema', 'preserved_actual_v3_refusal'): new['provenance'].pop(key)
        new['reader_sha256'] = old['reader_sha256']
        self.assertEqual(new, old)
        command = json.loads((HERE / 'initialized-cold-command-04af74c1-v4.json').read_bytes())
        self.assertEqual(len(command['control_files']), 10)
        self.assertLess(command['control_total_bytes'], 1048576)
        self.assertEqual(command['command'][-3].split('/')[-1], 'initialized_cold_audit_v4.py')
        self.assertEqual(command['command'][-1], hashlib.sha256((HERE / 'initialized-cold-policy-04af74c1-v4.json').read_bytes()).hexdigest())


if __name__ == '__main__': unittest.main(verbosity=2)
