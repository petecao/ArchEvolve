"""2026-10-16 ET. Source/compact-metadata policy preparation, never execution."""
import ast
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
INIT = TRACE.parent / '28-initialized-u32-resume-20261016'
POC = TRACE.parent.parent
RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-trace-04af74c1-v4'
COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v1'
CONTROL = COLD + '/control'
COMMIT = '04af74c121a733589fbe1a2087ad602deaef598b'
POLICY_SHA = 'd61807f5595e77aabdbd054b6f00caff636775f07ab697f368af8f87864241de'
ROOT_SHA = 'c94420bdb85074be52aa2044158c9ee77cace37f4dbb0fac2274e64973a5e7ff'
CONTEXT_SHA = '66c95b6c1a7eec239d95ca9fce7b9290381a54407472e572a4e5dcaa28732bf4'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(path, value):
    data = path.read_bytes(); assert sha(data) == value
    return data


def pin(path, remote=None):
    data = path.read_bytes()
    return {'path': remote or str(path.resolve()), 'bytes': len(data), 'sha256': sha(data)}


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def build():
    policy_path = TRACE / 'linux_trace_policy_04af74c1_v4.json'
    original = json.loads(checked(policy_path, POLICY_SHA))
    root_path = POC / 'evidence/t28-trace-v4-root-execution-20261016.json'
    root = json.loads(checked(root_path, ROOT_SHA))
    context_path = HERE / 'passive-trace-v4-context.json'
    context = json.loads(checked(context_path, CONTEXT_SHA))
    assert context['raw'] == root['raw_root'] == RAW
    assert context['file_count'] == root['raw_files'] == 1409
    assert context['total_bytes'] == root['raw_bytes'] == 42682114
    assert context['json']['lane.json'] == root['actual']['lane.json']
    assert original['source_commit'] == COMMIT
    final = context['json']['memory-trace-final-physical-check.json']
    assert final['source_before'] == final['source_after'] and final['unchanged'] is True
    assert final['source_before']['count'] == 1678
    packet = '.scratch/probata-proof-of-concept-2026-10-13/prototype/28-public-memory-trace-resume-20261016'
    data = (TRACE / 'trace_cases.py').read_bytes()
    assert sha(data) == original['source_files'][packet + '/trace_cases.py']
    # Bind to fixed public source order, never record verdict or lexical path order.
    public = json.loads((TRACE / 'actual-policy.json').read_bytes())
    assert sha((TRACE / 'actual-policy.json').read_bytes()) == original['source_files'][packet + '/actual-policy.json']
    assert len(public['cases']) == 25
    indexed = {}
    for row in root['records']:
        match = re.search(r'/test_actual_public_abstract_me([0-9]+)/records/proofs/', row['pin']['path'])
        assert match and int(match[1]) not in indexed
        indexed[int(match[1])] = row
    assert set(indexed) == set(range(25))
    records = []
    for index, case in enumerate(public['cases']):
        row = indexed[index]
        assert row['verdict'] == case['expected_verdict'] and row['failure_class'] is None
        assert row['bounds'] == {'threads': 1} and row['subject'] == {'kind': 'library_summary', 'id': 'contract.dx100_trust_fixture'}
        name = str(Path(row['pin']['path']).relative_to(RAW))
        assert context['raw_manifest']['files'][name] == {key: row['pin'][key] for key in ('bytes', 'sha256')}
        records.append({'case': case['name'], 'id': row['id'], 'record': row['pin']})
    reader = HERE / 'trace_cold_audit_v1.py'
    files = {name: HERE / name for name in ('reviewed_cold_primitives_v1.py', 'public_assertions_v1.py')}
    files.update({name: TRACE / name for name in ('closed_python_surface.py', 'python_startup_roles_v2.py')})
    files['initialized_cold_identities_v2.py'] = INIT / 'initialized_cold_identities_v2.py'
    policy = {'schema': 'trace-cold-audit-policy-1', 'date': '2026-10-16 ET', 'admitted': False,
        'source_commit': COMMIT, 'raw': RAW, 'project': original['source_root'],
        'original_entry': pin(TRACE / 'linux_trace_entry_v4.py', RAW + '/control/linux_trace_entry_v4.py'),
        'source_policy': pin(policy_path, RAW + '/control/' + policy_path.name),
        'root_execution_receipt': pin(root_path, CONTROL + '/' + root_path.name),
        'settled_lane': root['actual']['lane.json']['socket_lane'], 'raw_manifest': context['raw_manifest'],
        'source_consumer_receipt_sha256': final['source_before']['canonical_sha256'],
        'reader_sha256': sha(reader.read_bytes()),
        'reader_files': {name: pin(path, CONTROL + '/' + name) for name, path in files.items()},
        'reader_admission': {'admitted': False, 'role': 'isolated-passive-cold-reader',
            'sys_path': original['python_startup_roles_v2']['package_sys_path'],
            'pycache_prefix': COLD + '/reader-source-cache',
            'environment': {'PYTHONPATH': original['source_root'], 'PYTHONPYCACHEPREFIX': COLD + '/cache',
                'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': None, 'PYTHONSAFEPATH': None,
                'SETUPTOOLS_USE_DISTUTILS': None}},
        'records': records, 'scope': 'UNADMITTED exact original abstract25 policy request. No actual reader execution, '
            'hardware counterexamples, source-call refinement, whole-interface, current0.2 or full28 claim.',
        'provenance': {'root_receipt': pin(root_path), 'passive_context': pin(context_path),
            'fixed_case_order': 'source actual-policy.json order and exact fixture index 0..24; never verdict selection'},
        'root_duties': ['Independently review exact source, copied primitives, policy and runtime before changing both admission Booleans',
            'Stage exact regular control files and admit selected isolated Python/environment/absent cache under a fresh bounded guard',
            'Reconfirm source commit/Git readback and finite original process/lease settlement independently',
            'Capture passive result outside the original immutable raw; no scientific rerun'],
    }
    policy_name = 'trace-cold-policy-template-04af74c1-v1.json'
    dump(policy_name, policy)
    controls = {reader.name: pin(reader, CONTROL + '/' + reader.name),
                root_path.name: pin(root_path, CONTROL + '/' + root_path.name)}
    controls.update({name: pin(path, CONTROL + '/' + name) for name, path in files.items()})
    controls[policy_name] = pin(HERE / policy_name, CONTROL + '/' + policy_name)
    assert sum(row['bytes'] for row in controls.values()) < 1048576
    dump('trace-cold-command-template-04af74c1-v1.json', {
        'date': '2026-10-16 ET', 'status': 'INERT_UNADMITTED_AWAITING_INDEPENDENT_SOURCE_REVIEW',
        'command': [original['tools']['python']['path'], '-I', '-B', '-X',
            'pycache_prefix=' + COLD + '/reader-source-cache', CONTROL + '/' + reader.name,
            CONTROL + '/' + policy_name, sha((HERE / policy_name).read_bytes())],
        'fresh_raw': COLD, 'environment': policy['reader_admission']['environment'], 'control_files': controls,
        'control_total_bytes': sum(row['bytes'] for row in controls.values()),
        'reader_executed': False, 'scientific_execution': False,
        'conditions': ['Both policy admission Booleans remain false; root must update and repin after independent source review',
            'No extra PYTHON* environment variables; null values mean unset',
            'The explicit -X cache prefix must remain absent; outer environment cache may exist',
            'stdout/stderr belong only under the fresh cold raw; original trace raw remains immutable'],
    })


if __name__ == '__main__':
    build()
