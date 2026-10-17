"""2026-10-16 ET. Inert ABI-inlet/private-observer successor, never execute it."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import shutil

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OLD = WHOLE / 'normalized-unit-envelope-v3'
OBSERVER = WHOLE / 'normalized-unit-observation-v1'
ABI = WHOLE / 'abi-role-transport-v2'
OUT = HERE / 'observer'
MODULES = OUT / 'modules'
MODULES.mkdir(parents=True, exist_ok=True)


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


assert pin(OLD / 'source-packet-v3.json')['sha256'] == 'd7e90dcdf36edaebd7a9b694ba673ed88ddbb4bca907d29b5ae5ee403d5df0cb'
assert pin(ABI / 'source-packet-v2.json')['sha256'] == 'dc34b92c47111545777e7268df1f2f471889678b298fe1705d1308dc3f170b15'
for packet in (OLD / 'source-packet-v3.json', ABI / 'source-packet-v2.json'):
    for row in json.loads(packet.read_bytes())['files']:
        assert pin(Path(row['path'])) == row

inverses = {}


def edit(source, old, new, rows, count=1):
    assert count > 0 and source.count(old) == count, old[:90]
    rows.append({'old': old, 'new': new, 'count': count})
    return source.replace(old, new)


manifest = json.loads((OBSERVER / 'fixed-modules-v1.json').read_bytes())
rows = manifest['modules']
for row in rows:
    shutil.copyfile(OBSERVER / 'modules' / row['file'], MODULES / row['file'])
adapter = next(row for row in rows if row['module'] == 'swdb._dx100_whole.normalized_compiler_adapter_v1')
# The unchanged ingress uses this explicit compatibility module name. The
# physical source basename and manifest identify the reviewed V2 implementation.
(MODULES / adapter['file']).unlink()
adapter.update(file='normalized_compiler_adapter_v2.py', origin=str(ABI / 'normalized_compiler_adapter_v2.py'))
shutil.copyfile(ABI / adapter['file'], MODULES / adapter['file'])
adapter.update(bytes=pin(MODULES / adapter['file'])['bytes'], sha256=pin(MODULES / adapter['file'])['sha256'])
ingress = next(row for row in rows if row['module'] == 'swdb._dx100_whole.normalized_capture_ingress_v2')
source = (MODULES / ingress['file']).read_text()
edits = []
source = edit(source,
    "NORMALIZED_COMPILER_SHA='0bbf572196677dbc926bb5d331022c2766e44c287bd1ea3cce0ef077153a8a01'",
    "NORMALIZED_COMPILER_SHA='8acf26651a1e682bb6857128f1a0d5e184b52f489cccd32ea60eb471c1a65ff3'", edits)
(MODULES / ingress['file']).write_text(source)
ingress.update(bytes=pin(MODULES / ingress['file'])['bytes'], sha256=pin(MODULES / ingress['file'])['sha256'],
    exact_constant_rebinding='NORMALIZED_COMPILER_SHA only; all functions and other constants unchanged')
inverses['observer/modules/' + ingress['file']] = {
    'basis': pin(OBSERVER / 'modules' / ingress['file']), 'replacements': edits}
new_modules = [
    ('swdb._dx100_whole.strict_minify_v2', WHOLE / 'streaming-minify-v1/strict_minify_v2.py'),
    ('swdb._dx100_whole.abi_role_transport_v1', ABI / 'abi_role_transport_v1.py')]
at = rows.index(adapter)
for offset, (name, origin) in enumerate(new_modules):
    shutil.copyfile(origin, MODULES / origin.name)
    raw = pin(MODULES / origin.name)
    rows.insert(at + offset, {'module': name, 'file': origin.name, 'origin': str(origin),
        'bytes': raw['bytes'], 'sha256': raw['sha256']})
manifest.update(schema='fixed-private-normalized-observer-module-inventory-2',
    predecessor=pin(OBSERVER / 'fixed-modules-v1.json'),
    compatibility_module_alias={adapter['module']: adapter['file']},
    actual_ABI_replay_or_observer_execution=False)
write_json(OUT / 'fixed-modules-v2.json', manifest)

source = (OBSERVER / 'observe_entry_v1.py').read_text()
edits = []
assignment = next(node for node in ast.parse(source).body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'MANIFEST_SHA' for t in node.targets))
source = edit(source, ast.get_source_segment(source, assignment), "MANIFEST_SHA = '" + pin(OUT / 'fixed-modules-v2.json')['sha256'] + "'", edits)
assignment = next(node for node in ast.parse(source).body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'MODULE_NAMES' for t in node.targets))
source = edit(source, ast.get_source_segment(source, assignment), 'MODULE_NAMES = ' + repr(tuple(row['module'] for row in rows)), edits)
source = edit(source, 'fixed-modules-v1.json', 'fixed-modules-v2.json', edits, count=2)
(OUT / 'observe_entry_v2.py').write_text(source)
inverses['observer/observe_entry_v2.py'] = {'basis': pin(OBSERVER / 'observe_entry_v1.py'), 'replacements': edits}

template = json.loads((OBSERVER / 'observation-policy-template-v1.json').read_bytes())
control = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v4/observer/control')
template['controls'] = {}
for path in [*(MODULES / row['file'] for row in rows), OUT / 'fixed-modules-v2.json', OUT / 'observe_entry_v2.py']:
    template['controls'][path.name] = {**pin(path), 'path': str(control / path.name)}
write_json(OUT / 'observation-policy-template-v2.json', template)

source = (OLD / 'linux_observation_envelope_v3.py').read_text()
edits = []
for old, new, count in (
    ('t28-unit-observation-2baf722f-v3', 't28-unit-observation-2baf722f-v4', 1),
    ('control/linux_observation_envelope_v3.py', 'control/linux_observation_envelope_v4.py', 2),
    ('control/envelope-policy-v3.json', 'control/envelope-policy-v4.json', 2),
    ('observer/control/observe_entry_v1.py', 'observer/control/observe_entry_v2.py', 1)):
    source = edit(source, old, new, edits, count=count)
source = edit(source, "OBSERVER_SHA = '00886e67fe33b8b9ec37a1b86f494120c0ad3769b887d792fe8e1a38fc3b6926'",
    "OBSERVER_SHA = '" + pin(OUT / 'observe_entry_v2.py')['sha256'] + "'", edits)
assignment = next(node for node in ast.parse(source).body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'OBSERVER_CONTROLS' for t in node.targets))
source = edit(source, ast.get_source_segment(source, assignment), 'OBSERVER_CONTROLS = ' + repr(tuple(sorted(template['controls']))), edits)
(HERE / 'linux_observation_envelope_v4.py').write_text(source)
inverses['linux_observation_envelope_v4.py'] = {'basis': pin(OLD / 'linux_observation_envelope_v3.py'), 'replacements': edits}

source = (OLD / 'prepare_envelope_v3.py').read_text()
edits = []
for old, new in (
    ("OBSERVER = WHOLE / 'normalized-unit-observation-v1'", "OBSERVER = HERE / 'observer'"),
    ('t28-unit-observation-2baf722f-v3', 't28-unit-observation-2baf722f-v4'),
    ('linux_observation_envelope_v3.py', 'linux_observation_envelope_v4.py'),
    ('envelope-policy-v3.json', 'envelope-policy-v4.json'),
    ('envelope-policy-template-v3.json', 'envelope-policy-template-v4.json'),
    ('command-v3.json', 'command-v4.json'), ('command-template-v3.json', 'command-template-v4.json'),
    ('observation-policy-template-v1.json', 'observation-policy-template-v2.json'),
    ('OBSERVER / \'observe_entry_v1.py\'', 'OBSERVER / \'observe_entry_v2.py\''),
    ("'observer_code_unchanged'", "'observer_code_selected'")):
    source = edit(source, old, new, edits, count=source.count(old))
(HERE / 'prepare_envelope_v4.py').write_text(source)
inverses['prepare_envelope_v4.py'] = {'basis': pin(OLD / 'prepare_envelope_v3.py'), 'replacements': edits}

metadata = (OLD / 'root-metadata-selection-v3.json').read_text().replace('t28-unit-observation-2baf722f-v3', 't28-unit-observation-2baf722f-v4')
(HERE / 'root-metadata-selection-v4.json').write_text(metadata)
shutil.copyfile(OLD / 'root-metadata-provenance-v1.json', HERE / 'root-metadata-provenance-v1.json')
write_json(HERE / 'exact-inverses-v4.json', {'schema': 'ABI-observer-envelope-successor-exact-inverses-4',
    'date': '2026-10-16 ET', 'files': inverses,
    'adapter': pin(ABI / 'normalized_compiler_adapter_v2.py'),
    'ABI_helper': pin(ABI / 'abi_role_transport_v1.py'),
    'strict_token_grammar': pin(WHOLE / 'streaming-minify-v1/strict_minify_v2.py'),
    'all_other_observer_module_bytes_unchanged': True,
    'root_launcher_source_or_guard_profile_changed': False})
builder = runpy.run_path(str(HERE / 'prepare_envelope_v4.py'), run_name='inert_observer_successor_builder')
print(json.dumps(builder['build'](json.loads(metadata)), sort_keys=True))
