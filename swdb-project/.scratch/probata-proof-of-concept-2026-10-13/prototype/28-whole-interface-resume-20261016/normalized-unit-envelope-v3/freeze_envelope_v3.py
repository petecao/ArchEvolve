"""Freeze source-only controls and immutable provenance; no child execution."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


suite = unittest.TestSuite()
for name, cls in (('test_envelope_v3.py', 'Controls'), ('test_root_environment_v3.py', 'RootEnvironmentControls')):
    namespace = runpy.run_path(str(HERE / name), run_name='pure_' + cls)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace[cls]))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
(HERE / 'pure-controls-v3.log').write_text(stream.getvalue())
assert result.testsRun == 18 and result.wasSuccessful() and not result.skipped
(HERE / 'pure-controls-v3.json').write_text(json.dumps({'tests': 18, 'errors': 0, 'failures': 0, 'skipped': 0,
    'no_child_project_compiler_native_solver_shell_launcher_or_actual_observer': True,
    'log': pin(HERE / 'pure-controls-v3.log')}, sort_keys=True, indent=2) + '\n')
old = WHOLE / 'normalized-unit-envelope-v2/source-packet-v2.json'
assert pin(old)['sha256'] == '2243b14b5abbcc3abe0f775ebb1d2cbf98f2f01a65415656bd5f6cfad327822a'
for row in json.loads(old.read_bytes())['files']:
    assert pin(Path(row['path'])) == row
command = json.loads((HERE / 'command-v3.json').read_bytes())
(HERE / 'root-argv-v3.json').write_text(json.dumps(command['argv'], indent=2) + '\n')
assert command['root_metadata_complete'] and command['root_controls_bytes_including_policy'] == 434627
assert command['root_launcher']['sha256'] == 'b4a2664da950070e5e37ffb88eb260e90d8cdb2d5a591504a7e9723c4891272b'
basis = [old,
    WHOLE / 'root-launcher-loader-v11/source-packet-v11.json',
    WHOLE / 'root-launcher-loader-v11-independent-review/independent-source-review-v11.json',
    WHOLE / 'normalized-unit-envelope-v2-actual/passive-shell-source-stdout-v2.json',
    WHOLE / 'normalized-unit-envelope-v2-actual/retained-legacy-v2.sh',
    WHOLE / 'normalized-unit-envelope-v2-actual/retained-actual-v2.sh',
    WHOLE / 'normalized-unit-envelope-v2-actual/retained-environment-v2.sh',
    WHOLE / 'normalized-unit-envelope-v2-actual/settled-log-diagnostic-stdout-v2.json']
packet = {'schema': 'inert-linux-normalized-unit-envelope-source-packet-3', 'date': '2026-10-16 ET',
    'files': [pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name != 'source-packet-v3.json'],
    'basis': [pin(path) for path in basis], 'entry': pin(HERE / 'linux_observation_envelope_v3.py'),
    'policy': pin(HERE / 'envelope-policy-v3.json'), 'command': pin(HERE / 'command-v3.json'),
    'tests': 18, 'entry_delta': 'raw namespace and entry/policy basenames only',
    'strict_environment_and_scientific_functions_unchanged': True,
    'root_preinterpreter_unset': ['LIBRARY_PATH', 'LD_LIBRARY_PATH'],
    'root_control_bytes_including_policy': 434627,
    'actual_executed': False, 'public_admission': False, 'root_admission_pending': True}
(HERE / 'source-packet-v3.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({name: pin(HERE / path) for name, path in {'packet': 'source-packet-v3.json',
    'entry': 'linux_observation_envelope_v3.py', 'policy': 'envelope-policy-v3.json', 'command': 'command-v3.json'}.items()}, sort_keys=True))
