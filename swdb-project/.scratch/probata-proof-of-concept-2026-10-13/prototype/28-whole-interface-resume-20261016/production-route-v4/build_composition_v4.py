"""2026-10-16 ET. Compose owned V4 draft; never write shared production.

The normalized-ingress module is supplied by a separately reviewed packet before
final freeze. Until then this source draft is deliberately not runnable/admitted.
"""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
V3 = WHOLE / 'production-route-v3/proposed/swdb'
OUT = HERE / 'proposed/swdb'


def replace(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new, 1)


def function(text, name, replacement):
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == name)
    return replace(text, ast.get_source_segment(text, node), replacement.strip())


POLICY = '''def source_policy(selection, reads):
    need(type(selection) is SourceSelection and selection.method_id == METHOD, 'separate checked-source method required')
    from swdb.library import Library
    physical_library = Library(selection.library.root)
    entry = physical_library.get(selection.entry_id)
    need(not physical_library.problems and entry == selection.library.get(selection.entry_id),
         'selected entry/library bytes changed after selection')
    normalized = contracts.policy(physical_library, entry)
    raw = reads.portable(normalized['source_policy'])
    policy = contracts.document(raw)
    if type(policy) is dict and policy.get('schema') == unit_registry.SCHEMA:
        need(type(selection.proof_unit_json) is bytes and selection.proof_unit_json,
             'registered structural source/function coordinates required')
        proof_unit = contracts.document(selection.proof_unit_json)
        selected, policy = registry_consumer.baseline(physical_library, reads,
            normalized['source_policy'], proof_unit)
        normalized = {**normalized, 'unit_registry': normalized['source_policy'], 'source_policy': selected}
    else:
        need(type(policy) is dict and policy.get('function') == FUNCTION
             and policy.get('schema') == 'dx100-whole-fixed-source-policy-1',
             'memory source policies require the complete closed unit registry')
    definition = [row for row in unit_registry.FUNCTIONS if row[0] == policy.get('function')]
    need(len(definition) == 1, 'unknown source policy function')
    unit_registry.portable(policy.get('proof_source'))
    need(policy['proof_source']['sha256'] == definition[0][1], 'exact registered source bytes required')
    unit_registry.check_policy(policy, {'source': policy.get('proof_source'),
        'contracts': policy.get('unit_contracts')}, definition[0], normalized['choice_budget'])
    if selection.proof_unit_json:
        need(contracts.document(selection.proof_unit_json) ==
             {'source': policy['proof_source'], 'function': policy['function']},
             'structural selection differs from the exact per-unit policy')
    reads.recheck()
    return entry, normalized, policy
'''

SELECT = '''def select_baseline(library, proof_unit):
    """Structural source/function lookup; actual contract selection remains separate."""
    if type(proof_unit) is not dict or proof_unit.get('function') not in UNIT_FUNCTIONS:
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
    entry_id, _data = selected[0]
    from swdb import paths
    selection = SourceSelection(library, entry_id, Path(paths.HOME).resolve(strict=True), METHOD, canonical(proof_unit))
    reads = Inputs(library)
    _entry, _normalized, policy = source_policy(selection, reads)
    need(proof_unit == {'source': policy['proof_source'], 'function': policy['function']},
         'exact structural source/function selection required')
    reads.recheck()
    return selection
'''


PRODUCERS = '''def producer_paths():
    """Actual fixed imported/read/exec consumers, including transport and aliases."""
    from swdb._dx100_whole import normalized_capture_ingress_v2 as ingress
    from swdb._dx100_whole import closed_python_surface, role_normalized_gzip_v2, lossless_gzip_v2
    from swdb._dx100_whole import runtime_projection_v3, normalized_compiler_adapter_v1
    modules = (compiler, codec, model, receiver, memory_receiver, staging, dispatch,
        globals_observer, statements, binder, unit_registry, memory_selection, memory_runtime, resources,
        ingress, closed_python_surface, role_normalized_gzip_v2, lossless_gzip_v2, runtime_projection_v3, normalized_compiler_adapter_v1)
    rows = [(Path(module.__file__).name, Path(module.__file__)) for module in modules]
    need(len({name for name, _path in rows}) == len(rows), 'producer module names must be unique')
    paths = dict(rows)
    fixed = {
        'dx100_checked_source.py': Path(__file__), 'dx100_whole_checked.py': Path(contracts.__file__),
        'package/__init__.py': Path(__file__).with_name('__init__.py'),
        '_dx100_whole/__init__.py': Path(__file__).parent / '_dx100_whole/__init__.py',
        'runtime_projection_v2.py': Path(__file__).parent / '_dx100_whole/runtime_projection_v2.py',
        'receiver-state-draws-v2/receiver_state_draws_v2.py':
            Path(__file__).parent / '_dx100_whole/receiver-state-draws-v2/receiver_state_draws_v2.py',
        'source-memory-selection-v1/source_memory_selection_v1.py':
            Path(__file__).parent / '_dx100_whole/source-memory-selection-v1/source_memory_selection_v1.py',
        'receiver-memory-v1/receiver_memory_v1.py':
            Path(__file__).parent / '_dx100_whole/receiver-memory-v1/receiver_memory_v1.py'}
    fixed.update({name: Path(__file__).with_name(name) for name in ROUTE_PRODUCERS})
    need(not set(paths) & set(fixed), 'producer roles cannot overwrite imported module identities')
    return {**paths, **fixed}


def producer_closure(policy, reads):
    manifest = reads.document(policy['producer_manifest'])
    paths = producer_paths()
    need(type(manifest) is dict and set(manifest) == {'schema', 'files'}
         and manifest['schema'] == 'swdb-dx100-whole-producers-1' and set(manifest['files']) == set(paths),
         'exact complete promoted source/registry/runtime/transport producer closure required')
    for name, path in paths.items():
        row = manifest['files'][name]
        need(row['path'] == str(path), 'producer manifest must bind the actual fixed physical consumer')
        reads.absolute(row)
'''

CAPTURE_INPUTS = '''def capture_inputs(capture):
    """Metadata roles only; complete_capture must independently validate them."""
    need(type(capture) is dict, 'typed complete capture selection required')
    if capture.get('kind') == CAPTURE_KIND:
        return capture['compressed_tu'], capture['observation']
    from swdb._dx100_whole import normalized_capture_ingress_v2 as ingress
    need(capture.get('kind') == ingress.KIND, 'unknown complete capture input roles')
    return capture['transform']['normalized_gzip'], capture['original']['observation']
'''


def source(text):
    text = replace(text, 'from swdb import dx100_whole_checked as contracts',
        'from swdb import dx100_whole_checked as contracts\nfrom swdb import dx100_checked_registry as registry_consumer\n'
        'from swdb._dx100_whole import unit_policy_registry_v2 as unit_registry\n'
        'from swdb._dx100_whole import receiver_memory_v1 as memory_receiver\n'
        'from swdb._dx100_whole import source_memory_selection_v1 as memory_selection\n'
        'from swdb._dx100_whole import runtime_projection_v4 as memory_runtime\n'
        'from swdb._dx100_whole import resource_profile_v2 as resources')
    text = replace(text, 'Only the fixed no-parameter value fixture is supported.',
        'Only the fixed registered no-parameter source units are supported; each requires its own complete capture.')
    text = replace(text, "FUNCTION = 'whole_interface_source_fixture'",
        "FUNCTION = 'whole_interface_source_fixture'\nUNIT_FUNCTIONS = tuple(row[0] for row in unit_registry.FUNCTIONS)")
    text = replace(text, '    method_id: str\n', '    method_id: str\n    proof_unit_json: bytes = b\'\'\n')
    text = replace(text, "'proof_semantics.py', 'proof_setup.py', 'dx100_checked_adapter.py', 'dx100_checked_native.py')",
        "'proof_semantics.py', 'proof_setup.py', 'dx100_checked_adapter.py', 'dx100_checked_native.py',\n"
        "                   'dx100_checked_registry.py')")
    text = function(text, 'source_policy', POLICY)
    text = function(text, 'select_baseline', SELECT)
    text = function(text, 'producer_closure', PRODUCERS + '\n\n' + CAPTURE_INPUTS)
    text = replace(text, "proof_unit.get('function') != FUNCTION", "proof_unit.get('function') not in UNIT_FUNCTIONS")
    text = replace(text, "need(function == FUNCTION and tuple(sorted(defines)) == tuple(policy['defines']), 'unsupported function/build configuration')",
        "need(function == policy['function'] and tuple(sorted(defines)) == tuple(policy['defines']), 'unsupported function/build configuration')\n"
        "    source_sha = policy['proof_source']['sha256']\n    is_memory = source_sha == unit_registry.MEMORY_SHA")
    text = replace(text, "and sha(requested) == SOURCE_SHA, 'exact selected first-fixture proof buffer required')",
        "and sha(requested) == source_sha, 'exact selected registered proof buffer required')")
    text = replace(text, '    captured_path, original, tu, declarations, prepared, stream_receipt = complete_capture(policy, reads, selection.project)',
        '    from swdb._dx100_whole import normalized_capture_ingress_v2 as ingress\n'
        '    captured_path, original, tu, declarations, prepared, stream_receipt = ingress.complete_capture(policy, reads, selection.project)')
    text = replace(text, "need(set(expected) == {'atlas', 'globals', 'statements', 'assembly', 'receiver_binding_sha256'}, 'complete source expectation closure required')",
        "need(set(expected) == ({'atlas', 'globals', 'statements', 'assembly', 'receiver_binding_sha256'} |\n"
        "         ({'selected_root'} if is_memory else set())), 'complete per-unit source expectation closure required')")
    text = replace(text, "    need(receiver_policy['inputs']['full_tu']['sha256'] == policy['capture']['compressed_tu']['sha256']\n         and receiver_policy['full_tu_canonical_sha256'] == prepared['normalized_full_tu_sha256'],\n         'compressed storage and canonical original graph identities must remain distinct')",
        "    graph_storage, compiler_observation = capture_inputs(policy['capture'])\n"
        "    need(receiver_policy['inputs']['full_tu'] == graph_storage\n"
        "         and receiver_policy['inputs']['capture_receipt'] == compiler_observation\n"
        "         and receiver_policy['full_tu_canonical_sha256'] == prepared['normalized_full_tu_sha256'],\n"
        "         'selected graph storage, original compiler observation and canonical graph identities differ')")
    text = replace(text, "    base_parts = [model.hook_text(policy['choice_budget']), *component_texts,",
        "    resource_profile = resource_selection(source_sha, function,\n"
        "        {name: sha(components[name].encode('utf-8')) for name in COMPONENT_ORDER})\n"
        "    resource_text = resources.prefix(resource_profile) if resource_profile is not None else ''\n"
        "    need(assembly['entry']['model'].get('resource_profile') == resource_profile,\n"
        "         'source-profile model capacity/unwind binding differs')\n"
        "    base_parts = [model.hook_text(policy['choice_budget']) + resource_text, *component_texts,")
    text = replace(text, "    parts = [model.hook_text(policy['choice_budget']), *component_texts,",
        "    parts = [model.hook_text(policy['choice_budget']) + resource_text, *component_texts,")
    text = replace(text, "    allocations = context['ordinary_allocations']",
        "    allocations = context['ordinary_allocations']\n"
        "    root_cut = None\n    if is_memory:\n"
        "        root_cut = memory_selection.selected_root(binder.__dict__, normalized_tu=tu, source_path=captured_path,\n"
        "            preparation=prepared, function=function, declarations=declarations, abi=abi)\n"
        "        need(root_cut == reads.document(expected['selected_root']), 'exact original memory root/call closure differs')\n"
        "        memory_receiver.check_allocations(allocations, atlas, source_sha, 1)\n"
        "        memory_runtime.memory_object(atlas, allocations, memory_selection.profile(function),\n"
        "            policy['caller_mangled'], policy['thread'], binder.__dict__, stage.owner)")
    text = replace(text, "    prepared_receiver = receiver.prepare(receiver.OwnedSelection(receiver.Pin(str(receiver_path), len(receiver_raw), sha(receiver_raw))))",
        "    receiver_module = memory_receiver if is_memory else receiver\n"
        "    prepared_receiver = receiver_module.prepare(receiver_module.OwnedSelection(\n"
        "        receiver_module.Pin(str(receiver_path), len(receiver_raw), sha(receiver_raw))))")
    text = replace(text, "'source_sha256': SOURCE_SHA, 'captured_source_path': str(captured_path), 'proof_source_path': str(Path(source)),",
        "'source_sha256': source_sha, 'captured_source_path': str(captured_path), 'proof_source_path': str(Path(source)),")
    text = replace(text, "'buffer_projection': BUFFER_PROJECTION, 'full_tu_expanded_sha256': stream_receipt['expanded_sha256'],",
        "'buffer_projection': policy['buffer_projection'], 'full_tu_expanded_sha256': stream_receipt['expanded_sha256'],")
    text = replace(text, "'full_tu_compressed_sha256': stream_receipt['compressed_sha256'], 'normalized_original_graph_sha256': prepared['normalized_full_tu_sha256'],",
        "'full_tu_compressed_sha256': stream_receipt['compressed_sha256'], 'normalized_original_graph_sha256': prepared['normalized_full_tu_sha256'],\n"
        "        'capture_transport_binding': stream_receipt, 'selected_graph_storage': graph_storage,\n"
        "        'whole_unit_preparation_sha256': digest(prepared),\n"
        "        'normalized_transport': prepared.get('normalized_transport'),")
    text = replace(text, "'CPU_access_count': len(lowered['CPU_projections']), 'call_count': len(lowered['call_bindings'])}",
        "'CPU_access_count': len(lowered['CPU_projections']), 'call_count': len(lowered['call_bindings'])}\n"
        "    if 'unit_registry' in normalized:\n        certificate['unit_registry'] = normalized['unit_registry']\n"
        "    if is_memory:\n        certificate['selected_root_sha256'] = digest(root_cut)\n"
        "        need(memory_selection.selected_root(binder.__dict__, normalized_tu=tu, source_path=captured_path,\n"
        "            preparation=prepared, function=function, declarations=declarations, abi=abi) == root_cut,\n"
        "            'selected original memory root/call closure changed during composition')")
    text = replace(text, "'formal_frame': FRAME, 'source_loop_bound': 1, 'helper_loop_bound': 513,",
        "'formal_frame': FRAME, 'source_loop_bound': 1, 'helper_loop_bound': 513,\n"
        "        'helper_loop_bound_role': 'default; explicit resource-profile owner overrides remain mandatory',\n"
        "        'resource_profile': resource_profile,")
    text = replace(text, "'parameters': (), 'source_sha256': SOURCE_SHA, 'defines': tuple(json.loads(unit.policy_json)['defines']),",
        "'parameters': (), 'source_sha256': certificate['source_sha256'], 'defines': tuple(json.loads(unit.policy_json)['defines']),")
    text = replace(text, '    policy = json.loads(unit.policy_json)\n    selected = [row for row in policy[\'unit_contracts\'] if row[\'id\'] == contract_id and row[\'sha256\'] == contract_sha256]',
        "    if 'unit_registry' in unit.certificate:\n        return registry_consumer.contract(unit, contract_id, contract_sha256, rows)\n"
        "    policy = json.loads(unit.policy_json)\n    selected = [row for row in policy['unit_contracts'] if row['id'] == contract_id and row['sha256'] == contract_sha256]")
    text = replace(text, 'interface.function == FUNCTION', 'interface.function == unit.function')
    before = "    clauses = sorted((row.kind, ' '.join(row.text.split())) for row in rows)\n    need(len(rows) == 2 and clauses in ([('assigns',r'\\everything'),('ensures',r'\\result == 80')],\n         [('assigns',r'\\everything'),('ensures',r'\\result == 79')]), 'exact prospective scalar pair required')"
    text = replace(text, before, '    registry_consumer.harness_clauses(unit, rows)')
    text = replace(text, "helpers and FUNCTION not in helpers and 'dws_source_program' not in helpers",
        "helpers and unit.function not in helpers and 'dws_source_program' not in helpers")
    text = replace(text, 'def model_fields(unit):', '''def resource_selection(source_sha256, function, components):
    if source_sha256 == SOURCE_SHA:
        return resources.select(source_sha256, function, components)
    need(source_sha256 == unit_registry.MEMORY_SHA and function in UNIT_FUNCTIONS and function != FUNCTION
         and components == contracts.COMPONENTS, 'unknown source-specific model resource selection')
    return None  # Existing memory backend defaults, not a first-source capacity exemption.


def unit_resource_profile(unit):
    need(type(unit) is SourceUnit, 'checked source unit required for resource selection')
    expected = resource_selection(unit.certificate['source_sha256'], unit.function, dict(contracts.COMPONENTS))
    need(unit.certificate.get('resource_profile') == expected, 'source-unit resource profile changed')
    return expected


def model_fields(unit):''')
    return text


def main():
    text = source((V3 / 'dx100_checked_source.py').read_text())
    ast.parse(text)
    (OUT / 'dx100_checked_source.py').write_text(text)
    adapter = (V3 / 'dx100_checked_adapter.py').read_text()
    adapter = replace(adapter,
        'selection = source.SourceSelection(selection.library, selection.entry_id, selection.project, adapter.method.id)',
        'selection = source.SourceSelection(selection.library, selection.entry_id, selection.project, adapter.method.id, selection.proof_unit_json)')
    # Both fixed projections raise ValueError subclasses. The new dispatcher
    # intentionally exposes no old `projection` alias; keep refusal handling
    # independent of that removed module attribute.
    adapter = adapter.replace('native.projection.Refused, ', '').replace('native.projection.Refused,', '')
    adapter = replace(adapter, 'whole_source_draws=plan.draws, source_loop_bound=1, helper_loop_bound=513)',
        "whole_source_draws=plan.draws, source_loop_bound=1, helper_loop_bound=513,\n"
        "        whole_source_resource_profile=source.unit_resource_profile(unit))")
    adapter = replace(adapter, "allowed=helpers|{source.FUNCTION,'dws_source_program','swdb_run','main','swdb_next','swdb_next_real'}",
        "allowed=helpers|{unit.function,'dws_source_program','swdb_run','main','swdb_next','swdb_next_real'}")
    adapter = replace(adapter, "source.need(len(loops)==len(set(loops)),'duplicate actual CBMC loop IDs refused')",
        "source.need(bool(loops) and len(loops)==len(set(loops)),'nonempty duplicate-free actual CBMC loop inventory required')")
    adapter = replace(adapter, "    return [loop for loop in loops if loop.rsplit('.',1)[0] in helpers]",
        "    selected=[loop for loop in loops if loop.rsplit('.',1)[0] in helpers]\n"
        "    source.need(bool(selected),'nonempty actual model-helper loop inventory required')\n"
        "    context['settings']['whole_source_actual_loop_ids']=loops\n"
        "    context['settings']['whole_source_actual_loop_inventory_scope']='complete actual --show-loops of freshly rechecked same job.c; no source-reconstructed selectors'\n"
        "    return selected")
    adapter += '''\n\ndef helper_loop_bounds(unit, actual_loop_ids, context):
    """Checked-only bounds for retained actual selectors; all unwinding checks stay."""
    helpers = source.model_fields(unit)['functions']
    profile = source.unit_resource_profile(unit)
    if profile is not None:
        source.need(set(profile['helper_owner_unwind']) <= {loop.rsplit('.',1)[0] for loop in actual_loop_ids},
            'actual first-source capacity-owner loop observation is incomplete')
        rows = source.resources.helper_loop_bounds(profile, actual_loop_ids, helpers)
    else:
        source.need(type(actual_loop_ids) is list and all(type(loop) is str for loop in actual_loop_ids)
            and len(actual_loop_ids) == len(set(actual_loop_ids))
            and all(loop.rsplit('.',1)[0] in helpers for loop in actual_loop_ids), 'actual memory helper selectors required')
        rows = [{'loop':loop,'owner':loop.rsplit('.',1)[0],'unwind':513} for loop in actual_loop_ids]
    context['settings']['whole_source_actual_helper_loop_bounds'] = rows
    context['settings']['whole_source_resource_profile'] = profile
    return rows
'''
    (OUT / 'dx100_checked_adapter.py').write_text(adapter)
    copied = {
        'unit_policy_registry_v2.py': WHOLE / 'source-unit-registry-v2/unit_policy_registry_v2.py',
        'resource_profile_v2.py': WHOLE / 'first-source-resources-v2/resource_profile_v2.py',
        'runtime_projection_v3.py': WHOLE / 'runtime-projection-v3/runtime_projection_v3.py',
        'runtime_projection_v4.py': WHOLE / 'runtime-projection-v4/runtime_projection_v4.py',
        'source_memory_selection_v1.py': WHOLE / 'source-memory-selection-v1/source_memory_selection_v1.py',
        'source-memory-selection-v1/source_memory_selection_v1.py': WHOLE / 'source-memory-selection-v1/source_memory_selection_v1.py',
        'receiver_memory_v1.py': WHOLE / 'receiver-memory-v1/receiver_memory_v1.py',
        'receiver-memory-v1/receiver_memory_v1.py': WHOLE / 'receiver-memory-v1/receiver_memory_v1.py'}
    for name in ('normalized_capture_ingress_v2.py', 'closed_python_surface.py',
                 'role_normalized_gzip_v2.py', 'lossless_gzip_v2.py', 'normalized_compiler_adapter_v1.py'):
        copied[name] = WHOLE / 'normalized-ingress-v2/proposed' / name
    rows = []
    for name, origin in copied.items():
        raw = origin.read_bytes(); target = OUT / '_dx100_whole' / name
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        rows.append({'path': target.relative_to(HERE).as_posix(), 'origin': origin.relative_to(WHOLE).as_posix(),
                     'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    (HERE / 'draft-component-origins-v4.json').write_text(json.dumps({'date': '2026-10-16 ET', 'files': rows,
        'state': 'DRAFT; native view/producer closure/normalized ingress and controls pending; no public admission'},
        sort_keys=True, indent=2) + '\n')
    print(json.dumps({'source_bytes': len(text.encode()), 'components': len(rows), 'shared_production_written': False}))


if __name__ == '__main__':
    main()
