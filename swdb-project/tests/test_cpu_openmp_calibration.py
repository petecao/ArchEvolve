"""Legal native OpenMP probe scope through public commands,2026-10-06 ET; a2 set 2026-10-12 ET.
Updated 2026-10-12 ET (cpud review 8a/8b): the native tests copy only the record closure of the
runner's count seeds, not the 1.1 GB store, and pass `SWDB_TOOLCHAIN_FLAGS` (Linux headers)."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

# The records the OpenMP count step reads (`swdb/cpu_openmp_calibration.py`, its `seeds`).
COUNT_SEEDS = ('gapbs-bfs-do', 'kron-g16-k16')


def run_openmp(records, output, llvm, *args, env_controls=None):
    env={**os.environ,'OMP_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE','OMP_PROC_BIND':'close','OMP_PLACES':'cores'}
    env.update(env_controls or {})
    return subprocess.run([sys.executable,'-m','swdb.cpu_openmp_calibration','--records',str(records.path),
        '--output',str(output),'--fixture','--llvm-bin',str(llvm),*map(str,args)],
        capture_output=True,text=True,env=env,timeout=240)


def test_count_only_matrix_proves_exact_selected_event_scope_without_elapsed(records,tmp_path,llvm22,toolchain_flags):
    records.copy_closure(*COUNT_SEEDS);output=tmp_path/'openmp-count'
    result=run_openmp(records,output,llvm22,'--count-only','--max-wall-s','180',*toolchain_flags)
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'count-proof.json').read_text());proof=raw['count_proof']
    assert raw['format']=='swdb.cpu-openmp-count-only.v1' and raw['timings_collected'] is False
    assert raw['context']['openmp_environment']['OMP_NUM_THREADS']=='1'
    assert len(proof['profiles'])==23 and len(proof['points'])==4
    projection=proof['static_projection']
    assert len(projection['calls'])==23
    assert all(c['ident_flags']['state']=='constant' for c in projection['calls'])
    assert all(p['normalized_ir_sha256']==projection['source_ir_sha256'] for p in proof['points'])
    for point in proof['points']:
        assert len(point['cells'])==23
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


def test_portable_probe_retains_every_legal_event_and_is_imported_only_as_fixture(records,tmp_path,llvm22,toolchain_flags):
    from conftest import make_records, run_swdb
    records.copy_closure(*COUNT_SEEDS);output=tmp_path/'openmp-elapsed'
    result=run_openmp(records,output,llvm22,'--machine','testhost','--repetitions','3','--min-trial-s','.0002','--max-wall-s','180',*toolchain_flags)
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'receipt.json').read_text())
    assert raw['evidence_kind']=='fixture' and len(raw['services'])==23 and raw['settings']['group']=='openmp_v2'
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



def _repo_record(rel):
    import yaml
    from conftest import REPO
    from swdb.store import Record
    return Record(rel,yaml.load((REPO/'records'/rel).read_text(),Loader=yaml.CSafeLoader))


def test_frozen_a1_receipt_record_still_validates_after_the_a2_set_is_added():
    from swdb.cpu_service_calibration import validate_record
    record=_repo_record('cpu_service_calibrations/mbit10.cpu.lanl20261006.service.openmp.a1.yaml')
    assert record.data['settings']['group']=='openmp_v1' and len(record.data['services'])==22
    assert list(validate_record(record,None))==[]


def test_a2_receipt_may_time_only_the_new_class_but_proves_the_full_23_class_count_matrix(tmp_path):
    from testkit.cpu_openmp import native_receipt
    from swdb.cpu_service_calibration import identity
    path=tmp_path/'a2.json'
    def validate(raw):
        raw['identity_sha256']=identity(raw);path.write_text(json.dumps(raw))
        return subprocess.run([sys.executable,'-m','swdb.cpu_openmp_calibration','--validate-receipt',str(path)],capture_output=True,text=True)
    accepted=validate(native_receipt('a2',measured=[22]));assert accepted.returncode==0,accepted.stderr+accepted.stdout
    accepted=validate(native_receipt('a2'));assert accepted.returncode==0,accepted.stderr+accepted.stdout
    raw=native_receipt('a2',measured=[22]);raw['settings']['measured_profiles']=[21]
    rejected=validate(raw);assert rejected.returncode!=0 and 'ABI/probe/state' in rejected.stderr
    raw=native_receipt('a2',measured=[22]);proof=raw['services'][0]['denominator']['proof'];proof['profiles']=proof['profiles'][:22]
    rejected=validate(raw);assert rejected.returncode!=0
    raw=native_receipt('a1');raw['settings']['measured_profiles']=list(range(22))
    rejected=validate(raw);assert rejected.returncode!=0 and 'full matrix' in rejected.stderr



def test_runner_with_a_timing_double_writes_an_a2_receipt_for_the_new_class_that_imports_and_binds(records,tmp_path,monkeypatch,capsys):
    """Seam 2: the collector's command runner is doubled (no compiler, no timer, no LLVM count);
    the count proof is the synthetic a2 matrix. The receipt must still validate and bind."""
    import types
    import swdb.cpu_openmp_calibration as calibrator
    from testkit.cpu_openmp import native_receipt
    from test_cpu_openmp_binding import setup, estimate
    from testkit.cpu_service import bind
    synthetic=native_receipt('a2')['services'][0]['denominator']['proof']
    timed=[]
    def command(argv,timeout):
        argv=[str(a) for a in argv]
        if argv[-1]=='--version':return types.SimpleNamespace(stdout='clang version 22.1.8\n',stderr='')
        if '-S' in argv:
            names=sorted({p['name'] for p in calibrator.PROFILES})
            Path(argv[-1]).write_text(''.join('  call void @'+n+'(ptr null)\n' for n in names));return types.SimpleNamespace(stdout='',stderr='')
        if '-o' in argv:Path(argv[-1]).write_bytes(b'double');return types.SimpleNamespace(stdout='',stderr='')
        op,n,first=int(argv[1]),int(argv[2]),argv[3]=='1';timed.append(op)
        outcome=calibrator.PROFILES[op]['constructed_outcome']==1
        return types.SimpleNamespace(stderr='',stdout=json.dumps({'events':n,'gross_seconds':.09,'driver_seconds':.07,
            'order':'service_first' if first else 'driver_first','checked_legal_sequences':n,'driver_checked_legal_sequences':n,
            'event_return_sum':n if outcome else 0,'driver_event_return_sum':n if outcome else 0,'team_size':1,
            'omp_level':0 if op<6 else 1,'omp_active_level':0,'probe_kind':'per_event_steady_clock_empty_window'}))
    monkeypatch.setattr(calibrator,'_command',command)
    monkeypatch.setattr(calibrator,'proof',lambda args,output,command:copy.deepcopy(synthetic))
    for key,value in {'OMP_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE','OMP_PROC_BIND':'close','OMP_PLACES':'cores'}.items():monkeypatch.setenv(key,value)
    (tmp_path/'llvm').mkdir();(tmp_path/'llvm'/'clang++').write_bytes(b'compiler double')
    output=tmp_path/'openmp-a2'
    monkeypatch.setattr(sys,'argv',['cpu_openmp_calibration','--records',str(records.path),'--output',str(output),'--fixture',
        '--llvm-bin',str(tmp_path/'llvm'),'--machine','testhost','--profile','22','--repetitions','7','--min-trial-s','.05'])
    assert calibrator.main()==0,capsys.readouterr().err
    raw=json.loads((output/'receipt.json').read_text())
    assert raw['settings']['group']=='openmp_v2' and raw['settings']['measured_profiles']==[22]
    assert [s['scope']['event_abi'] for s in raw['services']]==['__kmpc_for_static_init_8u'] and set(timed)=={22}
    assert len(raw['services'][0]['denominator']['proof']['profiles'])==23
    projection,save,args=setup(records,tmp_path,with_8u=True,a2=raw)
    bound=bind(records,*args,'--id','fixture.omp.runner')
    assert bound.returncode==0,bound.stderr+bound.stdout
    data=estimate(records,tmp_path,'fixture.omp.runner')
    assert data['seconds'] is not None
    assert records.validate().returncode==0
