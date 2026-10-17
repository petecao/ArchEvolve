"""2026-10-16 ET. Isolated, child-free private-frame public artifact controls."""
import ast
import hashlib
import json
import runpy
import signal
import sys
import traceback
from pathlib import Path

import pytest


def main():
    stage = sys.argv[1]
    assert stage in {'red', 'green'}
    project = Path(__file__).resolve().parents[4]
    output = Path('/private/tmp/probata-resume-20261016-t25-private-frame-' + stage)
    output.mkdir(exist_ok=False)
    (output / 'swdb').mkdir()
    (output / 'swdb/__init__.py').write_text('')
    signal.alarm(30)
    pins = []
    if stage == 'green':
        for name in ['vector_reallocation_private_frame.py', 'heap_reallocation.mlw']:
            data = (project / 'swdb' / name).read_bytes()
            if name.endswith('.py'):
                imports = {alias.name for node in ast.walk(ast.parse(data))
                           if isinstance(node, ast.Import) for alias in node.names}
                imports |= {node.module for node in ast.walk(ast.parse(data))
                            if isinstance(node, ast.ImportFrom)}
                assert imports <= {'hashlib', 'json', 'pathlib'}
            (output / 'swdb' / name).write_bytes(data)
            pins.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest()})
    test = output / 'test_private_frame.py'
    test.write_bytes((project / 'tests/test_vector_reallocation_private_frame.py').read_bytes())
    attempts = []

    def audit(event, arguments):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn',
                     'os.exec', 'os.fork', 'ctypes.dlopen'}:
            attempts.append(event)
            raise RuntimeError('external/native execution forbidden in pure frame controls')

    sys.addaudithook(audit)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(output))
    tests = runpy.run_path(str(test))
    cases = [('test_private_frame_packet_retains_release_and_the_complete_incoming_observation', [])]
    cases += [('test_private_frame_packet_refuses_transition_or_frame_tampering', [change])
              for change in ['release', 'observation', 'metadata', 'extra']]
    results = []
    for index, (name, arguments) in enumerate(cases):
        path = output / ('case-' + str(index))
        path.mkdir()
        try:
            tests[name](path, *arguments)
            results.append({'name': name, 'arguments': arguments, 'passed': True})
        except (Exception, pytest.fail.Exception) as error:
            results.append({'name': name, 'arguments': arguments, 'passed': False,
                            'error': type(error).__name__ + ': ' + str(error),
                            'traceback': traceback.format_exc()})
    raw_bytes = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
    assert raw_bytes < 4 * 1024 * 1024
    result = {'created': '2026-10-16 ET', 'stage': stage, 'source_pins': pins,
              'outcomes': results, 'passed': sum(row['passed'] for row in results),
              'failed': sum(not row['passed'] for row in results),
              'external_native_attempts': attempts, 'raw_bytes': raw_bytes,
              'whole_alarm_seconds': 30, 'proof_acceptance': False,
              'source_typed_bridge_established': False, 'caller_acceptance': False}
    (output / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    signal.alarm(0)
    print(json.dumps({'path': str(output / 'result.json'), 'passed': result['passed'],
                      'failed': result['failed'], 'external_native_attempts': attempts}))
    return int(result['failed'] != 0 or bool(attempts))


if __name__ == '__main__':
    raise SystemExit(main())
