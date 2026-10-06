"""Description-selected CPU service models. Created: 2026-10-06 ET.

Costs represent scoped independent constructed work, never physical issue latency.
"""
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
        if not isinstance(selection, dict) or set(selection) != {'name', 'parameter', 'unit'} or selection.get('unit') != 'seconds/call':
            missing.append('selector.calls.scalar_seconds_per_call')
            continue
        name = selection['name']
        if name in seen:
            missing.append('selector.calls.duplicate_name')
            continue
        seen.add(name)
        rate = parameter(mechanism, selection['parameter'], selection['unit'])
        for call in source:
            if call.get('name') != name:
                continue
            count = call.get('execution_count', {}).get('value')
            selected.append({'site': call.get('site'), 'name': name, 'executions': count,
                'body_counted': call.get('body_counted'), 'parameter': mechanism['parameters'].get(selection['parameter'])})
            if call.get('body_counted') is True or count == 0:
                continue
            if type(count) is not int or count < 0:
                missing.append('call_count.' + name)
                continue
            missing.extend(_serial(region, context))
            if rate is None:
                missing.append(selection['parameter'])
            elif call.get('site') is None:
                missing.append('call_site.' + name)
            else:
                seconds += count * rate
                covered.append({'site': call['site'], 'execution_count': count})
    return bound('native_service_costs', None if missing else seconds,
        'sum(exact selected opaque call executions * independently scoped seconds/call)',
        {'calls': selected, 'covered_calls': covered if not missing else []}, sorted(set(missing)),
        ['A counted callee body receives no second service charge. Exact site/full-count coverage is required.',
         'Initial service scope is serial T1; unsupported length/lifetime/selector semantics remain unknown.'])


def memory_service_scenario(region, mechanism, *, context=None):
    return bound('memory_service_scenario', None, 'unsupported memory service scenario',
        mechanism['parameters'], ['memory_service_scenario.not_implemented'])
