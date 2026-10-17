"""NOTRUN: new isolated synthetic G9 byte/metadata sequencing contracts.

No full source module/import/main, native Git, proc, deletion, real plan, SSH,
Store or old test suite. A future authorized invocation reads one pinned source
and lifts only named pure definitions and four administrative methods plus the
exact removal/final-preservation suffix of perform(). All external operations
are closed in-memory boundaries; no production constants/caps are changed.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
from types import SimpleNamespace
import unittest

SOURCE = ('/private/tmp/lanl_consumed_detached_source_guard_r9_20261008_a1.py', 120381,
          'efbdafffa53fb56f9e97555ae5894ac4bad0c253328d1f89b322edea5e6879c2')
SYNTHETIC_UID = 17001
SYNTHETIC_ROWS = {'row-a': {'head': 'a'*40}, 'row-b': {'head': 'b'*40}}
BASE = PurePosixPath('/SYNTHETIC/checkouts')
PRIMARY = PurePosixPath('/SYNTHETIC/primary')
RAW = PurePosixPath('/SYNTHETIC/raw')
PIN_BYTES = b'SYNTHETIC_PIN'
PIN_SHA = hashlib.sha256(PIN_BYTES).hexdigest()


class VirtualPath(PurePosixPath):
    model = None

    def lstat(self):
        return self.model.file_stat(str(self))

    def is_symlink(self):
        return stat.S_ISLNK(self.lstat().st_mode)

    def iterdir(self):
        if str(self) != str(RAW):
            raise AssertionError('synthetic directory listing scope')
        return iter(())


def lifted_sequence():
    path, size, digest = SOURCE
    with Path(path).open('rb') as source:
        body = source.read(128*1024 + 1)
    if len(body) != size or hashlib.sha256(body).hexdigest() != digest:
        raise AssertionError('synthetic source pin changed')
    module = ast.parse(body)
    names = ('Refused', 'require', 'sha', 'canonical', 'stamp', 'inside', 'tracked_mode_equivalent')
    pure = [copy.deepcopy(n) for n in module.body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    if len(pure) != len(names):
        raise AssertionError('closed pure definition inventory')
    limits = next(n for n in module.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'LIMITS' for t in n.targets))
    guard = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'Guard')
    methods = {n.name: n for n in guard.body if isinstance(n, ast.FunctionDef)}
    picked = [copy.deepcopy(methods[n]) for n in
              ('tree', 'stable_inventory', 'pre_remove_gate', 'gate', 'pin_fact')]
    perform = methods['perform']
    first = next(i for i, n in enumerate(perform.body) if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'first' for t in n.targets))
    end = next(i for i, n in enumerate(perform.body) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
                       and t.slice.value == 'admitted' for t in n.targets))
    operation = copy.deepcopy(perform)
    operation.name = 'synthetic_operation'
    operation.body = copy.deepcopy(perform.body[first:end])
    if ast.dump(ast.Module(body=operation.body, type_ignores=[]), include_attributes=False) != \
            ast.dump(ast.Module(body=perform.body[first:end], type_ignores=[]), include_attributes=False):
        raise AssertionError('original operation statement slice changed')
    closed = ast.Module(body=pure+[copy.deepcopy(limits),
        ast.ClassDef(name='ExactSequence', bases=[], keywords=[],
                     body=picked+[operation], decorator_list=[])], type_ignores=[])
    if any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(closed)):
        raise AssertionError('no target imports in lift')
    ast.fix_missing_locations(closed)
    # UID/ROWS/routes are explicitly synthetic rebindings. Exact production
    # LIMITS assignment is lifted unchanged; virtual costs have separate limits.
    context = {'__name__': 'synthetic_exact_slice', 'hashlib': hashlib, 'json': json,
               'stat': stat, 'P': VirtualPath, 'UID': SYNTHETIC_UID,
               'BASE': VirtualPath(BASE), 'PRIMARY': VirtualPath(PRIMARY),
               'RAW': VirtualPath(RAW), 'ROWS': SYNTHETIC_ROWS,
               'now': lambda: 'SYNTHETIC_TIME', '__file__': '/SYNTHETIC/source.py'}
    # Compilation/definition lift occurs only when parent later runs this fixture.
    exec(compile(closed, '<SYNTHETIC exact G9 slice>', 'exec'), context)
    return context


class VirtualSystem:
    def __init__(self, context, remove=True, mutation=None, new_consumer=None):
        self.context = context
        self.args = SimpleNamespace(select=['row-a', 'row-b'], remove=remove,
            plan='/SYNTHETIC/plan.json', plan_sha256=PIN_SHA, expected_primary='c'*40)
        self.selected = [VirtualPath(BASE/name) for name in self.args.select]
        self.plan = {'protected_file_pins': []}
        self.facts = {'removed_rows': [], 'pre_remove_full_byte_checks': {}}
        self.current_removal = None
        self.own_sha = PIN_SHA
        self.raw_before = {}
        self.raw_namespace = []
        self.passive_stats = {}
        self.passive_hashes = {}
        self.reference_hits = {}
        self.initial_tracked_metadata_stats = {}
        self.directory_stats = {}
        self.symlink_stats = {}
        self.stat_checks = 0
        self.stats = {}
        self.bodies = {}
        self.heads = {n: d['head'] for n, d in SYNTHETIC_ROWS.items()}
        self.tracked = {}
        self.git_removed = []
        self.kernel_reads = []
        self.role_visits = 0
        self.last_stable_removed = None
        self.last_process_removed = None
        self.last_process_rows = None
        self.raw_calls = 0
        self.final_raw_checked = False
        self.mutation = mutation
        self.new_consumer = new_consumer
        self.initial_snapshot = None
        self.failure = None
        self.events = []
        for p in (BASE, PRIMARY, RAW):
            self.add(str(p), None, directory=True)
        for n in self.args.select:
            folder = str(BASE/n)
            self.add(folder, None, directory=True)
            body = b'AAAA' if n == 'row-a' else b'BBBB'
            self.add(folder+'/kernel.c', body)
            oid = hashlib.sha1(b'blob 4\0'+body).hexdigest()
            self.tracked[n] = [(b'100644', oid.encode(), b'kernel.c')]
            self.add(folder+'/.git', ('gitdir: '+str(PRIMARY/'.git/worktrees'/n)+'\n').encode())
        self.add('/SYNTHETIC/plan.json', PIN_BYTES)
        self.add('/SYNTHETIC/source.py', PIN_BYTES)

    def add(self, path, body, directory=False):
        self.stats[path] = SimpleNamespace(st_dev=1, st_ino=100+len(self.stats),
            st_mode=(stat.S_IFDIR|0o700) if directory else (stat.S_IFREG|0o644),
            st_uid=SYNTHETIC_UID, st_gid=1, st_nlink=1,
            st_size=0 if directory else len(body), st_mtime_ns=10,
            st_ctime_ns=20, st_blocks=1)
        if not directory:
            self.bodies[path] = body

    def fail(self, reason):
        raise self.context['Refused'](reason)

    def check(self, value, reason):
        self.context['require'](value, reason)

    def file_stat(self, path):
        if any(path == str(BASE/n) or path.startswith(str(BASE/n)+'/') for n in self.git_removed):
            raise FileNotFoundError(path)
        self.check(path in self.stats, 'virtual_unknown_path')
        return copy.copy(self.stats[path])

    def path(self, path, directory=False, **unused):
        p = VirtualPath(path)
        s = self.file_stat(str(p))
        self.check(s.st_uid == SYNTHETIC_UID and
                   (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)),
                   'virtual_path_type_or_owner')
        return p, s

    def private_ancestor(self, path):
        return True

    def privacy_gate(self):
        return {'SYNTHETIC': True}

    def left(self):
        return 10000

    def retain_git(self):
        return {'SYNTHETIC': 'retained'}

    def native_git(self):
        pass

    def protect(self):
        pass

    def leases(self):
        return {'SYNTHETIC': {'sha256': 'released-synthetic-generation'}}

    def text_git(self, path, *args):
        name = PurePosixPath(path).name
        if args == ('rev-parse', 'HEAD'):
            return self.heads[name]
        if args == ('branch', '--show-current'):
            return ''
        if args == ('rev-parse', '--path-format=absolute', '--git-common-dir'):
            return str(PRIMARY/'.git')
        if args == ('rev-parse', 'HEAD^{tree}'):
            return ('1' if name == 'row-a' else '2')*40
        raise AssertionError(('unexpected virtual text Git', args))

    def git(self, path, *args):
        if args[:2] == ('worktree', 'remove'):
            self.check(path == VirtualPath(PRIMARY) and len(args) == 3, 'virtual_exact_remove')
            name = PurePosixPath(args[2]).name
            prior = tuple(self.facts['removed_rows'])
            proof = self.facts['pre_remove_full_byte_checks'].get(name)
            self.check(proof is not None and proof['regular_bytes_verified'] is True
                and proof['tracked_mode_blob_source_inventory_sha256'] is not None,
                'virtual_remove_without_journaled_full_bytes')
            self.check(proof['tracked_stat_inventory_sha256'] ==
                self.baseline[name]['tracked_stat_inventory_sha256'], 'virtual_remove_without_initial_identity')
            self.check(self.last_stable_removed == prior, 'virtual_remove_without_fresh_preservation')
            self.check(self.last_process_removed == prior and self.last_process_rows == [name],
                       'virtual_remove_without_fresh_process')
            self.git_removed.append(name)
            self.events.append(('git_remove', name))
            return b''
        if args[:2] in (('status', '--porcelain'), ('ls-files', '--others')):
            return b''
        if args[:3] == ('ls-tree', '-r', '-z'):
            head = args[3]
            name = next(n for n, d in SYNTHETIC_ROWS.items() if d['head'] == head)
            return b''.join(mode+b' blob '+oid+b'\t'+rel+b'\0' for mode, oid, rel in self.tracked[name])
        if args[:2] == ('merge-base', '--is-ancestor'):
            return b''
        if args[:2] == ('rev-list', '--objects'):
            return b'0'*40+b' object\n'
        raise AssertionError(('unexpected virtual Git', args))

    def batch_git(self, argv, **kwargs):
        self.check(argv == ['/usr/bin/git', '-c', 'protocol.allow=never', '-C', str(PRIMARY),
            'cat-file', '--batch-check=%(objectname) %(objecttype)'], 'virtual_exact_batch_Git')
        return SimpleNamespace(returncode=0, stderr=b'', stdout=b'0'*40+b' blob\n')

    def read(self, path, cap=None):
        p = str(path)
        s = self.file_stat(p)
        body = self.bodies[p]
        self.check(len(body) == s.st_size and (cap is None or len(body) <= cap), 'virtual_read_size')
        stamp = self.context['stamp'](s)
        if p in self.passive_stats:
            self.check(stamp == self.passive_stats[p], 'virtual_byte_cache_identity_changed')
        self.passive_stats[p] = stamp
        self.passive_hashes[p] = hashlib.sha256(body).hexdigest()
        if p.endswith('/kernel.c'):
            self.kernel_reads.append(PurePosixPath(p).parent.name)
            self.events.append(('full_read', PurePosixPath(p).parent.name))
        return body, stamp

    def pinned(self, pin, cap=None):
        body, got = self.read(pin['path'], cap)
        self.check(len(body) == pin['bytes'] and hashlib.sha256(body).hexdigest() == pin['sha256'],
                   'virtual_pin_changed')
        return body

    def aliases_and_sources(self):
        return {'SYNTHETIC': True}

    def process_references(self, continuity_rows=None):
        rows = [x for x in self.args.select if x not in self.facts['removed_rows']] \
            if continuity_rows is None else list(continuity_rows)
        self.role_visits += 2*sum({'row-a': 2, 'row-b': 3}[x] for x in rows)
        self.check(self.role_visits <= 25, 'virtual_role_visit_budget')
        if self.initial_snapshot is None:
            self.initial_snapshot = {'kernel_reads': list(self.kernel_reads),
                'byte_cache_paths': sorted(self.passive_stats),
                'metadata_paths': sorted(self.initial_tracked_metadata_stats)}
            if self.mutation is not None:
                self.mutation(self)
        if continuity_rows is not None and self.new_consumer in rows:
            self.fail('virtual_new_live_consumer')
        self.last_process_removed = tuple(self.facts['removed_rows'])
        self.last_process_rows = rows
        self.events.append(('fresh_process', tuple(rows)))
        return {'SYNTHETIC': True}

    def lexists(self, path):
        return PurePosixPath(path).name not in self.git_removed

    def receipts_and_raw(self):
        self.raw_calls += 1
        if self.raw_calls >= 2:
            # Final pass cannot proceed without the actual final preservation sweep.
            self.check(self.last_stable_removed == tuple(self.facts['removed_rows']),
                       'virtual_final_raw_without_final_preservation')
            self.final_raw_checked = True
        return {'SYNTHETIC': 'unchanged-preserved-originals'}


def run_virtual(remove=True, mutation=None, new_consumer=None, exercise_pin_cache=False):
    context = lifted_sequence()
    base = context['ExactSequence']
    # Keep the exact selected stable_inventory but record successful boundary
    # completion separately. This marker is a virtual external observation only.
    def observed_stable(self):
        result = base.stable_inventory(self)
        self.last_stable_removed = tuple(self.facts['removed_rows'])
        self.events.append(('stable_inventory', self.last_stable_removed))
        return result
    composite = type('VirtualGuard', (base, VirtualSystem), {'stable_inventory': observed_stable})
    model = composite(context, remove, mutation, new_consumer)
    VirtualPath.model = model
    context['C'] = 'd'*40
    context['os'] = SimpleNamespace(path=SimpleNamespace(lexists=model.lexists),
        readlink=lambda path: (_ for _ in ()).throw(AssertionError('fixture has no symlinks')))
    context['subprocess'] = SimpleNamespace(run=model.batch_git)
    try:
        if exercise_pin_cache:
            initial = model.gate()
            model.baseline = initial['trees']
            name = str(BASE/'row-a'/'kernel.c')
            self_pin = {'path': name, 'bytes': 4, 'sha256': hashlib.sha256(b'AAAA').hexdigest()}
            model.pin_fact(self_pin)
        else:
            model.synthetic_operation()
    except context['Refused'] as error:
        model.failure = str(error)
    return model


class DeferredByteRegression(unittest.TestCase):
    def test_remove_initial_metadata_is_not_byte_cache_and_full_proofs_precede_both_commands(self):
        result = run_virtual()
        self.assertIsNone(result.failure)
        self.assertEqual(result.initial_snapshot['kernel_reads'], [])
        self.assertEqual(result.initial_snapshot['metadata_paths'],
            [str(BASE/'row-a'/'kernel.c'), str(BASE/'row-b'/'kernel.c')])
        self.assertFalse(any(x.endswith('/kernel.c') for x in result.initial_snapshot['byte_cache_paths']))
        self.assertTrue(all(x['regular_bytes_verified'] is False and
            x['tracked_mode_blob_source_inventory_sha256'] is None for x in result.baseline.values()))
        self.assertEqual(result.kernel_reads, ['row-a', 'row-b'])
        self.assertEqual(result.git_removed, ['row-a', 'row-b'])
        self.assertEqual(sorted(result.facts['pre_remove_full_byte_checks']), ['row-a', 'row-b'])
        self.assertTrue(result.final_raw_checked)
        self.assertEqual(result.role_visits, 20)  # independently worked ten + four + six
        self.assertEqual([x for x in result.events if x[0]=='stable_inventory'],
            [('stable_inventory', ()), ('stable_inventory', ('row-a',)),
             ('stable_inventory', ('row-a','row-b'))])

    def test_default_inspection_still_full_hashes_every_regular_source(self):
        result = run_virtual(remove=False)
        self.assertIsNone(result.failure)
        self.assertEqual(result.initial_snapshot['kernel_reads'], ['row-a', 'row-b'])
        self.assertEqual(result.initial_snapshot['metadata_paths'], [])
        self.assertTrue(all(x['regular_bytes_verified'] is True and
            x['tracked_mode_blob_source_inventory_sha256'] is not None for x in result.baseline.values()))
        self.assertEqual(result.git_removed, [])
        self.assertEqual(result.facts['pre_remove_full_byte_checks'], {})
        self.assertTrue(result.final_raw_checked)

    def test_same_stat_changed_bytes_refuse_full_Git_blob_check_before_any_removal(self):
        def change(model):
            model.bodies[str(BASE/'row-a'/'kernel.c')] = b'ZZZZ'
        result = run_virtual(mutation=change)
        self.assertEqual(result.failure, 'tracked_source_bytes_changed')
        self.assertEqual(result.git_removed, [])
        self.assertEqual(result.facts['pre_remove_full_byte_checks'], {})

    def test_initial_metadata_never_substitutes_for_a_real_pin_fact_byte_read(self):
        result = run_virtual(exercise_pin_cache=True)
        self.assertIsNone(result.failure)
        self.assertEqual(result.initial_snapshot['kernel_reads'], [])
        self.assertEqual(result.kernel_reads, ['row-a'])
        self.assertIn(str(BASE/'row-a'/'kernel.c'), result.passive_hashes)

    def test_stat_mode_owner_link_head_and_layout_mutations_refuse_before_destructive_command(self):
        def stat_change(model, key, value):
            setattr(model.stats[str(BASE/'row-a'/'kernel.c')], key, value)
        cases = {
            'ctime': lambda m: stat_change(m, 'st_ctime_ns', 21),
            'mode': lambda m: stat_change(m, 'st_mode', stat.S_IFREG|0o755),
            'owner': lambda m: stat_change(m, 'st_uid', SYNTHETIC_UID+1),
            'link': lambda m: stat_change(m, 'st_nlink', 2),
            'head': lambda m: m.heads.__setitem__('row-a', 'e'*40),
            'layout': lambda m: m.tracked.__setitem__('row-a', []),
        }
        for label, mutation in cases.items():
            with self.subTest(label=label):
                result = run_virtual(mutation=mutation)
                self.assertIsNotNone(result.failure)
                self.assertEqual(result.git_removed, [])
                self.assertEqual(result.facts['pre_remove_full_byte_checks'], {})

    def test_new_live_consumer_still_refuses_second_removal_after_journaled_full_read(self):
        result = run_virtual(new_consumer='row-b')
        self.assertEqual(result.failure, 'virtual_new_live_consumer')
        self.assertEqual(result.git_removed, ['row-a'])
        self.assertEqual(result.facts['removed_rows'], ['row-a'])
        self.assertEqual(result.kernel_reads, ['row-a','row-b'])
        self.assertEqual(sorted(result.facts['pre_remove_full_byte_checks']), ['row-a','row-b'])
        self.assertFalse(result.final_raw_checked)


if __name__ == '__main__':
    unittest.main(verbosity=2)
