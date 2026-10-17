"""2026-10-16 ET. Inert exact public-pair command plan; executes no children.

Root binds this plan to the independently reviewed Linux guard, complete runtime,
compiler/verifier inventory, lane and cleanup contract before actual dispatch.
The planner cannot grant that admission or assert a future result.
"""
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def need(value, text):
    if not value:
        raise ValueError(text)


def plan(profile, selection):
    need(type(selection) is dict and set(selection) == {'python', 'original_project', 'producer_project',
        'library_root', 'records', 'runs', 'verifier_lock', 'pycache', 'compiler_wrapper', 'cbmc',
        'root_admission_receipt'}, 'closed explicit root command selection required')
    need(all(type(selection[name]) is str and Path(selection[name]).is_absolute() for name in selection
             if name != 'root_admission_receipt'), 'absolute selected paths required')
    receipt = selection['root_admission_receipt']
    need(type(receipt) is dict and set(receipt) == {'path', 'bytes', 'sha256'}
         and receipt['bytes'] > 0 and len(receipt['sha256']) == 64, 'root must independently bind exact admission receipt')
    rows = profile['contracts']
    need(len(rows) == 2 and {row['expected_result'] for row in rows} == {79, 80}
         and len({row['id'] for row in rows}) == 2, 'exact pair required')
    need(str(Path(selection['records']).parent / 'library') == selection['library_root']
         and selection['records'] != str(Path(selection['original_project']) / 'records'),
         'real default_root(records) must select the separate profile library')
    environment = {'SWDB_HOME': selection['original_project'],
        'PYTHONPATH': selection['producer_project'], 'PYTHONNOUSERSITE': '1', 'PYTHONSAFEPATH': '1',
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPYCACHEPREFIX': selection['pycache'],
        'SWDB_CLANG': selection['compiler_wrapper'], 'SWDB_CBMC': selection['cbmc'],
        'SWDB_VERIFIER_LOCK': selection['verifier_lock']}
    jobs = []
    for row in rows:
        argv = [selection['python'], '-B', '-P', '-m', 'swdb', 'prove', '--records', selection['records'],
            '--summary', row['id'], '--method-version', 'method.dx100-whole-checked-source-v1',
            '--define', 'NUM_CORES=4', '--define', 'TILE_SIZE=16384',
            '--adapter', 'cbmc', '--bounds', '{"threads":1}',
            '--runs-dir', selection['runs'], '--format', 'json']
        jobs.append({'expected_result': row['expected_result'], 'contract': {'id': row['id'], 'content_sha256': row['sha256']},
            'argv': argv, 'cwd': selection['producer_project'],
            'required_outcome': 'proven' if row['expected_result'] == 80 else 'refuted with retained original-source C++ replay',
            'outcome_observed': False})
    return {'schema': 'dx100-public-pair-plan-1', 'environment': environment, 'jobs': jobs,
        'root_admission_receipt': receipt, 'method': 'method.dx100-whole-checked-source-v1',
        'semantics_content_sha256': profile['semantics_content_sha256'],
        'method_content_sha256': profile['method_content_sha256'],
        'producer_manifest_sha256': profile['producer_manifest_sha256'],
        'expected_value_never_passed_to_source_or_model': True, 'sequential_workers': 1,
        'actual_guard_and_lane_binding': 'required separately by root; no budget/lease/process fact inferred',
        'scientific_outcomes': 'pending', 'execution_authorized_by_this_plan': False}
