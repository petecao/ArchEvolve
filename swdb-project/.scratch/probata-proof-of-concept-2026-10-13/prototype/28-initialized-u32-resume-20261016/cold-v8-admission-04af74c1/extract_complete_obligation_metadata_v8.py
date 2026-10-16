"""Pinned compact inputs to the complete goal/CSV reader seam, no full audit."""
from pathlib import Path
import hashlib
import json
import sys
import types


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event in {'os.system', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir'}:
        raise RuntimeError('passive obligation extraction refuses ' + event)
    if event == 'open':
        _path, mode, flags = args
        if mode is not None and any(c in mode for c in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('passive obligation extraction refuses writes')


sys.addaudithook(deny)
context = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v8/control')
data = (context / 'initialized-cold-policy-04af74c1-v8.json').read_bytes()
assert hashlib.sha256(data).hexdigest() == 'c4f0bd5ea71b59fe8672c378ac04f2de58c07434b237c4158d3a7750a831762a'
policy = json.loads(data)
raw = Path(policy['raw'])


def pin_read(row):
    path = Path(row['path'])
    data = path.read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    return data


source_policy = json.loads(pin_read(policy['source_policy']))
wanted_yaml = source_policy['startup_roles']['module_origins']['yaml']
yaml_path = Path(wanted_yaml['path'])
yaml_hash = hashlib.sha256(yaml_path.read_bytes()).hexdigest()
import yaml
assert Path(yaml.__file__).resolve() == yaml_path and yaml.__spec__.origin == wanted_yaml['spec_origin']
helper_path = context / 'initialized_cold_obligations_v3.py'
helper_raw = helper_path.read_bytes()
assert hashlib.sha256(helper_raw).hexdigest() == '817c4041cae251e8c2002f7ea9858bc85e5d6f0adc37d174390367c3261b138f'
helper = types.ModuleType('inert_original_obligations_metadata')
exec(compile(helper_raw, str(helper_path), 'exec'), helper.__dict__)
rows = []
for selected in policy['records']:
    record = yaml.safe_load(pin_read(selected['record']))
    reports = {row['name']: row for row in record['evidence']['reports']}
    def evidence(name):
        row = reports[name]
        path = Path(row['path'])
        assert raw in path.parents
        manifest = policy['raw_manifest']['files'][str(path.relative_to(raw))]
        assert row['sha256'] == manifest['sha256']
        return pin_read({'path': str(path), **manifest})
    inventory = json.loads(evidence('wp_inventory'))
    native = json.loads(evidence('wp_goals'))
    csvrows = helper.csv_properties(evidence('wp_properties').decode())
    query = helper.initialized_wp_source(evidence('wp_input').decode(), selected['expected_result'], context)
    compact = {key: record[key] for key in ('id', 'verdict', 'goals', 'assumptions')}
    compact['pins'] = {'proof_semantics': record['pins']['proof_semantics']}
    for key in ('failure_class', 'unproven_properties'):
        if key in record:
            compact[key] = record[key]
    rows.append({'expected_result': selected['expected_result'], 'record_pin': selected['record'],
        'record_projection': compact, 'inventory': inventory, 'native': native, 'csvrows': csvrows,
        'validated_query': query, 'expected_wp_input': str(helper.retained_wp_input_path(reports['wp_input']['path']))})
    assert pin_read(selected['record'])
assert hashlib.sha256(yaml_path.read_bytes()).hexdigest() == yaml_hash
result = {'classification': 'PINNED_COMPLETE_OBLIGATION_INPUT_METADATA_ONLY', 'records': rows,
    'yaml_origin': wanted_yaml, 'yaml_source_sha256': yaml_hash, 'helper_sha256': hashlib.sha256(helper_raw).hexdigest(),
    'record_audit_executed': False, 'scientific_reexecution': False,
    'scope': 'Complete inputs to current_goals/current_csv/dependency_DAG only; no source/runtime/native capture reexecution or new cold acceptance.'}
encoded = json.dumps(result, sort_keys=True, indent=2).encode()
assert len(encoded) <= 1024 * 1024
print(encoded.decode())
