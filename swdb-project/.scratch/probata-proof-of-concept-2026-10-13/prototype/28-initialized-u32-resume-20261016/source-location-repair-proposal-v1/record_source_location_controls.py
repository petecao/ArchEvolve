"""2026-10-16 ET. Record only the local pure assertion regression run."""
import hashlib
import io
import json
import runpy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pin(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    namespace = runpy.run_path(str(HERE / 'test_source_location_assertions.py'), run_name='pure_regressions')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(namespace['SourceLocationRegression'])
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    (HERE / 'pure-control-output.txt').write_text(output.getvalue())
    receipt = {
        'date': '2026-10-16 ET', 'kind': 'local compiler-free regression controls',
        'tests_run': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skips': len(result.skipped),
        'unexpected_successes': len(result.unexpectedSuccesses),
        'child_native_audit_events': list(namespace['EVENTS']),
        'interpreter': {'executable': sys.executable, 'version': sys.version,
                        'isolated': sys.flags.isolated, 'dont_write_bytecode': sys.dont_write_bytecode},
        'checked_inputs': {name: pin(HERE / name) for name in (
            'base-source.py', 'proposed-source.py', 'proposal-base.json', 'source-location.patch',
            'test_source_location_assertions.py', 'build_source_location_fixture.py',
            'synthetic-source-location-fixture.json', 'retained-diagnostic-metadata.json')},
        'output': pin(HERE / 'pure-control-output.txt'),
        'scope': 'Synthetic diagnostic seam only; not independent review or retained remote AST admission; no project import/compiler/native/verifier/SSH/child.',
    }
    passed = result.wasSuccessful() and result.testsRun == 11 and not result.skipped and not namespace['EVENTS']
    receipt['status'] = 'PASS' if passed else 'FAIL'
    (HERE / 'pure-control-receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(output.getvalue(), end='')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
