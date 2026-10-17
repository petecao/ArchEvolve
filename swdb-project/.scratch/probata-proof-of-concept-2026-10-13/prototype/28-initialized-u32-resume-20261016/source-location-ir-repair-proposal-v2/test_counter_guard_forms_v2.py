"""2026-10-16 ET. Pure closed signed-counter/branch and SourceLoc controls.

The LLVM snippets are synthetic pattern-seam fixtures. The exact diagnostic
LLVM remains on mbit10 and is consumed only by the separately reviewed reader.
"""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / 'source-location-repair-proposal-v1'
SOURCE_SHA = '01c043e544e50c30fc3d92b6be5a8b097f4dfef0606f53c29068a2ba008ac145'
SOURCE = (HERE / 'proposed-source.py').read_bytes()
assert hashlib.sha256(SOURCE).hexdigest() == SOURCE_SHA
SPEC = importlib.util.spec_from_file_location('frozen_source_location_controls', V1 / 'test_source_location_assertions.py')
base_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base_module)


def checker(source):
    tree = ast.parse(source)
    names = {'Refused', '_flow', '_counter_bound_flow'}
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    context = {'re': re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-counter-checker>', 'exec'), context)
    return context


NEW = checker(SOURCE)
OLD = checker((V1 / 'proposed-source.py').read_bytes())


def fixture(profile, canonical=False):
    patterns = []
    rows = []
    if profile == 'bounded':
        signature = 'i32 @synthetic(i32 %0, i32 %1)'
        parameters = ['old', 'data']
        guards = [('late', 'reload', 'bad', 'finish', 3, 4, 5, 6)]
    else:
        signature = 'i32 @synthetic()'
        parameters = []
        guards = [('late_first', 'reload_first', 'bad_first', 'good_first', 1, 2, 3, 4),
                  ('late_second', 'reload_second', 'bad_second', 'good_second', 5, 6, 7, 8)]
    for result, operand, bad, good, load, compare, bad_label, good_label in guards:
        patterns += ['{' + operand + '} = load i32, ptr @REG_count, align 4',
                     '{' + result + '} = icmp sgt i32 {' + operand + '}, 32',
                     'br i1 {' + result + '}, label {' + bad + '}, label {' + good + '}',
                     'LABEL {' + bad + '}', r'tail call void @synthetic_abort\(\)', 'unreachable',
                     'LABEL {' + good + '}']
        predicate, limit = ('slt', 33) if canonical else ('sgt', 32)
        true_label, false_label = (good_label, bad_label) if canonical else (bad_label, good_label)
        rows += [f'%{load} = load i32, ptr @REG_count, align 4',
                 f'%{compare} = icmp {predicate} i32 %{load}, {limit}',
                 f'br i1 %{compare}, label %{true_label}, label %{false_label}',
                 f'{bad_label}:', 'tail call void @synthetic_abort()', 'unreachable', f'{good_label}:']
    patterns += ['ret i32 0']; rows += ['ret i32 0']
    return signature, '\n'.join(rows), patterns, parameters


def run(profile, canonical=False, mutate=None):
    signature, body, patterns, parameters = fixture(profile, canonical)
    if mutate is not None:
        body, patterns = mutate(body, patterns)
    return NEW['_counter_bound_flow'](signature, body, patterns, parameters, profile)


class CounterGuardControls(unittest.TestCase):
    def test_old_refusal_reproduces_then_both_closed_forms_pass(self):
        for profile in ('bounded', 'caller'):
            for canonical in (False, True):
                signature, body, patterns, parameters = fixture(profile, canonical)
                if canonical:
                    with self.assertRaises(OLD['Refused']): OLD['_flow'](signature, body, patterns, parameters)
                else:
                    OLD['_flow'](signature, body, patterns, parameters)
                bindings = run(profile, canonical)
                self.assertIn('late' if profile == 'bounded' else 'late_first', bindings)

    def test_wrong_predicate_constant_or_branch_pair_refuses(self):
        changes = (
            lambda body: body.replace('icmp slt', 'icmp ult'),
            lambda body: body.replace('icmp slt', 'icmp sle'),
            lambda body: body.replace(', 33', ', 32'),
            lambda body: body.replace('icmp slt', 'icmp sgt').replace(', 33', ', 32'),
            lambda body: re.sub(r'(br i1 %\d+, label )(%\d+)(, label )(%\d+)', r'\1\4\3\2', body),
            lambda body: body.replace('icmp slt i32', 'icmp slt i64'),
        )
        for profile in ('bounded', 'caller'):
            for index, change in enumerate(changes):
                with self.subTest(profile=profile, mutation=index):
                    with self.assertRaises(NEW['Refused']): run(profile, True, lambda body, patterns: (change(body), patterns))

    def test_wrong_operand_branch_consumer_or_abort_effect_refuses(self):
        for profile in ('bounded', 'caller'):
            changes = (
                lambda body: re.sub(r'(icmp slt i32 )%\d+', r'\g<1>%99', body),
                lambda body: re.sub(r'br i1 %\d+', 'br i1 %99', body),
                lambda body: body.replace('@synthetic_abort()', '@mutate()'),
                lambda body: body.replace('unreachable', 'ret i32 7'),
                lambda body: body.replace('ret i32 0', 'store i32 7, ptr @REG_count, align 4\nret i32 0'),
            )
            for index, change in enumerate(changes):
                with self.subTest(profile=profile, mutation=index):
                    with self.assertRaises(NEW['Refused']): run(profile, True, lambda body, patterns: (change(body), patterns))

    def test_unique_consumer_check_rejects_even_matching_extra_pattern(self):
        for canonical in (False, True):
            def extra(body, patterns):
                rows = list(patterns)
                rows.insert(-1, '{foreign} = zext i1 {late} to i32')
                return body.replace('ret i32 0', '%99 = zext i1 %4 to i32\nret i32 0'), rows
            with self.assertRaisesRegex(NEW['Refused'], 'one exact branch consumer'):
                run('bounded', canonical, extra)

    def test_mixed_caller_forms_unknown_profile_and_anchor_drift_refuse(self):
        signature, body, patterns, parameters = fixture('caller', True)
        body = body.replace('%2 = icmp slt i32 %1, 33', '%2 = icmp sgt i32 %1, 32').replace(
            'br i1 %2, label %4, label %3', 'br i1 %2, label %3, label %4')
        with self.assertRaises(NEW['Refused']): NEW['_counter_bound_flow'](signature, body, patterns, parameters, 'caller')
        with self.assertRaises(NEW['Refused']): NEW['_counter_bound_flow'](signature, body, patterns, parameters, 'unlisted')
        patterns[1] = patterns[1].replace(', 32', ', 31')
        with self.assertRaises(NEW['Refused']): NEW['_counter_bound_flow'](signature, body, patterns, parameters, 'caller')

    def test_signed_i32_predicate_partition_has_exact_abort_equivalence(self):
        # Integer thresholds partition all signed i32 values into these closed
        # intervals. Comparisons are constant on each interval, so endpoint
        # checks and interval adjacency exhaust this fixed threshold relation.
        partitions = [(-2**31, 32), (33, 2**31 - 1)]
        self.assertEqual(partitions[0][0], -2**31)
        self.assertEqual(partitions[-1][1], 2**31 - 1)
        self.assertEqual(partitions[0][1] + 1, partitions[1][0])
        for lower, upper in partitions:
            for value in (lower, upper):
                self.assertEqual(value > 32, not (value < 33))
                self.assertEqual(value > 32, lower > 32)
                self.assertEqual(value < 33, lower < 33)

    def test_exact_v1_inverse_and_reader_delta(self):
        old = ast.parse((HERE / 'source-location-v1-reviewed.py').read_bytes())
        new = ast.parse(SOURCE)
        old_defs = {node.name: node for node in old.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        new_defs = {node.name: node for node in new.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        self.assertEqual(set(new_defs) - set(old_defs), {'_counter_bound_flow'})
        self.assertEqual({name for name in old_defs if ast.dump(old_defs[name]) != ast.dump(new_defs[name])}, {'_operations'})
        inverse = copy.deepcopy(new_defs['_operations'])
        changed = 0
        for node in ast.walk(inverse):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_counter_bound_flow':
                self.assertEqual(node.args.pop().value, 'bounded' if changed == 0 else 'caller')
                node.func.id = '_flow'; changed += 1
        self.assertEqual(changed, 2)
        self.assertEqual(ast.dump(inverse), ast.dump(old_defs['_operations']))
        outside = lambda tree: ast.dump(ast.Module(body=[node for node in tree.body if not isinstance(node, (ast.FunctionDef, ast.ClassDef))], type_ignores=[]))
        self.assertEqual(outside(old), outside(new))
        reader = (HERE / 'replay_retained_observation_v2.py').read_text()
        reader = reader.replace(SOURCE_SHA, '63d8fff0599d409b7cd89af28d5a52ddc4fd38972057645abc5ede5b9a50237c').replace(
            "'_flow', '_counter_bound_flow', '_operations'", "'_flow', '_operations'").replace(
            "{'_assert_source_location_diagnostics', '_counter_bound_flow'}", "{'_assert_source_location_diagnostics'}")
        self.assertEqual(reader, (V1 / 'replay_retained_observation_v1.py').read_text())


class SourceLocationCombinedControls(base_module.SourceLocationRegression):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new, cls.new_tree = base_module.load_checker(HERE / 'proposed-source.py', True)

    def test_only_assertion_seam_and_token_forwarding_change(self):
        previous = ast.parse((V1 / 'proposed-source.py').read_bytes())
        old = {node.name: node for node in previous.body if isinstance(node, ast.FunctionDef)}
        new = {node.name: node for node in self.new_tree.body if isinstance(node, ast.FunctionDef)}
        for name in ('_assert_source_location_diagnostics', '_assertion', '_bodies'):
            self.assertEqual(ast.dump(old[name]), ast.dump(new[name]))


if __name__ == '__main__': unittest.main(verbosity=2)
