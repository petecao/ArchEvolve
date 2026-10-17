"""Source-only freeze, with six no-child resource controls."""
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


namespace = runpy.run_path(str(HERE / 'test_resources_v1.py'), run_name='pure_source_resource_controls')
stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(namespace['Controls']))
(HERE / 'pure-controls-v1.log').write_text(stream.getvalue())
assert result.testsRun == 6 and result.wasSuccessful() and not result.skipped
scope = namespace['namespace']()
profile = scope['select'](scope['SOURCE_SHA'], scope['FUNCTION'], scope['COMPONENTS'])
(HERE / 'resource-selection-v1.json').write_text(json.dumps(profile, sort_keys=True, indent=2) + '\n')
packet = {'schema': 'first-source-resource-source-packet-1', 'date': '2026-10-16 ET',
    'files': [pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name != 'source-packet-v1.json'],
    'basis': [pin(HERE.parent / name) for name in ('source_call_fixture_v2.cpp', *scope['COMPONENTS'])],
    'tests': 6, 'default_backend_bytes_unchanged': True, 'node_capacity': 1024,
    'accounting_budget': 828, 'default_helper_unwind': 513, 'dxm_cover_owner_unwind': 20481,
    'actual_show_loops_and_capacity_checks_still_required': True, 'actual_executed': False,
    'public_or_hardware_or_full_ticket_admission': False}
(HERE / 'source-packet-v1.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({'packet': pin(HERE / 'source-packet-v1.json'), 'module': pin(HERE / 'resource_profile_v1.py')}, sort_keys=True))
