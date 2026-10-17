"""Three exact source-root certificates and separately selected body projection.

No source program/model is executed. No context, mapping, resource ownership,
receiver, runtime or public acceptance is granted by these derived outputs.
"""
import hashlib
import json
from pathlib import Path
from swdb import dx100_checked_source as source
from swdb._dx100_whole import source_memory_selection_v1 as selection
from swdb._dx100_whole import memory_normalized_compiler_adapter_v1 as compiler


def need(value, message):
    if not value: raise ValueError(message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(value): return hashlib.sha256(canonical(value)).hexdigest()


def prepare_roots(*, normalized_tu, source_path, preparation, declarations, abi):
    """Recheck the complete same graph and every selected function; never filter it."""
    api = source.binder.__dict__
    compiler.check_cases(preparation)
    transport = preparation.get('normalized_transport')
    need(type(transport) is dict and transport.get('kind') == compiler.KIND
         and transport.get('source_sha256') == compiler.SOURCE_SHA
         and transport.get('normalized_expanded_sha256') == compiler.EXPANDED_SHA
         and transport.get('original_wire_identity_is_normalized_identity') is False,
         'closed memory transport must survive complete preparation')
    graph = digest(normalized_tu); prepared_sha = digest(preparation)
    need(graph == preparation['normalized_full_tu_sha256'] and preparation['abi_observation']['abi'] == abi,
         'actual same-TU graph and ABI observation differ')
    rows = []
    for name, _count in compiler.CASES:
        root = selection.selected_root(api,normalized_tu=normalized_tu,source_path=source_path,
            preparation=preparation,function=name,declarations=declarations,abi=abi)
        need(root['profile']['function'] == name and root['original_normalized_tu_sha256'] == graph,
             'exact selected original memory root differs')
        rows.append({'schema':'memory-source-unit-preparation-1','function':name,
            'source_sha256':compiler.SOURCE_SHA,'complete_preparation_sha256':prepared_sha,
            'normalized_transport':transport,'original_normalized_tu_sha256':graph,
            'selected_root':root,'selected_root_sha256':digest(root),
            'body_CPU_lifetime_mapping_receiver_checks_required':True,
            'owned_context_or_public_admission':False})
    need(digest(normalized_tu) == graph and digest(preparation) == prepared_sha,
         'complete graph or preparation changed during three-root selection')
    need(len({row['selected_root']['selected_declaration_id'] for row in rows}) == 3,
         'three distinct original declaration identities required')
    return {'schema':'memory-three-source-unit-preparation-1','source_sha256':compiler.SOURCE_SHA,
        'complete_preparation_sha256':prepared_sha,'units':rows,'same_TU_graph_modified_or_filtered':False,
        'actual_body_CPU_lifetime_or_public_acceptance':False}


def prepare_body(*, reads, mapping_pin, physical_inputs, root_certificate, normalized_tu,
                 source_path, preparation, declarations, abi, assertion_header_pin):
    """Root supplies the actual mapping; this emits checks, never ownership.

    Final normal SourceUnit composition must still call the fixed receiver and
    exact allocation/lifetime instrumentation, and compare these observations.
    """
    from swdb._dx100_whole import source_argument_staging_v2 as staging
    from swdb._dx100_whole import source_dispatch_v3 as dispatch
    from swdb._dx100_whole import source_statements_v2 as statements
    from swdb._dx100_whole import receiver_memory_v1 as receiver
    from swdb._dx100_whole import runtime_projection_v4 as runtime
    mapping = reads.document(mapping_pin)
    need(type(mapping) is dict and set(mapping) == {'schema','owner','source_sha256','capture_observation_sha256',
        'physical_inputs_sha256','function','object'} and mapping['schema'] == 'root-selected-memory-source-object-mapping-1'
        and type(mapping['owner']) is str and mapping['owner'].strip()
        and mapping['source_sha256'] == compiler.SOURCE_SHA
        and mapping['capture_observation_sha256'] == compiler.CAPTURE_SHA
        and mapping['physical_inputs_sha256'] == digest(physical_inputs), 'exact external memory mapping selection required')
    function = mapping['function']; profile = selection.profile(function)
    roots = prepare_roots(normalized_tu=normalized_tu, source_path=source_path,
        preparation=preparation,declarations=declarations,abi=abi)
    current = next(row for row in roots['units'] if row['function'] == function)
    need(current == root_certificate, 'complete selected original source certificate differs')
    need(type(mapping['object']) is dict and set(mapping['object']) == {'object_id','guest_base','physical_base'},
         'exact one-object ordinary mapping required')
    owners = [node for node in statements.walk(normalized_tu) if node.get('kind') == 'FunctionDecl'
        and node.get('id') == current['selected_root']['selected_declaration_id']]
    need(len(owners) == 1, 'one actual selected original definition required')
    owner = owners[0]; bodies = [node for node in owner.get('inner',[]) if node.get('kind') == 'CompoundStmt']
    arrays = [node for node in statements.walk(owner) if node.get('kind') == 'VarDecl'
        and node.get('name') == 'data' and node.get('type',{}).get('qualType') in ('std::uint32_t[16]','std::uint32_t [16]')]
    need(len(bodies) == len(arrays) == 1, 'exact selected data16 automatic declaration required')
    node = arrays[0]; caller = profile['caller_mangled']
    source_pin = digest({'source_sha256':compiler.SOURCE_SHA,'caller':caller,'local_id':node['id'],'declaration_sha256':digest(node)})
    atlas = dispatch.prepare_atlas([{**mapping['object'],'extent':16,'dtype':0,'source_pin':source_pin}])
    allocations = [{'object_index':0,'object_id':mapping['object']['object_id'],'caller':caller,'local_id':node['id'],
        'declaration_sha256':digest(node),'declaration_range':list(source.binder._span(node)),
        'scope_end_offset':source.binder._span(bodies[0])[1],'allocation_thread':0,
        'allocation_origin':'checked-original-automatic-declaration'}]
    receiver.check_allocations(allocations,atlas,compiler.SOURCE_SHA,1)
    runtime.memory_object(atlas,allocations,profile,caller,0,source.binder.__dict__,owner)
    need(not any(item.get('kind') in {'ForStmt','WhileStmt','DoStmt'} for item in statements.walk(owner)),
         'exact no-loop memory source profile required')
    stage = staging.Stager(source.binder.__dict__,dispatch.__dict__,normalized_tu,caller=caller,
        source_path=source_path,source_text=Path(source_path).read_text(encoding='ascii'),declarations=declarations,
        abi=abi,atlas=atlas,live_local_ids=set(),thread='owned_thread')
    checked = statements.Lowerer(stage,preparation,assertion_header_pin=assertion_header_pin).lower()
    need(checked['public_admission'] is False and checked['receiver_state_and_harness_draw_binding_required'] is True,
         'body projection cannot substitute for owned receiver/draw binding')
    reads.document(mapping_pin); reads.recheck()
    return {'schema':'memory-source-body-preparation-1','function':function,
        'root_certificate_sha256':digest(current),'mapping_pin':mapping_pin,'atlas':atlas,'allocations':allocations,
        'statements':checked,'statement_preparation_sha256':digest(checked),
        'owned_runtime_context_receiver_preparation_still_required':True,'public_admission':False}
