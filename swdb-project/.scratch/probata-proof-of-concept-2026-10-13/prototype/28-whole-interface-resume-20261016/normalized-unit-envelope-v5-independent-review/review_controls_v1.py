"""2026-10-16 ET. Independent no-child observer source controls."""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / 'normalized-unit-envelope-v5'
PACKET = ROOT / 'source-packet-v5.json'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise AssertionError('observer source review blocks external execution: ' + event)


sys.addaudithook(audit)


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def rows(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= set(value):
            yield value
        for item in value.values():
            yield from rows(item)
    elif isinstance(value, list):
        for item in value:
            yield from rows(item)


def snapshot():
    selected = list(rows(json.loads(PACKET.read_bytes())))
    for row in selected:
        assert pin(Path(row['path'])) == {key: row[key] for key in ('path', 'bytes', 'sha256')}
    return selected


before = snapshot()
inverse = json.loads((ROOT / 'exact-inverses-v5.json').read_bytes())
for relative, row in inverse['files'].items():
    text = (ROOT / relative).read_text()
    for change in reversed(row['replacements']):
        assert text.count(change['new']) == change['count'], relative
        text = text.replace(change['new'], change['old'])
    assert text.encode() == Path(row['basis']['path']).read_bytes(), relative
    ast.parse((ROOT / relative).read_bytes())

suite = unittest.TestSuite()
for index, filename in enumerate(('test_envelope_v5.py', 'test_root_environment_v5.py', 'test_semantic_observer_v5.py')):
    spec = importlib.util.spec_from_file_location('_independent_semantic_observer_' + str(index), ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
(HERE / 'fresh-pure-controls-v1.log').write_text(stream.getvalue())
assert result.testsRun == 23 and result.wasSuccessful() and not result.skipped
assert not EVENTS and snapshot() == before
command = json.loads((ROOT / 'command-v5.json').read_bytes())
policy = json.loads((ROOT / 'envelope-policy-v5.json').read_bytes())
stages = command['stage_sources']
assert len(stages) == 30
assert sum(row['bytes'] for row in stages.values()) + (ROOT / 'envelope-policy-v5.json').stat().st_size == 479538
for name, row in stages.items():
    assert pin(Path(row['path'])) == row
    assert policy['controls'][name]['sha256'] == row['sha256']
print(json.dumps(dict(date='2026-10-16 Eastern', packet=pin(PACKET), pin_occurrences=len(before), exact_declared_inverses=True, tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), skips=len(result.skipped), denied_attempts=EVENTS, root_controls=30, separate_envelope_policy=1, total_flat_staged_files=31, root_stage_bytes=479538, actual_scientific_or_remote_execution=False), sort_keys=True))
