"""Reuse immutable logical counts only under identical complete observation policy.
Updated: 2026-10-06 ET. Unknown fields stay in the digest. No count is rewritten.
"""
import copy
import re
from swdb import artifacts
from swdb.cli import Failure

# These fields are record metadata/provenance, not observer configuration.
METADATA=frozenset({'id','version','status','created','updated','provenance','notes','deprecated_by','calibration_sources','parameter_estimation'})
# Only these recognized numerical service premises may change without counting.
# Model/selector/accounting and every unknown parameter/field remain in the digest.
POLICY_FORMAT='swdb.observation-policy.v1'
# This versioned classification table is immutable once execution receipts exist.
RATES={
    'compute_throughput':{k+'_ops_per_s':'operations/s' for k in ('integer','floating_point','branch','atomic')},
    'streaming_bandwidth':{'bytes_per_s':'bytes/s'},
    'requests_in_flight_latency':{'dependent_latency_s':'seconds/load','effective_requests_per_thread':'requests/thread'},
    'cache_fit':{'bytes_per_s':'bytes/s','cold_bytes_per_s':'bytes/s'},
    'offload_setup':{'seconds_per_event':'seconds/event'},
    'reorder_window_rows':{'row_miss_service_s':'seconds/request','row_hit_service_s':'seconds/request','effective_memory_parallelism':'requests'},
    'fetch_queue':{'fetch_latency_s':'seconds/request','admission_requests_per_s':'requests/s'},
    'tile_staging':{'staging_bytes_per_s':'bytes/s'}}


def policy(target):
    result={k:copy.deepcopy(v) for k,v in target.items() if k not in METADATA}
    removed=[]
    for index,mechanism in enumerate(result.get('mechanisms',[])):
        allowed=RATES.get(mechanism.get('model'),{})
        parameters=mechanism.get('parameters',{})
        for name in list(parameters):
            fact=parameters[name]
            if name in allowed and isinstance(fact,dict) and set(fact)=={'value','basis','source','unit'} and fact.get('unit')==allowed[name]:
                removed.append((index,name,parameters.pop(name)))
    # Schema v1 uses literal layout/window/request values. Retain resolved facts
    # if any preserved/unknown policy field nevertheless names a rate parameter.
    def strings(value):
        if isinstance(value,str):yield value
        elif isinstance(value,dict):
            for key,child in value.items():
                yield key
                yield from strings(child)
        elif isinstance(value,list):
            for child in value:yield from strings(child)
    identifiers={word for text in strings(result) for word in re.findall(r'[A-Za-z_][A-Za-z0-9_]*',text)}
    referenced=[{'mechanism_index':index,'parameter':name,'resolved_fact':fact}
        for index,name,fact in removed if name in identifiers]
    return {'format':POLICY_FORMAT,'record_policy':result,'referenced_rate_parameters':referenced}


def policy_sha256(target):return artifacts.digest(policy(target))


def snapshot_problems(data):
    observation=data.get('observation_contract',{})
    snapshot=observation.get('counted_target_description_snapshot')
    if snapshot is None:return
    from swdb import paths,vocab
    from swdb.schemas import SchemaSet
    vocabs,_=vocab.load_all(paths.VOCAB)
    errors=list(SchemaSet(paths.SCHEMAS,vocabs).for_kind('target_description').iter_errors(snapshot))
    if errors:
        yield 'observation_contract.counted_target_description_snapshot','invalid counted target snapshot: '+errors[0].message
        return
    from swdb.analytic import _payload_problems
    yield from _payload_problems(snapshot)
    try:actual_snapshot=artifacts.digest(snapshot);actual_policy=policy_sha256(snapshot)
    except (ValueError,TypeError):
        yield 'observation_contract.counted_target_description_snapshot','non-finite or non-JSON counted target snapshot'
        return
    if observation.get('target_observation_policy_format')!=POLICY_FORMAT:
        yield 'observation_contract.target_observation_policy_format','unsupported observation policy format'
    if actual_snapshot!=observation.get('requested_target_description_sha256'):
        yield 'observation_contract.counted_target_description_snapshot','snapshot differs from original counted target hash'
    if actual_policy!=observation.get('target_observation_policy_sha256'):
        yield 'observation_contract.target_observation_policy_sha256','complete observation policy digest differs'
    for field in ('functional_observation','dram_address_layout'):
        if snapshot.get(field)!=observation.get(field):
            yield 'observation_contract.'+field,'counted target snapshot differs from sealed observer configuration'


def resolve(characterization,target):
    observation=characterization.get('observation_contract',{})
    if 'functional_observation' not in observation:return None
    counted=observation['requested_target_description_sha256'];requested=artifacts.digest(target)
    snapshot=observation.get('counted_target_description_snapshot')
    if counted!=requested:
        if snapshot is None:raise Failure('complete counted observation policy unavailable; fresh counts required')
        if policy_sha256(snapshot)!=policy_sha256(target):
            raise Failure('observation policy changed; fresh counts required')
    return {'format':'swdb.identical-observation-reuse.v1',
        'state':'exact_counted_target' if counted==requested else 'identical_observation_policy',
        'counted_target_description_sha256':counted,'requested_target_description_sha256':requested,
        'observation_policy_format':observation.get('target_observation_policy_format'),
        'observation_policy_sha256':observation.get('target_observation_policy_sha256'),
        'counted_characterization_sha256':artifacts.digest(characterization),
        'count_observation_context_sha256':artifacts.digest(observation),
        'notes':['The original count and execution receipt are immutable. Only explicitly classified numerical service rates/costs and record provenance may differ.',
            'Source/backend/command/role/width/layout/window/placement/unknown parameter policies require fresh counts; recorded state budget and runtime context remain sealed in the original characterization.',
            'Error-band bindings belong to the frozen protocol and do not change the counted observation policy.']}
