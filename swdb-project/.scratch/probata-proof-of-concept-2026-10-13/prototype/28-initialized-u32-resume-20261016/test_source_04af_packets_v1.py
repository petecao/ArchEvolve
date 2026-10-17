"""2026-10-16 ET. Pure source rebind/inverse controls; no tools or children."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent / '28-public-memory-trace-resume-20261016'
SOURCE = '04af74c121a733589fbe1a2087ad602deaef598b'
PROJECT = '/data1/yanruj/probata-resume-20261016-04af74c1/swdb-project'
EVENTS = []


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.')) or event in {'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('pure source-binding controls refuse ' + event)


sys.addaudithook(deny)


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FreshSourcePackets(unittest.TestCase):
    def test_pair_inverse_changes_only_source_policy_binding(self):
        old = load(HERE / 'linux_pair_policy_2baf722f_v4.json')
        new = load(HERE / 'linux_pair_policy_04af74c1_v5.json')
        self.assertEqual(new['source_commit'], SOURCE)
        self.assertEqual(new['startup_roles']['source_project'], PROJECT)
        self.assertEqual(new['runtime_controller_version'], 4)
        self.assertEqual(set(old['source_files']), set(new['source_files']))
        self.assertEqual(set(old['source_consumer_trees']), set(new['source_consumer_trees']))
        self.assertEqual(new['source_files']['swdb/dx100_initialized_register_source.py'],
                         '01c043e544e50c30fc3d92b6be5a8b097f4dfef0606f53c29068a2ba008ac145')
        inverse = copy.deepcopy(new)
        for key in ('source_commit', 'raw_name', 'source_files', 'source_consumer_trees'): inverse[key] = old[key]
        inverse['startup_roles']['source_project'] = old['startup_roles']['source_project']
        self.assertEqual(inverse, old)

    def test_trace_inverse_keeps_all25_criteria_and_complete_runtime(self):
        old = load(TRACE / 'linux_trace_policy_57c22ba6_v2.json')
        new = load(TRACE / 'linux_trace_policy_04af74c1_v3.json')
        self.assertEqual(new['source_commit'], SOURCE)
        self.assertEqual(new['source_root'], PROJECT)
        self.assertEqual(new['python_startup_roles_v2']['source_project'], PROJECT)
        self.assertLessEqual(set(old['source_files']), set(new['source_files']))
        packet = str(TRACE.relative_to(HERE.parents[3])) + '/'
        self.assertTrue(all(name.startswith(packet) for name in set(new['source_files']) - set(old['source_files'])))
        self.assertFalse(any(name.startswith('records/') for name in new['source_files']))
        self.assertEqual(new['source_files']['tests/testkit/dx100_trust.py'],
                         '4d55a093a7a92eeb57c9878760bc48ae71c6d5683bbdbf50760be15997cb0982')
        inverse = copy.deepcopy(new)
        for key in ('source_commit', 'source_root', 'raw_name', 'source_files', 'source_consumer_trees', 'status'): inverse[key] = old[key]
        inverse['python_startup_roles_v2']['source_project'] = old['python_startup_roles_v2']['source_project']
        self.assertEqual(inverse, old)

    def test_exact_command_source_lane_budget_and_staging(self):
        profiles = ((HERE, 'linux_pair_policy_04af74c1_v5.json', 'linux_pair_command_04af74c1_v5.json',
                     'linux_pair_entry_v4.py', '9a6246962ed8288829b609711c2fc3d77f436b9411de5bbad58148937895bf6d', 0, 6),
                    (TRACE, 'linux_trace_policy_04af74c1_v3.json', 'linux_trace_command_04af74c1_v3.json',
                     'linux_trace_entry_v2.py', 'd319185131bd708c57229fe16e269da6e6298d1afba3c057a8fcc0f89aa43c93', 1, 9))
        for root, policy_name, command_name, entry_name, entry_sha, node, count in profiles:
            with self.subTest(profile=command_name):
                policy = load(root / policy_name); command = load(root / command_name)
                self.assertEqual(command['source_commit'], SOURCE)
                self.assertEqual(command['source'], PROJECT)
                self.assertEqual(command['node'], node)
                self.assertIn('04af74c1', command['raw_root'])
                self.assertEqual(command['argv'][7:], [command['raw_root'] + '/control/' + entry_name, PROJECT,
                    command['raw_root'], command['raw_root'] + '/control/' + policy_name, sha(root / policy_name)])
                self.assertEqual(sha(root / entry_name), entry_sha)
                self.assertEqual(command['root_guard']['whole_tree_seconds'], 1200)
                self.assertEqual(command['root_guard']['rss_cap_bytes'], 8589934592)
                self.assertEqual(command['root_guard']['workers'], 1)
                rows = command['controller_inputs']
                self.assertEqual(len(rows), count)
                self.assertEqual(len({row['name'] for row in rows}), count)
                self.assertLessEqual(sum(row['bytes'] for row in rows), 1048576)
                for row in rows:
                    path = Path(row['path'])
                    self.assertFalse(path.is_symlink())
                    self.assertEqual(path.stat().st_size, row['bytes'])
                    self.assertEqual(sha(path), row['sha256'])
                self.assertIs(command['proof_acceptance'], False)
                self.assertIs(command.get('actual_launched', command.get('actual_pair_launched')), False)

    def test_author_staging_refuses_changed_or_unlisted_helper_before_packet(self):
        path = HERE / 'prepare_source_04af_packets_v1.py'
        tree = ast.parse(path.read_bytes())
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {'sha', 'read', 'staged'}]
        namespace = {'hashlib': hashlib}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('entry.py', 'policy.json', 'helper.py')]
            for item in paths: item.write_text('inert')
            wanted = {'helper.py': {'bytes': 5, 'sha256': sha(paths[2])}}
            self.assertEqual(len(namespace['staged'](paths, wanted)), 3)
            paths[2].write_text('changed')
            with self.assertRaisesRegex(ValueError, 'helper bytes'): namespace['staged'](paths, wanted)
            paths[2].write_text('inert')
            with self.assertRaisesRegex(ValueError, 'helper membership'): namespace['staged'](paths, {})

    def test_original_health_answers_and_no_child_events(self):
        old = load(HERE / 'linux_pair_policy_2baf722f_v4.json')
        new = load(HERE / 'linux_pair_policy_04af74c1_v5.json')
        self.assertEqual(old['actual_initialized_lineup'], new['actual_initialized_lineup'])
        self.assertEqual(old['compiler_selector_normalization'], new['compiler_selector_normalization'])
        self.assertEqual(old['reporter'], new['reporter'])
        self.assertEqual(EVENTS, [])


if __name__ == '__main__': unittest.main(verbosity=2)
