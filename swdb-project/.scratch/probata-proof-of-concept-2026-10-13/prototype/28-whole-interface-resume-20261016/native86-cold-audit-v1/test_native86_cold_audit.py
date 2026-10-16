"""2026-10-16 ET. No-child tiny synthetic cold-reader controls.

No actual cold audit or record/evidence acceptance is invoked. Remote names in
recipe fixtures are inert strings. Temporary raw fixtures contain zero bytes,
not scientific source/binary artifacts. All generated files are temporary.
"""
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
EVENTS = []


def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event == 'os.system':
        EVENTS.append(event); raise RuntimeError('pure passive-native controls refuse ' + event)


sys.addaudithook(no_child)
reader = {'__name__': 'inert_passive_native86', '__file__': str(HERE / 'native86_cold_audit.py')}
exec(compile((HERE / 'native86_cold_audit.py').read_text(), reader['__file__'], 'exec'), reader)


def pin(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


class NativeColdControls(unittest.TestCase):
    def test_strict_json_and_exact_census(self):
        self.assertEqual(reader['strict_json']('{"x":1}'), {'x': 1})
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises((AssertionError, ValueError)): reader['strict_json'](value)
        self.assertEqual(reader['result_census'](dict(reader['RESULT'])), reader['RESULT'])
        for value in (dict(reader['RESULT'], controls=85), dict(reader['RESULT'], history_cases=True),
                      dict(reader['RESULT'], extra=0), {k: v for k, v in reader['RESULT'].items() if k != 'refusals'}):
            with self.assertRaises(AssertionError): reader['result_census'](value)

    def test_physical_bytes_types_aliases_and_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); path = root / 'data'; path.write_bytes(b'bounded')
            physical = reader['Physical'](); row = pin(path)
            self.assertEqual(physical.pin(path, row), row); self.assertEqual(physical.read(row), b'bounded')
            physical.unchanged()
            for value in (dict(row, bytes=True), dict(row, sha256='0' * 64)):
                with self.assertRaises(AssertionError): physical.read(value)
            alias = root / 'alias'; alias.symlink_to(path)
            with self.assertRaises(AssertionError): reader['Physical']().pin(alias)
            path.write_bytes(b'changed')
            with self.assertRaises(AssertionError): physical.unchanged()
            path.unlink(); os.mkfifo(path)
            with self.assertRaises(AssertionError): reader['Physical']().pin(path)

    def test_complete_raw_membership_and_schema(self):
        # Exact fixed size/count exercise the actual census function without
        # using any real raw data or executing the complete cold audit.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for index in range(62): (root / ('file-' + str(index))).write_bytes(b'')
            with (root / 'file-0').open('wb') as stream:
                remaining = 9587978
                while remaining:
                    size = min(remaining, 65536); stream.write(bytes(size)); remaining -= size
            rows = [{'relative': p.name, 'bytes': p.stat().st_size, 'sha256': pin(p)['sha256']} for p in sorted(root.iterdir())]
            expected = {'files': rows, 'directories': []}
            original = reader['RAW']; reader['RAW'] = str(root)
            try:
                self.assertEqual(len(reader['raw_snapshot'](root, expected, reader['Physical']())), 62)
                changed = copy.deepcopy(expected); changed['files'][1]['bytes'] = False
                with self.assertRaises(AssertionError): reader['raw_snapshot'](root, changed, reader['Physical']())
                (root / 'unknown').write_bytes(b'')
                with self.assertRaises(AssertionError): reader['raw_snapshot'](root, expected, reader['Physical']())
                (root / 'unknown').unlink(); (root / 'file-1').unlink(); (root / 'file-1').symlink_to(root / 'file-2')
                with self.assertRaises(AssertionError): reader['raw_snapshot'](root, expected, reader['Physical']())
            finally: reader['RAW'] = original

    def test_resources_refuse_unhealthy_nonfinite_or_boolean(self):
        valid = {'exit_code': 0, 'out_of_memory': False, 'timed_out': False,
                 'peak_rss_bytes': 1024, 'wall_seconds': 1.0, 'cpu_seconds': 2.0}
        reader['resource_result'](valid)
        for field, value in (('exit_code', True), ('exit_code', 1), ('out_of_memory', True),
                ('timed_out', True), ('peak_rss_bytes', True), ('peak_rss_bytes', 4294967297),
                ('wall_seconds', float('nan')), ('wall_seconds', 180.01), ('cpu_seconds', -1)):
            with self.subTest(field=field, value=value), self.assertRaises(AssertionError): reader['resource_result'](dict(valid, **{field: value}))

    def test_eight_exact_recipes_and_sanitizer_output(self):
        raw = Path('/inert-only/native-root'); policy = {'compiler': {'command': ['/inert-only/clang-wrapper'], 'linker': {'path': '/inert-only/ld.bfd'}}}
        expected = reader['recipe'](policy, raw); self.assertEqual(len(expected), 8)
        files, commands = {}, []
        payload = json.dumps(reader['RESULT']).encode()
        class InertPhysical:
            def read(self, row, maximum): return payload
        for name, argv, maximum in expected:
            stream_rows = {}
            for stream in ('stdout', 'stderr'):
                data = payload if name.endswith('-run') and stream == 'stdout' else b''
                row = {'path': str(raw / 'component' / (name + '.' + stream)), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                files['component/' + name + '.' + stream] = row; stream_rows[stream] = row
            commands.append({'name': name, 'argv': argv, 'cwd': str(raw / 'component'), 'timeout_seconds': maximum, 'returncode': 0, **stream_rows})
        reader['check_commands'](commands, policy, raw, files, InertPhysical())
        for mutation in ('missing', 'argv', 'linker', 'no_sanitizer', 'timeout', 'exit', 'native_stderr'):
            changed = copy.deepcopy(commands)
            if mutation == 'missing': changed.pop()
            elif mutation == 'argv': changed[0]['argv'].append('-DNDEBUG')
            elif mutation == 'linker': changed[2]['argv'] = [arg for arg in changed[2]['argv'] if not arg.startswith('-fuse-ld=')]
            elif mutation == 'no_sanitizer': changed[1]['argv'].remove('-fsanitize=address,undefined')
            elif mutation == 'timeout': changed[0]['timeout_seconds'] = math.inf
            elif mutation == 'exit': changed[0]['returncode'] = True
            else: changed[3]['stderr']['bytes'] = 1
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError): reader['check_commands'](changed, policy, raw, files, InertPhysical())

    def test_manifest_requires_all_29_exact_unique_rows(self):
        files, manifest = {}, []
        for index in range(29):
            name = 'file-' + str(index)
            row = {'path': '/inert-only/component/' + name, 'bytes': index, 'sha256': '0' * 64}
            files['component/' + name] = row; manifest.append({'relative': name, **row})
        reader['artifact_manifest'](manifest, files)
        for changed in (manifest[:-1], [*manifest[:-1], manifest[0]], [dict(row, bytes=True) if row['relative'] == 'file-1' else row for row in manifest]):
            with self.assertRaises(AssertionError): reader['artifact_manifest'](changed, files)

    def test_exact_passive_functions_never_execute_entry(self):
        source = (HERE.parent / 'linux_native86_entry_v4.py').read_bytes()
        helpers = reader['passive_entry'](source + b'\nraise RuntimeError("entry must never execute")\n', reader['Physical']())
        self.assertTrue(callable(helpers['make_dependencies']))
        self.assertNotIn('main', helpers); self.assertNotIn('verified_linux_lane', helpers)
        self.assertFalse(any(key.startswith('subprocess') for key in helpers))

    def test_no_child_network_or_filesystem_write_guard(self):
        for event in ('subprocess.Popen', 'os.execve', 'os.fork', 'socket.connect', 'ctypes.dlopen',
                      'os.remove', 'os.mkdir', 'os.chmod', 'os.symlink', 'os.utime'):
            with self.assertRaises(RuntimeError): reader['deny'](event, ())
        for mode, flags in (('w', 0), ('a', 0), ('r+', 0), (None, 1), (None, 2), (None, 64), (None, 512), (None, 1024)):
            with self.assertRaises(RuntimeError): reader['deny']('open', ('/inert', mode, flags))
        reader['deny']('open', ('/inert', 'r', 0))
        self.assertEqual(EVENTS, [])

    def test_template_is_unadmitted_and_source_scope_has_no_actual_reexecution(self):
        policy = json.loads((HERE / 'native86-cold-policy-template.json').read_text())
        self.assertFalse(policy['admitted']); self.assertFalse(policy['reader_admission']['admitted'])
        self.assertIsNone(policy['reader']['path'])
        self.assertEqual(set(policy['reader_admission']['environment']), reader['ADMISSION_ENV_KEYS'])
        source = (HERE / 'native86_cold_audit.py').read_text(); module = ast.parse(source)
        for node in module.body:
            if isinstance(node, ast.Import): self.assertFalse(any(alias.name.startswith(('swdb', 'yaml', 'subprocess', 'socket', 'ctypes')) for alias in node.names))
            if isinstance(node, ast.ImportFrom): self.assertFalse((node.module or '').startswith(('swdb', 'yaml', 'subprocess')))
        self.assertIn('no separate raw final-null watchdog field is inferred', source)
        self.assertIn('No continuing absence guarantee', source)
        self.assertEqual(EVENTS, [])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeColdControls))
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun == 9 and not result.skipped and not EVENTS else 1)
