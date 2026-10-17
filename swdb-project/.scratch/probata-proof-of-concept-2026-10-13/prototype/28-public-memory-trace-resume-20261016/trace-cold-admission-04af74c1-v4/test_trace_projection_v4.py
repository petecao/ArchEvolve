"""2026-10-16 ET. Retained scalar flags/source/inverse controls, no actual audit."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
PROJECT = TRACE.parents[3]
V3 = TRACE / 'trace-cold-admission-04af74c1-v3'
OLD = (V3 / 'trace_cold_audit_v3.py').read_text()
NEW = (HERE / 'trace_cold_audit_v4.py').read_text()
OLD_ASSIGNMENT = "flags = ['-DSWDB_CBMC', '--unwind', '1', *identities['frozen']]"
NEW_ASSIGNMENT = "flags = model_unwind_flags_v4(settings, identities['frozen'], entry['constants'], (fixture / 'library/proof_semantics/synthetic-memory-trace/model.h').read_text(), project)"
H = lambda raw: hashlib.sha256(raw).hexdigest()
assert H(OLD.encode()) == 'a323298395677ed638d1e92a53fd0d386f54cab5eb815c266d8cdd1d3aff63aa'
META_RAW = (V3 / 'retained-trace-flags-metadata-20261016.json').read_bytes()
assert H(META_RAW) == '157305bff9221f169ff2a103f6bbfe3b06e30900b8babcda746ab29d11f0abb3'
METADATA = json.loads(META_RAW)
PROJECTION = next(iter(METADATA['groups'].values()))['projection']
MODEL = (TRACE / 'model.h').read_text()
CONSTANTS = {'DX_K': 2, 'DX_NT': 4, 'DX_NR': 1, 'DX_NM': 2, 'DX_TS': 1}
FROZEN = ['--unwinding-assertions', '--pointer-overflow-check']


def deny(event, _arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {'os.system', 'os.fork', 'os.forkpty'}:
        raise RuntimeError('trace projection controls refuse ' + event)


sys.addaudithook(deny)
NEW_NODES = [node for node in ast.parse(NEW).body if
    isinstance(node, ast.FunctionDef) and node.name in {'validated_model_flags_v4', 'model_unwind_flags_v4'} or
    isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'TRACE_LOOP_IDS_V4' for target in node.targets)]
assert len(NEW_NODES) == 3
NS = {'ast': ast, 're': re, 'types': types, 'H': H}
exec(compile(ast.Module(body=NEW_NODES, type_ignores=[]), '<exact-v4-flags-helpers-only>', 'exec'), NS)


def settings():
    return {'flags': list(PROJECTION['actual_settings_flags']), 'unwind': PROJECTION['actual_unwind'],
            'array_length': PROJECTION['actual_array_length']}


class ReadOnlyModelFixture:
    """Only supplies the checked model source at the exact audit assignment seam."""
    def __init__(self, relative=''):
        self.relative = relative

    def __truediv__(self, relative):
        return ReadOnlyModelFixture(self.relative + relative)

    def read_text(self):
        assert self.relative == 'library/proof_semantics/synthetic-memory-trace/model.h'
        assert H(MODEL.encode()) == '2fe44f7fea203d1f7914db6077b999d03f64a2e43472bd2884eb8e534e775be8'
        return MODEL


class Controls(unittest.TestCase):
    def test_01_exact_actual_assignment_and_original_assertion_red_green(self):
        old_record = next(node for node in ast.parse(OLD).body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
        new_record = next(node for node in ast.parse(NEW).body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
        def slice_at_flags(node):
            index = next(index for index, child in enumerate(node.body) if isinstance(child, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'flags' for target in child.targets))
            self.assertIsInstance(node.body[index + 1], ast.Assert)
            return node.body[index:index + 2]
        old_seam, new_seam = slice_at_flags(old_record), slice_at_flags(new_record)
        self.assertEqual(ast.dump(old_seam[1]), ast.dump(new_seam[1]))
        namespace = {**NS, 'settings': settings(), 'identities': {'frozen': FROZEN},
            'entry': {'constants': CONSTANTS}, 'fixture': ReadOnlyModelFixture(), 'project': PROJECT}
        with self.assertRaises(AssertionError):
            exec(compile(ast.Module(body=old_seam, type_ignores=[]), '<old-actual-flags-seam-red>', 'exec'), namespace)
        exec(compile(ast.Module(body=new_seam, type_ignores=[]), '<new-actual-flags-seam-green>', 'exec'), namespace)
        self.assertEqual(namespace['flags'], PROJECTION['actual_settings_flags'])

    def test_02_all_25_retained_projections_and_exact_35_selector_order(self):
        self.assertEqual(len(METADATA['cases']), 25)
        self.assertEqual(len(METADATA['groups']), 1)
        group_sha, group = next(iter(METADATA['groups'].items()))
        self.assertEqual(H(json.dumps(group['projection'], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()), group_sha)
        self.assertEqual([row['case'] for row in METADATA['cases']], group['cases'])
        self.assertTrue(all(row['projection_sha256'] == group_sha for row in METADATA['cases']))
        selected = PROJECTION['actual_settings_flags'][-1].split(',')
        self.assertEqual(len(selected), 35)
        self.assertEqual([item.rsplit(':', 1)[0] for item in selected], list(NS['TRACE_LOOP_IDS_V4']))
        self.assertEqual({item.rsplit(':', 1)[1] for item in selected}, {'5'})

    def test_03_exact_pinned_producer_function_selection_and_bound(self):
        policy_raw = (TRACE / 'linux_trace_policy_04af74c1_v4.json').read_bytes()
        self.assertEqual(H(policy_raw), 'd61807f5595e77aabdbd054b6f00caff636775f07ab697f368af8f87864241de')
        policy = json.loads(policy_raw)
        for name in ('swdb/cbmc_adapter.py', 'swdb/proof_semantics.py'):
            self.assertEqual(H((PROJECT / name).read_bytes()), policy['source_files'][name])
        flags = NS['model_unwind_flags_v4'](settings(), FROZEN, CONSTANTS, MODEL, PROJECT)
        self.assertEqual(flags, PROJECTION['actual_settings_flags'])
        proof = ast.parse((PROJECT / 'swdb/proof_semantics.py').read_bytes())
        model_for = next(node for node in proof.body if isinstance(node, ast.FunctionDef) and node.name == 'model_for')
        assignments = [node for node in model_for.body if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'functions', 'unwind'}]
        context = {'re': re, 'model': MODEL, 'constants': CONSTANTS}
        exec(compile(ast.Module(body=assignments, type_ignores=[]), '<independent-exact-model-assignments>', 'exec'), context)
        self.assertEqual(context['unwind'], 5)
        self.assertTrue(all(loop.rsplit('.', 1)[0] in context['functions'] for loop in NS['TRACE_LOOP_IDS_V4']))

    def test_04_missing_changed_reordered_or_extra_loop_flags_refuse(self):
        original = settings()
        loop_items = original['flags'][-1].split(',')
        candidates = [loop_items[:-1], [*reversed(loop_items)], [loop_items[0], *loop_items],
            [loop_items[0].replace('tr_thread', 'other_function'), *loop_items[1:]],
            [loop_items[0].replace(':5', ':6'), *loop_items[1:]]]
        for items in candidates:
            observed = copy.deepcopy(original); observed['flags'][-1] = ','.join(items)
            with self.assertRaises(AssertionError):
                NS['model_unwind_flags_v4'](observed, FROZEN, CONSTANTS, MODEL, PROJECT)
        for flags in (original['flags'][:-2], original['flags'] + ['--no-unwinding-assertions'],
                      [flag for flag in original['flags'] if flag != '--unwinding-assertions']):
            with self.assertRaises(AssertionError):
                NS['model_unwind_flags_v4'](dict(original, flags=flags), FROZEN, CONSTANTS, MODEL, PROJECT)

    def test_05_model_function_membership_derived_bound_and_mandatory_flags_refuse(self):
        selected = list(NS['TRACE_LOOP_IDS_V4'])
        functions = sorted({loop.rsplit('.', 1)[0] for loop in selected})
        with self.assertRaises(AssertionError):
            NS['validated_model_flags_v4'](settings(), FROZEN, [f for f in functions if f != 'tr_thread'], 5, selected)
        for bound in (4, 6, True, '5'):
            with self.assertRaises(AssertionError):
                NS['validated_model_flags_v4'](settings(), FROZEN, functions, bound, selected)
        with self.assertRaises(AssertionError):
            NS['model_unwind_flags_v4'](settings(), FROZEN, dict(CONSTANTS, DX_NT=5), MODEL, PROJECT)
        with self.assertRaises(AssertionError):
            NS['model_unwind_flags_v4'](settings(), FROZEN, CONSTANTS, MODEL.replace('tr_thread(', 'other_function('), PROJECT)
        for frozen in ([], FROZEN[:1], list(reversed(FROZEN)), FROZEN + ['--extra']):
            with self.assertRaises(AssertionError):
                NS['model_unwind_flags_v4'](settings(), frozen, CONSTANTS, MODEL, PROJECT)
        for field, value in (('unwind', 2), ('array_length', 1), ('unwind', True), ('array_length', False)):
            with self.assertRaises(AssertionError):
                NS['model_unwind_flags_v4'](dict(settings(), **{field: value}), FROZEN, CONSTANTS, MODEL, PROJECT)

    def test_06_full_source_inverse_and_every_other_audit_function_unchanged(self):
        tree = ast.parse(NEW)
        start = next(node.lineno for node in NEW_NODES)
        end = max(node.end_lineno for node in NEW_NODES)
        helper_text = '\n'.join(NEW.splitlines()[start - 1:end])
        self.assertEqual(NEW.replace(helper_text + '\n\n\n\n', '', 1).replace(NEW_ASSIGNMENT, OLD_ASSIGNMENT, 1), OLD)
        for before in ast.parse(OLD).body:
            if isinstance(before, (ast.FunctionDef, ast.ClassDef)) and before.name != 'audit_record':
                after = next(node for node in tree.body if isinstance(node, type(before)) and node.name == before.name)
                self.assertEqual(ast.get_source_segment(OLD, before), ast.get_source_segment(NEW, after))
        old_record = next(node for node in ast.parse(OLD).body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
        new_record = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
        self.assertEqual(ast.get_source_segment(NEW, new_record).replace(NEW_ASSIGNMENT, OLD_ASSIGNMENT), ast.get_source_segment(OLD, old_record))

    def test_07_policy_inverse_and_exact_closed_19_control_command(self):
        old = json.loads((V3 / 'trace-cold-policy-04af74c1-v3.json').read_bytes())
        new = json.loads((HERE / 'trace-cold-policy-04af74c1-v4.json').read_bytes())
        def undo(value):
            if isinstance(value, dict): return {key: undo(item) for key, item in value.items()}
            if isinstance(value, list): return [undo(item) for item in value]
            if isinstance(value, str): return value.replace('trace-cold-04af74c1-v4', 'trace-cold-04af74c1-v3')
            return value
        inverse = undo(new); inverse['reader_sha256'] = old['reader_sha256']; inverse['provenance'].pop('model_unwind_projection_v4')
        self.assertEqual(inverse, old)
        command = json.loads((HERE / 'trace-cold-command-04af74c1-v4.json').read_bytes())
        manifest = json.loads((HERE / 'trace-cold-control-manifest-v4.json').read_bytes())
        self.assertEqual(command['control_file_count'], 19)
        self.assertEqual(manifest['payload_file_count'], 18)
        self.assertEqual(manifest['expected_control_basenames'], sorted(command['control_files']))
        self.assertLess(command['control_total_bytes'], 1048576)
        self.assertEqual(command['control_total_bytes'], sum(row['bytes'] for row in command['control_files'].values()))
        for row in command['control_files'].values():
            raw = Path(row['source']).read_bytes()
            self.assertEqual(len(raw), row['bytes']); self.assertEqual(H(raw), row['sha256'])
        self.assertEqual(command['command'][-1], H((HERE / 'trace-cold-policy-04af74c1-v4.json').read_bytes()))
        old_command = json.loads((V3 / 'trace-cold-command-04af74c1-v3.json').read_bytes())
        command_inverse = undo(command)
        for name in ('trace_cold_audit_v4.py', 'trace-cold-policy-04af74c1-v4.json', 'trace-cold-control-manifest-v4.json',
                     'retained-trace-flags-metadata-20261016.json', 'trace-cold-v3-actual-refusal-receipt-20261016.json'):
            command_inverse['control_files'].pop(name)
        for name in ('trace_cold_audit_v3.py', 'trace-cold-policy-04af74c1-v3.json', 'trace-cold-control-manifest-v3.json'):
            command_inverse['control_files'][name] = old_command['control_files'][name]
        command_inverse['command'][-3:] = old_command['command'][-3:]
        for key in ('control_file_count', 'control_total_bytes', 'status'):
            command_inverse[key] = old_command[key]
        self.assertEqual(command_inverse, old_command)
        self.assertEqual(set(command['process_environment']), {'PATH', 'LANG', 'LC_ALL', 'PYTHONPATH', 'PYTHONPYCACHEPREFIX', 'PYTHONDONTWRITEBYTECODE'})

    def test_08_refusal_and_predecessor_staging_preserved_no_probe_or_rerun(self):
        self.assertEqual(H((V3 / 'trace-cold-v3-actual-refusal-receipt-20261016.json').read_bytes()),
            '98c7e00af83f4383611e78614183d440c4434f1ab173e24fd67b44702ecd9ce4')
        v2 = TRACE / 'trace-cold-admission-04af74c1-v2'
        self.assertEqual(H((v2 / 'staging-receipt-20261016.json').read_bytes()), 'e1a75dc16afdcde062cf79910b3fbf1adfb727d5e7a24a506e5a1db9f78cc42a')
        for node in NEW_NODES:
            for child in ast.walk(node):
                self.assertNotIsInstance(child, (ast.Import, ast.ImportFrom))
                if isinstance(child, ast.Attribute):
                    self.assertNotIn(child.attr, {'run', 'Popen', 'system', 'write_bytes', 'write_text'})
        self.assertIn('There is no retained --show-loops stdout', NEW)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date': '2026-10-16 ET', 'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skips': len(result.skipped), 'actual_reader_or_scientific_execution': False}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
