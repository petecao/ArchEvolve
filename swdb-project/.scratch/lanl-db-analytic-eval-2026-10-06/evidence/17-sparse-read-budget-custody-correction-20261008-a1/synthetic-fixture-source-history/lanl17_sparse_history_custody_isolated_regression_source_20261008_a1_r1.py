"""SOURCE-ONLY synthetic regression proposal. NOT RUN.

Only the named AST definitions below are lifted from byte-pinned R5/R2 sources
at a future parent-authorized invocation. No operational module/main imports,
Guard.__init__/perform, native Git/process/proc calls or real source/RAW paths.
Every virtual operational route maps to a fresh temporary sandbox. Synthetic
True receipts are test inputs, never actual default/retirement/science evidence.
"""
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import types
import unittest

SOURCE = Path('/private/tmp/lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py')
SOURCE_BYTES = 180887
SOURCE_SHA = 'd75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301'
LEGACY = Path('/private/tmp/lanl_sparse_retire_consumed_source_guard_20261008_a1_r2.py')
LEGACY_BYTES = 166145
LEGACY_SHA = '4956a7453ae569d7ccf6e1a9ed98a1a933bee2e35cca1774932afbfba819bd26'
PURE_DEFINITIONS = ('Refused', 'require', 'sha', 'canonical', 'strict_json',
                    'stamp', 'inside', 'any_inside', 'now')
METHODS = ('read', 'pinned', 'pin_fact', 'sealed', 'historical_custody_projection',
           'historical_custody_eligible_paths', 'check_inherited_history_file',
           'inherit_historical_custody', 'record_historical_custody',
           'stable_inventory', 'pre_retire_gate', 'gate', 'aliases_and_sources')
BASE = '/data1/yanruj'
PRIMARY = BASE + '/ArchEvolve'
RAW = '/data/yanruj/EvolveSWDB_runs'
ROW = 'ArchEvolve-isolated-synthetic-row'
HEAD = '1' * 40
PRIMARY_HEAD = '2' * 40
EVIDENCE = 'swdb-project/.scratch/isolated-synthetic/evidence/'
FRESH_ROOT = RAW + '/lanl-current-data-a1'
SIBLING_ROOT = RAW + '/lanl-current-side-a1'
ELIGIBLE = (RAW + '/lanl-history-only-a1/first.json',
            RAW + '/lanl-history-only-a1/second.txt')
CURRENT_PATHS = (FRESH_ROOT + '/count.json', SIBLING_ROOT + '/state.json',
                 PRIMARY + '/swdb-project/records/probe.yaml',
                 BASE + '/' + ROW + '/swdb-project/fixture.cpp')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def wire(value):
    # Exact documented True canonical policy of these synthetic seals.
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def checked_source(path, count, expected):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ValueError('test_source_not_single_regular_file')
    fields = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink',
              'st_size', 'st_mtime_ns', 'st_ctime_ns')
    if before.st_size != count:
        raise ValueError('test_source_size_changed')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        if any(getattr(before, key) != getattr(opened, key) for key in fields):
            raise ValueError('test_source_open_identity_changed')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(count + 1)
        final_fd = os.fstat(fd)
    finally:
        os.close(fd)
    after = path.lstat()
    if (len(raw) != count or digest(raw) != expected or any(
            getattr(before, key) != getattr(final_fd, key) or
            getattr(before, key) != getattr(after, key) for key in fields)):
        raise ValueError('test_source_pin_or_identity_changed')
    return ast.parse(raw, filename=str(path))


def closed_literal(node):
    """Only a closed literal graph and nonnegative integer multiplication."""
    if isinstance(node, ast.Constant) and type(node.value) in (str, int, bool, type(None)):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [closed_literal(item) for item in node.elts]
        return tuple(values) if isinstance(node, ast.Tuple) else values
    if isinstance(node, ast.Dict):
        keys = [closed_literal(item) for item in node.keys]
        if len(keys) != len(set(keys)):
            raise ValueError('duplicate_literal_key')
        return dict(zip(keys, (closed_literal(item) for item in node.values)))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        left, right = closed_literal(node.left), closed_literal(node.right)
        if type(left) is int and type(right) is int and left >= 0 and right >= 0:
            return left * right
    raise ValueError('nonclosed_literal_AST')


class VirtualPath:
    """Pure logical routes; __fspath__ can reach only this synthetic sandbox."""
    def __init__(self, fs, value):
        self.fs = fs
        self.route = PurePosixPath(str(value))
        if '..' in self.route.parts:
            raise ValueError('synthetic_route_escape')
        if self.route.is_absolute() and not any(
                str(self.route) == root or str(self.route).startswith(root + '/')
                for root in (BASE, RAW)):
            raise ValueError('synthetic_route_outside_two_virtual_roots')

    def __str__(self):
        return str(self.route)

    def __fspath__(self):
        if not self.route.is_absolute():
            raise ValueError('relative_synthetic_path_has_no_physical_route')
        return str(self.fs.root.joinpath(*self.route.parts[1:]))

    def __truediv__(self, other):
        return VirtualPath(self.fs, self.route / str(other))

    def __eq__(self, other):
        return isinstance(other, VirtualPath) and self.fs is other.fs and self.route == other.route

    def __hash__(self):
        return hash((id(self.fs), self.route))

    def __lt__(self, other):
        return str(self) < str(other)

    @property
    def parent(self):
        return VirtualPath(self.fs, self.route.parent)

    @property
    def name(self):
        return self.route.name

    @property
    def suffix(self):
        return self.route.suffix

    @property
    def parts(self):
        return self.route.parts

    def is_absolute(self):
        return self.route.is_absolute()

    def lstat(self):
        return Path(os.fspath(self)).lstat()

    def stat(self):
        return Path(os.fspath(self)).stat()

    def resolve(self, strict=False):
        if strict and not Path(os.fspath(self)).exists():
            raise FileNotFoundError('synthetic_route_absent')
        if Path(os.fspath(self)).is_symlink():
            raise ValueError('synthetic_fixture_never_resolves_symlink')
        return self

    def iterdir(self):
        return iter(self / item.name for item in Path(os.fspath(self)).iterdir())


class Sandbox:
    def __init__(self, root):
        self.root = root
        for route in (BASE, PRIMARY, RAW):
            self.physical(route).mkdir(parents=True, exist_ok=True)

    def path(self, route):
        return route if isinstance(route, VirtualPath) else VirtualPath(self, route)

    def physical(self, route):
        return Path(os.fspath(self.path(route)))

    def put(self, route, raw):
        path = self.physical(route)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o600)
        return self.pin(route)

    def pin(self, route):
        path = self.path(route)
        raw = self.physical(route).read_bytes()
        observed = path.lstat()
        return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw),
                'stat': {key: getattr(observed, 'st_' + key) for key in
                         ('dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size',
                          'mtime_ns', 'ctime_ns')}}

    def replace_same_bytes(self, route):
        path = self.physical(route)
        saved = path.read_bytes()
        replacement = path.with_name(path.name + '.synthetic-replacement')
        replacement.write_bytes(saved)
        replacement.chmod(0o600)
        os.replace(replacement, path)


def lift(fs):
    tree = checked_source(SOURCE, SOURCE_BYTES, SOURCE_SHA)
    legacy_tree = checked_source(LEGACY, LEGACY_BYTES, LEGACY_SHA)
    definitions = {node.name: node for node in tree.body
                   if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    guard = definitions['Guard']
    named = {node.name: node for node in guard.body if isinstance(node, ast.FunctionDef)}
    if any(name not in named for name in METHODS):
        raise ValueError('selected_method_missing')
    helpers = [copy.deepcopy(definitions[name]) for name in PURE_DEFINITIONS]
    if any(node.decorator_list for node in helpers):
        raise ValueError('unexpected_selected_helper_decorator')
    for node in helpers + [named[name] for name in METHODS]:
        if any(isinstance(child, (ast.Import, ast.ImportFrom)) for child in ast.walk(node)):
            raise ValueError('selected_AST_contains_import')
    limits = [node.value for node in tree.body if isinstance(node, ast.Assign)
              and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
              and node.targets[0].id == 'LIMITS']
    if len(limits) != 1:
        raise ValueError('limits_assignment_not_unique')
    namespace = {'hashlib': hashlib, 'json': json, 'os': os, 're': re,
                 'stat': stat, 'datetime': datetime, 'P': fs.path,
                 'BASE': fs.path(BASE), 'PRIMARY': fs.path(PRIMARY), 'RAW': fs.path(RAW),
                 'LIMITS': closed_literal(limits[0]), 'EVIDENCE': EVIDENCE,
                 'ROWS': {ROW: {'head': HEAD, 'receipts': ['SYNTHETIC']}},
                 'RECEIPTS': {'SYNTHETIC': {'file': 'source-proof.json',
                             'sha256': '', 'raw_names': ['lanl-current-data-a1']}},
                 'FUTURE_SOURCE_HASHES': {}}
    # Future execution only: compile exactly these helpers and selected methods.
    cls = ast.ClassDef(name='LiftedGuard', bases=[], keywords=[],
                       body=[copy.deepcopy(named[name]) for name in METHODS],
                       decorator_list=[], type_params=[])
    module = ast.fix_missing_locations(ast.Module(body=helpers + [cls], type_ignores=[]))
    exec(compile(module, str(SOURCE) + ':closed-synthetic-AST', 'exec'), namespace)
    original_parse = namespace['strict_json']
    namespace['parse_calls'] = 0

    def counted_parse(raw):
        namespace['parse_calls'] += 1
        return original_parse(raw)
    namespace['strict_json'] = counted_parse
    old_guard = next(node for node in legacy_tree.body
                     if isinstance(node, ast.ClassDef) and node.name == 'Guard')
    old_gate = next(node for node in old_guard.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'gate')
    old = copy.deepcopy(old_gate)
    old.name = 'legacy_gate'
    exec(compile(ast.fix_missing_locations(ast.Module(body=[old], type_ignores=[])),
                 str(LEGACY) + ':one-legacy-gate-AST', 'exec'), namespace)
    # Exact publish prefix through the unchanged compact_receipt_limit require.
    # The later Linux/account/output publication portion is never lifted/called.
    publish = copy.deepcopy(named['publish'])
    prefix = []
    found_cap = False
    for statement in publish.body:
        prefix.append(statement)
        if (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Name)
                and statement.value.func.id == 'require'
                and len(statement.value.args) == 2
                and isinstance(statement.value.args[1], ast.Constant)
                and statement.value.args[1].value == 'compact_receipt_limit'):
            found_cap = True
            break
    if not found_cap or any(isinstance(node, ast.Name) and node.id in
                           ('sys', 'socket', 'UID', 'print', 'open')
                           for statement in prefix for node in ast.walk(statement)):
        raise ValueError('publication_prefix_boundary_changed')
    publish.name = 'compact_publication_prefix'
    publish.body = prefix + [ast.Return(value=ast.Name(id='body', ctx=ast.Load()))]
    exec(compile(ast.fix_missing_locations(ast.Module(body=[publish], type_ignores=[])),
                 str(SOURCE) + ':receipt-prefix-only-AST', 'exec'), namespace)
    return namespace


class Fixture:
    """Fresh byte reads are real tiny-file reads; all operational boundaries virtual."""
    def __init__(self, root):
        self.fs = Sandbox(root)
        self.ns = lift(self.fs)
        self.cls = self.ns['LiftedGuard']
        self.Refused = self.ns['Refused']
        self.trace = []
        self.read_calls = []
        self.body_by_rel = {'swdb-project/fixture.cpp': b'int fixture = 7;\n',
                            'swdb-project/second.cpp': b'int second = 9;\n'}
        self.history = []
        for index, route in enumerate(ELIGIBLE + CURRENT_PATHS):
            body = self.body_by_rel['swdb-project/fixture.cpp'] if route == CURRENT_PATHS[-1] else (
                ('synthetic historical bytes ' + str(index) + '\n').encode())
            pin = self.fs.put(route, body)
            pin.update(handling='historical_only_not_dereferenced',
                       review_basis='isolated synthetic explicitly classified original')
            self.history.append(pin)
        self.fs.put(BASE + '/' + ROW + '/swdb-project/second.cpp',
                    self.body_by_rel['swdb-project/second.cpp'])
        self.library = self.fs.put(BASE + '/' + ROW + '/swdb-project/library/tiny.txt', b'library\n')
        self.wrapper_pin = self.fs.put(BASE + '/synthetic-wrapper.py', b'# synthetic inert wrapper\n')
        self.proof_route = PRIMARY + '/' + EVIDENCE + 'source-proof.json'
        proof_doc = {'first': digest(self.body_by_rel['swdb-project/fixture.cpp']),
                     'second': digest(self.body_by_rel['swdb-project/second.cpp'])}
        self.proof_pin = self.fs.put(self.proof_route, wire(proof_doc))
        self.ns['RECEIPTS']['SYNTHETIC']['sha256'] = self.proof_pin['sha256']
        self.plan = {
            'historical_reference_files': copy.deepcopy(self.history),
            'raw_control_sibling_paths': [SIBLING_ROOT],
            'original_raw_file_pins': [copy.deepcopy(self.history[2])],
            'receipt_source_file_proofs': [], 'pending_control_files': [],
            'future_source_pins': {}, 'native_git_pin': {'synthetic': 'inert native witness'},
            'account_service_identification_pin': {'synthetic': 'inert PAM witness'},
            'portal_service_review_pin': {'synthetic': 'inert role witness'},
            'retained_raw_library_aliases': [], 'retirement_operation': {'synthetic': 'no action'},
            'protected_file_pins': [copy.deepcopy(self.wrapper_pin)],
            'control_siblings_complete_review': {'complete': True},
            'pending_alias_coverage_review': {'complete': True, 'no_queued_source_consumers': True},
            'receipt_source_proofs_complete_review': {'complete': True},
            'original_raw_files_complete_review': {'complete': True},
            'relevant_privileged_consumers': [{'synthetic_role': 'explicit fixture only'}]}
        self.prior_custody = None
        self.bundle = None

    def guard(self, retire=False):
        guard = object.__new__(self.cls)
        guard.args = types.SimpleNamespace(retire=retire, select=[ROW], expected_primary=PRIMARY_HEAD)
        guard.own_sha = SOURCE_SHA
        guard.plan = copy.deepcopy(self.plan)
        guard.parent_review = {'actual_default_only': not retire}
        guard.selected = [self.fs.path(BASE + '/' + ROW)]
        guard.passive_stats = {}; guard.passive_hashes = {}; guard.reference_hits = {}
        guard.initial_tracked_metadata_stats = {}; guard.inherited_history = {}
        guard.directory_stats = {}; guard.symlink_stats = {}; guard.stat_checks = 0
        guard.read_bytes = 0; guard.raw_before = {}; guard.baseline = {}
        guard.completed_dropped_paths = {}
        guard.raw_namespace = sorted(path.name for path in self.fs.path(RAW).iterdir()
                                     if path.name.startswith(('lanl-', 'lanl17-')))
        guard.facts = {'started_at': '2026-10-08T10:10:00+00:00',
                       'pre_retire_full_byte_checks': {}}
        guard.left = lambda: 60
        guard.privacy_gate = lambda: {'synthetic': 'temporary routes only'}
        guard.private_ancestor = lambda path: True
        guard.path = lambda path: (self.fs.path(path), self.fs.path(path).lstat())
        guard.completed_names = lambda: []
        guard.shared_administration = lambda: self.trace.append('shared_administration')
        guard.leases = lambda: {'synthetic': {'sha256': '3' * 64}}
        guard.retain_git = lambda: {'synthetic': 'no native Git called'}
        guard.protect = lambda: self.trace.append('protect')
        guard.walk = lambda root: []
        guard.library_snapshot = lambda name, full_bytes=False: self.read_library(guard, full_bytes)
        guard.git = lambda root, *args: self.git_body(args)
        guard.tree = lambda path, head, hash_regular_bytes=True: self.tree(guard, hash_regular_bytes)
        guard.receipts_and_raw = lambda: self.fresh_raw(guard)
        original_read = self.cls.read

        def counted_read(current, path, cap=None):
            self.read_calls.append(str(path))
            return original_read(current, path, cap)
        guard.read = types.MethodType(counted_read, guard)
        return guard

    def tree(self, guard, full):
        self.trace.append(('tree', full))
        if getattr(guard, 'reject_initial_full', False) and full:
            raise self.Refused('synthetic_initial_full_tree_not_allowed')
        result = {'synthetic_static_metadata': 'one tracked tiny file',
                  'regular_bytes_verified': bool(full),
                  'tracked_mode_blob_source_inventory_sha256': None}
        if full:
            body, unused = guard.read(CURRENT_PATHS[-1])
            result['tracked_mode_blob_source_inventory_sha256'] = digest(body)
        return result

    def fresh_raw(self, guard):
        self.trace.append('fresh_RAW')
        body, unused = guard.read(CURRENT_PATHS[0])
        return {'synthetic_root': digest(body)}

    def read_library(self, guard, full):
        self.trace.append(('library', full))
        if not full:
            raise self.Refused('synthetic_full_library_required')
        guard.read(self.library['path'])
        return {'synthetic': 'fresh tiny bytes'}

    def git_body(self, args):
        self.trace.append(('Git_blob', args))
        if len(args) != 3 or args[:2] != ('cat-file', 'blob') or not args[2].startswith(HEAD + ':'):
            raise AssertionError('synthetic_Git_unexpected_operation')
        return self.body_by_rel[args[2].split(':', 1)[1]]

    def make_proofs(self):
        return [{'row': ROW, 'receipt_key': 'SYNTHETIC', 'commit': HEAD,
                 'relative_path': relative, 'sha256': digest(self.body_by_rel[relative]),
                 'receipt_json_path': [field]}
                for relative, field in [('swdb-project/fixture.cpp', 'first'),
                                        ('swdb-project/second.cpp', 'second')]]

    def sealed(self, route, payload, corrupt=False):
        body = copy.deepcopy(payload)
        body['canonical_ensure_ascii'] = True
        body.pop('identity_sha256', None)
        identity = digest(wire(body))
        body['identity_sha256'] = identity
        if corrupt:
            body['synthetic_after_seal_mutation'] = True
        pin = self.fs.put(route, wire(body))
        pin.update(identity_sha256=identity, canonical_ensure_ascii=True, format=body['format'])
        return body, pin

    def prepare_prior(self):
        default = self.guard(False)
        default.record_historical_custody()
        self.prior_custody = copy.deepcopy(default.facts['historical_byte_custody'])

    def bundle_for(self, guard, review_change=None, plan_change=None, receipt_change=None,
                   status_change=None, returned_change=None, corrupt_receipt=False):
        if self.prior_custody is None:
            self.prepare_prior()
        configuration = copy.deepcopy(self.plan)
        configuration.update(format='swdb.library-preserving-sparse-retirement-parent-plan.v1',
                             canonical_ensure_ascii=True, guard_source_sha256=SOURCE_SHA,
                             expected_primary=PRIMARY_HEAD, selected_rows=[ROW],
                             checked_at='2026-10-08T10:00:00+00:00')
        review = {'format': 'isolated.synthetic.parent-review.v1',
                  'actual_default_only': True, 'accepted_for_exact_subset': True,
                  'accepted_library_preserving_sparse_scope': True,
                  'final14_completed_and_released': True,
                  'reviewed_configuration_sha256': digest(wire(configuration))}
        if review_change:
            review_change(review)
        review, review_pin = self.sealed(BASE + '/synthetic-default-review.json', review)
        prior_plan = copy.deepcopy(configuration)
        for key in ('control_siblings_complete_review', 'pending_alias_coverage_review',
                    'receipt_source_proofs_complete_review', 'original_raw_files_complete_review'):
            prior_plan[key]['parent_review_identity_sha256'] = review['identity_sha256']
        for consumer in prior_plan['relevant_privileged_consumers']:
            consumer['parent_review_identity_sha256'] = review['identity_sha256']
        prior_plan['parent_review_pin'] = review_pin
        if plan_change:
            plan_change(prior_plan)
        prior_plan, plan_pin = self.sealed(BASE + '/synthetic-default-plan.json', prior_plan)
        receipt = {'format': 'swdb.library-preserving-sparse-retirement-guard.v1',
                   'admitted': True, 'failure': None, 'retire_requested': False,
                   'retired_rows': [], 'completed_retirements': [],
                   'pre_retire_full_byte_checks': {}, 'full_raw_byte_passes': 2,
                   'inspection_limits': copy.deepcopy(self.ns['LIMITS']),
                   'scientific_admission': False, 'capacity_admission': False,
                   'guard_source_sha256': SOURCE_SHA, 'expected_primary': PRIMARY_HEAD,
                   'selected_rows': [ROW], 'reviewed_plan_file_sha256': plan_pin['sha256'],
                   'reviewed_plan_identity_sha256': prior_plan['identity_sha256'],
                   'parent_review_identity_sha256': review['identity_sha256'],
                   'bytes_read': 100, 'walk_entries_checked': 10, 'stable_stat_checks': 20,
                   'started_at': '2026-10-08T10:01:00+00:00',
                   'finished_at': '2026-10-08T10:02:00+00:00',
                   'initial_checks': {'trees': {ROW: {
                       'regular_bytes_verified': False,
                       'tracked_mode_blob_source_inventory_sha256': None}}},
                   'historical_byte_custody': copy.deepcopy(self.prior_custody),
                   'synthetic_test_input_not_actual_admission': True}
        if receipt_change:
            receipt_change(receipt)
        receipt_route = BASE + '/lanl-library-preserving-sparse-retirement-20261008-a1/receipt.json'
        receipt, receipt_pin = self.sealed(receipt_route, receipt, corrupt=corrupt_receipt)
        reviewed_plan = {'file': copy.deepcopy(plan_pin), 'identity_sha256': prior_plan['identity_sha256']}
        returned = {'format': 'swdb.library-preserving-sparse-retirement-return.v1',
                    'path': receipt_route, 'bytes': receipt_pin['bytes'],
                    'sha256': receipt_pin['sha256'], 'identity_sha256': receipt_pin['identity_sha256'],
                    'admitted': True, 'retired_count': 0, 'failure': None}
        if returned_change:
            returned_change(returned)
        control = BASE + '/lanl17-detached-sparse-synthetic-default-a1'
        stdout_pin = self.fs.put(control + '/guard.stdout', wire(returned))
        status = {'format': 'swdb.lanl17-detached-library-sparse-administration-status.v1',
                  'sealed': False, 'state': 'guard_completed', 'guard_exit_code': 0,
                  'retire_requested': False, 'expected_primary': PRIMARY_HEAD,
                  'selected_rows': [ROW], 'inputs': {'guard': {'sha256': SOURCE_SHA},
                                                    'wrapper': copy.deepcopy(self.wrapper_pin)},
                  'guard_stdout': copy.deepcopy(stdout_pin), 'reviewed_plan': reviewed_plan,
                  'guard_attempt': 'a1'}
        if status_change:
            status_change(status)
        status_pin = self.fs.put(control + '/status.json', wire(status))
        bindings = {'original_guard_receipt': receipt_pin, 'status': status_pin,
                    'stdout': stdout_pin, 'default_reviewed_plan': reviewed_plan,
                    'default_review': copy.deepcopy(review_pin)}
        guard.parent_review = {'actual_default_only': False,
                               'successful_default_original_bindings': bindings}
        self.bundle = {'receipt': receipt, 'plan': prior_plan, 'review': review,
                       'status': status, 'returned': returned, 'bindings': bindings}
        return self.bundle


class HistoricalCustodyRegression(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lanl17-isolated-history-')
        self.addCleanup(self.temporary.cleanup)
        self.fixture = Fixture(Path(self.temporary.name))

    def fresh(self):
        temporary = tempfile.TemporaryDirectory(prefix='lanl17-isolated-subcase-')
        self.addCleanup(temporary.cleanup)
        return Fixture(Path(temporary.name))

    def test_metadata_gate_both_modes_and_original_R2_default_challenge(self):
        f = self.fixture
        for retire in (False, True):
            with self.subTest(retire=retire):
                g = f.guard(retire); g.reject_initial_full = True
                result = g.gate()
                self.assertFalse(result['trees'][ROW]['regular_bytes_verified'])
                self.assertIsNone(result['trees'][ROW]['tracked_mode_blob_source_inventory_sha256'])
        old = f.guard(False); old.reject_initial_full = True
        with self.assertRaisesRegex(f.Refused, '^synthetic_initial_full_tree_not_allowed$'):
            f.ns['legacy_gate'](old)
        self.assertIn(('tree', False), f.trace)

    def test_fresh_default_record_then_exact_eligible_reuse_with_honest_origin(self):
        f = self.fixture; f.prepare_prior()
        self.assertEqual(len(f.prior_custody['files']), 6)
        self.assertTrue(f.prior_custody['all_history_bytes_freshly_read_in_this_operation'])
        g = f.guard(True); f.bundle_for(g)
        g.inherit_historical_custody()
        self.assertEqual(set(g.inherited_history), set(ELIGIBLE))
        self.assertTrue(set(g.inherited_history).isdisjoint(g.passive_hashes))
        reads_before = len(f.read_calls)
        for pin in g.plan['historical_reference_files']:
            if pin['path'] in ELIGIBLE:
                g.pin_fact(pin)
        self.assertEqual(len(f.read_calls), reads_before)
        for route in CURRENT_PATHS:
            g.pin_fact(next(pin for pin in f.history if pin['path'] == route))
            self.assertEqual(f.read_calls[-1], route)
        g.record_historical_custody()
        self.assertFalse(g.facts['historical_byte_custody']['all_history_bytes_freshly_read_in_this_operation'])
        self.assertFalse(g.facts['inherited_history_origin']['fresh_byte_read_in_this_operation_claimed'])
        self.assertEqual(g.facts['historical_byte_custody']['inherited_history_files'], 2)

    def test_default_rejects_prior_bindings_and_metadata_cache_becomes_fresh_bytes(self):
        f = self.fixture; g = f.guard(False)
        g.inherit_historical_custody()
        g.initial_tracked_metadata_stats = {pin['path']: dict(pin['stat']) for pin in f.history}
        g.record_historical_custody()
        self.assertEqual(set(g.passive_hashes), {pin['path'] for pin in f.history})
        self.assertTrue(set(g.initial_tracked_metadata_stats).issubset(g.passive_hashes))
        bad = f.guard(False); bad.parent_review['successful_default_original_bindings'] = {}
        with self.assertRaisesRegex(f.Refused, '^default_cannot_inherit_historical_byte_custody$'):
            bad.inherit_historical_custody()

    def test_failed_source_scope_and_limit_receipts_refuse(self):
        cases = [
            ('failed', lambda r: r.update(admitted=False, failure='synthetic_failure')),
            ('wrong_source', lambda r: r.update(guard_source_sha256='0' * 64)),
            ('RAW_pass_missing', lambda r: r.update(full_raw_byte_passes=1)),
            ('counter_overflow', lambda r: r.update(bytes_read=16 * 1024**3 + 1)),
            ('old_full_tree_policy', lambda r: r['initial_checks']['trees'][ROW].update(regular_bytes_verified=True)),
            ('future_finish', lambda r: r.update(finished_at='2026-10-08T10:11:00+00:00')),
            ('prior_start_too_old', lambda r: r.update(started_at='2026-10-08T10:06:00+00:00',
                                                     finished_at='2026-10-08T10:07:00+00:00'))]
        for label, mutate in cases:
            with self.subTest(case=label):
                f = self.fresh(); g = f.guard(True); f.bundle_for(g, receipt_change=mutate)
                with self.assertRaises(f.Refused):
                    g.inherit_historical_custody()
        f = self.fresh(); g = f.guard(True); f.bundle_for(g)
        g.plan['original_raw_file_pins'] = []
        with self.assertRaisesRegex(f.Refused, '^original_default_history_coverage_changed$'):
            g.inherit_historical_custody()

    def test_missing_witness_wrong_projection_seal_stat_and_boolean_refuse(self):
        cases = [
            ('missing', lambda r: r['historical_byte_custody']['files'].pop()),
            ('projection', lambda r: r['historical_byte_custody'].update(historical_projection_sha256='0' * 64)),
            ('stat', lambda r: r['historical_byte_custody']['files'][0]['stat'].update(ino=0)),
            ('reference_type', lambda r: r['historical_byte_custody']['files'][0].update(reference_hits='false'))]
        for label, mutate in cases:
            with self.subTest(case=label):
                f = self.fresh(); g = f.guard(True); f.bundle_for(g, receipt_change=mutate)
                with self.assertRaises(f.Refused):
                    g.inherit_historical_custody()
        f = self.fresh(); g = f.guard(True); f.bundle_for(g, corrupt_receipt=True)
        with self.assertRaisesRegex(f.Refused, '^seal_changed$'):
            g.inherit_historical_custody()
        f = self.fresh(); g = f.guard(True)
        with self.assertRaisesRegex(f.Refused, '^retirement_requires_original_default_history_custody$'):
            g.inherit_historical_custody()
        for label, alter in (
                ('missing_True_policy', lambda b: b['original_guard_receipt'].pop('canonical_ensure_ascii')),
                ('wrong_status_file_SHA', lambda b: b['status'].update(sha256='0' * 64)),
                ('wrong_stdout_file_SHA', lambda b: b['stdout'].update(sha256='0' * 64))):
            with self.subTest(binding=label):
                f = self.fresh(); g = f.guard(True); f.bundle_for(g)
                alter(g.parent_review['successful_default_original_bindings'])
                with self.assertRaises(f.Refused):
                    g.inherit_historical_custody()

    def test_review_digest_backlinks_status_and_stdout_bindings_refuse(self):
        cases = [
            ('config', {'review_change': lambda r: r.update(reviewed_configuration_sha256='0' * 64)}),
            ('backlink', {'plan_change': lambda p: p['control_siblings_complete_review'].update(parent_review_identity_sha256='0' * 64)}),
            ('failed_status', {'status_change': lambda s: s.update(state='guard_failed', guard_exit_code=1)}),
            ('guard_status_source', {'status_change': lambda s: s['inputs']['guard'].update(sha256='0' * 64)}),
            ('receipt_return_pin', {'returned_change': lambda r: r.update(sha256='0' * 64)}),
            ('receipt_return_route', {'returned_change': lambda r: r.update(path=BASE + '/wrong/receipt.json')}),
            ('missing_wrapper_plan_pin', {'plan_change': lambda p: p.update(protected_file_pins=[])}),
            ('plan_too_old', {'plan_change': lambda p: p.update(checked_at='2026-10-08T09:00:00+00:00')})]
        for label, kwargs in cases:
            with self.subTest(case=label):
                f = self.fresh(); g = f.guard(True); f.bundle_for(g, **kwargs)
                with self.assertRaises(f.Refused):
                    g.inherit_historical_custody()

    def test_inherited_pin_precedes_fresh_cache_and_refuses_changed_pin(self):
        f = self.fixture; g = f.guard(True); f.bundle_for(g); g.inherit_historical_custody()
        original = next(pin for pin in f.history if pin['path'] == ELIGIBLE[0])
        g.passive_stats[original['path']] = copy.deepcopy(original['stat'])
        g.passive_hashes[original['path']] = '0' * 64
        g.pin_fact(original)  # The independent inherited map takes precedence.
        for key, replacement in [('bytes', original['bytes'] + 1), ('sha256', '0' * 64),
                                 ('stat', {**original['stat'], 'ino': 0})]:
            with self.subTest(field=key):
                changed = copy.deepcopy(original); changed[key] = replacement
                with self.assertRaisesRegex(f.Refused, '^inherited_history_pin_changed$'):
                    g.pin_fact(changed)

    def test_stat_mutation_and_same_bytes_inode_replacement_refuse_at_use_and_stable(self):
        for replacement in (False, True):
            with self.subTest(inode_replacement=replacement):
                f = self.fresh(); g = f.guard(True); f.bundle_for(g); g.inherit_historical_custody()
                route = ELIGIBLE[0]
                if replacement:
                    f.fs.replace_same_bytes(route)
                else:
                    path = f.fs.physical(route)
                    before = path.lstat(); body = path.read_bytes()
                    path.write_bytes(bytes([body[0] ^ 1]) + body[1:])
                    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                pin = next(pin for pin in f.history if pin['path'] == route)
                with self.assertRaisesRegex(f.Refused, '^inherited_history_file_identity_changed$'):
                    g.pin_fact(pin)
                with self.assertRaisesRegex(f.Refused, '^inherited_history_file_identity_changed$'):
                    g.stable_inventory()

    def test_RAW_and_PRIMARY_candidate_scope_never_inherits_and_each_gate_reads_RAW(self):
        f = self.fixture; g = f.guard(True); f.bundle_for(g); g.inherit_historical_custody()
        self.assertEqual(g.historical_custody_eligible_paths(), set(ELIGIBLE))
        self.assertTrue(set(CURRENT_PATHS).isdisjoint(g.inherited_history))
        before = f.read_calls.count(CURRENT_PATHS[0])
        g.gate(); g.gate(compare=False)
        self.assertEqual(f.read_calls.count(CURRENT_PATHS[0]) - before, 2)

    def test_each_pre_retire_gate_requires_fresh_full_tree_library_and_source_bytes(self):
        f = self.fixture; g = f.guard(True)
        g.plan['receipt_source_file_proofs'] = f.make_proofs()
        g.baseline[ROW] = f.tree(g, False)
        before = len(f.read_calls)
        current = g.pre_retire_gate(ROW)
        self.assertTrue(current['regular_bytes_verified'])
        self.assertIn(('tree', True), f.trace)
        self.assertIn(('library', True), f.trace)
        new_reads = f.read_calls[before:]
        for route in (CURRENT_PATHS[-1], f.library['path'],
                      BASE + '/' + ROW + '/swdb-project/second.cpp'):
            self.assertIn(route, new_reads)
        self.assertEqual(sum(item[0] == 'Git_blob' for item in f.trace if isinstance(item, tuple)), 2)
        g.tree = lambda *args, **kwargs: copy.deepcopy(g.baseline[ROW])
        with self.assertRaisesRegex(f.Refused, '^full_pre_retire_regular_byte_check_required$'):
            g.pre_retire_gate(ROW)

    def test_duplicate_receipt_parse_once_per_call_but_every_field_physical_and_Git_check(self):
        f = self.fixture; g = f.guard(False)
        g.plan['historical_reference_files'] = []
        g.plan['receipt_source_file_proofs'] = f.make_proofs()
        start = f.ns['parse_calls']; before = f.read_calls.count(f.proof_route)
        g.aliases_and_sources()
        self.assertEqual(f.ns['parse_calls'] - start, 1)
        self.assertEqual(f.read_calls.count(f.proof_route) - before, 1)
        for relative in ('swdb-project/fixture.cpp', 'swdb-project/second.cpp'):
            self.assertIn(BASE + '/' + ROW + '/' + relative, f.read_calls)
        self.assertEqual(sum(item[0] == 'Git_blob' for item in f.trace if isinstance(item, tuple)), 2)
        g.aliases_and_sources()
        self.assertEqual(f.ns['parse_calls'] - start, 2)
        self.assertEqual(f.read_calls.count(f.proof_route) - before, 2)

    def test_duplicate_receipt_second_field_and_physical_bytes_still_refuse(self):
        for wrong_physical in (False, True):
            with self.subTest(wrong_physical=wrong_physical):
                f = self.fresh(); g = f.guard(False)
                g.plan['historical_reference_files'] = []
                g.plan['receipt_source_file_proofs'] = f.make_proofs()
                if wrong_physical:
                    f.fs.put(BASE + '/' + ROW + '/swdb-project/second.cpp', b'WRONG synthetic bytes\n')
                    expected = '^receipt_source_byte_proof_changed$'
                else:
                    g.plan['receipt_source_file_proofs'][1]['receipt_json_path'] = ['first']
                    expected = '^original_source_hash_field_changed$'
                with self.assertRaisesRegex(f.Refused, expected):
                    g.aliases_and_sources()
                self.assertEqual(f.read_calls.count(f.proof_route), 1)
                self.assertEqual(sum(item[0] == 'Git_blob' for item in f.trace if isinstance(item, tuple)), 2)

    def test_cached_receipt_same_bytes_inode_swap_before_second_field_refuses(self):
        f = self.fixture; g = f.guard(False)
        g.plan['historical_reference_files'] = []
        g.plan['receipt_source_file_proofs'] = f.make_proofs()
        calls = []
        original_git = g.git

        def replace_before_second(root, *args):
            calls.append(args)
            if len(calls) == 2:
                f.fs.replace_same_bytes(f.proof_route)
            return original_git(root, *args)
        g.git = replace_before_second
        with self.assertRaisesRegex(f.Refused, '^source_proof_cached_original_receipt_changed$'):
            g.aliases_and_sources()
        self.assertEqual(f.read_calls.count(f.proof_route), 1)
        self.assertEqual(len(calls), 2)


    def test_compact_receipt_345_witnesses_preserves_whole_object_True_seal(self):
        f = self.fixture; g = f.guard(False)
        sample = f.history[0]
        witnesses = []
        for index in range(345):
            witnesses.append({'path': RAW + '/lanl-isolated-history-long-20261008-a1/'
                              + ('nested-' * 7) + '/original-' + str(index) + '.json',
                              'bytes': 1000 + index, 'sha256': 'a' * 64,
                              'stat': {**sample['stat'], 'size': 1000 + index,
                                       'ino': 20000 + index}, 'reference_hits': bool(index % 2)})
        g.facts.update(format='swdb.library-preserving-sparse-retirement-guard.v1',
                       canonical_ensure_ascii=True, admitted=True, failure=None,
                       historical_byte_custody={
                           'format': 'swdb.original-historical-byte-custody.v1',
                           'all_history_bytes_freshly_read_in_this_operation': True,
                           'inherited_history_files': 0,
                           'historical_projection_sha256': 'b' * 64, 'files': witnesses},
                       initial_checks={'synthetic': 'no original actual record fields'},
                       guard_source_sha256=SOURCE_SHA)
        g.walk_entries = 345
        raw = f.ns['compact_publication_prefix'](g)
        self.assertLessEqual(len(raw), 256 * 1024)
        self.assertEqual(raw[-1:], b'\n')
        decoded = json.loads(raw)
        identity = decoded.pop('identity_sha256')
        self.assertEqual(digest(wire(decoded)), identity)
        self.assertEqual(decoded['historical_byte_custody']['files'], witnesses)
        self.assertEqual(len(decoded['historical_byte_custody']['files']), 345)
        self.assertTrue(decoded['canonical_ensure_ascii'])
        self.assertNotIn(b'\n  ', raw)

    def test_compact_receipt_oversize_refuses_before_any_native_or_publication_boundary(self):
        f = self.fixture; g = f.guard(False)
        g.facts.update(canonical_ensure_ascii=True, admitted=False, failure='synthetic',
                       synthetic_padding='x' * (256 * 1024))
        g.walk_entries = 0
        with self.assertRaisesRegex(f.Refused, '^compact_receipt_limit$'):
            f.ns['compact_publication_prefix'](g)
        self.assertFalse(f.fs.physical(BASE + '/receipt.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
