"""2026-10-16 ET. Pure artifact-observer controls; synthetic data proves no VC.

Exercise the public complete-census reader with external artifacts. No project
module, process, native helper, compiler, verifier or solver may execute.
"""
import copy
import hashlib
import importlib.util
import json
import signal
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ENTRY=HERE/'inert-615ddf50-public-v1/entry.py'
OUTPUT=Path('/private/tmp/probata-resume-20261016-t25-closed-view-observer-controls-v1')
EXPECTED_ENTRY='fe38605db3e05034870dff4e12e523607ba4370e79f8f50a064097a93f49e30a'
ROOT='vector_realloc_v3_no_growth'
CALLEE='std_vector_int_ctor_count_value'
CALL='std_vector_int_ctor_count_value(&v, (unsigned long)n, 7);'


def main():
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('pure observer controls 30s budget')))
    signal.alarm(30)
    assert hashlib.sha256(ENTRY.read_bytes()).hexdigest()==EXPECTED_ENTRY
    OUTPUT.mkdir(exist_ok=False)
    attempts=[]
    def audit(name,args):
        if name in {'subprocess.Popen','os.system','os.posix_spawn','ctypes.dlopen'}:
            attempts.append(name)
            raise RuntimeError('pure observer control forbids external execution')
    sys.addaudithook(audit)
    spec=importlib.util.spec_from_file_location('closed_observer_under_test',ENTRY)
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    policy={'output_budget_bytes':4*1024**2,'metadata_reserve_bytes':1024**2}
    expected={'function':ROOT,'constructor_call':CALL}
    records=[]
    def run(name,mutation=None,refuse=False):
        directory=OUTPUT/name;directory.mkdir()
        (directory/'wp_input.c').write_text(CALL+'\n')
        goals=[{'goal':'typed_ctor_requires','property':'ctor_requires_s47','function':ROOT,'line':1,'smoke':False,'passed':True,'results':['valid']},
               {'goal':'typed_ctor_smoke','property':CALLEE+'_wp_smoke_dead_call_s47','function':CALLEE,'line':1,'smoke':True,'passed':False,'results':['timeout']},
               {'goal':'typed_closed_assert','property':'closed_assert','function':ROOT,'line':1,'smoke':False,'passed':True,'results':['valid']}]
        properties=[{'property':'ctor_requires_s47','property_variant':'IPPropertyInstance','origin':'ctor_base_requires','dependencies':[],
                     'extern':False,'line':1,'call_context':{'caller':ROOT,'callee':CALLEE,'statement_id':47,'source_file':str(directory/'wp_input.c')}},
                    {'property':'ctor_base_requires','property_variant':'IPPredicate','origin':None,'dependencies':[],'extern':False},
                    {'property':CALLEE+'_wp_smoke_dead_call_s47','property_variant':'IPOther','property_export_origin':'wp-smoke-reference',
                     'status_registered':False,'description':'wp_smoke_dead_call','source_file':str(directory/'wp_input.c'),'extern':False,'dependencies':[],'origin':None},
                    {'property':'closed_assert','property_variant':'IPCodeAnnot','origin':None,'dependencies':[],'extern':False}]
        standard=copy.deepcopy(goals)
        for row in standard:
            row.update(function=ROOT,provers=[{'prover':'qed','success':1}] if not row['smoke'] else [])
        inventory={'complete':True,'goals':goals,'properties':properties}
        log='EXPORT GOAL smoke\ntheory T\ngoal smoke : false\nend\n'
        state={'inventory':inventory,'standard':standard,'log':log}
        if mutation:mutation(state)
        (directory/'wp-inventory.json').write_text(json.dumps(state['inventory']))
        (directory/'wp-goals.json').write_text(json.dumps(state['standard']))
        (directory/'frama-c.log').write_text(state['log'])
        try:
            result=observer.closed_census(directory,expected,OUTPUT,policy)
        except ValueError as error:
            assert refuse,(name,str(error))
            records.append({'control':name,'expected_refusal':True,'reason':str(error),'passed':True})
        else:
            assert not refuse,name
            assert result['native_goals']==3 and result['ordinary_count']==2 and result['smoke_count']==1
            assert result['call_bindings'][0]['native_callee_owner']==CALLEE
            assert result['call_bindings'][0]['standard_caller_owner']==ROOT
            records.append({'control':name,'expected_refusal':False,'passed':True,'all_actual_rows_retained':True})
    run('complete-callee-source-binding')
    run('foreign-ordinary-owner',lambda s:s['inventory']['goals'][0].update(function='foreign'),True)
    run('call-statement-mismatch',lambda s:s['inventory']['properties'][0]['call_context'].update(statement_id=48),True)
    run('owner-normalized-away',lambda s:s['inventory']['goals'][1].update(function=ROOT),True)
    run('missing-property-dependency',lambda s:s['inventory']['properties'][3].update(dependencies=['absent']),True)
    run('missing-standard-goal',lambda s:s['standard'].pop(),True)
    run('missing-common-smoke-task',lambda s:s.update(log=''),True)
    run('incomplete-common-task',lambda s:s.update(log='EXPORT GOAL smoke\ntheory T\ngoal smoke : false\n'),True)
    assert attempts==[] and all(row['passed'] for row in records)
    result={'created':'2026-10-16 ET','entry_sha256':EXPECTED_ENTRY,'controls':records,'passed':len(records),
            'external_execution_attempts':attempts,'actual_source_tools_or_tasks_run':False,
            'scope':'Synthetic public artifact-census positive/refusal controls only; no solver/task semantics or caller proof.'}
    (OUTPUT/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    assert sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<4*1024**2
    signal.alarm(0)
    print(json.dumps({'output':str(OUTPUT/'result.json'),'passed':len(records),'external_execution_attempts':attempts}))


if __name__=='__main__':
    main()
