import sys
sys.dont_write_bytecode=True
from pathlib import Path
import copy,datetime,json,math,os,shutil,signal,subprocess,time
S=Path(SOURCE_VALUE);R=Path(RAW_VALUE);C=COMMIT_VALUE;W=S/'swdb-project'
M=Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a3')
H=Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-holdout-20261006-a3')
status=0;child=None;deadline=time.monotonic()+9200
os.environ.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(R/'compiler-temp'))
sys.path.insert(0,str(W))
from swdb import artifacts,access
from swdb.store import Store

def sealed(document):
    assert document['identity_sha256']==artifacts.digest({k:v for k,v in document.items() if k!='identity_sha256'}),'receipt seal differs'

def check_inputs(store,model,holdout,revision):
    sealed(model);sealed(holdout)
    assert model['phase']=='model' and holdout['phase']=='holdout'
    assert model['source_commit']==holdout['source_commit']==revision and model['source_clean'] is True and holdout['source_clean'] is True
    assert model['ready_for_development'] is True and model['application_performance_timings_collected'] is False and holdout['application_performance_timings_collected'] is True
    assert holdout['frozen_model_acceptance']['identity_sha256']==model['identity_sha256']
    assert holdout['protocols']==model['protocols'] and set(model['protocols'])=={'bfs','bc'}
    target='mbit10.cpu.lanl20261006.t1.services.v1';td=store.get(target,'target_description')
    assert artifacts.digest(td)==model['target_sha256']
    binding=td['extensions']['cpu_services_binding']
    assert model['calibrations']==binding['calibrations'] and model['characterizations']==binding['characterization_allowlist']
    expected_chars={k+'.kron-g'+str(g)+'.t1.characterization.objects.a1' for k in ('bfs','bc') for g in (16,17)}
    assert len(model['characterizations'])==4 and {p['id'] for p in model['characterizations']}==expected_chars
    for pin in model['calibrations']+model['characterizations']:
        assert artifacts.digest(store.get(pin['id']))==pin['sha256'],'calibration/characterization changed'
    original={};expected_estimates={'lanl.cpu.'+k+'.g'+str(g)+'.t1.estimate.v1' for k in ('bfs','bc') for g in (16,17)}
    assert len(model['estimates'])==4 and {r['id'] for r in model['estimates']}==expected_estimates
    for row in model['estimates']:
        e=store.get(row['id'],'estimate');assert artifacts.digest(e)==row['sha256'],'original estimate changed'
        assert e['target_description_sha256']==model['target_sha256'] and e['threads']==1 and e['evidence_kind']=='execution'
        assert type(e['seconds']) in (int,float) and math.isfinite(e['seconds']) and e['seconds']>0
        original[e['id']]=e
    for kernel,pin in model['protocols'].items():
        protocol=store.get(pin['id'],'protocol');assert artifacts.digest(protocol)==pin['sha256'],'original protocol changed'
        settings=protocol['settings'];assert settings['target_description']['sha256']==model['target_sha256'] and settings['threads']==1
        for scale in (16,17):
            e=original['lanl.cpu.'+kernel+'.g'+str(scale)+'.t1.estimate.v1']
            char=store.get(kernel+'.kron-g'+str(scale)+'.t1.characterization.objects.a1','workload_characterization')
            assert e['protocol']==pin['id'] and e['estimator_sha256']==settings['estimator_sha256']
            assert e['characterization']==char['id'] and e['characterization_sha256']==artifacts.digest(char)
            assert e['input']==char['input'] and e['subject']['id']==char['subject']['id']
            assert settings['input_run_arguments'][char['input']]==char['source']['run_arguments']
            assert settings['sources']==[char['subject']['id']] and settings['roi']==char['binding']['roi']
    assert set(holdout['bands'])=={'bfs','bc'}
    bands={};devs={}
    for kernel,pin in holdout['bands'].items():
        band=store.get(pin['id'],'cpu_error_band');sealed(band)
        assert pin['id']=='lanl.cpu.'+kernel+'.t1.heldout-band.v1'
        assert artifacts.digest(band)==pin['sha256'] and band['state']==pin['state'] and band['width_log']==pin['width_log']
        assert band['evidence_kind']=='native' and band['state'] in ('validated','failed') and band['admission']['validated']==(band['state']=='validated')
        assert band['target_description_sha256']==model['target_sha256'] and band['threads']==1
        assert type(band['width_log']) in (int,float) and math.isfinite(band['width_log']) and band['width_log']>=0
        dev=store.get(band['development_band'],'cpu_error_band');sealed(dev)
        assert dev['id']=='lanl.cpu.'+kernel+'.t1.development-band.v1'
        assert dev['state']=='development' and dev['evidence_kind']=='native' and dev['width_log']==band['width_log']
        assert len(band['pairs'])==1 and band['pairs'][0]['estimate']=='lanl.cpu.'+kernel+'.g17.t1.estimate.v1'
        pair=band['pairs'][0];e=original[pair['estimate']]
        assert pair['estimate_sha256']==artifacts.digest(e) and pair['characterization']==e['characterization'] and pair['characterization_sha256']==e['characterization_sha256']
        assert pair['input']==e['input'] and pair['scope']['implementation']==e['subject']['id']
        assert e['estimator_sha256']==band['estimator_sha256']
        if band['state']=='validated':assert not pair['missing']
        bands[kernel]=band;devs[kernel]=dev
    return original,bands,devs

def perform_report(store,model,holdout,revision,model_dir,root,run):
    original,bands,devs=check_inputs(store,model,holdout,revision)
    rows=[];protocols={};prefix=['python3','-m','swdb']
    keys={'mode','estimator_version','target_description','inputs','input_run_arguments','sources','roi','threads'}
    for kernel in ('bfs','bc'):
        band=bands[kernel];dev=devs[kernel]
        previous=store.get(model['protocols'][kernel]['id'],'protocol')
        request=json.loads((model_dir/(kernel+'-protocol-request.json')).read_text());assert set(request['settings'])==keys
        expected=copy.deepcopy(previous['settings']);expected['target_description']=expected['target_description']['id']
        assert all(request['settings'][k]==expected[k] for k in keys),'raw per-kernel request differs from frozen protocol'
        request['id']='lanl.cpu.'+kernel+'.t1.report-model.v1';request['settings']['cpu_error_band']=band['id']
        path=root/(kernel+'-request.json');path.write_text(json.dumps(request,indent=2)+'\n')
        p=json.loads(run([*prefix,'freeze-protocol',path,'--records',root/'records','--format','json'],'freeze-'+kernel,1800))
        assert p['id']==request['id']+'.'+p['identity_sha256'][:16]
        assert p['settings']['estimator_sha256']==previous['settings']['estimator_sha256'] and p['settings']['target_description']==previous['settings']['target_description']
        assert p['settings']['cpu_error_band']['id']==band['id'] and p['settings']['cpu_error_band']['sha256']==artifacts.digest(band)
        protocols[kernel]={'id':p['id'],'sha256':artifacts.digest(p)}
        old=original['lanl.cpu.'+kernel+'.g17.t1.estimate.v1']
        e=json.loads(run([*prefix,'estimate','--records',root/'records','--characterization',old['characterization'],'--target-description','mbit10.cpu.lanl20261006.t1.services.v1','--protocol',p['id'],'--id','lanl.cpu.'+kernel+'.g17.t1.report.v1','--format','json'],'estimate-'+kernel,1400))
        for field in ('seconds','regions','subject','input','threads','target','evidence_kind','characterization','characterization_sha256','target_description_sha256','estimator_sha256'):
            assert e[field]==old[field],'report changed '+field
        assert e['protocol']==p['id']
        reported=e['error_band'];expected_validated=band['state']=='validated' and band['admission']['validated'] is True
        assert reported['id']==band['id'] and reported['sha256']==artifacts.digest(band) and reported['state']==band['state'] and reported['width_log']==band['width_log'] and reported['validated'] is expected_validated
        assert reported['missing']==band['admission']['missing'] and e['verdict']=='within_error'
        rows.append({'id':e['id'],'sha256':artifacts.digest(e),'original_estimate':old['id'],'original_estimate_sha256':artifacts.digest(old),'seconds':e['seconds'],'per_region_costs_sha256':artifacts.digest(e['regions']),'seconds_unchanged':True,'per_region_costs_unchanged':True,'error_band':reported,'verdict':e['verdict']})
    return {'protocols':protocols,'reports':rows,
        'bands':{k:{'id':b['id'],'sha256':artifacts.digest(b),'state':b['state'],'width_log':b['width_log'],'validated':b['admission']['validated']} for k,b in bands.items()},
        'development_bands':{k:{'id':b['id'],'sha256':artifacts.digest(b),'width_log':b['width_log']} for k,b in devs.items()}}

sys.path.insert(0,str(W))
from swdb.processes import stop_group
import ctypes,importlib.util
cleanup_path=Path('/data1/yanruj/lanl17-control-20261006.py')
assert hashlib.sha256(cleanup_path.read_bytes()).hexdigest()=='31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
assert hashlib.sha256((W/'swdb/processes.py').read_bytes()).hexdigest()=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
proof=json.loads((W/'.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-linux-cleanup-smoke-mbit10-20261006-a1.json').read_text())['receipt']
assert proof['passed'] is True and proof['helper_sha256']=='31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec' and proof['cleanup']['survivors']=={}
assert proof['processes_py_sha256']=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
assert sys.platform=='linux' and ctypes.CDLL(None).prctl(36,1,0,0,0)==0
spec=importlib.util.spec_from_file_location('cpu_owned_cleanup',cleanup_path);cleanup=importlib.util.module_from_spec(spec);spec.loader.exec_module(cleanup)

def clean():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==C
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=S,text=True)

def stop(signum,frame):raise RuntimeError('report runner signal '+str(signum))
for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,stop)

def run(args,name,cap=1400):
    global child
    remaining=min(cap,deadline-time.monotonic()-45);assert remaining>0
    with (R/(name+'.stdout')).open('w') as out,(R/(name+'.stderr')).open('w') as err:
        child=subprocess.Popen(list(map(str,args)),cwd=W,stdout=out,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=remaining)
        finally:
            stop_group(child,grace_seconds=15);child=None
            cleaned=cleanup.cleanup_owned()
            (R/(name+'.cleanup.json')).write_text(json.dumps(cleaned,indent=2)+'\n')
            assert cleaned['survivors']=={},'owned descendants survived stage cleanup'
    assert code==0,name+' exit '+str(code)
    return (R/(name+'.stdout')).read_text()

try:
    clean();(R/'started.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
    for parent in (M,H):
        assert (parent/'runner-exit-code.txt').read_text().strip()=='0' and (parent/'exit-code.txt').read_text().strip()=='0'
    model=json.loads((M/'acceptance.json').read_text());holdout=json.loads((H/'acceptance.json').read_text())
    shutil.copytree(H/'records',R/'records');(R/'library').symlink_to(W/'library',target_is_directory=True)
    prior={str(p.relative_to(R/'records')):artifacts.file_hash(p) for p in (R/'records').rglob('*.yaml')}
    result=perform_report(Store(R/'records'),model,holdout,C,M,R,run)
    store=Store(R/'records')
    for pin in list(result['protocols'].values())+result['reports']:
        assert artifacts.digest(store.get(pin['id']))==pin['sha256'],'CLI output/persisted record differs'
    validation=run(['python3','-m','swdb','validate','--records',R/'records'],'validate',1400).strip();assert validation.startswith('OK: ')
    assert all((R/'records'/rel).is_file() and artifacts.file_hash(R/'records'/rel)==sha for rel,sha in prior.items()),'prior canonical bytes changed'
    new=[p for p in (R/'records').rglob('*.yaml') if str(p.relative_to(R/'records')) not in prior];assert len(new)==4
    summary={'format':'swdb.cpu-band-report-acceptance.v1','phase':'band_report','updated':'2026-10-06 ET','source_commit':C,'source_clean':True,'raw_transferred':False,'application_performance_timings_collected':False,'new_phase_records':4,'frozen_model_acceptance':{'path':str(M/'acceptance.json'),'identity_sha256':model['identity_sha256']},'heldout_acceptance':{'path':str(H/'acceptance.json'),'identity_sha256':holdout['identity_sha256']},'target_sha256':model['target_sha256'],'calibrations':model['calibrations'],'characterizations':model['characterizations'],'original_estimates':model['estimates'],'prior_record_bytes_preserved':len(prior),'validation':validation,'scope':'Exact g17 original-driver counted scopes only. Reporting replay adds the immutable held-out band; no timing, predicted-cost change, width change, fitting or unseen confidence.',**result}
    clean();summary['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();summary['identity_sha256']=artifacts.digest(summary)
    (R/'acceptance.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
except BaseException as exc:
    status=1;(R/'runner-error.txt').write_text(type(exc).__name__+': '+str(exc)+'\n')
finally:
    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,signal.SIG_IGN)
    stop_group(child,grace_seconds=15);child=None
    final_cleanup=cleanup.cleanup_owned();(R/'final-cleanup.json').write_text(json.dumps(final_cleanup,indent=2)+'\n');assert final_cleanup['survivors']=={}
    (R/'runner-exit-code.txt').write_text(str(status)+'\n');(R/'completed.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
sys.exit(status)
