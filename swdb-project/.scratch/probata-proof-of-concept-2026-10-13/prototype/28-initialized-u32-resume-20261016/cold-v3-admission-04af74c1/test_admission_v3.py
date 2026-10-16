"""2026-10-16 ET. Pure source/metadata controls; never run an actual auditor."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
INITIALIZED = HERE.parent
POC = INITIALIZED.parent.parent
COMMIT = '04af74c121a733589fbe1a2087ad602deaef598b'
ROOT_SHA = '832980ed68bdcd9654e82e9e6e33debdf8021054a7e7e03f8dfb794e86754665'
ROOT_BYTES = (POC / 'evidence/t28-initialized-v5-root-execution-20261016.json').read_bytes()
assert len(ROOT_BYTES) == 5623 and hashlib.sha256(ROOT_BYTES).hexdigest() == ROOT_SHA
ROOT = json.loads(ROOT_BYTES)
OLD = (INITIALIZED / 'initialized_cold_audit_v2.py').read_text()
NEW = (HERE / 'initialized_cold_audit_v3.py').read_text()
POLICY = json.loads((HERE / 'initialized-cold-policy-04af74c1-v3.json').read_bytes())


def deny_child(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure controls refuse ' + event)


sys.addaudithook(deny_child)


def namespace():
    tree = ast.parse(NEW)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and
                node.name in ('strict_json', 'validate_original_lane_v3')]
    assert len(selected) == 2
    result = {'json': json, 'SOURCE_COMMIT': COMMIT}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<exact-two-pure-source-nodes>', 'exec'), result)
    return result


class PinnedRoot:
    """Stand-in physical boundary: exact root bytes, not an actual evidence audit."""
    def read(self, row):
        assert row == POLICY['original_root_receipt']
        assert row['bytes'] == len(ROOT_BYTES)
        assert row['sha256'] == hashlib.sha256(ROOT_BYTES).hexdigest()
        return ROOT_BYTES


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.fn = namespace()['validate_original_lane_v3']
        self.lane = copy.deepcopy(ROOT['actual']['lane.json']['socket_lane'])
        self.policy = copy.deepcopy(POLICY)
        self.expected = {'source_commit': COMMIT, 'linux_launch_binding': {'node': 0}}
        self.raw = Path(ROOT['raw_root'])

    def validate(self, **changes):
        args = dict(policy=self.policy, expected=self.expected, raw=self.raw,
                    physical=PinnedRoot(), lane=self.lane)
        args.update(changes)
        return self.fn(**args)

    def test_actual_old_predicate_refuses_new_exact_observation_accepts(self):
        old_tree = ast.parse(OLD)
        launch = next(node for node in old_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'original_launch')
        old_assertion = launch.body[-2]
        self.assertIsInstance(old_assertion, ast.Assert)
        with self.assertRaises(AssertionError):
            exec(compile(ast.Module(body=[old_assertion], type_ignores=[]), '<actual-V2-lane-predicate>', 'exec'),
                 {'lane': self.lane, 'raw': self.raw})
        self.assertIsNone(self.validate())

    def test_exact_inverse_preserves_all_scientific_functions(self):
        old, new = ast.parse(OLD), ast.parse(NEW)
        new.body[0] = old.body[0]
        new.body = [node for node in new.body if not isinstance(node, ast.FunctionDef) or node.name != 'validate_original_lane_v3']
        old_launch = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == 'original_launch')
        new_launch = next(node for node in new.body if isinstance(node, ast.FunctionDef) and node.name == 'original_launch')
        new_launch.body[-2] = old_launch.body[-2]
        self.assertEqual(ast.dump(old, include_attributes=False), ast.dump(new, include_attributes=False))
        for name in ('audit_record', 'workflow', 'initialized_rules', 'semantic_model', 'audit'):
            before = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == name)
            after = next(node for node in new.body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(ast.get_source_segment(OLD, before), ast.get_source_segment(NEW, after))

    def test_job_node_generation_and_command_mutations_refused(self):
        mutations = {'job': self.raw.name, 'lease_generation': 614, 'node': 1,
                     'command': ['bash', str(self.raw / 'run.sh')], 'exit_code': 1,
                     'host': 'another-host', 'ended_utc': '2026-10-16T19:47:38Z'}
        for key, value in mutations.items():
            with self.subTest(key=key), self.assertRaises(AssertionError):
                lane = copy.deepcopy(self.lane); lane[key] = value
                policy = copy.deepcopy(self.policy); policy['settled_lane'] = lane
                self.validate(lane=lane, policy=policy)

    def test_raw_source_and_expected_node_mutations_refused(self):
        for raw in (Path(str(self.raw) + '-other'), Path(str(self.raw).replace('04af74c1', '2baf722f'))):
            with self.subTest(raw=raw), self.assertRaises(AssertionError):
                self.validate(raw=raw)
        for expected in ({'source_commit': '0' * 40, 'linux_launch_binding': {'node': 0}},
                         {'source_commit': COMMIT, 'linux_launch_binding': {'node': 1}}):
            with self.subTest(expected=expected), self.assertRaises(AssertionError):
                self.validate(expected=expected)

    def test_unpinned_root_receipt_rejected(self):
        for key, value in (('bytes', 5624), ('sha256', '0' * 64), ('path', '/other/receipt.json')):
            policy = copy.deepcopy(self.policy); policy['original_root_receipt'][key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError):
                self.validate(policy=policy)
        class MutatedRoot(PinnedRoot):
            def read(self, row):
                bad = copy.deepcopy(ROOT); bad['actual']['lane.json']['socket_lane']['lease_generation'] += 1
                return json.dumps(bad).encode()
        with self.assertRaises(AssertionError):
            self.validate(physical=MutatedRoot())

    def test_filled_policy_keeps_exact_records_and_complete_census(self):
        self.assertEqual([row['expected_result'] for row in POLICY['records']], [711, 1107])
        for index, row in enumerate(POLICY['records']):
            self.assertEqual(row['record'], ROOT['records'][index]['pin'])
            self.assertEqual(row['id'], ROOT['records'][index]['id'])
        self.assertEqual([row['verdict'] for row in ROOT['records']], ['proven', 'not_proven'])
        self.assertEqual(ROOT['records'][1]['failure_class'], 'timeout')
        self.assertEqual(ROOT['records'][1]['ordinary_goals'], {'valid': 22, 'timeout': 1})
        manifest = POLICY['raw_manifest']
        self.assertEqual(len(manifest['files']), 184)
        self.assertEqual(sum(row['bytes'] for row in manifest['files'].values()), 62761931)
        for row in POLICY['records']:
            key = str(Path(row['record']['path']).relative_to(POLICY['raw']))
            self.assertEqual(manifest['files'][key], {k: row['record'][k] for k in ('bytes', 'sha256')})

    def test_explicit_startup_command_and_all_staged_bytes(self):
        command = json.loads((HERE / 'initialized-cold-command-04af74c1-v3.json').read_bytes())
        argv = command['command']
        self.assertEqual(argv[1:4], ['-I', '-B', '-X'])
        self.assertEqual(argv[4], 'pycache_prefix=' + POLICY['reader_admission']['pycache_prefix'])
        self.assertEqual(argv[-1], hashlib.sha256((HERE / 'initialized-cold-policy-04af74c1-v3.json').read_bytes()).hexdigest())
        self.assertEqual(len(command['control_files']), 10)
        self.assertLess(command['control_total_bytes'], 1048576)
        self.assertEqual(set(POLICY['reader_admission']['environment']), {'PYTHONPATH', 'PYTHONPYCACHEPREFIX',
            'PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE', 'PYTHONSAFEPATH', 'SETUPTOOLS_USE_DISTUTILS'})
        self.assertEqual(POLICY['reader_admission']['environment']['PYTHONDONTWRITEBYTECODE'], '1')
        self.assertNotEqual(POLICY['reader_admission']['environment']['PYTHONPYCACHEPREFIX'],
                            POLICY['reader_admission']['pycache_prefix'])
        for name, row in command['control_files'].items():
            candidates = [HERE / name, INITIALIZED / name,
                          INITIALIZED.parent / '28-public-memory-trace-resume-20261016' / name,
                          POC / 'evidence' / name]
            paths = [path for path in candidates if path.is_file()]
            self.assertEqual(len(paths), 1, name)
            data = paths[0].read_bytes()
            self.assertEqual({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()},
                             {key: row[key] for key in ('bytes', 'sha256')})


if __name__ == '__main__':
    unittest.main(verbosity=2)
