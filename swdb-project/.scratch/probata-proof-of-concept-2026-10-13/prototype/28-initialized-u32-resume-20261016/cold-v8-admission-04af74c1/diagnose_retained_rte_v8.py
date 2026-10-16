"""Passive original reporter metadata only; no record-audit or tools."""
from pathlib import Path
import csv
import hashlib
import io
import json
import sys


def deny(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event in {'os.system', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir'}:
        raise RuntimeError('passive RTE metadata refuses ' + event)
    if event == 'open':
        _path, mode, flags = args
        if mode is not None and any(c in mode for c in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('passive RTE metadata refuses writes')


sys.addaudithook(deny)
context = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v8/control')
raw_policy = (context / 'initialized-cold-policy-04af74c1-v8.json').read_bytes()
assert hashlib.sha256(raw_policy).hexdigest() == 'c4f0bd5ea71b59fe8672c378ac04f2de58c07434b237c4158d3a7750a831762a'
policy = json.loads(raw_policy)
raw = Path(policy['raw'])


def read(name):
    pin = policy['raw_manifest']['files'][name]
    data = (raw / name).read_bytes()
    assert len(data) == pin['bytes'] and hashlib.sha256(data).hexdigest() == pin['sha256']
    return data, pin


rows = []
for record in policy['records']:
    names = [name for name in policy['raw_manifest']['files']
        if name.endswith('/wp/wp-inventory.json') and record['id'] in Path(name).parts]
    assert len(names) == 1
    name = names[0]
    data, inventory_pin = read(name)
    inventory = json.loads(data)
    properties = [row for row in inventory['properties'] if row['emitter'] == 'rte']
    ids = {row['property'] for row in properties}
    goals = [goal for goal in inventory['goals'] if goal['property'] in ids or set(goal['targets']) & ids]
    csv_name = name[:-len('wp-inventory.json')] + 'wp-properties.csv'
    csv_data, csv_pin = read(csv_name)
    csv_rows = list(csv.DictReader(io.StringIO(csv_data.decode()), delimiter='\t'))
    selected_csv = [row for row in csv_rows if row['property kind'] == 'initialization']
    rows.append({'expected_result': record['expected_result'], 'inventory_pin': inventory_pin,
        'CSV_pin': csv_pin, 'RTE_properties': properties, 'RTE_native_goals': goals,
        'initialization_CSV_rows': selected_csv, 'total_properties': len(inventory['properties']),
        'total_native_goals': len(inventory['goals'])})
    assert read(name)[0] == data and read(csv_name)[0] == csv_data
print(json.dumps({'classification': 'PASSIVE_ORIGINAL_RTE_REPORTER_METADATA_ONLY', 'records': rows,
    'reader_audit_executed': False, 'scientific_reexecution': False}, sort_keys=True, indent=2))
