"""Public synthetic bulk receipt builder; never measured data,2026-10-06 ET."""
def native_bulk_receipt():
    """Synthetic public admission fixture, never remote measurement evidence."""
    import copy
    from swdb.cpu_service_controls import SCOPE
    from swdb.cpu_bulk_calibration import FUNCTIONS, REGIMES, SOURCES
    sizes=[8,292]
    matrix=[('memcpy',FUNCTIONS[0],8)]+[('memmove',f,n) for f in FUNCTIONS[1:] for n in sizes]
    proof={'format':'swdb.cpu-bulk-count-proof.v1','pipeline':{'version':'source-normalized-v2','passes':['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']},
        'sizes':sizes,'source_sha256':'a'*64,'count_driver_sha256':'a'*64,'plugin_source_sha256':'a'*64,'runtime_source_sha256':'a'*64,
        'visibility':'Count-only always-inline exposes the identical shared loop; native elapsed wrappers remain noinline.',
        'retention':'Empty inline asm retains source memory work; counted indirect-call diagnostics are not ABI events.','points':[]}
    for invoke in (True,False):
        for n in (3,5):
            proof['points'].append({'events':n,'invoke':invoke,'characterization_sha256':'a'*64,'normalized_ir_sha256':'a'*64,'source_map_sha256':'a'*64,
                'source_sites':[{'site':i,'line':20+i,'helper_function':f,'normalized_name':'llvm.'+abi+'.p0.p0.i64'} for i,(abi,f) in enumerate(zip(('memcpy','memmove','memmove','memmove'),FUNCTIONS))],
                'cells':[{'event_abi':abi,'helper_function':f,'size_bytes':size,'executions':n if invoke else 0,'source_sites':[FUNCTIONS.index(f)]} for abi,f,size in matrix],
                'operation_counts':{'integer':100,'floating_point':0,'branch':100,'atomic':0}})
    services=[]
    for op,(f,regime) in enumerate(zip(FUNCTIONS,REGIMES)):
        for n in ([8] if op==0 else sizes):
            services.append({'id':f'bulk.{op}.{n}','unit':'seconds/call','event_definition':'synthetic bulk test',
                'scope':{'event_abi':'memcpy' if op==0 else 'memmove','worker_scope':'serial','bulk_regime':regime,'size_bytes':n,
                    'alignment_min_bytes':8 if op==0 else 4,'transfer_basis':'inferred','first_touch':'preparation excluded',
                    'cache_state':'prepared reused buffers; physical cache level unverified'},
                'denominator':{'level':'source_normalized_work','basis':'measured','proof':copy.deepcopy(proof)},
                'trials':[{'events':1000000,'gross_seconds':.1,'driver_seconds':.06,'order':'service_first' if i%2==0 else 'driver_first',
                    'checked_one_copy':True,'copied_size_bytes':n,'source_destination_delta_bytes':((n+63)//64)*64+64 if op<2 else 4 if op==2 else -4,'overlap_bytes':0 if op<2 else n-4,'destination_alignment_min_bytes':8 if op==0 else 4,'source_alignment_min_bytes':8 if op==0 else 4} for i in range(7)]})
    return {'format':'swdb.cpu-service-calibration.v1','evidence_kind':'native','machine':'mbit10','threads':1,
        'context':{'system':'Linux','architecture':'x86_64','host':'mbit10','dirty':False,'commit':'a'*40,
            'lane':'mbit10-evaluation-node0(verified: synthetic test)','cpus':[0],'instrumented_timer':False,
            'compiler_version':'clang version 22.1.8','compiler_sha256':'a'*64,'flags':['-O3','-std=c++11'],
            'source_sha256':{n:'a'*64 for n in SOURCES},'binary_sha256':'a'*64,'machine_sha256':'a'*64,
            'loaded_libraries':{'libstdc++.so.6':{'path':'/synthetic/libstdc++','sha256':'a'*64},'libc.so.6':{'path':'/synthetic/libc','sha256':'a'*64}},
            'optimized_work':{'ir_sha256':'a'*64,'retained':{f:'constant8_word_load_store' if f==FUNCTIONS[0] else 'dynamic_length_memmove' for f in FUNCTIONS}},
            'control_environment_scope':copy.deepcopy(SCOPE),'control_environment':{k:None for k in SCOPE['exact_variables']}},
        'settings':{'group':'bulk_v1','sizes':sizes,'repetitions':7,'min_trial_s':.05,'max_wall_s':900,'event_cap':134217728,
            'count_build_cap_bytes':64*1024**2,'timed_data_cap_bytes':25*1024**2,'live_payload_cap_bytes':3*1048576+320},'services':services}

