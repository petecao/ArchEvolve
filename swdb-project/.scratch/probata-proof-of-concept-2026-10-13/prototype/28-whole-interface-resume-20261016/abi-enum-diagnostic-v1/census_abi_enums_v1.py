"""2026-10-16 ET. Offline exact-small-artifact census; never ABI admission.

No SSH, child, compiler, source program or installed project import. The fixed
probe adapter preserves original serialized coordinates while reading only the
two exact verified local copies. It is disclosed metadata replay, not a claim
that those original remote filesystem paths were opened by this local reader.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import types

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
TRANSFER = WHOLE / 'abi-small-artifact-transfer-v1'
REPLAY = WHOLE / 'abi-retained-replay-v1'
STABLE = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
LIMIT = 262144
OUTPUT_LIMIT = 1048576
READS = {}


def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('offline ABI census forbids child/native/network')
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise RuntimeError('offline ABI census forbids installed project import')


sys.addaudithook(no_child)


def need(value, message):
    if not value: raise ValueError(message)


def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def fingerprint(value): return {name: getattr(value, name) for name in STABLE}


def strict(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate diagnostic metadata key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite diagnostic metadata')))


def read_pin(row, limit=LIMIT):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'} and type(row['bytes']) is int
        and 0 <= row['bytes'] <= limit, 'closed bounded diagnostic input pin required')
    path = Path(row['path']); before = path.lstat()
    need(path.is_absolute() and path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode)
        and before.st_size == row['bytes'], 'canonical regular selected extent required')
    with path.open('rb') as handle: raw = handle.read(row['bytes'] + 1)
    after = path.lstat()
    need(fingerprint(before) == fingerprint(after) and len(raw) == row['bytes'] and sha(raw) == row['sha256'],
        'diagnostic physical input changed')
    prior = READS.get(str(path))
    need(prior is None or prior['pin'] == row, 'conflicting diagnostic input identity')
    READS[str(path)] = {'pin': row, 'before': fingerprint(before), 'after': fingerprint(after)}
    return raw


def local_control(name):
    policy_raw = (REPLAY / 'controls/policy.json').read_bytes()
    need(sha(policy_raw) == '3f20967eaeaa7a3469ef4a4b249c2ce2161ae0ec9a9eda41be80c6d950919ad4', 'exact admitted replay policy required')
    row = strict(policy_raw)['controls'][name]
    return {**row, 'path': str(REPLAY / 'controls' / Path(row['path']).name)}


def source_module(name, row, **injected):
    raw = read_pin(row)
    tree = ast.parse(raw)
    # Only the helper's two fixed project import statements are replaced by
    # explicitly pinned in-memory modules. All function bodies remain exact.
    removed = [node for node in tree.body if isinstance(node, ast.ImportFrom) and (node.module or '').startswith('swdb')]
    need(not removed or name == 'helper' and len(removed) == 2 and all(node.module == 'swdb._dx100_whole' for node in removed),
        'only fixed helper primitive imports may be substituted')
    tree.body = [node for node in tree.body if node not in removed]
    module = types.ModuleType('offline_exact_' + name)
    module.__file__ = row['path']; module.__dict__.update(injected)
    exec(compile(tree, row['path'], 'exec'), module.__dict__)
    return module


def primitives():
    normalizer = source_module('normalizer', local_control('normalizer'))
    tokens = source_module('tokens', local_control('tokens'))
    helper = source_module('helper', local_control('helper'), normalizer=normalizer, tokens=tokens)
    legacy = source_module('legacy', local_control('legacy'))
    binder = source_module('binder', local_control('binder'))
    return helper, legacy, binder


def syntax(probe, expected):
    need(type(probe) is bytes and len(probe) == 1588 and sha(probe) == 'c0f4f37ba62992b3de117f6117b134ad0ba663484c172ffa98081952f769bf34',
        'exact original ABI enum probe syntax required')
    result = []; offset = 0
    for line_no, line in enumerate(probe.decode('ascii').splitlines(keepends=True), 1):
        match = re.fullmatch(r'    dws_probe_([a-zA-Z0-9_]+) = (.*?)(?:,)?\n', line)
        if match:
            name, expression = match.groups()
            if re.fullmatch(r'[A-Z_]+', expression): kind = 'macro-expanded-integer-expression'
            elif re.fullmatch(r'sizeof\((?:int|void \*|dws_probe_[a-zA-Z0-9_]+)\)(?: \* CHAR_BIT)?', expression): kind = 'sizeof-expression'
            elif re.fullmatch(r'alignof\(dws_probe_[a-zA-Z0-9_]+\)', expression): kind = 'alignof-expression'
            elif expression == '__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__': kind = 'macro-integer-comparison'
            else: kind = 'unrecognized-source-expression'
            result.append({'name': 'dws_probe_' + name, 'expression': expression, 'syntax_class': kind,
                'line': line_no, 'line_byte_range': [offset, offset + len(line)]})
        offset += len(line)
    need([row['name'] for row in result] == ['dws_probe_' + name for name in expected], 'complete ordered original probe enums required')
    return {row['name']: row for row in result}


def pointer(parts): return '/' + '/'.join(str(part).replace('~', '~0').replace('/', '~1') for part in parts)


def candidate_rows(root):
    result = []; objects = arrays = scalars = 0
    def visit(value, path):
        nonlocal objects, arrays, scalars
        if isinstance(value, dict):
            objects += 1
            if 'kind' in value or 'value' in value:
                present = 'value' in value
                selected = value.get('value')
                need(not present or type(selected) in (str, int, float, bool, type(None)), 'non-scalar value candidate requires a separate diagnostic')
                result.append({'path': pointer(path), 'kind': value.get('kind'), 'object_keys': list(value),
                    'node_type': copy.deepcopy(value.get('type')), 'value_present': present,
                    'value_type': type(selected).__name__ if present else None, 'value': selected if present else None,
                    'direct_child_kinds': [item.get('kind') if isinstance(item, dict) else type(item).__name__ for item in value.get('inner', [])],
                    'source_location': {'loc': copy.deepcopy(value.get('loc')), 'range': copy.deepcopy(value.get('range'))},
                    'complete_derived_subtree_canonical_sha256': sha(canonical(value))})
            for key, item in value.items(): visit(item, [*path, key])
        elif isinstance(value, list):
            arrays += 1
            for index, item in enumerate(value): visit(item, [*path, index])
        else: scalars += 1
    visit(root, [])
    return {'nodes': result, 'object_count': objects, 'array_count': arrays, 'scalar_count': scalars,
        'all_kind_or_value_objects_reported': True}


def legacy_gate(legacy):
    text = read_pin(local_control('legacy')).decode()
    function = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'observed_abi')
    call = next(node for node in ast.walk(function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == 'need' and len(node.args) == 2 and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == 'one observed integer ConstantExpr required')
    expression = compile(ast.Expression(call.args[0]), '<unchanged-exact-observed-ABI-constant-gate>', 'eval')
    return lambda root: bool(eval(expression, {'constants': [node for node in root.get('inner', []) if node.get('kind') == 'ConstantExpr'], 're': re}))


def analyze(raw, probe, original_probe, helper, legacy, binder):
    original_refusal = None
    try: legacy.parse_json_roots(raw)
    except legacy.Refused as error:
        original_refusal = {'type': type(error).__name__, 'message': str(error),
            'cause': None if error.__cause__ is None else {'type': type(error.__cause__).__name__, 'message': str(error.__cause__)}}
    need(original_refusal is not None and original_refusal['cause'] == {'type': 'Refused', 'message': 'duplicate compiler JSON key'},
        'unchanged original strict duplicate refusal required')
    derived, transport = helper.normalize_abi(raw)
    roots = legacy.parse_json_roots(derived)
    original_spans = helper.roots(raw, strict=False)
    expected_names = ['dws_probe_' + key for key in (*legacy.TYPE_KEYS, *legacy.ABI_INTS)]
    need(len(roots) == len(original_spans) == 29 and [row.get('name') for row in roots] == expected_names,
        'all29 original ordered ABI roots required')
    source = syntax(probe, legacy.ABI_INTS)
    gate = legacy_gate(legacy)
    headers = []; enums = []
    for index, (root, span) in enumerate(zip(roots, original_spans)):
        headers.append({'index': index, 'name': root.get('name'), 'kind': root.get('kind'),
            'type': copy.deepcopy(root.get('type')), 'source_location': copy.deepcopy(root.get('loc')),
            'exact_original_root_bytes': len(span), 'exact_original_root_sha256': sha(span),
            'complete_derived_root_canonical_sha256': sha(canonical(root))})
        if root['name'] in source:
            enums.append({'index': index, 'name': root['name'], 'kind': root.get('kind'), 'source': source[root['name']],
                'complete_original_root_sha256': sha(span), 'complete_derived_root_canonical_sha256': sha(canonical(root)),
                'unchanged_legacy_direct_gate_accepts': gate(root), 'candidate_census': candidate_rows(root)})
    # Diagnostic-only exact probe read adapter. Original coordinates remain the
    # original captured string. Other filesystem paths cannot be consumed.
    base_path = Path
    class BoundProbe:
        def __init__(self, value):
            need(str(value) == original_probe, 'only the exact original probe coordinate may be rebound')
        def __str__(self): return original_probe
        def resolve(self): return self
        def read_bytes(self): return probe
    old_path = legacy.Path
    try:
        legacy.Path = BoundProbe
        try:
            observed = legacy.observed_abi(derived, probe_path=original_probe, api=binder.__dict__)
            reader = {'accepted': True, 'observation': observed}
        except legacy.Refused as error:
            reader = {'accepted': False, 'error': {'type': type(error).__name__, 'message': str(error)}}
    finally: legacy.Path = old_path
    return {'family': transport['selected_family'], 'original_strict_refusal': original_refusal,
        'original_ABI': {'bytes': len(raw), 'sha256': sha(raw)}, 'derived_ABI': {'bytes': len(derived), 'sha256': sha(derived)},
        'transport': transport, 'root_headers': headers, 'enum_census': enums, 'enum_count': len(enums),
        'unchanged_reader': reader, 'probe_coordinate_adapter': {'original': original_probe,
            'read_source': 'Exact checked local transfer bytes; no remote path was opened locally.',
            'only_Path_binding_changes': True},
        'no_AST_payload_or_selected_integer_interpretation_emitted': True, 'ABI_source_or_public_admission': False}


def main():
    receipt = {'path': str(TRANSFER / 'verified-transfer.json'), 'bytes': 9292,
        'sha256': 'fb4a5d46a64b8e439da569f1264cf70c752d1625f866668ff11b2146fc30b276'}
    transferred = strict(read_pin(receipt))
    policy = strict((REPLAY / 'controls/policy.json').read_bytes())
    helper, legacy, binder = primitives()
    results = []
    for artifact in policy['artifacts']:
        selected = {role: next(row for row in transferred['files'] if row['remote'] == artifact[role]) for role in ('ABI', 'probe')}
        need(all(row['before'] == row['after'] and row['local']['sha256'] == row['remote']['sha256']
            and row['local']['bytes'] == row['remote']['bytes'] for row in selected.values()), 'exact unchanged remote-to-local transfer required')
        results.append(analyze(read_pin(selected['ABI']['local']), read_pin(selected['probe']['local']),
            artifact['probe']['path'], helper, legacy, binder))
    for row in list(READS.values()): read_pin(row['pin'])
    result = {'schema': 'offline-complete-two-ABI-enum-census-1', 'date': '2026-10-16 ET',
        'transfer_receipt': receipt, 'families': results, 'physical_local_readset': list(READS.values()),
        'original_runtime_compiler_ABI_theorem_claimed': False, 'generic_decoder_or_reader_changed': False,
        'remote_child_compiler_native_verifier_project_import_or_source_program_executed': False,
        'local_offline_parser_TCB': 'Selected local Python stdlib plus exact reviewed token/role/legacy source; no original-runtime equivalence claim.',
        'source_IDs_joined_or_actual_source_body_or_public_admission': False}
    raw = canonical(result) + b'\n'; need(len(raw) <= OUTPUT_LIMIT, 'complete compact metadata census output cap')
    destination = HERE / 'actual-complete-enum-census-v1.json'
    with destination.open('xb') as handle: handle.write(raw)
    print(json.dumps({'path': str(destination), 'bytes': len(raw), 'sha256': sha(raw),
        'families': [{'family': row['family'], 'roots': len(row['root_headers']), 'enums': row['enum_count'],
            'failed_old_gate': [item['name'] for item in row['enum_census'] if not item['unchanged_legacy_direct_gate_accepts']],
            'reader': row['unchanged_reader']} for row in results]}, sort_keys=True))


if __name__ == '__main__': main()
