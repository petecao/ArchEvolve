"""2026-10-16 ET. Exact trace flags successor preparation; no audit/remote action."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
PROJECT = TRACE.parents[3]
V3 = TRACE / 'trace-cold-admission-04af74c1-v3'
OLD_COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v3'
COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v4'
CONTROL = COLD + '/control'
OLD_ASSIGNMENT = "flags = ['-DSWDB_CBMC', '--unwind', '1', *identities['frozen']]"
NEW_ASSIGNMENT = "flags = model_unwind_flags_v4(settings, identities['frozen'], entry['constants'], (fixture / 'library/proof_semantics/synthetic-memory-trace/model.h').read_text(), project)"
METADATA_SHA = '157305bff9221f169ff2a103f6bbfe3b06e30900b8babcda746ab29d11f0abb3'
REFUSAL_SHA = '98c7e00af83f4383611e78614183d440c4434f1ab173e24fd67b44702ecd9ce4'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def pin(path, remote=None):
    raw = path.read_bytes()
    return {'path': remote or str(path.resolve()), 'bytes': len(raw), 'sha256': sha(raw)}


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def rebind(value, reverse=False):
    if isinstance(value, dict): return {key: rebind(item, reverse) for key, item in value.items()}
    if isinstance(value, list): return [rebind(item, reverse) for item in value]
    if isinstance(value, str): return value.replace(COLD, OLD_COLD) if reverse else value.replace(OLD_COLD, COLD)
    return value


def helper_text(loop_ids):
    # Fixed helpers consume selected source and metadata. No tool output is
    # regenerated: the opaque IDs/order remain the original CBMC selector TCB.
    literal = '\n'.join('    ' + repr(loop) + ',' for loop in loop_ids)
    return 'TRACE_LOOP_IDS_V4 = (\n' + literal + '\n)\n\n\n' + '''def validated_model_flags_v4(settings, frozen, functions, unwind, selected):
    assert type(unwind) is int and unwind == 5
    assert type(functions) in (list, tuple) and all(type(name) is str for name in functions)
    assert type(selected) is list and selected == list(TRACE_LOOP_IDS_V4)
    assert len(selected) == len(set(selected)) == 35
    assert all(loop.rsplit('.', 1)[0] in functions for loop in selected)
    assert tuple(frozen) == ('--unwinding-assertions', '--pointer-overflow-check')
    flags = ['-DSWDB_CBMC', '--unwind', '1', *frozen,
             '--unwindset', ','.join(f'{loop}:{unwind}' for loop in selected)]
    assert type(settings['flags']) is list and settings['flags'] == flags
    assert type(settings['unwind']) is int and settings['unwind'] == 1
    assert type(settings['array_length']) is int and settings['array_length'] == 0
    return flags


def model_unwind_flags_v4(settings, frozen, constants, model_text, project):
    # Exact retained producer source, not an imported project module. The
    # assignments and selector return below are the only executed AST leaves.
    assert H(model_text.encode()) == '2fe44f7fea203d1f7914db6077b999d03f64a2e43472bd2884eb8e534e775be8'
    expected = {'swdb/cbmc_adapter.py': '2ef59469412c287b174f085e2c08c8a969435ccf1bc129fe34ea89bbb78cac4a',
                'swdb/proof_semantics.py': '9c3fd649fecd2162a7d8f0b416ea1e5543991bf40cc8f8a0eb115a0e24b66436'}
    texts = {}
    for relative, digest in expected.items():
        raw = (project / relative).read_bytes()
        assert H(raw) == digest
        texts[relative] = raw.decode('utf-8')
    tree = ast.parse(texts['swdb/proof_semantics.py'])
    producer = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'model_for')
    assignments = [node for node in producer.body if isinstance(node, ast.Assign) and len(node.targets) == 1
                   and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'functions', 'unwind'}]
    assert len(assignments) == 2 and [node.targets[0].id for node in assignments] == ['functions', 'unwind']
    namespace = {'re': re, 'model': model_text, 'constants': constants}
    exec(compile(ast.Module(body=assignments, type_ignores=[]), '<exact-source-model-functions-and-bound>', 'exec'), namespace)
    tree = ast.parse(texts['swdb/cbmc_adapter.py'])
    adapter = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'CbmcAdapter')
    selector = next(node for node in adapter.body if isinstance(node, ast.FunctionDef) and node.name == '_model_loops')
    assert len(selector.body) == 4 and isinstance(selector.body[-1], ast.Return)
    selected = eval(compile(ast.Expression(body=selector.body[-1].value), '<exact-source-model-loop-selector-only>', 'eval'),
                    {'loops': list(TRACE_LOOP_IDS_V4), 'model': types.SimpleNamespace(functions=namespace['functions'])})
    # There is no retained --show-loops stdout. This checks the exact original
    # selector against the closed observed suffix; it does not rediscover IDs.
    return validated_model_flags_v4(settings, frozen, namespace['functions'], namespace['unwind'], selected)
'''


def build():
    before = (V3 / 'trace_cold_audit_v3.py').read_bytes()
    assert sha(before) == 'a323298395677ed638d1e92a53fd0d386f54cab5eb815c266d8cdd1d3aff63aa'
    metadata_path = V3 / 'retained-trace-flags-metadata-20261016.json'
    refusal = V3 / 'trace-cold-v3-actual-refusal-receipt-20261016.json'
    assert pin(metadata_path)['sha256'] == METADATA_SHA and pin(refusal)['sha256'] == REFUSAL_SHA
    metadata = json.loads(metadata_path.read_bytes())
    assert len(metadata['cases']) == 25 and len(metadata['groups']) == 1
    group = next(iter(metadata['groups'].values()))
    projection = group['projection']
    prefix = ['-DSWDB_CBMC', '--unwind', '1', '--unwinding-assertions', '--pointer-overflow-check', '--unwindset']
    assert projection['actual_settings_flags'][:-1] == prefix
    items = projection['actual_settings_flags'][-1].split(',')
    assert len(items) == 35 and all(item.endswith(':5') for item in items)
    loop_ids = [item[:-2] for item in items]
    assert len(set(loop_ids)) == 35
    old = before.decode(); helpers = helper_text(loop_ids)
    assert old.count(OLD_ASSIGNMENT) == 1 and old.count('def audit_record(') == 1
    after = old.replace(OLD_ASSIGNMENT, NEW_ASSIGNMENT, 1).replace('def audit_record(', helpers + '\n\n\ndef audit_record(', 1)
    assert after.replace(helpers + '\n\n\n', '', 1).replace(NEW_ASSIGNMENT, OLD_ASSIGNMENT, 1) == old
    reader = HERE / 'trace_cold_audit_v4.py'; reader.write_text(after)
    old_policy_raw = (V3 / 'trace-cold-policy-04af74c1-v3.json').read_bytes()
    assert sha(old_policy_raw) == 'e2fe50f515a9eb287d5a559909671f01451dec932c4ec5d6256d9de472c86531'
    old_policy = json.loads(old_policy_raw); policy = rebind(old_policy)
    policy['reader_sha256'] = pin(reader)['sha256']
    policy['provenance']['model_unwind_projection_v4'] = {'base_reader': pin(V3 / 'trace_cold_audit_v3.py'),
        'retained_metadata': pin(metadata_path, CONTROL + '/' + metadata_path.name),
        'preserved_v3_refusal': pin(refusal, CONTROL + '/' + refusal.name), 'source_commit': policy['source_commit'],
        'producer_sources': {name: pin(PROJECT / name) for name in ('swdb/cbmc_adapter.py', 'swdb/proof_semantics.py')},
        'model_source': pin(TRACE / 'model.h'), 'loop_ids': loop_ids, 'model_unwind': 5,
        'scope': 'Exact retained suffix/order plus source-derived function membership and bound; all other audit gates unchanged',
        'TCB': 'Original pinned producer and CBMC --show-loops discovery/selection; separate show-loops output was not retained and is not reconstructed'}
    inverse = rebind(policy, reverse=True); inverse['reader_sha256'] = old_policy['reader_sha256']
    inverse['provenance'].pop('model_unwind_projection_v4'); assert inverse == old_policy
    policy_name = 'trace-cold-policy-04af74c1-v4.json'; dump(policy_name, policy)
    command = rebind(json.loads((V3 / 'trace-cold-command-04af74c1-v3.json').read_bytes()))
    controls = command['control_files']
    for name in ('trace_cold_audit_v3.py', 'trace-cold-policy-04af74c1-v3.json', 'trace-cold-control-manifest-v3.json'):
        controls.pop(name)
    for path, purpose in [(reader, 'exact retained model-loop flags projection successor pending review'),
            (HERE / policy_name, 'fresh trace cold V4 admission request'),
            (metadata_path, 'exact passive retained flags metadata, not scientific payload'),
            (refusal, 'preserved actual cold V3 refusal provenance')]:
        controls[path.name] = {**pin(path, CONTROL + '/' + path.name), 'source': str(path), 'purpose': purpose}
    manifest_name = 'trace-cold-control-manifest-v4.json'
    dump(manifest_name, {'date': '2026-10-16 ET', 'fresh_raw': COLD, 'source_commit': policy['source_commit'],
        'payload_files': controls, 'payload_file_count': len(controls), 'payload_bytes': sum(row['bytes'] for row in controls.values()),
        'manifest_self_listed': False, 'reader_executed': False, 'expected_control_basenames': sorted([*controls, manifest_name])})
    controls[manifest_name] = {**pin(HERE / manifest_name, CONTROL + '/' + manifest_name), 'source': str(HERE / manifest_name),
        'purpose': 'complete control membership and pins excluding its own recursive hash'}
    command['command'][-3] = CONTROL + '/' + reader.name
    command['command'][-2] = CONTROL + '/' + policy_name
    command['command'][-1] = pin(HERE / policy_name)['sha256']
    command['control_file_count'] = len(controls); command['control_total_bytes'] = sum(row['bytes'] for row in controls.values())
    assert command['control_file_count'] == 19 and command['control_total_bytes'] < 1048576
    command['status'] = 'PREPARED_EXACT_MODEL_UNWIND_PROJECTION_SUCCESSOR_AWAITING_INDEPENDENT_REVIEW_AND_ROOT_ADMISSION'
    dump('trace-cold-command-04af74c1-v4.json', command)
    dump('trace-cold-projection-inverse-v4.json', {'date': '2026-10-16 ET', 'base_reader': pin(V3 / 'trace_cold_audit_v3.py'),
        'successor_reader': pin(reader), 'allowed_source_delta': ['two exact source/retained flags helpers and closed 35-ID constant',
            'audit_record flags assignment only'], 'source_text_inverse': True, 'policy_inverse': True,
        'all_other_audit_functions_byte_unchanged': True, 'preserved_actual_v3_refusal': pin(refusal),
        'actual_reader_executed': False, 'scientific_execution': False})


if __name__ == '__main__': build()
