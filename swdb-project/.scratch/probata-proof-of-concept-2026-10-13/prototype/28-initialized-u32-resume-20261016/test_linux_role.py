"""2026-10-16 ET. Pure Linux launch-receipt seam; no kernel/tool execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('pure launch control refuses ' + event)


sys.addaudithook(deny)
ENTRY = Path(__file__).with_name('linux_pair_entry_v1.py')
tree = ast.parse(ENTRY.read_bytes())
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {'pin', 'validate_linux_launch'}]
assert len(functions) == 2
context = {'Path': Path, 'pathlib': __import__('pathlib'), 'hashlib': hashlib, 'json': json}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(ENTRY), 'exec'), context)
validate = context['validate_linux_launch']


class LinuxRoleTests(unittest.TestCase):
    def observe(self, mutation=None):
        with tempfile.TemporaryDirectory(prefix='probata-resume-20261016-t28-linux-role-') as directory:
            base = Path(directory).resolve(); raw = base / 'raw'; raw.mkdir(); controls = raw / 'control'; controls.mkdir()
            repository = base / 'source'; repository.mkdir()
            controller = controls / 'linux_pair_entry_v1.py'; controller.write_text('# INERT DATA ONLY\n')
            policy = controls / 'policy.json'; policy.write_text('{}\n')
            wrappers = {}
            for name in ('execute.py', 'watch.py'):
                path = raw / name; path.write_text('# INERT WRAPPER DATA ONLY\n'); wrappers[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            source = '2baf722fdaa6cba24b859eae3172a6f597417d72'
            expected = {'source_commit': source, 'tools': {'opam': {'path': '/selected/opam'}},
                        'linux_launch_binding': {'entry_sha256': hashlib.sha256(controller.read_bytes()).hexdigest(),
                                                 'python': '/selected/python', 'wrappers': wrappers, 'node': 1}}
            digest = hashlib.sha256(policy.read_bytes()).hexdigest()
            command = ['/selected/opam', 'exec', '--switch=framac-33', '--', '/selected/python', '-I', '-B',
                       str(controller), str(repository / 'swdb-project'), str(raw), str(policy), digest]
            launch = {'source': str(repository), 'source_commit': source, 'rss_cap_bytes': 8589934592,
                      'workers': 1, 'timeout_seconds': 1200, 'node': 1, 'command': command, 'reviewed_wrapper_reuse': dict(wrappers)}
            environment = {'PROBATA_OUTPUT': str(raw), 'SWDB_VERIFIER_LOCK': str(raw / 'verifier.lock'),
                           'SWDB_VERIFIER_RSS_CAP_BYTES': '8589934592'}
            if mutation == 'source': launch['source'] = str(base / 'other')
            elif mutation == 'commit': launch['source_commit'] = '0' * 40
            elif mutation == 'rss': launch['rss_cap_bytes'] = 1024
            elif mutation == 'workers': launch['workers'] = 2
            elif mutation == 'timeout': launch['timeout_seconds'] = 1199
            elif mutation == 'node': launch['node'] = 0
            elif mutation == 'command': command[4] = '/unbound/python'
            elif mutation == 'isolation': command[5] = '-O'
            elif mutation == 'policy_binding': command[-1] = '0' * 64
            elif mutation == 'entry_bytes': controller.write_text('# changed\n')
            elif mutation == 'wrapper_bytes': (raw / 'watch.py').write_text('# changed\n')
            elif mutation == 'wrapper_receipt': launch['reviewed_wrapper_reuse']['watch.py'] = '0' * 64
            elif mutation == 'output_marker': environment['PROBATA_OUTPUT'] = str(base / 'other')
            elif mutation == 'lock_marker': environment['SWDB_VERIFIER_LOCK'] = str(base / 'other.lock')
            elif mutation == 'cap_marker': environment['SWDB_VERIFIER_RSS_CAP_BYTES'] = '1024'
            (raw / 'launch.json').write_text(json.dumps(launch))
            return validate(expected, repository, raw, policy, digest, controller, environment)

    def test_exact_linux_receipt_has_distinct_scope(self):
        receipt = self.observe()
        self.assertFalse(receipt['Mac_counted_token_required'])
        self.assertEqual(receipt['whole_seconds'], 1200)
        self.assertEqual(receipt['rss_cap_bytes'], 8589934592)
        self.assertEqual(receipt['workers'], 1)

    def test_every_unbound_source_guard_or_command_refuses(self):
        for mutation in ('source', 'commit', 'rss', 'workers', 'timeout', 'node', 'command', 'isolation',
                         'policy_binding', 'entry_bytes', 'wrapper_bytes', 'wrapper_receipt',
                         'output_marker', 'lock_marker', 'cap_marker'):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): self.observe(mutation)


if __name__ == '__main__':
    unittest.main()
