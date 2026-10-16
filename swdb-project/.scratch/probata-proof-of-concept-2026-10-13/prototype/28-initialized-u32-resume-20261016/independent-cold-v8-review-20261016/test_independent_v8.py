"""2026-10-16 ET. Independent V8 source/inverse and inert metadata controls."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
INIT = HERE.parent
V7 = INIT / 'cold-v7-admission-04af74c1'
V8 = INIT / 'cold-v8-admission-04af74c1'
H = lambda value: hashlib.sha256(value).hexdigest()
OLD = (INIT / 'initialized_cold_obligations_v2.py').read_text()
NEW = (V8 / 'initialized_cold_obligations_v3.py').read_text()


def deny(event, _args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event == 'os.system':
        raise RuntimeError('independent source controls refuse ' + event)


sys.addaudithook(deny)
NS = {'__name__': 'independent_inert_v8_obligations'}
exec(compile(NEW, '<independent-pinned-v8-obligations-only>', 'exec'), NS)
META = json.loads((V7 / 'retained-arity0-property-metadata-20261016.json').read_bytes())


def fn(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def rebind(value):
    if isinstance(value, dict): return {key: rebind(item) for key, item in value.items()}
    if isinstance(value, list): return [rebind(item) for item in value]
    if isinstance(value, str): return value.replace('initialized-cold-04af74c1-v8', 'initialized-cold-04af74c1-v7')
    return value


class IndependentControls(unittest.TestCase):
    def test_full_obligations_ast_and_reader_byte_inverses(self):
        a, b = ast.parse(OLD), ast.parse(NEW)
        b.body.remove(fn(b, 'unused_arity0_v3')); b.body.remove(fn(b, 'current_csv'))
        fn(b, 'current_csv_active_v2').name = 'current_csv'
        oldgoal, newgoal = fn(a, 'current_goals'), fn(b, 'current_goals')
        newgoal.args = oldgoal.args
        newgoal.body = [node for node in newgoal.body if not (isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == 'unused' for target in node.targets))]
        for index, node in enumerate(newgoal.body):
            if isinstance(node, ast.Assert) and 'for p in extern' in ast.unparse(node):
                newgoal.body[index] = next(value for value in oldgoal.body if isinstance(value, ast.Assert) and 'for p in extern' in ast.unparse(value))
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and getattr(node.value.func, 'id', None) == 'current_csv':
                newgoal.body[index] = next(value for value in oldgoal.body if isinstance(value, ast.Assign) and isinstance(value.value, ast.Call) and getattr(value.value.func, 'id', None) == 'current_csv')
        source = fn(b, 'initialized_wp_source')
        source.body = [node for node in source.body if not (isinstance(node, ast.Assert) and 'get_new_reg_unsigned_int_args0' in ast.unparse(node))]
        result = source.body[-1].value
        keep = [(key, value) for key, value in zip(result.keys, result.values) if ast.literal_eval(key) != 'unused_arity0_declaration_only']
        result.keys = [key for key, _value in keep]; result.values = [value for _key, value in keep]
        self.assertEqual(ast.dump(a), ast.dump(b))
        before = (V7 / 'initialized_cold_audit_v7.py').read_text()
        after = (V8 / 'initialized_cold_audit_v8.py').read_text()
        after = after.replace('initialized_cold_audit_v8.py', 'initialized_cold_audit_v7.py')
        after = after.replace('initialized_cold_obligations_v3.py', 'initialized_cold_obligations_v2.py')
        after = after.replace('817c4041cae251e8c2002f7ea9858bc85e5d6f0adc37d174390367c3261b138f', 'dfc647552f4a1bbfd33cc4745289257a9aca4e8b587ce45ca9aa757066950dc9')
        after = after.replace('csvrows, scratch, validated_query=query)', 'csvrows, scratch)')
        self.assertEqual(after, before)

    def test_complete_policy_and_command_json_inverses(self):
        old = json.loads((V7 / 'initialized-cold-policy-04af74c1-v7.json').read_bytes())
        new = rebind(json.loads((V8 / 'initialized-cold-policy-04af74c1-v8.json').read_bytes()))
        new['reader_sha256'] = old['reader_sha256']
        new['reader_files'].pop('initialized_cold_obligations_v3.py')
        new['reader_files']['initialized_cold_obligations_v2.py'] = old['reader_files']['initialized_cold_obligations_v2.py']
        for key in ('unused_arity0_metadata', 'unused_arity0_primary', 'preserved_actual_v7_refusal'):
            new['provenance'].pop(key)
        self.assertEqual(new, old)
        old = json.loads((V7 / 'initialized-cold-command-04af74c1-v7.json').read_bytes())
        new = rebind(json.loads((V8 / 'initialized-cold-command-04af74c1-v8.json').read_bytes()))
        for name in ('initialized_cold_audit_v8.py', 'initialized_cold_obligations_v3.py', 'initialized-cold-policy-04af74c1-v8.json'):
            new['control_files'].pop(name)
        for name in ('initialized_cold_audit_v7.py', 'initialized_cold_obligations_v2.py', 'initialized-cold-policy-04af74c1-v7.json'):
            new['control_files'][name] = old['control_files'][name]
        new['command'][-3:] = old['command'][-3:]; new['control_total_bytes'] = old['control_total_bytes']
        self.assertEqual(new, old)

    def test_unused_rows_cannot_hide_active_origins_dependencies_or_goals(self):
        count = 0
        for row in META['records']:
            reference = INIT / ('cold-reference-wp-correct.c' if row['expected_result'] == 711 else 'cold-reference-wp-wrong.c')
            query = NS['initialized_wp_source'](reference.read_text(), row['expected_result'], INIT)
            props = {value['property']: copy.deepcopy(value) for value in row['unused_arity0_all_properties']}
            path = Path(next(iter(props.values()))['source_file'])
            ids = list(props)
            for target in ids:
                for mutation in ('origin', 'dependency', 'goal_property', 'goal_target', 'goal_function'):
                    changed = copy.deepcopy(props); generated = {}
                    if mutation in ('origin', 'dependency'):
                        changed['active'] = {'function': 'trust_fixture', 'origin': target if mutation == 'origin' else None,
                            'dependencies': [target] if mutation == 'dependency' else []}
                    else:
                        generated['active'] = {'function': 'get_new_reg_unsigned_int_args0' if mutation == 'goal_function' else 'trust_fixture',
                            'property': target if mutation == 'goal_property' else 'active', 'targets': [target] if mutation == 'goal_target' else []}
                    with self.subTest(result=row['expected_result'], target=target, mutation=mutation), self.assertRaises(AssertionError):
                        NS['unused_arity0_v3'](row['unused_arity0_CSV'], changed, generated, query, path)
                    count += 1
            self.assertEqual(row['unused_arity0_attached_goals'], [])
        self.assertEqual(count, 30)

    def test_material_shape_status_and_complete_query_changes_still_refuse(self):
        row = META['records'][0]
        reference = INIT / 'cold-reference-wp-correct.c'
        query = NS['initialized_wp_source'](reference.read_text(), 711, INIT)
        props = {value['property']: copy.deepcopy(value) for value in row['unused_arity0_all_properties']}
        path = Path(next(iter(props.values()))['source_file'])
        for key, value in (('line', 18), ('source_file', '/unrelated/wp_input.c'), ('emitter', 'other'),
                           ('generated_smoke_failure', True), ('new_payload', 'must-refuse')):
            changed = copy.deepcopy(props); changed['get_new_reg_unsigned_int_args0_assigns'][key] = value
            with self.assertRaises(AssertionError):
                NS['unused_arity0_v3'](row['unused_arity0_CSV'], changed, {}, query, path)
        for status in ('Valid', 'Unknown', 'Invalid'):
            changed = copy.deepcopy(row['unused_arity0_CSV']); changed[0]['status'] = status
            with self.assertRaises(AssertionError): NS['unused_arity0_v3'](changed, props, {}, query, path)
        for text in (reference.read_text().replace('get_new_reg_unsigned_int_args0(void);', 'get_new_reg_unsigned_int_args0(void) { return 0; }'),
                     reference.read_text().replace('get_new_reg_unsigned_int_args1(21)', 'get_new_reg_unsigned_int_args1(22)')):
            if text != reference.read_text():
                with self.assertRaises(AssertionError): NS['initialized_wp_source'](text, 711, INIT)


if __name__ == '__main__': unittest.main(verbosity=2)
