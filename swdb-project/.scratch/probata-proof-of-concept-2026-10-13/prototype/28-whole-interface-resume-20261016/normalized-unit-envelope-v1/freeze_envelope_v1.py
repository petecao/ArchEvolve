"""Source-only freeze; runs no-child unit controls, never the envelope itself."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parent.parent


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


namespace = runpy.run_path(str(HERE / 'test_envelope_v1.py'), run_name='pure_envelope_controls')
stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(namespace['Controls']))
(HERE / 'pure-controls-v1.log').write_text(stream.getvalue())
assert result.testsRun == 10 and result.wasSuccessful() and not result.skipped
receipt = {'schema': 'no-child-linux-observer-envelope-controls-1', 'date': '2026-10-16 ET',
    'tests': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures), 'skipped': len(result.skipped),
    'compiler_native_solver_project_import_or_actual_observer': False, 'log': pin(HERE / 'pure-controls-v1.log')}
(HERE / 'pure-controls-v1.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
sources = [path for path in sorted(HERE.iterdir()) if path.is_file() and path.name != 'source-packet-v1.json']
bases = [WHOLE / 'normalized-unit-observation-v1/source-packet-v1.json',
    WHOLE / 'normalized-unit-observation-v1/independent-observer-v1-source-review-20261016.json',
    POC / 'evidence/t28-normalized-unit-observer-v1-root-standards-review-20261016.json',
    WHOLE / 'normalized-ingress-v2/source-packet-v2.json',
    WHOLE / 'memory-role-gzip-v1-actual/fresh-original-v10-role-pins-v1.json',
    WHOLE / 'compiler-capture-v10/linux_compiler_capture_policy_v10.json',
    POC / 'prototype/resume-root-20261016/launch_reviewed_main_v9.py']
packet = {'schema': 'inert-linux-normalized-unit-envelope-source-packet-1', 'date': '2026-10-16 ET',
    'files': [pin(path) for path in sources], 'basis': [pin(path) for path in bases],
    'limits': {'whole_seconds': 1200, 'entry_seconds': 1180, 'rss_bytes': 4294967296,
        'workers': 1, 'raw_bytes': 268435456, 'observer_file_bytes': 4194304, 'root_controls_bytes': 1048576},
    'control_manifest': pin(HERE / 'command-v1.json'), 'source_project': '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project',
    'original_observer_bytes_unchanged': True, 'actual_executed': False, 'public_admission': False,
    'root_actual_admission_and_settlement_pending': True}
(HERE / 'source-packet-v1.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({'packet': pin(HERE / 'source-packet-v1.json'), 'entry': pin(HERE / 'linux_observation_envelope_v1.py'),
    'policy': pin(HERE / 'envelope-policy-v1.json'), 'command': pin(HERE / 'command-v1.json'), 'controls': 10}, sort_keys=True))
