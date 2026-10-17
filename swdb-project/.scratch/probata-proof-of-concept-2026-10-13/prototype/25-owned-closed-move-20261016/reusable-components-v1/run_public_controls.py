"""2026-10-16 ET. Pure public archive controls; all project actions audited.

Initialize stdlib ctypes' existing Python-process API before installing the
audit hook. Thereafter all project imports and public actions reject every
subprocess, socket and ctypes library load, including any libclang load.
"""
import ctypes
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
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) \
            or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise AssertionError('pure reusable controls reject '+event)


sys.dont_write_bytecode = True
sys.addaudithook(audit)
sys.path.insert(0, str(PROJECT))
TESTS = runpy.run_path(str(PROJECT/'tests/test_vector_reallocation_reusable_components.py'))
ROWS = []
for name, function in TESTS.items():
    if not name.startswith('test_'):
        continue
    try:
        if function.__code__.co_argcount:
            with tempfile.TemporaryDirectory(prefix='probata-reusable-components-public-') as directory:
                function(Path(directory))
        else:
            function()
        ROWS.append({'test': name, 'passed': True})
    except Exception as error:
        ROWS.append({'test': name, 'passed': False, 'error': str(error),
                     'traceback': traceback.format_exc()})
print(json.dumps({'date': '2026-10-16 ET', 'rows': ROWS, 'external_attempts_after_audit': ATTEMPTS,
                  'stdlib_existing_Python_API_initialized_before_project_imports': True,
                  'native_compiler_solver_or_network_workflow': False}, sort_keys=True, indent=2))
raise SystemExit(any(not row['passed'] for row in ROWS) or bool(ATTEMPTS))
