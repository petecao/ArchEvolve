"""SOURCE-ONLY reviewed harness for SYNTHETIC binding and signal custody.

Future harness execution lifts only pinned config/check, two journal statements,
and failure-projection AST blocks. It never imports/calls a guard, main, Git,
process, file, native, SSH, cleanup or actual-plan operation. Source byte reads
are limited to the two explicit local reviewed source pins below.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE_PINS = {
    'R1': ('/private/tmp/lanl_consumed_detached_source_guard_r1_20261007.py', 64859,
           '66944bb04d05a690dc1c81ced7c203c0494cc028c6c9c1531e1fcb9cecd110e1'),
    'R2': ('/private/tmp/lanl_consumed_detached_source_guard_r2_20261007.py', 65830,
           '3ff7bde67947adf524d0c4f556047fcf1377bc6ddb1e64c9ac58409c3e0acfeb'),
}
COVERAGE_KEYS = ('control_siblings_complete_review', 'pending_alias_coverage_review',
                 'receipt_source_proofs_complete_review', 'original_raw_files_complete_review')


class SyntheticRefused(Exception):
    pass


class SyntheticInterrupt(Exception):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(doc):
    return json.dumps(doc, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def require(condition, reason):
    if not condition:
        raise SyntheticRefused(reason)


def assigned_name(node, name):
    return (isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name)


def target_text(node):
    return ast.unparse(node)


def load_blocks(label):
    source_path, size, expected = SOURCE_PINS[label]
    raw = Path(source_path).read_bytes()
    if len(raw) != size or sha(raw) != expected:
        raise AssertionError('pinned reviewed source changed')
    module = ast.parse(raw.decode())
    guards = [n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'Guard']
    if len(guards) != 1:
        raise AssertionError('one original Guard AST required')
    perform = [n for n in guards[0].body if isinstance(n, ast.FunctionDef) and n.name == 'perform']
    if len(perform) != 1:
        raise AssertionError('one perform AST required')
    statements = perform[0].body
    starts = [i for i, n in enumerate(statements) if assigned_name(n, 'config')]
    ends = [i for i, n in enumerate(statements) if assigned_name(n, 'native')]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise AssertionError('exact contiguous config/check block required')
    config = copy.deepcopy(statements[starts[0]:ends[0]])
    # No target calls beyond the explicit pure config/check closure may be lifted.
    for n in ast.walk(ast.Module(body=config, type_ignores=[])):
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            raise AssertionError('definition/import not allowed in isolated projection')
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name):
                if n.func.id not in {'dict', 'all', 'require', 'sha', 'canonical'}:
                    raise AssertionError('unreviewed projection call')
            elif not (isinstance(n.func, ast.Attribute) and n.func.attr in {'items', 'append', 'pop'}):
                raise AssertionError('unreviewed projection attribute call')
    remove_loops = [n for n in statements if isinstance(n, ast.For)
                    and isinstance(n.target, ast.Name) and n.target.id == 'name']
    if len(remove_loops) != 1:
        raise AssertionError('one explicit row-removal loop AST required')
    loop = remove_loops[0].body
    matches = []
    for i in range(len(loop) - 1):
        text = {target_text(loop[i]), target_text(loop[i+1])}
        if text == {'self.current_removal = None', "self.facts['removed_rows'].append(name)"}:
            matches.append(copy.deepcopy(loop[i:i+2]))
    if len(matches) != 1:
        raise AssertionError('exact adjacent journal statements required')
    journal = matches[0]
    mains = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'main']
    if len(mains) != 1:
        raise AssertionError('one original main AST required for projection only')
    handlers = [h for n in mains[0].body if isinstance(n, ast.Try) for h in n.handlers]
    failure = []
    for handler in handlers:
        for i, n in enumerate(handler.body[:-1]):
            if target_text(n) == "g.facts['partial_failure_rows_already_removed'] = list(g.facts['removed_rows'])":
                nxt = handler.body[i+1]
                if not (isinstance(nxt, ast.If)
                        and target_text(nxt.test) == 'g.current_removal is not None'):
                    raise AssertionError('exact failure marker projection required')
                failure.append(copy.deepcopy([n, nxt]))
    if len(failure) != 1:
        raise AssertionError('one two-statement failure custody projection required')
    # Both projected blocks are kept byte-source pinned; no main/loop call is made.
    if Path(source_path).read_bytes() != raw:
        raise AssertionError('source changed during AST preparation')
    return config, journal, failure[0]


def execute_tiny(statements, supplied):
    # No open/import/native/process/Git/filesystem function exists in this closure.
    scope = {'__builtins__': {'dict': dict, 'all': all, 'list': list},
             'require': require, 'sha': sha, 'canonical': canonical, **supplied}
    node = ast.fix_missing_locations(ast.Module(body=copy.deepcopy(statements), type_ignores=[]))
    exec(compile(node, '<SYNTHETIC_PINNED_AST_BLOCK>', 'exec'), scope, scope)
    return scope


def reviewed_fixture():
    """Explicitly SYNTHETIC dictionaries; no actual plan, path or observation."""
    d = {'identity_sha256': 'SYNTHETIC_UNSEALED_PLAN_PLACEHOLDER',
         'parent_review_pin': {'identity_sha256': 'SYNTHETIC_UNBOUND_REVIEW'},
         'selected_rows': ['SYNTHETIC_ROW'], 'expected_primary': 'SYNTHETIC_PRIMARY',
         'guard_source_sha256': 'SYNTHETIC_SOURCE',
         'unknown_extra_configuration': {'ordinary_fact': 7,
                                         'parent_review_identity_sha256': 'SYNTHETIC_BOUND_EXTRA_ID'},
         'allocation_decision': {'minimal_selected_subset': True, 'bytes': 12345},
         'relevant_privileged_consumers': [
             {'pid': 111, 'identified_as_owned_consumer': True,
              'review_basis': 'SYNTHETIC_IDENTIFICATION_A',
              'identification_file_pin': {'sha256': 'SYNTHETIC_PIN_A', 'bytes': 8},
              'parent_review_identity_sha256': 'SYNTHETIC_UNBOUND_REVIEW'},
             {'pid': 222, 'identified_as_owned_consumer': True,
              'review_basis': 'SYNTHETIC_IDENTIFICATION_B',
              'identification_file_pin': {'sha256': 'SYNTHETIC_PIN_B', 'bytes': 9},
              'parent_review_identity_sha256': 'SYNTHETIC_UNBOUND_REVIEW'}]}
    for key in COVERAGE_KEYS:
        d[key] = {'complete': True, 'source_pin': {'sha256': 'SYNTHETIC_'+key, 'bytes': 10},
                  'parent_review_identity_sha256': 'SYNTHETIC_UNBOUND_REVIEW'}
    # Parent binding order is explicit: bind substantive facts, seal review, fill
    # only its back-links, then seal the full plan. No target helper is used here.
    projection = copy.deepcopy(d)
    del projection['identity_sha256']; del projection['parent_review_pin']
    for key in COVERAGE_KEYS:
        del projection[key]['parent_review_identity_sha256']
    for item in projection['relevant_privileged_consumers']:
        del item['parent_review_identity_sha256']
    review = {'format': 'swdb.consumed-detached-source-parent-review.v1',
              'canonical_ensure_ascii': True, 'accepted_for_exact_subset': True,
              'final14_completed_and_released': True,
              'reviewed_configuration_sha256': sha(canonical(projection))}
    review['identity_sha256'] = sha(canonical(review))
    d['parent_review_pin']['identity_sha256'] = review['identity_sha256']
    for key in COVERAGE_KEYS:
        d[key]['parent_review_identity_sha256'] = review['identity_sha256']
    for item in d['relevant_privileged_consumers']:
        item['parent_review_identity_sha256'] = review['identity_sha256']
    body = {k:v for k,v in d.items() if k != 'identity_sha256'}
    d['identity_sha256'] = sha(canonical(body))
    return d, review, projection


def leaf_paths(value, prefix=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaf_paths(v, prefix+(k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaf_paths(v, prefix+(i,))
    else:
        yield prefix


def changed_value(value):
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if isinstance(value, str):
        return value + '_SYNTHETIC_TAMPER'
    raise AssertionError('closed synthetic leaf types only')


class SyntheticRoot:
    def __truediv__(self, row):
        return ('SYNTHETIC_NO_FILESYSTEM', row)


def failure_custody(failure_block, state):
    virtual_os = SimpleNamespace(path=SimpleNamespace(lexists=lambda p: False))
    execute_tiny(failure_block, {'g': state, 'BASE': SyntheticRoot(), 'os': virtual_os})
    # This is a snapshot of the actual isolated source-projected failure facts.
    return copy.deepcopy(state.facts)


def journal_custody(journal, failure, boundary):
    state = SimpleNamespace(facts={'removed_rows': []},
                            current_removal={'row': 'SYNTHETIC_ROW', 'started_at': 'SYNTHETIC_TIME'})
    try:
        for index in range(3):
            if index == boundary:
                raise SyntheticInterrupt('SYNTHETIC_SIGNAL_AFTER_LOGICAL_SUCCESS')
            if index < 2:
                execute_tiny([journal[index]], {'self': state, 'name': 'SYNTHETIC_ROW'})
    except SyntheticInterrupt:
        return failure_custody(failure, state)
    raise AssertionError('one synthetic statement boundary must interrupt')


def has_row_custody(custody):
    return ('SYNTHETIC_ROW' in custody['partial_failure_rows_already_removed']
            or custody.get('incomplete_removal_attempt', {}).get('row') == 'SYNTHETIC_ROW')


class BindingJournalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = {label: load_blocks(label) for label in ('R1', 'R2')}

    def test_noncyclic_binding_r1_known_negative_r2_accepts_metadata_unchanged(self):
        d, review, projection = reviewed_fixture(); original = copy.deepcopy((d, review))
        with self.assertRaises(SyntheticRefused):
            execute_tiny(self.blocks['R1'][0], {'d': d, 'review': review})
        result = execute_tiny(self.blocks['R2'][0], {'d': d, 'review': review})
        self.assertEqual(result['config'], projection)
        self.assertEqual(sha(canonical(result['config'])), review['reviewed_configuration_sha256'])
        self.assertEqual((d, review), original)
        self.assertEqual(review['identity_sha256'], sha(canonical({k:v for k,v in review.items() if k!='identity_sha256'})))
        self.assertEqual(d['identity_sha256'], sha(canonical({k:v for k,v in d.items() if k!='identity_sha256'})))

    def test_every_non_backlink_configuration_leaf_remains_bound(self):
        d, review, projection = reviewed_fixture()
        paths = list(leaf_paths(projection)); self.assertGreater(len(paths), 20)
        for path in paths:
            with self.subTest(path=path):
                modified = copy.deepcopy(d); slot = modified
                for key in path[:-1]: slot = slot[key]
                slot[path[-1]] = changed_value(slot[path[-1]])
                with self.assertRaises(SyntheticRefused):
                    execute_tiny(self.blocks['R2'][0], {'d': modified, 'review': review})

    def test_each_excluded_backlink_is_checked_against_sealed_review_identity(self):
        d, review, _ = reviewed_fixture()
        paths = [(k, 'parent_review_identity_sha256') for k in COVERAGE_KEYS]
        paths += [('relevant_privileged_consumers', i, 'parent_review_identity_sha256') for i in range(2)]
        self.assertEqual(len(paths), 6)
        for path in paths:
            with self.subTest(path=path):
                modified = copy.deepcopy(d); slot = modified
                for key in path[:-1]: slot = slot[key]
                slot[path[-1]] = 'SYNTHETIC_WRONG_REVIEW_ID'
                with self.assertRaisesRegex(SyntheticRefused, 'excluded_parent_review_link_not_bound'):
                    execute_tiny(self.blocks['R2'][0], {'d': modified, 'review': review})

    def test_non_whitelisted_nested_identity_name_is_not_stripped(self):
        d, review, projection = reviewed_fixture()
        self.assertIn('parent_review_identity_sha256', projection['unknown_extra_configuration'])
        d['unknown_extra_configuration']['parent_review_identity_sha256'] = 'SYNTHETIC_TAMPER'
        with self.assertRaises(SyntheticRefused):
            execute_tiny(self.blocks['R2'][0], {'d': d, 'review': review})

    def test_original_r1_signal_boundary_loses_both_custody_channels(self):
        _, journal, failure = self.blocks['R1']
        custody = [journal_custody(journal, failure, b) for b in range(3)]
        self.assertEqual([has_row_custody(x) for x in custody], [True, False, True])
        self.assertEqual(custody[1]['partial_failure_rows_already_removed'], [])
        self.assertNotIn('incomplete_removal_attempt', custody[1])

    def test_corrected_r2_every_signal_boundary_retains_completed_or_uncertain_row(self):
        _, journal, failure = self.blocks['R2']
        custody = [journal_custody(journal, failure, b) for b in range(3)]
        self.assertTrue(all(has_row_custody(x) for x in custody))
        self.assertEqual(custody[0]['partial_failure_rows_already_removed'], [])
        self.assertEqual(custody[0]['incomplete_removal_attempt']['row'], 'SYNTHETIC_ROW')
        self.assertEqual(custody[1]['partial_failure_rows_already_removed'], ['SYNTHETIC_ROW'])
        self.assertEqual(custody[1]['incomplete_removal_attempt']['row'], 'SYNTHETIC_ROW')
        self.assertEqual(custody[2]['partial_failure_rows_already_removed'], ['SYNTHETIC_ROW'])
        self.assertNotIn('incomplete_removal_attempt', custody[2])


if __name__ == '__main__':
    unittest.main(verbosity=2)
