"""2026-10-16 ET. Bounded template controls; no project, Git or verifier calls."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import shutil
import signal
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
OLD = HERE.parents[2]/'prototype/25-owned-swap-header-cases-20261016/public3-v1'
CANONICAL = HERE.parent/'inert-all-types-v1'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('inert template controls refuse '+event)


def read(path):
    return json.loads(path.read_bytes())


def functions(path):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(path.read_bytes()).body if isinstance(node, ast.FunctionDef)}


class Controls(unittest.TestCase):
    def test_full_entry_and_author_inverses(self):
        inverse = read(HERE/'template-inverses-v1.json')
        for name in ('entry', 'author'):
            row = inverse[name]; raw = Path(row['output']['path']).read_text()
            for change in reversed(row['replacements']):
                self.assertEqual(raw.count(change['after']), change['count'])
                raw = raw.replace(change['after'], change['before'])
            basis = Path(row['predecessor']['path']).read_bytes()
            self.assertEqual(hashlib.sha256(basis).hexdigest(), row['predecessor']['sha256'])
            self.assertEqual(raw.encode(), basis)

    def test_all_eighteen_runtime_source_engine_and_finalizer_helpers_remain_exact(self):
        old, new = functions(OLD/'entry_template.py'), functions(HERE/'entry_template.py')
        self.assertEqual(set(old), set(new))
        changed = [name for name in old if old[name] != new[name]]
        self.assertEqual(changed, ['canonical_check', 'main'])
        self.assertEqual(len(old)-len(changed), 18)
        for name in ('linux_admission', 'consumer_closure', 'guarded_generation', 'normal_task_census',
                     'raw_bytes', 'root_sibling_census', 'why3_runtime_check', 'why3_dependency_check'):
            self.assertEqual(old[name], new[name])

    def test_no_published_source_or_actual_command_is_invented(self):
        plan = read(HERE/'pending-source-selection-v1.json')
        for field in ('source_commit', 'remote_project', 'source_package_inventory', 'source_consumer_oids',
                      'sparse_projection_files', 'sparse_projection_bytes', 'node'):
            self.assertIsNone(plan[field])
        self.assertTrue(plan['actual_expected_command_launcher_unmaterialized'])
        self.assertTrue(plan['publication_root_review_and_once_admission_required'])
        self.assertEqual(plan['canonical_files'], 48)
        self.assertEqual(plan['targets'], 3)
        self.assertFalse(any(HERE.glob('inert-*')))

    def test_missing_source_refuses_before_any_git_or_output(self):
        original = sys.argv
        try:
            for arguments in ([], ['not-a-sha'], ['a'*40, 'extra']):
                sys.argv = [str(HERE/'prepare.py'), *arguments]
                with self.assertRaisesRegex(ValueError, 'separately published'):
                    runpy.run_path(str(HERE/'prepare.py'), run_name='unpublished_author_refusal')
        finally:
            sys.argv = original
        self.assertEqual(EVENTS, [])

    def test_exact_canonical_source_and_typed_recovery_gate(self):
        source = (HERE/'entry_template.py').read_bytes()
        node = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
                    and node.name == 'canonical_check')
        namespace = {'Path': Path, 'sha': lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual-witness-canonical-admission>', 'exec'), namespace)
        original = read(CANONICAL/'manifest.json')
        rows = [{'path': str(path.relative_to(CANONICAL)), 'bytes': path.stat().st_size,
                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                for path in sorted(CANONICAL.rglob('*')) if path.is_file()]
        class PublicPacket:
            @staticmethod
            def check(directory, *, elements):
                self.assertEqual(directory, CANONICAL)
                self.assertEqual(elements, ('int', 'float', 'double', 'int *'))
                return current
        expected = {'canonical_manifest': original, 'canonical_files': rows, 'elements': original['elements'],
                    'target_ids': [row['id'] for row in original['obligations']]}
        current = original
        self.assertEqual(namespace['canonical_check'](PublicPacket, expected, CANONICAL), original)
        for field, value in (('all_three_stronger_proofs_required', False), ('reverse_implication_claimed', True),
                             ('self_swap_excluded', True), ('added_premises', ['sibling']), ('axioms_added', ['goal'])):
            current = copy.deepcopy(original); current['reconstruction'][field] = value
            # The expected-byte check is a separate earlier gate. This isolates
            # the actual additional semantic refusal even for matching metadata.
            changed = {**expected, 'canonical_manifest': current}
            with self.assertRaisesRegex(ValueError, 'stronger-witness'):
                namespace['canonical_check'](PublicPacket, changed, CANONICAL)
        for field, value in (('bound_variable_capture', True), ('full_statement_inverse_checked', False),
                             ('witness_sorts_checked_against_bound_source', False),
                             ('instance_to_existential_is_sufficient', False)):
            current = copy.deepcopy(original); current['obligations'][0]['existential_introduction'][field] = value
            with self.assertRaisesRegex(ValueError, 'existential recovery'):
                namespace['canonical_check'](PublicPacket, {**expected, 'canonical_manifest': current}, CANONICAL)

    def test_actual_witness_module_only_and_no_scientific_promotion(self):
        tree = ast.parse((HERE/'entry_template.py').read_bytes())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        text = ast.unparse(main)
        self.assertIn('vector_owned_swap_header_witness as packets', text)
        self.assertNotIn('vector_owned_swap_header_cases as packets', text)
        self.assertIn('all_three_producer_proven', text)
        for field in ('proof_acceptance', 'source_typed_bridge_established', 'caller_acceptance', 'body_acceptance',
                      'public_proof_record_created', 'universal_proof_setup_attested'):
            self.assertIn(repr(field)+': False', text)
        self.assertIn('independent_task_hypothesis_review_pending', text)
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                             and node.func.id == 'layout_checks' for node in ast.walk(main)))

    def test_normal_portfolio_caps_runtime_and_sparse_protocol_stay_unchanged(self):
        plan = read(HERE/'pending-source-selection-v1.json')
        old = read(OLD/'inert-abb598a4-public3-v1/expected.json')
        self.assertEqual(plan['resource_policy'], old['resource_policy'])
        self.assertEqual(plan['resource_policy']['cap_bytes'], 8*1024**3)
        self.assertEqual(plan['resource_policy']['root_whole_seconds'], 2800)
        self.assertEqual(plan['resource_policy']['root_outer_seconds'], 2920)
        self.assertEqual(plan['source_mount_floor_bytes'], 10*1024**3)
        self.assertEqual(plan['source_metadata_headroom_bytes'], 1024**3)
        entry = (HERE/'entry_template.py').read_text()
        self.assertIn("tools['seconds'] != 30", entry)
        self.assertIn("['alt-ergo','z3','cvc5']", entry)
        self.assertIn("('-wp-prop','-wp-fct')", entry)
        author = (HERE/'prepare.py').read_text()
        self.assertIn("old_launcher.replace(before, after, 1)", author)
        self.assertIn("launcher.replace(after, before, 1) == old_launcher", author)
        self.assertIn('launch_reviewed_main_v10.py', author)
        self.assertIn("len(bootstrap.encode()) < 120000", author)
        self.assertIn("expected['resource_policy'] == old['resource_policy']", author)
        self.assertNotIn('rmtree(', author)
        self.assertNotIn('.unlink(', author)


def main():
    sys.dont_write_bytecode = True
    sys.addaudithook(audit)
    signal.alarm(30)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    with (HERE/'pure-template-controls-v1.log').open('x') as stream:
        stream.write(log.getvalue())
    output = {'date': '2026-10-16 ET', 'tests': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skips': len(result.skipped), 'external_attempts': EVENTS,
              'actual_Git_compiler_native_verifier_SSH_or_entry_execution': False,
              'published_source': None}
    with (HERE/'pure-template-controls-v1.json').open('x') as stream:
        stream.write(json.dumps(output, sort_keys=True, indent=2)+'\n')
    signal.alarm(0)
    print(json.dumps(output))
    return int(not result.wasSuccessful() or bool(EVENTS))


if __name__ == '__main__':
    raise SystemExit(main())
