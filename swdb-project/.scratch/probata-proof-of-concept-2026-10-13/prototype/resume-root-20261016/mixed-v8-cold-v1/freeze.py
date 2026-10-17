"""2026-10-16 ET. Local-only mixed cold source preparation; no actual execution."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]


def pin(path):
    value = path.read_bytes()
    return {'path': str(path), 'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}


def main():
    prior = POC / 'prototype/25-owned-transfer-20261016/cold-g621-v3/observer.py'
    prior_source = prior.read_text()
    names = {'need', 'sha', 'compact', 'digest', 'identity', 'physical', 'read_bytes', 'pin', 'read', 'git', 'audit'}
    helpers = {node.name: ast.get_source_segment(prior_source, node) for node in ast.parse(prior_source).body
               if isinstance(node, ast.FunctionDef) and node.name in names}
    assert set(helpers) == names
    packet_dir = HERE.parent / 'mixed-pair-actual-v8'
    entry_source = (packet_dir / 'entry.py').read_text()
    gate = next(ast.get_source_segment(entry_source, node) for node in ast.parse(entry_source).body
                if isinstance(node, ast.FunctionDef) and node.name == 'check_eight_records')
    evidence = POC / 'evidence/resume-20261016-lane-coordination'
    actual_path = evidence / 't25-mixed-v8-actual-passive-settlement-v2-20261016.json'
    actual = json.loads(actual_path.read_bytes())
    assert pin(actual_path)['sha256'] == '25094840f2dd1460d3bcca972103ac1fffb79c28efce71734f3a0edb1854ce86'
    context = {'date': '2026-10-16 ET', 'policy_sha256': '0e7df71c422e83137d9fc18737233c756dab772cd3aca5b495008dc1f5a20f97',
        'raw_regular_pins': {r['relative']: {k: r[k] for k in ('bytes', 'sha256')}
                             for r in actual['raw_manifest'] if r['kind'] == 'regular'},
        'raw_membership': [{k: r[k] for k in ('relative', 'kind')} for r in actual['raw_manifest']],
        'aliases': {r['relative']: r['literal_target'] for r in actual['raw_manifest'] if r['kind'] == 'symlink'},
        'model_names': ['std_pair_int_int_ptr_' + name for name in ('ctor_default', 'ctor', 'copy_ctor', 'operator_assign')],
        'eight_record_gate_source': gate,
        'equal_retained_before_after': [['mixed-source-before.json', 'mixed-source-after.json'],
             ['initialized-runtime-before.json', 'initialized-runtime-after.json'],
             ['mixed-why3-runtime-before.json', 'mixed-why3-runtime-after.json'],
             ['mixed-native-runtime-before.json', 'mixed-native-runtime-after.json'],
             ['mixed-native-C-wrapper-before.json', 'mixed-native-C-wrapper-after.json']]}
    template = (HERE / 'observer.py').read_text()
    assert template.count('# __REVIEWED_READ_ONLY_HELPERS__') == 1
    source = template.replace('# __REVIEWED_READ_ONLY_HELPERS__', '\n\n\n'.join(helpers.values()))
    source = source.replace("if __name__ == '__main__':", 'CONTEXT = json.loads(' + repr(json.dumps(context, sort_keys=True)) + ")\n\nif __name__ == '__main__':")
    ast.parse(source)
    compile(source, '<inert-mixed-cold-reader>', 'exec')
    entry = HERE / 'entry.py'
    assert not entry.exists()
    entry.write_text(source)
    (HERE / 'context.json').write_text(json.dumps(context, sort_keys=True, indent=2) + '\n')
    recipe = {'schema': 'mixed-v8-cold-passive-command-1', 'date': '2026-10-16 ET',
        'status': 'INERT_ROOT_REVIEW_AND_ADMISSION_REQUIRED', 'actual_executed': False,
        'argv_after_fresh_root_readonly_host_preflight': ['/usr/bin/python3', '-I', '-B', '-'],
        'stdin': pin(entry), 'host': 'mbit10', 'outer_timeout_seconds': 200, 'inner_alarm_seconds': 180,
        'address_space_bytes': 536870912, 'stdout_cap_bytes': 2097152, 'remote_writes': False,
        'only_child': 'Fixed read-only Git rev-parse/status, with fsmonitor/preload/index threading disabled.',
        'selected_metadata_package_TCB': 'System PyYAML SafeLoader with duplicate-key refusal; no project import.',
        'expected_completed_observation_exit': 2,
        'result_scope': 'All available record/native/CSV/CBMC/output metadata reconciliation remains separate from unavailable complete original solver-task/import/hypothesis bytes. No cold scientific PASS or native/proof rerun.'}
    (HERE / 'command.json').write_text(json.dumps(recipe, sort_keys=True, indent=2) + '\n')
    packet = {'schema': 'mixed-v8-cold-source-packet-1', 'date': '2026-10-16 ET',
        'status': 'INERT_AVAILABLE_EVIDENCE_READER_FULL_TASK_CLOSURE_KNOWN_UNAVAILABLE',
        'actual_executed': False, 'scientific_acceptance': False,
        'source_commit': actual['source_commit'], 'raw_root': actual['raw_root'],
        'raw_regular_files': 144, 'raw_bytes': 10897771, 'fixture_records': 8,
        'known_retained_original_standalone_solver_task_files': 0,
        'inputs': [pin(path) for path in (prior, packet_dir / 'source-packet.json', packet_dir / 'entry.py',
            packet_dir / 'policy.json', actual_path, evidence / 't25-mixed-v8-actual-passive-decision-20261016.json')],
        'read_only_helper_lineage': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in helpers.items()},
        'unchanged_complete_eight_record_gate_sha256': hashlib.sha256(gate.encode()).hexdigest(),
        'outputs': [pin(HERE / name) for name in ('observer.py', 'entry.py', 'context.json', 'command.json', 'pure_controls.py')],
        'full_closure_gate': 'The raw namespace contains no standalone solver tasks. Read all available native/CSV/CBMC/replay contexts, preserve missing hypotheses/import/task bytes explicitly and do not grant a complete cold scientific certificate.',
        'root_source_review_and_passive_admission_required': True,
        'no_compiler_native_verifier_solver_or_remote_mutation': True}
    (HERE / 'source-packet.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
    print(json.dumps(pin(HERE / 'source-packet.json')))


if __name__ == '__main__':
    main()
