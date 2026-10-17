"""2026-10-16 ET. Derive the inert first-pair builder for coherent V4."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OUT = HERE / 'profile'


def replace(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new, 1)


def function(text, name, replacement):
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == name)
    return replace(text, ast.get_source_segment(text, node), replacement.strip())


CAPTURE_ROLES = '''def capture_roles(capture):
    """Closed role projection only; the real complete ingress grants no shortcut."""
    need(type(capture) is dict, 'typed capture selection required')
    if capture.get('kind') == 'lossless-complete-original-tu-v1':
        return {'storage': capture['compressed_tu'], 'observation': capture['observation'],
                'raw_abi': capture['abi'], 'result': capture['result'], 'normalized': False}
    need(capture.get('kind') == 'complete-original-tu-paired-type-gzip-2', 'unknown complete capture transport')
    exact(capture, {'kind', 'original', 'transform', 'prepared'}, 'closed normalized capture')
    exact(capture['original'], {'policy', 'result', 'observation', 'runtime_before', 'runtime_after',
        'zlib_before', 'zlib_after', 'zlib_runtime', 'gzip_receipt', 'compressed_tu', 'abi', 'probe', 'source', 'source_after'},
        'closed original capture roles')
    exact(capture['transform'], {'controller', 'command', 'bootstrap', 'policy', 'result', 'transport', 'inverse',
        'manifest', 'normalized_gzip', 'complete_census', 'execution', 'stdout', 'stderr'}, 'closed transform roles')
    return {'storage': capture['transform']['normalized_gzip'], 'observation': capture['original']['observation'],
            'raw_abi': capture['original']['abi'], 'result': capture['transform']['result'], 'normalized': True}


def selected(library, row):
    if type(row) is dict and set(row) == {'root', 'path', 'sha256'}:
        return portable(library, row)
    return read(row)


def read_complete_capture(request, reads, project):
    from swdb._dx100_whole import normalized_capture_ingress_v2 as ingress
    return ingress.complete_capture(request, reads, project)


def check_receiver_compiler_projection(receiver, capture, prepared, captured_path, original, assertion_header):
    """Raw ABI AST and the derived ABI observation are different physical roles."""
    roles = capture_roles(capture)
    need(receiver['inputs']['source'] == pin(captured_path, original)
         and receiver['inputs']['full_tu'] == roles['storage']
         and receiver['inputs']['capture_receipt'] == roles['observation']
         and receiver['inputs']['assertion_header'] == assertion_header,
         'receiver exact source/storage/original compiler observation/assertion selection differs')
    observation = prepared['abi_observation']
    need(read(receiver['inputs']['abi_observation']) == canonical(observation)
         and receiver['inputs']['abi_observation']['sha256'] == digest(observation),
         'receiver must bind the derived ABI observation, not the original ABI AST')
'''

VALIDATE = '''def validate_request(request):
    exact(request, REQUEST_KEYS, 'profile selection')
    need(request['schema'] == 'dx100-public-profile-selection-1'
         and request['ingress'] == INGRESS and type(request['owner']) is str and request['owner'].strip()
         and type(request['choice_budget']) is int and 1 <= request['choice_budget'] <= 256,
         'closed profile/owner/budget and reviewed ingress required')
    library = LibraryRoot(Path(request['library_root']), Path(request['original_project']))
    need(library.root.is_absolute() and library.root.resolve(strict=True) == library.root,
         'canonical staging library root required')
    roles = capture_roles(request['capture'])
    if roles['normalized']:
        selected_modules(request)
        from swdb._dx100_whole import normalized_capture_ingress_v2 as ingress
        original, transform = request['capture']['original'], request['capture']['transform']
        ingress.fixed_pin(original['policy'], ingress.ORIGINAL_POLICY_SHA, 'exact original policy required')
        ingress.fixed_pin(original['result'], ingress.ORIGINAL_RESULT_SHA, 'exact original refusal required')
        ingress.fixed_pin(transform['result'], ingress.TRANSFORM_RESULT_SHA, 'exact normalized result required')
        ingress.fixed_pin(transform['execution'], ingress.ROOT_EXECUTION_SHA, 'exact settled root observation required')
        ingress.original_refusal(parse(selected(library, original['result'])))
        ingress.transform_gate(parse(selected(library, transform['result'])))
        ingress.execution_gate(parse(selected(library, transform['execution'])), transform)
    else:
        require_capture(parse(selected(library, roles['result'])))
    original_project_role(request['original_project'], parse(selected(library, roles['observation'])))
    exact(request['physical_inputs'], {'compiler_driver', 'compiler_wrapper', 'device_configuration',
        'address_projection', 'numeric_runtime'}, 'complete physical role census')
    for row in request['physical_inputs'].values():
        read(row, limit=256 * 1024 * 1024)
    return library
'''

ATTACH_REGISTRY = '''def attach_registry(completed, library_root):
    """Close all four structural rows; unprepared memory selection always refuses.

    This emits explicit unready data, never a prepared or owned receiver receipt.
    The existing registry remains structural and retains type-sensitive shared
    memory capture equality. The first policy/contract/model bytes are untouched.
    """
    from swdb._dx100_whole import unit_policy_registry_v2 as registry
    root = Path(library_root)
    need(root.is_absolute() and root.resolve(strict=True) == root and root.is_dir(), 'canonical selected library root required')
    memory_file = root / 'proof_units/same_thread_memory_v1.cpp'
    memory_pin = {'path': str(memory_file), 'bytes': 3258, 'sha256': registry.MEMORY_SHA}
    read(memory_pin)
    memory_source = {'root': 'library', 'path': 'proof_units/same_thread_memory_v1.cpp', 'sha256': registry.MEMORY_SHA}
    outputs = dict(completed['files'])
    first_policy_name = 'proof_semantics/dx100_whole/source-policy.json'
    first_policy_raw = outputs[first_policy_name]; first_policy = parse(first_policy_raw)
    need(first_policy['function'] == FUNCTION and first_policy['proof_source']['sha256'] == SOURCE_SHA,
         'exact completed first-source policy required')
    contracts = {parse(raw)['id']: raw for name, raw in outputs.items() if name.startswith('rewrite_contracts/')}
    need(len(contracts) == 2 and all(row['id'] in contracts for row in first_policy['unit_contracts']),
         'both unchanged first-source contracts required')
    references = [{'root': 'library', 'path': first_policy_name, 'sha256': sha(first_policy_raw)}]
    policies = {sha(first_policy_raw): first_policy_raw}
    unready = {'schema': 'unprepared-memory-source-profile-1', 'source_sha256': registry.MEMORY_SHA,
        'state': 'complete-source-observation-and-owned-receiver-pending',
        'scope': 'explicit refusal data; no prepared AST, receiver/context/mapping or scientific acceptance'}
    unready_name = 'proof_semantics/dx100_whole/memory-unready.json'
    outputs[unready_name] = canonical(unready)
    unready_ref = {'root': 'library', 'path': unready_name, 'sha256': sha(outputs[unready_name])}
    capture = {'kind': 'unsupported-unprepared-memory-profile-1', 'source_sha256': registry.MEMORY_SHA,
        'state': 'complete-source-observation-and-owned-receiver-pending'}
    for function, source_sha, expected in registry.FUNCTIONS[1:]:
        rows = []
        for value, contract_id in expected:
            contract = copy.deepcopy(unit_contracts(memory_source)[80])
            contract['id'] = contract_id; contract['proof_unit']['function'] = function
            contract['clauses'][1]['statement'] = 'Original scalar result equals ' + str(value) + '.'
            contract['clauses'][1]['acsl']['text'] = r'ensures \\result == ' + str(value) + ';'
            raw = canonical(contract); contracts[contract_id] = raw
            outputs['rewrite_contracts/' + contract_id.removeprefix('contract.') + '.yaml'] = raw
            rows.append({'id': contract_id, 'sha256': sha(raw), 'expected_result': value})
        policy = {'kind': SOURCE_KIND, 'schema': 'dx100-whole-exact-memory-source-policy-1', 'function': function,
            'caller_mangled': '_Z' + str(len(function)) + function + 'v', 'defines': list(first_policy['defines']),
            'choice_budget': first_policy['choice_budget'], 'thread': 0,
            'buffer_projection': 'exact-three-root-cxx-view-with-captured-origin-v1', 'proof_source': memory_source,
            'capture': dict(capture), 'receiver_selection': unready_ref,
            'expected': {'state': 'unprepared-no-source-certificate'}, 'producer_manifest': first_policy['producer_manifest'],
            'native_projection': {'state': 'unprepared-original-source-view'}, 'frame': FRAME, 'unit_contracts': rows,
            'source_loop_bound': 1, 'helper_loop_bound': 513}
        raw = canonical(policy); name = 'proof_semantics/dx100_whole/' + function + '-unready-policy.json'
        outputs[name] = raw; references.append({'root': 'library', 'path': name, 'sha256': sha(raw)}); policies[sha(raw)] = raw
    assembled = registry.assemble(references, policies, contracts)
    registry_name = 'proof_semantics/dx100_whole/source-unit-registry.json'
    outputs[registry_name] = assembled['registry_bytes']
    entry_name = 'proof_semantics/dx100_bfs_0_2.yaml'; entry = parse(outputs[entry_name])
    entry['checked_body']['source_policy'] = {'root': 'library', 'path': registry_name, 'sha256': assembled['registry_sha256']}
    entry['description'] = 'Exact first-source79/80 with closed structural memory rows that refuse until actual preparation and owned context exist.'
    outputs[entry_name] = canonical(entry)
    need(outputs[first_policy_name] == first_policy_raw, 'ready first-source policy bytes changed while attaching registry')
    read(memory_pin)
    return {**completed, 'files': outputs, 'semantics_content_sha256': digest(entry),
        'semantics_physical_sha256': sha(outputs[entry_name]), 'unit_registry': entry['checked_body']['source_policy'],
        'unready_memory_functions': [row[0] for row in registry.FUNCTIONS[1:]], 'memory_buffer': memory_pin,
        'unready_data_grants_receiver_or_source_admission': False}
'''


def main():
    OUT.mkdir(exist_ok=True)
    # Normal source identities are fixed before this builder/method is emitted;
    # the builder itself is not in this manifest, so no hash cycle is introduced.
    files = []
    for path in sorted((HERE / 'proposed/swdb').rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            files.append({'relative': 'swdb/' + path.relative_to(HERE / 'proposed/swdb').as_posix(),
                          'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    for name in ('__init__.py', 'wp_adapter.py', 'wp_pointer_bounds.py', 'standard_vector_member_view.py'):
        path = WHOLE.parents[3] / 'swdb' / name; raw = path.read_bytes()
        files.append({'relative': 'swdb/' + name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    files.sort(key=lambda row: row['relative'])
    assert len({row['relative'] for row in files}) == len(files)
    basis = {'date': '2026-10-16 ET', 'schema': 'coherent-checked-source-producer-basis-4',
        'root_base_commit': '1c45737f6cff9b43731d8da530be869a7e5d745e', 'files': files}
    basis_raw = (json.dumps(basis, sort_keys=True, indent=2) + '\n').encode()
    (OUT / 'normal-producer-basis-v4.json').write_bytes(basis_raw)
    text = (WHOLE / 'public-profile-builder-v2/profile_builder_v2.py').read_text()
    text = text.replace('The complete-capture ingress remains the reviewed production-route V3 boundary;\na role-normalized transport requires a separately reviewed version of this\nbuilder and route.', 'The complete-capture ingress is the separately reviewed normalized V2 boundary\ncomposed in proposed production-route V4. Original and derived transport roles\nremain distinct, and the current first-stream gate cannot admit memory source.')
    text = text.replace('normal-producer-basis-v1.json', 'normal-producer-basis-v4.json')
    text = replace(text, "BASIS_SHA = '66bacdc09fd1996cebe3f9d806101ae010cb058571158a9a1522a14cd7c9784f'",
        "BASIS_SHA = '" + hashlib.sha256(basis_raw).hexdigest() + "'")
    text = replace(text, "INGRESS = 'reviewed-production-route-v3-complete-capture'",
        "INGRESS = 'reviewed-production-route-v4-normalized-complete-capture'")
    text = text.replace('reviewed V3', 'coherent proposed V4')
    text = text.replace("request['capture']['observation']", "capture_roles(request['capture'])['observation']")
    text = text.replace("request['capture']['compressed_tu']", "capture_roles(request['capture'])['storage']")
    text = text.replace("request['capture']['abi']", "capture_roles(request['capture'])['raw_abi']")
    text = function(text, 'validate_request', VALIDATE + '\n\n' + CAPTURE_ROLES)
    text = replace(text, "    need(source.CAPTURE_KIND == request['capture']['kind'], 'role-normalized ingress successor not integrated')\n", '')
    text = text.replace('source.complete_capture(request, reads, library.project)', 'read_complete_capture(request, reads, library.project)')
    text = replace(text, "    body = '\\n'.join([source.model.hook_text(request['choice_budget']), *(components[name] for name in COMPONENTS),",
        "    resource_profile = source.resource_selection(SOURCE_SHA, FUNCTION,\n"
        "        {name: sha(components[name].encode('utf-8')) for name in COMPONENTS})\n"
        "    resource_text = source.resources.prefix(resource_profile)\n"
        "    body = '\\n'.join([source.model.hook_text(request['choice_budget']) + resource_text, *(components[name] for name in COMPONENTS),")
    text = replace(text, "'model': {'sha256': sha(body.encode()), 'source_atlas_sha256': digest(atlas), 'source_inputs': physical_components},",
        "'model': {'sha256': sha(body.encode()), 'source_atlas_sha256': digest(atlas), 'source_inputs': physical_components,\n"
        "                  'resource_profile': resource_profile},")
    text = replace(text, "'abi_observation': capture_roles(request['capture'])['raw_abi']['sha256'], 'capture_receipt': capture_roles(request['capture'])['observation']['sha256'],",
        "'abi_observation': digest(prepared['abi_observation']), 'capture_receipt': capture_roles(request['capture'])['observation']['sha256'],")
    old = "    need(selected_receiver['inputs']['source'] == pin(captured_path, original)\n         and selected_receiver['inputs']['full_tu']['sha256'] == capture_roles(request['capture'])['storage']['sha256']\n         and selected_receiver['inputs']['abi_observation']['sha256'] == capture_roles(request['capture'])['raw_abi']['sha256']\n         and selected_receiver['inputs']['capture_receipt']['sha256'] == capture_roles(request['capture'])['observation']['sha256']\n         and selected_receiver['inputs']['assertion_header'] == request['assertion_header'],\n         'receiver source/storage/ABI/capture/assertion selection differs')"
    text = replace(text, old, "    check_receiver_compiler_projection(selected_receiver, request['capture'], prepared,\n        captured_path, original, request['assertion_header'])")
    start = text.index('    producer_files = {}\n', text.index('def assemble('))
    stop = text.index('    manifest = ', start)
    text = text[:start] + "    producer_files = {name: pin(path, path.read_bytes()) for name, path in source.producer_paths().items()}\n" + text[stop:]
    text = text.replace("'dx100-whole-source-preserving-cxx-v2'", "'dx100-whole-source-preserving-cxx-v3'")
    text = text.replace("producer_files['runtime_projection_v2.py']", "producer_files['runtime_projection_v3.py']")
    start = text.index("    return {'files': outputs, 'contracts': rows, 'semantics_content_sha256': digest(entry),")
    end = text.index('\n\n\ndef write_new_files', start)
    original_return = text[start:end]
    text = text[:start] + original_return.replace("return {'files'", "return attach_registry({'files'", 1).removesuffix('}') + '}, library.root)' + text[end:]
    text = text.replace('def write_new_files(root, files):', ATTACH_REGISTRY + '\n\n\ndef write_new_files(root, files):', 1)
    ast.parse(text)
    (OUT / 'profile_builder_v3.py').write_text(text)
    preparer = (WHOLE / 'public-profile-builder-v1/profile_prepare_v1.py').read_text()
    preparer = preparer.replace('profile_builder_v1.py', 'profile_builder_v3.py').replace('selected_profile_builder_v1', 'selected_profile_builder_v3')
    preparer = replace(preparer, "BUILDER_SHA = 'f594d5c23bef2bcda7a97c6a214601913425d7a24f2575985102eefe0b0391c2'",
        "BUILDER_SHA = '" + hashlib.sha256(text.encode()).hexdigest() + "'")
    preparer = replace(preparer, "            'derived-abi-summary.json': builder.canonical(derived['abi']),",
        "            'derived-abi-summary.json': builder.canonical(derived['abi']),\n"
        "            'abi-observation.json': builder.canonical(derived['prepared']['abi_observation']),\n"
        "            'whole-unit-preparation.json': builder.canonical(derived['prepared']),")
    (OUT / 'profile_prepare_v3.py').write_text(preparer)
    (OUT / 'pair_plan_v2.py').write_bytes((WHOLE / 'public-profile-planner-v2/pair_plan_v2.py').read_bytes())
    print(json.dumps({'builder_bytes': len(text.encode()), 'normal_basis_files': len(files),
                      'public_or_owned_admission': False}))


if __name__ == '__main__':
    main()
