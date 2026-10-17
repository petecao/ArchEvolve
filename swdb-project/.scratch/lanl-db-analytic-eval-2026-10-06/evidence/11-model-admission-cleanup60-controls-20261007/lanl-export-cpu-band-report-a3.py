"""Compact public band-reader evidence only; no raw binaries, LLVM, logs or new timing are exported."""
from pathlib import Path
import hashlib,json,math,shutil,socket,subprocess,sys
revision=sys.argv[1];assert len(sys.argv)==2 and len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
assert socket.gethostname().split('.')[0]=='mbit10'
source=Path('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1')
raw=Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-band-report-20261006-a3')
M=Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a3');H=Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-holdout-20261006-a3')
checkout=Path('/data1/yanruj/ArchEvolve-lanl-cpu-band-report-evidence-20261006-a3');branch='codex/lanl-cpu-band-report-evidence-a3'
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*map(str,args)],text=True).strip()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert not checkout.exists() and git(source,'rev-parse','HEAD')==revision and not git(source,'status','--porcelain')
leases={n:json.loads((Path('/data1/yanruj/lact-host-lease')/(n+'.meta.json')).read_text()) for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')};assert all(d['state']=='released' for d in leases.values())
assert (raw/'runner-exit-code.txt').read_text().strip()=='0' and (raw/'exit-code.txt').read_text().strip()=='0'
lane=json.loads((raw/'lane.json').read_text())['socket_lane'];assert lane['exit_code']==0 and lane['ended_utc'] and lane['node']==0 and lane['numa_memory_policy']=='bind:0'
sys.dont_write_bytecode=True;sys.path.insert(0,str(source/'swdb-project'))
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

def inspect_export(before,records,proof,store,model,holdout,revision):
    original,bands,devs=check_inputs(store,model,holdout,revision)
    sealed(proof)
    assert proof['source_commit']==revision and proof['source_clean'] is True and proof['phase']=='band_report' and proof['raw_transferred'] is False
    assert proof['application_performance_timings_collected'] is False and proof['new_phase_records']==4 and proof['validation'].startswith('OK: ')
    assert proof['frozen_model_acceptance']['identity_sha256']==model['identity_sha256'] and proof['heldout_acceptance']['identity_sha256']==holdout['identity_sha256']
    assert proof['target_sha256']==model['target_sha256'] and proof['calibrations']==model['calibrations'] and proof['characterizations']==model['characterizations'] and proof['original_estimates']==model['estimates']
    assert proof['bands']=={k:{'id':b['id'],'sha256':artifacts.digest(b),'state':b['state'],'width_log':b['width_log'],'validated':b['admission']['validated']} for k,b in bands.items()}
    assert proof['development_bands']=={k:{'id':b['id'],'sha256':artifacts.digest(b),'width_log':b['width_log']} for k,b in devs.items()}
    assert set(proof['protocols'])=={'bfs','bc'} and len(proof['reports'])==2
    expected={p['id'] for p in proof['protocols'].values()}|{r['id'] for r in proof['reports']};assert len(expected)==4
    prior={str(p.relative_to(before)):sha(p) for p in before.rglob('*.yaml')};assert len(prior)==proof['prior_record_bytes_preserved']
    assert all((records/rel).is_file() and sha(records/rel)==digest for rel,digest in prior.items()),'prior heldout bytes changed'
    new=[];seen={}
    for path in sorted(records.rglob('*.yaml')):
        relative=str(path.relative_to(records))
        if relative in prior:continue
        d=access.read_record(path)
        assert d['id'] in expected and d['kind'] in ('protocol','estimate'),'unexpected phase record'
        kernel=d['id'].split('.')[2];band=bands[kernel]
        seen[d['kind']]=seen.get(d['kind'],0)+1
        new.append({'id':d['id'],'kind':d['kind'],'path':relative,'sha256':artifacts.digest(d),'file_sha256':sha(path),'bytes':path.stat().st_size})
        if d['kind']=='protocol':
            kernel=next(k for k,pin in proof['protocols'].items() if pin['id']==d['id']);assert artifacts.digest(d)==proof['protocols'][kernel]['sha256']
            old=store.get(model['protocols'][kernel]['id'],'protocol')
            assert d['settings']['target_description']==old['settings']['target_description'] and d['settings']['estimator_sha256']==old['settings']['estimator_sha256']
            for field in ('inputs','input_run_arguments','sources','roi','threads'):assert d['settings'][field]==old['settings'][field]
            pin=d['settings']['cpu_error_band'];assert pin['id']==band['id'] and pin['sha256']==artifacts.digest(band) and pin['snapshot']==band
        else:
            row=next(r for r in proof['reports'] if r['id']==d['id']);old=original[row['original_estimate']]
            assert old['id'] in {'lanl.cpu.'+k+'.g17.t1.estimate.v1' for k in ('bfs','bc')}
            assert artifacts.digest(d)==row['sha256'] and artifacts.digest(old)==row['original_estimate_sha256']
            for field in ('seconds','regions','subject','input','threads','target','evidence_kind','characterization','characterization_sha256','target_description_sha256','estimator_sha256'):assert d[field]==old[field]
            assert row['seconds_unchanged'] is True and row['per_region_costs_unchanged'] is True and row['per_region_costs_sha256']==artifacts.digest(d['regions'])
            assert d['error_band']==row['error_band'] and d['verdict']==row['verdict']=='within_error'
            assert d['error_band']['state']==band['state'] and d['error_band']['width_log']==band['width_log'] and d['error_band']['validated'] is (band['state']=='validated' and band['admission']['validated'] is True)
    assert seen=={'protocol':2,'estimate':2} and {row['id'] for row in new}==expected
    return new,len(prior)

proof=json.loads((raw/'acceptance.json').read_text());model=json.loads((M/'acceptance.json').read_text());holdout=json.loads((H/'acceptance.json').read_text())
store=Store(raw/'records');new,preserved=inspect_export(H/'records',raw/'records',proof,store,model,holdout,revision)
pre=json.loads((raw/'preregistration.json').read_text());assert pre['source_commit']==revision
summary={'format':'swdb.cpu-band-report-compact-receipt.v1','updated':'2026-10-06 ET','source_commit':revision,'source_clean':True,'raw_directory':str(raw),'raw_transferred':False,'application_performance_timings_collected':False,'acceptance':proof,'lane':lane,'preregistration_sha256':sha(raw/'preregistration.json'),'new_phase_records':new,'prior_heldout_records_preserved':preserved,'scope':'Four new public band-reader records plus prior additive typed closure only. Exact held-out g17 scopes, unchanged seconds/per-region costs and width; failed bands remain unvalidated. No raw logs/builds/IR or new application execution.'}
summary['identity_sha256']=artifacts.digest(summary)
git(source,'worktree','add','-b',branch,checkout,revision);paths=[]
for path in sorted((raw/'records').rglob('*.yaml')):
    relative=path.relative_to(raw/'records');destination=checkout/'swdb-project/records'/relative
    if destination.exists():assert sha(destination)==sha(path);continue
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination);paths.append(str(destination.relative_to(checkout)))
evidence=checkout/'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence';path=evidence/'11-cpu-band-report-mbit10-20261006-a3.json';assert not path.exists()
path.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n');paths.append(str(path.relative_to(checkout)))
assert all(path.startswith('swdb-project/') for path in paths)
git(checkout,'add','--',*paths);git(checkout,'diff','--cached','--check');git(checkout,'commit','-m','Record exact CPU band-reader replay evidence');git(checkout,'push','-u','origin',branch);assert not git(checkout,'status','--porcelain')
print(json.dumps({'commit':git(checkout,'rev-parse','HEAD'),'branch':branch,'receipt_identity':summary['identity_sha256'],'new_phase_records':new,'exported_paths':len(paths),'raw_transferred':False}))
