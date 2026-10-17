"""2026-10-16 ET. Bounded isolated public packet tests; no child/native tools."""
import hashlib
import json
from pathlib import Path
import runpy
import signal
import sys
import traceback

import pytest

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]


def main():
    stage = sys.argv[1]
    if stage not in {'red-v1', 'green-v1', 'red-v2', 'green-v2', 'green-v2b', 'red-v3', 'green-v3',
                     'red-v4', 'green-v4'}:
        raise ValueError('explicit retained stage required')
    root = Path('/private/tmp/probata-resume-20261016-t25-owned-swap-witness-'+stage)
    root.mkdir(exist_ok=False)
    (root/'swdb').mkdir()
    names = ['std_models.py', 'c_lowering.py', 'vector_owned_transfer.py',
             'vector_owned_state.mlw', 'heap_reallocation.mlw', 'vector_owned_source_view.py',
             'vector_owned_effects.mlw', 'vector_owned_swap_parts.py', 'vector_owned_swap_header_cases.py']
    if stage != 'red-v1':
        names.append('vector_owned_swap_header_witness.py')
    pins = []
    for name in names:
        raw = (PROJECT/'swdb'/name).read_bytes()
        (root/'swdb'/name).write_bytes(raw)
        pins.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    test = root/'test_swap_header_witness.py'
    raw = (PROJECT/'tests/test_vector_owned_swap_header_witness.py').read_bytes()
    test.write_bytes(raw)
    attempts = []

    def audit(event, args):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec',
                     'os.fork', 'ctypes.dlopen', 'socket.connect'}:
            attempts.append(event)
            raise RuntimeError('pure swap witness controls rejected '+event)

    sys.addaudithook(audit)
    sys.path.insert(0, str(root))
    sys.dont_write_bytecode = True
    signal.alarm(30)
    tests = runpy.run_path(str(test))
    outcomes = []
    for name, function in tests.items():
        if not name.startswith('test_'):
            continue
        directory = root/name
        directory.mkdir()
        try:
            function(directory)
            outcomes.append({'name': name, 'passed': True})
        except (Exception, pytest.fail.Exception) as error:
            outcomes.append({'name': name, 'passed': False,
                             'error': type(error).__name__+': '+str(error),
                             'traceback': traceback.format_exc()})
    size = sum(path.lstat().st_size for path in root.rglob('*') if path.is_file() and not path.is_symlink())
    if size > 16*1024**2:
        raise ValueError('pure swap witness raw bound exceeded')
    result = {'date': '2026-10-16 ET', 'stage': stage, 'source_pins': pins,
              'test_sha256': hashlib.sha256(raw).hexdigest(), 'outcomes': outcomes,
              'passed': sum(row['passed'] for row in outcomes),
              'failed': sum(not row['passed'] for row in outcomes),
              'external_native_attempts': attempts, 'raw_bytes': size, 'actual_formal_run': False}
    (root/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    signal.alarm(0)
    print(json.dumps({'result': str(root/'result.json'), 'passed': result['passed'],
                      'failed': result['failed'], 'attempts': attempts}))
    return int(result['failed'] != 0 or bool(attempts))


if __name__ == '__main__':
    raise SystemExit(main())
