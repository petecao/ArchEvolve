"""Description-selected CPU service models. Created: 2026-10-06 ET.

Costs represent scoped independent constructed work, never physical issue latency.
"""
import math
import re

from swdb.analytic_models import bound, parameter


def _serial(region, context):
    if not isinstance(context, dict) or context.get('configured_threads') != 1:
        return ['service_scope.configured_serial_T1']
    if region.get('active_workers', {}).get('value') != 1 or region.get('worker_context', {}).get('team_sizes') != [1]:
        return ['service_scope.observed_serial_T1']
    return []



def _scope_missing(selector,context,prefix,*,required=False):
    allowed=selector.get('characterization_allowlist')
    if allowed is not None:
        valid=isinstance(allowed,list) and bool(allowed) and all(isinstance(row,dict) and set(row)=={'id','sha256'} and isinstance(row['id'],str) and bool(row['id']) and re.fullmatch('[0-9a-f]{64}',str(row['sha256'])) for row in allowed)
        if valid:valid=len({row['id'] for row in allowed})==len(allowed) and len({row['sha256'] for row in allowed})==len(allowed)
        if not valid or 'characterization_sha256' in selector or not isinstance(context,dict) or {'id':context.get('characterization_id'),'sha256':context.get('characterization_sha256')} not in allowed:
            return [prefix+'.characterization_allowlist']
        return []
    pin=selector.get('characterization_sha256')
    if (required or pin is not None) and (not pin or not isinstance(context,dict) or context.get('characterization_sha256')!=pin):
        return [prefix+'.characterization_sha256']
    return []

def native_service_costs(region, mechanism, *, context=None):
    selector = mechanism.get('selector', {})
    missing = ['selector.' + key for key in sorted(set(selector) - {'domain', 'worker_scope', 'calls', 'characterization_sha256','characterization_allowlist','openmp_projections','calibration_admission'})]
    if selector.get('domain') != 'host' or selector.get('worker_scope') != 'serial_T1':
        missing.append('selector.host_serial_T1')
    missing.extend(_scope_missing(selector,context,'service_scope'))
    missing.extend(_admission_missing(mechanism))
    calls = selector.get('calls')
    if not isinstance(calls, list) or not calls:
        missing.append('selector.calls')
        calls = []
    if not isinstance(context, dict) or not isinstance(context.get('source_calls'), list):
        missing.append('source_call_inventory')
    source = context.get('source_calls', []) if isinstance(context, dict) else []
    seconds, selected, covered, seen = 0., [], [], set()
    for selection in calls:
        scalar = isinstance(selection,dict) and set(selection)=={'name','parameter','unit'}
        shaped = isinstance(selection,dict) and set(selection)=={'name','unit','bin_kind','bins','scope_assumption'}
        openmp = isinstance(selection,dict) and set(selection)=={'name','unit','abi_sites','scope_assumption'}
        if not (scalar or shaped or openmp) or selection.get('unit') != 'seconds/call' or not isinstance(selection.get('name'),str) or not selection['name'] or (scalar and not isinstance(selection.get('parameter'),str)):
            missing.append('selector.calls.scalar_seconds_per_call')
            continue
        name = selection['name']
        if name in seen:
            missing.append('selector.calls.duplicate_name')
            continue
        seen.add(name)
        rate = _rate(mechanism,selection['parameter']) if scalar else None
        shape_parameters, shape_missing = _shape_parameters(selection,mechanism) if shaped else ({},[])
        missing.extend(shape_missing)
        for call in source:
            if call.get('name') != name:
                continue
            count = call.get('execution_count', {}).get('value')
            selected.append({'site': call.get('site'), 'name': name, 'executions': count,
                'body_counted': call.get('body_counted'), 'selection': selection})
            if call.get('body_counted') is True or count == 0:
                continue
            if type(count) is not int or count < 0:
                missing.append('call_count.' + name)
                continue
            missing.extend(_serial(region, context))
            if openmp:
                from swdb.analytic_cpu_openmp import cost as openmp_cost
                cost,reasons=openmp_cost(region,call,selection,mechanism,context)
                missing.extend(reasons)
            elif shaped:
                cost, reasons = _shape_cost(region,call,selection,shape_parameters,mechanism)
                missing.extend(reasons)
            else:
                cost = None if rate is None else count * rate
                if rate is None: missing.append(selection['parameter'])
                elif not math.isfinite(cost): missing.append('call_cost.finite.' + name)
            if call.get('site') is None:
                missing.append('call_site.' + name)
            elif cost is not None and math.isfinite(cost):
                seconds += cost
                covered.append({'site': call['site'], 'execution_count': count})
    return bound('native_service_costs', None if missing else seconds,
        'sum(exact selected opaque call size-bin executions * independently scoped seconds/call)' ,
        {'calls': selected, 'covered_calls': covered if not missing else [],
         'calibration_admission':selector.get('calibration_admission',{})}, sorted(set(missing)),
        ['A counted callee body receives no second service charge. Exact site/full-count coverage is required.',
         'Service scope is serial T1; size-bin allocator-state transfer is explicitly inferred. Unsupported length/lifetime/selector semantics remain unknown.',
         'OpenMP requires full characterization/static-site projection and exact ABI classes. Legal warmed-T1 state, dynamic bounds and pointer-state transfer remain inferred; both dispatch return-profile costs are required.',
         'Bulk profile maxima are explicitly inferred constructed scenarios; application overlap and alignment remain unverified. No physical latency or proven application upper bound is established.'])



def _admission_missing(mechanism):
    admission=mechanism.get('selector',{}).get('calibration_admission',{})
    valid=isinstance(admission,dict) and all(isinstance(name,str) and name in mechanism.get('parameters',{}) and
        isinstance(reasons,list) and bool(reasons) and all(isinstance(r,str) and bool(r) for r in reasons)
        for name,reasons in admission.items())
    return [] if valid else ['calibration_admission.valid_structural_premises']


def _rate(mechanism,name,unit='seconds/call'):
    # Structural context admission remains independent of any numeric fill.
    if _admission_missing(mechanism) or name in mechanism.get('selector',{}).get('calibration_admission',{}):return None
    fact=mechanism['parameters'].get(name,{})
    return None if fact.get('basis')=='unknown' else parameter(mechanism,name,unit)


BULK_PROFILES=('dynamic_length_disjoint_align4','dynamic_length_overlap_forward4_align4','dynamic_length_overlap_backward4_align4')
BULK_ABIS={'memcpy':'copy','llvm.memcpy.p0.p0.i64':'copy','memmove':'move','llvm.memmove.p0.p0.i64':'move'}
BULK_ASSUMPTION={'regime':'prepared_reused_bulk_buffers','transfer_basis':'inferred','profile_policy':'max_constructed_profiles_median',
    'source_overlap':'unverified','source_alignment':'unverified','physical_upper_bound':False}
BULK_RESOURCE_ASSUMPTION={**BULK_ASSUMPTION,'cost_basis':'gross_bulk_loop_resource_v1','includes_loop_control':True}


def _bulk_profile_parameters(item,selection,mechanism):
    source=item.get('source_profiles');copy=BULK_ABIS[selection['name']]=='copy'
    expected=('constant8_noalias_align8',) if copy else BULK_PROFILES
    if (not isinstance(source,list) or len(source)!=len(expected) or any(not isinstance(row,dict) or set(row)!={'regime','parameter','calibration','service'} or any(not isinstance(v,str) or not v for v in row.values()) for row in source)):
        return ['selector.calls.exact_constructed_bulk_profiles']
    if tuple(row['regime'] for row in source)!=expected or len({(r['calibration'],r['service']) for r in source})!=len(source):
        return ['selector.calls.exact_constructed_bulk_profiles']
    if copy and item['bytes']!=8:return ['selector.calls.constant8_bulk_bin']
    rates=[_rate(mechanism,r['parameter']) for r in source]
    expected_rate=max(rates) if all(r is not None and r>0 for r in rates) else None
    actual=_rate(mechanism,item['parameter'])
    if (actual!=expected_rate or (copy and item['parameter']!=source[0]['parameter']) or
        (not copy and mechanism['parameters'].get(item['parameter'],{}).get('basis')!=('inferred' if expected_rate is not None else 'unknown'))):
        return ['selector.calls.exact_constructed_bulk_envelope']
    return []


def _shape_parameters(selection,mechanism):
    missing=[]
    allocator_fields={'_Znam':'known_length_bins','_Znwm':'known_length_bins',
        '_ZdaPv':'allocation_lifetime_size_bins','_ZdlPv':'allocation_lifetime_size_bins'}
    bulk=selection['name'] in BULK_ABIS
    if bulk:
        if selection['bin_kind']!='known_length_bins':missing.append('selector.calls.bulk_abi_bin_kind')
        if isinstance(selection['scope_assumption'],dict) and selection['scope_assumption'].get('regime')=='fresh_process_repeated_allocate_free_batches':missing.append('selector.calls.allocator_abi_bin_kind')
        if selection['scope_assumption'] not in (BULK_ASSUMPTION,BULK_RESOURCE_ASSUMPTION) or selection['scope_assumption'].get('physical_upper_bound') is not False:
            missing.append('selector.calls.explicit_constructed_bulk_transfer')
    else:
        if allocator_fields.get(selection['name']) != selection['bin_kind']:
            missing.append('selector.calls.allocator_abi_bin_kind')
        if selection['scope_assumption']!={'regime':'fresh_process_repeated_allocate_free_batches','transfer_basis':'inferred'}:
            missing.append('selector.calls.explicit_allocator_regime_transfer')
    if selection['bin_kind'] not in ('known_length_bins','allocation_lifetime_size_bins'):
        missing.append('selector.calls.bin_kind')
    bins=selection['bins'];values={}
    if not isinstance(bins,list) or not bins:return {},missing+['selector.calls.bins']
    for item in bins:
        fields={'bytes','parameter','source_profiles'} if bulk else {'bytes','parameter'}
        if not isinstance(item,dict) or set(item)!=fields or type(item.get('bytes')) is not int or item['bytes']<(8 if bulk else 0) or (bulk and item['bytes']>1048576) or not isinstance(item.get('parameter'),str) or not item['parameter'] or item['bytes'] in values:
            missing.append('selector.calls.unique_exact_byte_bins')
        else:
            values[item['bytes']]=item['parameter']
            if bulk:missing.extend(_bulk_profile_parameters(item,selection,mechanism))
    return values,missing


def _shape_cost(region,call,selection,parameters,mechanism):
    rows=[r for r in region.get('call_shape_counts',{}).get('calls',[]) if r.get('site')==call.get('site') and r.get('name')==call['name']]
    if len(rows)!=1:return None,['call_shape.exact_site.'+call['name']]
    row=rows[0]; count=call['execution_count']['value']; scope=call['execution_count'].get('scope')
    field=selection['bin_kind']; unknown='unknown_free_lifetimes' if field=='allocation_lifetime_size_bins' else 'unknown_lengths'
    if field not in ('allocation_lifetime_size_bins','known_length_bins') or row.get(unknown,{}).get('value')!=0 or row.get('execution_count',{}).get('value')!=count or row['execution_count'].get('scope')!=scope:
        return None,['call_shape.complete_scoped_bins.'+call['name']]
    cost=0.; observed=0; missing=[]; seen=set()
    for item in row.get(field,[]):
        size=item.get('bytes'); fact=item.get('execution_count',{}); n=fact.get('value')
        if type(size) is not int or size<0 or size in seen or type(n) is not int or n<0 or fact.get('scope')!=scope or fact.get('basis')=='unknown':
            missing.append('call_shape.valid_unique_bin_counts.'+call['name']); continue
        seen.add(size); observed+=n
        if not n:continue
        rate=_rate(mechanism,parameters[size]) if size in parameters else None
        if rate is None:missing.append('call_shape.cost.'+call['name']+'.'+str(size))
        else:cost+=n*rate
    if observed!=count:missing.append('call_shape.full_site_count.'+call['name'])
    if not math.isfinite(cost):missing.append('call_shape.finite_cost.'+call['name'])
    return (None if missing else cost),missing



def _memory_construction(item,mechanism):
    construction=item.get('construction');kind=item.get('update_kind');width=item.get('element_bytes')
    expected={'read':'ordinary_read','write':'ordinary_write','add-update':'integer_seq_cst_add',
        'compare-and-swap':'integer_strong_seq_cst_compare_exchange'}.get(kind)
    required={'primitive','regime','footprint_bytes','transfer_basis','physical_cache_level','source_services'}
    if kind=='compare-and-swap':required.add('outcome_policy')
    if not isinstance(construction,dict) or set(construction)-{'cost_basis'}!=required:return None,['memory_scenario.explicit_construction']
    if construction.get('cost_basis','paired_driver_subtraction') not in ('paired_driver_subtraction','gross_constructed_resource_v1'):return None,['memory_scenario.resource_recipe']
    size=construction['footprint_bytes'];small=width==1
    if (expected is None or construction['primitive'] not in ((expected,'floating_monotonic_add') if kind=='add-update' and width==8 else (expected,)) or construction['regime']!=('fixed_small_byte_read_constructed_requests' if small else 'resident_serial_constructed_requests') or
        construction['transfer_basis']!='inferred' or construction['physical_cache_level']!='unverified' or type(size) is not int or size<64 or size>8388608 or size&(size-1) or
        (small and (kind!='read' or size!=256))):return None,['memory_scenario.supported_construction']
    sources=construction['source_services']
    if not isinstance(sources,list) or len(sources)!=(2 if kind=='compare-and-swap' else 1) or any(not isinstance(s,dict) or set(s)!={'calibration','service','parameter'} or any(not isinstance(v,str) or not v for v in s.values()) for s in sources):
        return None,['memory_scenario.typed_source_services']
    if len({(s['calibration'],s['service']) for s in sources})!=len(sources):return None,['memory_scenario.unique_source_services']
    if kind=='compare-and-swap':
        if construction['outcome_policy']!='max_constructed_success_failure_median':return None,['memory_scenario.collapse_outcome_policy']
        values=[_rate(mechanism,s['parameter'],'seconds/request') for s in sources]
        expected_rate=max(values) if all(v is not None for v in values) else None
        actual=_rate(mechanism,item['parameter'],'seconds/request')
        if actual!=expected_rate or (actual is not None and mechanism['parameters'][item['parameter']].get('basis')!='inferred'):
            return None,['memory_scenario.exact_constructed_outcome_envelope']
    elif sources[0]['parameter']!=item['parameter']:return None,['memory_scenario.exact_source_parameter']
    return construction,[]


def _primitive_supported(access,construction):
    p=access.get('primitive_semantics',{});width=access.get('element_bytes')
    if (p.get('format')!='swdb.source-memory-primitive.v1' or p.get('vector') is not False or access.get('ir_lanes')!=1 or
        p.get('element_bits')!=8*width or p.get('value_kind') not in ('integer','floating','pointer')):return False
    profile=construction['primitive'];op=p.get('opcode');order=p.get('atomic_ordering')
    if profile in ('ordinary_read','ordinary_write'):
        return op==('load' if profile=='ordinary_read' else 'store') and order=='not_atomic' and p.get('failure_ordering') is None and p.get('weak') is None and access.get('read_write') is False
    if profile=='floating_monotonic_add':return width==8 and p.get('value_kind')=='floating' and access.get('read_write') is True and op=='atomicrmw' and p.get('update_opcode')=='fadd' and order=='monotonic' and p.get('failure_ordering') is None and p.get('weak') is None and p.get('volatile') is False
    if p.get('value_kind')!='integer' or access.get('read_write') is not True:return False
    if profile=='integer_seq_cst_add':return op=='atomicrmw' and p.get('update_opcode')=='add' and order=='seq_cst' and p.get('failure_ordering') is None and p.get('weak') is None
    if profile=='integer_strong_seq_cst_compare_exchange':return op=='cmpxchg' and p.get('update_opcode') is None and order=='seq_cst' and p.get('failure_ordering')=='seq_cst' and p.get('weak') is False
    return False


def _source_memory_proof(context,observed,cells):
    sources=context.get('source_accesses') if isinstance(context,dict) else None
    if not isinstance(sources,list):return {},{},[],['memory_scenario.exact_source_access_inventory']
    totals={};profile_counts={};inputs=[];missing=[];seen=set()
    for access in sources:
        identifier=access.get('id');width=access.get('element_bytes');kind=access.get('update_kind');fact=access.get('element_count',{});n=fact.get('value')
        if not isinstance(identifier,str) or not identifier or identifier in seen or type(width) is not int or width<=0 or type(n) is not int or n<0 or fact.get('basis')=='unknown' or fact.get('scope')!=observed.get('scope'):
            missing.append('memory_scenario.exact_source_scoped_counts');continue
        seen.add(identifier);key=(kind,width);totals[key]=totals.get(key,0)+n
        if not n:continue
        profiles=[(k,c) for k,c in cells.items() if k[:2]==key and c.get('construction') is not None and _primitive_supported(access,c['construction'])]
        valid=len(profiles)==1
        parameter_name=profiles[0][1]['parameter'] if valid else None
        if valid:profile_counts[profiles[0][0]]=profile_counts.get(profiles[0][0],0)+n
        inputs.append({'site':identifier,'requests':fact,'primitive_semantics':access.get('primitive_semantics'),'supported':valid,'parameter':parameter_name})
        if not valid:missing.append('memory_scenario.primitive.'+identifier)
        b=access.get('bytes_accessed',{})
        if b.get('value')!=n*width or b.get('basis')=='unknown' or b.get('scope')!=observed.get('scope'):
            missing.append('memory_scenario.exact_source_useful_bytes')
    return totals,profile_counts,inputs,missing

def memory_service_scenario(region, mechanism, *, context=None):
    selector=mechanism.get('selector',{})
    allowed={'domain','worker_scope','scenario','transfer_basis','object_scope','characterization_sha256','characterization_allowlist','requests','calibration_admission'}
    missing=['selector.'+k for k in sorted(set(selector)-allowed)]
    required={'domain':'host','worker_scope':'serial_T1','scenario':'resident_serial_constructed_requests',
        'transfer_basis':'inferred','object_scope':'logical_requests_and_bounded_referent_views'}
    if any(selector.get(k)!=v for k,v in required.items()):missing.append('memory_scenario.explicit_supported_transfer')
    missing.extend(_scope_missing(selector,context,'memory_scenario',required=True))
    missing.extend(_admission_missing(mechanism))
    rates={}
    selected=selector.get('requests')
    if not isinstance(selected,list):selected=[];missing.append('selector.requests')
    for item in selected:
        if not isinstance(item,dict) or set(item)!={'update_kind','element_bytes','parameter','construction'} or not isinstance(item.get('update_kind'),str) or type(item.get('element_bytes')) is not int or item['element_bytes']<=0 or not isinstance(item.get('parameter'),str):
            missing.append('selector.exact_request_cells');continue
        construction,reasons=_memory_construction(item,mechanism);missing.extend(reasons)
        key=(item['update_kind'],item['element_bytes'],None if construction is None else construction['primitive'])
        if key in rates:missing.append('selector.duplicate_request_cell')
        rates[key]={'parameter':item['parameter'],'construction':construction}
    observed=region.get('memory_service_counts',{})
    if observed.get('format')!='swdb.memory-service-counts.v1' or observed.get('scope') not in ('per_run','per_trial'):
        missing.append('memory_service_counts.format_scope')
    rows=observed.get('requests_by_update_kind',{})
    source_totals,profile_counts,source_inputs,source_missing=_source_memory_proof(context,observed,rates);missing.extend(source_missing)
    inputs=[];seconds=0.;useful_bytes=0;executed=0;seen=set()
    for kind,items in rows.items():
        for item in items:
            width=item.get('element_bytes');fact=item.get('requests',{});count=fact.get('value')
            if type(width) is not int or width<=0 or type(count) is not int or count<0 or fact.get('basis')=='unknown' or fact.get('scope')!=observed.get('scope'):
                missing.append('memory_service_counts.known_scoped_requests');continue
            key=(kind,width)
            if key in seen:missing.append('memory_service_counts.duplicate_request_cell')
            seen.add(key);executed+=count;useful_bytes+=count*width
            if source_totals.get(key,0)!=count:missing.append('memory_scenario.exact_source_cell_sum.'+kind+'.'+str(width))
            profiles=[];covered=0;cost=0.;resolved=True
            for profile,cell in rates.items():
                if profile[:2]!=key:continue
                n=profile_counts.get(profile,0)
                if not n:continue
                rate=_rate(mechanism,cell['parameter'],'seconds/request')
                profiles.append({'primitive':profile[2],'parameter':cell['parameter'],'requests':n,
                    'seconds_per_request':rate,'construction':cell['construction']})
                covered+=n
                if rate is None:resolved=False
                else:cost+=n*rate
            inputs.append({'update_kind':kind,'element_bytes':width,'requests':fact,'source_primitive_profiles':profiles})
            if count and (covered!=count or not resolved):missing.append('memory_scenario.cell.'+kind+'.'+str(width))
            elif count:seconds+=cost
    if any(n and key not in seen for key,n in source_totals.items()):missing.append('memory_scenario.exact_source_complete_cell_set')
    if useful_bytes!=observed.get('useful_bytes',{}).get('value') or observed.get('useful_bytes',{}).get('basis')=='unknown':
        missing.append('memory_service_counts.complete_useful_byte_sum')
    if executed:missing.extend(_serial(region,context))
    if not math.isfinite(seconds):missing.append('memory_scenario.finite_seconds')
    return bound('memory_service_scenario',None if missing else seconds,
        'sum(exact logical source requests * independently constructed resident serial seconds/request)',
        {'requests':inputs,'source_accesses':source_inputs,'useful_bytes':useful_bytes,'unknown_object_requests':observed.get('unknown_object_requests'),
         'object_scope_counts':observed.get('object_scope_counts'),'physical_residency_known':False,
         'calibration_admission':selector.get('calibration_admission',{})},sorted(set(missing)),
        ['Residency/dependence transfer from constructed cells is explicitly inferred; this is a conditional service scenario.',
         'Logical source requests and bounded referent views do not establish full allocation identity, physical cache misses, first-touch faults or page residency.',
         'Exact scalar opcode/type/order/strong-CAS proof and exact source-site partitions are required; floating64 monotonic fadd needs its separate construction. Collapsed kinds do not admit other floating RMW, atomic exchange, weak CAS or vectors. Compiler retention/locality transfer remains inferred.',
         'Total-cell resource costs include retained driver work and compose as a maximum with counted compute; their application transfer is inferred, not a proven upper bound. Paired-subtraction inputs remain separately pinned.',
         'This mechanism supplies no opaque-call coverage or separate first-touch service. Unsupported executed update-kind/width cells remain unknown.'])
