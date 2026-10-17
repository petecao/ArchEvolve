"""2026-10-16 ET. Freeze source-only controls, never prepare a public profile."""
import ast
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
    return {'path': path.relative_to(root).as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def main():
    ns = runpy.run_path(str(HERE / 'test_contract_formatter_v2.py'), run_name='pure_formatter_controls')
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ns['FormatterControls'])
    names = [test.id() for test in suite]
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (HERE / 'pure-controls-v2.txt').write_text(stream.getvalue())
    assert result.wasSuccessful() and result.testsRun == 11 and not result.skipped
    write('pure-controls-v2.json', {'date': '2026-10-16 ET', 'tests': names,
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skips': len(result.skipped), 'no_child': True, 'project_imports': False,
        'scientific_execution': False, 'actual_profile_preparation': False,
        'scope': 'Real Python metadata checks; policy-selection protocol stand-in, retained-schema test evaluator, no compiler typecheck.'})
    basis = json.loads((HERE / 'test-source-basis-v2.json').read_bytes())
    copied = []
    sources = {
        HERE / 'base-source/library.py': ('Library.get', 'Library.content_sha256', 'Library.resolve', 'Library._pin', 'Library.validate'),
        HERE / 'base-source/library_operations.py': ('chain_form_problems',),
        HERE / 'base-source/artifacts.py': ('digest', 'file_hash'),
        WHOLE / 'production-route-v3/proposed/swdb/formal_frame.py': ('_entry', '_placement', '_concurrency', '_roles'),
        WHOLE / 'production-route-v3/proposed/swdb/dx100_checked_source.py': ('Refused', 'need', 'checked_unit_format', 'sole_whole_frame', 'unit_contract'),
        WHOLE / 'production-route-v3/proposed/swdb/cbmc_translator.py': ('Untranslatable', 'Clause', 'clauses', '_tokens')}
    for path, names in sources.items():
        text = path.read_text(); tree = ast.parse(text)
        for name in names:
            if '.' in name:
                owner, leaf = name.split('.')
                cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == owner)
                node = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == leaf)
            else:
                node = next(node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name)
            raw = ast.get_source_segment(text, node).encode()
            copied.append({'path': path.relative_to(WHOLE).as_posix(), 'node': name,
                'line': node.lineno, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    write('extracted-node-provenance-v2.json', {'date': '2026-10-16 ET', 'nodes': copied,
        'complete_stdlib_scanner': pin(HERE / 'base-source/acsl_subset.py', WHOLE),
        'no_ast_rewrites_of_extracted_functions': True,
        'protocol_seams': ['selected source-policy lookup only', 'third-party JSONSchema engine only',
                           'formal_frame.check adapter invokes real metadata _entry only; no compiler stage']})
    files = [pin(path, HERE) for path in sorted(HERE.rglob('*'))
             if path.is_file() and path.name != 'source-packet-v2.json']
    assert not any(path.name == '__pycache__' for path in HERE.rglob('*'))
    write('source-packet-v2.json', {'date': '2026-10-16 ET',
        'schema': 'inert-public-profile-builder-formatter-source-packet-2',
        'scope': 'Only unit_contracts differs from V1: separate frame/result clauses, concurrency_frame empty list, one target role for one stream shape.',
        'files': files, 'file_count': len(files), 'external_inputs': basis['files'],
        'unchanged': ['all non-formatter builder bytes', 'public-profile-builder-v1', 'public-profile-planner-v2',
                      'runtime-projection-v4 draft', 'shared production', 'source/model/receiver/draw/transport algorithms'],
        'actual_profile_preparation': False, 'public_proof': False, 'native_executed': False,
        'production_applied': False, 'independent_review': 'pending'})
    print(json.dumps(pin(HERE / 'source-packet-v2.json', HERE), sort_keys=True))


if __name__ == '__main__':
    main()
