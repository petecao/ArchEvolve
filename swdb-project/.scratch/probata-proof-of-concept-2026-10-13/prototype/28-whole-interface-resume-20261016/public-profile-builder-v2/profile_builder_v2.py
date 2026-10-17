"""2026-10-16 ET. Inert two-phase, compiler-free first-source profile builder.

Only derive()/assemble() import the separately installed, root-selected normal
SWDB package. Neither launches a process. This file never imports .scratch code.
The complete-capture ingress remains the reviewed production-route V3 boundary;
a role-normalized transport requires a separately reviewed version of this
builder and route. A matching receipt hash does not grant external authority.
"""
from dataclasses import dataclass
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from types import SimpleNamespace

SOURCE_SHA = '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'
SOURCE_KIND = 'dx100-whole-interface-source-v1'
MODEL_KIND = 'dx100-whole-interface-checked-body-1'
FUNCTION = 'whole_interface_source_fixture'
METHOD = 'method.dx100-whole-checked-source-v1'
INGRESS = 'reviewed-production-route-v3-complete-capture'
BASIS_SHA = '66bacdc09fd1996cebe3f9d806101ae010cb058571158a9a1522a14cd7c9784f'
FRAME = r'assigns \everything;'
COMPONENTS = ('whole_value_backend_v1.h', 'whole_adapters.h',
              'whole_value_builders_v1.h', 'whole_closed_routes_v1.h')
CONTRACT_IDS = {80: 'contract.dx100_whole_source_80', 79: 'contract.dx100_whole_source_79'}
REQUEST_KEYS = {'schema', 'owner', 'original_project', 'producer_project', 'library_root',
    'producer_snapshot', 'capture', 'proof_source', 'design', 'components', 'physical_inputs',
    'runtime_receipt', 'mapping_receipt', 'assertion_header', 'choice_budget', 'method_seed',
    'compiler_observation', 'owned_rules_receipt', 'ingress'}


class Refused(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refused(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(canonical(value))


def exact(value, keys, name):
    need(type(value) is dict and set(value) == set(keys), name + ' exact fields required')


def parse(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'duplicate JSON key refused; no last-wins interpretation')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(Refused('nonfinite JSON refused')))


def stable(metadata):
    return tuple(getattr(metadata, name) for name in ('st_dev', 'st_ino', 'st_mode', 'st_nlink',
        'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def pin(path, raw):
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def read(row, *, limit=8 * 1024 * 1024):
    exact(row, {'path', 'bytes', 'sha256'}, 'physical pin')
    need(type(row['path']) is str and Path(row['path']).is_absolute()
         and type(row['bytes']) is int and 0 <= row['bytes'] <= limit
         and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']),
         'bounded physical pin required')
    path = Path(row['path']); before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path
         and before.st_size == row['bytes'], 'canonical physical regular file required')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    need(len(raw) == row['bytes'] and sha(raw) == row['sha256']
         and stable(path.lstat()) == stable(before), 'physical input changed or hash differs')
    return raw


def relative(value):
    need(type(value) is str and value and not Path(value).is_absolute()
         and value == Path(value).as_posix() and '\\' not in value
         and not any(part in ('.', '..', '.git', '__pycache__') for part in value.split('/')),
         'canonical source-relative path required')
    return value


@dataclass(frozen=True)
class LibraryRoot:
    root: Path
    project: Path

    def resolve(self, row):
        exact(row, {'root', 'path', 'sha256'}, 'portable pin')
        need(row['root'] in ('library', 'project'), 'closed portable root required')
        return (self.root if row['root'] == 'library' else self.project) / relative(row['path'])


def portable(library, row):
    path = library.resolve(row)
    return read({'path': str(path), 'bytes': path.lstat().st_size, 'sha256': row['sha256']})


def require_capture(result):
    need(type(result) is dict and result.get('accepted') is True and result.get('error') is None
         and result.get('after_input_errors') == [] and result.get('bytecode_cache_present') is False
         and 'finalization_refusal' not in result, 'failed, partial, or unsettled capture refused')


def original_project_role(project, observation):
    """Check original physical coordinates before any semantic helper imports."""
    project = Path(project)
    need(project.is_absolute() and project.resolve(strict=True) == project,
         'canonical captured original project required')
    need(os.environ.get('SWDB_HOME') == str(project), 'SWDB_HOME must select the captured original project')
    expected = {str(project / 'apps/dx100/benchmarks/API' / name) for name in ('MAA.hpp', 'MAA_gem5.hpp')}
    groups = observation.get('groups')
    need(type(groups) is list and [row.get('label') for row in groups] == ['caller', 'abi'],
         'complete caller/ABI groups required before semantic preparation')
    for group in groups:
        paths = [row['path'] for row in group['dependencies']]
        actual = {name for name in paths if Path(name).name in ('MAA.hpp', 'MAA_gem5.hpp')}
        need(actual == expected, 'captured original header paths differ from selected project')


def source_inventory(design, declarations):
    """Complete immutable inventory, never a caller-name or filtered-ID subset."""
    calls = design.get('calls')
    need(type(calls) is list and len(calls) == 26 and len({row['call'] for row in calls}) == 26
         and sum(len(row['source_declarations']) for row in calls) == 27
         and sum(len(row['typed_arity_instances']) for row in calls) == 132,
         'exact 26-name/27-declaration/132-instance design required')
    need(len(declarations) == 27 and {row['name'] for row in declarations} == {row['call'] for row in calls},
         'complete original declaration inventory required')


def unit_contracts(proof_source):
    """No semantics back-reference: finalize these hashes before source policy."""
    result = {}
    for expected in (79, 80):
        result[expected] = {'id': CONTRACT_IDS[expected], 'kind': 'rewrite_contract',
            'formal_frame': 1, 'version': '1.0',
            'provenance': {'origin': {'intrinsic_specification': 'ticket28 checked original whole-source unit; 2026-10-16 ET'}},
            'proof_unit': {'source': proof_source, 'function': FUNCTION},
            'concurrency_frame': [],
            'clauses': [{'id': 'frame', 'role': 'frame',
                'statement': 'The checked whole-source unit may change its whole modeled state.',
                'discharge_mode': 'runtime_guard', 'negative_control': {'id': 'narrow-frame', 'check': 'whole-state-frame'},
                'acsl': {'text': FRAME, 'uses': []}, 'proof_placement': {'once': 'self'}},
                {'id': 'result', 'role': 'postcondition',
                'statement': 'Original whole-source scalar result equals ' + str(expected) + '.',
                'discharge_mode': 'runtime_guard', 'negative_control': {'id': 'wrong-result', 'check': 'result'},
                'acsl': {'text': r'ensures \result == ' + str(expected) + ';', 'uses': []},
                'proof_placement': {'once': 'self'}}],
            'pattern_key': [{'roles': ['target'], 'address_shapes': ['stream'], 'update_kind': 'read'}],
            'strategies': [], 'uses_intrinsics': [], 'uses_library_operations': [], 'runtime_guards': [],
            'knobs': [], 'preservation_obligations': [], 'requirement_map': [],
            'correctness_check': {'kernel': FUNCTION, 'check': 'original-result'},
            'execution_witness': {'check': 'original-result'},
            'negative_controls': [{'id': name, 'kind': name, 'check': 'original-result'}
                for name in ('overlapping_pointer', 'double_claim', 'dropped_operand')]}
    return result


def contract_rows(contracts):
    need(set(contracts) == {79, 80}, 'closed positive80/negative79 pair required')
    return [{'id': contracts[value]['id'], 'sha256': digest(contracts[value]), 'expected_result': value}
            for value in (79, 80)]


def context_rules(premises, owner, expected):
    need(type(premises) is list and len(premises) == len(expected), 'complete owned context premise census required')
    rules = []
    for row, name in zip(premises, sorted(expected)):
        need(row == {'rule': name, 'statement': expected[name], 'owner': owner, 'record_assumption': True},
             'exact external owner/statement/record linkage required')
        rules.append({'id': 'whole_context_' + name.replace('-', '_'),
            'statement': row['statement'] + ' Owner: ' + owner + '.',
            'assumed': {'owner': owner}, 'record_assumption': True})
    return rules


def external_owned_rules(receipt, request, expected):
    exact(receipt, {'schema', 'owner', 'design_sha256', 'capture_observation_sha256',
        'physical_inputs_sha256', 'rules'}, 'external compiler/numeric premise receipt')
    need(receipt['schema'] == 'root-owned-checked-source-premises-1' and receipt['owner'] == request['owner']
         and receipt['design_sha256'] == request['design']['sha256']
         and receipt['capture_observation_sha256'] == request['capture']['observation']['sha256']
         and receipt['physical_inputs_sha256'] == digest(request['physical_inputs']),
         'external compiler/numeric receipt does not bind this exact selection')
    wanted = [{'id': name, 'statement': text, 'assumed': {'owner': request['owner']}, 'record_assumption': True}
              for name, text in expected.items()]
    need(receipt['rules'] == wanted, 'explicit complete compiler/numeric ownership required; builder cannot fill it')
    return copy.deepcopy(receipt['rules'])


def lowering_identity_without_probe(module, compiler_observation):
    """Same exact hash recipe; only two observed-runtime leaves are supplied.

    Never call locate()/runtime_identity(): both may probe a compiler. The root
    must have separately admitted the physical wrapper, driver, selected runtime
    descriptor and version. This reproduces an identity, not its observation.
    """
    exact(compiler_observation, {'schema', 'command', 'version', 'wrapper', 'driver', 'runtime_identity'}, 'compiler observation')
    need(compiler_observation['schema'] == 'root-selected-compiler-observation-1'
         and compiler_observation['command'] == [compiler_observation['wrapper']['path']]
         and compiler_observation['version'] == '22.1.8', 'exact absolute singleton compiler observation required')
    read(compiler_observation['wrapper']); read(compiler_observation['driver'], limit=256 * 1024 * 1024)
    runtime = compiler_observation['runtime_identity']
    need(type(runtime) is dict and runtime.get('command') == compiler_observation['command']
         and runtime.get('driver') == {key: compiler_observation['driver'][key] for key in ('path', 'sha256')}
         and 'unavailable' not in runtime, 'exact observed underlying-driver runtime descriptor required')
    tree = ast.parse(Path(module.__file__).read_text())
    nodes = [item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == 'identity']
    need(len(nodes) == 1, 'one pinned production lowering identity recipe required')
    function = nodes[0]; before = ast.dump(function, include_attributes=False)
    class Leaves(ast.NodeTransformer):
        count = [0, 0]
        def visit_Call(self, node):
            if ast.dump(node.func) == "Name(id='locate', ctx=Load())" and not node.args and not node.keywords:
                self.count[0] += 1
                return ast.copy_location(ast.Name(id='observed_tool', ctx=ast.Load()), node)
            if ast.unparse(node) == 'stdlib_provenance.runtime_identity(tool)':
                self.count[1] += 1
                return ast.copy_location(ast.Name(id='observed_runtime', ctx=ast.Load()), node)
            return self.generic_visit(node)
    transform = Leaves(); function = transform.visit(function)
    need(transform.count == [1, 1] and before != ast.dump(function, include_attributes=False),
         'only exact production probe/runtime leaves may be substituted')
    namespace = dict(module.__dict__)
    namespace.update(observed_tool=SimpleNamespace(command=compiler_observation['command'],
        version=compiler_observation['version'], missing=False), observed_runtime=compiler_observation['runtime_identity'])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), '<frozen-identity-no-probe>', 'exec'), namespace)
    return namespace['identity']()


def producer_snapshot(request):
    """Full normal swdb/vocab source census, physically checked before import."""
    snapshot = parse(read(request['producer_snapshot'], limit=4 * 1024 * 1024))
    exact(snapshot, {'schema', 'project', 'files'}, 'producer snapshot')
    project = Path(request['producer_project'])
    need(project.resolve(strict=True) == project and snapshot['project'] == str(project)
         and snapshot['schema'] == 'root-selected-normal-producer-source-census-1', 'separate selected producer root required')
    rows = snapshot['files']
    need(type(rows) is list and rows and [row['relative'] for row in rows] == sorted({row['relative'] for row in rows}),
         'unique complete producer source membership required')
    basis_raw = Path(__file__).with_name('normal-producer-basis-v1.json').read_bytes()
    need(sha(basis_raw) == BASIS_SHA, 'reviewed normal producer basis changed')
    basis = parse(basis_raw)
    indexed = {row['relative']: row for row in rows}
    need(all(indexed.get(row['relative']) == row for row in basis['files']),
         'selected producer differs from the reviewed source/physical-role proposal; version a successor')
    actual = []
    for directory in ('swdb', 'vocab'):
        for path in (project / directory).rglob('*'):
            metadata = path.lstat()
            need(not stat.S_ISLNK(metadata.st_mode), 'producer source links refused')
            if stat.S_ISDIR(metadata.st_mode):
                need(path.name != '__pycache__', 'producer bytecode cache refused')
            else:
                need(stat.S_ISREG(metadata.st_mode), 'producer source special file refused')
                actual.append(path.relative_to(project).as_posix())
    need(sorted(actual) == [row['relative'] for row in rows], 'producer source membership differs')
    for row in rows:
        exact(row, {'relative', 'bytes', 'sha256'}, 'producer file row')
        read({'path': str(project / relative(row['relative'])), 'bytes': row['bytes'], 'sha256': row['sha256']})
    return snapshot


def selected_modules(request):
    """Fixed normal imports only; caller-selected Python/runtime admission is external."""
    producer_snapshot(request)
    from swdb import dx100_checked_source as source
    from swdb import c_lowering, cbmc_translator, proof_setup
    need(Path(source.__file__).resolve() == Path(request['producer_project']) / 'swdb/dx100_checked_source.py',
         'imported source consumer is outside selected normal producer root')
    from swdb import paths
    need(str(Path(paths.HOME)) == request['original_project'], 'imported original project role differs')
    return source, c_lowering, cbmc_translator, proof_setup


def validate_request(request):
    exact(request, REQUEST_KEYS, 'profile selection')
    need(request['schema'] == 'dx100-public-profile-selection-1'
         and request['ingress'] == INGRESS and type(request['owner']) is str and request['owner'].strip()
         and type(request['choice_budget']) is int and 1 <= request['choice_budget'] <= 256,
         'closed profile/owner/budget and reviewed ingress required')
    library = LibraryRoot(Path(request['library_root']), Path(request['original_project']))
    need(library.root.is_absolute() and library.root.resolve(strict=True) == library.root,
         'canonical staging library root required')
    result = parse(portable(library, request['capture']['result']))
    require_capture(result)
    original_project_role(request['original_project'], parse(portable(library, request['capture']['observation'])))
    exact(request['physical_inputs'], {'compiler_driver', 'compiler_wrapper', 'device_configuration',
        'address_projection', 'numeric_runtime'}, 'complete physical role census')
    for row in request['physical_inputs'].values():
        read(row, limit=256 * 1024 * 1024)
    return library


def derive(request):
    """Recompute complete source expectations; return data, never owned receipts.

    This phase writes nothing and never launches a tool. The output's context
    request is deliberately not a context receipt. Root must supply its own
    exact context after reviewing allocation and numeric/mapping selections.
    """
    library = validate_request(request)
    source, _lowering, _translator, _setup = selected_modules(request)
    need(source.CAPTURE_KIND == request['capture']['kind'], 'role-normalized ingress successor not integrated')
    reads = source.Inputs(library)
    captured_path, original, tu, declarations, prepared, stream = source.complete_capture(request, reads, library.project)
    need(original == portable(library, request['proof_source']) and sha(original) == SOURCE_SHA,
         'exact captured first source and proof buffer required')
    design = parse(portable(library, request['design']))
    need(request['design']['sha256'] == source.contracts.DESIGN_SHA, 'exact reviewed design required')
    source_inventory(design, declarations)
    source.model.check_contract_inventory(design['calls'], declarations)
    abi = prepared['abi_observation']['abi']; source.binder.validate_abi(abi)
    owners = [node for node in source.statements.walk(tu) if node.get('kind') == 'FunctionDecl'
              and node.get('name') == FUNCTION and any(child.get('kind') == 'CompoundStmt' for child in node.get('inner', []))]
    need(len(owners) == 1, 'one original no-parameter source definition required')
    owner = owners[0]; caller = owner['mangledName']
    need(re.fullmatch(r'_Z[0-9]+whole_interface_source_fixturev', caller), 'original caller has unsupported parameters or ABI')
    bodies = [node for node in owner['inner'] if node.get('kind') == 'CompoundStmt']
    need(len(bodies) == 1, 'one exact original source body required')
    mapping = parse(read(request['mapping_receipt']))
    exact(mapping, {'schema', 'owner', 'source_sha256', 'capture_observation_sha256', 'physical_inputs_sha256', 'objects'}, 'owned mapping selection')
    need(mapping['schema'] == 'root-selected-first-source-object-mapping-1' and mapping['owner'] == request['owner']
         and mapping['source_sha256'] == SOURCE_SHA and mapping['capture_observation_sha256'] == request['capture']['observation']['sha256']
         and mapping['physical_inputs_sha256'] == digest(request['physical_inputs']), 'mapping root/source/capture/physical binding differs')
    need(type(mapping['objects']) is list and [row.get('name') for row in mapping['objects']] == ['data', 'limits'],
         'root must select the two exact ordinary mappings; no invented address allocation')
    objects, allocations = [], []
    for index, (name, dtype) in enumerate((('data', 0), ('limits', 1))):
        nodes = [node for node in source.statements.walk(owner) if node.get('kind') == 'VarDecl' and node.get('name') == name]
        need(len(nodes) == 1, 'one source-owned local array declaration required')
        node = nodes[0]; selected = mapping['objects'][index]
        exact(selected, {'name', 'object_id', 'guest_base', 'physical_base'}, 'root ordinary mapping')
        need(re.search(r'\[2\]$', node['type']['qualType']), 'exact two-element original local array required')
        object_pin = digest({'source_sha256': SOURCE_SHA, 'caller': caller, 'local_id': node['id'], 'declaration_sha256': digest(node)})
        objects.append({key: selected[key] for key in ('object_id', 'guest_base', 'physical_base')} |
                       {'extent': 2, 'dtype': dtype, 'source_pin': object_pin})
        allocations.append({'object_index': index, 'object_id': selected['object_id'], 'caller': caller,
            'local_id': node['id'], 'declaration_sha256': digest(node), 'declaration_range': list(source.binder._span(node)),
            'scope_end_offset': source.binder._span(bodies[0])[1], 'allocation_thread': 0,
            'allocation_origin': 'checked-original-automatic-declaration'})
    atlas = source.dispatch.prepare_atlas(objects)
    source.receiver.check_allocations(allocations, atlas, SOURCE_SHA, 1)
    stage = source.staging.Stager(source.binder.__dict__, source.dispatch.__dict__, tu, caller=caller,
        source_path=captured_path, source_text=original.decode('ascii'), declarations=declarations, abi=abi,
        atlas=atlas, live_local_ids=set())
    statements = source.statements.Lowerer(stage, prepared, assertion_header_pin=request['assertion_header']).lower()
    need(not any(node.get('kind') in {'ForStmt', 'WhileStmt', 'DoStmt'} for node in source.statements.walk(stage.owner)),
         'first source has no original loops; successor source profile required')
    components = {Path(row['path']).name: portable(library, row).decode('utf-8') for row in request['components']}
    need(len(request['components']) == len(components) == 4 and set(components) == set(COMPONENTS)
         and all(row['sha256'] == source.contracts.COMPONENTS[Path(row['path']).name] for row in request['components']),
         'four exact fixed backend components required')
    routes, instances = source.dispatch.render_routes(source.binder.__dict__, declarations, abi)
    need(len(instances) == 132, 'complete actual typed/arity instance census required')
    body = '\n'.join([source.model.hook_text(request['choice_budget']), *(components[name] for name in COMPONENTS),
        source.dispatch.render_direct_families(source.binder.__dict__, declarations), source.dispatch.render_pointer_bridge(atlas), routes]) + '\n'
    physical_components = [pin(library.resolve(row), portable(library, row)) for row in request['components']]
    assembly = {'entry': {**design['prospective_entry'], 'kind': 'proof_semantics', 'target': 'dx100-mmio',
        'contract_form': MODEL_KIND, 'calls': design['calls'], 'public_admission': False, 'source_preconditions_assumed': False,
        'model': {'sha256': sha(body.encode()), 'source_atlas_sha256': digest(atlas), 'source_inputs': physical_components},
        'harness_draws': {'object': 'dws_choice_table', 'scalar_type': 'uint32_t', 'count': request['choice_budget'],
            'independent': True, 'draw_before_source_unit': True}}, 'c_text': body, 'instances': instances, 'atlas': atlas}
    runtime = parse(read(request['runtime_receipt']))
    exact(runtime, {'schema', 'evidence_kind', 'owner', 'physical_inputs_sha256', 'numeric_flags'}, 'root runtime receipt')
    need(runtime['schema'] == 'whole-interface-runtime-selection-1'
         and runtime['evidence_kind'] == 'selected-configuration-and-owned-numeric-policies'
         and runtime['owner'] == request['owner'] and runtime['physical_inputs_sha256'] == digest(request['physical_inputs']),
         'independently selected runtime receipt required')
    exact(runtime['numeric_flags'], source.receiver.FLAGS, 'complete numeric runtime flags')
    for name, row in runtime['numeric_flags'].items():
        need(type(row) is dict and row == {'value': row.get('value'), 'policy': source.receiver.FLAGS[name]}
             and type(row['value']) is int and row['value'] in (0, 1), 'exact selected numeric flag required')
    context_request = {'schema': 'whole-interface-context-request-1', 'owner': request['owner'],
        'source_kind': SOURCE_KIND, 'model_kind': MODEL_KIND,
        'profile': 'fresh-program-exclusive-quiescent-modeled-trace-v1',
        'execution_mode': 'fresh-cxx-program-globals', 'modeled_threads': 1,
        'ordinary_allocations': allocations, 'numeric_flags': {name: {**row, 'runtime_receipt_sha256': request['runtime_receipt']['sha256']}
            for name, row in runtime['numeric_flags'].items()},
        'physical_inputs_sha256': digest(request['physical_inputs']), 'not_an_owned_context_receipt': True,
        'input_bindings': {'source': SOURCE_SHA, 'full_tu': request['capture']['compressed_tu']['sha256'],
            'abi_observation': request['capture']['abi']['sha256'], 'capture_receipt': request['capture']['observation']['sha256'],
            'model_assembly': digest(assembly), 'source_atlas': digest(atlas), 'statement_preparation': digest(statements),
            'runtime_receipt': request['runtime_receipt']['sha256'], 'assertion_header': request['assertion_header']['sha256']},
        'premises_for_root_review': [{'rule': name, 'statement': text} for name, text in sorted(source.receiver.PREMISES.items())]}
    reads.recheck(); producer_snapshot(request)
    return {'schema': 'whole-interface-profile-derivation-1', 'selection_sha256': digest(request),
        'caller_mangled': caller, 'prepared': prepared, 'abi': abi, 'atlas': atlas, 'assembly': assembly,
        'statements': statements, 'context_request': context_request,
        'source_inventory': declarations, 'stream_identities': stream,
        'expected_result_used_by_derivation': False}


def bind_globals(request, derived, context_receipt):
    """Data-only second phase after root supplies its exact context bytes."""
    need(derive(request) == derived, 'fresh derivation differs before context binding')
    context = parse(read(context_receipt))
    wanted = derived['context_request']
    need(context.get('bindings') == wanted['input_bindings']
         and context.get('ordinary_allocations') == wanted['ordinary_allocations']
         and context.get('numeric_flags') == wanted['numeric_flags']
         and context.get('owner') == request['owner'], 'root context does not bind exact derived inputs')
    library = validate_request(request)
    source, _lowering, _translator, _setup = selected_modules(request)
    reads = source.Inputs(library)
    _path, _original, tu, declarations, _prepared, _stream = source.complete_capture(request, reads, library.project)
    observed = source.globals_observer.observe_globals(source.binder.__dict__, tu, declarations,
        execution_mode='fresh-cxx-program-globals', program_context_receipt_sha256=context_receipt['sha256'])
    reads.recheck(); producer_snapshot(request)
    return observed


def build_method(base, identities, producer_manifest):
    need(base.get('kind') == 'method_version' and base.get('evidence_kind') == 'execution',
         'root-selected actual execution method required; fixture identity forbidden')
    method = copy.deepcopy(base)
    method.update(id=METHOD, status='frozen', sequence=base['sequence'] + 1, created='2026-10-16')
    method['description'] = 'Checked original first-source 79/80 pair; concrete new0.2 bodies and exact fresh producer manifest.'
    method['checks'].update(identities['setup'])
    method['c_lowering']['naming_rules'] = identities['lowering']['naming_rules']
    method['c_lowering']['translators'] = [identities['lowering']['c_lowering'], identities['translator'],
        {'id': 'swdb-dx100-whole-checked-producers-1', 'sha256': digest(producer_manifest)}]
    return method


def assemble(request, derived, *, context_receipt, receiver_policy):
    """Finish only with exact independently supplied root receipts already on disk.

    Never create, alter, sign, or fill an owned context/runtime/mapping receipt.
    Root stages deterministic expectations first, then selects its exact context
    and receiver policy. The entire derivation is freshly recomputed here.
    """
    need(derive(request) == derived, 'fresh complete source derivation differs')
    library = validate_request(request)
    source, lowering, translator, setup = selected_modules(request)
    reads = source.Inputs(library)
    selected_receiver = parse(read(receiver_policy))
    need(selected_receiver['context_receipt'] == context_receipt
         and selected_receiver['selection_owner'] == request['owner'], 'root-selected receiver/context linkage differs')
    context = parse(read(context_receipt))
    need(context['ordinary_allocations'] == derived['context_request']['ordinary_allocations']
         and context['numeric_flags'] == derived['context_request']['numeric_flags'], 'root context differs from derived local origin/runtime')
    for name, value in (('source_atlas', derived['atlas']), ('model_assembly', derived['assembly']),
                        ('statement_preparation', derived['statements'])):
        need(read(selected_receiver['inputs'][name]) == canonical(value), 'staged derived expectation differs')
    need(selected_receiver['inputs']['runtime_receipt'] == request['runtime_receipt']
         and selected_receiver['physical_inputs'] == request['physical_inputs']
         and selected_receiver['full_tu_canonical_sha256'] == derived['prepared']['normalized_full_tu_sha256'],
         'selected receiver physical/runtime/TU differs')
    captured_path, original, tu, declarations, prepared, _stream = source.complete_capture(request, reads, library.project)
    observed = source.globals_observer.observe_globals(source.binder.__dict__, tu, declarations,
        execution_mode='fresh-cxx-program-globals', program_context_receipt_sha256=context_receipt['sha256'])
    need(read(selected_receiver['inputs']['source_globals']) == canonical(observed),
         'root must stage the exact twelve-global observation bound to its context')
    need(selected_receiver['inputs']['source'] == pin(captured_path, original)
         and selected_receiver['inputs']['full_tu']['sha256'] == request['capture']['compressed_tu']['sha256']
         and selected_receiver['inputs']['abi_observation']['sha256'] == request['capture']['abi']['sha256']
         and selected_receiver['inputs']['capture_receipt']['sha256'] == request['capture']['observation']['sha256']
         and selected_receiver['inputs']['assertion_header'] == request['assertion_header'],
         'receiver source/storage/ABI/capture/assertion selection differs')
    receiver = source.receiver.prepare(source.receiver.OwnedSelection(source.receiver.Pin.parse(receiver_policy)))
    rules = context_rules(context['premises'], request['owner'], source.receiver.PREMISES)
    producer_files = {}
    modules = (source.compiler, source.codec, source.model, source.receiver, source.staging, source.dispatch,
        source.globals_observer, source.statements, source.binder, source, source.contracts)
    for module in modules:
        raw = Path(module.__file__).read_bytes(); producer_files[Path(module.__file__).name] = pin(Path(module.__file__), raw)
    for name in source.ROUTE_PRODUCERS:
        path = Path(source.__file__).with_name(name); producer_files[name] = pin(path, path.read_bytes())
    for name in ('runtime_projection_v2.py', 'receiver-state-draws-v2/receiver_state_draws_v2.py'):
        path = Path(source.__file__).parent / '_dx100_whole' / name; producer_files[name] = pin(path, path.read_bytes())
    manifest = {'schema': 'swdb-dx100-whole-producers-1', 'files': producer_files}
    # proof_setup.identity uses the selected original project's vocabulary,
    # whereas Python producer modules live in the separate producer checkout.
    for name in ('proof_failure_classes.yaml', 'proof_subject_kinds.yaml'):
        path = library.project / 'vocab' / name
        reads.absolute(pin(path, path.read_bytes()))
    identities = {'lowering': lowering_identity_without_probe(lowering, parse(read(request['compiler_observation']))),
        'translator': translator.identity(), 'setup': setup.identity()}
    method = build_method(parse(read(request['method_seed'])), identities, manifest)
    contracts = unit_contracts(request['proof_source']); rows = contract_rows(contracts)
    # No output references its own bytes. Contracts -> policy -> semantics;
    # producer manifest -> method. Context -> globals -> receiver is separate.
    def ref(name, value):
        return {'root': 'library', 'path': 'proof_semantics/dx100_whole/' + name, 'sha256': digest(value)}
    receiver_ref = {'root': 'library', 'path': str(Path(receiver_policy['path']).relative_to(library.root)),
                    'sha256': receiver_policy['sha256']}
    policy = {'kind': SOURCE_KIND, 'schema': 'dx100-whole-fixed-source-policy-1', 'function': FUNCTION,
        'caller_mangled': derived['caller_mangled'], 'defines': ['NUM_CORES=4', 'TILE_SIZE=16384'],
        'choice_budget': request['choice_budget'], 'thread': 0, 'buffer_projection': source.BUFFER_PROJECTION,
        'proof_source': request['proof_source'], 'capture': request['capture'], 'receiver_selection': receiver_ref,
        'expected': {name: ref(name + '.json', value) for name, value in
            (('atlas', derived['atlas']), ('globals', observed), ('statements', derived['statements']), ('assembly', derived['assembly']))},
        'producer_manifest': ref('producers.json', manifest), 'native_projection': {
            'kind': 'dx100-whole-source-preserving-cxx-v2',
            'producer': producer_files['runtime_projection_v2.py'], 'assertion_header': request['assertion_header']},
        'frame': FRAME, 'unit_contracts': rows, 'source_loop_bound': 1, 'helper_loop_bound': 513}
    policy['expected']['receiver_binding_sha256'] = sha(receiver.binding_json)
    design = parse(portable(library, request['design']))
    header_rows = [{'root': 'project', 'path': 'apps/dx100/benchmarks/API/' + name, 'sha256': expected}
                   for name, expected in sorted(source.contracts.HEADERS.items())]
    declaration_rows = []
    for row in header_rows:
        declaration_rows += source.contracts.declarations(portable(library, row), Path(row['path']).name)
    trust = [{'id': name, 'statement': text, 'assumed': {'owner': 'Eric'}, 'record_assumption': True}
             for name, text in source.contracts.TRUST.items()]
    owned = external_owned_rules(parse(read(request['owned_rules_receipt'])), request, source.contracts.OWNED)
    entry = {'id': 'semantics.dx100_bfs_0_2', 'kind': 'proof_semantics', 'formal_frame': 1,
        'version': '0.2', 'sequence': 2, 'target': 'dx100-mmio', 'hardware_interface': design['prospective_entry']['hardware_interface'],
        'description': 'First exact original-source checked concrete model; owned compiler/MMIO/runtime/context premises.',
        'provenance': {'origin': {'probata_ticket': '28', 'created': '2026-10-16 ET'}},
        'contract_form': MODEL_KIND, 'checked_body': {'design': request['design'], 'components': request['components'],
            'source_policy': ref('source-policy.json', policy), 'choice_budget': request['choice_budget']},
        'calls': design['calls'], 'declaration_inventory': {'sources': header_rows,
            'declarations': sorted(declaration_rows, key=lambda row: (row['file'], row['line'], row['name'], row['declaration']))},
        'clauses': [], 'rules': trust + owned + rules}
    source.bind_context_rules(entry, context['premises'])
    outputs = {'methods/' + METHOD.removeprefix('method.') + '.yaml': canonical(method),
        'proof_semantics/dx100_bfs_0_2.yaml': canonical(entry)}
    for value, contract in contracts.items():
        outputs['rewrite_contracts/dx100_whole_source_' + str(value) + '.yaml'] = canonical(contract)
    for name, value in (('source-policy', policy), ('producers', manifest), ('atlas', derived['atlas']),
                        ('globals', observed), ('statements', derived['statements']), ('assembly', derived['assembly'])):
        outputs['proof_semantics/dx100_whole/' + name + '.json'] = canonical(value)
    reads.recheck(); producer_snapshot(request)
    return {'files': outputs, 'contracts': rows, 'semantics_content_sha256': digest(entry),
        'semantics_physical_sha256': sha(outputs['proof_semantics/dx100_bfs_0_2.yaml']),
        'method_content_sha256': digest(method), 'producer_manifest_sha256': digest(manifest),
        'scientific_outcomes': 'pending root admission and actual public pair; no proof result inferred'}


def write_new_files(root, files):
    """Explicit output operation: exclusive create; never replace a staged input."""
    root = Path(root)
    need(root.is_absolute() and root.resolve(strict=True) == root, 'canonical root-created staging directory required')
    for name, raw in files.items():
        relative(name); need(type(raw) is bytes, 'exact emitted bytes required')
        target = root / name
        need(not target.exists() and not target.is_symlink(), 'profile output already exists')
        target.parent.mkdir(parents=True, exist_ok=True)
        need(target.parent.resolve(strict=True) == target.parent, 'profile output directory alias refused')
        with target.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return [{'relative': name, 'bytes': len(raw), 'sha256': sha(raw)} for name, raw in sorted(files.items())]
