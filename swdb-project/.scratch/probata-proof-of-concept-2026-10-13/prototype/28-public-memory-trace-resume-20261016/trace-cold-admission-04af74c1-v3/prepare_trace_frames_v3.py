"""2026-10-16 ET. Frame-only trace successor; no audit or remote action."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
V1 = TRACE / 'trace-cold-audit-v1'
V2 = TRACE / 'trace-cold-admission-04af74c1-v2'
INIT = TRACE.parent / '28-initialized-u32-resume-20261016'
INITIALIZED = INIT / 'cold-v6-admission-04af74c1/initialized_cold_audit_v6.py'
OLD_COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v2'
COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v3'
CONTROL = COLD + '/control'


def sha(data): return hashlib.sha256(data).hexdigest()


def pin(path, remote=None):
    data = path.read_bytes()
    return {'path': remote or str(path.resolve()), 'bytes': len(data), 'sha256': sha(data)}


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def rebind(value, reverse=False):
    if isinstance(value, dict): return {key: rebind(item, reverse) for key, item in value.items()}
    if isinstance(value, list): return [rebind(item, reverse) for item in value]
    if isinstance(value, str): return value.replace(COLD, OLD_COLD) if reverse else value.replace(OLD_COLD, COLD)
    return value


def build():
    data = (V1 / 'trace_cold_audit_v1.py').read_bytes()
    assert sha(data) == '3cefa1c4eb7c05371afcdaf8b43d6f46927dfe80aed0be90e652bac0cf0157ee'
    origin = INITIALIZED.read_bytes()
    assert sha(origin) == '02744c321c9bc60535f374d0b47b4d634b54e02c9786a31351c77859c3d8b598'
    before = data.decode(); origin = origin.decode()
    helper_node = next(node for node in ast.parse(origin).body if isinstance(node, ast.FunctionDef) and node.name == 'refusal_frame_report_v6')
    helper = ast.get_source_segment(origin, helper_node)
    old_ast = ast.parse(before)
    old_formatter = ast.get_source_segment(before, old_ast.body[-1].body[-1].handlers[0].body[0])
    assert old_formatter.startswith('print(json.dumps(') and 'str(error)' in old_formatter
    after = before.replace(old_formatter, 'print(json.dumps(refusal_frame_report_v6(error), sort_keys=True))', 1)
    after = after.replace("if __name__ == '__main__':", helper + '\n\n\n' + "if __name__ == '__main__':", 1)
    new_ast = ast.parse(after)
    new_ast.body = [node for node in new_ast.body if not isinstance(node, ast.FunctionDef) or node.name != 'refusal_frame_report_v6']
    new_ast.body[-1].body[-1].handlers[0].body[0] = old_ast.body[-1].body[-1].handlers[0].body[0]
    assert ast.dump(old_ast, include_attributes=False) == ast.dump(new_ast, include_attributes=False)
    reader = HERE / 'trace_cold_audit_v3.py'; reader.write_text(after)
    policy_bytes = (V2 / 'trace-cold-policy-04af74c1-v2.json').read_bytes()
    assert sha(policy_bytes) == 'ee3b56886af7a9c257309b1acd6cd3077b1308652a39c8a794a6f32644ece8b7'
    old_policy = json.loads(policy_bytes); policy = rebind(old_policy)
    policy['reader_sha256'] = sha(reader.read_bytes())
    policy['provenance']['frame_only_diagnostics'] = {'origin_reader': pin(INITIALIZED), 'helper_sha256': sha(helper.encode()),
        'base_reader': pin(V1 / 'trace_cold_audit_v1.py'), 'preserved_staged_v2': pin(V2 / 'staging-receipt-20261016.json'),
        'scope': 'Frame formatter only; every prior audit function/check byte unchanged; no execution or final admission'}
    inverse = rebind(policy, reverse=True); inverse['reader_sha256'] = old_policy['reader_sha256']
    inverse['provenance'].pop('frame_only_diagnostics'); assert inverse == old_policy
    policy_name = 'trace-cold-policy-04af74c1-v3.json'; dump(policy_name, policy)
    command = rebind(json.loads((V2 / 'trace-cold-command-04af74c1-v2.json').read_bytes()))
    controls = command['control_files']
    controls.pop('trace_cold_audit_v1.py'); controls.pop('trace-cold-policy-04af74c1-v2.json'); controls.pop('trace-cold-control-manifest-v2.json')
    for name, path, purpose in [(reader.name, reader, 'reviewed science unchanged; frame-only error successor pending review'),
            (policy_name, HERE / policy_name, 'fresh frame-only trace admission request')]:
        controls[name] = {**pin(path, CONTROL + '/' + name), 'source': str(path), 'purpose': purpose}
    manifest_name = 'trace-cold-control-manifest-v3.json'
    dump(manifest_name, {'date': '2026-10-16 ET', 'fresh_raw': COLD, 'source_commit': policy['source_commit'],
        'payload_files': controls, 'payload_file_count': len(controls), 'payload_bytes': sum(row['bytes'] for row in controls.values()),
        'manifest_self_listed': False, 'reader_executed': False, 'expected_control_basenames': sorted([*controls, manifest_name])})
    controls[manifest_name] = {**pin(HERE / manifest_name, CONTROL + '/' + manifest_name), 'source': str(HERE / manifest_name),
        'purpose': 'complete control membership and pins excluding its own recursive hash'}
    command['command'][-3] = CONTROL + '/' + reader.name
    command['command'][-2] = CONTROL + '/' + policy_name
    command['command'][-1] = sha((HERE / policy_name).read_bytes())
    command['control_file_count'] = len(controls); command['control_total_bytes'] = sum(row['bytes'] for row in controls.values())
    assert command['control_file_count'] == 17 and command['control_total_bytes'] < 1048576
    command['status'] = 'PREPARED_FRAME_ONLY_SUCCESSOR_AWAITING_INDEPENDENT_REVIEW_STAGING_AND_ROOT_ADMISSION'
    dump('trace-cold-command-04af74c1-v3.json', command)
    dump('trace-cold-frames-inverse-v3.json', {'date': '2026-10-16 ET', 'base_reader': pin(V1 / 'trace_cold_audit_v1.py'),
        'successor_reader': pin(reader), 'helper_origin': pin(INITIALIZED), 'helper_sha256': sha(helper.encode()),
        'allowed_source_delta': ['exact V6 frame formatter copy', 'top-level refusal formatter call'], 'complete_ast_inverse': True,
        'all_prior_audit_functions_byte_unchanged': True, 'complete_policy_inverse': True,
        'staged_v2_preserved_unexecuted': True, 'actual_reader_executed': False})


if __name__ == '__main__': build()
