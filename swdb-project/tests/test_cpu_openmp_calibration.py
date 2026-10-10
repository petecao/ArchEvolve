"""Legal native OpenMP probe scope through public commands,2026-10-06 ET."""
import json
import os
import subprocess
import sys


def run_openmp(records, output, llvm, *args, env_controls=None):
    env={**os.environ,'OMP_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE','OMP_PROC_BIND':'close','OMP_PLACES':'cores'}
    env.update(env_controls or {})
    return subprocess.run([sys.executable,'-m','swdb.cpu_openmp_calibration','--records',str(records.path),
        '--output',str(output),'--fixture','--llvm-bin',str(llvm),*map(str,args)],
        capture_output=True,text=True,env=env,timeout=240)


def test_count_only_matrix_proves_exact_selected_event_scope_without_elapsed(records,tmp_path,llvm22):
    records.copy_repo();output=tmp_path/'openmp-count'
    result=run_openmp(records,output,llvm22,'--count-only','--max-wall-s','180')
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'count-proof.json').read_text());proof=raw['count_proof']
    assert raw['format']=='swdb.cpu-openmp-count-only.v1' and raw['timings_collected'] is False
    assert raw['context']['openmp_environment']['OMP_NUM_THREADS']=='1'
    assert len(proof['profiles'])==22 and len(proof['points'])==4
    projection=proof['static_projection']
    assert len(projection['calls'])==22
    assert all(c['ident_flags']['state']=='constant' for c in projection['calls'])
    assert all(p['normalized_ir_sha256']==projection['source_ir_sha256'] for p in proof['points'])
    for point in proof['points']:
        assert len(point['cells'])==22
        assert all(c['executions']==(point['events'] if point['invoke'] else 0) for c in point['cells'])
        assert len(point['characterization_sha256'])==64
    assert not (output/'receipt.json').exists() and not (output/'partial-trials.json').exists()


def test_probe_caps_and_thread_scope_fail_before_output(records,tmp_path,llvm22):
    output=tmp_path/'unbounded'
    failed=run_openmp(records,output,llvm22,'--count-only','--max-wall-s','901')
    assert failed.returncode!=0 and not output.exists()
    failed=run_openmp(records,output,llvm22,'--count-only',env_controls={'OMP_NUM_THREADS':'2'})
    assert failed.returncode!=0 and 'serial controls' in failed.stderr and not output.exists()


def test_public_native_admission_checks_actual_runtime_abi_and_return_scope(tmp_path):
    from testkit.cpu_openmp import native_receipt
    from swdb.cpu_service_calibration import identity
    raw=native_receipt();path=tmp_path/'synthetic-native.json'
    def validate():
        raw['identity_sha256']=identity(raw);path.write_text(json.dumps(raw))
        return subprocess.run([sys.executable,'-m','swdb.cpu_openmp_calibration','--validate-receipt',str(path)],capture_output=True,text=True)
    accepted=validate();assert accepted.returncode==0,accepted.stderr+accepted.stdout
    raw['services'][17]['trials'][0]['event_return_sum']=0
    rejected=validate();assert rejected.returncode!=0 and 'return outcome' in rejected.stderr
    raw=native_receipt();del raw['context']['loaded_libraries']['libomp.so.5']
    rejected=validate();assert rejected.returncode!=0 and 'libomp' in rejected.stderr
    raw=native_receipt();raw['services'][0]['denominator']['proof']['points'][0]['cells'][0]['executions']=0
    rejected=validate();assert rejected.returncode!=0 and 'coefficient' in rejected.stderr


def test_portable_probe_retains_every_legal_event_and_is_imported_only_as_fixture(records,tmp_path,llvm22):
    from conftest import make_records, run_swdb
    records.copy_repo();output=tmp_path/'openmp-elapsed'
    result=run_openmp(records,output,llvm22,'--machine','testhost','--repetitions','3','--min-trial-s','.0002','--max-wall-s','180')
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'receipt.json').read_text())
    assert raw['evidence_kind']=='fixture' and len(raw['services'])==22
    for service in raw['services']:
        outcome=service['scope']['abi_profile']['constructed_outcome']
        for trial in service['trials']:
            assert trial['checked_legal_sequences']==trial['events']==trial['driver_checked_legal_sequences']
            assert trial['event_return_sum']==trial['driver_event_return_sum']==(trial['events'] if outcome==1 else 0)
            assert min(trial['gross_seconds'],trial['driver_seconds'])>=.0002
    (tmp_path/'import').mkdir()
    imported_records=make_records(tmp_path/'import');imported_records.add_stub()
    imported=run_swdb('import-cpu-service-calibration','--records',imported_records.path,'--receipt',output/'receipt.json',
        '--id','fixture.openmp.probes','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    data=json.loads(imported.stdout)
    assert all(s['parameter']['basis'] in ('reported','unknown') for s in data['services'])
    assert all(s['trials']==raw['services'][i]['trials'] for i,s in enumerate(data['services']))
    assert imported_records.validate().returncode==0


def test_native_probe_import_uses_typed_scope_validator_on_store_replay(records,tmp_path):
    from conftest import run_swdb
    from testkit.cpu_openmp import native_receipt
    from testkit.cpu_service import save_receipt
    records.copy_repo('machines')
    raw=native_receipt()
    result=run_swdb('import-cpu-service-calibration','--records',records.path,
        '--receipt',save_receipt(tmp_path,raw),'--id','synthetic.native.openmp','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    assert records.validate().returncode==0
    raw['services'][0]['scope']['abi_profile']['fork_arity']=99
    rejected=run_swdb('import-cpu-service-calibration','--records',records.path,
        '--receipt',save_receipt(tmp_path,raw),'--id','synthetic.native.openmp.bad','--format','json')
    assert rejected.returncode!=0
