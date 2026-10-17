"""Export compact prospective native evidence after each complete bounded phase; raw timing/build/IR remain remote."""
from pathlib import Path
import hashlib,json,os,shutil,socket,subprocess,sys
phase,revision=sys.argv[1:3];assert phase in ('development','holdout') and len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
assert socket.gethostname().split('.')[0]=='mbit10'
source=Path('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1');raw=Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+phase+'-20261006-a3')
checkout=Path('/data1/yanruj/ArchEvolve-lanl-cpu-'+phase+'-evidence-20261006-a3');branch='codex/lanl-cpu-'+phase+'-evidence-a3'
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*map(str,args)],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not checkout.exists() and git(source,'rev-parse','HEAD')==revision and not git(source,'status','--porcelain')
leases={n:json.loads((Path('/data1/yanruj/lact-host-lease')/(n+'.meta.json')).read_text()) for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')};assert all(d['state']=='released' for d in leases.values())
assert (raw/'runner-exit-code.txt').read_text().strip()=='0' and (raw/'exit-code.txt').read_text().strip()=='0'
lane=json.loads((raw/'lane.json').read_text())['socket_lane'];assert lane['exit_code']==0 and lane['ended_utc'] and lane['node']==0 and lane['numa_memory_policy']=='bind:0'
sys.dont_write_bytecode=True;sys.path.insert(0,str(source/'swdb-project'));from swdb import artifacts,access
proof=json.loads((raw/'acceptance.json').read_text());assert proof['identity_sha256']==artifacts.digest({k:v for k,v in proof.items() if k!='identity_sha256'})
assert proof['source_commit']==revision and proof['source_clean'] is True and proof['raw_transferred'] is False and proof['phase']==phase
assert proof['application_performance_timings_collected']==(phase!='model') and proof['validation'].startswith('OK: ')
pre=json.loads((raw/'preregistration.json').read_text());assert pre['source_commit']==revision
before=source/'swdb-project/records' if phase=='model' else Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+('model' if phase=='development' else 'development')+'-20261006-a3/records')
prior={str(p.relative_to(before)):sha(p) for p in before.rglob('*.yaml')}
assert len(prior)==proof['prior_record_bytes_preserved']
assert all((raw/'records'/rel).is_file() and sha(raw/'records'/rel)==digest for rel,digest in prior.items())
allowed={'target_description':1,'protocol':2,'estimate':4} if phase=='model' else {'cpu_native_validation':2,'cpu_error_band':2}
new=[];seen={};timings=[]
for p in sorted((raw/'records').rglob('*.yaml')):
 rel=str(p.relative_to(raw/'records'))
 if rel in prior:continue
 d=access.read_record(p);kind=d['kind'];assert kind in allowed
 assert d['id'].startswith('lanl.cpu.') or (phase=='model' and kind=='target_description' and d['id']=='mbit10.cpu.lanl20261006.t1.services.v1')
 seen[kind]=seen.get(kind,0)+1
 new.append({'id':d['id'],'kind':kind,'path':rel,'sha256':artifacts.digest(d),'file_sha256':sha(p),'bytes':p.stat().st_size})
 if kind=='cpu_native_validation':
  assert d['evidence_kind']=='native' and d['threads']==1 and d['correctness']['checks']==['PASS']*5 and d['correctness']['separate_process'] is True
  assert d['context']['instrumented_timer'] is False and d['context']['dirty'] is False
  timings.append({'id':d['id'],'characterization':d['characterization'],'input':d['input'],'implementation':d['implementation'],'median_whole_call_s':d['summary']['median_whole_call_s'],'trials':d['trials'],'correctness':d['correctness'],'estimate_protocol':d['estimate_protocol'],'development_band':d['development_band'],'scope':d['scope'],'context_sha256':artifacts.digest(d['context'])})
assert seen==allowed,(seen,allowed)
summary={'format':'swdb.prospective-native-model-compact-receipt.v1','updated':'2026-10-06 ET','phase':phase,'source_commit':revision,'source_clean':True,'raw_directory':str(raw),'raw_transferred':False,'acceptance':proof,'lane':lane,'preregistration_sha256':sha(raw/'preregistration.json'),'new_records':new,'prior_records_preserved':len(prior),'matched_native_observations':timings,'scope':'Exact prospective ArchEvolve T1 original-driver whole-call validation; conditional independently constructed model. Five printed times form one scoped workload pair each; no region timing measurement or unseen-target confidence.'}
summary['identity_sha256']=artifacts.digest(summary)
git(source,'worktree','add','-b',branch,checkout,revision);paths=[]
# Later phases include all additive earlier evidence so a branch from the same immutable source is self-contained.
for p in sorted((raw/'records').rglob('*.yaml')):
 rel=p.relative_to(raw/'records');dest=checkout/'swdb-project/records'/rel
 if dest.exists():assert sha(dest)==sha(p);continue
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);paths.append(str(dest.relative_to(checkout)))
evidence=checkout/'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence';path=evidence/('11-cpu-'+phase+'-mbit10-20261006-a3.json');assert not path.exists();path.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n');paths.append(str(path.relative_to(checkout)))
assert all(s.startswith('swdb-project/') for s in paths);git(checkout,'add','--',*paths);git(checkout,'diff','--cached','--check');git(checkout,'commit','-m','Record prospective CPU '+phase+' validation evidence');git(checkout,'push','-u','origin',branch);assert not git(checkout,'status','--porcelain')
print(json.dumps({'commit':git(checkout,'rev-parse','HEAD'),'branch':branch,'phase':phase,'receipt_identity':summary['identity_sha256'],'validation':proof['validation'],'new_phase_records':new,'exported_paths':len(paths),'raw_transferred':False}))
