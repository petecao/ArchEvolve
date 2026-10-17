"""2026-10-16 ET. Run only the public pure floating-mode boundary controls."""
import ctypes
import hashlib
import inspect
import json
from pathlib import Path
import runpy
import sys
import traceback

import pytest


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
OUTPUT = HERE / 'history' / sys.argv[1]
OUTPUT.mkdir(parents=True, exist_ok=False)
attempts = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn',
                         'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        attempts.append(event)
        raise RuntimeError('pure floating-mode controls reject ' + event)


pins = []
for name in ('swdb/vector_float_mode.py', 'tests/test_vector_float_mode.py', 'swdb/std_models.py'):
    path = PROJECT / name
    if path.is_file():
        raw = path.read_bytes()
        target = OUTPUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        pins.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
sys.addaudithook(audit)
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT))
tests = runpy.run_path(str(PROJECT / 'tests/test_vector_float_mode.py'))
rows = []
for name, function in tests.items():
    if not name.startswith('test_'):
        continue
    assert not inspect.signature(function).parameters
    try:
        function()
        rows.append({'test': name, 'passed': True})
    except Exception as error:
        rows.append({'test': name, 'passed': False, 'error': str(error),
                     'traceback': traceback.format_exc()})
result = {'date': '2026-10-16 ET', 'stage': sys.argv[1], 'input_pins': pins, 'rows': rows,
          'passed': sum(row['passed'] for row in rows),
          'failed': sum(not row['passed'] for row in rows),
          'external_attempts_after_audit': attempts, 'native_or_formal_or_remote_execution': False}
(OUTPUT / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True, indent=2))
raise SystemExit(bool(result['failed'] or attempts))
