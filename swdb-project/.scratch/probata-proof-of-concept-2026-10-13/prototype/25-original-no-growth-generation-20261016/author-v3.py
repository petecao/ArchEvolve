"""2026-10-16 ET. Inert two-basename Linux source-pin repair from immutable V2.

Only stdlib file/JSON/hash operations; no project imports or tool children.
"""
import ast
import base64
import copy
import hashlib
import json
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
OLD = HERE / 'inert-c978393b-v2'
OUTPUT = HERE / 'inert-c978393b-v3'
PHYSICAL = BASE / 'evidence/t25-original-no-growth-v3-physical-source-pins-20261016.json'
FAILURE = BASE / 'evidence/t25-original-no-growth-generation-v2-actual-failure-20261016.json'
REPAIRS = {'Ctypes.ml': 'ctypes.ml', 'Wp_parameters.ml': 'wp_parameters.ml'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': sha(data), 'bytes': len(data)}


def main():
    packet_raw = (OLD / 'packet.json').read_bytes()
    if sha(packet_raw) != '0c94a7a757749f383cb8e4491455b2b075d55ff17f2508f118f0c579d9a311f8':
        raise ValueError('immutable independently reviewed V2 packet differs')
    packet = json.loads(packet_raw)
    for name in ['entry', 'expected', 'root_command', 'author', 'template',
                 'predecessor_packet', 'previous_unexecuted_generation_packet',
                 'guard_control_script', 'guard_control_receipt']:
        row = packet[name]
        if pin(Path(row['path'])) != row:
            raise ValueError('reviewed V2 reference differs: ' + name)
    old_expected_raw = (OLD / 'expected.json').read_bytes()
    expected = json.loads(old_expected_raw)
    physical = json.loads(PHYSICAL.read_bytes())
    selected = {row['name']: row for row in physical['sources']}
    if len(selected) != 10 or len(physical['sources']) != 10:
        raise ValueError('all ten selected installed sources must be physically read')
    repaired = copy.deepcopy(expected)
    for row in repaired['runtime_sources']:
        row['name'] = REPAIRS.get(row['name'], row['name'])
        actual = selected.pop(row['name'])
        path = expected['linux_prefix'] + '/lib/frama-c-wp/core/' + row['name']
        if actual != {'name': row['name'], 'path': path, 'sha256': row['sha256']}:
            raise ValueError('selected physical source content/path differs: ' + row['name'])
    if selected:
        raise ValueError('unexpected source physical pin')
    inverse = copy.deepcopy(repaired)
    reverse = {after: before for before, after in REPAIRS.items()}
    for row in inverse['runtime_sources']:
        row['name'] = reverse.get(row['name'], row['name'])
    if encoded(inverse) != old_expected_raw:
        raise ValueError('only two physical basenames may change expected metadata')
    failure = json.loads(FAILURE.read_bytes())
    if failure['generation_complete'] is not False or failure['error_type'] != 'FileNotFoundError' or \
            '/core/Ctypes.ml' not in failure['error'] or failure['source_commit'] != expected['source_commit']:
        raise ValueError('retained V2 pre-tool source-pin refusal differs')
    new_expected_raw = encoded(repaired)
    old_entry = (OLD / 'entry.py').read_bytes()
    if old_entry.count(sha(old_expected_raw).encode()) != 1:
        raise ValueError('one exact expected digest is required')
    entry = old_entry.replace(sha(old_expected_raw).encode(), sha(new_expected_raw).encode())
    if entry.replace(sha(new_expected_raw).encode(), sha(old_expected_raw).encode()) != old_entry:
        raise ValueError('entry source must inverse-restore exactly')
    ast.parse(entry)
    command = json.loads((OLD / 'root-command.json').read_bytes())
    bootstrap = command[6]
    for before, after in [
            (sha(old_entry), sha(entry)),
            (sha(old_expected_raw), sha(new_expected_raw)),
            (base64.b64encode(zlib.compress(old_entry, 9)).decode(),
             base64.b64encode(zlib.compress(entry, 9)).decode()),
            (base64.b64encode(zlib.compress(old_expected_raw, 9)).decode(),
             base64.b64encode(zlib.compress(new_expected_raw, 9)).decode())]:
        if bootstrap.count(before) != 1:
            raise ValueError('one exact V2 bootstrap embedding is required')
        bootstrap = bootstrap.replace(before, after)
    old_namespace = 'original-no-growth-generation-v2'
    if bootstrap.count(old_namespace) != 5:
        raise ValueError('five exact entry/expected/profile output namespace references are required')
    bootstrap = bootstrap.replace(old_namespace, 'original-no-growth-generation-v3')
    ast.parse(bootstrap)
    command[6] = bootstrap
    if len(bootstrap.encode()) >= 120000:
        raise ValueError('reviewed transport allowance exceeded')
    OUTPUT.mkdir(exist_ok=False)
    for name, data in [('entry.py', entry), ('expected.json', new_expected_raw),
                       ('root-command.json', encoded(command))]:
        (OUTPUT / name).write_bytes(data)
    for name in ['wp-input.expected.c', 'lowering.cached.c', 'anchors.cached.json']:
        (OUTPUT / name).write_bytes((OLD / name).read_bytes())
    new_packet = copy.deepcopy(packet)
    new_packet.update(root_kind='t25-original-no-growth-generation-v3',
        entry=pin(OUTPUT / 'entry.py'), expected=pin(OUTPUT / 'expected.json'),
        root_command=pin(OUTPUT / 'root-command.json'), author=pin(Path(__file__)),
        runtime_sources=repaired['runtime_sources'], predecessor_v2_packet=pin(OLD / 'packet.json'),
        v2_actual_pretool_failure=pin(FAILURE), installed_source_physical_receipt=pin(PHYSICAL),
        v3_repair_scope='Only Ctypes.ml -> ctypes.ml and Wp_parameters.ml -> wp_parameters.ml physical installed source basenames; all ten hashes freshly matched. Entry inverse restores V2 except expected digest, bootstrap only rebinds digests/payloads and output namespace. Original source/C/contract/flags/guard logic/budgets unchanged.',
        v2_expected_inverse_equal=True, v2_entry_inverse_equal=True,
        bootstrap_bytes=len(bootstrap.encode()))
    (OUTPUT / 'packet.json').write_bytes(encoded(new_packet))
    print(json.dumps({'packet': pin(OUTPUT / 'packet.json'), 'entry': new_packet['entry'],
                      'expected': new_packet['expected'], 'root_command': new_packet['root_command']}, indent=2))


if __name__ == '__main__':
    main()
