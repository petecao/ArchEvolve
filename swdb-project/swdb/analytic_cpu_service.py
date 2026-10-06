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
    missing = ['selector.' + key for key in sorted(set(selector) - {'domain', 'worker_scope', 'calls'})]
    if selector.get('domain') != 'host' or selector.get('worker_scope') != 'serial_T1':
        missing.append('selector.host_serial_T1')
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



def _rate(mechanism,name):
    fact=mechanism['parameters'].get(name,{})
    return None if fact.get('basis')=='unknown' else parameter(mechanism,name,'seconds/call')


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
    return bound('memory_service_scenario', None, 'unsupported memory service scenario',
        mechanism['parameters'], ['memory_service_scenario.not_implemented'])
