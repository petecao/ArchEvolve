"""2026-10-16 ET. Pure inert packet author: SOURCE_COMMIT NODE.

Uses exact reviewed runtime metadata, physical helpers and read-only Git blobs.
It neither selects a live lane nor launches Python/compiler/verifier processes.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
PROJECT = POC.parents[1]
REPO = PROJECT.parent
SELECTION = 'tests/test_vector_reallocation_closed_public_workflow.py::test_public_closed_source_proof_and_exact_opt_in_controls'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def row(path):
    raw = path.read_bytes()
    return {'path': str(path), 'name': path.name, 'bytes': len(raw), 'sha256': digest(raw)}


def document(path, expected):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError('reviewed metadata changed: '+str(path))
    return json.loads(raw)


def git(*args, data=None):
    return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '-C', str(REPO), *args],
                                   input=data, timeout=180)


def blob_hashes(source, names):
    names = sorted(set(names))
    packed = git('cat-file', '--batch', data=b'\n'.join((source+':swdb-project/'+name).encode() for name in names)+b'\n')
    result, offset = {}, 0
    for name in names:
        newline = packed.index(b'\n', offset)
        _oid, kind, size = packed[offset:newline].split()
        if kind != b'blob':
            raise ValueError('selected source entry is not an immutable Git blob: '+name)
        offset = newline+1
        result[name] = digest(packed[offset:offset+int(size)])
        offset += int(size)
        if packed[offset:offset+1] != b'\n':
            raise ValueError('invalid Git blob framing')
        offset += 1
    if offset != len(packed):
        raise ValueError('unconsumed Git metadata')
    return result


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n')


def main():
    source, node = sys.argv[1:]
    if re.fullmatch('[0-9a-f]{40}', source) is None or node not in {'0', '1'}:
        raise ValueError('one exact published source commit and selected prospective node required')
    node = int(node)
    remote = '/data1/yanruj/probata-resume-20261016-'+source[:8]
    raw_name = 'probata-resume-20261016-'+source[:8]+'-t25-closed-source-public-v3'
    raw = '/data/yanruj/EvolveSWDB_runs/'+raw_name
    destination = HERE/('inert-'+source[:8]+'-node'+str(node))
    if destination.exists():
        raise ValueError('fresh inert packet namespace required')
    initialized_path = POC/'prototype/28-initialized-u32-resume-20261016/linux_pair_policy_04af74c1_v5.json'
    initialized = document(initialized_path, 'bae7dc4c11e44bfd763ece9178dcc99f1aaffac3e492efdd3477137fae846637')
    native_path = POC/'prototype/28-whole-interface-resume-20261016/linux_native86_policy_v4.json'
    native = document(native_path, '14be0baf2dece709210abb6039b0ab7ede41c5e8d5d1dfbe08ed47b6f3ba9f5b')
    if any(native[key] != initialized[key] for key in ('runtime_files', 'linux_header_surfaces', 'python_surface_binding')):
        raise ValueError('reviewed compiler/Python/native physical closures do not agree')
    preparation_path = POC/'evidence/t25-closed-source-shared-integration-preparation-v2-20261016.json'
    preparation = document(preparation_path, '9032f187f722979f391743bbabefefe4985f766c1c31303d1179dfe0207b780c')
    repair_path = POC/'evidence/t25-explicit-method-selection-repair-preparation-v2-20261016.json'
    repair = document(repair_path, '71cb0e200f81682f97abdd17047b027ef3d29369596b1bea12fe50214c2bf5c8')
    repairs = {str(Path(item['path']).relative_to(PROJECT)): item['sha256'] for item in repair['implementation_and_tests']}
    if blob_hashes(source, repairs) != repairs:
        raise ValueError('published source lacks the exact independently reviewed explicit-method repair')
    files = [str(Path(item['path']).relative_to(PROJECT)) for item in preparation['implementation_and_tests']]
    expected = {str(Path(item['path']).relative_to(PROJECT)): item['sha256'] for item in preparation['implementation_and_tests']}
    if blob_hashes(source, files) != expected:
        raise ValueError('selected published source differs from the frozen reviewed implementation')
    fixture = PROJECT/'tests/fixtures/proof/vector_closed_scientific_bundle'
    files += [str(path.relative_to(PROJECT)) for path in fixture.rglob('*') if path.is_file()]
    files += [*repairs]
    files += ['swdb/vector_reallocation_closed_binding.py', 'tests/testkit/vector_reallocation.py',
              'tests/testkit/dx100_selector.py', 'tests/fixtures/proof/vector_reallocation_v3.cc']
    policy = copy.deepcopy(initialized)
    policy['source_files'] = blob_hashes(source, [*initialized['source_files'], *files])
    roots = [*initialized['source_consumer_trees'], 'tests/test_vector_reallocation_closed_public_workflow.py',
             'tests/fixtures/proof/vector_closed_scientific_bundle']
    policy['source_consumer_trees'] = {name: {'oid': git('rev-parse', '--verify', source+':swdb-project/'+name).decode().strip()}
                                       for name in sorted(set(roots))}
    template = document(HERE/'template-preparation.json', '0fe401e54fc80f641132d721dcbf55fdcda7f93f31d817902107165efc7da950')
    if row(HERE/'entry_template.py')['sha256'] != template['template']['sha256']:
        raise ValueError('frozen inert entry template changed')
    destination.mkdir()
    entry = (HERE/'entry_template.py').read_text().replace('__SOURCE_COMMIT__', source).replace('__RAW_NAME__', raw_name).replace('__NODE__', str(node))
    (destination/'entry.py').write_text(entry)
    policy.update(source_commit=source, raw_name=raw_name, date='2026-10-16 ET',
        schema='closed-source-public-prospective-3', selection=SELECTION, profile_seconds=1000,
        native_runtime=native['native_runtime'], source_preparation_complete=True,
        guard={'whole_tree_seconds': 1200, 'external_timeout_seconds': 1320, 'rss_cap_bytes': 8589934592,
               'workers': 1, 'raw_budget_bytes': 536870912, 'per_file_bytes': 134217728},
        scope='Five public source-rule fixture cases; no new native WP/solver job. Producer completion is separate from independent source/evidence acceptance.')
    observation = document(HERE/'pytest-tmpdir-source-observation.json', '24709dcf0212c84770bf60826a5472072e94862ad3d8a630b335e66c11c0777d')
    case_ids = ['safe', 'missing_bundle', 'stale_method', 'wrong_result', 'default_method']
    prefixes = [re.sub(r'[\W]', '_', SELECTION.split('::')[-1]+'['+name+']')[:30] for name in case_ids]
    if len(set(prefixes)) != 1 or prefixes[0] != 'test_public_closed_source_proo':
        raise ValueError('five exact public cases must have the observed single truncated pytest prefix')
    prefix = prefixes[0]
    basetemp = 'closed-source-profile/pytest'
    targets = [{'literal_target': raw+'/'+basetemp+'/'+prefix+str(index), 'target_relative': basetemp+'/'+prefix+str(index)} for index in range(5)]
    policy['pytest_alias_policy'] = {'case_ids': case_ids, 'case_prefix': prefix, 'basetemp_relative': basetemp,
        'aliases': {basetemp+'/'+prefix+'current': {'allowed_targets': targets, 'final_target': targets[-1]}},
        'source': {key: observation[key] for key in ('path', 'sha256', 'bytes')},
        'derivation': 'Pinned _mk_tmp sanitizes node.name, truncates at 30 characters, then numbered=True; all five collide, final current targets index4.'}
    policy['finalization'] = {'reserve_bytes': 65536, 'result_byte_cap': 16384, 'time_margin_seconds': 1.0}
    policy['startup_roles']['source_project'] = remote+'/swdb-project'
    policy['linux_launch_binding'].update(node=node, entry_sha256=row(destination/'entry.py')['sha256'])
    helpers = [POC/'prototype/28-public-memory-trace-resume-20261016'/name for name in
               ('closed_python_surface.py', 'python_startup_roles_v2.py', 'python_role_observer_v2.py')]
    helpers += [POC/'evidence/resume-20261016-lane-coordination'/initialized['root_observer_file']]
    helpers += [HERE/name for name in ('reviewed_wp_gates.py', 'reviewed_native_gates.py', 'reviewed-function-lineage.json')]
    inputs = [row(path) for path in helpers]
    for item in inputs:
        if item['name'] in initialized['controller_files'] and \
                {key: item[key] for key in ('bytes', 'sha256')} != initialized['controller_files'][item['name']]:
            raise ValueError('reviewed runtime helper/observation changed')
    policy['controller_files'] = {item['name']: {key: item[key] for key in ('bytes', 'sha256')} for item in inputs}
    write(destination/'policy.json', policy)
    inputs += [row(destination/name) for name in ('entry.py', 'policy.json')]
    if len({item['name'] for item in inputs}) != len(inputs) or sum(item['bytes'] for item in inputs) > 1048576:
        raise ValueError('unique closed controller inputs must fit the root1MiB staging bound')
    command = {'created': '2026-10-16 ET', 'status': 'INERT_PENDING_INDEPENDENT_ENTRY_REVIEW', 'actual_launched': False,
        'source_commit': source, 'source': remote+'/swdb-project', 'raw_root': raw, 'node': node,
        'argv': [policy['tools']['opam']['path'], 'exec', '--switch=framac-33', '--',
            policy['linux_launch_binding']['python'], '-I', '-B', raw+'/control/entry.py',
            remote+'/swdb-project', raw, raw+'/control/policy.json', row(destination/'policy.json')['sha256']],
        'controller_inputs': inputs, 'controller_total_bytes': sum(item['bytes'] for item in inputs),
        'root_guard': policy['guard'], 'test_seconds': 1000, 'selection': SELECTION,
        'pytest_alias_policy': policy['pytest_alias_policy'], 'finalization': policy['finalization'],
        'run_environment_unset': ['LIBRARY_PATH'],
        'actual_environment': {'SWDB_VECTOR_CLOSED_SOURCE_ACTUAL': '1', 'SWDB_PAIR_ACTUAL': '0',
            'SWDB_MIXED_PAIR_ACTUAL': '0', 'SWDB_DX100_SELECTOR_ACTUAL_LINEUP': policy['actual_initialized_lineup']},
        'expected': {'junit_cases': 5, 'records': 5, 'source_rule_proven': 1, 'unsupported_controls': 4,
                     'schema_refusal_controls': 3, 'new_WP_solver_jobs': 0},
        'runtime_boundary': 'Inherited complete physical source/Python/startup-role/compiler/native/WP/config surfaces rehashed before/after; observed use and between-check loader behavior remain explicit TCB.',
        'independent_cold_acceptance': False, 'source_or_caller_admission': False}
    write(destination/'command.json', command)
    receipt = {'created': '2026-10-16 ET', 'status': command['status'], 'source_commit': source,
        'source_preparation': row(preparation_path), 'method_selection_repair': row(repair_path), 'runtime_input_policies': [row(initialized_path), row(native_path)],
        'author': row(HERE/'prepare.py'), 'outputs': [row(destination/name) for name in ('entry.py', 'policy.json', 'command.json')],
        'source_file_count': len(policy['source_files']), 'consumer_root_count': len(policy['source_consumer_trees']),
        'controller_total_bytes': command['controller_total_bytes'], 'compiler_or_solver_executed': False,
        'SSH_used': False, 'actual_admission': False}
    write(destination/'preparation.json', receipt)
    print(json.dumps({'packet': str(destination), 'command': row(destination/'command.json')}))


if __name__ == '__main__':
    main()
