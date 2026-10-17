"""2026-10-16 ET. Child-free controls for the inert passive reader only."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
ATTEMPTS = []


def no_children(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen'} or event.startswith('socket.'):
        ATTEMPTS.append(event)
        raise RuntimeError('child/native/network forbidden in pure controls')


sys.addaudithook(no_children)
semantic = types.ModuleType('pure_ownership_terms')
exec(compile((HERE / 'semantic_terms.py').read_text(), '<pure-term-controls>', 'exec'), semantic.__dict__)
observer = types.ModuleType('pure_observer')
observer.__dict__['__name__'] = 'pure_observer'
exec(compile((HERE / 'observer.py').read_text(), '<unexecuted-observer-definitions>', 'exec'), observer.__dict__)


class Controls(unittest.TestCase):
    def test_all_ten_independent_goal_transcriptions_parse(self):
        self.assertEqual(len(semantic.GOALS), 10)
        for ident in semantic.GOALS:
            term = semantic.source_goal(ident)
            self.assertEqual(term[0], 'not')
            self.assertEqual(term[1][0], 'forall')
            semantic.canon(term)

    def test_all_nine_source_definition_transcriptions_parse(self):
        self.assertEqual(len(semantic.DEFINITIONS), 9)
        for name in semantic.DEFINITIONS:
            semantic.canon(semantic.definition_expected(name))

    def test_smt_token_coverage_and_query_shape(self):
        for bad in ('(assert true', '(assert "unterminated)', '(assert |unterminated)', '(assert true))'):
            with self.assertRaises(ValueError):
                semantic.forms(bad)
        for query in ('(check-sat)(check-sat)', '(check-sat)(assert false)', '(push 1)(assert false)(check-sat)'):
            with self.assertRaises(ValueError):
                semantic.task_semantics(query, 'swap.self', {})

    def test_goal_not_replaced_by_desired_or_sibling_premise(self):
        for bad in ('(assert check_lemma_t25_owned_swap_self)', '(assert (wp_goal true))'):
            with self.assertRaises(ValueError):
                semantic.task_semantics(bad + '(assert (not true))(check-sat)', 'swap.self', {})

    def test_unknown_support_is_pending_not_standard(self):
        result = semantic.task_semantics('(assert false)(assert (not true))(check-sat)', 'swap.self', {})
        self.assertFalse(result['complete_semantic_match'])
        self.assertIn('support_assertion', [r['kind'] for r in result['unresolved']])

    def test_unknown_record_encoding_is_pending(self):
        result = semantic.task_semantics('(declare-datatype state ((mk_state (active (Array Int Bool)) (backing (Array Int Int))))) (assert (not true))(check-sat)', 'swap.self', {})
        self.assertIn('encoding_declaration', [r['kind'] for r in result['unresolved']])
        self.assertFalse(result['complete_semantic_match'])

    def test_antecedent_mutation_is_not_alpha_normalization(self):
        term = semantic.source_goal('move.transfer')
        changed = json.loads(json.dumps(term))
        changed[1][2][1].pop(4)
        self.assertNotEqual(semantic.canon(term), semantic.canon(changed))

    def test_move_store_order_is_material(self):
        term = semantic.definition_expected('move')
        changed = json.loads(json.dumps(term))
        stores = changed[2][2]
        stores[2] = 'destination'
        self.assertNotEqual(semantic.canon(term), semantic.canon(changed))

    def test_alpha_and_conjunction_order_are_the_only_permitted_changes(self):
        a = semantic.one('(forall ((r Int) (q Int)) (and (= r q) (< r 4)))')
        b = semantic.one('(forall ((x Int) (y Int)) (and (< x 4) (= y x)))')
        self.assertEqual(semantic.canon(a), semantic.canon(b))
        c = semantic.one('(exists ((x Int) (y Int)) (and (< x 4) (= y x)))')
        self.assertNotEqual(semantic.canon(a), semantic.canon(c))

    def test_let_bindings_are_simultaneous(self):
        actual = semantic.one('(let ((x y) (y x)) (= x y))')
        expected = semantic.one('(= y x)')
        self.assertEqual(semantic.canon(actual), semantic.canon(expected))

    def test_raw_symlink_special_and_outside_membership_refuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / 'file').write_bytes(b'x')
            self.assertEqual(len(observer.walk(root)), 1)
            (root / 'alias').symlink_to(root / 'file')
            with self.assertRaises(ValueError):
                observer.walk(root)
            with self.assertRaises(ValueError):
                observer.read_bytes(root / 'alias')

    def test_input_and_aggregate_bounds_refuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / 'file').write_bytes(b'12345')
            with self.assertRaises(ValueError):
                observer.read_bytes(root / 'file', 4)
            with self.assertRaises(ValueError):
                observer.walk(root, byte_cap=4)
            with self.assertRaises(ValueError):
                observer.walk(root, entry_cap=0)

    def test_duplicate_or_nonfinite_metadata_refuses(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / 'a.json'
            for payload in ('{"a":1,"a":2}', '{"a":NaN}'):
                path.write_text(payload)
                with self.assertRaises(ValueError):
                    observer.read(path)

    def test_read_only_git_disables_repository_fsmonitor_helpers(self):
        tree = ast.parse((HERE / 'observer.py').read_bytes())
        git = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'git')
        text = ast.get_source_segment((HERE / 'observer.py').read_text(), git)
        self.assertIn("'core.fsmonitor=false'", text)
        self.assertIn("'core.preloadIndex=false'", text)
        self.assertIn("'index.threads=1'", text)

    def test_actual_command_file_and_resolved_argv_domains_remain_separate(self):
        file = HERE.parent / 'public10-v2/inert-d7f685c6-public10-v2/root-command.json'
        raw = file.read_bytes()
        frozen = json.loads(raw)
        resolved = [value.replace('{SOURCE}', str(observer.SOURCE)).replace('{OUTPUT}', str(observer.RAW)) for value in frozen]
        context = {'frozen_root_command': frozen, 'frozen_root_command_file_sha256': hashlib.sha256(raw).hexdigest(),
                   'resolved_root_command_sha256': observer.digest(resolved)}
        self.assertEqual(observer.resolved_command(context), resolved)
        self.assertNotEqual(observer.digest(frozen), context['frozen_root_command_file_sha256'])
        self.assertNotEqual(observer.digest(resolved), context['frozen_root_command_file_sha256'])
        self.assertEqual(observer.digest(resolved), '38f8de3d374aae446abbf1e9f7e8d3fa23817d0074bc8320b1518659288480a4')
        for key in ('frozen_root_command_file_sha256', 'resolved_root_command_sha256'):
            bad = dict(context); bad[key] = '0' * 64
            with self.assertRaises(ValueError):
                observer.resolved_command(bad)
        bad = json.loads(json.dumps(context)); bad['frozen_root_command'][7] = str(observer.SOURCE) + '/swdb-project'
        with self.assertRaises(ValueError):
            observer.resolved_command(bad)
        actual = {'command': resolved}
        self.assertEqual(actual['command'], observer.resolved_command(context))
        actual['command'] = [*resolved[:-1], str(observer.RAW) + '-different']
        self.assertNotEqual(actual['command'], observer.resolved_command(context))

    def test_full_actual_shaped_guard_consumes_exact_resolved_argv(self):
        frozen_dir = HERE.parent / 'public10-v2/inert-d7f685c6-public10-v2'
        command_file = (frozen_dir / 'root-command.json').read_bytes()
        frozen = json.loads(command_file)
        expected = json.loads((frozen_dir / 'expected.json').read_bytes())
        resolved = [s.replace('{SOURCE}', str(observer.SOURCE)).replace('{OUTPUT}', str(observer.RAW)) for s in frozen]
        context = {'frozen_root_command': frozen, 'frozen_root_command_file_sha256': hashlib.sha256(command_file).hexdigest(),
                   'resolved_root_command_sha256': observer.digest(resolved), 'known_metadata_pins': {}}
        lane = {'node': 0, 'lease_generation': 621, 'exit_code': 0, 'numa_memory_policy': 'bind:0',
                'started_utc': '2026-10-16T21:51:35Z', 'ended_utc': '2026-10-16T21:52:07Z'}
        resource = {'exit_code': 0, 'out_of_memory': False, 'timed_out': False,
                    'peak_rss_bytes': 291246080, 'wall_seconds': 29.589660208672285}
        wrappers = expected['linux_launch_binding']['wrappers']
        launch = {'command': resolved, 'source_commit': observer.COMMIT, 'source': str(observer.SOURCE),
                  'timeout_seconds': 2100, 'rss_cap_bytes': 8589934592, 'workers': 1,
                  'reviewed_wrapper_reuse': wrappers}
        metadata = {'launch.json': launch, 'lane.json': {'socket_lane': lane},
                    'resources.json': resource, 'outer-resources.json': resource,
                    'source-after.json': {'commit': observer.COMMIT, 'source_unchanged': True, 'tracked_changes': ''},
                    'dispatch-environment.json': {}}
        original_read, original_pin = observer.read, observer.pin
        try:
            observer.read = lambda path: metadata[str(path.relative_to(observer.RAW))]
            observer.pin = lambda path: {'sha256': wrappers[path.name]}
            self.assertEqual(observer.guards(expected, context)['lane'], lane)
            launch['command'] = frozen
            with self.assertRaises(ValueError):
                observer.guards(expected, context)
            launch['command'] = [*resolved[:-1], str(observer.RAW) + '-wrong']
            with self.assertRaises(ValueError):
                observer.guards(expected, context)
        finally:
            observer.read, observer.pin = original_read, original_pin

    def test_observer_has_no_project_import_or_tool_version_probe(self):
        tree = ast.parse((HERE / 'observer.py').read_bytes())
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any(getattr(n, 'module', '').startswith('swdb') for n in imports if isinstance(n, ast.ImportFrom)))
        self.assertNotIn('--version', (HERE / 'observer.py').read_text())
        self.assertNotIn('ctypes.CDLL', (HERE / 'observer.py').read_text())
        self.assertEqual(ATTEMPTS, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
