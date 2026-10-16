"""Mechanical fresh namespace/helper binding after the pure seam controls."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'cold-v8-admission-04af74c1'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


old_helper = pin(BASE / 'initialized_cold_obligations_v3.py')
helper = pin(HERE / 'initialized_cold_obligations_v4.py')
old_reader = (BASE / 'initialized_cold_audit_v8.py').read_text()
reader = old_reader.replace('initialized_cold_obligations_v3.py', 'initialized_cold_obligations_v4.py').replace(
    old_helper['sha256'], helper['sha256']).replace('initialized_cold_audit_v8.py', 'initialized_cold_audit_v9.py')
(HERE / 'initialized_cold_audit_v9.py').write_text(reader)
reader_pin = pin(HERE / 'initialized_cold_audit_v9.py')


def swap(value):
    if isinstance(value, str):
        return value.replace('initialized-cold-04af74c1-v8', 'initialized-cold-04af74c1-v9').replace(
            'initialized_cold_audit_v8.py', 'initialized_cold_audit_v9.py').replace(
            'initialized-cold-policy-04af74c1-v8.json', 'initialized-cold-policy-04af74c1-v9.json').replace(
            'initialized_cold_obligations_v3.py', 'initialized_cold_obligations_v4.py').replace(
            old_helper['sha256'], helper['sha256'])
    if isinstance(value, list):
        return [swap(item) for item in value]
    if isinstance(value, dict):
        return {swap(key): swap(item) for key, item in value.items()}
    return value


policy = swap(json.loads((BASE / 'initialized-cold-policy-04af74c1-v8.json').read_bytes()))
policy['reader_files']['initialized_cold_obligations_v4.py'].update(bytes=helper['bytes'], sha256=helper['sha256'])
policy['reader_sha256'] = reader_pin['sha256']
policy['provenance']['preserved_actual_v8_refusal'] = pin(BASE / 'initialized-cold-v8-actual-refusal-receipt-20261016.json')
policy['provenance']['complete_obligation_metadata_v8'] = pin(BASE / 'complete-obligation-input-metadata-20261016.json')
policy['provenance']['reviewed_RTE_projection'] = {
    'native_RTE_goal_count': 2, 'source_read_locals': ['first', 'second'], 'source_line': 47,
    'implicit_init_termination': 'Unknown; non-Extern; no native goal or active dependency; never credited',
    'partial_normal_return_scope_unchanged': True, 'historical_Why3server_before_after_pin': False}
policy_path = HERE / 'initialized-cold-policy-04af74c1-v9.json'
policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + '\n')
policy_pin = pin(policy_path)
command = swap(json.loads((BASE / 'initialized-cold-command-04af74c1-v8.json').read_bytes()))
command['command'][-1] = policy_pin['sha256']
rows = command['control_files']
for name, selected in ((helper_path := 'initialized_cold_obligations_v4.py', helper),
    ('initialized_cold_audit_v9.py', reader_pin), (policy_path.name, policy_pin)):
    rows[name].update(bytes=selected['bytes'], sha256=selected['sha256'])
command['control_total_bytes'] = sum(row['bytes'] for row in rows.values())
command_path = HERE / 'initialized-cold-command-04af74c1-v9.json'
command_path.write_text(json.dumps(command, indent=2, sort_keys=True) + '\n')
ns = {'__name__': 'inert_full_obligation_replay', '__file__': str(HERE / 'test_complete_obligations_v9.py')}
exec(compile((HERE / 'test_complete_obligations_v9.py').read_bytes(), ns['__file__'], 'exec'), ns)
results = [{'expected_result': row['expected_result'], 'closure': ns['run'](ns['NEW'], row)} for row in ns['DATA']['records']]
(HERE / 'complete-obligation-replay-result-v9.json').write_text(json.dumps({
    'classification': 'PASS_COMPLETE_PINNED_GOAL_CSV_SEAMS_ONLY', 'records': results,
    'record_audit_executed': False, 'scientific_reexecution': False, 'full_source_runtime_cold_closure': False}, indent=2, sort_keys=True) + '\n')
old_tree = ast.parse((BASE / 'initialized_cold_obligations_v3.py').read_bytes())
new_tree = ast.parse((HERE / 'initialized_cold_obligations_v4.py').read_bytes())
functions = lambda tree: {node.name: ast.dump(node, include_attributes=False) for node in tree.body if isinstance(node, ast.FunctionDef)}
before, after = functions(old_tree), functions(new_tree)
changed = [name for name in before if before[name] != after[name]]
assert changed == ['current_csv_active_v2', 'current_csv']
assert set(after) - set(before) == {'initialized_reads_v4', 'init_termination_v4'}
assert reader.replace('initialized_cold_obligations_v4.py', 'initialized_cold_obligations_v3.py').replace(
    helper['sha256'], old_helper['sha256']).replace('initialized_cold_audit_v9.py', 'initialized_cold_audit_v8.py') == old_reader
packet = {'date': '2026-10-16 ET', 'status': 'FROZEN_AWAITING_INDEPENDENT_REVIEW_AND_ROOT_ADMISSION',
    'files': {path.name: pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name != 'initialized-cold-v9-source-packet.json'},
    'predecessor_reader': pin(BASE / 'initialized_cold_audit_v8.py'), 'predecessor_obligations': old_helper,
    'actual_refusal': pin(BASE / 'initialized-cold-v8-actual-refusal-receipt-20261016.json'),
    'complete_pinned_metadata': pin(BASE / 'complete-obligation-input-metadata-20261016.json'),
    'primary_reporter_metadata': [pin(BASE / name) for name in ('implicit-terminates-primary-search-20261016.json',
        'implicit-terminates-primary-context-20261016.json', 'implicit-terminates-cfgannot-primary-20261016.json')],
    'changed_obligation_functions': changed, 'new_obligation_functions': sorted(set(after) - set(before)),
    'reader_only_helper_filename_digest_and_doc_invocation_changed': True,
    'pure_controls': {'tests': 7, 'exit_code': 0, 'failures': 0, 'errors': 0, 'skips': 0,
        'complete_actual_seams': [711, 1107], 'no_child_audit_guard': True},
    'control_files': len(rows), 'control_bytes': command['control_total_bytes'],
    'scientific_criteria': '711 ordinary23Valid plus10healthy smokes; 1107 ordinary22Valid/one normal ensures timeout plus10healthy smokes. Both source-read initialization goals are direct Valid. Implicit init termination remains Unknown/no goal/no active premise, never a new Extern. Existing partial normal-return and source/query/runtime gates unchanged.',
    'actual_or_scientific_execution': False}
path = HERE / 'initialized-cold-v9-source-packet.json'
path.write_text(json.dumps(packet, indent=2, sort_keys=True) + '\n')
print(json.dumps({'packet': pin(path), 'reader': reader_pin, 'helper': helper,
    'policy': policy_pin, 'command': pin(command_path), 'controls': len(rows), 'control_bytes': command['control_total_bytes']}, indent=2))
