"""Independent no-child inverse, pin and representative environment controls."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
NEW = WHOLE / 'normalized-unit-envelope-v3'
OLD = WHOLE / 'normalized-unit-envelope-v2'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('independent review prohibits child/native/network')


sys.addaudithook(audit)


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def replacements(value, pairs):
    if isinstance(value, str):
        for new, old in pairs:
            value = value.replace(new, old)
        return value
    if isinstance(value, dict):
        return {replacements(key, pairs): replacements(item, pairs) for key, item in value.items()}
    if isinstance(value, list):
        return [replacements(item, pairs) for item in value]
    return value


packet = json.loads((NEW / 'source-packet-v3.json').read_bytes())
checked = []


def check_rows(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= set(value):
            assert pin(Path(value['path'])) == value
            checked.append(value)
        for item in value.values():
            check_rows(item)
    elif isinstance(value, list):
        for item in value:
            check_rows(item)


check_rows(packet)
pairs = [
    ('t28-unit-observation-2baf722f-v3', 't28-unit-observation-2baf722f-v2'),
    ('normalized-unit-envelope-v3/', 'normalized-unit-envelope-v2/'),
    ('linux_observation_envelope_v3.py', 'linux_observation_envelope_v2.py'),
    ('envelope-policy-v3.json', 'envelope-policy-v2.json'),
]
new_entry = NEW / 'linux_observation_envelope_v3.py'
old_entry = OLD / 'linux_observation_envelope_v2.py'
assert replacements(new_entry.read_text(), pairs) == old_entry.read_text()
new_policy = json.loads((NEW / 'envelope-policy-v3.json').read_bytes())
old_policy = json.loads((OLD / 'envelope-policy-v2.json').read_bytes())
new_observer = json.loads((NEW / 'observation-policy-v1.json').read_bytes())
old_observer = json.loads((OLD / 'observation-policy-v1.json').read_bytes())
assert replacements(new_observer, pairs) == old_observer
digest_pairs = [
    (pin(new_entry)['sha256'], pin(old_entry)['sha256']),
    (pin(NEW / 'observation-policy-v1.json')['sha256'], pin(OLD / 'observation-policy-v1.json')['sha256']),
    (pin(NEW / 'envelope-policy-v3.json')['sha256'], pin(OLD / 'envelope-policy-v2.json')['sha256']),
]
assert replacements(new_policy, pairs + digest_pairs) == old_policy
new_command = json.loads((NEW / 'command-v3.json').read_bytes())
old_command = json.loads((OLD / 'command-v2.json').read_bytes())
inverse_command = replacements(new_command, pairs + digest_pairs)
inverse_command['root_launcher'] = copy.deepcopy(old_command['root_launcher'])
inverse_command['root_launch_requirements']['run_environment_unset'] = ['LIBRARY_PATH']
assert inverse_command == old_command
staged = new_command['stage_sources']
assert len(staged) == 27
for name, row in staged.items():
    assert pin(Path(row['path'])) == row
assert sum(row['bytes'] for row in staged.values()) + new_command['policy']['bytes'] == 434627
assert new_command['guard'] == old_command['guard']
assert new_command['root_launch_requirements']['run_environment_unset'] == ['LIBRARY_PATH', 'LD_LIBRARY_PATH']

snapshot = json.loads((WHOLE.parent.parent / 'evidence/resume-20261016-lane-coordination/mbit10-preflight-and-wrapper-snapshots.json').read_bytes())
rows = snapshot['wrapper_snapshots']
if isinstance(rows, dict):
    rows = list(rows.values())
for name, original, adapted in [
    ('execute.py', 'ea774376', '8442533f911e2ba7f10757a5b16ba451d4ece7d9d5dc292ce5b9d8c29eabdcbf'),
    ('watch.py', '4485ae66', '49be8a36d6e04b50e1ab599dad8b00f78a1c639132c3079c523c2c0c9177c5f0'),
]:
    source = next(row['content'] for row in rows if row['path'].endswith('/' + name))
    assert hashlib.sha256(source.encode()).hexdigest().startswith(original)
    assert hashlib.sha256(source.replace('8589934592', '4294967296').encode()).hexdigest() == adapted
    assert new_policy['guard_files'][name] == adapted

suite = unittest.TestSuite()
for name, cls in [('test_envelope_v3.py', 'Controls'), ('test_root_environment_v3.py', 'RootEnvironmentControls')]:
    namespace = runpy.run_path(str(NEW / name), run_name='independent_' + cls)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace[cls]))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
print(stream.getvalue(), end='')
assert result.wasSuccessful() and result.testsRun == 18 and not EVENTS
print(json.dumps({'packet_pin_occurrences': len(checked), 'packet_unique_paths': len({row['path'] for row in checked}),
    'entry_inverse': True, 'policy_inverse': True, 'observer_policy_inverse': True, 'command_inverse': True,
    'staged_files': len(staged), 'staged_bytes_including_policy': 434627,
    'adapted_guard_bytes_match_policy': True, 'tests': result.testsRun, 'forbidden_events': EVENTS}, sort_keys=True))
