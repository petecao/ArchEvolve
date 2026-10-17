"""2026-10-16 ET. Reproducible no-child outer controls, never the actual guard."""
import ctypes
import hashlib
import json
from pathlib import Path
import runpy
import sys
import unittest


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
OUTPUT = HERE / 'history' / sys.argv[1]
OUTPUT.mkdir(parents=True, exist_ok=False)
attempts = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn',
                         'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        attempts.append(event)
        raise RuntimeError('pure outer controls reject ' + event)


pins = []
for name in ('outer.py', 'test_controls.py'):
    raw = (HERE / name).read_bytes()
    (OUTPUT / name).write_bytes(raw)
    pins.append({'path': str(HERE / name), 'bytes': len(raw),
                 'sha256': hashlib.sha256(raw).hexdigest()})
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT))
sys.addaudithook(audit)
tests = runpy.run_path(str(HERE / 'test_controls.py'))
with (OUTPUT / 'controls.log').open('x') as log:
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(tests['Controls']))
receipt = {'date': '2026-10-16 ET', 'tests': result.testsRun, 'source_pins': pins,
    'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful(),
    'external_attempts': attempts, 'actual_observation_root_or_tools_or_SSH': False}
(OUTPUT / 'result.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps(receipt, sort_keys=True))
raise SystemExit(bool(not result.wasSuccessful() or attempts))
