"""2026-10-16 ET. Closed30 actual-public command plan; no dispatch authority."""
from pathlib import Path

METHOD='method.dx100-finite-whole-trace-v1'
def need(ok,message):
    if not ok:raise ValueError(message)

def plan(profile,selection):
    keys={'python','original_project','producer_project','library_root','records','runs','verifier_lock','pycache','compiler_wrapper','cbmc','root_admission_receipt'}
    need(type(selection) is dict and set(selection)==keys,'explicit root command/runtime/lane admission selection required')
    need(all(type(value) is str and Path(value).is_absolute() for key,value in selection.items() if key!='root_admission_receipt'),'absolute root-selected command paths required')
    need(type(selection['root_admission_receipt']) is dict and set(selection['root_admission_receipt'])=={'path','bytes','sha256'},'physical root admission receipt required')
    need(str(Path(selection['records']).parent/'library')==selection['library_root'],'normal default_root(records) must select the actual finite profile Library')
    rows=profile['cases'];need(len(rows)==30 and len({row['case_id'] for row in rows})==30 and all(row['actual_verdict'] is None for row in rows),'closed30 prospective public profile required')
    env=dict(SWDB_HOME=selection['original_project'],PYTHONPATH=selection['producer_project'],PYTHONNOUSERSITE='1',PYTHONSAFEPATH='1',PYTHONDONTWRITEBYTECODE='1',
        PYTHONPYCACHEPREFIX=selection['pycache'],SWDB_CLANG=selection['compiler_wrapper'],SWDB_CBMC=selection['cbmc'],SWDB_VERIFIER_LOCK=selection['verifier_lock'])
    jobs=[]
    for row in rows:
        argv=[selection['python'],'-B','-P','-m','swdb','prove','--records',selection['records'],'--summary',row['contract']['id'],
            '--method-version',METHOD,'--adapter','cbmc','--bounds','{"threads":1}','--runs-dir',selection['runs'],'--format','json']
        jobs.append(dict(case_id=row['case_id'],contract=row['contract'],argv=argv,cwd=selection['producer_project'],conditional_predicted_verdict=row['conditional_predicted_verdict']))
    return dict(schema='finite-public-command-plan-1',date='2026-10-16 ET',environment=env,jobs=jobs,root_admission_receipt=selection['root_admission_receipt'],
        actual_root_guard_lane_runtime_admission_required=True,execution_authorized=False,required_public_count=30,required_skips=0,
        native_scope='sanitized exact abstract model samples/replay; no original C++ equivalence',predictions_never_passed_to_model_or_contract=True)
