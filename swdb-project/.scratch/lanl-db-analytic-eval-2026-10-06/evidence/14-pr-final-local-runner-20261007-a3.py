#!/usr/bin/env python3
"""Local portable metadata replay only; no native/compiler/provider/remote commands."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

MODEL_C='f893fed400347ed23d92e917d8bde21b75e5375d'
BUNDLE='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
TARGET='mbit10.cpu.lanl20261006.t1.services.v1'
CHAR='pagerank.jacobi.kron-g16.cpu.t1.characterization.generality.a1'
ESTIMATE='generality.pagerank.cpu.kron-g16.t1.estimate.final-admission.a1'
REQUEST_SHA='2ee4a07880bb1bca74b5e3611d0a7147befc9ebabb340a832935c4c32443fe90'
CHECKER_SHA='86df23903c131913cd952d3648cfed58e43824982308082bb235579d4b7da3bf'
EVIDENCE='.scratch/lanl-db-analytic-eval-2026-10-06/evidence'


def require(value,message):
    if not value: raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def inventory(root):
    return {path.relative_to(root).as_posix():sha(path) for path in sorted(root.rglob('*')) if path.is_file()}


def validate_model_receipt(receipt,*,store,records,target_sha256,digest,file_hash):
    require(receipt.get('format')=='swdb.prospective-native-model-compact-receipt.v1','Unsupported explicit model export receipt')
    require(receipt.get('identity_sha256')==digest({k:v for k,v in receipt.items() if k!='identity_sha256'}),'Model export receipt seal differs')
    require(receipt.get('phase')=='model' and receipt.get('source_commit')==MODEL_C and receipt.get('source_clean') is True and receipt.get('raw_transferred') is False,'Accepted clean final C model phase required')
    acceptance=receipt['acceptance']
    require(acceptance.get('identity_sha256')==digest({k:v for k,v in acceptance.items() if k!='identity_sha256'}),'Nested model acceptance seal differs')
    require(acceptance.get('source_commit')==MODEL_C and acceptance.get('phase')=='model' and acceptance.get('source_clean') is True and acceptance.get('raw_transferred') is False and acceptance.get('application_performance_timings_collected') is False,'Exact untimed model source/phase required')
    require(acceptance.get('ready_for_development') is True and acceptance.get('target_sha256')==target_sha256 and str(acceptance.get('validation','')).startswith('OK: '),'Accepted real target and development readiness required')
    lane=receipt['lane']
    require(lane.get('exit_code')==0 and bool(lane.get('ended_utc')) and lane.get('node')==0 and lane.get('numa_memory_policy')=='bind:0','Successful released model lane receipt required')
    expected_estimates={f'lanl.cpu.{kernel}.g{scale}.t1.estimate.v1':f'{kernel}.kron-g{scale}.t1.characterization.objects.a1' for kernel in ('bfs','bc') for scale in (16,17)}
    estimates=acceptance['estimates'];require(len(estimates)==4 and {r['id'] for r in estimates}==set(expected_estimates),'Four exact model execution estimates required')
    protocols=acceptance['protocols'];require(set(protocols)=={'bfs','bc'} and len({r['id'] for r in protocols.values()})==2,'Two exact model protocol pins required')
    target=store.get(TARGET,'target_description');require(target is not None and digest(target)==target_sha256,'Receipt real target differs from source Store')
    for row in estimates:
        value=row['seconds'];estimate=store.get(row['id'],'estimate')
        require(type(value) in (int,float) and math.isfinite(value) and value>0 and row['evidence_kind']=='execution' and row['estimator_sha256']==BUNDLE and row['target_description_sha256']==target_sha256,'Positive execution estimate from final F6/target required')
        require(estimate is not None and digest(estimate)==row['sha256'] and estimate['seconds']==value and estimate['evidence_kind']=='execution' and estimate['estimator_sha256']==BUNDLE and estimate['target_description_sha256']==target_sha256 and estimate['characterization']==expected_estimates[row['id']],'Model estimate differs from source Store')
        kernel=expected_estimates[row['id']].split('.')[0]
        require(row['protocol']==estimate['protocol']==protocols[kernel]['id'] and row['characterization_sha256']==estimate['characterization_sha256']==digest(store.get(expected_estimates[row['id']],'workload_characterization')),'Model estimate source/protocol pins differ')
    for row in protocols.values():
        protocol=store.get(row['id'],'protocol')
        require(protocol is not None and digest(protocol)==row['sha256'] and protocol['settings']['estimator_sha256']==BUNDLE and protocol['settings']['target_description']['sha256']==target_sha256,'Model frozen protocol bundle/target differs')
    pins=receipt['new_records'];require(len(pins)==7 and len({r['id'] for r in pins})==7,'Exactly seven exported model records required')
    required_ids={TARGET}|set(expected_estimates)|{r['id'] for r in protocols.values()}
    require({r['id'] for r in pins}==required_ids,'Model exported closure IDs differ')
    kinds={}
    for pin in pins:
        kinds[pin['kind']]=kinds.get(pin['kind'],0)+1
        path=(records/pin['path']).resolve();require(records.resolve() in path.parents and path.is_file(),'Exported model pin must stay inside source records')
        data=store.get(pin['id'],pin['kind']);require(data is not None and store.path_of(pin['id'])==pin['path'] and digest(data)==pin['sha256'] and file_hash(path)==pin['file_sha256'] and path.stat().st_size==pin['bytes'],'Seven exported model record bytes/pins differ')
    require(kinds=={'target_description':1,'protocol':2,'estimate':4},'Model exported closure kinds differ')
    require(receipt['prior_records_preserved']==acceptance['prior_record_bytes_preserved'] and receipt['prior_records_preserved']>=665,'Model prior record preservation differs')
    return {'receipt_identity_sha256':receipt['identity_sha256'],'acceptance_identity_sha256':acceptance['identity_sha256'],'phase':'model','source_commit':MODEL_C,'estimator_sha256':BUNDLE,'ready_for_development':True,'verified_new_records':pins,'positive_execution_estimate_ids':sorted(expected_estimates)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','raw','model-export-receipt'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('source-sha','target-sha256','model-export-commit','model-export-receipt-sha256'):p.add_argument('--'+name,required=True)
    a=p.parse_args();source=a.source.resolve();raw=a.raw.resolve();cwd=source/'swdb-project'
    require(not raw.exists() and source not in raw.parents,'Fresh external raw path required')
    require(all(len(value)==size and all(ch in '0123456789abcdef' for ch in value) for value,size in ((a.source_sha,40),(a.target_sha256,64),(a.model_export_commit,40),(a.model_export_receipt_sha256,64))),'Exact source/target/export pins required')
    def git(*args):return subprocess.check_output(['git','-C',str(source),*args],text=True,timeout=30).strip()
    require(git('rev-parse','HEAD')==a.source_sha and not git('status','--porcelain'),'Source must be clean at exact owned tip')
    require(subprocess.run(['git','-C',str(source),'merge-base','--is-ancestor',a.model_export_commit,a.source_sha],timeout=30).returncode==0,'Accepted model export must be included in source tip')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(cwd))
    from swdb import artifacts
    from swdb.estimate_protocol import estimator_identity
    from swdb.processes import stop_group
    from swdb.store import Store
    require(estimator_identity()==BUNDLE,'Full final F6 bundle differs')
    request=cwd/EVIDENCE/'14-pr-final-freeze-request-20261007-a1.json'
    checker=cwd/EVIDENCE/'14-check-pr-final-replay-20261007.py'
    require(sha(request)==REQUEST_SHA and sha(checker)==CHECKER_SHA,'Frozen preparation helpers differ')
    model_receipt_path=a.model_export_receipt.resolve()
    require(model_receipt_path.is_file() and sha(model_receipt_path)==a.model_export_receipt_sha256,'Explicit actual model receipt file SHA differs')
    source_store=Store(cwd/'records');require(not source_store.problems,'Source Store parse failed')
    target=source_store.get(TARGET,'target_description')
    require(target is not None and artifacts.digest(target)==a.target_sha256,'Real exported services.v1 target differs')
    model_receipt=json.loads(model_receipt_path.read_text())
    model_custody=validate_model_receipt(model_receipt,store=source_store,records=cwd/'records',target_sha256=a.target_sha256,digest=artifacts.digest,file_hash=sha)
    protected={name:inventory(cwd/name) for name in ('records','library','apps')}
    require(len(protected['records'])>=665,'Data-enriched source catalogue required')
    require(shutil.disk_usage(raw.parent).free>=2*1024**3,'Local disk reserve below 2 GiB')
    raw.mkdir();shutil.copytree(cwd/'records',raw/'records');shutil.copytree(cwd/'library',raw/'library')
    require(inventory(raw/'records')==protected['records'] and inventory(raw/'library')==protected['library'],'Initial external copy differs')
    stages=[];env=os.environ.copy();env.update(PYTHONPATH=str(cwd),PYTHONDONTWRITEBYTECODE='1',OMP_THREAD_LIMIT='16')
    def run(name,argv,budget):
        started=time.monotonic();child=None;exit_code=None;timed_out=False;empty_group=False
        out=raw/(name+'.stdout.json');err=raw/(name+'.stderr.txt')
        try:
            with out.open('wb') as stdout,err.open('wb') as stderr:
                child=subprocess.Popen(argv,cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
                try:exit_code=child.wait(timeout=budget)
                except subprocess.TimeoutExpired:timed_out=True;raise
        finally:
            if child is not None:
                stop_group(child,grace_seconds=5)
                try:os.killpg(child.pid,0)
                except ProcessLookupError:empty_group=True
                exit_code=child.returncode
            row={'stage':name,'argv':argv,'budget_seconds':budget,'wall_seconds':time.monotonic()-started,'exit_code':exit_code,'timed_out':timed_out,'owned_process_group_empty':empty_group,'stdout_sha256':sha(out),'stderr_sha256':sha(err)}
            stages.append(row);(raw/'child-stages.json').write_text(json.dumps(stages,indent=2)+'\n')
        require(exit_code==0 and empty_group,name+' failed or left owned processes')
        return json.loads(out.read_text())
    freeze=run('freeze',[sys.executable,'-m','swdb','freeze-protocol',str(request),'--records',str(raw/'records'),'--format','json'],1800)
    protocol=freeze['id']
    run('estimate',[sys.executable,'-m','swdb','estimate','--records',str(raw/'records'),'--characterization',CHAR,'--target-description',TARGET,'--protocol',protocol,'--id',ESTIMATE,'--format','json'],1400)
    run('checker',[sys.executable,str(checker),'--source',str(source),'--source-sha',a.source_sha,'--estimator-sha256',BUNDLE,'--target-sha256',a.target_sha256,'--records',str(raw/'records'),'--protocol',protocol,'--estimate',ESTIMATE,'--output',str(raw/'actual-pr-services-acceptance.json')],1000)
    after=inventory(raw/'records');new=set(after)-set(protected['records'])
    require(all(after.get(path)==value for path,value in protected['records'].items()),'Prior copied record bytes changed')
    auxiliary=new-{path for path in new if path.endswith('.yaml')};new_yaml=new-auxiliary
    require(auxiliary<={'.swdb.lock'} and all((raw/'records'/path).stat().st_size==0 for path in auxiliary),'Unexpected noncanonical copied catalog artifacts')
    require(len(new_yaml)==2,'Replay adds only protocol and estimate')
    selected=Store(raw/'records');require({selected.get(protocol)['kind'],selected.get(ESTIMATE)['kind']}=={'protocol','estimate'},'Replay closure differs')
    require({selected.path_of(protocol),selected.path_of(ESTIMATE)}==new_yaml,'Unexpected isolated new records')
    require(inventory(raw/'library')==protected['library'],'Copied library changed')
    require({name:inventory(cwd/name) for name in protected}==protected,'Source protected bytes changed')
    require(git('rev-parse','HEAD')==a.source_sha and not git('status','--porcelain') and estimator_identity()==BUNDLE,'Source changed during portable replay')
    acceptance=json.loads((raw/'actual-pr-services-acceptance.json').read_text())
    identity=acceptance.pop('identity_sha256');require(artifacts.digest(acceptance)==identity,'Actual checker proof seal differs');acceptance['identity_sha256']=identity
    proof={'format':'swdb.lanl14-local-actual-pr-services-custody.v1','updated':'2026-10-07 ET','scope':'Portable public metadata freeze/estimate/checker on actual immutable PR counts and real exported final CPU target; no native/compiler/provider/remote execution.',
      'source_commit':a.source_sha,'estimator_sha256':BUNDLE,'model_export_commit':a.model_export_commit,'model_export_receipt_sha256':a.model_export_receipt_sha256,'model_export_receipt_path':str(model_receipt_path),'model_export_custody':model_custody,'target_description_sha256':a.target_sha256,'raw':str(raw),'acceptance':acceptance,'children':stages,'prior_record_files_preserved':len(protected['records']),'prior_library_files_preserved':len(protected['library']),'source_protected_files_preserved':sum(map(len,protected.values())),
      'new_isolated_records':{path:after[path] for path in sorted(new_yaml)},'new_auxiliary_catalog_files':{path:after[path] for path in sorted(auxiliary)},'source_clean':True,'application_execution':0,'compiler_execution':0,'provider_calls':0,'remote_actions':0,'local_runner_sha256':sha(Path(__file__)),'request_sha256':REQUEST_SHA,'checker_sha256':CHECKER_SHA}
    proof['identity_sha256']=artifacts.digest(proof);(raw/'actual-pr-services-custody.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'state':'accepted','protocol':protocol,'estimate':ESTIMATE,'proof':str(raw/'actual-pr-services-custody.json'),'identity_sha256':proof['identity_sha256']}))


if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,subprocess.SubprocessError) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(2)
