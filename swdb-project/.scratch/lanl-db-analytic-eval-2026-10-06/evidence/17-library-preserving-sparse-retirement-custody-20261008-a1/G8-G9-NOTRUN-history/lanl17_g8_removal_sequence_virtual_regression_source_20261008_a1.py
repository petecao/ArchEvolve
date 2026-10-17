"""NOTRUN source: isolated synthetic sequencing/cost regression, not guard admission.

Only exact AST slices gate(), pre_remove_gate(), and the removal/final-preservation
suffix of perform() are lifted. Full source modules, main(), Linux/process/Git,
filesystems, receipts, plans, native tools and the existing 16-case suite are not
invoked. The virtual process/metadata/Git boundaries are independently specified
below. Only the two pinned local source files are read by a future test invocation.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import unittest

SOURCE_PINS = {
    'G7': ('/private/tmp/lanl_consumed_detached_source_guard_r7_20261008_a1.py', 117232,
           '97219cdb326edf76e6d341aab4a2a8d58a4750e3da8d2e24a5f9e1097f4a69be'),
    'G8': ('/private/tmp/lanl_consumed_detached_source_guard_r8_20261008_a1.py', 117156,
           '2bf03516ee69ccadc9ad5b1191959e205314db59aab1edc7b5d62800138e5493'),
}
SYNTHETIC_BASE = PurePosixPath('/SYNTHETIC/checkout')
SYNTHETIC_PRIMARY = PurePosixPath('/SYNTHETIC/primary')
SYNTHETIC_ROWS = {'row-a': {'head': 'synthetic-a'}, 'row-b': {'head': 'synthetic-b'}}
# A worked virtual example, not an estimate or replacement of any production cap.
ROLE_COST = {'row-a': 2, 'row-b': 3}
SYNTHETIC_BYTES = b'SYNTHETIC_PIN'
SYNTHETIC_PIN = hashlib.sha256(SYNTHETIC_BYTES).hexdigest()


class Refused(Exception):
    pass


def require(value, reason):
    if not value:
        raise Refused(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def sha(body):
    return hashlib.sha256(body).hexdigest()


def selected_slice(version):
    path, size, digest = SOURCE_PINS[version]
    with Path(path).open('rb') as source:
        body = source.read(128 * 1024 + 1)
    require(len(body) == size and sha(body) == digest, 'synthetic_source_pin')
    module = ast.parse(body)
    guard = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'Guard')
    functions = {n.name: n for n in guard.body if isinstance(n, ast.FunctionDef)}
    gate = copy.deepcopy(functions['gate'])
    pre = copy.deepcopy(functions['pre_remove_gate'])
    perform = functions['perform']
    first = next(i for i, n in enumerate(perform.body) if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'first' for t in n.targets))
    end = next(i for i, n in enumerate(perform.body) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
                       and t.slice.value == 'admitted' for t in n.targets))
    operation = copy.deepcopy(perform)
    operation.name = 'synthetic_operation'
    operation.body = copy.deepcopy(perform.body[first:end])
    # Validate the lifted public-operation suffix is an exact original statement
    # projection, not a rewritten simulation of the guard's sequencing code.
    require(ast.dump(ast.Module(body=operation.body, type_ignores=[]), include_attributes=False)
            == ast.dump(ast.Module(body=perform.body[first:end], type_ignores=[]), include_attributes=False),
            'synthetic_operation_exact_slice')
    closed = ast.Module(body=[ast.ClassDef(name='SelectedSequence', bases=[], keywords=[],
                                         body=[gate, pre, operation], decorator_list=[])], type_ignores=[])
    for n in ast.walk(closed):
        require(not isinstance(n, (ast.Import, ast.ImportFrom)), 'synthetic_no_import_lift')
    ast.fix_missing_locations(closed)
    # Closed virtual environment: os has only in-memory lexists; path objects are
    # pure and have no filesystem operations. No target module globals are loaded.
    context = {'require': require, 'sha': sha, 'canonical': canonical,
               'BASE': SYNTHETIC_BASE, 'PRIMARY': SYNTHETIC_PRIMARY, 'ROWS': SYNTHETIC_ROWS,
               'LIMITS': {'git_seconds': 120, 'plan_bytes': 2 * 1024 * 1024},
               'P': PurePosixPath, '__file__': '/SYNTHETIC/source.py',
               'now': lambda: 'SYNTHETIC_TIME'}
    return closed, context


class VirtualSystem:
    """In-memory filesystem/process/command boundaries; never real Guard state."""
    def __init__(self, role_limit=25, stable_limit=3, new_consumer=None, changed_inventory_at=None):
        self.args = SimpleNamespace(select=['row-a', 'row-b'], remove=True,
                                    plan='/SYNTHETIC/plan.json', plan_sha256=SYNTHETIC_PIN)
        self.selected = [SYNTHETIC_BASE / name for name in self.args.select]
        self.plan = {'protected_file_pins': []}
        self.facts = {'removed_rows': []}
        self.current_removal = None
        self.own_sha = SYNTHETIC_PIN
        self.raw_before = {}
        self.role_limit = role_limit
        self.stable_limit = stable_limit
        self.role_visits = 0
        self.stable_calls = 0
        self.new_consumer = new_consumer
        self.changed_inventory_at = changed_inventory_at
        self.last_stable_removed = None
        self.last_process_removed = None
        self.last_process_rows = None
        self.git_removed = []
        self.final_raw_checked = False
        self.failure = None
        self.events = []

    def remaining(self):
        return [x for x in self.args.select if x not in self.facts['removed_rows']]

    def left(self):
        return 10000

    def privacy_gate(self):
        return {'SYNTHETIC': True}

    def leases(self):
        return {'SYNTHETIC': {'sha256': 'released-synthetic-generation'}}

    def retain_git(self):
        return {'SYNTHETIC': 'retained'}

    def protect(self):
        pass

    def tree(self, path, head):
        return {'row': path.name, 'head': head, 'SYNTHETIC': True}

    def aliases_and_sources(self):
        return {'SYNTHETIC': True}

    def read(self, path, cap):
        require(str(path) in ('/SYNTHETIC/plan.json', '/SYNTHETIC/source.py')
                and len(SYNTHETIC_BYTES) <= cap, 'synthetic_read_closed')
        return SYNTHETIC_BYTES, {}

    def pinned(self, pin):
        raise AssertionError('synthetic fixture has no protected-file pins')

    def process_references(self, continuity_rows=None):
        rows = self.remaining() if continuity_rows is None else list(continuity_rows)
        require(all(x in self.remaining() for x in rows), 'synthetic_remaining_rows_only')
        self.role_visits += 2 * sum(ROLE_COST[x] for x in rows)
        require(self.role_visits <= self.role_limit, 'virtual_role_visit_budget')
        # The new consumer appears only at the immediate per-current-row boundary.
        if continuity_rows is not None and self.new_consumer in rows:
            raise Refused('virtual_new_live_consumer')
        self.last_process_removed = tuple(self.facts['removed_rows'])
        self.last_process_rows = rows
        self.events.append(('fresh_process', tuple(rows), self.last_process_removed))
        return {'SYNTHETIC': True}

    def stable_inventory(self):
        self.stable_calls += 1
        require(self.stable_calls <= self.stable_limit, 'virtual_stable_stat_budget')
        if self.changed_inventory_at == self.stable_calls:
            raise Refused('virtual_preserved_inventory_changed')
        self.last_stable_removed = tuple(self.facts['removed_rows'])
        self.events.append(('stable_inventory', self.last_stable_removed))
        return {'SYNTHETIC': True}

    def git(self, primary, *argv):
        require(primary == SYNTHETIC_PRIMARY and len(argv) == 3
                and argv[:2] == ('worktree', 'remove'), 'synthetic_command_boundary')
        name = PurePosixPath(argv[2]).name
        prior = tuple(self.facts['removed_rows'])
        # Destructive boundary independently enforces fresh process evidence and
        # a preservation stamp acquired since the previous successful removal.
        require(self.last_stable_removed == prior, 'virtual_remove_without_fresh_inventory')
        require(self.last_process_removed == prior and self.last_process_rows == [name],
                'virtual_remove_without_fresh_current_process')
        require(name in self.remaining(), 'virtual_remove_only_remaining')
        self.git_removed.append(name)
        self.events.append(('git_remove', name, prior))
        return b''

    def lexists(self, path):
        return PurePosixPath(path).name not in self.git_removed

    def receipts_and_raw(self):
        if self.git_removed:
            require(self.last_stable_removed == tuple(self.facts['removed_rows']),
                    'virtual_final_raw_without_fresh_final_inventory')
            self.final_raw_checked = True
            self.events.append(('final_raw', tuple(self.facts['removed_rows'])))
        return {'SYNTHETIC': 'preserved-original-bytes'}


def run_virtual(version, **scenario):
    closed, context = selected_slice(version)
    exec(compile(closed, '<SYNTHETIC exact sequencing slice>', 'exec'), context)
    selected = context['SelectedSequence']
    composite = type('VirtualGuard', (selected, VirtualSystem), {})
    model = composite(**scenario)
    context['os'] = SimpleNamespace(path=SimpleNamespace(lexists=model.lexists))
    try:
        model.synthetic_operation()
    except Refused as error:
        model.failure = str(error)
    return model


class SequencingRegression(unittest.TestCase):
    def test_two_removals_fit_role_budget_without_losing_fresh_safety_boundaries(self):
        original = run_virtual('G7', role_limit=25, stable_limit=100)
        self.assertEqual(original.failure, 'virtual_role_visit_budget')
        self.assertEqual(original.facts['removed_rows'], ['row-a'])
        corrected = run_virtual('G8', role_limit=25, stable_limit=3)
        self.assertIsNone(corrected.failure)
        self.assertEqual(corrected.facts['removed_rows'], ['row-a', 'row-b'])
        self.assertEqual(corrected.git_removed, ['row-a', 'row-b'])
        self.assertTrue(corrected.final_raw_checked)
        # Independently worked literal: initial ten + current-row four + six.
        self.assertEqual(corrected.role_visits, 20)

    def test_preservation_budget_fits_before_each_removal_and_final_raw_pass(self):
        original = run_virtual('G7', role_limit=100, stable_limit=3)
        self.assertEqual(original.failure, 'virtual_stable_stat_budget')
        self.assertEqual(original.facts['removed_rows'], ['row-a', 'row-b'])
        self.assertFalse(original.final_raw_checked)
        corrected = run_virtual('G8', role_limit=100, stable_limit=3)
        self.assertIsNone(corrected.failure)
        self.assertTrue(corrected.final_raw_checked)
        self.assertEqual(corrected.stable_calls, 3)

    def test_new_live_consumer_refuses_second_destructive_command(self):
        result = run_virtual('G8', new_consumer='row-b')
        self.assertEqual(result.failure, 'virtual_new_live_consumer')
        self.assertEqual(result.git_removed, ['row-a'])
        self.assertEqual(result.facts['removed_rows'], ['row-a'])
        self.assertFalse(result.final_raw_checked)

    def test_changed_preserved_inventory_refuses_next_removal_or_final_byte_pass(self):
        for boundary, removed in ((2, ['row-a']), (3, ['row-a', 'row-b'])):
            with self.subTest(boundary=boundary):
                result = run_virtual('G8', changed_inventory_at=boundary)
                self.assertEqual(result.failure, 'virtual_preserved_inventory_changed')
                self.assertEqual(result.git_removed, removed)
                self.assertEqual(result.facts['removed_rows'], removed)
                self.assertFalse(result.final_raw_checked)


if __name__ == '__main__':
    unittest.main(verbosity=2)
