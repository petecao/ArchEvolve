"""Description-driven logical offload mechanisms; no target/kernel constants.
Created: 2026-10-06 ET. Logical grouping is never physical row-buffer evidence.
Updated: 2026-10-09 ET (code review): tile staging may select semantic events. Row
and queue counts are recorded per region only, so their event selectors stay unknown.
"""
from swdb.analytic_models import bound,parameter


def counts(region,mechanism,context):
    missing=[]
    selector=mechanism.get('selector',{})
    missing.extend('selector.'+key for key in sorted(set(selector)-{'domain'}))
    if selector.get('domain')!='offload':missing.append('selector.domain.offload')
    target=(context or {}).get('logical_count_target_description_sha256') or (context or {}).get('target_description_sha256')
    observed=region.get('address_stream_counts',{}).get(target)
    if not target or not isinstance(observed,dict):
        missing.append('address_stream_counts.requested_target_description')
        observed={}
    elif observed.get('target_description_sha256')!=target:
        missing.append('address_stream_counts.target_description_sha256')
    if observed and (observed.get('format')!='swdb.logical-address-counts.v1'
        or observed.get('level')!='derived_logical_transactions'):
        missing.append('address_stream_counts.observation_contract')
    return observed,missing


def integer_fact(observed,name,missing):
    value=observed.get(name,{}).get('value')
    if type(value) is not int or value<0:
        missing.append('address_stream_counts.'+name)
        return None
    return value


def reorder_window_rows(region,mechanism,*,context=None):
    observed,missing=counts(region,mechanism,context)
    requests=integer_fact(observed,'line_requests',missing)
    groups=integer_fact(observed,'row_groups',missing) if requests else 0 if requests==0 else None
    if groups is not None and requests is not None and groups>requests:
        missing.append('address_stream_counts.row_groups_exceed_requests')
    rates={name:parameter(mechanism,name,unit) for name,unit in (
        ('row_miss_service_s','seconds/request'),('row_hit_service_s','seconds/request'),
        ('effective_memory_parallelism','requests'))}
    if requests:
        for name,value in rates.items():
            if value is None and (name!='row_hit_service_s' or groups!=requests):missing.append(name)
    seconds=None if missing else (groups*rates['row_miss_service_s']+(requests-groups)*(rates['row_hit_service_s'] or 0))/rates['effective_memory_parallelism'] if requests else 0.
    return bound('reorder_window_rows',seconds,
        '(row_groups * row_miss_service_s + grouped_hits * row_hit_service_s) / effective_memory_parallelism',
        {'line_requests':requests,'row_groups':groups,'parameters':mechanism['parameters'],
         'target_description_sha256':(context or {}).get('target_description_sha256'),
         'counted_target_description_sha256':(context or {}).get('logical_count_target_description_sha256') or (context or {}).get('target_description_sha256')},missing,
        ['Ideal grouping within declared logical windows; no physical row-buffer state or execution schedule is observed.'])


def fetch_queue(region,mechanism,*,context=None):
    observed,missing=counts(region,mechanism,context)
    requests=integer_fact(observed,'line_requests',missing)
    rates={name:parameter(mechanism,name,unit) for name,unit in (
        ('queue_entries','entries'),('fetch_latency_s','seconds/request'),
        ('admission_requests_per_s','requests/s'))}
    if requests:
        missing.extend(name for name,value in rates.items() if value is None)
    seconds=None if missing else max(requests/rates['admission_requests_per_s'],
        requests*rates['fetch_latency_s']/rates['queue_entries']) if requests else 0.
    return bound('fetch_queue',seconds,
        'max(line_requests / admission_requests_per_s, line_requests * fetch_latency_s / queue_entries)',
        {'line_requests':requests,'parameters':mechanism['parameters'],
         'target_description_sha256':(context or {}).get('target_description_sha256'),
         'counted_target_description_sha256':(context or {}).get('logical_count_target_description_sha256') or (context or {}).get('target_description_sha256')},missing,
        ['A capacity/latency lower bound over declared logical requests; queue occupancy and physical scheduling are not observed.'])


def selected_events(region,mechanism,context,staged,missing):
    """Staged bytes of the description's selected semantic events only.

    Per-command useful bytes are exact when the region's logical row is known;
    an event outside the counted contract never becomes zero work.
    """
    events=mechanism.get('selector',{}).get('event_ids')
    if not isinstance(events,list) or not events or any(not isinstance(event,str) for event in events):
        missing.append('selector.event_ids');return None
    declared={command.get('event') for command in ((context or {}).get('observation_contract') or {})
        .get('functional_observation',{}).get('commands',[])}
    if not set(events)<=declared:
        missing.append('accelerator_calls.event_coverage');return None
    if staged is None:return None
    values=[call.get('useful_bytes',{}).get('value') for call in region.get('accelerator_calls',[]) if call.get('event') in events]
    if any(type(value) is not int or value<0 for value in values):
        missing.append('accelerator_calls.useful_bytes');return None
    return sum(values)


def tile_staging(region,mechanism,*,context=None):
    # 2026-10-09 ET: `selector.event_ids` keys staging to a design's operations.
    selector=mechanism.get('selector',{})
    observed,missing=counts(region,{**mechanism,'selector':{k:v for k,v in selector.items() if k!='event_ids'}},context)
    staged=integer_fact(observed,'staged_bytes',missing)
    if 'event_ids' in selector:staged=selected_events(region,mechanism,context,staged,missing)
    rate=parameter(mechanism,'staging_bytes_per_s','bytes/s')
    if staged and rate is None:missing.append('staging_bytes_per_s')
    return bound('tile_staging',None if missing else staged/rate if staged else 0.,
        'dynamic staged bytes of selected events / staging_bytes_per_s' if 'event_ids' in selector else 'dynamic staged bytes / staging_bytes_per_s',
        {'staged_bytes':staged,'staging_bytes_per_s':mechanism['parameters'].get('staging_bytes_per_s'),
         'target_description_sha256':(context or {}).get('target_description_sha256'),
         'counted_target_description_sha256':(context or {}).get('logical_count_target_description_sha256') or (context or {}).get('target_description_sha256'),
         **({'selected_event_ids':selector['event_ids']} if 'event_ids' in selector else {})},missing,
        ['Dynamic semantic useful stage bytes; tile capacity and physical transfer multiplicity are not inferred.'])
