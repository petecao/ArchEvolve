"""Independent bulk service construction public seams, 2026-10-06 ET."""
import json
import subprocess
import sys

from conftest import run_swdb


def run_bulk(records,*args):
    return subprocess.run([sys.executable,'-m','swdb.cpu_bulk_calibration','--records',str(records.path),
        *map(str,args)],capture_output=True,text=True,timeout=150)


def test_portable_bulk_cells_retain_separate_alias_regimes_and_exact_sizes(records,tmp_path):
    output=tmp_path/'bulk'
    result=run_bulk(records,'--output',output,'--fixture','--size',8,'--size',292,
        '--repetitions',3,'--min-trial-s',.002,'--max-wall-s',90)
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'receipt.json').read_text())
    assert raw['evidence_kind']=='fixture' and raw['threads']==1
    scopes=[(s['scope']['event_abi'],s['scope']['size_bytes'],s['scope']['bulk_regime']) for s in raw['services']]
    assert set(scopes)=={('memcpy',8,'constant8_noalias_align8')}|{('memmove',n,r) for n in (8,292)
        for r in ('dynamic_length_disjoint_align4','dynamic_length_overlap_forward4_align4','dynamic_length_overlap_backward4_align4')}
    assert len(scopes)==7
    assert all(s['scope']['transfer_basis']=='inferred' and len(s['trials'])==3 for s in raw['services'])
    assert all(t['events']>0 and t['gross_seconds']>0 and t['driver_seconds']>0 for s in raw['services'] for t in s['trials'])
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',output/'receipt.json',
        '--id','fixture.bulk.cost','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    assert all(s['parameter']['basis'] in ('reported','unknown') for s in json.loads(imported.stdout)['services'])
    assert records.validate().returncode==0
    refused=run_bulk(records,'--output',tmp_path/'oversized','--fixture','--size',1048577)
    assert refused.returncode!=0 and not (tmp_path/'oversized').exists()


def test_counted_bulk_matrix_proves_every_exact_bin_and_regime_without_timing(records,tmp_path,llvm22):
    records.copy_repo('applications','kernels','implementations','inputs','machines','profiles','hardware_targets','strategies','operations','intrinsics')
    output=tmp_path/'proof'
    result=run_bulk(records,'--output',output,'--fixture','--count-only','--llvm-bin',llvm22,
        '--size',8,'--size',292,'--max-wall-s',120)
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'count-proof.json').read_text())
    assert raw['timings_collected'] is False and not (output/'receipt.json').exists()
    proof=raw['count_proof'];assert len(proof['points'])==4
    assert proof['pipeline']['version']=='source-normalized-v2'
    for point in proof['points']:
        assert len(point['cells'])==7
        assert all(c['executions']==(point['events'] if point['invoke'] else 0) for c in point['cells'])
        assert all(len(c['source_sites'])==1 for c in point['cells'])
        assert {s['helper_function'] for s in point['source_sites']}=={'bulk_copy8','bulk_move_disjoint','bulk_move_forward','bulk_move_backward'}
    assert raw['context']['optimized_work']['retained']['bulk_copy8']=='constant8_word_load_store'
    assert len(set(p['characterization_sha256'] for p in proof['points']))==4


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


def test_native_bulk_import_requires_full_exact_matrix_and_preserves_unresolved_subtraction(records,tmp_path):
    import copy
    from swdb.cpu_service_calibration import identity
    records.copy_repo('machines')
    def ingest(raw,key):
        raw['identity_sha256']=identity(raw);path=tmp_path/(key+'.json');path.write_text(json.dumps(raw))
        return run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',path,'--id',key,'--format','json')
    raw=native_bulk_receipt()
    result=ingest(raw,'synthetic.bulk.accepted')
    assert result.returncode==0,result.stderr+result.stdout
    assert records.validate().returncode==0
    missing=copy.deepcopy(raw)
    for s in missing['services']:s['denominator']['proof']['points'][0]['cells'].pop()
    wrong=copy.deepcopy(raw);wrong['services'][1]['scope']['bulk_regime']='application_nonoverlap'
    elided=copy.deepcopy(raw);elided['context']['optimized_work']['retained'].pop('bulk_move_forward')
    unchecked=copy.deepcopy(raw);unchecked['services'][0]['trials'][0]['checked_one_copy']=False
    short=copy.deepcopy(raw);short['services'][0]['trials'][0]['driver_seconds']=.001
    for i,data in enumerate((missing,wrong,elided,unchecked,short)):
        refused=ingest(data,'synthetic.bulk.invalid.'+str(i));assert refused.returncode!=0
    unresolved=copy.deepcopy(raw);unresolved['services'][1]['trials'][0]['driver_seconds']=.2
    kept=ingest(unresolved,'synthetic.bulk.unresolved')
    assert kept.returncode==0,kept.stderr+kept.stdout
    service=json.loads(kept.stdout)['services'][1]
    assert service['parameter']['value'] is None and service['seconds_per_event']['min']<0
