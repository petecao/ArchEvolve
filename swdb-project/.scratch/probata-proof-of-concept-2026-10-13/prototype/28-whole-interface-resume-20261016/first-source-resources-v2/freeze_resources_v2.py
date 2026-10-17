"""Source-only freeze of the node-count scanner correction."""
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


namespace = runpy.run_path(str(HERE / 'test_resources_v2.py'), run_name='pure_source_resources_v2')
stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(namespace['Controls']))
(HERE / 'pure-controls-v2.log').write_text(stream.getvalue())
assert result.testsRun == 8 and result.wasSuccessful() and not result.skipped
scope = namespace['namespace'](); profile = scope['select'](scope['SOURCE_SHA'], scope['FUNCTION'], scope['COMPONENTS'])
(HERE / 'resource-selection-v2.json').write_text(json.dumps(profile, sort_keys=True, indent=2) + '\n')
old = HERE.parent / 'first-source-resources-v1/source-packet-v1.json'
assert pin(old)['sha256'] == '6d88f448f8f70c40e221fb39e73259cfc6d728f83dd4eb51e755511e5f8d7d5d'
prior = json.loads(old.read_bytes())
for row in prior['files']: assert pin(Path(row['path'])) == row
packet = {'schema': 'first-source-resource-source-packet-2', 'date': '2026-10-16 ET',
    'files': [pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name != 'source-packet-v2.json'],
    'predecessor': pin(old), 'basis': prior['basis'], 'node_capacity': 1024, 'source_accounting_budget': 828,
    'helper_owner_unwind': profile['helper_owner_unwind'], 'default_helper_unwind': 513,
    'actual_selector_observation_and_all_capacity_checks_required': True, 'tests': 8,
    'actual_executed': False, 'hardware_or_public_or_full_ticket_admission': False}
(HERE / 'source-packet-v2.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({'packet': pin(HERE / 'source-packet-v2.json'), 'module': pin(HERE / 'resource_profile_v2.py')}, sort_keys=True))
