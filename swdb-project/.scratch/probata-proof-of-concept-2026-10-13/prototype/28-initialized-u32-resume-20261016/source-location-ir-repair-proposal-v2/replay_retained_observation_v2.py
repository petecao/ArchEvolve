"""2026-10-16 ET. Read-only retained observer replay; never a new proof.

Run on mbit10 with isolated Python. stdin is the exact reviewed proposed source
as a JSON string. Full AST/preprocessed/LLVM inputs remain on the remote host.
No project imports, subprocesses, native tools, network or filesystem writes.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys


RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-ast-diagnostic-2baf722f-v1')
PROJECT = Path('/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project')
PROPOSAL_SHA = '01c043e544e50c30fc3d92b6be5a8b097f4dfef0606f53c29068a2ba008ac145'
RESULT_SHA = '6d5346b565fcdd3c6d9879283ee6effc30ee825b2cceddb1d587729f9db73a61'
SOURCE_PINS = {
    'swdb/dx100_initialized_register_source.py': 'c023a4a6298fab7a34f4213f888b6c0fb4fe5c405e5a53741942e3e2accb81cb',
    'swdb/dx100_initialized_register_model.py': 'a568c08f6e8d928ecb46212b7120b29740d719c65ae7ae818b540bcf6790961f',
    'swdb/dx100_size_source.py': 'fe070713b91257d73a77112a7114c3ec049d2dc3ca8dbe0c1dfa6404c35a70f3',
}
FUNCTIONS = {
    '_hash', '_function', '_flow', '_counter_bound_flow', '_operations', 'observation', '_checked_sources',
    '_children', '_walk', '_parse_dump', '_slice', '_clean', '_body', '_strip_expr',
    '_expression', '_callee', '_string', '_assert_function_diagnostic',
    '_assert_source_location_diagnostics', '_assertion', '_bodies',
}
FAMILIES = ('init_MAA', 'get_new_reg', 'set_reg', 'get_reg', 'trust_fixture')


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'socket.')) or event in {
            'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen', 'os.remove',
            'os.rename', 'os.rmdir', 'os.mkdir', 'os.link', 'os.symlink', 'os.truncate'}:
        raise RuntimeError('read-only retained replay refuses ' + event)
    if event == 'open':
        _path, mode, flags = arguments
        if mode is not None and any(character in mode for character in 'wax+') or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError('read-only retained replay refuses file mutation')


sys.addaudithook(deny)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular(path, digest=None):
    if path.is_symlink() or path.resolve() != path or not path.is_file():
        raise ValueError('canonical regular retained input required: ' + str(path))
    before = path.stat()
    if before.st_size > 64 * 2**20:
        raise ValueError('bounded individual retained input cap exceeded')
    data = path.read_bytes()
    after = path.stat()
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    if any(getattr(before, field) != getattr(after, field) for field in fields) or len(data) != before.st_size:
        raise ValueError('retained input changed during read: ' + str(path))
    if digest is not None and sha(data) != digest:
        raise ValueError('retained input digest differs: ' + str(path))
    return data


def literal(source, name):
    nodes = [node for node in ast.parse(source).body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(nodes) != 1:
        raise ValueError('one exact source literal required: ' + name)
    return ast.literal_eval(nodes[0].value)


def pinned_path_type(source_rows):
    """Diagnostic-only read adapter: bind _bodies' unchanged header read."""
    pins = {row['path']: row for row in source_rows}
    if len(pins) != 7 or len(pins) != len(source_rows):
        raise ValueError('exact seven physical source read pins required')

    class PinnedPath(type(Path())):
        def read_text(self, encoding=None, errors=None):
            key = str(self)
            if key not in pins:
                raise ValueError('unlisted physical observer source read')
            wanted = pins[key]
            data = regular(Path(key), wanted['sha256'])
            if len(data) != wanted['bytes']:
                raise ValueError('physical observer source read extent differs')
            return data.decode(encoding or 'utf-8', errors or 'strict').replace('\r\n', '\n').replace('\r', '\n')

    return PinnedPath


def namespace(source, caller, source_pins, source_rows):
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS
             or isinstance(node, ast.ClassDef) and node.name == 'Refused'
             or isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in {'_FENCE', '_ABORT'} for target in node.targets)]
    expected = FUNCTIONS - ({'_assert_source_location_diagnostics', '_counter_bound_flow'} if sha(source) == SOURCE_PINS['swdb/dx100_initialized_register_source.py'] else set())
    if {node.name for node in nodes if isinstance(node, ast.FunctionDef)} != expected:
        raise ValueError('exact closed passive observer definition set differs')
    context = {'hashlib': hashlib, 'json': json, 're': re, 'Path': pinned_path_type(source_rows),
               'CALLER': caller, 'SOURCE_PINS': source_pins}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<pinned-passive-observer>', 'exec'), context)
    return context


def retained_snapshot(root, expected):
    if root.is_symlink() or root.resolve() != root or not root.is_dir():
        raise ValueError('canonical retained observation directory required')
    if {path.name for path in root.iterdir()} != set(expected):
        raise ValueError('exact complete retained observation membership differs')
    result = {}; payloads = {}
    for name, wanted in expected.items():
        data = regular(root / name, wanted['sha256'])
        if len(data) != wanted['bytes']:
            raise ValueError('retained input extent differs')
        result[name] = {'bytes': len(data), 'sha256': sha(data)}
        payloads[name] = data
    if sum(row['bytes'] for row in result.values()) > 64 * 2**20:
        raise ValueError('bounded retained observation cap exceeded')
    return result, payloads


def main(proposed):
    if not isinstance(proposed, str) or sha(proposed.encode()) != PROPOSAL_SHA:
        raise ValueError('exact reviewed proposed observer bytes required')
    result_path = RAW / 'initialized-profile/diagnostic-result.json'
    diagnostic = json.loads(regular(result_path, RESULT_SHA))
    if diagnostic['status'] != 'DIAGNOSTIC_REPRODUCED_SOURCE_REFUSAL' or diagnostic['capture_completion']['accepted'] is not True:
        raise ValueError('complete original diagnostic capture required')
    observed = RAW / 'initialized-profile/retained-observation'
    expected = {row['name']: row for row in diagnostic['retained_files']}
    if len(expected) != 32 or len(expected) != len(diagnostic['retained_files']):
        raise ValueError('complete unique original artifact census required')
    before, payloads = retained_snapshot(observed, expected)
    project_bytes = {name: regular(PROJECT / name, digest) for name, digest in SOURCE_PINS.items()}
    project_before = {name: sha(data) for name, data in project_bytes.items()}
    caller = literal(project_bytes['swdb/dx100_initialized_register_model.py'], 'CALLER')
    source_pins = literal(project_bytes['swdb/dx100_size_source.py'], 'SOURCE_PINS')
    sources = json.loads(payloads['observation-source-pins.json'])
    old = namespace(project_bytes['swdb/dx100_initialized_register_source.py'], caller, source_pins, sources)
    new = namespace(proposed.encode(), caller, source_pins, sources)
    tokens = payloads['preprocessed-original.ii'].decode()
    dumps = {name: payloads['ast-' + name + '.json'].decode() for name in FAMILIES}
    module = payloads['compiler-observed.ll'].decode()
    old['_checked_sources'](sources)
    families = [node for node in old['_parse_dump'](dumps['get_new_reg']) if node.get('name') == 'get_new_reg' and node.get('kind') == 'FunctionTemplateDecl']
    families = [family for family in families if all(sum(child.get('kind') == 'ParmVarDecl' for child in old['_children'](function)) == 1
                for function in old['_children'](family) if function.get('kind') == 'FunctionDecl')]
    variants = [node for family in families for node in old['_children'](family) if node.get('kind') == 'FunctionDecl'
                and [child.get('type', {}).get('qualType') for child in old['_children'](node) if child.get('kind') == 'TemplateArgument'] == ['unsigned int']]
    if len(variants) != 1 or variants[0].get('type', {}).get('qualType') != 'int (unsigned int)':
        raise ValueError('unique original initialized u32 same-TU variant required')
    bodies = [node for node in old['_children'](variants[0]) if node.get('kind') == 'CompoundStmt']
    if len(bodies) != 1 or len(old['_children'](bodies[0])) != 7:
        raise ValueError('exact original initialized seven-statement body required')
    statements = old['_children'](bodies[0]); assertions = []
    for index, kind, variable, line in ((1, 'width', 'num_regs_needed', 121), (5, 'bound', 'REG_count', 125)):
        node = statements[index]
        try:
            old['_assertion'](node, kind, variable)
        except old['Refused'] as exception:
            if str(exception) != 'initialized assertion contains an unchecked AST effect':
                raise ValueError('original source refusal differs') from exception
        else:
            raise ValueError('original source checker unexpectedly accepted retained SourceLoc')
        new['_assertion'](node, kind, variable, tokens)
        assertions.append({'statement_index': index, 'expected': kind, 'line': line,
                           'old': 'exact original unchecked-AST refusal', 'new': 'accepted exact retained diagnostic'})
    original_failure = None
    try:
        old['observation'](tokens, dumps, module, sources)
    except old['Refused'] as exception:
        original_failure = str(exception)
    if original_failure != 'initialized assertion contains an unchecked AST effect':
        raise ValueError('original complete observer refusal differs')
    outcome = new['observation'](tokens, dumps, module, sources)
    new['_checked_sources'](sources)
    after, _unused_after_payloads = retained_snapshot(observed, expected)
    project_after = {name: sha(regular(PROJECT / name, digest)) for name, digest in SOURCE_PINS.items()}
    if before != after or project_before != project_after:
        raise ValueError('retained/project input changed across replay')
    return {'date': '2026-10-16 ET', 'status': 'RETAINED_OBSERVER_REPLAY_PASS',
            'scope': 'Exact diagnostic AST/token/LLVM replay only; no fresh compiler, native execution, WP, solver or public proof result',
            'raw_root': str(RAW), 'proposal_sha256': PROPOSAL_SHA, 'diagnostic_result_sha256': RESULT_SHA,
            'assertions': assertions, 'source_pins': sources, 'source_components': project_before,
            'retained_files': before, 'complete_pre_post_membership_and_bytes_equal': True,
            'body_families': sorted(outcome['body_bindings']), 'source_body_proof': outcome['source_body_proof'],
            'observed_result_sha256': sha(json.dumps(outcome, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()),
            'operation_checks': {'caller_fences': outcome['operations']['caller']['fences'],
                                 'caller_poststore_counter_reloads': outcome['operations']['caller']['poststore_counter_reloads'],
                                 'source_model_correspondence': outcome['operations']['source_model_correspondence']},
            'read_adapter': 'Unchanged observer functions with Path.read_text bound to exact canonical seven-source bytes and hashes; diagnostic-only input binding',
            'native_tool_or_child_launched': False, 'raw_payload_transferred': False}


if __name__ == '__main__':
    try:
        receipt = main(json.load(sys.stdin))
    except Exception as exception:
        print(json.dumps({'status': 'RETAINED_OBSERVER_REPLAY_REFUSED', 'type': type(exception).__name__,
                          'reason': str(exception), 'scope': 'Retained diagnostic replay only; no fresh public proof',
                          'proposal_sha256': PROPOSAL_SHA, 'native_tool_or_child_launched': False}, sort_keys=True, indent=2))
        raise SystemExit(1)
    print(json.dumps(receipt, sort_keys=True, indent=2))
