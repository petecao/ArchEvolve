"""Prospective isolated R3 permission contract fixture. SOURCE ONLY; NOT RUN.

At a future reviewed invocation, lift only four pure source definitions, Refused,
and four Guard permission methods. No target-module import, Guard main, filesystem
permission mutation, proc/Git/SSH/native/provider/Store/removal call exists here.
Virtual paths keep the production spelling while all metadata/UID are SYNTHETIC.
"""
import ast
import copy
import hashlib
from pathlib import Path, PurePosixPath
import stat
from types import SimpleNamespace
import unittest

SOURCE = Path('/private/tmp/lanl_consumed_detached_source_guard_r3_20261008.py')
SOURCE_BYTES = 69303
SOURCE_SHA256 = '552cd7424138adcf025db119e0a132e0bc70d733d61aaaddda0effe2932c5371'
SYNTHETIC_UID = 424242
PRODUCTION_UID_NOT_USED = 114316761
FUNCTIONS = ('require', 'stamp', 'inside', 'tracked_mode_equivalent')
METHODS = ('check_private_root', 'private_ancestor', 'privacy_gate', 'path')


def synthetic_stat(kind, mode, uid=SYNTHETIC_UID, ino=100):
    return SimpleNamespace(st_dev=11, st_ino=ino, st_mode=kind | mode, st_uid=uid,
                           st_gid=99, st_nlink=1, st_size=5,
                           st_mtime_ns=1000, st_ctime_ns=2000)


class VirtualPath:
    """Path protocol over in-memory facts; never consult or modify a real path."""
    nodes = {}
    links = {}

    def __init__(self, value):
        self.value = PurePosixPath(str(value))

    def __str__(self):
        return str(self.value)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return isinstance(other, VirtualPath) and self.value == other.value

    def __truediv__(self, value):
        return VirtualPath(self.value / str(value))

    @property
    def name(self):
        return self.value.name

    @property
    def parts(self):
        return self.value.parts

    @property
    def parents(self):
        return tuple(VirtualPath(value) for value in self.value.parents)

    @property
    def parent(self):
        return VirtualPath(self.value.parent)

    def is_absolute(self):
        return self.value.is_absolute()

    def is_symlink(self):
        node = self.nodes.get(str(self))
        return node is not None and stat.S_ISLNK(node.st_mode)

    def lstat(self):
        try:
            return self.nodes[str(self)]
        except KeyError:
            raise FileNotFoundError('synthetic_missing_node') from None

    def stat(self):
        return self.lstat()

    def resolve(self, strict=False):
        if strict:
            for value in (self, *self.parents):
                value.lstat()
        return self.links.get(str(self), self)


def lift_selected_source():
    # Bounded byte/pin read only at the future test invocation, not during preparation.
    with SOURCE.open('rb') as stream:
        raw = stream.read(SOURCE_BYTES + 1)
    if len(raw) != SOURCE_BYTES or hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise AssertionError('selected_R3_source_pin_changed')
    parsed = ast.parse(raw, filename=str(SOURCE))
    functions = {n.name: n for n in parsed.body if isinstance(n, ast.FunctionDef)}
    classes = {n.name: n for n in parsed.body if isinstance(n, ast.ClassDef)}
    refused = classes['Refused']
    if refused.bases != [] and ast.dump(refused.bases[0]) != ast.dump(ast.Name(id='Exception', ctx=ast.Load())):
        raise AssertionError('unexpected_refusal_base')
    original_guard = classes['Guard']
    methods = {n.name: n for n in original_guard.body if isinstance(n, ast.FunctionDef)}
    selected_guard = ast.ClassDef(name='PermissionGuard', bases=[], keywords=[],
                                  body=[copy.deepcopy(methods[k]) for k in METHODS],
                                  decorator_list=[], type_params=[])
    selected = ast.Module(body=[copy.deepcopy(refused)] +
                          [copy.deepcopy(functions[k]) for k in FUNCTIONS] +
                          [selected_guard], type_ignores=[])
    ast.fix_missing_locations(selected)
    # UID is explicitly synthetic. No target assignment, initializer, or main is lifted.
    namespace = {'P': VirtualPath, 'stat': stat, 'UID': SYNTHETIC_UID,
                 'BASE': VirtualPath('/data1/yanruj'),
                 'PRIMARY': VirtualPath('/data1/yanruj/ArchEvolve'),
                 'RAW': VirtualPath('/data/yanruj/EvolveSWDB_runs')}
    exec(compile(selected, '<isolated_selected_R3_permission_AST>', 'exec'), namespace)
    return namespace


class PermissionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = lift_selected_source()

    def setUp(self):
        self.assertNotEqual(SYNTHETIC_UID, PRODUCTION_UID_NOT_USED)
        VirtualPath.nodes = {}
        VirtualPath.links = {}
        directories = {'/': 0o755, '/data1': 0o755, '/data': 0o755,
                       '/data1/yanruj': 0o700, '/data/yanruj': 0o700,
                       '/data1/yanruj/work': 0o775,
                       '/data1/yanruj/ArchEvolve': 0o2777,
                       '/data/yanruj/EvolveSWDB_runs': 0o775,
                       '/data/yanruj/other': 0o775, '/outside': 0o755}
        for index, (path, mode) in enumerate(directories.items(), 10):
            owner = 0 if path in ('/', '/data1', '/data') else SYNTHETIC_UID
            VirtualPath.nodes[path] = synthetic_stat(stat.S_IFDIR, mode, owner, index)
        for index, path in enumerate(('/data1/yanruj/work/file',
                                      '/data/yanruj/EvolveSWDB_runs/file',
                                      '/data/yanruj/other/file', '/outside/file'), 100):
            VirtualPath.nodes[path] = synthetic_stat(stat.S_IFREG, 0o664, ino=index)
        self.guard = self.ns['PermissionGuard']()
        self.guard.private_root_stats = {}
        self.refused = self.ns['Refused']

    def refused_code(self, code, action):
        with self.assertRaises(self.refused) as captured:
            action()
        self.assertEqual(str(captured.exception), code)

    def test_literal_private_700_admits_existing_write_modes_and_records_roots(self):
        for path in ('/data1/yanruj/work/file', '/data/yanruj/EvolveSWDB_runs/file'):
            for mode in (0o644, 0o664, 0o666):
                with self.subTest(path=path, mode=oct(mode)):
                    VirtualPath.nodes[path].st_mode = stat.S_IFREG | mode
                    actual, observed = self.guard.path(path)
                    self.assertEqual(str(actual), path)
                    self.assertEqual(stat.S_IMODE(observed.st_mode), mode)
        self.guard.path('/data1/yanruj/work', directory=True)
        captured = self.guard.privacy_gate()
        self.assertEqual(set(captured), {'/data1/yanruj', '/data/yanruj'})
        for row in captured.values():
            self.assertEqual(stat.S_IMODE(row['fixed_privacy_identity']['mode']), 0o700)
            self.assertEqual(row['fixed_privacy_identity']['uid'], SYNTHETIC_UID)
            self.assertGreater(row['checks'], 1)

    def test_701_and_755_private_roots_refuse_even_a_readonly_target(self):
        path = '/data1/yanruj/work/file'
        VirtualPath.nodes[path].st_mode = stat.S_IFREG | 0o644
        for mode in (0o701, 0o755):
            with self.subTest(root_mode=oct(mode)):
                VirtualPath.nodes['/data1/yanruj'].st_mode = stat.S_IFDIR | mode
                self.refused_code('private_ancestor_owner_mode', lambda: self.guard.path(path))

    def test_foreign_root_and_foreign_leaf_remain_refused(self):
        path = '/data1/yanruj/work/file'
        VirtualPath.nodes['/data1/yanruj'].st_uid = SYNTHETIC_UID + 1
        self.refused_code('private_ancestor_owner_mode', lambda: self.guard.path(path))
        VirtualPath.nodes['/data1/yanruj'].st_uid = SYNTHETIC_UID
        VirtualPath.nodes[path].st_uid = SYNTHETIC_UID + 1
        self.refused_code('wrong_owner', lambda: self.guard.path(path))

    def test_symlink_root_ancestor_and_leaf_are_never_privacy_proofs(self):
        for bad in ('/data1/yanruj', '/data1', '/data1/yanruj/work/file'):
            with self.subTest(symlink=bad):
                prior = VirtualPath.nodes[bad]
                VirtualPath.nodes[bad] = synthetic_stat(stat.S_IFLNK, 0o777, ino=800)
                self.refused_code('symlink_component',
                                  lambda: self.guard.path('/data1/yanruj/work/file'))
                VirtualPath.nodes[bad] = prior
        VirtualPath.nodes['/data1/yanruj'] = synthetic_stat(stat.S_IFLNK, 0o777, ino=801)
        self.refused_code('private_ancestor_redirect',
                          lambda: self.guard.check_private_root(VirtualPath('/data1/yanruj')))

    def test_replaced_root_inode_refuses_and_captured_facts_are_independent(self):
        root = '/data1/yanruj'
        self.guard.path(root, directory=True)
        captured = self.guard.privacy_gate()
        original_capture = copy.deepcopy(captured)
        VirtualPath.nodes[root].st_mtime_ns += 50
        VirtualPath.nodes[root].st_ctime_ns += 50
        VirtualPath.nodes[root].st_nlink += 1
        self.guard.path(root, directory=True)
        self.assertEqual(captured, original_capture)
        replacement = copy.deepcopy(VirtualPath.nodes[root])
        replacement.st_ino += 1
        VirtualPath.nodes[root] = replacement
        self.refused_code('private_ancestor_identity_or_mode_changed',
                          lambda: self.guard.path(root, directory=True))
        self.assertEqual(captured, original_capture)

    def test_private_scope_does_not_cover_data_siblings_or_unrelated_paths(self):
        for path in ('/data/yanruj/other/file', '/outside/file'):
            with self.subTest(outside=path):
                self.refused_code('writable_untrusted_path', lambda: self.guard.path(path))
                VirtualPath.nodes[path].st_mode = stat.S_IFREG | 0o644
                self.assertEqual(str(self.guard.path(path)[0]), path)
        self.assertFalse(self.guard.private_ancestor(VirtualPath('/data/yanruj')))
        self.refused_code('private_ancestor_not_literal',
                          lambda: self.guard.check_private_root(VirtualPath('/outside')))

    def test_special_bits_auth_denials_and_exact_primary_exception_stay_intact(self):
        path = '/data1/yanruj/work/file'
        VirtualPath.nodes[path].st_mode = stat.S_IFREG | 0o4664
        self.refused_code('special_permission_bits', lambda: self.guard.path(path))
        self.refused_code('auth_or_credential_route_refused',
                          lambda: self.guard.path('/data1/yanruj/.ssh/key'))
        primary = '/data1/yanruj/ArchEvolve'
        self.refused_code('special_permission_bits',
                          lambda: self.guard.path(primary, directory=True))
        actual, observed = self.guard.path(primary, directory=True, allow_primary_mode=True)
        self.assertEqual(str(actual), primary)
        self.assertEqual(stat.S_IMODE(observed.st_mode), 0o2777)

    def test_tracked_git_modes_accept_only_optional_022_with_a_privacy_proof(self):
        equivalent = self.ns['tracked_mode_equivalent']
        for git_mode, exact, writable in (('100644', 0o644, (0o646, 0o664, 0o666)),
                                          ('100755', 0o755, (0o757, 0o775, 0o777))):
            with self.subTest(git_mode=git_mode):
                self.assertTrue(equivalent(exact, git_mode, False))
                for mode in writable:
                    self.assertFalse(equivalent(mode, git_mode, False))
                    self.assertTrue(equivalent(mode, git_mode, True))
        # Independently enumerated changed read/execute/owner/special-bit cases.
        for git_mode, modes in (('100644', (0o600, 0o640, 0o645, 0o444, 0o744, 0o4644)),
                                 ('100755', (0o700, 0o750, 0o754, 0o555, 0o655, 0o4755))):
            for mode in modes:
                with self.subTest(git_mode=git_mode, bad_mode=oct(mode)):
                    self.assertFalse(equivalent(mode, git_mode, True))
        self.refused_code('unsupported_tracked_permission_kind',
                          lambda: equivalent(0o644, '120000', True))


if __name__ == '__main__':
    unittest.main(verbosity=2)
