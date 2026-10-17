"""2026-10-16 ET. Proposed complete checked-source unit boundary.

Only the fixed no-parameter value fixture is supported. Library selection binds
exact documents, not an admission boolean. Complete compiler provenance and
external receiver/runtime premises remain explicitly owned assumptions. This
module neither imports .scratch code nor launches a compiler/verifier/process.
"""
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import re
import stat

from swdb import dx100_whole_checked as contracts
from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler
from swdb._dx100_whole import lossless_gzip_v1 as codec
from swdb._dx100_whole import model_primitives as model
from swdb._dx100_whole import receiver_state_draws_v2 as receiver
from swdb._dx100_whole import source_argument_staging_v2 as staging
from swdb._dx100_whole import source_dispatch_v3 as dispatch
from swdb._dx100_whole import source_program_globals_v1 as globals_observer
from swdb._dx100_whole import source_statements_v2 as statements
from swdb._dx100_whole import whole_interface_v4 as binder

KIND = 'dx100-whole-interface-source-v1'
FUNCTION = 'whole_interface_source_fixture'
SOURCE_SHA = '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'
FRAME = r'assigns \everything;'
CAPTURE_KIND = 'lossless-complete-original-tu-v1'
BUFFER_PROJECTION = 'fixed-fixture-identical-buffer-with-captured-diagnostic-origin-v1'
METHOD = 'method.dx100-whole-checked-source-v1'
COMPONENT_ORDER = ('whole_value_backend_v1.h', 'whole_adapters.h', 'whole_value_builders_v1.h', 'whole_closed_routes_v1.h')
DEFINES = ('NUM_CORES=4', 'TILE_SIZE=16384')
ROUTE_PRODUCERS = ('c_lowering.py', 'cbmc_translator.py', 'cbmc_adapter.py', 'formal_frame.py',
                   'proof_semantics.py', 'proof_setup.py', 'dx100_checked_adapter.py', 'dx100_checked_native.py')


class Refused(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refused(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def digest(value): return sha(canonical(value))


@dataclass(frozen=True)
class SourceSelection:
    library: object
    entry_id: str
    project: Path
    method_id: str


@dataclass(frozen=True)
class SourceUnit:
    function: str
    returns: str
    source_text: str
    model_text: str
    anchors: tuple
    summaries: tuple
    certificate_json: bytes
    draw_rows_json: bytes
    input_pins: tuple
    policy_json: bytes
    normalized_tu: object
    unit_preparation: object
    statement_preparation: object
    atlas: object
    allocations: tuple
    abi: object
    selection: SourceSelection
    receiver_policy_pin_json: bytes
    receiver_preparation: object

    @property
    def certificate(self): return json.loads(self.certificate_json)


class Inputs:
    """Private physical read set; public callers provide no reader callbacks."""
    def __init__(self, library):
        self.library, self.pins = library, {}

    def absolute(self, row, *, retain=True, limit=8 * 1024 * 1024):
        selected = receiver.Pin.parse(row)
        old = self.pins.get(selected.path)
        need(old is None or old == selected, 'one physical input cannot have conflicting identities')
        value = receiver.check_file(selected, retain=retain, limit=limit)
        self.pins[selected.path] = selected
        return value

    def portable(self, row, *, limit=4 * 1024 * 1024):
        raw = contracts.pinned(self.library, row, limit=limit)
        path = str(Path(self.library.resolve(row)))
        return self.absolute({'path': path, 'bytes': len(raw), 'sha256': row['sha256']}, limit=limit)

    def selected(self, row, *, retain=True, limit=8 * 1024 * 1024):
        if type(row) is dict and set(row) == {'root', 'path', 'sha256'}:
            return self.portable(row, limit=limit)
        return self.absolute(row, retain=retain, limit=limit)

    def path(self, row):
        return Path(self.library.resolve(row)) if 'root' in row else Path(receiver.Pin.parse(row).path)

    def document(self, row): return contracts.document(self.selected(row))

    def stable(self):
        # Compression's chunk callback is deliberately cheap. Full hashes are
        # checked before and after decoding, never once per compressed chunk.
        for selected in self.pins.values():
            path = Path(selected.path)
            metadata = path.lstat()
            need(path.resolve(strict=True) == path and stat.S_ISREG(metadata.st_mode)
                 and metadata.st_size == selected.bytes, 'decoder input shape changed')

    def recheck(self):
        for selected in self.pins.values(): receiver.check_file(selected)


def source_policy(selection, reads):
    need(type(selection) is SourceSelection and selection.method_id == METHOD, 'separate checked-source method required')
    from swdb.library import Library
    physical_library = Library(selection.library.root)
    entry = physical_library.get(selection.entry_id)
    need(not physical_library.problems and entry == selection.library.get(selection.entry_id),
         'selected entry/library bytes changed after selection')
    normalized = contracts.policy(physical_library, entry)
    raw = reads.portable(normalized['source_policy'])
    policy = contracts.document(raw)
    keys = {'kind', 'schema', 'function', 'caller_mangled', 'defines', 'choice_budget', 'thread',
        'buffer_projection', 'proof_source', 'capture', 'receiver_selection', 'expected', 'producer_manifest',
        'native_projection', 'frame', 'unit_contracts', 'source_loop_bound', 'helper_loop_bound'}
    need(type(policy) is dict and set(policy) == keys and policy['kind'] == KIND
         and policy['schema'] == 'dx100-whole-fixed-source-policy-1' and policy['function'] == FUNCTION,
         'one closed current fixture policy required')
    need(policy['buffer_projection'] == BUFFER_PROJECTION and policy['frame'] == FRAME,
         'explicit identical-buffer projection and whole-state frame required')
    need(policy['defines'] == ['NUM_CORES=4', 'TILE_SIZE=16384'] and policy['thread'] == 0
         and type(policy['thread']) is int and policy['choice_budget'] == normalized['choice_budget'],
         'exact original fixture configuration and receiver thread required')
    need(type(policy['source_loop_bound']) is int and policy['source_loop_bound'] == 1
         and type(policy['helper_loop_bound']) is int and policy['helper_loop_bound'] == 513,
         'source and fixed-helper loop bounds must remain separate checked bounds')
    need(type(policy['caller_mangled']) is str and re.fullmatch(r'_Z[0-9]+whole_interface_source_fixturev', policy['caller_mangled']),
         'exact original same-TU caller identity required')
    rows = policy['unit_contracts']
    need(type(rows) is list and len(rows) == 2 and all(type(row) is dict and
         set(row) == {'id','sha256','expected_result'} and type(row['expected_result']) is int and
         type(row['id']) is str and row['id'] and re.fullmatch('[0-9a-f]{64}',str(row['sha256'])) for row in rows)
         and {row['expected_result'] for row in rows} == {79,80} and len({row['id'] for row in rows}) == 2,
         'exact selected positive80/negative79 unit-contract pair required; values never feed the model/draws')
    return entry, normalized, policy


def producer_closure(policy, reads):
    manifest = reads.document(policy['producer_manifest'])
    modules = {Path(item.__file__).name: item for item in
        (compiler, codec, model, receiver, staging, dispatch, globals_observer, statements, binder)}
    fixed_paths = {'runtime_projection_v2.py': Path(__file__).parent / '_dx100_whole/runtime_projection_v2.py',
        'receiver-state-draws-v2/receiver_state_draws_v2.py':
            Path(__file__).parent / '_dx100_whole/receiver-state-draws-v2/receiver_state_draws_v2.py'}
    wanted = set(modules) | {'dx100_checked_source.py', 'dx100_whole_checked.py'} | set(ROUTE_PRODUCERS) | set(fixed_paths)
    need(type(manifest) is dict and set(manifest) == {'schema', 'files'}
         and manifest['schema'] == 'swdb-dx100-whole-producers-1' and set(manifest['files']) == wanted,
         'exact promoted source producer closure required')
    for name in wanted:
        if name in fixed_paths:
            row = manifest['files'][name]
            need(row['path'] == str(fixed_paths[name]), 'fixed native component execution path differs')
            reads.absolute(row)
            continue
        if name in ROUTE_PRODUCERS:
            path = Path(__file__).with_name(name)
            row = manifest['files'][name]
            need(row['path'] == str(path), 'route identity must pin the actual production hook module')
            reads.absolute(row)
            continue
        module = contracts if name == 'dx100_whole_checked.py' else None if name == 'dx100_checked_source.py' else modules[name]
        path = Path(__file__) if module is None else Path(module.__file__)
        row = manifest['files'][name]
        need(row['path'] == str(path), 'producer manifest must bind the actual imported module')
        reads.absolute(row)


def select_baseline(library, proof_unit):
    """Fresh validation selector; it grants no method/runtime or source admission."""
    if type(proof_unit) is not dict or proof_unit.get('function') != FUNCTION:
        return None
    candidates = [(entry_id, data) for entry_id, data in library.entries.items()
                  if data.get('kind') == 'proof_semantics' and data.get('target') == 'dx100-mmio']
    if not candidates:
        return None
    maximum = max(data.get('sequence', 0) for _, data in candidates)
    current = [(entry_id, data) for entry_id, data in candidates if data.get('sequence', 0) == maximum]
    selected = [(entry_id, data) for entry_id, data in current if contracts.checked(data)]
    if not selected:
        return None
    need(len(current) == len(selected) == 1, 'ambiguous current checked semantics version')
    entry_id, data = selected[0]
    binding = contracts.policy(library, data)
    reads = Inputs(library)
    policy = reads.document(binding['source_policy'])
    need(proof_unit.get('source') == policy['proof_source'], 'first whole unit source selection differs')
    # SWDB_HOME is the selected swdb-project root containing the original
    # apps/dx100 headers; never a caller-chosen include root.
    from swdb import paths
    return SourceSelection(library, entry_id, Path(paths.HOME).resolve(strict=True), METHOD)


def checked_unit_format(library, contract_id, data):
    """Narrow formal-frame recognition, without claiming source admission."""
    if (data.get('proof_unit') or {}).get('function') != FUNCTION:
        return None
    try:
        selected = select_baseline(library,data['proof_unit'])
        if selected is None:
            return None
        _,_,policy = source_policy(selected,Inputs(library))
        content = library.content_sha256(contract_id)
        matches = [row for row in policy['unit_contracts'] if row['id'] == contract_id and row['sha256'] == content]
        need(len(matches) == 1 and library.get(contract_id) == data, 'exact selected scalar-pair contract ID/hash required')
        expected = matches[0]['expected_result']
        clauses = data.get('clauses')
        need(type(clauses) is list and len(clauses) == 2, 'exact scalar ensures plus sole whole-state frame required')
        texts=[]
        for row in clauses:
            acsl=row.get('acsl') or {}
            need(set(acsl) <= {'text','uses'} and acsl.get('uses',[]) == [], 'first scalar pair has no extra logic or clauses')
            texts.append(' '.join(acsl.get('text','').split()))
        need(sorted(texts) == sorted([r'assigns \everything;',r'ensures \result == '+str(expected)+';']),
             'no requires, narrower/mixed frames, extra properties or unknown builtins in the fixed scalar pair')
        return []
    except (Refused,ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        return [str(error)]


def sole_whole_frame(acsl):
    return type(acsl) is dict and set(acsl) <= {'text','uses'} and acsl.get('uses',[]) == [] and \
        ' '.join(acsl.get('text','').split()) == r'assigns \everything;'


def complete_capture(policy, reads, project):
    """No partial prefix or unreviewed projected graph is a complete TU input."""
    selected = policy['capture']
    keys = {'kind', 'policy', 'result', 'observation', 'prepared', 'runtime_before', 'runtime_after',
        'zlib_before', 'zlib_after', 'zlib_runtime', 'gzip_receipt', 'compressed_tu', 'abi', 'probe', 'source'}
    need(type(selected) is dict and set(selected) == keys and selected['kind'] == CAPTURE_KIND,
         'unreviewed/partial streaming projections are unsupported; preserve separate graph identities')
    capture_policy = reads.document(selected['policy'])
    result, observation = (reads.document(selected[name]) for name in ('result', 'observation'))
    need(result.get('accepted') is True and result.get('error') is None
         and result.get('after_input_errors') == [] and result.get('bytecode_cache_present') is False
         and 'finalization_refusal' not in result, 'complete settled capture required; accepted alone grants nothing')
    need(observation.get('source_commit') == capture_policy['source_commit']
         and observation.get('original_source_coordinates') is True, 'original configured source coordinate observation required')
    commands = observation['commands']; recipe = capture_policy['capture_recipe']['commands']
    need(len(commands) == len(recipe) == 4 and [row['phase'] for row in commands] ==
         ['caller-preprocess', 'caller-ast', 'abi-preprocess', 'abi-ast'], 'exact four compiler phases required')
    for actual, expected in zip(commands, recipe):
        need(actual['phase'] == expected['phase'] and actual['argv'] == expected['argv']
             and actual['cwd'] == expected['cwd'] and type(actual['returncode']) is int and actual['returncode'] == 0
             and type(actual['timeout_seconds']) in (int, float) and 0 < actual['timeout_seconds'] <= 45,
             'actual compiler command/configuration/exit differs')
        reads.absolute(actual['stdout'], retain=False); reads.absolute(actual['stderr'], retain=False)
    before = reads.document(selected['runtime_before']); after = reads.document(selected['runtime_after'])
    need(after == {'runtime': before, 'after_errors': []}, 'captured runtime pre/post closure differs')
    zbefore, zafter = (reads.document(selected[name]) for name in ('zlib_before', 'zlib_after'))
    need(zbefore == zafter == capture_policy['zlib_binding'], 'captured zlib selection changed')
    for row in observation['inputs']: reads.absolute(row, retain=False)
    need([group['label'] for group in observation['groups']] == ['caller', 'abi'], 'complete caller/ABI groups required')
    for group in observation['groups']:
        for row in group['dependencies']: reads.absolute(row, retain=False)
        for name in ('frozen', 'preprocess_dependency', 'ast', 'ast_dependency'):
            reads.absolute(group[name], retain=False)
        if group['label'] == 'caller': reads.absolute(group['expanded_stream_receipt'], retain=False)
    receipt = reads.document(selected['gzip_receipt'])
    compressed = reads.portable(selected['compressed_tu'], limit=134217728)
    need(receipt['compressed_sha256'] == sha(compressed), 'retained gzip identity differs')
    # zlib is imported only after the physical selected runtime has been checked.
    runtime = reads.document(selected['zlib_runtime'])
    need(set(runtime) == {'schema', 'origin', 'version', 'physical_inputs'}
         and runtime['schema'] == 'selected-stdlib-zlib-runtime-1', 'closed decoder runtime selection required')
    for row in runtime['physical_inputs']: reads.absolute(row, retain=False)
    import zlib
    need(zlib.__spec__.origin == runtime['origin'] and zlib.ZLIB_RUNTIME_VERSION == runtime['version'], 'actual selected zlib identity differs')
    full_tu_raw = codec.decode(zlib, io.BytesIO(compressed), receipt,
        expanded_limit=536870912, compressed_limit=134217728, check=reads.stable)
    source = reads.selected(selected['source']); probe = reads.selected(selected['probe'])
    need(sha(source) == SOURCE_SHA, 'first captured original source fixture differs')
    source_path, probe_path = reads.path(selected['source']), reads.path(selected['probe'])
    declarations = binder.inventory(project)
    prepared = compiler.prepare_unit(binder.__dict__, full_tu_raw=full_tu_raw, abi_raw=reads.selected(selected['abi']),
        source_path=source_path, source_bytes=source, probe_path=probe_path, probe_bytes=probe, declarations=declarations,
        compiler_capture_pin=selected['observation']['sha256'], full_tu_compressed_bytes=receipt['compressed_bytes'], full_tu_expanded_limit=536870912)
    need(prepared == reads.document(selected['prepared']), 'fresh complete original TU/ABI preparation differs')
    need(prepared['raw_full_tu_sha256'] == receipt['expanded_sha256'], 'expanded original stream identity differs')
    tu = compiler.resolve_locations(compiler.parse_json_roots(full_tu_raw, full_tu=True, expanded_limit=536870912)[0], source_path)
    reads.recheck()
    return source_path, source, tu, declarations, prepared, receipt


class LifetimeLowerer(statements.Lowerer):
    """Fixed producer hooks, never an externally supplied renderer."""
    def __init__(self, *args, allocations, public_function, **kwargs):
        super().__init__(*args, **kwargs)
        self.allocations = {row['local_id']: row for row in allocations}
        self.public_function, self.source_anchors, self.serial_anchor = public_function, [], 0

    def local(self, node):
        if node.get('id') in self.allocations:
            row = self.allocations[node['id']]
            need(row['declaration_sha256'] == digest(node), 'allocation hook declaration identity differs')
            self.emit('dws_local_enter_%d_v1();' % row['object_index'])
        super().local(node)

    def _leave(self, frames):
        for frame in reversed(frames):
            for ident in reversed(frame['arrays']):
                need(ident in self.allocations, 'every source allocation requires a fixed lifetime hook')
                self.emit('dws_local_leave_%d_v1();' % self.allocations[ident]['object_index'])

    def statement(self, node):
        serial = self.serial_anchor; self.serial_anchor += 1
        ident = self.public_function + '.s' + str(serial)
        self.emit('/* swdb-anchor ' + ident + '.before */')
        self.source_anchors.append({'id': ident + '.before', 'source_range': self.api['_span'](node), 'kind': 'statement_before'})
        super().statement(node)
        self.emit('/* swdb-anchor ' + ident + '.after */')
        self.source_anchors.append({'id': ident + '.after', 'source_range': self.api['_span'](node), 'kind': 'statement_after'})


def live_pointer_bridge(atlas, thread):
    text = dispatch.render_pointer_bridge(atlas)
    marker = 'if(p.kind==1) {'
    need(text.count(marker) == 3, 'fixed ordinary pointer bridge changed')
    text = text.replace(marker, marker + '\n    dws_local_require_v1(p.object,%du);' % thread)
    marker = 'DXM_CHECK(p.kind==1 && p.dtype==dtype && p.offset<total && p.offset%bytes==0,"source-array-pointer-binding");'
    need(text.count(marker) == 1, 'fixed device ordinary footprint bridge changed')
    return 'static void dws_local_require_v1(unsigned object,unsigned accessing_thread);\n' + text.replace(marker,
        marker + '\n  dws_local_require_v1(p.object,%du);' % thread)


def compose(selection, *, source, function, defines=()):
    """Return one checked complete unit; all unsupported policy/graph kinds refuse."""
    reads = Inputs(selection.library)
    entry, normalized, policy = source_policy(selection, reads)
    semantics_path = Path(selection.library.files[selection.entry_id])
    semantics_raw = semantics_path.read_bytes()
    semantics_pin = {'path':str(semantics_path),'bytes':len(semantics_raw),'sha256':sha(semantics_raw)}
    reads.absolute(semantics_pin)
    producer_closure(policy, reads)
    need(function == FUNCTION and tuple(sorted(defines)) == tuple(policy['defines']), 'unsupported function/build configuration')
    requested = reads.portable(policy['proof_source'])
    need(Path(source).resolve(strict=True) == Path(selection.library.resolve(policy['proof_source']))
         and sha(requested) == SOURCE_SHA, 'exact selected first-fixture proof buffer required')
    captured_path, original, tu, declarations, prepared, stream_receipt = complete_capture(policy, reads, selection.project)
    need(requested == original, 'explicit first-fixture identical-buffer projection differs')
    expected = policy['expected']
    need(set(expected) == {'atlas', 'globals', 'statements', 'assembly', 'receiver_binding_sha256'}, 'complete source expectation closure required')
    atlas = reads.document(expected['atlas'])
    receiver_raw = reads.portable(policy['receiver_selection'])
    receiver_policy = contracts.document(receiver_raw)
    receiver_path = Path(selection.library.resolve(policy['receiver_selection']))
    context = contracts.document(reads.absolute(receiver_policy['context_receipt']))
    need(receiver_policy['inputs']['full_tu']['sha256'] == policy['capture']['compressed_tu']['sha256']
         and receiver_policy['full_tu_canonical_sha256'] == prepared['normalized_full_tu_sha256'],
         'compressed storage and canonical original graph identities must remain distinct')
    observed = globals_observer.observe_globals(binder.__dict__, tu, declarations,
        execution_mode='fresh-cxx-program-globals', program_context_receipt_sha256=receiver_policy['context_receipt']['sha256'])
    need(observed == reads.document(expected['globals']), 'actual twelve-global observation differs')
    abi = prepared['abi_observation']['abi']
    stage = staging.Stager(binder.__dict__, dispatch.__dict__, tu, caller=policy['caller_mangled'], source_path=captured_path,
        source_text=original.decode('ascii'), declarations=declarations, abi=abi, atlas=atlas, live_local_ids=set())
    header = receiver_policy['inputs']['assertion_header']
    uninstrumented = statements.Lowerer(stage, prepared, assertion_header_pin=header).lower()
    need(uninstrumented == reads.document(expected['statements']), 'complete original statement/CPU/assertion projection differs')
    allocations = context['ordinary_allocations']
    need(not any(node.get('kind') in {'ForStmt', 'WhileStmt', 'DoStmt'} for node in statements.walk(stage.owner)),
         'first fixed fixture has no original source loops; successor required')
    bodies = [node for node in stage.owner.get('inner', []) if node.get('kind') == 'CompoundStmt']
    need(len(bodies) == 1, 'one original source function body required')
    for row in allocations:
        node = stage.declarations[row['local_id']]
        need(row['declaration_sha256'] == digest(node) and row['declaration_range'] == list(binder._span(node))
             and row['scope_end_offset'] == binder._span(bodies[0])[1]
             and row['caller'] == policy['caller_mangled'] and row['allocation_thread'] == policy['thread'],
             'ordinary allocation origin/scope is not the exact original declaration')
    # New state for the second, instrumented emission; no source is executed.
    stage = staging.Stager(binder.__dict__, dispatch.__dict__, tu, caller=policy['caller_mangled'], source_path=captured_path,
        source_text=original.decode('ascii'), declarations=declarations, abi=abi, atlas=atlas, live_local_ids=set())
    lowerer = LifetimeLowerer(stage, prepared, assertion_header_pin=header, allocations=allocations, public_function=function)
    lowered = lowerer.lower()
    prepared_receiver = receiver.prepare(receiver.OwnedSelection(receiver.Pin(str(receiver_path), len(receiver_raw), sha(receiver_raw))))
    need(sha(prepared_receiver.binding_json) == expected['receiver_binding_sha256'], 'receiver binding differs')
    # Preparation validates historical producer bases as data. Retain that entire
    # physical closure for all later prelaunch/postlaunch checks too.
    for row in receiver_policy['inputs'].values(): reads.absolute(row, retain=False)
    for row in receiver_policy['physical_inputs'].values(): reads.absolute(row, retain=False)
    for row in receiver_policy['frozen_inputs'].values(): reads.absolute(row, retain=False)
    assembly = reads.document(expected['assembly'])
    components = {Path(row['path']).name: reads.portable(row).decode('utf-8') for row in normalized['components']}
    need(set(components) == set(COMPONENT_ORDER), 'exact reviewed backend body set required')
    component_texts = [components[name] for name in COMPONENT_ORDER]
    routes, instances = dispatch.render_routes(binder.__dict__, declarations, abi)
    design = reads.document(normalized['design']); model.check_contract_inventory(design['calls'], declarations)
    base_parts = [model.hook_text(policy['choice_budget']), *component_texts,
        dispatch.render_direct_families(binder.__dict__, declarations), dispatch.render_pointer_bridge(atlas), routes]
    need('\n'.join(base_parts) + '\n' == assembly['c_text'], 'checked concrete assembly differs from exact selected source bodies')
    parts = [model.hook_text(policy['choice_budget']), *component_texts, dispatch.render_direct_families(binder.__dict__, declarations),
        live_pointer_bridge(atlas, policy['thread']), routes, statements.lifetime_helper(), prepared_receiver.c_text]
    model_text = '\n'.join(parts) + '\n'
    lifetime = statements.lifetime_helper() + '\n'
    need(lowered['text'].startswith(lifetime), 'fixed lifetime helper placement changed')
    body = lowered['text'][len(lifetime):]
    wrapper = '\n/* swdb-anchor %s.contract */\n%s %s(void) {\n/* swdb-anchor %s.entry */\n  return dws_source_program(%du);\n}\n' % (function, lowerer.returns, function, function, policy['thread'])
    text = body + wrapper
    anchors = tuple({'id': match[1], 'function': function, 'kind': 'contract' if match[1].endswith('.contract') else
        'entry' if match[1].endswith('.entry') else 'statement', 'line': text.count('\n', 0, match.start()) + 1}
        for match in re.finditer(r'/\* swdb-anchor (\S+) \*/', text))
    draws = json.loads(prepared_receiver.draw_plan_json)['producer_plan_rows']
    draws = [{**row, 'c_lvalue': 'dws_choice_table[%d]' % index} for index, row in enumerate(draws)]
    certificate = {'kind': KIND, 'entry': selection.entry_id, 'source_policy': normalized['source_policy'],
        'semantics_entry_file':semantics_pin,
        'semantics_entry_content_sha256':selection.library.content_sha256(selection.entry_id),
        'source_sha256': SOURCE_SHA, 'captured_source_path': str(captured_path), 'proof_source_path': str(Path(source)),
        'buffer_projection': BUFFER_PROJECTION, 'full_tu_expanded_sha256': stream_receipt['expanded_sha256'],
        'full_tu_compressed_sha256': stream_receipt['compressed_sha256'], 'normalized_original_graph_sha256': prepared['normalized_full_tu_sha256'],
        'original_statement_preparation_sha256': digest(uninstrumented), 'instrumented_statement_sha256': sha(text.encode()),
        'model_sha256': sha(model_text.encode()), 'receiver_binding_sha256': sha(prepared_receiver.binding_json),
        'draw_plan_sha256': digest(draws), 'producer_manifest': policy['producer_manifest'],
        'formal_frame': FRAME, 'source_loop_bound': 1, 'helper_loop_bound': 513,
        'native_mode': 'one fresh program per sampled oracle line; source-preserving C++ view mandatory',
        'recorded_context_assumptions': json.loads(prepared_receiver.binding_json)['record_assumptions'],
        'precise_frame_projection': 'unsupported', 'source_assertion_count': len(lowered['assertions']),
        'CPU_access_count': len(lowered['CPU_projections']), 'call_count': len(lowered['call_bindings'])}
    reads.recheck()
    summaries = tuple({'name': row['binding']['name'],
        'c_name': ('dws_get_data_type_other' if row['binding']['name'] == 'get_data_type' and row['binding']['dtype'] == 6
                   else 'dws_' + row['binding']['c_name']),
        'summary': selection.entry_id,
        'semantic_instance': {'source_call': row['binding'], 'dispatch_plan': row['dispatch_plan'],
                              'staged_arguments': row['staged_arguments']}}
        for row in lowered['call_bindings'])
    return SourceUnit(function, lowerer.returns, text, model_text, anchors, summaries,
        canonical(certificate), canonical(draws), tuple(reads.pins.values()), canonical(policy), tu, prepared, uninstrumented,
        atlas, tuple(allocations), abi, selection,
        canonical(receiver.Pin(str(receiver_path), len(receiver_raw), sha(receiver_raw)).row()), prepared_receiver)


def recheck(unit):
    """Fresh composition, never formal_frame's generic source/name-only cache."""
    need(type(unit) is SourceUnit, 'producer-created whole source unit required')
    policy = json.loads(unit.policy_json)
    fresh = compose(unit.selection, source=unit.certificate['proof_source_path'],
        function=unit.function, defines=policy['defines'])
    need(fresh == unit, 'checked source/receiver/atlas/transport closure changed')
    return unit.certificate


def lowering_fields(unit):
    """Dependency-free data for c_lowering.Lowering; no generic _Unit traversal."""
    need(type(unit) is SourceUnit, 'checked source unit required')
    certificate = unit.certificate
    return {'function': unit.function, 'text': unit.source_text, 'anchors': unit.anchors,
        'declaration': '#include <stddef.h>\n#include <stdint.h>\n' + unit.returns + ' ' + unit.function + '(void);\n',
        'parameters': (), 'source_sha256': SOURCE_SHA, 'defines': tuple(json.loads(unit.policy_json)['defines']),
        'tool': {'id': KIND, 'source_policy_sha256': digest(json.loads(unit.policy_json)),
                 'whole_source_certificate_sha256': sha(unit.certificate_json)},
        'summaries': unit.summaries, 'whole_source': unit}


def unit_contract(library, unit, contract_id, contract_sha256, rows):
    """The selected real positive/negative pair changes only its result property."""
    policy = json.loads(unit.policy_json)
    selected = [row for row in policy['unit_contracts'] if row['id'] == contract_id and row['sha256'] == contract_sha256]
    need(len(selected) == 1 and library.content_sha256(contract_id) == contract_sha256,
         'exact selected first unit contract required')
    result = selected[0]['expected_result']
    need(type(result) is int and result in (79,80), 'only the exact selected positive80/negative79 pair is supported')
    need(len(rows) == 2 and sorted((row.kind, ' '.join(row.text.split())) for row in rows) ==
         [('assigns', r'\everything'), ('ensures', r'\result == ' + str(result))],
         'first unit states exactly its selected result and assigns everything; no hidden requires or precise frame')


def harness_profile(unit, interface, rows, sizes, knobs, setup, state, finish, array_domains):
    """Fixed checked-entry draw accounting. Receiver performs the actual draws once."""
    need(type(unit) is SourceUnit and interface.function == FUNCTION
         and interface.returns == unit.returns and interface.parameters == () and interface.globals == (),
         'one original no-parameter scalar interface required')
    need(not sizes and not knobs and not setup and not state and not finish and not array_domains,
         'checked receiver profile cannot mix generic reset, havoc, callbacks, knobs or pointer windows')
    clauses = sorted((row.kind, ' '.join(row.text.split())) for row in rows)
    need(len(rows) == 2 and clauses in ([('assigns',r'\everything'),('ensures',r'\result == 80')],
         [('assigns',r'\everything'),('ensures',r'\result == 79')]), 'exact prospective scalar pair required')
    draws = json.loads(unit.draw_rows_json)
    budget = json.loads(unit.policy_json)['choice_budget']
    need(type(budget) is int and 1 <= budget <= 256 and draws == [
        {'name': 'whole_choice_' + str(i), 'role': 'whole-model-choice', 'ctype': 'uint32_t',
         'c_lvalue': 'dws_choice_table[' + str(i) + ']'} for i in range(budget)],
         'exact ordered full-domain independent uint32 draw slots required')
    return {'setup': ('dws_prepare_receiver_v1();',), 'draws': draws,
        'frame': r'\everything', 'native_mode': 'one-source-call-per-fresh-program',
        'certificate_sha256': sha(unit.certificate_json)}


def model_fields(unit):
    need(type(unit) is SourceUnit, 'source-bound concrete model required')
    helpers = tuple(sorted(set(re.findall(r'^(?:static\s+)?[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*\{',
        unit.model_text, re.M))))
    need(helpers and FUNCTION not in helpers and 'dws_source_program' not in helpers,
         'fixed helper functions and original source functions must be disjoint')
    return {'entry': unit.selection.entry_id, 'sha256': unit.certificate['semantics_entry_file']['sha256'],
        'calls': tuple(sorted({row['name'] for row in unit.summaries})), 'queries': (),
        'c_text': unit.model_text, 'functions': helpers, 'unwind': 513, 'tile_objects': ()}


def record_assumptions(unit):
    """Owned trace premises remain visible; no hardware refinement is inferred."""
    cert = unit.certificate
    reference = {'id': unit.selection.entry_id, 'sha256': cert['semantics_entry_file']['sha256']}
    rows = [{'kind': 'assumed_clause', 'reference': dict(reference,
        clause='owned-context.' + row['rule']), 'sentence': row['statement'] + ' Owner: ' + row['owner'] + '.'}
        for row in cert['recorded_context_assumptions']]
    rows.append({'kind': 'proof_semantics', 'reference': reference,
        'sentence': 'The selected complete original TU and fixed identical-buffer projection bind this scalar source fixture to its checked concrete call model under the recorded compiler, numeric and MMIO premises. The prospective unit frame is assigns everything. Native agreement samples a source-preserving runtime view under the same model premise; it does not independently establish hardware refinement or a precise frame.'})
    return rows


WHOLE_NATIVE_FAILURE = r'''/* Checked source: one fresh native process, no recovery across C++ lifetimes. */
#if defined(SWDB_NATIVE)
static void swdb_whole_native_stop(const char *name, const char *end) {
  if(name) swdb_failed(name);
  printf(" end=%s\n",end); fflush(stdout); _Exit(0);
}
#undef SWDB_CHECK
#undef SWDB_ASSUME
#define SWDB_CHECK(c,name) do { if(!(c)) swdb_whole_native_stop((name),"check"); } while(0)
#define SWDB_ASSUME(c) do { if(!(c)) swdb_whole_native_stop(NULL,"infeasible"); } while(0)
#endif
'''


def native_prelude(unit, text):
    need(type(unit) is SourceUnit, 'checked source unit required for fresh native failure mode')
    marker = '#define SWDB_SEPARATED('
    need(text.count(marker) == 1 and text.index(marker) < text.index('static long long swdb_next(void)'),
         'checked native macro override must precede the oracle and all source/model definitions')
    return text.replace(marker, WHOLE_NATIVE_FAILURE + marker, 1)
