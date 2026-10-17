"""2026-10-16 ET. Synthetic complete-command metadata controls; no child calls."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ATTEMPTS = []


def block(event, args):
    if event in {'subprocess.Popen', 'ctypes.dlopen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork'} or event.startswith('socket.'):
        ATTEMPTS.append(event)
        raise RuntimeError('pure controls forbid '+event)


sys.addaudithook(block)
ns = {'__name__': '_pure_control'}
for name in ('syntax.py', 'observer.py'):
    exec(compile((HERE/name).read_bytes(), str(HERE/name), 'exec'), ns)
TEXT = '''(set-logic ALL)
(set-info :source "OPAQUE_METADATA_NEVER_EXPORTED")
(set-option :random-seed 9)
(declare-sort S 0)
(declare-fun f (Int) Int)
(declare-const c Int)
(declare-datatype D ((mkD (field Int))))
(declare-datatypes ((E 0)) (((mkE (flag Bool)))))
(define-fun id ((x Int)) Int x)
(assert (= (id 0) 0))
(assert (not (= (f c) c)))
(check-sat)
(get-info :reason-unknown)
'''


def row(text=TEXT, ident='synthetic'):
    commands = ns['forms'](text)
    return {'id': ident, 'artifact': {'relative': ident+'.psmt2', 'bytes': len(text.encode()),
            'sha256': hashlib.sha256(text.encode()).hexdigest()},
            'complete_command_census': [{'index': i, 'kind': c[0], 'sha256': ns['digest'](c)}
                                      for i, c in enumerate(commands)]}


class Controls(unittest.TestCase):
    def test_all_heads_and_every_ordered_reference_retained(self):
        trees = {}; output = ns['capture_task'](TEXT, row(), trees)
        self.assertEqual([r['kind'] for r in output['commands']],
            ['set-logic', 'set-info', 'set-option', 'declare-sort', 'declare-fun', 'declare-const',
             'declare-datatype', 'declare-datatypes', 'define-fun', 'assert', 'assert', 'check-sat', 'get-info'])
        self.assertEqual([r['index'] for r in output['commands']], list(range(13)))
        self.assertEqual(set(c[0] for c in trees.values()), ns['MATH'])
        self.assertEqual(len(trees), 8)
        self.assertEqual(output['goal_command_index'], 10)
        self.assertEqual(output['support_assertions'], 1)
        for ref in output['commands']:
            self.assertEqual(ref['tree_ref'], ref['sha256'] if ref['kind'] in ns['MATH'] else None)
        definition = next(value for value in trees.values() if value[0] == 'define-fun')
        self.assertEqual(definition, ['define-fun', 'id', [['x', 'Int']], 'Int', 'x'])

    def test_complete26_dedup_preserves_all_tasks_and_commands(self):
        trees = {}; tasks = [ns['capture_task'](TEXT, row(ident='task'+str(i)), trees) for i in range(26)]
        self.assertEqual(len(trees), 8)
        self.assertEqual(len(tasks), 26)
        self.assertEqual(sum(len(task['commands']) for task in tasks), 338)
        self.assertTrue(all(sum(ref['role'] == 'goal' for ref in task['commands']) == 1 for task in tasks))
        self.assertTrue(all(task['semantic_equivalence_or_support_admission'] is False for task in tasks))

    def test_shared_assertion_retains_distinct_goal_and_support_roles(self):
        trees = {}; first = ns['capture_task'](TEXT, row(), trees)
        changed = TEXT.replace('(assert (= (id 0) 0))\n(assert (not (= (f c) c)))',
                               '(assert (not (= (f c) c)))\n(assert (= (id 0) 0))')
        second = ns['capture_task'](changed, row(changed, 'other'), trees)
        self.assertEqual(len(trees), 8)
        self.assertNotEqual(first['goal_command_sha256'], second['goal_command_sha256'])
        self.assertEqual(first['commands'][9]['sha256'], second['commands'][10]['sha256'])
        self.assertEqual(first['commands'][9]['role'], 'support')
        self.assertEqual(second['commands'][10]['role'], 'goal')

    def test_changed_goal_cannot_match_old_census(self):
        with self.assertRaisesRegex(ValueError, 'prior full ordered'):
            ns['capture_task'](TEXT.replace('(f c) c', '(f c) 1'), row(), {})

    def test_missing_support_or_reordered_command_cannot_match(self):
        for changed in [TEXT.replace('(assert (= (id 0) 0))\n', ''),
                        TEXT.replace('(declare-sort S 0)\n(declare-fun f (Int) Int)',
                                     '(declare-fun f (Int) Int)\n(declare-sort S 0)')]:
            with self.assertRaisesRegex(ValueError, 'prior full ordered'):
                ns['capture_task'](changed, row(), {})

    def test_unknown_commands_refuse_even_with_consistent_census(self):
        for command in ['(push 1)', '(eval c)', '(reset)', '(exit)']:
            changed = command+'\n'+TEXT
            with self.assertRaisesRegex(ValueError, 'closed command-head'):
                ns['capture_task'](changed, row(changed), {})

    def test_query_multiplicity_and_epilogue_are_closed(self):
        for changed in [TEXT.replace('(check-sat)', '(check-sat)\n(check-sat)'),
                        TEXT.replace('(check-sat)', ''),
                        TEXT.replace('(check-sat)', '(check-sat)\n(assert false)'),
                        TEXT.replace(':reason-unknown)', ':all-statistics)'),
                        '(get-info :reason-unknown)\n'+TEXT]:
            with self.assertRaisesRegex(ValueError, 'closed query'):
                ns['capture_task'](changed, row(changed), {})

    def test_missing_goal_and_bad_command_shapes_refuse(self):
        changes = [TEXT.replace('(assert (= (id 0) 0))\n', '').replace('(assert (not (= (f c) c)))\n', ''),
                   TEXT.replace('(define-fun id ((x Int)) Int x)', '(define-fun id ((x Int)) Int)'),
                   TEXT.replace('(assert (= (id 0) 0))', '(assert true false)'),
                   TEXT.replace('(declare-fun f (Int) Int)', '(declare-fun f Int Int)')]
        for changed in changes:
            with self.assertRaises(ValueError):
                ns['capture_task'](changed, row(changed), {})

    def test_opaque_payloads_are_not_exported(self):
        trees = {}; result = ns['capture_task'](TEXT, row(), trees)
        output = json.dumps({'tasks': [result], 'trees': trees})
        self.assertNotIn('OPAQUE_METADATA_NEVER_EXPORTED', output)
        self.assertNotIn('random-seed', output)
        self.assertNotIn('reason-unknown', output)
        self.assertEqual(result['commands'][1]['tree_ref'], None)
        self.assertEqual(result['commands'][1]['kind'], 'set-info')

    def test_full_math_syntax_is_preserved_without_normalization(self):
        left = TEXT.replace('(not (= (f c) c))', '(not (= (+ 1 c) (+ c 1)))')
        trees = {}; result = ns['capture_task'](left, row(left), trees)
        self.assertEqual(trees[result['goal_command_sha256']],
            ['assert', ['not', ['=', ['+', '1', 'c'], ['+', 'c', '1']]]])

    def test_atom_byte_bounds_cover_opaque_and_math_atoms(self):
        for changed in [TEXT.replace('OPAQUE_METADATA_NEVER_EXPORTED', 'x'*2049),
                        TEXT.replace('(declare-sort S 0)', '(declare-sort '+'x'*2049+' 0)'),
                        TEXT.replace('OPAQUE_METADATA_NEVER_EXPORTED', '界'*700)]:
            with self.assertRaisesRegex(ValueError, 'atom byte cap'):
                ns['capture_task'](changed, row(changed), {})
        ns['atom_bounds']([['assert', 'x'*2048]])

    def test_depth_file_and_complete_token_coverage_caps(self):
        for text in ['('*161+'x'+')'*161, ' '*1048577, '(assert |unterminated)', '(assert true']:
            with self.assertRaises(ValueError):
                ns['forms'](text)

    def test_digest_collision_refuses_instead_of_dedup_overwrite(self):
        trees = {}; result = ns['capture_task'](TEXT, row(), trees)
        key = result['goal_command_sha256']; trees[key] = ['assert', 'false']
        with self.assertRaisesRegex(ValueError, 'digest collision'):
            ns['capture_task'](TEXT, row(), trees)

    def test_publication_is_complete_and_bounded(self):
        value = {'result': 'whole'}
        payload = ns['publication'](value)
        self.assertEqual(json.loads(payload), value)
        self.assertTrue(payload.endswith(b'\n'))
        with self.assertRaisesRegex(ValueError, 'output cap'):
            ns['publication']({'value': 'x'*(2*1024*1024)})

    def test_read_only_audit_rejects_mutating_flags_and_other_paths(self):
        ns['ALLOWED'] = frozenset({'/synthetic/selected'})
        ns['audit']('open', ('/synthetic/selected', None, ns['os'].O_NOFOLLOW | ns['os'].O_NONBLOCK))
        for args in [('/synthetic/selected', 'w', 0), ('/synthetic/selected', None, ns['os'].O_CREAT),
                     ('/synthetic/selected', None, ns['os'].O_TRUNC), ('/synthetic/other', None, 0), (3, None, 0)]:
            with self.assertRaises(ValueError):
                ns['audit']('open', args)
        for event in ['os.rename', 'subprocess.Popen', 'socket.connect', 'ctypes.dlopen', 'resource.setrlimit']:
            with self.assertRaises(RuntimeError):
                ns['audit'](event, ())

    def test_physical_read_and_nine_stat_repeat_with_local_synthetic_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()/'input.psmt2'; path.write_text('(assert true)')
            raw = path.read_bytes(); wanted = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            ns['ALLOWED'] = frozenset({str(path)}); ns['FILES'] = {}; ns['PARENTS'] = {}
            self.assertEqual(ns['read_input'](str(path), wanted), raw)
            self.assertEqual(ns['read_input'](str(path), wanted), raw)
            self.assertEqual(len(ns['FILES'][str(path)]), 9)
            path.write_text('(assert false)')
            changed = path.read_bytes(); fresh = {'bytes': len(changed), 'sha256': hashlib.sha256(changed).hexdigest()}
            with self.assertRaisesRegex(ValueError, 'nine-field'):
                ns['read_input'](str(path), fresh)

    def test_context_is_complete_old26_and_exact_three_theories(self):
        context = json.loads((HERE/'context.json').read_bytes())
        raw = Path(context['prior_capture']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), context['prior_capture']['sha256'])
        old = json.loads(raw)
        self.assertEqual(context['tasks'], [{'id': x['id'], 'artifact': x['artifact'],
            'complete_command_census': x['complete_command_census']} for x in old['materialized_tasks']])
        self.assertEqual(len(context['tasks']), 26)
        self.assertEqual(len({x['artifact']['relative'] for x in context['tasks']}), 26)
        self.assertEqual({x['module'] for x in context['theories']},
            {'heap_reallocation.Heap', 'vector_owned_state.Owners', 'vector_owned_effects.OwnedEffects'})
        for theory in context['theories']:
            self.assertEqual({k: theory[k] for k in ['path', 'bytes', 'sha256']}, old['import_source_closure'][theory['module']]['file'])
        self.assertEqual([x['normal_verdict'] for x in context['retained_outcomes']], ['proven']*8+['not_proven'])

    def test_only_exact_three_syntax_helpers_and_no_semantics(self):
        lineage = json.loads((HERE/'syntax-lineage.json').read_bytes())
        original = ast.parse(Path(lineage['parent_syntax_file']['path']).read_bytes())
        syntax = ast.parse((HERE/'syntax.py').read_bytes())
        functions = [n for n in syntax.body if isinstance(n, ast.FunctionDef)]
        self.assertEqual([n.name for n in functions], ['need', 'digest', 'forms'])
        for node in functions:
            before = next(n for n in original.body if isinstance(n, ast.FunctionDef) and n.name == node.name)
            self.assertEqual(ast.dump(node, include_attributes=False), ast.dump(before, include_attributes=False))
        imports = {a.name for tree in [syntax, ast.parse((HERE/'observer.py').read_bytes())]
                   for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertLessEqual(imports, {'hashlib', 'json', 're', 'os', 'resource', 'signal', 'stat', 'sys', 'time'})
        self.assertEqual(ATTEMPTS, [])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print('child_native_network_attempts='+repr(ATTEMPTS))
    raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)
