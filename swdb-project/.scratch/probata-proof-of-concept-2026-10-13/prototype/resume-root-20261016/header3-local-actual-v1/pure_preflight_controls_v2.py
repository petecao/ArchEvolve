"""2026-10-16 ET. Pure synthetic guard controls; no remote/tool invocation."""
from pathlib import Path
import ast
import hashlib
import json
import types
import unittest

HERE = Path(__file__).resolve().parent
DELTA = json.loads((HERE/'preflight-delta-v2.json').read_text())
BLOCK = compile(DELTA['inverse']['new'], '<exact-v2-wrapper-gate>', 'exec')
HASHES = ['00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8',
          '50745f827bac2a3db4fc56fdedc95f6fb57fb4b39cf9b269796c77c0274dc996']
PATHS = ['AgenticRefiner/scripts/host/socket_lane.sh', 'AgenticRefiner/scripts/host/hostlock.sh']


def gate(mutation=None):
    physical = {p: (p+'\n').encode() for p in PATHS}
    blobs = {(revision, p): b for p, b in physical.items() for revision in ('HEAD', 'FETCH_HEAD')}
    refs = {'HEAD': '76cca359136794afa5ede975cfac8293cfa2ab9a',
            'FETCH_HEAD': '41f22f0ba765adcd4f4188aca91009ea0fe5a22b'}
    status = ''
    if mutation == 'head': refs['HEAD'] = '0'*40
    if mutation == 'fetched': refs['FETCH_HEAD'] = '0'*40
    if mutation == 'dirty': status = ' M '+PATHS[0]
    if mutation in ('socket', 'hostlock'):
        physical[PATHS[mutation == 'hostlock']] += b'changed'
    if mutation in ('headblob', 'fetchedblob', 'trailing'):
        revision = 'FETCH_HEAD' if mutation == 'fetchedblob' else 'HEAD'
        blobs[(revision, PATHS[0])] += b'\n' if mutation == 'trailing' else b'changed'
    root = Path('/exact/synthetic/lane')
    def read(path): return physical[str(path.relative_to(root))]
    def git(control, *args):
        assert control == root
        return refs[args[1]] if args[0] == 'rev-parse' else status
    def check_output(argv, *, env, timeout):
        assert argv[:-1] == ['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
            '-c', 'core.fsmonitor=false', '-c', 'core.preloadIndex=false', '-c', 'index.threads=1',
            '-C', str(root), 'show']
        assert env == {'synthetic': 'closed'} and timeout == 10
        revision, relative = argv[-1].split(':', 1)
        return blobs[(revision, relative)]
    def sha(data):
        for i, path in enumerate(PATHS):
            if data == (path+'\n').encode(): return types.SimpleNamespace(hexdigest=lambda: HASHES[i])
        return types.SimpleNamespace(hexdigest=lambda: 'f'*64)
    scope = {'control': root, 'read': read, 'git': git, 'env': {'synthetic': 'closed'},
             'hashlib': types.SimpleNamespace(sha256=sha),
             'subprocess': types.SimpleNamespace(check_output=check_output)}
    exec(BLOCK, scope)
    return scope


class Controls(unittest.TestCase):
    def test_exact_observed_metadata_admits(self):
        self.assertEqual(gate()['wrapper_commit'], '76cca359136794afa5ede975cfac8293cfa2ab9a')
    def test_refuses_each_changed_binding(self):
        for mutation in ('head', 'fetched', 'dirty', 'socket', 'hostlock', 'headblob', 'fetchedblob', 'trailing'):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): gate(mutation)
    def test_full_preflight_inverse_and_original_scanner_bodies(self):
        old = (HERE/'scoped-preflight-v1.py').read_text()
        new = (HERE/'scoped-preflight-v2.py').read_text()
        self.assertEqual(new.replace(DELTA['inverse']['new'], DELTA['inverse']['old']), old)
        def bodies(text):
            return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(text).body
                    if isinstance(node, ast.FunctionDef)}
        a, b = bodies(old), bodies(new)
        for name in ('read', 'pam_identity', 'transport_identity', 'scan'):
            self.assertEqual(a[name], b[name])
    def test_runner_only_declared_inverse(self):
        old = (HERE/'dispatch_once.py').read_text()
        new = (HERE/'dispatch_once_v2.py').read_text()
        reverse = new.replace("PREFIX = 't25-owned-swap-header3-public-v1-attempt2-'", "PREFIX = 't25-owned-swap-header3-public-v1-'")
        reverse = reverse.replace("HERE/'scoped-preflight-v2.py'", "HERE/'scoped-preflight-v1.py'")
        reverse = reverse.replace(DELTA['successor_preflight']['sha256'], DELTA['original_preflight']['sha256'])
        self.assertEqual(reverse, old)

if __name__ == '__main__':
    unittest.main()
