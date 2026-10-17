"""Narrow profile-only successor; all V4 production and scientific bytes freeze."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'production-route-v4'
OUT = HERE / 'profile'
OUT.mkdir(exist_ok=True)
source = (OLD / 'profile/profile_builder_v3.py').read_text()
assert hashlib.sha256(source.encode()).hexdigest() == 'ef778f285269d4b743bb3e626adbae47824f8885fe736a887306e6d2051beee1'
edits = []


def change(old, new):
    global source
    assert source.count(old) == 1
    source = source.replace(old, new, 1)
    edits.append({'old': old, 'new': new})


HELPERS = '''# Exact physical extent in the already admitted Clang22 Linux inventory.
# This is a selected driver-role bound, not a generic document-cap increase.
SELECTED_DRIVER_BYTES = 271520144


def stream_pin(row, *, limit):
    """Hash a bounded physical input without retaining its payload."""
    exact(row, {'path', 'bytes', 'sha256'}, 'physical pin')
    need(type(row['path']) is str and Path(row['path']).is_absolute()
         and type(limit) is int and type(row['bytes']) is int and 0 <= row['bytes'] <= limit
         and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']),
         'explicit bounded physical pin required')
    path = Path(row['path']); before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path
         and before.st_size == row['bytes'], 'canonical physical extent required before streaming')
    hasher = hashlib.sha256(); count = 0
    with path.open('rb') as handle:
        while True:
            chunk = handle.read(min(1024 * 1024, row['bytes'] - count + 1))
            if not chunk: break
            count += len(chunk)
            need(count <= row['bytes'], 'physical stream grew beyond selected extent')
            hasher.update(chunk)
    need(count == row['bytes'] and hasher.hexdigest() == row['sha256']
         and stable(path.lstat()) == stable(before), 'physical stream changed or hash differs')
    return dict(row)


def check_physical_inventory(inventory):
    exact(inventory, {'compiler_driver', 'compiler_wrapper', 'device_configuration',
        'address_projection', 'numeric_runtime'}, 'complete physical role census')
    need(type(inventory['compiler_driver']) is dict
         and inventory['compiler_driver'].get('bytes') == SELECTED_DRIVER_BYTES,
         'exact admitted Clang22 driver extent required')
    for role, row in inventory.items():
        stream_pin(row, limit=SELECTED_DRIVER_BYTES if role == 'compiler_driver' else 256 * 1024 * 1024)
    return inventory


'''
change('def lowering_identity_without_probe(module, compiler_observation):',
    HELPERS + 'def lowering_identity_without_probe(module, compiler_observation, *, physical_inventory):')
change("    read(compiler_observation['wrapper']); read(compiler_observation['driver'], limit=256 * 1024 * 1024)",
    "    exact(physical_inventory, {'compiler_driver', 'compiler_wrapper', 'device_configuration',\n"
    "        'address_projection', 'numeric_runtime'}, 'complete physical role census')\n"
    "    need(compiler_observation['wrapper'] == physical_inventory['compiler_wrapper']\n"
    "         and compiler_observation['driver'] == physical_inventory['compiler_driver']\n"
    "         and compiler_observation['driver']['bytes'] == SELECTED_DRIVER_BYTES,\n"
    "         'observed compiler pins differ from the exact selected physical inventory')\n"
    "    stream_pin(compiler_observation['wrapper'], limit=256 * 1024 * 1024)\n"
    "    stream_pin(compiler_observation['driver'], limit=SELECTED_DRIVER_BYTES)")
change("    exact(request['physical_inputs'], {'compiler_driver', 'compiler_wrapper', 'device_configuration',\n"
    "        'address_projection', 'numeric_runtime'}, 'complete physical role census')\n"
    "    for row in request['physical_inputs'].values():\n"
    "        read(row, limit=256 * 1024 * 1024)",
    "    check_physical_inventory(request['physical_inputs'])")
change("lowering_identity_without_probe(lowering, parse(read(request['compiler_observation'])))",
    "lowering_identity_without_probe(lowering, parse(read(request['compiler_observation'])),\n"
    "        physical_inventory=request['physical_inputs'])")
change("    need(type(runtime) is dict and runtime.get('command') == compiler_observation['command']\n"
    "         and runtime.get('driver') == {key: compiler_observation['driver'][key] for key in ('path', 'sha256')}\n"
    "         and 'unavailable' not in runtime, 'exact observed underlying-driver runtime descriptor required')",
    "    need(type(runtime) is dict and set(runtime) == {'check', 'command', 'driver', 'command_executable', 'frontend', 'parser', 'headers'}\n"
    "         and runtime['command'] == compiler_observation['command']\n"
    "         and runtime['driver'] == {key: compiler_observation['driver'][key] for key in ('path', 'sha256')}\n"
    "         and runtime['command_executable'] == {key: compiler_observation['wrapper'][key] for key in ('path', 'sha256')},\n"
    "         'complete selected wrapper/underlying-driver runtime descriptor required')")
change('''    """Same exact hash recipe; only two observed-runtime leaves are supplied.

    Never call locate()/runtime_identity(): both may probe a compiler. The root
    must have separately admitted the physical wrapper, driver, selected runtime
    descriptor and version. This reproduces an identity, not its observation.
    """''', '''    """Same exact hash recipe with two root-selected expected-runtime leaves.

    Never call locate()/runtime_identity(): both may probe a compiler. Root must
    preserve any original alias-command observation and separately select the
    exact absolute-command normalization/provenance. This derives the future
    job's expected identity; actual public recomputation must still match it.
    """''')
ast.parse(source)
(OUT / 'profile_builder_v4.py').write_text(source)
preparer = (OLD / 'profile/profile_prepare_v3.py').read_text().replace('profile_builder_v3.py', 'profile_builder_v4.py').replace('selected_profile_builder_v3', 'selected_profile_builder_v4')
old_hash = hashlib.sha256((OLD / 'profile/profile_builder_v3.py').read_bytes()).hexdigest()
preparer = preparer.replace(old_hash, hashlib.sha256(source.encode()).hexdigest())
(OUT / 'profile_prepare_v4.py').write_text(preparer)
for name in ('normal-producer-basis-v4.json', 'pair_plan_v2.py', 'pair-selection-template-v4.json'):
    (OUT / name).write_bytes((OLD / 'profile' / name).read_bytes())
selection = json.loads((OLD / 'profile/selection-template-v4.json').read_bytes())
selection['compiler_observation'] = None
(OUT / 'selection-template-v5.json').write_text(json.dumps(selection, sort_keys=True, indent=2) + '\n')
(HERE / 'builder-inverse-v5.json').write_text(json.dumps({'schema': 'exact-profile-streaming-v5-inverse-1',
    'replacements': edits, 'production_patch_unchanged': True,
    'preparer_inverse_names': {'profile_builder_v4.py': 'profile_builder_v3.py',
        'selected_profile_builder_v4': 'selected_profile_builder_v3'},
    'template_delta': {'compiler_observation': 'null until root selects the separate compiler/runtime descriptor'}}, sort_keys=True, indent=2) + '\n')
print(json.dumps({'builder_sha256': hashlib.sha256(source.encode()).hexdigest(), 'production_written': False}))
