"""Description-selected CPU service models. Created: 2026-10-06 ET.

Costs represent scoped independent constructed work, never physical issue latency.
"""
import math

from swdb.analytic_models import bound, parameter


def _serial(region, context):
    if not isinstance(context, dict) or context.get('configured_threads') != 1:
        return ['service_scope.configured_serial_T1']
    if region.get('active_workers', {}).get('value') != 1 or region.get('worker_context', {}).get('team_sizes') != [1]:
        return ['service_scope.observed_serial_T1']
    return []


def native_service_costs(region, mechanism, *, context=None):
    selector = mechanism.get('selector', {})
    missing = ['selector.' + key for key in sorted(set(selector) - {'domain', 'worker_scope', 'calls', 'characterization_sha256'})]
    if selector.get('domain') != 'host' or selector.get('worker_scope') != 'serial_T1':
        missing.append('selector.host_serial_T1')
    pin=selector.get('characterization_sha256')
    if pin is not None and (not isinstance(context,dict) or context.get('characterization_sha256')!=pin):
        missing.append('service_scope.characterization_sha256')
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
        if not (scalar or shaped) or selection.get('unit') != 'seconds/call' or not isinstance(selection.get('name'),str) or not selection['name'] or (scalar and not isinstance(selection.get('parameter'),str)):
            missing.append('selector.calls.scalar_seconds_per_call')
            continue
        name = selection['name']
        if name in seen:
            missing.append('selector.calls.duplicate_name')
            continue
        seen.add(name)
        rate = _rate(mechanism,selection['parameter']) if scalar else None
        shape_parameters, shape_missing = _shape_parameters(selection) if shaped else ({},[])
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
            if shaped:
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
        {'calls': selected, 'covered_calls': covered if not missing else []}, sorted(set(missing)),
        ['A counted callee body receives no second service charge. Exact site/full-count coverage is required.',
         'Service scope is serial T1; size-bin allocator-state transfer is explicitly inferred. Unsupported length/lifetime/selector semantics remain unknown.'])



def _rate(mechanism,name,unit='seconds/call'):
    fact=mechanism['parameters'].get(name,{})
    return None if fact.get('basis')=='unknown' else parameter(mechanism,name,unit)


def _shape_parameters(selection):
    missing=[]
    allocator_fields={'_Znam':'known_length_bins','_Znwm':'known_length_bins',
        '_ZdaPv':'allocation_lifetime_size_bins','_ZdlPv':'allocation_lifetime_size_bins'}
    if allocator_fields.get(selection['name']) != selection['bin_kind']:
        missing.append('selector.calls.allocator_abi_bin_kind')
    if selection['bin_kind'] not in ('known_length_bins','allocation_lifetime_size_bins'):
        missing.append('selector.calls.bin_kind')
    if selection['scope_assumption']!={'regime':'fresh_process_repeated_allocate_free_batches','transfer_basis':'inferred'}:
        missing.append('selector.calls.explicit_allocator_regime_transfer')
    bins=selection['bins']
    values={}
    if not isinstance(bins,list) or not bins:
        return {},missing+['selector.calls.bins']
    for item in bins:
        if not isinstance(item,dict) or set(item)!={'bytes','parameter'} or type(item.get('bytes')) is not int or item['bytes']<0 or not isinstance(item.get('parameter'),str) or not item['parameter'] or item['bytes'] in values:
            missing.append('selector.calls.unique_exact_byte_bins')
        else:values[item['bytes']]=item['parameter']
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


def memory_service_scenario(region, mechanism, *, context=None):
    selector=mechanism.get('selector',{})
    allowed={'domain','worker_scope','scenario','transfer_basis','object_scope','characterization_sha256','requests'}
    missing=['selector.'+k for k in sorted(set(selector)-allowed)]
    required={'domain':'host','worker_scope':'serial_T1','scenario':'resident_serial_constructed_requests',
        'transfer_basis':'inferred','object_scope':'logical_requests_and_bounded_referent_views'}
    if any(selector.get(k)!=v for k,v in required.items()):missing.append('memory_scenario.explicit_supported_transfer')
    pin=selector.get('characterization_sha256')
    if not pin or not isinstance(context,dict) or context.get('characterization_sha256')!=pin:
        missing.append('memory_scenario.characterization_sha256')
    rates={}
    selected=selector.get('requests')
    if not isinstance(selected,list):selected=[];missing.append('selector.requests')
    for item in selected:
        if not isinstance(item,dict) or set(item)!={'update_kind','element_bytes','parameter'} or not isinstance(item.get('update_kind'),str) or type(item.get('element_bytes')) is not int or item['element_bytes']<=0 or not isinstance(item.get('parameter'),str):
            missing.append('selector.exact_request_cells');continue
        key=(item['update_kind'],item['element_bytes'])
        if key in rates:missing.append('selector.duplicate_request_cell')
        rates[key]=item['parameter']
    observed=region.get('memory_service_counts',{})
    if observed.get('format')!='swdb.memory-service-counts.v1' or observed.get('scope') not in ('per_run','per_trial'):
        missing.append('memory_service_counts.format_scope')
    rows=observed.get('requests_by_update_kind',{})
    inputs=[];seconds=0.;useful_bytes=0;executed=0;seen=set()
    for kind,items in rows.items():
        for item in items:
            width=item.get('element_bytes');fact=item.get('requests',{});count=fact.get('value')
            if type(width) is not int or width<=0 or type(count) is not int or count<0 or fact.get('basis')=='unknown' or fact.get('scope')!=observed.get('scope'):
                missing.append('memory_service_counts.known_scoped_requests');continue
            key=(kind,width)
            if key in seen:missing.append('memory_service_counts.duplicate_request_cell')
            seen.add(key);executed+=count;useful_bytes+=count*width
            rate=_rate(mechanism,rates[key],'seconds/request') if key in rates else None
            inputs.append({'update_kind':kind,'element_bytes':width,'requests':fact,'seconds_per_request':rate})
            if count and rate is None:missing.append('memory_scenario.cell.'+kind+'.'+str(width))
            elif count:seconds+=count*rate
    if useful_bytes!=observed.get('useful_bytes',{}).get('value') or observed.get('useful_bytes',{}).get('basis')=='unknown':
        missing.append('memory_service_counts.complete_useful_byte_sum')
    if executed:missing.extend(_serial(region,context))
    if not math.isfinite(seconds):missing.append('memory_scenario.finite_seconds')
    return bound('memory_service_scenario',None if missing else seconds,
        'sum(exact logical source requests * independently constructed resident serial seconds/request)',
        {'requests':inputs,'useful_bytes':useful_bytes,'unknown_object_requests':observed.get('unknown_object_requests'),
         'object_scope_counts':observed.get('object_scope_counts'),'physical_residency_known':False},sorted(set(missing)),
        ['Residency/dependence transfer from constructed cells is explicitly inferred; this is a conditional service scenario.',
         'Logical source requests and bounded referent views do not establish full allocation identity, physical cache misses, first-touch faults or page residency.',
         'This mechanism supplies no opaque-call coverage or separate first-touch service. Unsupported executed update-kind/width cells remain unknown.'])
