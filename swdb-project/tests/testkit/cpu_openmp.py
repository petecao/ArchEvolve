"""Synthetic OpenMP admission fixtures; never measurement evidence.2026-10-06 ET."""
import copy
from swdb.cpu_openmp_profiles import PROFILES, STATE, PROBE, EVENT_CAP
from swdb.cpu_service_calibration import identity
from swdb.cpu_service_controls import SCOPE
from swdb.cpu_openmp_calibration import SOURCES, OMP_SCOPE, REQUIRED
from swdb.cpu_memory_calibration import PIPELINE, COUNT_CAP, TIMED_CAP


def native_receipt():
    calls=[]
    for profile in PROFILES:
        operands=[{'index':i,'kind':'pointer','bits':None,'state':'redacted','signed_decimal':None} for i in range(profile['argument_count'])]
        for constant in profile['integer_constants']:operands[constant['index']]={**constant,'kind':'integer','state':'constant'}
        calls.append({'site':profile['index'],'name':profile['name'],'argument_count':profile['argument_count'],'operands':operands,
            'ident_flags':{'state':'constant','bits':32,'signed_decimal':str(profile['ident_flags'])},'llvm_function':'service_openmp_matrix',
            'source_location':{'path':'/synthetic/CpuOpenmpWork.h','line':49+profile['index']}})
    projection={'format':'swdb.openmp-call-projection.v1','characterization':{'id':'synthetic','sha256':'a'*64},
        'source_ir_sha256':'b'*64,'source_json_sha256':'c'*64,'calls':calls}
    projection['identity_sha256']=identity(projection)
    proof={'format':'swdb.cpu-openmp-count-proof.v1','pipeline':copy.deepcopy(PIPELINE),'profiles':copy.deepcopy(PROFILES),'static_projection':projection,
        'source_sha256':'a'*64,'count_driver_sha256':'a'*64,'plugin_source_sha256':'a'*64,'runtime_source_sha256':'a'*64,'points':[]}
    for invoke in (True,False):
        for n in (3,5):
            proof['points'].append({'events':n,'invoke':invoke,'characterization_sha256':'a'*64,'normalized_ir_sha256':'b'*64,'source_map_sha256':'c'*64,
                'cells':[{'index':p['index'],'event_abi':p['name'],'executions':n if invoke else 0,'source_sites':[p['index']]} for p in PROFILES]})
    services=[]
    for p in PROFILES:
        services.append({'id':p['id'],'unit':'seconds/call','event_definition':'Synthetic exact event fixture only.',
            'scope':{'event_abi':p['name'],'worker_scope':'serial','openmp_regime':STATE,'abi_profile':copy.deepcopy(p),
                'probe_kind':PROBE,'warm_sequences':16,'transfer_basis':'inferred','dynamic_bounds':'constructed0..31; application bounds unverified'},
            'denominator':{'level':'selected_source_normalized_event','basis':'measured','proof':copy.deepcopy(proof)},
            'trials':[{'events':1000000,'gross_seconds':.08,'driver_seconds':.06,'order':'service_first' if i%2==0 else 'driver_first',
                'checked_legal_sequences':1000000,'driver_checked_legal_sequences':1000000,'event_return_sum':1000000 if p['constructed_outcome']==1 else 0,
                'driver_event_return_sum':1000000 if p['constructed_outcome']==1 else 0,'team_size':1,'omp_level':0 if p['index']<6 else 1,
                'omp_active_level':0,'probe_kind':PROBE} for i in range(7)]})
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'native','machine':'mbit10','threads':1,
        'context':{'system':'Linux','architecture':'x86_64','host':'mbit10','dirty':False,'commit':'a'*40,'lane':'mbit10-evaluation-node0(verified: synthetic test)',
            'cpus':[0],'instrumented_timer':False,'compiler_version':'clang version22.1.8','flags':['-O3','-std=c++11','-fopenmp'],
            'source_sha256':{name:'a'*64 for name in SOURCES},'compiler_sha256':'a'*64,'binary_sha256':'a'*64,'machine_sha256':'a'*64,
            'loaded_libraries':{name:{'path':'/synthetic/'+name,'sha256':'a'*64} for name in ('libc.so.6','libstdc++.so.6','libomp.so.5')},
            'control_environment_scope':copy.deepcopy(SCOPE),'control_environment':{key:None for key in SCOPE['exact_variables']},
            'openmp_environment_scope':copy.deepcopy(OMP_SCOPE),'openmp_environment':copy.deepcopy(REQUIRED),
            'optimized_work':{'ir_sha256':'a'*64,'retained_abis':sorted({p['name'] for p in PROFILES})}},
        'settings':{'group':'openmp_v1','repetitions':7,'min_trial_s':.05,'max_wall_s':900,'event_cap':EVENT_CAP,
            'count_build_cap_bytes':COUNT_CAP,'timed_data_cap_bytes':TIMED_CAP,'requested_helper_payload_cap_bytes':4096},'services':services}
    raw['context']['compiler_version']='clang version 22.1.8'
    raw['identity_sha256']=identity(raw)
    return raw
