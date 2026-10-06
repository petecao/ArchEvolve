"""Description-driven logical offload mechanisms; no target/kernel constants.
Created: 2026-10-06 ET. Logical grouping is never physical row-buffer evidence.
"""
from swdb.analytic_models import bound,parameter


def counts(region,mechanism,context):
    missing=[]
    selector=mechanism.get('selector',{})
    missing.extend('selector.'+key for key in sorted(set(selector)-{'domain'}))
    if selector.get('domain')!='offload':missing.append('selector.domain.offload')
    target=(context or {}).get('target_description_sha256')
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
         'target_description_sha256':(context or {}).get('target_description_sha256')},missing,
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
         'target_description_sha256':(context or {}).get('target_description_sha256')},missing,
        ['A capacity/latency lower bound over declared logical requests; queue occupancy and physical scheduling are not observed.'])


def tile_staging(region,mechanism,*,context=None):
    observed,missing=counts(region,mechanism,context)
    staged=integer_fact(observed,'staged_bytes',missing)
    rate=parameter(mechanism,'staging_bytes_per_s','bytes/s')
    if staged and rate is None:missing.append('staging_bytes_per_s')
    return bound('tile_staging',None if missing else staged/rate if staged else 0.,
        'dynamic staged bytes / staging_bytes_per_s',
        {'staged_bytes':staged,'staging_bytes_per_s':mechanism['parameters'].get('staging_bytes_per_s'),
         'target_description_sha256':(context or {}).get('target_description_sha256')},missing,
        ['Dynamic semantic useful stage bytes; tile capacity and physical transfer multiplicity are not inferred.'])
