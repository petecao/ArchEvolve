"""2026-10-16 ET. Closed three-caller original-source selection and C++ root cut.

No compiler, project import, native or proof execution. This does not construct
an AST, alter its IDs or replace source statement/effect/ABI validation. A future
normal producer must call this only after complete original-TU transport closure
and must still re-run the existing full selected-body checker. The old first
3148 source and fixed79/80 policy are deliberately outside this helper.
"""
import hashlib
import json
from pathlib import Path
import re
import stat

SOURCE_SHA = '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'
BINDER_SHA = '217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8'
CASES = (
    ('whole_same_thread_read_during_store', 7, 'refuted', 'store-footprint-cpu-access'),
    ('whole_same_thread_write_during_gather', 9, 'refuted', 'same-thread-read-footprint-write'),
    ('whole_same_thread_read_during_gather', 7, 'proven', None),
)


class Refused(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refused(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def stable(value):
    return tuple(getattr(value, name) for name in ('st_dev', 'st_ino', 'st_mode', 'st_nlink',
        'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def physical(path, expected, limit=131072):
    path = Path(path)
    before = path.lstat()
    need(path.is_absolute() and path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode)
         and 0 < before.st_size <= limit, 'bounded canonical original source/component required')
    with path.open('rb') as handle:
        raw = handle.read(limit + 1)
    need(len(raw) == before.st_size and stable(path.lstat()) == stable(before)
         and hashlib.sha256(raw).hexdigest() == expected, 'original source/component changed')
    return raw, {'path': str(path), 'bytes': len(raw), 'sha256': expected}


def walk(node):
    need(type(node) is dict, 'complete same-TU nodes must be objects')
    yield node
    children = node.get('inner', [])
    need(type(children) is list and all(type(child) is dict for child in children), 'closed same-TU child arrays required')
    for child in children:
        yield from walk(child)


def spelling_span(text, name):
    # This lexical convenience is closed by the immutable complete source SHA.
    # Actual compiler spans below must equal it; no AST is inferred from text.
    marker = 'std::uint32_t ' + name + '() {'
    need(text.count(marker) == 1, 'one exact source definition spelling required')
    start = text.index(marker)
    at = start + len(marker)
    depth = 1
    while depth:
        need(at < len(text), 'unclosed exact source definition')
        depth += (text[at] == '{') - (text[at] == '}')
        at += 1
    return [start, at]


def profile(function):
    choices = [row for row in CASES if row[0] == function]
    need(len(choices) == 1, 'unsupported exact original memory caller')
    name, result, verdict, failure = choices[0]
    return {'function': name, 'caller_mangled': '_Z' + str(len(name)) + name + 'v',
        'source_sha256': SOURCE_SHA, 'defines': ['NUM_CORES=4', 'TILE_SIZE=16384'],
        'thread': 0, 'choice_budget': 256, 'source_loop_bound': 1, 'helper_loop_bound': 513,
        'frame': r'assigns \everything;',
        'contract': {'id': 'contract.dx100_' + name, 'expected_result': result},
        'predicted_verdict': verdict, 'predicted_failure_rule': failure,
        'objects': [{'name': 'data', 'dtype': 0, 'extent': 16, 'bytes': 64,
            'requires_owned_physical_alignment': 64, 'alignment_inferred_from_source': False}],
        'pointer_locals': [] if name.endswith('during_store') else ['index_data']}


def selected_root(api, *, normalized_tu, source_path, preparation, function, declarations, abi):
    """Keep complete-TU identity and verify the selected no-argument root closure.

    No independently parsed or filtered subtree is accepted. `preparation` is
    recomputed upstream from that complete original TU and separate ABI literals.
    Actual compiler/runtime/source provenance is an additional upstream premise.
    """
    need(type(api) is dict, 'fixed reviewed binder namespace required')
    physical(api['__file__'], BINDER_SHA)
    raw, source_pin = physical(source_path, SOURCE_SHA)
    text = raw.decode('ascii')
    chosen = profile(function)
    need(normalized_tu.get('kind') == 'TranslationUnitDecl'
         and preparation.get('schema') == 'whole-interface-original-tu-preparation-1'
         and preparation.get('one_full_tu_for_all_declaration_ids') is True
         and preparation.get('normalized_full_tu_sha256') == digest(normalized_tu)
         and preparation.get('original_source_sha256') == SOURCE_SHA,
         'complete original same-TU preparation identity required')
    api['validate_abi'](abi)
    need(type(declarations) is list and len(declarations) == 27
         and len({row['name'] for row in declarations}) == 26,
         'complete source-derived original API inventory required')
    source_name = str(Path(source_path))
    physical_nodes = [node for node in walk(normalized_tu)
        if node.get('loc', {}).get('_file', node.get('loc', {}).get('file')) == source_name]
    roots = [node for node in physical_nodes if node.get('kind') == 'FunctionDecl']
    need(len(roots) == 3 and {node.get('name') for node in roots} == {row[0] for row in CASES},
         'complete three-function original-source declaration census differs')
    spans = []
    for root in roots:
        current = profile(root['name'])
        span = api['_span'](root)
        need(root.get('mangledName') == current['caller_mangled']
             and span == spelling_span(text, root['name'])
             and root.get('type', {}).get('qualType') == 'std::uint32_t ()'
             and root.get('storageClass') not in ('static', 'extern')
             and not root.get('variadic') and not root.get('isImplicit')
             and [child.get('kind') for child in root.get('inner', [])] == ['CompoundStmt'],
             'exact no-parameter original source definition/type/range required')
        need(type(root.get('id')) is str and re.fullmatch(r'0x[0-9a-f]+', root['id']), 'actual same-TU root identity required')
        spans.append((span, root))
    spans.sort(key=lambda row: row[0])
    need(all(left[0][1] <= right[0][0] for left, right in zip(spans, spans[1:]))
         and len({root['id'] for _, root in spans}) == 3, 'disjoint unique original source roots required')
    owner = next(root for _, root in spans if root['name'] == function)
    selected_nodes = list(walk(owner))
    selected_ids = {id(node) for node in selected_nodes}
    # Exact source text has only the three independent definitions. Still bind
    # that fact to the actual same-TU source nodes; no hidden global initializer,
    # source function, nested class/lambda or source-owned variable may be cut.
    for node in physical_nodes:
        kind = node.get('kind', '')
        if kind in {'VarDecl', 'ParmVarDecl', 'RecordDecl', 'CXXRecordDecl', 'LambdaExpr',
                    'NamespaceDecl', 'UsingDecl', 'TypeAliasDecl', 'TypedefDecl'}:
            need(any(id(node) in {id(child) for child in walk(root)} for _, root in spans)
                 and kind == 'VarDecl', 'source declaration outside the closed automatic-local scope')
    locals_by_id = {}
    for node in selected_nodes:
        if node.get('kind') == 'VarDecl':
            ident = node.get('id')
            need(type(ident) is str and ident not in locals_by_id
                 and node.get('storageClass') not in ('static', 'extern') and not node.get('tls'),
                 'unique selected automatic-local identity required')
            locals_by_id[ident] = node
    source_ids = {root['id'] for _, root in spans}
    source_locals = {node.get('id') for node in physical_nodes if node.get('kind') == 'VarDecl'}
    for node in selected_nodes:
        if node.get('kind') != 'DeclRefExpr':
            continue
        ref = node.get('referencedDecl', {})
        need(type(ref) is dict, 'original declaration reference object required')
        if ref.get('kind') == 'VarDecl':
            need(ref.get('id') in locals_by_id, 'selected body references a nonlocal/global variable')
        need(ref.get('id') not in source_ids
             and (ref.get('id') not in source_locals or ref.get('id') in locals_by_id),
             'selected body depends on an omitted source definition/local')
    call_rows = [row for row in preparation.get('calls', []) if row.get('caller_mangled') == chosen['caller_mangled']]
    actual_calls = [node for node in selected_nodes if node.get('kind') == 'CallExpr']
    need(call_rows and len(call_rows) == len(actual_calls)
         and len({tuple(row['call_range']) for row in call_rows}) == len(call_rows)
         and {tuple(row['call_range']) for row in call_rows} == {tuple(api['_span'](node)) for node in actual_calls},
         'every selected original call must bind the same complete-TU API census')
    names = {row['name'] for row in declarations}
    for row in call_rows:
        need(row['name'] in names, 'unadmitted selected source call')
        need(api['recheck_binding'](row, normalized_tu, caller=chosen['caller_mangled'],
             call_range=row['call_range'], source_path=source_path, source_text=text,
             declarations=declarations, abi=abi) == row, 'fresh actual selected API binding differs')
    # The full original graph is never replaced by this root cut. Only the C++
    # counterpart text omits the two uncalled definitions. Spaces preserve all
    # original offsets, lines and selected tokens. The existing checked-body
    # consumer must still validate every selected expression, CPU effect and
    # lifetime before any compiler/native/public route can use this text.
    removed = []
    chars = list(text)
    for span, root in spans:
        if id(root) in selected_ids:
            continue
        begin, end = span
        need(root['id'] not in {node.get('referencedDecl', {}).get('id') for node in selected_nodes},
             'omitted source function remains referenced')
        removed.append({'id': root['id'], 'name': root['name'], 'range': span,
            'definition_sha256': digest(root), 'source_slice_sha256': hashlib.sha256(raw[begin:end]).hexdigest()})
        chars[begin:end] = ['\n' if char == '\n' else '\r' if char == '\r' else ' ' for char in text[begin:end]]
    projected = ''.join(chars)
    begin, end = api['_span'](owner)
    need(projected[begin:end] == text[begin:end] and len(projected) == len(text)
         and [i for i, char in enumerate(projected) if char == '\n'] == [i for i, char in enumerate(text) if char == '\n'],
         'selected body/source coordinate preservation differs')
    physical(api['__file__'], BINDER_SHA)
    physical(source_path, SOURCE_SHA)
    return {'schema': 'exact-three-source-root-cut-1', 'profile': chosen,
        'source': source_pin, 'original_normalized_tu_sha256': digest(normalized_tu),
        'selected_declaration_id': owner['id'], 'selected_declaration_sha256': digest(owner),
        'selected_source_range': [begin, end], 'omitted_unreferenced_definitions': removed,
        'selected_API_call_binding_sha256': digest(call_rows),
        'same_TU_graph_modified_or_filtered': False, 'selected_tokens_and_coordinates_preserved': True,
        'counterpart_root_source': projected, 'counterpart_root_source_sha256': hashlib.sha256(projected.encode()).hexdigest(),
        'selected_full_body_CPU_effect_lifetime_validation_still_required': True,
        'upstream_complete_compiler_transport_and_owned_receiver_admission_required': True,
        'actual_source_ABI_native_public_or_new02_acceptance': False}
