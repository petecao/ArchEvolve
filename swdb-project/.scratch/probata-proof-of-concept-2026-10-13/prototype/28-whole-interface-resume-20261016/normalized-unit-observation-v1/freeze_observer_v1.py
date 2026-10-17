"""2026-10-16 ET. Freeze inert observer source and pure controls only."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent


def pin(path, root):
    raw = path.read_bytes()
    return {'path': path.relative_to(root).as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def main():
    ns = runpy.run_path(str(HERE / 'test_observer_v1.py'), run_name='observer_pure_controls')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ns['ObserverControls'])
    names = [test.id() for test in suite]; stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    assert result.wasSuccessful() and result.testsRun == 8 and not result.skipped
    (HERE / 'pure-controls-v1.txt').write_text(stream.getvalue())
    write('pure-controls-v1.json', {'date': '2026-10-16 ET', 'tests': names, 'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
        'actual_TU_observation': False, 'project_imports': False, 'scientific_execution': False,
        'scope': 'Exact source inverse/AST comparison seam, fixed bridge/module pins, fake registration bytes, real physical reader.'})
    capture_schema = json.loads((WHOLE / 'normalized-ingress-v1/capture-schema-v1.json').read_bytes())
    rows = json.loads((HERE / 'fixed-modules-v1.json').read_bytes())['modules']
    stage = [{**pin(HERE / 'modules' / row['file'], HERE), 'destination_basename': row['file']} for row in rows]
    stage += [{**pin(HERE / name, HERE), 'destination_basename': name} for name in ('fixed-modules-v1.json', 'observe_entry_v1.py')]
    write('control-stage-manifest-v1.json', {'date': '2026-10-16 ET', 'files': stage,
        'total_bytes': sum(row['bytes'] for row in stage), 'max_total_with_policy_bytes': 1048576,
        'root_runtime_guard_startup_and_launch_binding': 'pending independent root admission'})
    controls = {row['destination_basename']: {'path': None, 'bytes': row['bytes'], 'sha256': row['sha256']} for row in stage}
    template = {'schema': 'root-selected-normalized-unit-observation-1', 'original_project': None,
        'library_root': None, 'output_root': None, 'proof_source': {'root': 'library', 'path': 'proof_units/source.cpp',
            'sha256': '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'},
        'capture': {'kind': capture_schema['kind'], 'original': {name: None for name in capture_schema['original_keys']},
                    'transform': {name: None for name in capture_schema['transform_keys']}, 'prepared': None},
        'controls': controls, 'root_admission_receipt': None}
    write('observation-policy-template-v1.json', template)
    files = [pin(path, HERE) for path in sorted(HERE.rglob('*'))
             if path.is_file() and path.name != 'source-packet-v1.json']
    assert not any(path.name == '__pycache__' for path in HERE.rglob('*'))
    inputs = [pin(WHOLE / name, WHOLE) for name in
        ('normalized-ingress-v2/source-packet-v2.json', 'normalized-ingress-v2/independent-ingress-v2-source-review-20261016.json',
         'production-route-v3/proposed/swdb/dx100_checked_source.py')]
    write('source-packet-v1.json', {'date': '2026-10-16 ET', 'schema': 'private-normalized-unit-observer-source-packet-1',
        'files': files, 'file_count': len(files), 'input_packets': inputs, 'control_source_bytes': sum(row['bytes'] for row in stage),
        'actual_TU_observation': False, 'compiler_native_solver_executed': False, 'public_admission': False,
        'independent_review': 'pending', 'root_policy_runtime_guard_lane_admission': 'pending',
        'scope': 'Compute missing first normalized TU preparation as data; preserve public equality and every other ingress check.'})
    print(json.dumps(pin(HERE / 'source-packet-v1.json', HERE), sort_keys=True))


if __name__ == '__main__': main()
