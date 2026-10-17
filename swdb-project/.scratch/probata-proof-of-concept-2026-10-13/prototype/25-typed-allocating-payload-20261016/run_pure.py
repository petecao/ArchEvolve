"""2026-10-16 ET. No-child public typed-constructor source controls.

This exercises the pure source/model artifact seam, never an actual lowering,
compiler, native helper, verifier, solver, hardware or remote workflow.
"""
import ctypes
import hashlib
import inspect
import json
from pathlib import Path
import runpy
import sys
import tempfile
import traceback

import pytest


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
STAGE = sys.argv[1]
output = HERE/'history'/STAGE
output.mkdir(parents=True, exist_ok=False)
attempts = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn',
                         'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        attempts.append(event)
        raise RuntimeError('pure typed-constructor controls reject '+event)


pins = []
for name in ('swdb/vector_allocating_payload.py', 'swdb/vector_typed_payload.mlw',
             'tests/test_vector_allocating_payload.py', 'swdb/std_models.py', 'swdb/c_lowering.py'):
    path = PROJECT/name
    if path.is_file():
        raw = path.read_bytes()
        target = output/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        pins.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
sys.addaudithook(audit)
sys.path.insert(0, str(PROJECT))
sys.dont_write_bytecode = True
rows = []
tests = runpy.run_path(str(PROJECT/'tests/test_vector_allocating_payload.py'))
for name, function in tests.items():
    if not name.startswith('test_'):
        continue
    try:
        with tempfile.TemporaryDirectory(prefix='probata-typed-constructor-') as temporary:
            with pytest.MonkeyPatch.context() as monkeypatch:
                available = {'tmp_path': Path(temporary), 'monkeypatch': monkeypatch}
                function(**{key: available[key] for key in inspect.signature(function).parameters})
        rows.append({'test': name, 'passed': True})
    except Exception as error:
        rows.append({'test': name, 'passed': False, 'error': str(error), 'traceback': traceback.format_exc()})
result = {'date': '2026-10-16 ET', 'stage': STAGE, 'rows': rows, 'input_pins': pins,
          'passed': sum(row['passed'] for row in rows), 'failed': sum(not row['passed'] for row in rows),
          'external_attempts_after_audit': attempts, 'native_or_formal_workflow': False,
          'source_only_artifact_seam': True}
(output/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, sort_keys=True, indent=2))
raise SystemExit(bool(result['failed'] or attempts))
