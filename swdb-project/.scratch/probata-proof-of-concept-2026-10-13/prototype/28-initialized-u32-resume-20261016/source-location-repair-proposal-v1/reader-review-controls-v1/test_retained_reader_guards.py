"""2026-10-16 ET. Independent pure controls for retained-reader guard code.

No remote paths are opened. Small filesystem cases and explicit main-prefix
stand-ins exercise actual reader functions; they are not retained replay runs.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent
BLOCKED = []


def child_audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.', 'ctypes.dlopen')) or event in {'os.system', 'os.fork', 'os.forkpty'}:
        BLOCKED.append(event)
        raise RuntimeError('no child/native/network execution allowed in pure review controls')


sys.addaudithook(child_audit)


def load_reader(path):
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.Assign, ast.FunctionDef, ast.ClassDef))]
    namespace = {'ast': ast, 'hashlib': hashlib, 'json': json, 'Path': Path, 're': re, 'sys': sys}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace, tree


def pin(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


class ReaderGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader, cls.tree = load_reader(PROPOSAL / 'replay_retained_observation_v1.py')
        cls.before, cls.before_tree = load_reader(HERE / 'reader-before-review.py')

    def test_exact_source_namespaces_are_import_free_and_complete(self):
        source_rows = [{'path': '/control/source' + str(index), 'bytes': 0, 'sha256': '0' * 64} for index in range(7)]
        for name in ('base-source.py', 'proposed-source.py'):
            namespace = self.reader['namespace']((PROPOSAL / name).read_bytes(), 'CONTROL CALLER', {}, source_rows)
            wanted = set(self.reader['FUNCTIONS'])
            if name == 'base-source.py': wanted.remove('_assert_source_location_diagnostics')
            self.assertTrue(wanted <= set(namespace))
            source = ast.parse((PROPOSAL / name).read_text())
            selected = [node for node in source.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
            self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom)) for root in selected for node in ast.walk(root)))

    def test_regular_pin_canonical_extent_and_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); file = root / 'x'; file.write_bytes(b'bounded')
            self.assertEqual(self.reader['regular'](file, pin(file)['sha256']), b'bounded')
            for path, digest in ((file, '0' * 64), (root / 'absent', None), (root, None)):
                with self.subTest(path=str(path), digest=digest), self.assertRaises((ValueError, OSError)):
                    self.reader['regular'](path, digest)
            link = root / 'link'; link.symlink_to(file)
            with self.assertRaises(ValueError): self.reader['regular'](link)

    def test_regular_refuses_mutation_during_read_and_excessive_extent(self):
        class FakePath:
            def __init__(self, mutate=False, big=False): self.calls = 0; self.mutate = mutate; self.big = big
            def is_symlink(self): return False
            def resolve(self): return self
            def is_file(self): return True
            def stat(self):
                self.calls += 1
                return SimpleNamespace(st_dev=1, st_ino=2, st_size=64 * 2**20 + 1 if self.big else 1,
                                       st_mtime_ns=self.calls if self.mutate else 1, st_ctime_ns=1)
            def read_bytes(self):
                if self.big: raise AssertionError('oversized file was read')
                return b'x'
        for path in (FakePath(mutate=True), FakePath(big=True)):
            with self.assertRaises(ValueError): self.reader['regular'](path)

    def test_snapshot_requires_closed_membership_and_all_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); file = root / 'x'; file.write_bytes(b'x')
            wanted = {'x': pin(file)}
            value = self.reader['retained_snapshot'](root, wanted)
            self.assertTrue(value)
            (root / 'extra').write_bytes(b'')
            with self.assertRaises(ValueError): self.reader['retained_snapshot'](root, wanted)
            (root / 'extra').unlink(); file.write_bytes(b'y')
            with self.assertRaises(ValueError): self.reader['retained_snapshot'](root, wanted)
            file.write_bytes(b'x'); wanted['x']['bytes'] = 2
            with self.assertRaises(ValueError): self.reader['retained_snapshot'](root, wanted)

    def test_header_read_adapter_binds_actual_bytes_extent_and_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); rows = []
            for index in range(7):
                path = root / str(index); path.write_bytes(b'one\r\ntwo\rthree\n')
                rows.append({'path': str(path), **pin(path)})
            path_type = self.reader['pinned_path_type'](rows)
            self.assertEqual(path_type(rows[0]['path']).read_text(), 'one\ntwo\nthree\n')
            unknown = root / 'unknown'; unknown.write_bytes(b'')
            with self.assertRaises(ValueError): path_type(unknown).read_text()
            Path(rows[0]['path']).write_bytes(b'changed')
            with self.assertRaises(ValueError): path_type(rows[0]['path']).read_text()
            rows[1]['bytes'] += 1
            with self.assertRaises(ValueError): self.reader['pinned_path_type'](rows)(rows[1]['path']).read_text()
            for bad in (rows[:-1], [*rows[:-1], rows[0]]):
                with self.assertRaises(ValueError): self.reader['pinned_path_type'](bad)

    def test_real_main_prefix_old_red_revised_cached_bytes_green(self):
        # Execute the actual main statements through both namespace creations.
        # All filesystem inputs here are inert stand-ins; no remote read occurs.
        def execute_prefix(reader, tree, want_cache):
            context = dict(reader)
            source = b'CONTROL source'
            modules = {
                'swdb/dx100_initialized_register_source.py': source,
                'swdb/dx100_initialized_register_model.py': b'CALLER = "CONTROL caller"\n',
                'swdb/dx100_size_source.py': b'SOURCE_PINS = {"control.hpp": "CONTROL digest"}\n',
            }
            context['SOURCE_PINS'] = {name: hashlib.sha256(data).hexdigest() for name, data in modules.items()}
            diagnostic = {'status': 'DIAGNOSTIC_REPRODUCED_SOURCE_REFUSAL',
                          'capture_completion': {'accepted': True},
                          'retained_files': [{'name': str(index), 'bytes': 1, 'sha256': '0' * 64} for index in range(32)]}
            rows = [{'path': '/control/' + str(index), 'bytes': 0, 'sha256': '0' * 64} for index in range(7)]
            payloads = {'observation-source-pins.json': json.dumps(rows).encode()}
            calls = []; namespaces = []
            def regular(path, digest=None):
                path = str(path); prefix = str(context['PROJECT']) + '/'
                if path.startswith(prefix):
                    relative = path[len(prefix):]
                    if digest != context['SOURCE_PINS'][relative]:
                        raise ValueError('CONTROL unpinned project reread')
                    calls.append(relative)
                    return modules[relative]
                if path.endswith('/diagnostic-result.json'):
                    self.assertEqual(digest, context['RESULT_SHA'])
                    return json.dumps(diagnostic).encode()
                raise ValueError('CONTROL unlisted read')
            def namespace(data, caller, source_pins, *args):
                self.assertEqual(caller, 'CONTROL caller')
                self.assertEqual(source_pins, {'control.hpp': 'CONTROL digest'})
                namespaces.append(data)
                return {'CONTROL bytes': data}
            def snapshot(root, expected):
                self.assertEqual(len(expected), 32)
                return ({}, payloads) if want_cache else {}
            context.update(regular=regular, namespace=namespace, retained_snapshot=snapshot)
            function = next(node for node in ast.parse(ast.unparse(tree)).body if isinstance(node, ast.FunctionDef) and node.name == 'main')
            kept = []
            for node in function.body:
                kept.append(node)
                if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'new' for target in node.targets): break
            else: raise AssertionError('main namespace seam missing')
            function.body = [*kept, ast.Return(value=ast.Constant(value=None))]
            literal = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'literal')
            exec(compile(ast.fix_missing_locations(ast.Module(body=[literal, function], type_ignores=[])), '<actual-main-prefix>', 'exec'), context)
            proposed = (PROPOSAL / 'proposed-source.py').read_text()
            context['main'](proposed)
            self.assertEqual(sorted(calls), sorted(modules))
            self.assertEqual(namespaces, [source, proposed.encode()])
        with self.assertRaisesRegex(ValueError, 'CONTROL unpinned project reread'):
            execute_prefix(self.before, self.before_tree, False)
        execute_prefix(self.reader, self.tree, True)

    def test_retained_payload_consumption_has_no_unchecked_reread(self):
        main = next(node for node in self.tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        unchecked = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == 'regular' and len(node.args) < 2]
        self.assertEqual(unchecked, [])
        snapshots = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == 'retained_snapshot']
        self.assertEqual(len(snapshots), 2)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); file = root / 'x'; file.write_bytes(b'checked bytes')
            pins, data = self.reader['retained_snapshot'](root, {'x': pin(file)})
            self.assertEqual(data, {'x': b'checked bytes'})
            file.write_bytes(b'changed bytes')
            self.assertEqual(data, {'x': b'checked bytes'})
            with self.assertRaises(ValueError): self.reader['retained_snapshot'](root, pins)

    def test_audit_denies_children_network_and_content_writes(self):
        for event in ('subprocess.Popen', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.connect',
                      'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen', 'os.remove',
                      'os.rename', 'os.rmdir', 'os.mkdir', 'os.link', 'os.symlink', 'os.truncate'):
            with self.subTest(event=event), self.assertRaises(RuntimeError): self.reader['deny'](event, ())
        for flags in (1, 2, 64, 512, 1024):
            with self.subTest(flags=flags), self.assertRaises(RuntimeError): self.reader['deny']('open', ('/control', None, flags))
        for mode in ('w', 'a', 'x', 'r+'):
            with self.subTest(mode=mode), self.assertRaises(RuntimeError): self.reader['deny']('open', ('/control', mode, 0))
        self.reader['deny']('open', ('/control', 'r', 0))

    def test_replay_output_boundary_remains_diagnostic_only(self):
        constants = [node.value for node in ast.walk(self.tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
        self.assertIn('RETAINED_OBSERVER_REPLAY_PASS', constants)
        self.assertIn('Exact diagnostic AST/token/LLVM replay only; no fresh compiler, native execution, WP, solver or public proof result', constants)
        self.assertIn('source_body_proof', constants)
        self.assertEqual(self.reader['PROPOSAL_SHA'], pin(PROPOSAL / 'proposed-source.py')['sha256'])
        self.assertEqual(self.reader['SOURCE_PINS']['swdb/dx100_initialized_register_source.py'], pin(PROPOSAL / 'base-source.py')['sha256'])
        self.assertEqual(BLOCKED, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
