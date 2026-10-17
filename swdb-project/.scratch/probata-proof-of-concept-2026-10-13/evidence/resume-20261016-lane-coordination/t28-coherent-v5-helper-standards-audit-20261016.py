"""2026-10-16 ET. Independent local V5 byte/inverse and no-child controls audit.

No shared application, Git, compiler, verifier, native or SSH action is permitted.
Frozen producer/test files are read; all output goes beside this review script.
"""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import signal
import stat
import sys
import unittest

HERE = Path(__file__).resolve().parent
POC = HERE.parents[1]
WHOLE = POC/'prototype/28-whole-interface-resume-20261016'
V4 = WHOLE/'production-route-v4'
V5 = WHOLE/'production-route-v5'
LINEAGE = WHOLE/'production-route-v5-independent-review/helper-byte-lineage-v5.json'
EXPECTED = {
    V5/'source-packet-v5.json': '60d69b94c7dddc9040adee699cfdda17503aff66f295b90565401f90ddbc119b',
    V4/'source-packet-v4.json': '7e36fbf2dc634a62e1c9eb4350005d308f8ab3c32a44fc522e2abdafa9eb1565',
    LINEAGE: '18238c7eb194e1c0d11fc969a0644a58b05987be5edf13a51264e351f3227b1b',
}


def pin(path):
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and not path.is_symlink()
    raw = path.read_bytes()
    fields = lambda row: tuple(getattr(row, name) for name in ('st_dev', 'st_ino', 'st_mode',
        'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
    assert fields(before) == fields(path.lstat())
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


documents = {}
for path, wanted in EXPECTED.items():
    assert pin(path)['sha256'] == wanted
    documents[path] = json.loads(path.read_bytes())
paths_path = Path(documents[V4/'source-packet-v4.json']['production_paths_and_exact_bases']['path'])
documents[paths_path] = json.loads(paths_path.read_bytes())
occurrences = []


def verify(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= set(value) and isinstance(value['path'], str) and Path(value['path']).is_absolute():
            actual = pin(Path(value['path']))
            assert actual == {key: value[key] for key in actual}
            occurrences.append(actual)
        for member in value.values():
            verify(member)
    elif isinstance(value, list):
        for member in value:
            verify(member)


for value in documents.values():
    verify(value)
before = {row['path']: pin(Path(row['path'])) for row in occurrences}
inverse = json.loads((V5/'builder-inverse-v5.json').read_bytes())
builder = (V5/'profile/profile_builder_v4.py').read_text()
for row in reversed(inverse['replacements']):
    assert builder.count(row['new']) == 1
    builder = builder.replace(row['new'], row['old'], 1)
assert builder == (V4/'profile/profile_builder_v3.py').read_text()
preparer = (V5/'profile/profile_prepare_v4.py').read_text()
for new, old in inverse['preparer_inverse_names'].items():
    preparer = preparer.replace(new, old)
preparer = preparer.replace(pin(V5/'profile/profile_builder_v4.py')['sha256'], pin(V4/'profile/profile_builder_v3.py')['sha256'])
assert preparer == (V4/'profile/profile_prepare_v3.py').read_text()
for path in (V5/'profile/profile_builder_v4.py', V5/'profile/profile_prepare_v4.py'):
    ast.parse(path.read_bytes())
for row in documents[LINEAGE]['helpers']:
    proposal = Path(row['proposal']['path']).read_bytes()
    for origin in row['lineage']:
        assert Path(origin['pin']['path']).read_bytes() == proposal
attempts = []


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        attempts.append(event)
        raise AssertionError('independent V5 review forbids child/native/network')
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        attempts.append('project import')
        raise AssertionError('independent V5 review forbids project imports')


sys.addaudithook(deny)
sys.dont_write_bytecode = True
signal.alarm(60)
namespace = runpy.run_path(str(V5/'test_profile_streams_v5.py'), run_name='independent_v5_controls')
suite = unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace['PRIOR']['CompositionControls']))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace['StreamControls']))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
assert result.testsRun == 29 and result.wasSuccessful() and not result.skipped and not attempts
for path, observed in before.items():
    assert pin(Path(path)) == observed
signal.alarm(0)
log = HERE/'t28-coherent-v5-helper-standards-controls-20261016.log'
with log.open('x') as handle:
    handle.write(stream.getvalue())
out = {'date': '2026-10-16 ET', 'pin_occurrences_verified': len(occurrences),
       'unique_paths_verified': len(before), 'all_selected_bytes_before_after_equal': True,
       'helper_count': len(documents[LINEAGE]['helpers']), 'all_declared_origin_bytes_exact': True,
       'builder_full_inverse': True, 'preparer_names_and_pin_inverse': True,
       'no_child_controls': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures),
       'skips': len(result.skipped), 'forbidden_events': attempts, 'controls_log': pin(log),
       'shared_apply_Git_native_compiler_solver_SSH_or_actual_preparation': False,
       'basis': [pin(path) for path in documents], 'verified_pins': list(before.values())}
path = HERE/'t28-coherent-v5-helper-standards-controls-20261016.json'
with path.open('x') as handle:
    json.dump(out, handle, sort_keys=True, indent=2)
    handle.write('\n')
print(json.dumps({'result': pin(path), 'tests': result.testsRun, 'pin_occurrences': len(occurrences), 'unique_paths': len(before)}))
