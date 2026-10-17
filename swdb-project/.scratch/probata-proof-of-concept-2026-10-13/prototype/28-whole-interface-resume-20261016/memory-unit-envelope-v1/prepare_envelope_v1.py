"""2026-10-16 ET. Inert memory-family binding of the reviewed V4 envelope."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parent.parent
BASE = WHOLE / 'normalized-unit-envelope-v4'
MEMORY = WHOLE / 'memory-normalized-ingress-v2'
TRACE = WHOLE.parent / '28-public-memory-trace-resume-20261016'
RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-unit-observation-2baf722f-v2'
RUNTIME = WHOLE / 'compiler-memory-capture-v1/linux_memory_capture_policy_v1.json'
ROOT_SELECTION_KEYS = {'guard_files', 'node'}
KNOWN_GUARDS = {'execute.py': '8442533f911e2ba7f10757a5b16ba451d4ece7d9d5dc292ce5b9d8c29eabdcbf',
    'watch.py': '49be8a36d6e04b50e1ab599dad8b00f78a1c639132c3079c523c2c0c9177c5f0'}


def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def pin(path, remote=None):
    data = path.read_bytes()
    return {'path': str(path) if remote is None else remote, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def document(path): return json.loads(path.read_bytes())


def build(root_selection=None):
    # This is a prospective root selection, not an observed lane/guard state.
    if root_selection is not None:
        if type(root_selection) is not dict or set(root_selection) != ROOT_SELECTION_KEYS:
            raise ValueError('closed root guard/node selection required')
        guards = root_selection['guard_files']
        if type(guards) is not dict or guards != KNOWN_GUARDS:
            raise ValueError('exact root guard hashes required')
        if type(root_selection['node']) is not int or root_selection['node'] not in (0, 1):
            raise ValueError('one explicit root-selected node required')
    for path, expected in ((BASE / 'source-packet-v4.json', 'b74571794e41588c2110c9d0ccc9150c825c08a4ca83b78288db7fab21e06667'),
        (MEMORY / 'source-packet-v2.json', '9904def8876809e84e737355c93f6a1c87bfb4751bf1c901a05a3b6629915df9')):
        if pin(path)['sha256'] != expected: raise ValueError('frozen envelope/memory source basis changed')
    entry = (BASE / 'linux_observation_envelope_v4.py').read_text()
    observer_path = MEMORY / 'observer/observe_memory_entry_v1.py'
    selected = document(MEMORY / 'observer/observation-policy-template-v1.json')
    runtime = document(RUNTIME)
    edits = []
    def replace(old, new, count=1):
        nonlocal entry
        if entry.count(old) != count: raise ValueError('exact envelope binding inverse differs: ' + old[:80])
        entry = entry.replace(old, new); edits.append({'old': old, 'new': new, 'count': count})
    replace('t28-unit-observation-2baf722f-v4', 't28-memory-unit-observation-2baf722f-v2')
    replace('control/linux_observation_envelope_v4.py', 'control/linux_memory_observation_envelope_v1.py', 2)
    replace('control/envelope-policy-v4.json', 'control/envelope-policy-v1.json', 2)
    replace("OBSERVER_SHA = '0d12e2ac33e5417abaac8c071a0d2d36492c6dc52651f23d0229dc94527e4fab'",
        "OBSERVER_SHA = '" + pin(observer_path)['sha256'] + "'")
    replace("RUNTIME_POLICY_SHA = '8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517'",
        "RUNTIME_POLICY_SHA = '" + pin(RUNTIME)['sha256'] + "'")
    replace('observer/control/observe_entry_v2.py', 'observer/control/observe_memory_entry_v1.py')
    replace('source_call_fixture_v2.cpp', 'same_thread_memory_v1.cpp', 2)
    replace('proof_units/source.cpp', 'proof_units/same_thread_memory_v1.cpp', 3)
    replace("policy['library_source']['bytes'] == 4524", "policy['library_source']['bytes'] == 3258")
    replace("'3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'",
        "'55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'")
    tree = ast.parse(entry)
    for name, value in (
        ('OBSERVER_CONTROLS', tuple(sorted(selected['controls']))),
        ('OBSERVER_OUTPUTS', ('whole-unit-preparation.json', 'observed-input-pins.json', 'memory-source-units.json', 'unit-observation-result.json'))):
        node = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets))
        replace(ast.get_source_segment(entry, node), name + ' = ' + repr(value))
        tree = ast.parse(entry)
    (HERE / 'linux_memory_observation_envelope_v1.py').write_text(entry)
    (HERE / 'exact-envelope-inverse-v1.json').write_text(json.dumps({'schema': 'literal-memory-envelope-V4-inverse-1',
        'date': '2026-10-16 ET', 'basis': pin(BASE / 'linux_observation_envelope_v4.py'), 'replacements': edits,
        'logic_gates_removed_or_relaxed': False}, sort_keys=True, indent=2) + '\n')
    staged = {}; origins = {}
    def stage(path, name=None):
        name = path.name if name is None else name
        if name in staged: raise ValueError('duplicate root control basename')
        staged[name] = pin(path, RAW + '/control/' + name); origins[name] = pin(path)
        return staged[name]
    for name in selected['controls']:
        path = MEMORY / 'observer' / name
        stage(path if path.exists() else MEMORY / 'observer/modules' / name)
    stage(HERE / 'linux_memory_observation_envelope_v1.py')
    for name in ('python_startup_roles_v2.py', 'python_role_observer_v2.py'): stage(TRACE / name)
    stage(WHOLE / 'linux_native86_entry_v4.py')
    stage(POC / 'evidence/resume-20261016-lane-coordination/t28-linux-runtime-observer-v2-actual-20261016.json')
    # Data-only provenance, explicitly not an independent review or authority.
    provenance = stage(MEMORY / 'source-packet-v2.json', 'memory-source-proposal.json')
    for name, row in document(MEMORY / 'observer-staging-plan-v2.json')['external_provenance_mirrors'].items():
        stage(Path(row['path']), name)
    source = stage(WHOLE / 'source-memory-fixtures-v1/same_thread_memory_v1.cpp')
    selected['root_admission_receipt'] = provenance
    selected['controls'] = {name: {**staged[name], 'path': RAW + '/observer/control/' + name} for name in selected['controls']}
    (HERE / 'observation-policy-v1.json').write_bytes(canonical(selected))
    observer_pin = stage(HERE / 'observation-policy-v1.json')
    policy = {'schema': 'linux-normalized-unit-observation-envelope-1', 'raw_name': RAW.rsplit('/', 1)[1],
        'source_commit': runtime['source_commit'], 'source_project': runtime['source_project'], 'python': runtime['python'],
        'node': None if root_selection is None else root_selection['node'],
        'budgets': {'whole_seconds': 1200, 'entry_seconds': 1180, 'rss_bytes': 4294967296, 'total_bytes': 268435456,
            'file_bytes': 4194304, 'control_bytes': 1048576},
        'guard_files': None if root_selection is None else root_selection['guard_files'],
        'disk_floor_bytes': 21474836480, 'runtime_policy': pin(RUNTIME, selected['capture']['original']['policy']['path']),
        'controls': staged, 'observer_policy': {**observer_pin, 'path': RAW + '/observer/control/observation-policy-v1.json'},
        'library_source': {**source, 'path': RAW + '/library_fixture/proof_units/same_thread_memory_v1.cpp'},
        'root_admission_receipt': provenance}
    (HERE / 'envelope-policy-v1.json').write_bytes(canonical(policy))
    total = sum(row['bytes'] for row in staged.values()) + (HERE / 'envelope-policy-v1.json').stat().st_size
    if total > 1048576: raise ValueError('whole staged root packet exceeds one MiB')
    command = document(BASE / 'command-v4.json')
    command.update(raw=RAW, actual_executed=False, source_commit=runtime['source_commit'], source_project=runtime['source_project'],
        argv=[runtime['python'], '-I', '-B', '-X', 'pycache_prefix=' + RAW + '/entry-source-cache',
            RAW + '/control/linux_memory_observation_envelope_v1.py', RAW, RAW + '/control/envelope-policy-v1.json',
            pin(HERE / 'envelope-policy-v1.json')['sha256']], policy=pin(HERE / 'envelope-policy-v1.json'),
        stage_sources=origins, root_controls_bytes_including_policy=total, root_metadata_complete=root_selection is not None,
        root_created_directories=[RAW + '/control'],
        envelope_created_directories=[RAW + '/observer', RAW + '/observer/control', RAW + '/library_fixture', RAW + '/library_fixture/proof_units'],
        copies=[{'from': RAW + '/control/' + name, 'to': row['path']} for name, row in selected['controls'].items()] +
            [{'from': observer_pin['path'], 'to': policy['observer_policy']['path']}, {'from': source['path'], 'to': policy['library_source']['path']}],
        scope='Data-only genuine memory complete-TU/ABI/40-call/three-root observation; no model/body/native/proof/ownership/public admission')
    old_raw = document(BASE / 'command-v4.json')['raw']
    command = json.loads(json.dumps(command).replace(old_raw, RAW))
    command['root_source_provenance_role'] = 'Fixed memory source proposal bytes only; no review or execution authority inferred.'
    (HERE / 'command-v1.json').write_bytes(canonical(command))
    (HERE / 'root-selection-template-v1.json').write_text(json.dumps({'guard_files': {'execute.py': None, 'watch.py': None}, 'node': None}, indent=2) + '\n')
    return {'staged_controls': len(staged), 'staged_bytes_including_policy': total,
        'root_metadata_complete': root_selection is not None, 'actual_executed': False}


if __name__ == '__main__': print(json.dumps(build(), sort_keys=True))
