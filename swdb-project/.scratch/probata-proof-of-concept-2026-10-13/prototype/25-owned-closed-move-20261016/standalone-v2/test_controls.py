"""2026-10-16 ET. Pure operational controls; no compiler/native/prover calls."""
import copy
from pathlib import Path
import runpy
import stat
import tempfile
import types
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
API = runpy.run_path(str(HERE/'entry-template.py'))


def reports():
    properties = [{'property': key, 'dependencies': [], 'origin': None}
                  for key in ('post', 'smoke', 'terminates')]
    native = [{'goal': 'post', 'property': 'post', 'smoke': False, 'function': 'root', 'passed': True},
              {'goal': 'smoke', 'property': 'smoke', 'smoke': True, 'function': 'callee', 'passed': False},
              {'goal': 'terminates', 'property': 'terminates', 'smoke': False, 'function': 'root', 'passed': True}]
    standard = copy.deepcopy(native[:2])
    standard[1]['function'] = 'root'
    return {'version': '1', 'complete': True, 'goals': native, 'properties': properties}, standard


class Controls(unittest.TestCase):
    def test_unmaterialized_template_refuses_before_any_tool(self):
        with self.assertRaisesRegex(ValueError, 'unmaterialized'):
            API['main']()

    def test_normal_source_flags_retain_sole_absolute_output_and_full_portfolio(self):
        flags = ['-wp', '-wp-rte', '-wp-cache', 'none', '-wp-model', '+real',
                 '-rte-initialized', '@all', '-wp-no-filter-init', '-wp-out', '/exact/retained-native']
        tools = {'flags': flags, 'seconds': 30, 'provers': ['alt-ergo', 'z3', 'cvc5']}
        value = API['normal_flags'](tools)
        self.assertEqual(value, flags+['-machdep', 'x86_64', '-wp-prover', 'alt-ergo,z3,cvc5',
            '-wp-timeout', '30', '-wp-par', '1', '-wp-smoke-tests', '-wp-fct=vector_owned_move_capture'])
        self.assertEqual(value.count('-wp-out'), 1)
        tools['flags'] = [*flags, '-wp-prover', 'alt-ergo,z3,cvc5']
        self.assertEqual(API['normal_flags'](tools).count('-wp-prover'), 1)

    def test_complete_census_retains_every_ordinary_smoke_owner_and_inventory_row(self):
        inventory, standard = reports()
        value = API['complete_census'](inventory, standard)
        self.assertEqual((value['native_goals'], value['ordinary'], value['smokes'],
                          value['standard_goals'], value['properties']), (3, 2, 1, 2, 3))
        self.assertEqual(value['all_native_goals'], inventory['goals'])
        self.assertEqual(value['all_properties'], inventory['properties'])
        self.assertEqual(value['inventory_only_goal_ids'], ['terminates'])
        self.assertEqual(value['native_standard_pairs'][1]['native']['function'], 'callee')
        self.assertEqual(value['native_standard_pairs'][1]['standard']['function'], 'root')
        self.assertFalse(value['source_or_caller_admission'])

    def test_complete_census_refuses_each_missing_or_duplicate_identity(self):
        for kind in ('incomplete', 'native_duplicate', 'standard_duplicate', 'property_duplicate',
                     'foreign_standard', 'missing_property', 'missing_dependency', 'missing_origin'):
            inventory, standard = reports()
            if kind == 'incomplete': inventory['complete'] = False
            elif kind == 'native_duplicate': inventory['goals'].append(copy.deepcopy(inventory['goals'][0]))
            elif kind == 'standard_duplicate': standard.append(copy.deepcopy(standard[0]))
            elif kind == 'property_duplicate': inventory['properties'].append(copy.deepcopy(inventory['properties'][0]))
            elif kind == 'foreign_standard': standard[0]['goal'] = 'foreign'
            elif kind == 'missing_property': inventory['goals'][0]['property'] = 'missing'
            elif kind == 'missing_dependency': inventory['properties'][0]['dependencies'] = ['missing']
            else: inventory['properties'][0]['origin'] = 'missing'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                API['complete_census'](inventory, standard)

    def test_aggregate_extent_and_final_metadata_respect_same_cap(self):
        with tempfile.TemporaryDirectory(prefix='probata-move-standalone-budget-') as directory:
            root = Path(directory)
            globals_ = API['write'].__globals__
            with patch.dict(globals_, {'BUDGET': 100, 'FINAL_HEADROOM': 20}):
                (root/'native').write_bytes(b'x'*75)
                with self.assertRaises(ValueError): API['write'](root, root/'ordinary.json', b'123456')
                self.assertFalse((root/'ordinary.json').exists())
                API['write'](root, root/'result.json', b'1'*15, reserve=False)
                API['write'](root, root/'manifest.json', b'2'*10, reserve=False)
                self.assertEqual(API['extent'](root), 100)
                with self.assertRaises(ValueError): API['write'](root, root/'extra.json', b'3', reserve=False)

    def test_unknown_links_are_refused_even_in_native_scratch(self):
        with tempfile.TemporaryDirectory(prefix='probata-move-standalone-path-') as directory:
            root = Path(directory)
            scratch = root/'wp/tmp'; scratch.mkdir(parents=True)
            (root/'regular').write_bytes(b'unchanged')
            for parent in (root, scratch):
                path = parent/'redirect';path.symlink_to(root/'regular')
                try:
                    for active in (False, True):
                        with self.assertRaises(ValueError): API['extent'](root, active=active)
                finally: path.unlink()

    def test_transient_socket_exception_is_exact_owned_scratch_and_active_only(self):
        root = Path('/exact/private/observation')
        def scan_for(path, mode, disappears=False):
            def scan(directory):
                if directory != root: return []
                def observed(*, follow_symlinks):
                    self.assertFalse(follow_symlinks)
                    if disappears: raise FileNotFoundError(path)
                    return types.SimpleNamespace(st_mode=mode, st_size=0)
                return [types.SimpleNamespace(path=str(path), stat=observed)]
            return scan
        for path in (root/'wp/tmp/owned-socket', root/'wp/foreign-socket', root/'sibling'):
            with patch.object(API['os'], 'scandir', scan_for(path, stat.S_IFSOCK)):
                for active in (False, True):
                    if active and path.is_relative_to(root/'wp/tmp'):
                        self.assertEqual(API['extent'](root, active=active), 0)
                    else:
                        with self.assertRaises(ValueError): API['extent'](root, active=active)
            with patch.object(API['os'], 'scandir', scan_for(path, stat.S_IFREG, disappears=True)):
                for active in (False, True):
                    if active and path.is_relative_to(root/'wp/tmp'):
                        self.assertEqual(API['extent'](root, active=active), 0)
                    else:
                        with self.assertRaises(FileNotFoundError): API['extent'](root, active=active)

    def test_active_extent_guard_kills_only_through_explicit_callback(self):
        globals_ = API['OutputWatch'].loop.__globals__
        with tempfile.TemporaryDirectory(prefix='probata-move-standalone-active-') as directory:
            root = Path(directory)
            (root/'native').write_bytes(b'x'*81)
            calls = []
            watcher = API['OutputWatch'](root, lambda: (calls.append('kill-current-descendants'), watcher.stop.set()))
            with patch.dict(globals_, {'BUDGET': 100, 'FINAL_HEADROOM': 20}): watcher.loop()
            self.assertEqual(calls, ['kill-current-descendants'])
            self.assertIn('aggregate', watcher.error)

    def test_latched_guard_prevents_each_later_producer_and_process_launch(self):
        clock = [10.0]
        watcher = types.SimpleNamespace(error=None, thread=types.SimpleNamespace(ident=-1))
        gate = API['ProducerGate'](watcher, 600, clock=lambda: clock[0])
        calls = []
        self.assertEqual(gate.call(lambda: calls.append('first') or 9), 9)
        for label in ('compiler', 'identity', 'reader', 'foundation', 'native', 'git'):
            watcher.error = 'latched output failure'
            with self.subTest(label=label), self.assertRaises(ValueError):
                gate.call(lambda: calls.append(label))
        for event, args in [('subprocess.Popen', ('compiler', ['compiler'], None, None)),
                            ('os.system', ('compiler',)), ('os.posix_spawn', ('compiler', [], {}))]:
            with self.subTest(event=event), self.assertRaises(ValueError):
                gate.audit(event, args)
        self.assertEqual(calls, ['first'])
        watcher.error = None
        clock[0] = 601
        with self.assertRaises(ValueError): gate.call(lambda: calls.append('late'))
        with self.assertRaises(ValueError): gate.remaining(30)
        self.assertEqual(calls, ['first'])

    def test_finalization_rejects_post_close_or_hash_delay_and_includes_final_metadata(self):
        for fault in ('none', 'result_close', 'manifest_close', 'result_pin', 'manifest_pin', 'extent'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix='probata-move-final-') as directory:
                root = Path(directory)
                (root/'native').write_bytes(b'raw')
                clock = [599.0]
                gate = API['ProducerGate'](types.SimpleNamespace(error=None), 600, clock=lambda: clock[0])
                result = {'producer_complete': True, 'diagnostic_only': True}
                values = API['finalize'].__globals__
                old_write, old_pin, old_extent = API['write'], API['pin'], API['extent']
                def write(out, path, raw, **kw):
                    old_write(out, path, raw, **kw)
                    if (fault == 'result_close' and path.name == 'result.json') or (
                            fault == 'manifest_close' and path.name == 'artifact-manifest.json'):
                        clock[0] = 601
                def pin(path):
                    value = old_pin(path)
                    if fault == 'result_pin' and path.name == 'result.json': clock[0] = 601
                    if fault == 'manifest_pin' and path.name == 'artifact-manifest.json': clock[0] = 601
                    return value
                def extent(out, **kw):
                    value = old_extent(out, **kw)
                    if fault == 'extent' and (out/'artifact-manifest.json').exists(): clock[0] = 601
                    return value
                with patch.dict(values, {'write': write, 'pin': pin, 'extent': extent}):
                    if fault == 'none':
                        observed = API['finalize'](root, result, gate, 0)
                        self.assertTrue(observed['settled'])
                        self.assertEqual(observed['aggregate_bytes'], old_extent(root))
                        saved = API['json'].loads((root/'result.json').read_bytes())
                        self.assertTrue(saved['requires_zero_exit_and_settled_publication'])
                    else:
                        with self.assertRaises(ValueError): API['finalize'](root, result, gate, 0)

    def test_projection_refuses_final_metadata_before_any_file_overshoots(self):
        with tempfile.TemporaryDirectory(prefix='probata-move-projected-') as directory:
            root = Path(directory)
            gate = API['ProducerGate'](types.SimpleNamespace(error=None), 600, clock=lambda: 1)
            globals_ = API['finalize'].__globals__
            with patch.dict(globals_, {'BUDGET': 100}):
                with self.assertRaises(ValueError): API['finalize'](root, {'producer_complete': True}, gate, 0)
                self.assertFalse((root/'result.json').exists())
                self.assertFalse((root/'artifact-manifest.json').exists())

    def test_fragment_metadata_binds_allocators_all_members_and_full_source_before_native(self):
        rendered = {
            'ctor_count_value': [('swdb_alloc_int', 'ALLOC;'), ('swdb_free', 'FREE;'), ('ctor', 'CTOR;')],
            'dtor': [('swdb_alloc_int', 'ALLOC;'), ('swdb_free', 'FREE;'), ('dtor', 'DTOR;')],
            'data': [('data', 'DATA;')], 'move_ctor': [('move', 'MOVE;')]}
        names = ('swdb_alloc_int', 'swdb_free', 'ctor', 'dtor', 'data', 'move')
        lowering = types.SimpleNamespace(models=names, text='ALLOC;\nFREE;\nCTOR;\nDTOR;\nDATA;\nMOVE;')
        render = lambda vector, element, member: rendered[member]
        value = API['model_fragments'](lowering, render)
        self.assertEqual(tuple(row['name'] for row in value), names)
        self.assertTrue(all(row['occurrences_in_original_C'] == 1 for row in value))
        for fault in ('duplicate_disagrees', 'missing_membership', 'extra_membership', 'missing_fragment', 'duplicate_occurrence'):
            with self.subTest(fault=fault):
                changed = copy.deepcopy(rendered)
                fake = copy.copy(lowering)
                if fault == 'duplicate_disagrees': changed['dtor'][0] = ('swdb_alloc_int', 'OTHER;')
                elif fault == 'missing_membership': fake.models = names[:-1]
                elif fault == 'extra_membership': fake.models = (*names, 'foreign')
                elif fault == 'missing_fragment': fake.text = fake.text.replace('FREE;', '')
                else: fake.text += '\nALLOC;'
                with self.assertRaises(ValueError):
                    API['model_fragments'](fake, lambda vector, element, member: changed[member])

    def test_flushed_publication_delay_or_latched_guard_cannot_return_zero(self):
        for fault in ('none', 'delay', 'latch'):
            clock = [599.0]
            watcher = types.SimpleNamespace(error=None)
            gate = API['ProducerGate'](watcher, 600, clock=lambda: clock[0])
            result = {'producer_complete': True, 'finalized': {'settled': True},
                      'normal_reader_refusal': '\u2603'*100000,
                      'error': '\u2603'*100000, 'output_guard_error': 'original census failure'}
            captured = []
            def emit(value, *, flush):
                self.assertTrue(flush)
                captured.append(value)
                if fault == 'delay': clock[0] = 601
                if fault == 'latch': watcher.error = 'late latch'
            with patch.dict(API['publish'].__globals__, {'print': emit, 'extent': lambda root: 0}):
                self.assertEqual(API['publish'](Path('/fake'), result, gate), int(fault != 'none'))
            self.assertLessEqual(len(captured[0].encode())+1, 8192)
            value = API['json'].loads(captured[0])
            self.assertTrue(value['summary_truncated'])
            self.assertIn('output_guard_error', value)
            self.assertTrue(value['requires_zero_exit_and_settled_publication'])

    def test_latched_watcher_keeps_cleanup_fence_and_records_cleanup_failure(self):
        root = Path('/fake')
        calls = []
        def cleanup():
            calls.append('cleanup')
            if len(calls) == 1: raise RuntimeError('first cleanup failed')
            watcher.stop.set()
        watcher = API['OutputWatch'](root, cleanup)
        with patch.dict(API['OutputWatch'].loop.__globals__, {'extent': lambda *a, **kw: API['BUDGET']}):
            watcher.loop()
        self.assertEqual(calls, ['cleanup', 'cleanup'])
        self.assertIn('aggregate', watcher.error)
        self.assertIn('first cleanup failed', watcher.cleanup_error)

    def test_only_monitor_exact_readonly_rss_fallback_can_cross_latched_audit(self):
        watcher = types.SimpleNamespace(error='latched', thread=types.SimpleNamespace(ident=123))
        gate = API['ProducerGate'](watcher, 600, clock=lambda: 1)
        ps = ['ps', '-A', '-o', 'pid=,ppid=,rss=']
        with patch.object(API['threading'], 'get_ident', return_value=123):
            gate.audit('subprocess.Popen', ('ps', ps, None, None))
            for executable, argv in [('compiler', ['compiler']), ('ps', [*ps, 'foreign']),
                                     ('ps', ['ps', '-A']), ('/tmp/ps', ps)]:
                with self.subTest(argv=argv), self.assertRaises(ValueError):
                    gate.audit('subprocess.Popen', (executable, argv, None, None))
        with patch.object(API['threading'], 'get_ident', return_value=456):
            with self.assertRaises(ValueError): gate.audit('subprocess.Popen', ('ps', ps, None, None))


if __name__ == '__main__':
    unittest.main()
