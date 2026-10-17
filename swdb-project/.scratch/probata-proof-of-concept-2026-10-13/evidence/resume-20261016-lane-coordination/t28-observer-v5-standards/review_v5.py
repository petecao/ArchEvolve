"""2026-10-16 ET. Independent local Standards/inverse controls; no observer run."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import signal
import stat
import sys
import unittest

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
WHOLE = POC/'prototype/28-whole-interface-resume-20261016'
NEW = WHOLE/'normalized-unit-envelope-v5'
OLD = WHOLE/'normalized-unit-envelope-v4'
EXPECTED = 'eb932238f0504c3330cc67aa1728f40fcc6956d0a18947c13693cdd40fdaa873'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('local source review refuses '+event)


def pin(path):
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path
    raw = path.read_bytes()
    after = path.lstat()
    fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    assert tuple(getattr(before, key) for key in fields) == tuple(getattr(after, key) for key in fields)
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def data(path):
    return json.loads(path.read_bytes())


def walk(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= set(value):
            yield {key: value[key] for key in ('path', 'bytes', 'sha256')}
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def nodes(path):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(path.read_bytes()).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def main():
    sys.dont_write_bytecode = True
    sys.addaudithook(audit)
    signal.alarm(60)
    packet_path = NEW/'source-packet-v5.json'
    assert pin(packet_path)['sha256'] == EXPECTED
    packet = data(packet_path)
    documents = [packet, data(OLD/'source-packet-v4.json'),
        data(WHOLE/'abi-enum-repair-v1/source-packet-v1.json'),
        data(WHOLE/'abi-semantic-dependents-v1/exact-inverses-v1.json')]
    documents += [data(Path(row['path'])) for row in packet['basis']]
    occurrences = [row for document in documents for row in walk(document)]
    selected = {str(packet_path): pin(packet_path)}
    remote = []
    for row in occurrences:
        path = Path(row['path'])
        if not path.is_absolute():
            raise ValueError('ambiguous review lineage pin: '+str(path))
        if str(path).startswith(('/data/', '/data1/', '/usr/', '/lib/')):
            remote.append(row)
            continue
        actual = pin(path)
        assert actual == row, row
        assert str(path) not in selected or selected[str(path)] == row
        selected[str(path)] = row
    before = dict(selected)
    inverse_rows = []
    inverse = data(NEW/'exact-inverses-v5.json')
    for relative, row in inverse['files'].items():
        raw = (NEW/relative).read_text()
        for replacement in reversed(row['replacements']):
            assert raw.count(replacement['new']) == replacement['count']
            raw = raw.replace(replacement['new'], replacement['old'])
        basis = Path(row['basis']['path'])
        assert pin(basis) == row['basis'] and raw.encode() == basis.read_bytes()
        inverse_rows.append({'file': relative, 'basis': row['basis'],
            'declared_edits': len(row['replacements']), 'full_inverse_exact': True})
    module_root = NEW/'observer/modules'
    generic = module_root/'compiler_unit_adapter_v3.py'
    semantic = module_root/'compiler_unit_adapter_v4.py'
    assert pin(generic)['sha256'] == '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'
    assert pin(semantic)['sha256'] == 'b5bd7293259f69ffe4e5d6094cb6bd46c2d5527ef95cd28d0aaa95d88529e6c6'
    assert semantic.read_bytes() == (WHOLE/'abi-enum-repair-v1/proposed/compiler_unit_adapter_v4.py').read_bytes()
    old_nodes, new_nodes = nodes(generic), nodes(semantic)
    same = [name for name in old_nodes if name != 'observed_abi']
    assert all(old_nodes[name] == new_nodes[name] for name in same)
    policy = data(NEW/'envelope-policy-v5.json')
    old_policy = data(OLD/'envelope-policy-v4.json')
    invariant_policy = ('schema', 'source_commit', 'source_project', 'python', 'node', 'budgets',
                        'guard_files', 'disk_floor_bytes', 'runtime_policy')
    assert all(policy[key] == old_policy[key] for key in invariant_policy)
    observation = data(NEW/'observation-policy-v1.json')
    old_observation = data(OLD/'observation-policy-v1.json')
    assert observation['capture'] == json.loads(json.dumps(old_observation['capture']).replace(
        'unit-observation-2baf722f-v4', 'unit-observation-2baf722f-v5'))
    assert observation['capture']['prepared'] is None
    command = data(NEW/'command-v5.json')
    assert command['argv'] == data(NEW/'root-argv-v5.json')
    assert command['policy'] == pin(NEW/'envelope-policy-v5.json')
    assert command['source_commit'] == policy['source_commit'] == '2baf722fdaa6cba24b859eae3172a6f597417d72'
    assert command['root_launch_requirements']['run_environment_unset'] == ['LIBRARY_PATH', 'LD_LIBRARY_PATH']
    assert command['root_launcher'] == pin(WHOLE/'root-launcher-loader-v11/launch_observer_loader_v11.py')
    assert len(command['stage_sources']) == len(policy['controls']) == 30
    for name, row in command['stage_sources'].items():
        assert pin(Path(row['path'])) == row
        expected = {**row, 'path': command['raw']+'/control/'+name}
        assert expected == policy['controls'][name]
    assert sum(row['bytes'] for row in policy['controls'].values()) + command['policy']['bytes'] == 479538
    manifest = data(NEW/'observer/fixed-modules-v3.json')
    assert len(manifest['modules']) == 14 and manifest['compatibility_module_alias'] == {}
    for row in manifest['modules']:
        actual = pin(module_root/row['file'])
        assert actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes']
    suite = unittest.TestSuite()
    for filename, classname in (('test_envelope_v5.py', 'Controls'),
            ('test_root_environment_v5.py', 'RootEnvironmentControls'),
            ('test_semantic_observer_v5.py', 'SemanticObserverControls')):
        namespace = runpy.run_path(str(NEW/filename), run_name='independent_local_'+classname)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace[classname]))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    with (HERE/'controls-v5.log').open('x') as stream:
        stream.write(log.getvalue())
    assert result.testsRun == 23 and result.wasSuccessful() and not result.skipped
    assert not EVENTS
    after = {path: pin(Path(path)) for path in selected}
    assert after == before
    output = {'date': '2026-10-16 ET', 'packet': pin(packet_path),
        'local_physical_pin_occurrences': len(occurrences)-len(remote),
        'unique_local_physical_pins_before_after': len(selected),
        'remote_metadata_pin_occurrences_not_freshly_observed': len(remote),
        'all_selected_physical_pins_unchanged': True,
        'local_physical_pins': list(selected.values()), 'full_inverses': inverse_rows,
        'generic_semantic_function_nodes_identical_except_observed_abi': same,
        'invariant_policy_fields': list(invariant_policy),
        'root_controls': 30, 'root_control_bytes_including_policy': 479538,
        'observer_controls': 16, 'fixed_actual_modules': 14,
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skips': len(result.skipped), 'external_operations': EVENTS,
        'exact_next_entry_argv': command['argv'], 'root_launcher': command['root_launcher'],
        'no_compiler_native_proof_observer_SSH_Git_execution': True,
        'runtime_and_remote_freshness_still_pending': True}
    with (HERE/'controls-v5-result.json').open('x') as stream:
        stream.write(json.dumps(output, sort_keys=True, indent=2)+'\n')
    signal.alarm(0)
    print(json.dumps({key: output[key] for key in ('unique_local_physical_pins_before_after',
        'tests', 'failures', 'errors', 'skips', 'external_operations', 'root_controls',
        'root_control_bytes_including_policy')}))


if __name__ == '__main__':
    main()
