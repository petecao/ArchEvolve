"""Independent logical memory service through its public module CLI (2026-10-06)."""
import json
import subprocess
import sys

from conftest import run_swdb


def run_memory(records,*args):
    return subprocess.run([sys.executable,'-m','swdb.cpu_memory_calibration','--records',str(records.path),
        *map(str,args)],capture_output=True,text=True)


def test_portable_memory_cell_retains_driver_trials_and_reported_request_unit(records,tmp_path):
    output=tmp_path/'memory-cell'
    result=run_memory(records,'--output',output,'--fixture','--operation','read',
        '--element-bytes','4','--footprint-bytes','4096','--repetitions','3','--min-trial-s','.002','--max-wall-s','60')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads((output/'receipt.json').read_text())
    assert data['evidence_kind']=='fixture' and data['threads']==1
    service=data['services'][0]
    assert service['unit']=='seconds/request'
    assert service['scope']['update_kind']=='read' and service['scope']['element_bytes']==4
    assert service['scope']['footprint_bytes']==4096 and service['scope']['transfer_basis']=='inferred'
    assert len(service['trials'])==3
    assert all(t['events']>0 and t['gross_seconds']>0 and t['driver_seconds']>0 for t in service['trials'])
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',output/'receipt.json',
        '--id','fixture.memory.cost','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    cost=json.loads(imported.stdout)['services'][0]['parameter']
    assert cost['unit']=='seconds/request' and cost['basis'] in ('reported','unknown')
    invalid=run_memory(records,'--output',tmp_path/'oversized','--fixture','--footprint-bytes',64*1024**2)
    assert invalid.returncode!=0 and not (tmp_path/'oversized').exists()


def test_all_memory_request_primitives_bind_exact_service_and_driver_counts(records,tmp_path,llvm22):
    records.copy_repo('applications','kernels','implementations','inputs','machines','profiles',
        'hardware_targets','strategies','operations','intrinsics')
    output=tmp_path/'memory-counts'
    result=run_memory(records,'--output',output,'--fixture','--count-only','--llvm-bin',llvm22,
        '--footprint-bytes','4096','--max-wall-s','240')
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'count-proof.json').read_text())
    proof=raw['count_proof']
    assert raw['timings_collected'] is False and not (output/'receipt.json').exists()
    assert len(proof['points'])==40 and proof['pipeline']['version']=='source-normalized-v2'
    for point in proof['points']:
        assert point['requests']==(point['events'] if point['invoke'] else 0)
        assert point['element_bytes'] in (4,8) and len(point['characterization_sha256'])==64
        assert point['operation_counts']['floating_point']==0
    assert raw['context']['optimized_work']['retained_primitives']=={'1':['volatile_read'],**{str(w):['volatile_read','volatile_write','seq_cst_add','seq_cst_compare_exchange'] for w in (4,8)}}
    assert all(p['opaque_events']==0 for p in proof['points'])
    assert raw['budgets']=={'count_build_cap_bytes':64*1024**2,'timed_data_cap_bytes':25*1024**2}
    assert raw['context']['optimized_work']['ir_sha256']
    assert raw['context']['control_environment']['LD_AUDIT'] is None


def native_admission_receipt():
    """Synthetic admission input only: no measured record enters the checkout."""
    from swdb.cpu_service_controls import SCOPE
    import copy
    names=('read','write','add-update','cas-success','cas-failure')
    kinds=('read','write','add-update','compare-and-swap','compare-and-swap')
    proof={'format':'swdb.cpu-memory-count-proof.v1',
        'pipeline':{'version':'source-normalized-v2','passes':['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']},
        'source_sha256':'a'*64,'count_driver_sha256':'a'*64,
        'plugin_source_sha256':'a'*64,'runtime_source_sha256':'a'*64,'points':[]}
    for name,kind in zip(names,kinds):
        for width in (4,8):
            for invoke in (True,False):
                for n in (3,5):
                    proof['points'].append({'operation':name,'element_bytes':width,'invoke':invoke,'events':n,
                        'requests':n if invoke else 0,'opaque_events':0,
                        'checked_success_events':n if invoke and name=='cas-success' else 0 if invoke and name=='cas-failure' else None,
                        'requests_by_kind_width':[{'update_kind':kind,'element_bytes':width,'requests':n}] if invoke else [],
                        'operation_counts':{'integer':n,'floating_point':0,'branch':n,'atomic':n if invoke and name in names[2:] else 0},
                        'characterization_sha256':'a'*64})
    services=[]
    for name,kind in zip(names,kinds):
        for width in (4,8):
            elements=64//width;events=elements*100000
            services.append({'id':f'memory.{name}.{width}.64','unit':'seconds/request','event_definition':'Synthetic public admission fixture',
                'scope':{'worker_scope':'serial','memory_regime':'resident_serial_constructed_requests',
                    'operation':name,'update_kind':kind,'element_bytes':width,'footprint_bytes':64,'transfer_basis':'inferred',
                    'cache_state':'prepared buffers and repeated calls; physical cache level unverified','first_touch':'preparation excluded'},
                'denominator':{'level':'source_normalized_work','basis':'measured','proof':copy.deepcopy(proof)},
                'trials':[{'events':events,'batch_events':elements,'batches':100000,'gross_seconds':.1,'driver_seconds':.03,
                    'order':'service_first' if i%2==0 else 'driver_first','checksum':0,
                    'cycle_verified_elements':elements if name=='read' else None,
                    'success_events':events if name=='cas-success' else 0 if name=='cas-failure' else None} for i in range(7)]})
    return {'format':'swdb.cpu-service-calibration.v1','evidence_kind':'native','machine':'mbit10','threads':1,
        'context':{'system':'Linux','architecture':'x86_64','host':'mbit10','dirty':False,'commit':'a'*40,
            'lane':'mbit10-evaluation-node0(verified: synthetic test)','cpus':[0],'instrumented_timer':False,
            'compiler_version':'clang version 22.1.8','compiler_sha256':'a'*64,'flags':['-O3','-std=c++11'],
            'source_sha256':{n:'a'*64 for n in ('CpuMemoryWork.h','CpuMemoryCount.cpp','CpuMemoryTimer.cpp')},
            'binary_sha256':'a'*64,'machine_sha256':'a'*64,
            'loaded_libraries':{'libstdc++.so.6':{'path':'/synthetic/libstdc++','sha256':'a'*64},'libc.so.6':{'path':'/synthetic/libc','sha256':'a'*64}},
            'optimized_work':{'ir_sha256':'a'*64,'retained_primitives':{'1':['volatile_read'],'4':['volatile_read','volatile_write','seq_cst_add','seq_cst_compare_exchange'],
                '8':['volatile_read','volatile_write','seq_cst_add','seq_cst_compare_exchange']}},
            'control_environment_scope':copy.deepcopy(SCOPE),'control_environment':{k:None for k in SCOPE['exact_variables']}},
        'settings':{'group':'memory_v1','repetitions':7,'min_trial_s':.05,'max_wall_s':900,'event_cap':134217728,
            'count_build_cap_bytes':64*1024**2,'timed_data_cap_bytes':25*1024**2,'live_payload_cap_bytes':16*1024**2,
            'operations':list(names),'element_bytes':[4,8],'footprint_bytes':[64]},'services':services}


def import_memory(records,tmp_path,raw,identifier):
    from swdb.cpu_service_calibration import identity
    raw['identity_sha256']=identity(raw)
    path=tmp_path/(identifier+'.json');path.write_text(json.dumps(raw))
    return run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',path,'--id',identifier,'--format','json')


def test_native_memory_import_checks_typed_matrix_and_actual_denominator_not_only_gross_duration(records,tmp_path):
    import copy
    records.copy_repo('machines')
    raw=native_admission_receipt()
    accepted=import_memory(records,tmp_path,raw,'synthetic.memory.admission')
    assert accepted.returncode==0,accepted.stderr+accepted.stdout
    record=json.loads(accepted.stdout)
    assert all(s['parameter']['unit']=='seconds/request' for s in record['services'])
    assert run_swdb('validate','--records',records.path).returncode==0
    missing_width=copy.deepcopy(raw)
    for s in missing_width['services']:
        s['denominator']['proof']['points']=[p for p in s['denominator']['proof']['points'] if p['element_bytes']==4]
    bad_driver=copy.deepcopy(raw);bad_driver['services'][0]['denominator']['proof']['points'][2]['requests']=1
    duplicate=copy.deepcopy(raw);duplicate['services'][-1]=copy.deepcopy(duplicate['services'][0])
    bad_outcome=copy.deepcopy(raw);bad_outcome['services'][6]['trials'][0]['success_events']=0
    optimized=copy.deepcopy(raw);optimized['context']['optimized_work']['retained_primitives'].pop('8')
    for i,data in enumerate((missing_width,bad_driver,duplicate,bad_outcome,optimized)):
        refused=import_memory(records,tmp_path,data,'synthetic.invalid.memory.'+str(i))
        assert refused.returncode!=0,refused.stdout
        assert not (records.path/'cpu_service_calibrations'/('synthetic.invalid.memory.'+str(i)+'.yaml')).exists()
    unresolved=copy.deepcopy(raw);unresolved['services'][0]['trials'][0]['driver_seconds']=.2
    retained=import_memory(records,tmp_path,unresolved,'synthetic.unresolved.memory')
    assert retained.returncode==0,retained.stderr+retained.stdout
    service=json.loads(retained.stdout)['services'][0]
    assert service['parameter']['basis']=='unknown' and service['parameter']['value'] is None
    assert service['seconds_per_event']['min']<0


def test_portable_cas_pairs_report_both_widths_and_exact_success_failure_outcomes(records,tmp_path):
    output=tmp_path/'cas-pairs'
    result=run_memory(records,'--output',output,'--fixture','--operation','cas-success',
        '--operation','cas-failure','--footprint-bytes','64','--repetitions','3','--min-trial-s','.002','--max-wall-s','60')
    assert result.returncode==0,result.stderr+result.stdout
    services=json.loads((output/'receipt.json').read_text())['services']
    assert len(services)==4 and {s['scope']['element_bytes'] for s in services}=={4,8}
    for service in services:
        assert all(t['success_events']==(t['events'] if service['scope']['operation']=='cas-success' else 0) for t in service['trials'])
    refused=run_memory(records,'--output',tmp_path/'too-small','--fixture','--footprint-bytes','32')
    assert refused.returncode!=0 and not (tmp_path/'too-small').exists()


def test_byte_read_uses_independently_counted_verified_small_cycle_not_widened_access(records,tmp_path,llvm22):
    records.copy_repo('applications','kernels','implementations','inputs','machines','profiles',
        'hardware_targets','strategies','operations','intrinsics')
    output=tmp_path/'byte-read'
    result=run_memory(records,'--output',output,'--fixture','--operation','read','--element-bytes','1',
        '--footprint-bytes','256','--llvm-bin',llvm22,'--repetitions','3','--min-trial-s','.002','--max-wall-s','90')
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'receipt.json').read_text());service=raw['services'][0]
    assert service['scope']['element_bytes']==1 and service['scope']['footprint_bytes']==256
    assert service['scope']['memory_regime']=='fixed_small_byte_read_constructed_requests'
    assert all(t['cycle_verified_elements']==256 and t['batch_events']==256 for t in service['trials'])
    points=service['denominator']['proof']['points']
    assert len(points)==4 and all(p['element_bytes']==1 for p in points)
    assert all(p['requests_by_kind_width']==[{'update_kind':'read','element_bytes':1,'requests':p['events']}] for p in points if p['invoke'])
    assert raw['context']['optimized_work']['retained_primitives']['1']==['volatile_read']
    unsupported=run_memory(records,'--output',tmp_path/'byte-large','--fixture','--operation','read',
        '--element-bytes','1','--footprint-bytes','32768')
    assert unsupported.returncode!=0 and not (tmp_path/'byte-large').exists()
