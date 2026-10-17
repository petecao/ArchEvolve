"""2026-10-16 ET. Source-only runtime memory packet; no actual preparation."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parent.parent


def pin(path, root):
    raw = path.read_bytes()
    assert path.resolve(strict=True) == path and not path.is_symlink()
    return {'path': path.relative_to(root).as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def main():
    old = (WHOLE / 'runtime-projection-v3/runtime_projection_v3.py').read_bytes()
    new = (HERE / 'runtime_projection_v4.py').read_bytes()
    assert new[:len(old)] == old
    assert hashlib.sha256(new).hexdigest() == '56077c3476ba0f4af3b06089e937a0a5723318f7927ba81ea45c8556251cb7de'
    review = POC / 'evidence/resume-20261016-lane-coordination/t28-source-memory-selection-v1-independent-source-review-20261016.json'
    assert hashlib.sha256(review.read_bytes()).hexdigest() == '7ffabf19d082ca979fcf41b6e24ddb214ffcce4fccd53ac02048a6793ec8d7f8'
    draft = json.loads((HERE / 'prefix-inverse-v4-draft.json').read_bytes())
    final = {**draft, 'state': 'FROZEN source-only; independent composed-runtime review pending',
             'helper_review': pin(review, POC),
             'draft_inverse': pin(HERE / 'prefix-inverse-v4-draft.json', POC),
             'draft_documents_preserved': True, 'runtime_and_controls_changed_from_draft': False}
    write('prefix-inverse-v4-final.json', final)
    ns = runpy.run_path(str(HERE / 'test_runtime_projection_v4.py'), run_name='pure_memory_controls')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ns['MemoryControls'])
    names = [test.id() for test in suite]; stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (HERE / 'pure-controls-v4.txt').write_text(stream.getvalue())
    assert result.wasSuccessful() and result.testsRun == 12 and not result.skipped
    write('pure-controls-v4.json', {'date': '2026-10-16 ET', 'tests': names,
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skips': len(result.skipped), 'no_child': True, 'project_imports': False,
        'actual_complete_tu_preparation': False, 'actual_owned_receiver': False,
        'scientific_execution': False, 'scope': 'Real root selector/allocation guards; explicit compiler/body/receiver/header protocol doubles; synthetic TU/metadata.'})
    tree = ast.parse(new)
    inputs = set()
    for name in ('PINS', 'MEMORY_PINS'):
        node = next(node for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
        for relative, expected in ast.literal_eval(node.value).items():
            path = WHOLE / relative
            assert pin(path, WHOLE)['sha256'] == expected
            inputs.add(path)
    inputs.update([WHOLE / 'runtime-projection-v3/runtime_projection_v3.py',
        WHOLE / 'runtime-projection-v3/runtime-projection-source-packet-v3.json',
        WHOLE / 'source-memory-selection-v1/source-packet-v1.json',
        WHOLE / 'source-memory-selection-v1/test_source_memory_selection_v1.py',
        WHOLE / 'source-memory-fixtures-v1/same_thread_memory_v1.cpp',
        WHOLE / 'receiver-memory-v1/source-packet-v1.json',
        WHOLE / 'receiver-memory-v1-independent-review/independent-review-v1.json', review,
        WHOLE.parents[3] / 'apps/dx100/benchmarks/API/MAA.hpp',
        WHOLE.parents[3] / 'apps/dx100/benchmarks/API/MAA_gem5.hpp'])
    # Headers are external project inputs, separately labeled rather than made
    # portable by an invented same-root assumption.
    external = []
    for path in sorted(inputs):
        root = POC if path.is_relative_to(POC) else WHOLE.parents[3]
        external.append({'root': 'poc' if root == POC else 'project', **pin(path, root)})
    files = [pin(path, HERE) for path in sorted(HERE.rglob('*'))
             if path.is_file() and path.name != 'runtime-projection-source-packet-v4.json']
    assert not any(path.name == '__pycache__' for path in HERE.rglob('*'))
    write('runtime-projection-source-packet-v4.json', {'date': '2026-10-16 ET',
        'schema': 'inert-separate-memory-runtime-source-packet-4', 'files': files, 'file_count': len(files),
        'inputs': external, 'unchanged_v3_prefix_bytes': len(old),
        'new_public_api': 'memory_projection', 'old_public_api_unchanged': 'projection',
        'source_sha256': ns['R']['MEMORY_SOURCE_SHA'], 'functions': sorted(ns['S']['PROFILES']) if 'PROFILES' in ns['S'] else
            ['whole_same_thread_read_during_store', 'whole_same_thread_write_during_gather', 'whole_same_thread_read_during_gather'],
        'source_selection_peer_review': pin(review, POC),
        'actual_complete_tu_preparation': False, 'public_proof': False, 'native_executed': False,
        'production_applied': False, 'independent_composed_runtime_review': 'pending'})
    print(json.dumps(pin(HERE / 'runtime-projection-source-packet-v4.json', HERE), sort_keys=True))


if __name__ == '__main__':
    main()
