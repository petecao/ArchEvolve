"""2026-10-16 ET. Author immutable-source/runtime policy; never dispatch tools.

Only read-only Git commands execute. Selected Git blobs are hashed opaquely;
the records/catalog tree is bound by its object ID without reading its payload.
Final source/controller review and root fresh lane admission remain required.
"""
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
REPOSITORY = PROJECT.parent
EVIDENCE = HERE.parents[1] / 'evidence/resume-20261016-lane-coordination'
SOURCE = '57c22ba6fe1707c9b40a910ed1c19c3ef99e9e84'
PACKET = str(HERE.relative_to(PROJECT))
REMOTE_PROJECT = '/data1/yanruj/probata-resume-20261016-57c22ba6/swdb-project'
RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-trace-57c22ba6-v2'
ENTRY_SHA = 'd319185131bd708c57229fe16e269da6e6298d1afba3c057a8fcc0f89aa43c93'
TEMPLATE_SHA = '449df3c01be847e2137db28252e892b86ce6bd91bb2aa916ad5579c972762264'
CANDIDATE_SHA = '0c14cbbdde56cf824c48c908689d5675b32e07ffd0aefc1b128023b28e3daf4a'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path, expected=None):
    data = Path(path).read_bytes()
    if expected is not None and digest(data) != expected:
        raise ValueError('exact policy authoring input changed: ' + str(path))
    return data


def git(*arguments, payload=None):
    return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '-C', str(REPOSITORY), *arguments],
                                   input=payload, timeout=60)


def selected_source_pins(old_files):
    packet_files = []
    for entry in git('ls-tree', '-r', '-z', SOURCE, '--', 'swdb-project/' + PACKET).split(b'\0'):
        if not entry:
            continue
        meta, path = entry.decode().split('\t', 1)
        mode, kind, oid = meta.split()
        if mode not in ('100644', '100755') or kind != 'blob':
            raise ValueError('selected static fixture must be a regular immutable Git blob')
        packet_files.append(path.removeprefix('swdb-project/'))
    names = sorted(set(old_files) | set(packet_files))
    if any(name.startswith('records/') or '\n' in name for name in names):
        raise ValueError('catalog payload/unsupported source path must not be selected')
    packed = git('cat-file', '--batch', payload=''.join(SOURCE + ':swdb-project/' + name + '\n' for name in names).encode())
    pins, offset = {}, 0
    for name in names:
        end = packed.index(b'\n', offset)
        header = packed[offset:end].decode().split()
        if len(header) != 3 or header[1] != 'blob':
            raise ValueError('selected immutable source blob is absent')
        size = int(header[2])
        if size < 0 or size > 33554432:
            raise ValueError('unexpected selected source blob size')
        start = end + 1
        data = packed[start:start + size]
        if len(data) != size or packed[start + size:start + size + 1] != b'\n':
            raise ValueError('Git batch source record is not closed')
        pins[name] = digest(data)
        offset = start + size + 1
    if offset != len(packed):
        raise ValueError('Git batch contains extra source records')
    return pins


def prepare():
    policy = json.loads(read(HERE / 'linux_trace_policy_template_v2.json', TEMPLATE_SHA))
    candidate = json.loads(read(EVIDENCE / 't28-abstract25-linux-runtime-candidate-policy-fields.json', CANDIDATE_SHA))
    initialized = json.loads(read(HERE.parent / '28-initialized-u32-resume-20261016/linux_pair_policy_2baf722f_v3.json',
                                 '22448884a92a7154db776ab570383dc5889e142236964614479e86a3cbb526bf'))
    if git('rev-parse', '--verify', SOURCE).decode().strip() != SOURCE:
        raise ValueError('published static trace source is unavailable locally')
    entry = HERE / 'linux_trace_entry_v2.py'
    read(entry, ENTRY_SHA)
    policy.update(admitted=True, source_commit=SOURCE, source_root=REMOTE_PROJECT,
                  raw_name=Path(RAW).name, source_files=selected_source_pins(initialized['source_files']),
                  status='INERT prepared exact57c policy; independent review/root fresh guard admission and actual25 verdicts remain pending')
    for name in policy['source_consumer_trees']:
        oid = git('rev-parse', '--verify', SOURCE + ':swdb-project/' + name).decode().strip()
        if len(oid) != 40 or any(c not in '0123456789abcdef' for c in oid):
            raise ValueError('invalid immutable consumer object ID')
        policy['source_consumer_trees'][name] = {'oid': oid}
    for name in ('runtime_files', 'tools', 'config', 'wp_artifacts', 'ocaml_packages',
                 'portable_import_surfaces', 'linux_clang_components', 'naming'):
        policy[name] = candidate[name]
    meta = policy['ocaml_kernel_meta_provenance']['pin']
    policy['runtime_files'][meta['path']] = meta['sha256']
    policy['tools']['cbmc'].update(version='6.11.0', fresh_version_observed=True,
                                  version_origin='raw root guarded observation SHA092397608fe3a08c42d85e9c8e121ed139f0d94e345a12ae3aaa57ad6e93a5f0')
    policy['tools']['frama-c']['version'] = '33.0'
    policy['linux_launch_binding'].update(node=1, python=policy['tools']['python']['path'],
                                          entry_sha256=ENTRY_SHA,
                                          wrappers=initialized['linux_launch_binding']['wrappers'])
    policy['python_startup_roles_v2'].update(admitted=True, source_project=REMOTE_PROJECT)
    control_paths = {}
    for name, wanted in policy['control_files'].items():
        path = EVIDENCE / name if name == 't28-linux-runtime-observer-v2-actual-20261016.json' else HERE / name
        read(path, wanted)
        control_paths[name] = path
    parser = policy['linux_parser_physical']
    if policy['runtime_files'].get(parser['path']) != parser['sha256']:
        raise ValueError('exact parser physical input is absent from runtime closure')
    policy_path = HERE / 'linux_trace_policy_57c22ba6_v2.json'
    policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + '\n')
    staged = [entry, policy_path, *control_paths.values()]
    controls = [{'name': path.name, 'path': str(path), 'bytes': len(read(path)), 'sha256': digest(read(path))}
                for path in staged]
    if len({row['name'] for row in controls}) != 9 or sum(row['bytes'] for row in controls) > 1048576:
        raise ValueError('closed nine-file controller packet exceeds the root staging contract')
    command = [policy['tools']['opam']['path'], 'exec', '--switch=framac-33', '--', policy['tools']['python']['path'],
               '-I', '-B', RAW + '/control/' + entry.name, REMOTE_PROJECT, RAW,
               RAW + '/control/' + policy_path.name, digest(read(policy_path))]
    packet = {'date': '2026-10-16 ET', 'status': 'INERT, independent review and root source/runtime/lane admission pending',
              'source_commit': SOURCE, 'source': REMOTE_PROJECT, 'raw_root': RAW, 'node': 1,
              'argv': command, 'controller_inputs': controls, 'control_total_bytes': sum(row['bytes'] for row in controls),
              'root_guard': {'whole_tree_seconds': 1200, 'external_timeout_seconds': 1320,
                             'rss_cap_bytes': 8589934592, 'workers': 1, 'raw_budget_bytes': 268435456},
              'root_creates_fresh_raw_root': True, 'root_socket_lane_only': True,
              'root_places_exact_controller_metadata': {'entry_remote': command[7], 'policy_remote': command[-2]},
              'junit': policy['junit'], 'selection': policy['selection'],
              'source_consumer_trees': policy['source_consumer_trees'], 'selected_source_count': len(policy['source_files']),
              'scope': '25 synthetic fixed-order abstract scalar event traces; no actual API/header/hardware/current0.2/full28 promotion',
              'actual_launched': False, 'proof_acceptance': False, 'independent_review_pending': True}
    (HERE / 'linux_trace_command_57c22ba6_v2.json').write_text(json.dumps(packet, indent=2, sort_keys=True) + '\n')
    result = {'source_commit': SOURCE, 'source_files': len(policy['source_files']),
              'runtime_files': len(policy['runtime_files']), 'control_total_bytes': packet['control_total_bytes'],
              'entry_sha256': ENTRY_SHA, 'policy_sha256': command[-1],
              'command_sha256': digest(read(HERE / 'linux_trace_command_57c22ba6_v2.json'))}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    prepare()
