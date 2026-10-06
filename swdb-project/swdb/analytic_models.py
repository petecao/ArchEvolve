"""Reusable region-to-seconds mechanism models. Updated: 2026-10-06 ET.

No kernel/target IDs enter these formulas. Parameters are aggregate rates for the
frozen target and thread configuration. A required unknown is never replaced by zero.
"""
import math

CLASSES = ('integer', 'floating_point', 'branch', 'atomic')


def bound(model, seconds, formula, inputs, missing=(), notes=()):
    return {'model': model, 'seconds': seconds, 'basis': 'estimated',
            'state': 'unknown' if seconds is None else 'known', 'formula': formula,
            'inputs': inputs, 'missing': list(missing), 'notes': list(notes)}


def parameter(mechanism, name, unit):
    fact = mechanism['parameters'].get(name)
    if not fact or fact.get('value') is None or fact.get('unit') != unit:
        return None
    value = fact['value']
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0 else None


def compute_throughput(region, mechanism):
    values, missing, components = {}, [], []
    for category in CLASSES:
        count = region['operation_counts'][category]['value']
        name = category + '_ops_per_s'
        rate = parameter(mechanism, name, 'operations/s')
        values[category] = {'operations': count, 'rate': mechanism['parameters'].get(name)}
        if count is None:
            missing.append('operation_counts.' + category)
        elif count == 0:
            components.append(0.0)
        elif rate is None:
            missing.append(name)
        else:
            components.append(count / rate)
    return bound('compute_throughput', None if missing else max(components, default=0.0),
                 'max(operation_count[class] / operations_per_second[class])', values, missing,
                 ['Arithmetic counts include source loop control; address/cast instructions are excluded.'])


def streaming_bandwidth(region, mechanism, covered_nonstream=False):
    moved = 0
    missing = []
    access_inputs = []
    for access in region['access_patterns']:
        n = access['bytes_accessed']['value']
        shape = access['address_shape']['value']
        access_inputs.append({'access': access['id'], 'bytes': n, 'address_shape': shape})
        if n is None:
            missing.append(access['id'] + '.bytes_accessed')
        elif n == 0:
            continue
        elif shape != 'stream' and not covered_nonstream:
            missing.append(access['id'] + '.streaming_classification')
        elif shape == 'stream':
            moved += n
    rate = parameter(mechanism, 'bytes_per_s', 'bytes/s')
    if moved and rate is None:
        missing.append('bytes_per_s')
    seconds = None if missing else (moved / rate if moved else 0.0)
    return bound('streaming_bandwidth', seconds, 'sum(streaming useful bytes) / effective_bytes_per_second',
                 {'accesses': access_inputs, 'bytes': moved, 'bytes_per_s': mechanism['parameters'].get('bytes_per_s')}, missing,
                 ['Useful source element bytes; bandwidth must use this same convention, not bus bytes or a theoretical peak.'])


INDIRECT = {'single_valued_indirect','ranged_indirect','pointer_chase','data_dependent_merge','constant'}


def requests_in_flight_latency(region, mechanism):
    latency=parameter(mechanism,'dependent_latency_s','seconds/load')
    inflight=parameter(mechanism,'effective_requests_per_thread','requests/thread')
    workers=region.get('active_workers',{}).get('value')
    missing=[];seconds=0.;inputs=[]
    for access in region['access_patterns']:
        shape=access['address_shape']['value'];count=access['element_count']['value']
        if shape=='stream':continue
        item={'access':access['id'],'requests':count,'shape':shape};inputs.append(item)
        if count is None:missing.append(access['id']+'.element_count')
        elif count==0:continue
        elif shape not in INDIRECT:missing.append(access['id']+'.address_shape')
        else:
            if latency is None:missing.append('dependent_latency_s')
            if inflight is None:missing.append('effective_requests_per_thread')
            if workers is None or workers<=0:missing.append('active_workers')
            if latency is not None and inflight is not None and workers is not None and workers>0:
                overlap=min(inflight,1.) if shape=='pointer_chase' else inflight
                item['effective_requests_in_flight']=workers*overlap
                seconds+=count*latency/(workers*overlap)
    return bound('requests_in_flight_latency',None if missing else seconds,
        'sum(nonstream requests * dependent latency / (active workers * effective requests per worker))',
        {'accesses':inputs,'active_workers':region.get('active_workers'),
         'dependent_latency_s':mechanism['parameters'].get('dependent_latency_s'),
         'effective_requests_per_thread':mechanism['parameters'].get('effective_requests_per_thread')},
        sorted(set(missing)),['Concurrency is an effective inferred parameter, not measured MSHR occupancy.',
        'Pointer-chase recurrence limits overlap to one request per executing worker; useful atomic operand width is not bus traffic.'])


def cache_fit(region,mechanism):
    moved=0;missing=[]
    for access in region['access_patterns']:
        count=access['bytes_accessed']['value']
        if count is None:missing.append(access['id']+'.bytes_accessed')
        else:moved+=count
    footprint=region['footprint_bytes']['value']
    capacity=parameter(mechanism,'capacity_bytes','bytes')
    hit_rate=parameter(mechanism,'bytes_per_s','bytes/s')
    cold_rate=parameter(mechanism,'cold_bytes_per_s','bytes/s')
    cold=None;reused=None;seconds=0.
    if moved:
        if footprint is None:missing.append('footprint_bytes')
        if capacity is None:missing.append('capacity_bytes')
        if footprint is not None and capacity is not None and footprint>capacity:
            missing.append('footprint_exceeds_cache_capacity')
        if footprint is not None:
            cold=min(moved,footprint);reused=max(0,moved-cold)
            if cold and cold_rate is None:missing.append('cold_bytes_per_s')
            if reused and hit_rate is None:missing.append('bytes_per_s')
            if not missing:seconds=(cold/cold_rate if cold else 0)+(reused/hit_rate if reused else 0)
    return bound('cache_fit',None if missing else seconds,
        'if footprint <= capacity: cold useful bytes / cold bytes_per_s + reused useful bytes / cache bytes_per_s',
        {'useful_bytes':moved,'footprint_bytes':region['footprint_bytes'],
         'capacity_bytes':mechanism['parameters'].get('capacity_bytes'),'cold_useful_bytes':cold,
         'reused_useful_bytes':reused,'cold_bytes_per_s':mechanism['parameters'].get('cold_bytes_per_s'),
         'bytes_per_s':mechanism['parameters'].get('bytes_per_s')},missing,
        ['Cold first touches remain charged; fit alone does not prove every access is a cache hit.',
         'Ideal fully associative capacity bound over live virtual byte union; conflicts, allocator lifetime and physical placement are not inferred.',
         'Outside the modeled cache capacity this mechanism has no supported bound, so its required result remains unknown.'])


MODELS = {'compute_throughput':compute_throughput,'streaming_bandwidth':streaming_bandwidth,
          'requests_in_flight_latency':requests_in_flight_latency,'cache_fit':cache_fit}


def evaluate(region,mechanism,models=(),target_threads=1):
    implementation=MODELS.get(mechanism['model'])
    if implementation is None:
        return bound(mechanism['model'],None,'unsupported mechanism model',mechanism['parameters'],['mechanism_model.'+mechanism['model']])
    if mechanism['model']=='streaming_bandwidth':
        result=implementation(region,mechanism,covered_nonstream=bool(set(models)&{'requests_in_flight_latency','cache_fit'}))
        uses_rate=result['inputs']['bytes']>0
    else:
        result=implementation(region,mechanism)
        uses_rate=(any((region['operation_counts'][category]['value'] or 0)>0 for category in CLASSES)
            if mechanism['model']=='compute_throughput' else
            result['inputs']['useful_bytes']>0 if mechanism['model']=='cache_fit' else False)
    if uses_rate and target_threads>1 and (region.get('active_workers',{}).get('value')!=target_threads or region.get('worker_context',{}).get('team_sizes')!=[target_threads]):
        result['seconds']=None
        result['state']='unknown'
        result['missing'].append('aggregate_rate_worker_scope')
        result['inputs']['rate_active_workers']=target_threads
        result['inputs']['observed_active_workers']=region.get('active_workers')
        result['inputs']['worker_context']=region.get('worker_context')
        result['notes'].append('The aggregate rate was measured with all configured workers active; this region requires an independently measured rate for its observed worker count.')
    return result
