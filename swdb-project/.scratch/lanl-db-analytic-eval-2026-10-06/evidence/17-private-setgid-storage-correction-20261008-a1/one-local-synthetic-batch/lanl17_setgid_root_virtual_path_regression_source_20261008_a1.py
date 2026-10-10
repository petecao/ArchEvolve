"""SOURCE ONLY / NOT RUN: virtual paths only; no guard main, OS/Git/SSH actions."""
import ast
import hashlib
from pathlib import Path, PurePosixPath
import stat
import types
import unittest

OLD_SOURCE = Path('/private/tmp/lanl_consumed_detached_source_guard_r4_20261008_r3.py')
OLD_BYTES = 88521
OLD_SHA = '96e033426d492fab3be2a07757ab1e89665a7a67d0f06d3941f274b1214dd294'
NEW_SOURCE = Path('/private/tmp/lanl_consumed_detached_source_guard_r5_20261008_a1.py')
NEW_BYTES = 88872
NEW_SHA = 'a84dc9ca7ccd20e6485cc8e9a2007b3b982fad9c5ae19dacbb1f164d664748cb'
UID = 114316761
BASE_TEXT = '/data1/yanruj'
EV_TEXT = BASE_TEXT + '/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence'
MODEL_TEXT = BASE_TEXT + '/DX100-bfs-e4fc4af'
BASELINE_TEXT = BASE_TEXT + '/EvolveSWDB_sources/baseline-fixture'

class VirtualPath:
    """Closed in-memory pathname/stat model; never touches a real remote path."""
    rows = {}
    def __init__(self, value):
        self.value = PurePosixPath(str(value))
    def __str__(self): return str(self.value)
    def __hash__(self): return hash(self.value)
    def __eq__(self, other): return isinstance(other, VirtualPath) and self.value == other.value
    def __truediv__(self, value): return VirtualPath(self.value / str(value))
    @property
    def name(self): return self.value.name
    @property
    def parts(self): return self.value.parts
    @property
    def parent(self): return VirtualPath(self.value.parent)
    @property
    def parents(self): return tuple(VirtualPath(v) for v in self.value.parents)
    def is_absolute(self): return self.value.is_absolute()
    def is_symlink(self): return self.rows.get(str(self), {}).get('symlink', False)
    def resolve(self, strict=False):
        if strict and str(self) not in self.rows: raise FileNotFoundError('unregistered virtual path')
        return VirtualPath(self.rows.get(str(self), {}).get('redirect', str(self)))
    def lstat(self): return types.SimpleNamespace(**self.rows[str(self)]['stat'])
    def stat(self): return self.lstat()


def closed_source_lift(path, expected_bytes, expected_sha):
    # Read source as bytes only. Never import its module, execute its top-level
    # body or main, instantiate its original constructor, or lift any action.
    raw = path.read_bytes()
    if len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise AssertionError('exact reviewed source differs')
    tree = ast.parse(raw)
    assignments = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assignments[node.targets[0].id] = node
    expected = {'UID': str(UID), 'BASE': "P('/data1/yanruj')", 'PRIMARY': "BASE / 'ArchEvolve'", 'RAW': "P('/data/yanruj/EvolveSWDB_runs')"}
    for name, expression in expected.items():
        if ast.dump(assignments[name].value, include_attributes=False) != ast.dump(ast.parse(expression, mode='eval').body, include_attributes=False):
            raise AssertionError('closed original route constant differs')
    functions = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    original_guard = functions['Guard']
    methods = {n.name: n for n in original_guard.body if isinstance(n, ast.FunctionDef)}
    lifted_guard = ast.ClassDef(name='Guard', bases=[], keywords=[],
        body=[methods[name] for name in ('check_private_root', 'private_ancestor', 'path')], decorator_list=[])
    body = [assignments[n] for n in ('UID', 'BASE', 'PRIMARY', 'RAW')]
    body += [functions[n] for n in ('Refused', 'require', 'inside', 'stamp')]
    body += [lifted_guard]
    # Only these exact definitions/assignments are compiled when the parent
    # explicitly authorizes this isolated batch. No target imports/main/CLI.
    selected = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    if any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(selected)):
        raise AssertionError('unexpected imported AST')
    namespace = {'P': VirtualPath, 'stat': stat, '__name__': 'closed_virtual_path_fixture'}
    exec(compile(selected, '<closed-reviewed-virtual-path-guards>', 'exec'), namespace)
    guard = object.__new__(namespace['Guard'])
    guard.private_root_stats = {}
    return guard, namespace['Refused']


class SetgidRootVirtualPathTests(unittest.TestCase):
    def put(self, text, mode=0o2777, uid=UID, gid=0, dev=2097, symlink=False):
        path = VirtualPath(text)
        VirtualPath.rows[str(path)] = {'symlink': symlink, 'stat': {
            'st_dev': dev, 'st_ino': 100 + len(VirtualPath.rows), 'st_mode': stat.S_IFDIR | mode,
            'st_uid': uid, 'st_gid': gid, 'st_nlink': 2, 'st_size': 4096,
            'st_mtime_ns': 10, 'st_ctime_ns': 10}}
        return path
    def setUp(self):
        VirtualPath.rows = {}
        self.put('/', 0o755, uid=0, dev=2050)
        self.put('/data1', 0o2777, uid=0)
        self.put(BASE_TEXT, 0o700)
        self.put('/data', 0o755, uid=0, dev=2065)
        self.put('/data/yanruj', 0o700, dev=2065)
        self.put('/data/yanruj/EvolveSWDB_runs', 0o755, dev=2065)
        self.guard, self.Refused = closed_source_lift(NEW_SOURCE, NEW_BYTES, NEW_SHA)
    def refused(self, path, code, directory=True, allow_primary_mode=False):
        with self.assertRaises(self.Refused) as result:
            self.guard.path(path, directory=directory, allow_primary_mode=allow_primary_mode)
        self.assertEqual(str(result.exception), code)
    def test_accept_private_setgid_evidence_directory(self):
        path = self.put(EV_TEXT)
        accepted, observed = self.guard.path(path, directory=True)
        self.assertEqual(accepted, path)
        self.assertEqual(observed.st_mode, stat.S_IFDIR | 0o2777)
        self.assertEqual(self.guard.private_root_stats[BASE_TEXT]['fixed_privacy_identity']['gid'], 0)
    def test_accept_private_setgid_model_and_baseline_directories(self):
        for text in (MODEL_TEXT, BASELINE_TEXT):
            with self.subTest(path=text):
                path = self.put(text)
                self.assertEqual(self.guard.path(path, directory=True)[0], path)
    def test_primary_legacy_flag_rejects_suid_and_sticky(self):
        for mode in (0o777, 0o2777):
            with self.subTest(allowed=mode):
                path = self.put(BASE_TEXT + '/ArchEvolve', mode)
                self.assertEqual(self.guard.path(path, directory=True, allow_primary_mode=True)[0], path)
        for mode in (0o4777, 0o1777, 0o6777, 0o3777):
            with self.subTest(refused=mode):
                path = self.put(BASE_TEXT + '/ArchEvolve', mode)
                self.refused(path, 'special_permission_bits', allow_primary_mode=True)
    def test_reject_setgid_regular_file(self):
        path = self.put(BASE_TEXT + '/file-fixture', 0o2644)
        VirtualPath.rows[str(path)]['stat']['st_mode'] = stat.S_IFREG | 0o2644
        self.refused(path, 'special_permission_bits', directory=False)
    def test_reject_suid_directory(self):
        self.refused(self.put(EV_TEXT, 0o4777), 'special_permission_bits')
    def test_reject_sticky_directory(self):
        self.refused(self.put(EV_TEXT, 0o1777), 'special_permission_bits')
    def test_reject_foreign_group(self):
        self.refused(self.put(EV_TEXT, gid=17), 'special_permission_bits')
    def test_reject_foreign_device(self):
        self.refused(self.put(EV_TEXT, dev=2065), 'special_permission_bits')
    def test_reject_foreign_owner(self):
        self.refused(self.put(EV_TEXT, uid=0), 'wrong_owner')
    def test_reject_symlink_target_and_component(self):
        self.refused(self.put(EV_TEXT, symlink=True), 'symlink_component')
        self.put(EV_TEXT)
        self.put(BASE_TEXT + '/ArchEvolve', symlink=True)
        self.refused(VirtualPath(EV_TEXT), 'symlink_component')
    def test_reject_nonprivate_base(self):
        self.put(BASE_TEXT, 0o755)
        self.refused(self.put(EV_TEXT), 'private_ancestor_owner_mode')
    def test_reject_setgid_directory_outside_base_even_with_private_raw_ancestor(self):
        path = self.put('/data/yanruj/EvolveSWDB_runs/fixture', dev=2065)
        self.refused(path, 'special_permission_bits')
    def test_reject_changed_fixed_private_identity(self):
        path = self.put(EV_TEXT)
        self.guard.path(path, directory=True)
        VirtualPath.rows[BASE_TEXT]['stat']['st_ino'] += 1
        self.refused(path, 'private_ancestor_identity_or_mode_changed')
    def test_preserve_auth_route_denial(self):
        self.refused(self.put(BASE_TEXT + '/.codex'), 'auth_or_credential_route_refused')
    def test_original_guard_demonstrates_observed_root_refusal(self):
        path = self.put(EV_TEXT)
        old, OriginalRefused = closed_source_lift(OLD_SOURCE, OLD_BYTES, OLD_SHA)
        with self.assertRaises(OriginalRefused) as result:
            old.path(path, directory=True)
        self.assertEqual(str(result.exception), 'special_permission_bits')


if __name__ == '__main__':
    unittest.main(verbosity=2)
