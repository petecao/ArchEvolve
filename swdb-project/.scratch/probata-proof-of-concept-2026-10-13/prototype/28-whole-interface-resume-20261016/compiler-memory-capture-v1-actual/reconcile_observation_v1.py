"""2026-10-16 ET. Compact local metadata reconciliation, no remote work."""
import hashlib
import json
from pathlib import Path
import sys

EVENTS = []
def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('metadata reconciler refuses ' + event)
sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parent / 'compiler-memory-capture-v1'
POC = HERE.parents[2]
def document(path): return json.loads(Path(path).read_bytes())
def pin(path):
    path = Path(path); raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
def main():
    policy = document(AUTHOR / 'linux_memory_capture_policy_v1.json')
    command = document(AUTHOR / 'linux_memory_capture_command_v1.json')
    settled = document(HERE / 'settlement-stdout-v2.json')
    closure = document(HERE / 'closure-stdout-v1.json')
    for name in ['preflight-invocation.json', 'dispatch-invocation.json', 'settlement-invocation-v2.json', 'closure-invocation-v1.json']:
        assert document(HERE / name)['returncode'] == 0
    m = settled['metadata']; full = closure['metadata']; root = command['raw_root']
    assert settled['raw_root'] == closure['raw_root'] == root
    rows = closure['rows']; indexed = {row['path']: row for row in rows}
    assert len(rows) == len(indexed) == settled['extent']['files'] == 58
    assert all(row['path'] == root + '/' + row['relative'] and row['bytes'] <= 134217728 for row in rows)
    assert sum(row['bytes'] for row in rows) == settled['extent']['bytes'] == 48231895 <= 268435456
    assert settled['extent']['aliases'] == settled['extent']['special'] == []
    for row in command['controller_inputs']:
        current = indexed[root + '/control/' + Path(row['path']).name]
        assert (current['bytes'], current['sha256']) == (row['bytes'], row['sha256'])
    for name, expected in policy['guard_files'].items():
        assert indexed[root + '/' + name]['sha256'] == expected
    launch = m['launch.json']
    assert launch['command'] == command['argv'] and launch['source_commit'] == policy['source_commit']
    assert launch['source'] == command['source'] and launch['node'] == 1 and launch['timeout_seconds'] == 180
    assert launch['rss_cap_bytes'] == 4294967296 and launch['workers'] == 1
    assert launch['reviewed_wrapper_reuse'] == policy['guard_files']
    for role in ['outer-resources.json', 'resources.json']:
        result = m[role]
        assert result['exit_code'] == 0 and result['out_of_memory'] is False and result['timed_out'] is False
        assert 0 < result['wall_seconds'] <= 180 and 0 < result['peak_rss_bytes'] <= 4294967296
    lane = m['lane.json']['socket_lane']
    assert lane['node'] == 1 and lane['exit_code'] == 0 and lane['lease_generation'] == 642
    assert lane['numa_memory_policy'] == 'bind:1' and lane['cpus_allowed_list'] == ','.join(str(n) for n in range(1, 64, 2))
    assert settled['selected_original_processes'] == settled['process_read_failures'] == []
    assert settled['leases']['mbit10-evaluation-node1.meta.json']['state'] == 'released'
    assert settled['leases']['mbit10-evaluation.meta.json']['state'] == 'released'
    result = full['component/result.json']
    assert result == m['component/result.json'] and result['accepted'] is result['compiler_observation_complete'] is True
    assert result['error'] is None and result['after_input_errors'] == [] and result['bytecode_cache_present'] is False
    assert result['source_call_count'] == 0 and result['source_names'] == []
    for field in ['ABI_interpreted', 'source_call_admitted', 'strict_complete_TU_consumer_passed', 'native_or_solver_executed', 'public_proof', 'current_0_2', 'full_ticket28']:
        assert result[field] is False
    assert 'finalization_refusal' not in result and 0 < result['wall_seconds'] <= 165
    observation = full['component/compiler-observation.json']
    assert observation['source_commit'] == policy['source_commit'] and observation['original_source_coordinates'] is True
    commands = observation['commands']
    assert commands == m['component/commands.json'] and len(commands) == 4
    for actual, expected in zip(commands, policy['capture_recipe']['commands']):
        assert actual['phase'] == expected['phase'] and actual['argv'] == expected['argv'] and actual['cwd'] == expected['cwd']
        assert type(actual['returncode']) is int and actual['returncode'] == 0
        assert 0 < actual['timeout_seconds'] <= (120 if actual['phase'] == 'caller-ast' else 45)
        for role in ['stdout', 'stderr']:
            record = actual[role]; current = indexed[record['path']]
            assert all(record[key] == current[key] for key in ['path', 'bytes', 'sha256'])
        assert actual['stderr']['bytes'] == 0
    assert [g['label'] for g in observation['groups']] == ['caller', 'abi']
    for row in full['component/artifact-manifest.json']:
        current = indexed[row['path']]
        assert all(current[key] == row[key] for key in ['relative', 'path', 'bytes', 'sha256'])
    expected_inputs = [{'path': root + '/control/' + name, **policy['controller_files'][name]} for name in
                       ['same_thread_memory_v1.cpp', 'compiler_abi_probe_v1.cpp', 'm5ops.h']]
    expected_inputs += [{'path': policy['source_project'] + '/' + row['relative'], **{k: row[k] for k in ['bytes', 'sha256']}} for row in policy['source_inputs']]
    assert observation['inputs'] == expected_inputs
    assert full['capture-runtime-after.json'] == {'runtime': full['capture-runtime-before.json'], 'after_errors': []}
    assert full['capture-zlib-before.json'] == full['capture-zlib-after.json'] == policy['zlib_binding']
    assert full['source-after.json'] == m['source-after.json'] == {'commit': policy['source_commit'], 'source_unchanged': True, 'tracked_changes': ''}
    gzip = full['component/caller.ast.gzip.json']
    assert gzip == commands[1]['lossless_stdout'] and gzip['compressed_bytes'] == commands[1]['stdout']['bytes']
    assert gzip['compressed_sha256'] == commands[1]['stdout']['sha256'] and gzip['expanded_bytes'] == 537439896
    assert gzip['compressed_limit'] == 134217728 and gzip['expanded_limit'] == 2147483648
    assert not EVENTS
    receipt = {'date': '2026-10-16 ET', 'verdict': 'PASS_ACTUAL_COMPILER_OBSERVATION_METADATA_ONLY',
        'source_commit': policy['source_commit'], 'source_fixture_sha256': expected_inputs[0]['sha256'],
        'raw_root': root, 'node': 1, 'generation': 642, 'started_utc': lane['started_utc'], 'ended_utc': lane['ended_utc'],
        'actual_resources': {'outer': m['outer-resources.json'], 'inner': m['resources.json']},
        'root_admission': pin(POC / 'evidence/t28-memory-capture-v1-root-admission-20261016.json'),
        'author_packet': pin(AUTHOR / 'memory-capture-source-packet-v1.json'), 'policy': pin(AUTHOR / 'linux_memory_capture_policy_v1.json'),
        'source': pin(__file__), 'dispatch': pin(HERE / 'dispatch-invocation.json'),
        'preflight': pin(HERE / 'preflight-stdout.json'), 'settlement': pin(HERE / 'settlement-stdout-v2.json'),
        'full_compact_metadata': pin(HERE / 'closure-stdout-v1.json'), 'raw_inventory': {'files': 58, 'bytes': 48231895},
        'compiler_phases': [{'phase': row['phase'], 'returncode': row['returncode'], 'stdout': row['stdout'], 'stderr': row['stderr']} for row in commands],
        'wire_gzip': gzip, 'source_unchanged': True, 'all13_staged_controls_match': True,
        'raw_component_manifest_rows_match_fresh_hash_inventory': True,
        'declared_runtime_prepost_and_source_dependencies_remain_compiler_observer_premises': True,
        'finite_original_process_scan_empty': True, 'process_read_failures': [], 'target_and_legacy_leases_released': True,
        'boundaries': {'original_stream_JSON_or_role_grammar_interpreted': False, 'ABI_or_same_TU_source_calls_admitted': False,
            'current_runtime_and_all_used_headers_independently_rehashed_by_reconciler': False,
            'prospective_role_normalization_and_source_consumers_required': True,
            'native_or_solver_or_public_proof': False, 'current_0_2_or_full_ticket28': False,
            'raw_AST_or_preprocess_payload_transferred': False, 'compiler_observations_and_OS_loader_remain_TCB': True}}
    target = HERE / 'actual-observation-reconciliation-v1.json'
    target.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(pin(target), sort_keys=True))
if __name__ == '__main__': main()
