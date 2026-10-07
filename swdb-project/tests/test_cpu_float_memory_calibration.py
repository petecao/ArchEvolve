"""Public independent floating monotonic atomic evidence,2026-10-06 ET."""
import json,subprocess,sys
from conftest import run_swdb


def run_float(records,*args):
    return subprocess.run([sys.executable,'-m','swdb.cpu_float_memory_calibration','--records',str(records.path),*map(str,args)],capture_output=True,text=True)


def test_float_atomic_count_proof_and_portable_elapsed_remain_distinct_from_integer_cells(records,tmp_path,llvm22):
    records.copy_repo('applications','kernels','implementations','inputs','machines','profiles','hardware_targets','strategies','operations','intrinsics')
    proofdir=tmp_path/'float-proof'
    counted=run_float(records,'--output',proofdir,'--fixture','--count-only','--llvm-bin',llvm22,'--max-wall-s','240')
    assert counted.returncode==0,counted.stderr+counted.stdout
    proof=json.loads((proofdir/'count-proof.json').read_text())
    assert proof['timings_collected'] is False and not (proofdir/'receipt.json').exists()
    assert len(proof['count_proof']['points'])==4
    for p in proof['count_proof']['points']:
        assert p['requests']==(p['events'] if p['invoke'] else 0)
        assert p['atomic_events']==p['requests'] and p['opaque_events']==0
        assert p['primitive']=={'opcode':'atomicrmw','value_kind':'floating','element_bits':64,'update_opcode':'fadd','atomic_ordering':'monotonic'}
    elapsed=tmp_path/'float-elapsed'
    result=run_float(records,'--output',elapsed,'--fixture','--llvm-bin',llvm22,'--footprint-bytes','4096','--repetitions','3','--min-trial-s','.002','--max-wall-s','240')
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((elapsed/'receipt.json').read_text())
    service=raw['services'][0]
    assert service['scope']['operation']=='floating-add-update' and service['scope']['element_bytes']==8
    assert all(t['verified_updates']==t['events'] for t in service['trials'])
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',elapsed/'receipt.json','--id','fixture.float.cost','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    assert json.loads(imported.stdout)['services'][0]['parameter']['basis'] in ('reported','unknown')
    resource=subprocess.run([sys.executable,'-m','swdb.cpu_memory_resource','--records',str(records.path),'--source-calibration','fixture.float.cost','--id','fixture.float.resource','--fixture','--format','json'],capture_output=True,text=True)
    assert resource.returncode==0,resource.stderr+resource.stdout
    assert json.loads(resource.stdout)['services'][0]['cost_basis']=='gross_constructed_resource_v1'
    assert records.validate().returncode==0

    # Synthetic native-admission fixture tests metadata guards only; no measured
    # calibration is added to canonical project records.
    import copy
    from swdb.cpu_service_calibration import identity
    native=copy.deepcopy(raw);native['evidence_kind']='native'
    native['context'].update(system='Linux',architecture='x86_64',host='mbit10',dirty=False,commit='a'*40,
        lane='mbit10-evaluation-node0(verified: synthetic public admission fixture)',cpus=[0],machine_sha256='a'*64,
        loaded_libraries={n:{'path':'/synthetic/'+n,'sha256':'a'*64} for n in ('libc.so.6','libstdc++.so.6','libomp.so')})
    native['settings'].update(repetitions=7,min_trial_s=.05)
    original=native['services'][0]['trials'][0]
    native['services'][0]['trials']=[dict(copy.deepcopy(original),gross_seconds=.1,driver_seconds=.01,
        order='service_first' if i%2==0 else 'driver_first') for i in range(7)]
    def attempt(data,tag):
        data['identity_sha256']=identity(data);path=tmp_path/(tag+'.json');path.write_text(json.dumps(data))
        return run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',path,'--id','synthetic.float.'+tag,'--format','json')
    accepted=attempt(native,'accepted');assert accepted.returncode==0,accepted.stderr+accepted.stdout
    changed=[]
    for mutation in ('numerator','ordering','updates','runtime'):
        bad=copy.deepcopy(native)
        if mutation=='numerator':bad['services'][0]['denominator']['proof']['points'][0]['requests']+=1
        elif mutation=='ordering':bad['services'][0]['denominator']['proof']['points'][0]['primitive']['atomic_ordering']='seq_cst'
        elif mutation=='updates':bad['services'][0]['trials'][0]['verified_updates']-=1
        else:bad['context']['loaded_libraries'].pop('libomp.so')
        refused=attempt(bad,mutation)
        assert refused.returncode!=0 and not (records.path/'cpu_service_calibrations'/('synthetic.float.'+mutation+'.yaml')).exists()


def test_float_collector_refuses_caps_before_creating_output(records,tmp_path):
    for name,args in [('oversized',['--footprint-bytes','16777216']),('reps',['--repetitions','12']),('wall',['--max-wall-s','901'])]:
        output=tmp_path/name
        result=run_float(records,'--fixture','--output',output,*args)
        assert result.returncode!=0 and not output.exists()
