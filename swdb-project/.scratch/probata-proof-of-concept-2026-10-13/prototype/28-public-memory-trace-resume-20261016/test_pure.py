"""2026-10-16 ET. Standard-library preparation and abstract-reference controls.

No C/C++ execution or public adapter is exercised. A successful result is not a
verifier, source-body, native, hardware or ticket-acceptance certificate.
"""
import ast
import hashlib
import itertools
import json
from pathlib import Path
import re
import tempfile
import unittest

import trace_fixture as fixture
from trace_cases import CASES, source


class RuleFailure(Exception):
    pass


class Reference:
    """Independent Python abstract event specification, deliberately no C parser."""
    def __init__(self, choices):
        self.choices = iter(choices)
        self.memory = [0, 0]
        self.owner = [-1] * 4
        self.commands = []

    @staticmethod
    def check(condition, rule):
        if not condition:
            raise RuleFailure(rule)

    def mask(self, tile, width):
        self.check(width in (4, 8) and 0 <= tile and tile + width // 4 <= 4, 'pair_domain')
        return set(range(tile, tile + width // 4))

    def owned(self, thread, tiles):
        self.check(thread in (0, 1), 'thread_domain')
        self.check(all(self.owner[tile] == thread for tile in tiles), 'tile_ownership')

    def cover(self, command):
        if command['live']:
            if command['access'] == 1:
                command['result'] = command['history'][next(self.choices) % len(command['history'])] if len(command['history']) > 1 else command['history'][0]
            else:
                self.memory[command['cell']] = command['value']
            command['live'] = False

    def cpu(self, thread, cell, write):
        self.check(thread in (0, 1) and cell in (0, 1), 'cell_domain')
        for command in self.commands:
            if command['live'] and command['cell'] == cell:
                self.check(command['access'] != 2, 'store_footprint_cpu_access')
                self.check(not write or thread != command['thread'], 'same_thread_read_footprint_write')

    def claim(self, thread, tile, width):
        tiles = self.mask(tile, width)
        self.check(all(self.owner[i] == -1 for i in tiles), 'tile_already_owned')
        for i in tiles:
            self.owner[i] = thread
        return 0

    def cpu_read(self, thread, cell):
        self.cpu(thread, cell, False)
        return self.memory[cell]

    def cpu_write(self, thread, cell, value):
        self.cpu(thread, cell, True)
        self.check(0 <= value <= 31, 'value_domain')
        for command in self.commands:
            if command['live'] and command['access'] == 1 and command['cell'] == cell:
                self.check(len(command['history']) == 1, 'swdb.ghost_capacity')
                command['history'].append(value)
        self.memory[cell] = value
        return 0

    def cpu_cas(self, thread, cell, expected, desired):
        actual = self.cpu_read(thread, cell)
        if actual == expected:
            self.cpu_write(thread, cell, desired)
            return 1
        return 0

    def issue(self, thread, access, region, cell, tile, width, value):
        tiles = self.mask(tile, width)
        self.owned(thread, tiles)
        self.check(region == cell and cell in (0, 1), 'region_footprint_correspondence')
        self.check(len(self.commands) < 2, 'swdb.ghost_capacity')
        for command in self.commands:
            if command['live'] and ((access == 1 and tile == command['tile']) or
                (region == command['region'] and 2 in (access, command['access']))):
                self.cover(command)
        for command in self.commands:
            if command['live']:
                self.check(not (tiles & command['tiles']) or access == command['access'] == 2, 'pending_tile_write')
                self.check(cell != command['cell'] or access == command['access'] == 1, 'device_memory_conflict')
        self.commands.append(dict(live=True, thread=thread, access=access, region=region, cell=cell,
                                  tile=tile, tiles=tiles, value=value, history=[self.memory[cell]], result=0))
        return len(self.commands) - 1

    def wait(self, tile):
        self.mask(tile, 4)
        for command in self.commands:
            if command['live'] and tile in command['tiles']:
                self.cover(command)
        return 0

    def tile_read(self, thread, tile, width):
        tiles = self.mask(tile, width)
        self.owned(thread, tiles)
        for command in self.commands:
            self.check(not command['live'] or command['access'] != 1 or not (tiles & command['tiles']), 'pending_tile_write')
        return 0

    def pending(self, command):
        return int(self.commands[command]['live'])

    def result(self, command):
        self.check(not self.commands[command]['live'], 'pending_tile_write')
        return self.commands[command]['result']

    def ready(self, tile):
        pending = any(c['live'] and tile in c['tiles'] for c in self.commands)
        ready = next(self.choices) % 2 if pending else 1
        if ready:
            self.wait(tile)
        return ready


def evaluate_predicate(text, values):
    # This test consumes only the closed fixture expressions, never source eval.
    tree = ast.parse(text.replace('&&', ' and ').replace('||', ' or '), mode='eval')
    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.BoolOp):
            return (all if isinstance(node.op, ast.And) else any)(evaluate(v) for v in node.values)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
            return evaluate(node.left) == evaluate(node.comparators[0])
        raise AssertionError('predicate grammar expanded')
    return bool(evaluate(tree.body))


def reference_run(row, choices):
    model, values = Reference(choices), {}
    try:
        for action in row['actions']:
            args = [values[a] if isinstance(a, str) else a for a in action[1]]
            value = getattr(model, action[0])(*args)
            if len(action) == 3:
                values[action[2]] = value
        model.check(not any(c['live'] for c in model.commands), 'swdb.dx100_memory_domain')
        model.check(evaluate_predicate(row['predicate'], values), 'postcondition')
        return 'passed', values
    except RuleFailure as error:
        return str(error), values


class PreparationControls(unittest.TestCase):
    def test_exact_source_inventory_hashes(self):
        project = Path(__file__).resolve().parents[4]
        inventory = fixture.source_inventory(project)
        self.assertEqual(len(inventory['declarations']), 27)
        self.assertEqual(len({r['name'] for r in inventory['declarations']}), 26)

    def test_closed_model_components_equal_written_files_and_policy(self):
        folder = Path(__file__).parent
        policy = json.loads((folder / 'integration-policy.json').read_text())
        self.assertEqual(policy, fixture.policy_document())
        for key, text in fixture.components().items():
            filename = {'ghost': 'ghost.acsl', 'state': 'state.h', 'c': 'model.h', 'logic': 'logic.acsl'}[key]
            self.assertEqual((folder / filename).read_text(), text)
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), policy['components'][key])

    def test_no_production_model_import_or_child_runtime_in_preparation(self):
        tree = ast.parse(Path(fixture.__file__).read_text())
        allowed = {'hashlib', 'json', 'pathlib'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue({name.name for name in node.names} <= allowed)
            if isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, allowed)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {'exec', 'eval', 'compile', '__import__'})

    def test_preparation_refuses_other_output_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(fixture.Refused, 'exact owned'):
                fixture.prepare(folder)
            self.assertEqual(list(Path(folder).iterdir()), [])
        project = Path(__file__).resolve().parents[4]
        original = (project / 'library/proof_semantics/dx100_bfs_0_1.yaml').read_bytes()
        with self.assertRaisesRegex(fixture.Refused, 'installed library'):
            fixture.transform({}, project / 'library')
        self.assertEqual((project / 'library/proof_semantics/dx100_bfs_0_1.yaml').read_bytes(), original)

    def test_transform_closes_complete_inventory_and_refuses_every_real_call(self):
        with tempfile.TemporaryDirectory() as folder:
            library = Path(folder) / 'library'
            (library / 'proof_semantics').mkdir(parents=True)
            copied_legacy = library / 'proof_semantics/dx100_bfs_0_1.yaml'
            copied_legacy.write_text('fixture-only placeholder; never parsed or validated\n')
            data = {'hardware_interface': {'gem5_commit': 'e4fc4afdf894f295442cef3604667a469fab8e62'}}
            fixture.transform(data, library)
            self.assertFalse(copied_legacy.exists())
            self.assertEqual(data['id'], fixture.ENTRY)
            self.assertEqual(data['constants'], fixture.CONSTANTS)
            self.assertEqual(len(data['calls']), 26)
            self.assertTrue(all(r['supported'] is False and r['contract'] == fixture.WP_REFUSAL for r in data['calls']))
            self.assertEqual({r['query']: r['prototype'] for r in data['queries']}, fixture.QUERY_PROTOTYPES)
            self.assertTrue(all(r['contract'] == fixture.WP_REFUSAL for r in data['queries']))
            self.assertEqual(len(next(r for r in data['calls'] if r['call'] == 'get_new_reg')['overloads']), 2)
            self.assertNotIn('layout', data['model'])
            self.assertEqual(data['wp'], {})
            assumptions = {r['id'] for r in data['rules'] if r.get('record_assumption') is True}
            self.assertTrue(set(fixture.TRUST) | {'synthetic_trace_scope', 'trace_domain', 'history_visibility'} <= assumptions)

    def test_model_has_exact_scalar_query_definitions_and_no_pointer_or_loop(self):
        model = fixture.model_text()
        for prototype in fixture.QUERY_PROTOTYPES.values():
            self.assertEqual(model.count(prototype + ' {'), 1)
        # Four independently initialized harness cells are the only array reads;
        # all commands/values/history/owners and model locals are scalar.
        for line in model.splitlines():
            if re.match(r'\s+(?:unsigned |long )*int\s+\w+', line):
                self.assertIn('=', line)
        uncommented = re.sub(r'/\*.*?\*/|//[^\n]*', '', model, flags=re.S)
        self.assertEqual(re.findall(r'dx_tile_data\[(\d)\]\[0\]', uncommented), ['0', '1', '2', '3'])
        uncommented = re.sub(r'dx_tile_data\[[0-3]\]\[0\]', 'choice_cell', uncommented)
        self.assertNotRegex(uncommented, r'\b(?:for|while|do|malloc|free|assert)\b|\bint\s*\*|\[[^]]*\]')
        self.assertNotIn('SWDB_ASSUME', model)
        self.assertNotIn('__CPROVER_assume', model)
        self.assertNotIn('swdb_next', model)

    def test_no_expected_value_assumed_and_no_wp_proof_from_queries(self):
        self.assertEqual(fixture.WP_REFUSAL, r'requires \false; assigns \nothing;')
        model = fixture.model_text()
        self.assertIn('"swdb.ghost_capacity"', model)
        self.assertIn('"swdb.dx100_memory_domain"', model)
        self.assertIn('if (write) TR_CHECK(tr_c0_thread != thread', model)
        self.assertIn('tr_c0_result = pick ? tr_c0_later : tr_c0_issue;', model)
        self.assertIn('if (ready) swdb_t28_wait(tile);', model)

    def test_literal_width_and_dispatch_distinction_is_preserved(self):
        model = fixture.model_text()
        self.assertIn('return (bytes == 4 ? 1 : 3) << tile;', model)
        self.assertIn('(access == 1 && tile == tr_c0_tile)', model)
        self.assertNotIn('(access == 1 && (mask & tr_c0_mask)) tr_cover0', model)
        self.assertIn('tr_c0_pending && (tr_c0_mask & mask)) tr_cover0();', model)

    def test_25_expected_fixed_order_trace_outcomes_under_all_choice_bits(self):
        self.assertEqual(len(CASES), 25)
        self.assertEqual(len({row['name'] for row in CASES}), 25)
        for row in CASES:
            with self.subTest(name=row['name']):
                outcomes = [reference_run(row, bits)[0] for bits in itertools.product((0, 1), repeat=3)]
                if row['expected_verdict'] == 'proven':
                    self.assertEqual(set(outcomes), {'passed'})
                else:
                    self.assertIn(row['expected_property'], outcomes)
                    self.assertTrue(set(outcomes) <= {'passed', row['expected_property']})

    def test_history_union_has_two_real_values_and_excludes_old_or_future(self):
        row = next(r for r in CASES if r['name'] == 'history_result_freezes_at_cover')
        values = [reference_run(row, bits)[1] for bits in itertools.product((0, 1), repeat=3)]
        self.assertEqual({v['first'] for v in values}, {7, 11})
        self.assertTrue(all(v['second'] == v['first'] and v['second'] != 13 for v in values))

    def test_fixture_source_has_only_declared_bodyless_query_calls(self):
        for row in CASES:
            text = source(row)
            self.assertEqual(text.count('int trust_fixture(void) {'), 1)
            self.assertEqual(text.count(';\n'), len(fixture.QUERY_PROTOTYPES) + len(row['actions']) + 1)
            self.assertNotIn('#include', text)
            self.assertNotRegex(text, r'\bmaa_|\bwait_ready\s*\(|\bget_tile_ready\s*\(')
            self.assertTrue(set(re.findall(r'\b(swdb_t28_\w+)\s*\(', text)) <= fixture.QUERY_PROTOTYPES.keys())

    def test_reference_capacity_and_domain_failures_are_visible(self):
        model = Reference((0, 0, 0))
        model.claim(0, 0, 4)
        model.issue(0, 1, 0, 0, 0, 4, 0)
        model.cpu_write(1, 0, 1)
        with self.assertRaisesRegex(RuleFailure, 'swdb.ghost_capacity'):
            model.cpu_write(1, 0, 2)
        invalid = Reference(())
        invalid.claim(0, 0, 4)
        with self.assertRaisesRegex(RuleFailure, 'region_footprint_correspondence'):
            invalid.issue(0, 1, 1, 0, 0, 4, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
