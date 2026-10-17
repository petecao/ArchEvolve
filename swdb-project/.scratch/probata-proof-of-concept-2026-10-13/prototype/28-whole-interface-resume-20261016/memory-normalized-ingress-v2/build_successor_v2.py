"""2026-10-16 ET. Deterministic inert ABI-inlet successor; no consumer run."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OLD = WHOLE / 'memory-normalized-ingress-v1'
ABI = WHOLE / 'abi-role-transport-v2'


def pin(path, remote=None):
    raw = path.read_bytes()
    return {'path': str(path) if remote is None else remote, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


assert pin(OLD / 'source-packet-v1.json')['sha256'] == 'ac04c216bbd1a2a9bc4f40108db0f5810286bdece522295fd4bfec8f3a25eb4b'
assert pin(ABI / 'source-packet-v2.json')['sha256'] == 'dc34b92c47111545777e7268df1f2f471889678b298fe1705d1308dc3f170b15'
for packet in (OLD / 'source-packet-v1.json', ABI / 'source-packet-v2.json'):
    for row in json.loads(packet.read_bytes())['files']:
        assert pin(Path(row['path'])) == row

for folder in ('proposed', 'integration-source', 'observer'):
    shutil.copytree(OLD / folder, HERE / folder, dirs_exist_ok=True)
for name in ('facts-provenance-v1.json', 'source-family-hook-inverse-v1.json',
             'shared-utility-inverse-v1.json', 'observer-entry-inverse-v1.json'):
    shutil.copyfile(OLD / name, HERE / name)

changes = {}


def replace(text, old, new, rows):
    assert text.count(old) == 1, old[:100]
    rows.append({'old': old, 'new': new})
    return text.replace(old, new, 1)


path = HERE / 'proposed/memory_normalized_compiler_adapter_v1.py'
text = path.read_text()
rows = []
text = replace(text, 'from swdb._dx100_whole import compiler_unit_adapter_v3 as legacy',
    'from swdb._dx100_whole import compiler_unit_adapter_v3 as legacy\nfrom swdb._dx100_whole import abi_role_transport_v1 as abi_transport', rows)
text = replace(text, '    prepared = legacy.prepare_unit(api, full_tu_raw=full_tu_raw, abi_raw=abi_raw, source_path=source_path,',
    "    derived_abi, abi_receipt = abi_transport.normalize_abi(abi_raw)\n"
    "    need(abi_receipt['selected_family'] == 'three-memory-g642', 'exact genuine G642 original ABI family required')\n"
    '    prepared = legacy.prepare_unit(api, full_tu_raw=full_tu_raw, abi_raw=derived_abi, source_path=source_path,', rows)
text = replace(text, "    check_cases(prepared)\n    return {**prepared, 'normalized_transport':", 
    "    check_cases(prepared)\n"
    "    need(prepared['abi_observation']['raw_probe_sha256'] == abi_receipt['derived_strict_sha256'],\n"
    "         'unchanged legacy ABI reader must identify its actual derived strict memory input')\n"
    "    return {**prepared, 'abi_observation': {**prepared['abi_observation'],\n"
    "        'original_raw_probe_sha256': abi_receipt['original_sha256'],\n"
    "        'paired_type_role_transport': abi_receipt}, 'normalized_transport':", rows)
path.write_text(text)
changes['proposed/memory_normalized_compiler_adapter_v1.py'] = rows
shutil.copyfile(path, HERE / 'observer/modules/memory_normalized_compiler_adapter_v1.py')
path = HERE / 'proposed/memory_normalized_capture_ingress_v1.py'
text = path.read_text()
rows = []
text = replace(text, "MEMORY_COMPILER_SHA='1315ebef75dc4219bcb012aa2a5f85cbcaeb82c54bb625fdad6f18ea397a6e62'",
    "MEMORY_COMPILER_SHA='" + pin(HERE / 'proposed/memory_normalized_compiler_adapter_v1.py')['sha256'] + "'", rows)
path.write_text(text)
changes['proposed/memory_normalized_capture_ingress_v1.py'] = rows
shutil.copyfile(path, HERE / 'observer/modules/memory_normalized_capture_ingress_v1.py')
shutil.copyfile(ABI / 'abi_role_transport_v1.py', HERE / 'proposed/abi_role_transport_v1.py')
shutil.copyfile(ABI / 'abi_role_transport_v1.py', HERE / 'observer/modules/abi_role_transport_v1.py')
token = WHOLE / 'streaming-minify-v1/strict_minify_v2.py'
shutil.copyfile(token, HERE / 'proposed/strict_minify_v2.py')
shutil.copyfile(token, HERE / 'observer/modules/strict_minify_v2.py')

path = HERE / 'integration-source/dx100_checked_source.py'
text = path.read_text()
rows = []
old = '    from swdb._dx100_whole import memory_normalized_compiler_adapter_v1, memory_source_preparation_v1\n'
text = replace(text, old, old + '    from swdb._dx100_whole import abi_role_transport_v1, strict_minify_v2\n', rows)
old = '        memory_normalized_compiler_adapter_v1, memory_source_preparation_v1,\n'
text = replace(text, old, old + '        abi_role_transport_v1, strict_minify_v2,\n', rows)
path.write_text(text)
changes['integration-source/dx100_checked_source.py'] = rows
full_inverse = json.loads((HERE / 'source-family-hook-inverse-v1.json').read_bytes())
full_inverse['replacements'].extend([{**row, 'count': 1} for row in rows])
full_inverse['schema'] = 'memory-source-family-hook-inverse-2'
write_json(HERE / 'source-family-hook-inverse-v2.json', full_inverse)
base = Path(full_inverse['base']['path'])
(HERE / 'source-family-hook-proposal-v2.patch').write_text(''.join(difflib.unified_diff(
    base.read_text().splitlines(True), text.splitlines(True), fromfile='a/swdb-project/swdb/dx100_checked_source.py',
    tofile='b/swdb-project/swdb/dx100_checked_source.py')))

observer = HERE / 'observer'
manifest_path = observer / 'fixed-memory-modules-v1.json'
manifest = json.loads(manifest_path.read_bytes())
modules = manifest['modules']
for name in ('strict_minify_v2', 'abi_role_transport_v1'):
    path = observer / 'modules' / (name + '.py')
    row = {'module': 'swdb._dx100_whole.' + name, 'file': path.name,
        'bytes': path.stat().st_size, 'sha256': pin(path)['sha256']}
    at = next(index for index, item in enumerate(modules) if item['module'].endswith('.memory_normalized_compiler_adapter_v1'))
    modules.insert(at, row)
for row in modules:
    current = pin(observer / 'modules' / row['file'])
    row.update(bytes=current['bytes'], sha256=current['sha256'])
write_json(manifest_path, manifest)

path = observer / 'observe_memory_entry_v1.py'
text = path.read_text()
rows = []
old_sha = pin(OLD / 'observer/fixed-memory-modules-v1.json')['sha256']
text = replace(text, "MANIFEST_SHA = '" + old_sha + "'", "MANIFEST_SHA = '" + pin(manifest_path)['sha256'] + "'", rows)
node = next(n for n in ast.parse(text).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'MODULE_NAMES' for t in n.targets))
text = replace(text, ast.get_source_segment(text, node), 'MODULE_NAMES = ' + repr(tuple(row['module'] for row in modules)), rows)
path.write_text(text)
changes['observer/observe_memory_entry_v1.py'] = rows
full_inverse = json.loads((HERE / 'observer-entry-inverse-v1.json').read_bytes())
for original in full_inverse['replacements']:
    for row in rows:
        original['new'] = original['new'].replace(row['old'], row['new'])
write_json(HERE / 'observer-entry-inverse-v2.json', full_inverse)

policy_path = observer / 'observation-policy-template-v1.json'
policy = json.loads(policy_path.read_bytes())
old_raw = policy['output_root'].removesuffix('/observer')
raw = old_raw.removesuffix('-v1') + '-v2'
policy = json.loads(json.dumps(policy).replace(old_raw, raw))
control = raw + '/observer/control'
for row in modules:
    path = observer / 'modules' / row['file']
    policy['controls'][path.name] = pin(path, control + '/' + path.name)
for path in (manifest_path, observer / 'observe_memory_entry_v1.py'):
    policy['controls'][path.name] = pin(path, control + '/' + path.name)
write_json(policy_path, policy)
staging = json.loads((OLD / 'observer-staging-plan-v1.json').read_bytes())
staging = json.loads(json.dumps(staging).replace(old_raw, raw))
staging.update(schema='prospective-memory-observer-staging-plan-2', raw=raw,
    controls={name: pin(observer / 'modules' / name if (observer / 'modules' / name).exists() else observer / name)
              for name in policy['controls']}, policy=pin(policy_path))
for name, row in staging['external_provenance_mirrors'].items():
    staging['external_provenance_mirrors'][name] = pin(observer / name)
write_json(HERE / 'observer-staging-plan-v2.json', staging)

inverse = {'schema': 'memory-ABI-inlet-successor-exact-source-inverse-2',
    'predecessor': pin(OLD / 'source-packet-v1.json'), 'changed_source_replacements': changes,
    'new_source_copies': {'abi_role_transport_v1.py': pin(ABI / 'abi_role_transport_v1.py'),
        'strict_minify_v2.py': pin(token)},
    'unchanged_semantic_sources': ['proposed/memory_source_preparation_v1.py', 'proposed/capture_family_dispatch_v1.py',
        'proposed/memory_capture_facts_v1.json'],
    'memory_ingress_function_bodies_unchanged': True,
    'actual_retained_ABI_replay_or_observer_executed': False}
write_json(HERE / 'successor-inverse-v2.json', inverse)
print(json.dumps({'modules': len(modules), 'controls': len(policy['controls']),
    'control_bytes': sum(row['bytes'] for row in policy['controls'].values()), 'actual_executed': False}, sort_keys=True))
