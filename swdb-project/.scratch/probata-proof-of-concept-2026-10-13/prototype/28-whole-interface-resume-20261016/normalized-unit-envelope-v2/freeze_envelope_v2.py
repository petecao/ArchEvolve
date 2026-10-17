"""Freeze only stdlib source/control evidence; never run the envelope."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest

HERE = Path(__file__).resolve().parent


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


namespace = runpy.run_path(str(HERE / 'test_envelope_v2.py'), run_name='pure_envelope_v2_controls')
stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(namespace['Controls']))
(HERE / 'pure-controls-v2.log').write_text(stream.getvalue())
assert result.testsRun == 13 and result.wasSuccessful() and not result.skipped
(HERE / 'pure-controls-v2.json').write_text(json.dumps({'tests': 13, 'errors': 0, 'failures': 0, 'skipped': 0,
    'no_child_project_compiler_native_solver_or_actual_observer': True, 'log': pin(HERE / 'pure-controls-v2.log')}, sort_keys=True, indent=2) + '\n')
old = HERE.parent / 'normalized-unit-envelope-v1/source-packet-v1.json'
assert pin(old)['sha256'] == 'ea78f99927f9e0ab6f6a27bdee40b9d38ca0450fd0d758aade0fe69b991f3f17'
old_packet = json.loads(old.read_bytes())
for row in old_packet['files']:
    assert pin(Path(row['path'])) == row
command = json.loads((HERE / 'command-v2.json').read_bytes())
assert command['root_metadata_complete'] and command['root_controls_bytes_including_policy'] <= 1048576
packet = {'schema': 'inert-linux-normalized-unit-envelope-source-packet-2', 'date': '2026-10-16 ET',
    'files': [pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name != 'source-packet-v2.json'],
    'predecessor': pin(old), 'original_observer': old_packet['basis'][0],
    'limits': old_packet['limits'], 'disk_floor_bytes': 21474836480, 'final_metadata_reserve_bytes': 33554432,
    'command': pin(HERE / 'command-v2.json'), 'entry': pin(HERE / 'linux_observation_envelope_v2.py'),
    'policy': pin(HERE / 'envelope-policy-v2.json'), 'tests': 13,
    'observer_and_ingress_scientific_bytes_unchanged': True,
    'root_created_directories': command['root_created_directories'],
    'envelope_created_directories': command['envelope_created_directories'],
    'completion_requires_zero_exit_postpublication_checks_and_no_finalization_refusal': True,
    'actual_executed': False, 'public_admission': False, 'root_admission_pending': True}
(HERE / 'source-packet-v2.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({name: pin(HERE / path) for name, path in {'packet': 'source-packet-v2.json',
    'entry': 'linux_observation_envelope_v2.py', 'policy': 'envelope-policy-v2.json', 'command': 'command-v2.json'}.items()}, sort_keys=True))
