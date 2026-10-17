"""2026-10-16 ET. Child-free reader controls; no remote or proof execution."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
ATTEMPTS = []


def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.fork', 'os.posix_spawn', 'ctypes.dlopen'} or event.startswith('socket.'):
        ATTEMPTS.append(event)
        raise RuntimeError('no external execution in pure controls')


sys.addaudithook(audit)
module = types.ModuleType('inert_mixed_cold_controls')
exec(compile((HERE / 'entry.py').read_text(), '<inert-reader-definitions-only>', 'exec'), module.__dict__)


class Controls(unittest.TestCase):
    def setUp(self):
        self.read, self.pin, self.bytes = module.read, module.pin, module.read_bytes

    def tearDown(self):
        module.read, module.pin, module.read_bytes = self.read, self.pin, self.bytes

    def records(self):
        result = [{'job': {'adapter': 'wp'}, 'subject': {'kind': 'c_model', 'id': name}}
                  for name in module.CONTEXT['model_names']]
        result += [{'job': {'adapter': adapter}, 'subject': {'kind': 'library_summary', 'id': name}}
                   for adapter in ('wp', 'cbmc') for name in
                   ('contract.fixture_pair_pointer_values', 'contract.fixture_pair_pointer_wrong_identity')]
        return result

    def test_all_eight_roles_order_and_duplicate_refusal(self):
        records = self.records()
        self.assertEqual(module.record_order(list(reversed(records))), records)
        with self.assertRaises(ValueError):
            module.record_order([*records[:7], records[0]])
        records[-1]['subject']['id'] = 'unreviewed.subject'
        with self.assertRaises(ValueError):
            module.record_order(records)

    def test_full_native_standard_goal_mapping_refuses_drop_or_owner_change(self):
        native = {'version': '1', 'complete': True, 'goals': [{'goal': 'g', 'property': 'p', 'smoke': False}],
                  'properties': [{'property': 'p', 'dependencies': [], 'origin': None, 'extern': False}],
                  'property_closure': {}}
        table = {'wp-inventory.json': native, 'wp-goals.json': [{'goal': 'g', 'property': 'wrong', 'smoke': False}]}
        module.read = lambda path: table[path.name]
        with self.assertRaises(ValueError):
            module.wp_context(Path('/unused'), {'id': 'record'})
        table['wp-goals.json'] = []
        with self.assertRaises(ValueError):
            module.wp_context(Path('/unused'), {'id': 'record'})

    def cbmc(self, *, wrong=False, extra_failure=None):
        labels = ['swdb_reach.end']
        if wrong:
            labels += ['contract.fixture_pair_pointer_wrong_identity#post.ensures1']
        if extra_failure:
            labels += [extra_failure]
        goals = [{'goal': 'g%d' % index, 'property': name, 'status': 'failure'}
                 for index, name in enumerate(labels)]
        results = [{'property': goal['goal'], 'status': 'FAILURE'} for goal in goals]
        record = {'id': 'record', 'subject': {'id': 'contract.fixture_pair_pointer_wrong_identity' if wrong else
                  'contract.fixture_pair_pointer_values'}, 'goals': goals,
                  'settings': {'agreement': {'verdict': 'agree', 'runs': 49, 'sampled': False,
                      'c_output_sha256': 'x', 'cxx_output_sha256': 'x'}, 'forms': {}}}
        module.read = lambda path: [{'result': results}]
        module.pin = lambda path: {'sha256': 'x', 'path': str(path), 'bytes': 1}
        return record, results

    def test_cbmc_safe_reach_failure_is_expected_but_extra_failure_refuses(self):
        record, results = self.cbmc()
        observed = module.cbmc_context(Path('/unused/nonexistent'), record)
        self.assertEqual(observed['failed_property_labels'], ['swdb_reach.end'])
        record, results = self.cbmc(extra_failure='unmodeled_assertion')
        with self.assertRaises(ValueError):
            module.cbmc_context(Path('/unused/nonexistent'), record)

    def test_cbmc_missing_actual_property_refuses(self):
        record, results = self.cbmc()
        results.append({'property': 'hidden', 'status': 'SUCCESS'})
        with self.assertRaises(ValueError):
            module.cbmc_context(Path('/unused'), record)

    def test_cbmc_failed_unwind_cannot_hide_as_reachability(self):
        record, results = self.cbmc()
        results[0]['description'] = 'unwinding assertion'
        with self.assertRaises(ValueError):
            module.cbmc_context(Path('/unused'), record)

    def test_native_draw_count_or_sampling_change_refuses(self):
        for key, value in [('runs', 48), ('sampled', True), ('verdict', 'different')]:
            record, results = self.cbmc()
            record['settings']['agreement'][key] = value
            with self.assertRaises(ValueError):
                module.cbmc_context(Path('/unused'), record)

    def test_unknown_special_or_new_raw_member_refuses(self):
        old_raw, old_profile, old_context = module.RAW, module.PROFILE, module.CONTEXT
        try:
            with tempfile.TemporaryDirectory() as folder:
                module.RAW = Path(folder).resolve()
                module.PROFILE = module.RAW / 'mixed-pair-profile'
                module.CONTEXT = {'aliases': {}, 'raw_membership': []}
                self.assertEqual(module.raw_membership(), [])
                (module.RAW / 'unexpected').write_bytes(b'x')
                with self.assertRaises(ValueError):
                    module.raw_membership()
                (module.RAW / 'unexpected').unlink()
                (module.RAW / 'alias').symlink_to('/unreviewed')
                with self.assertRaises(ValueError):
                    module.raw_membership()
        finally:
            module.RAW, module.PROFILE, module.CONTEXT = old_raw, old_profile, old_context

    def test_semantic_unavailability_is_never_accepted(self):
        text = (HERE / 'entry.py').read_text()
        tree = ast.parse(text)
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        segment = ast.get_source_segment(text, main)
        self.assertIn("'scientific_cold_acceptance': False", segment)
        self.assertIn("'full_original_solver_task_files_retained': 0", segment)
        self.assertIn('return 2', segment)
        self.assertNotIn('subprocess.', segment)

    def test_reader_has_no_project_imports_or_actual_tool_probes(self):
        tree = ast.parse((HERE / 'entry.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or '').startswith('swdb'))
            if isinstance(node, ast.Import):
                self.assertFalse(any(alias.name.startswith('swdb') for alias in node.names))
        self.assertEqual(ATTEMPTS, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
