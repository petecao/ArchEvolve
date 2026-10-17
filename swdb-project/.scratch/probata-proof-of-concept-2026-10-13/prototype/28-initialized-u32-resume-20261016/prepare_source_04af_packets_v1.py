"""2026-10-16 ET. Fresh-source binding only; never dispatches actual tools.

Only read-only Git metadata/blob operations run. Catalog payload is never read.
Reviewed runtime entries, helpers and scientific acceptance criteria are reused.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent / '28-public-memory-trace-resume-20261016'
PROJECT = HERE.parents[3]
REPOSITORY = PROJECT.parent
SOURCE = '04af74c121a733589fbe1a2087ad602deaef598b'
REMOTE_PROJECT = '/data1/yanruj/probata-resume-20261016-04af74c1/swdb-project'
PAIR_RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-pair-04af74c1-v5'
TRACE_RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-trace-04af74c1-v3'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, wanted=None):
    if path.is_symlink() or not path.is_file(): raise ValueError('regular controller input required')
    data = path.read_bytes()
    if wanted is not None and sha(data) != wanted: raise ValueError('reviewed authoring basis differs: ' + str(path))
    return data


def git(*arguments, payload=None):
    return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '-C', str(REPOSITORY), *arguments], input=payload, timeout=60)


def selected_pins(names):
    names = sorted(set(names))
    if any(name.startswith('records/') or '\n' in name or '\r' in name for name in names):
        raise ValueError('catalog payload/unsupported path cannot be selected')
    packed = git('cat-file', '--batch', payload=''.join(SOURCE + ':swdb-project/' + name + '\n' for name in names).encode())
    pins = {}; at = 0
    for name in names:
        end = packed.index(b'\n', at); header = packed[at:end].decode().split()
        if len(header) != 3 or header[1] != 'blob' or len(header[0]) != 40: raise ValueError('regular immutable source blob required')
        size = int(header[2]); start = end + 1
        if not 0 <= size <= 33554432: raise ValueError('unexpected selected source extent')
        data = packed[start:start + size]
        if len(data) != size or packed[start + size:start + size + 1] != b'\n': raise ValueError('closed Git blob record required')
        pins[name] = sha(data); at = start + size + 1
    if at != len(packed): raise ValueError('extra Git blob data')
    return pins


def consumer_trees(old):
    result = {}
    for name in old:
        oid = git('rev-parse', '--verify', SOURCE + ':swdb-project/' + name).decode().strip()
        if len(oid) != 40 or any(character not in '0123456789abcdef' for character in oid): raise ValueError('exact consumer object ID required')
        result[name] = {'oid': oid}
    return result


def staged(paths, expected_helpers):
    result = [{'name': path.name, 'path': str(path), 'bytes': len(read(path)), 'sha256': sha(read(path))} for path in paths]
    if len({row['name'] for row in result}) != len(result) or sum(row['bytes'] for row in result) > 1048576:
        raise ValueError('closed staging membership/one MiB budget differs')
    if {row['name'] for row in result[2:]} != set(expected_helpers): raise ValueError('exact reviewed helper membership differs')
    for row in result[2:]:
        wanted = expected_helpers[row['name']]
        if row['sha256'] != (wanted if isinstance(wanted, str) else wanted['sha256']) or isinstance(wanted, dict) and row['bytes'] != wanted['bytes']:
            raise ValueError('exact reviewed staged helper bytes differ')
    return result


def prepare_pair():
    old_policy = json.loads(read(HERE / 'linux_pair_policy_2baf722f_v4.json', '44b5746071fbbd5db6852e6fd27f14abfdb3216395f73b6c99f047729c8b2b35'))
    old_command = json.loads(read(HERE / 'linux_pair_command_2baf722f_v4.json', '39346b58d963edc9cd2a8e33da34b8cabcb10b649f004fc53e8ea79afc1cdfc1'))
    policy = copy.deepcopy(old_policy)
    policy.update(source_commit=SOURCE, raw_name=Path(PAIR_RAW).name,
                  source_files=selected_pins(policy['source_files']), source_consumer_trees=consumer_trees(policy['source_consumer_trees']))
    policy['startup_roles']['source_project'] = REMOTE_PROJECT
    if policy['source_files']['swdb/dx100_initialized_register_source.py'] != '01c043e544e50c30fc3d92b6be5a8b097f4dfef0606f53c29068a2ba008ac145':
        raise ValueError('reviewed observer is not the selected committed source')
    entry = HERE / 'linux_pair_entry_v4.py'
    read(entry, '9a6246962ed8288829b609711c2fc3d77f436b9411de5bbad58148937895bf6d')
    policy_path = HERE / 'linux_pair_policy_04af74c1_v5.json'
    policy_path.write_text(json.dumps(policy, sort_keys=True, indent=2) + '\n')
    controls = staged([entry, policy_path, *(Path(row['path']) for row in old_command['controller_inputs'][2:])], policy['controller_files'])
    command = copy.deepcopy(old_command)
    command.update(source_commit=SOURCE, source=REMOTE_PROJECT, raw_root=PAIR_RAW,
                   consumer_roots=policy['source_consumer_trees'], selected_source_count=len(policy['source_files']),
                   controller_inputs=controls, status='INERT source-binding V5; exact reviewed V4 runtime/criteria reused, root admission and fresh proof pending')
    command['argv'][7:] = [PAIR_RAW + '/control/' + entry.name, REMOTE_PROJECT, PAIR_RAW,
                           PAIR_RAW + '/control/' + policy_path.name, sha(read(policy_path))]
    command['root_places_exact_controller_metadata'] = {'entry_remote': command['argv'][7], 'policy_remote': command['argv'][-2]}
    path = HERE / 'linux_pair_command_04af74c1_v5.json'
    path.write_text(json.dumps(command, sort_keys=True, indent=2) + '\n')
    return policy_path, path


def prepare_trace():
    old_policy = json.loads(read(TRACE / 'linux_trace_policy_57c22ba6_v2.json', '130a1569e75c1bee434270dc964c0771d8b4c3b1cce278e0cb193a7d25a8feca'))
    old_command = json.loads(read(TRACE / 'linux_trace_command_57c22ba6_v2.json', '9f339b928d42496826f7a305bc5147eb645801c816f1f31369aa2474fb1a95b7'))
    names = list(old_policy['source_files'])
    packet = str(TRACE.relative_to(PROJECT))
    for record in git('ls-tree', '-r', '-z', SOURCE, '--', 'swdb-project/' + packet).split(b'\0'):
        if not record: continue
        metadata, path = record.decode().split('\t', 1); mode, kind, _oid = metadata.split()
        if mode not in ('100644', '100755') or kind != 'blob': raise ValueError('regular selected static trace blob required')
        names.append(path.removeprefix('swdb-project/'))
    policy = copy.deepcopy(old_policy)
    policy.update(source_commit=SOURCE, source_root=REMOTE_PROJECT, raw_name=Path(TRACE_RAW).name,
                  source_files=selected_pins(names), source_consumer_trees=consumer_trees(policy['source_consumer_trees']),
                  status='INERT source-binding V3; bounds fixture repair, exact reviewed V2 runtime/25 criteria reused')
    policy['python_startup_roles_v2']['source_project'] = REMOTE_PROJECT
    if policy['source_files']['tests/testkit/dx100_trust.py'] != '4d55a093a7a92eeb57c9878760bc48ae71c6d5683bbdbf50760be15997cb0982':
        raise ValueError('reviewed bounds helper is not the selected committed source')
    entry = TRACE / 'linux_trace_entry_v2.py'
    read(entry, 'd319185131bd708c57229fe16e269da6e6298d1afba3c057a8fcc0f89aa43c93')
    policy_path = TRACE / 'linux_trace_policy_04af74c1_v3.json'
    policy_path.write_text(json.dumps(policy, sort_keys=True, indent=2) + '\n')
    controls = staged([entry, policy_path, *(Path(row['path']) for row in old_command['controller_inputs'][2:])], policy['control_files'])
    command = copy.deepcopy(old_command)
    command.update(source_commit=SOURCE, source=REMOTE_PROJECT, raw_root=TRACE_RAW,
                   source_consumer_trees=policy['source_consumer_trees'], selected_source_count=len(policy['source_files']),
                   controller_inputs=controls, control_total_bytes=sum(row['bytes'] for row in controls),
                   status='INERT source-binding V3; reviewed V2 runtime and all25 verdict criteria unchanged; root admission pending')
    command['argv'][7:] = [TRACE_RAW + '/control/' + entry.name, REMOTE_PROJECT, TRACE_RAW,
                           TRACE_RAW + '/control/' + policy_path.name, sha(read(policy_path))]
    command['root_places_exact_controller_metadata'] = {'entry_remote': command['argv'][7], 'policy_remote': command['argv'][-2]}
    path = TRACE / 'linux_trace_command_04af74c1_v3.json'
    path.write_text(json.dumps(command, sort_keys=True, indent=2) + '\n')
    return policy_path, path


if __name__ == '__main__':
    if git('rev-parse', '--verify', SOURCE + '^{commit}').decode().strip() != SOURCE: raise ValueError('exact published source unavailable')
    paths = (*prepare_pair(), *prepare_trace())
    print(json.dumps({'source_commit': SOURCE, 'source_project': REMOTE_PROJECT,
                      'prepared': [{'path': str(path), 'bytes': len(read(path)), 'sha256': sha(read(path))} for path in paths],
                      'actual_launched': False}, sort_keys=True, indent=2))
