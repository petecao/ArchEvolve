"""2026-10-16 ET. Exercise only public mathematical-dependency controls.

Initialize ctypes' existing Python-process API before the audit hook. All
project imports and test calls then reject tools, networks and library loads.
"""
import ctypes
import inspect
import json
from pathlib import Path
import runpy
import sys
import tempfile
import traceback

import pytest


PROJECT = Path(__file__).resolve().parents[5]
ATTEMPTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn',
                         'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise AssertionError('pure mathematical controls reject '+event)


sys.dont_write_bytecode = True
sys.addaudithook(audit)
sys.path.insert(0, str(PROJECT))
tests = runpy.run_path(str(PROJECT/'tests/test_vector_owned_move_binding.py'))
rows = []
for name, function in tests.items():
    if not name.startswith('test_'):
        continue
    try:
        with tempfile.TemporaryDirectory(prefix='probata-owned-move-binding-public-') as directory:
            with pytest.MonkeyPatch.context() as monkeypatch:
                supported = {'tmp_path': Path(directory), 'monkeypatch': monkeypatch}
                parameters = inspect.signature(function).parameters
                if set(parameters)-set(supported):
                    raise AssertionError('undeclared public fixture')
                function(**{parameter: supported[parameter] for parameter in parameters})
        rows.append({'test': name, 'passed': True})
    except Exception as error:
        rows.append({'test': name, 'passed': False, 'error': str(error),
                     'traceback': traceback.format_exc()})
print(json.dumps({'date': '2026-10-16 ET', 'rows': rows,
                  'external_attempts_after_audit': ATTEMPTS,
                  'stdlib_existing_Python_API_initialized_before_project_imports': True,
                  'native_compiler_solver_or_network_workflow': False}, sort_keys=True, indent=2))
raise SystemExit(any(not row['passed'] for row in rows) or bool(ATTEMPTS))
