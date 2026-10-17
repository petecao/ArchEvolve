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


if __name__ == '__main__':
    unittest.main()
