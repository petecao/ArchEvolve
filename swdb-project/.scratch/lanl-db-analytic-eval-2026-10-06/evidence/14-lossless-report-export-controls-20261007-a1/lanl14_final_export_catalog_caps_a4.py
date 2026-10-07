"""Parent-only compact nine-report Git export. Prepared 2026-10-07 ET.
Exact 18 new protocol/estimate records + report/request/custody metadata only.
No SSH, provider, native execution, raw IR/log/count/address stream transfer.
"""
import argparse,ctypes,hashlib,importlib.util,json,os,re,shutil,signal,subprocess,sys
from pathlib import Path

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def success(h,m):
 raw=Path(m['raw']);control=raw/'control';acceptance=h.checked(control/'acceptance.json');dispatch=h.checked(control/'dispatch.json')
 assert (control/'runner-exit-code.txt').read_text().strip()==(control/'wrapper-exit-code.txt').read_text().strip()=='0'
 assert acceptance['manifest_sha256']==dispatch['manifest_sha256']==m['identity_sha256'] and acceptance['source_commit']==m['source_commit'] and acceptance['source_clean'] is True
 assert acceptance['all_nine_public_estimates'] is True and acceptance['prior_record_library_app_bytes_preserved'] is True and acceptance['raw_transferred'] is False
 assert acceptance['provider_calls']==acceptance['application_timings']==0 and json.loads((control/'final-cleanup.json').read_text())['survivors']=={}
 lane=json.loads((control/'lane.json').read_text())['socket_lane'];node=dispatch['node']
 assert lane['exit_code']==0 and lane['ended_utc'] and lane['job']==dispatch['job']=='swdb-lanl14-reports-'+m['tag'] and lane['node']==node
 assert lane['lease_name']==f'mbit10-evaluation-node{node}' and lane['numa_memory_policy']==f'bind:{node}' and lane['command']==dispatch['command']
 assert lane['command']==['python3',str(control/'helper.py'),'run','--manifest',str(raw/'manifest.json')]
 assert h.sha(control/'helper.py')==m['helper']['sha256']
 report=h.checked(raw/'report/report.json');request=h.checked(raw/'report-request.json')
 assert acceptance['report_sha256']==report['identity_sha256'] and acceptance['request_sha256']==request['identity_sha256']==report['request_sha256']
 assert report['code_equality']['estimator_sha256']==m['estimator_sha256'] and report['code_equality']['module_hashes']==m['module_hashes'] and report['code_equality']['estimator_and_mechanism_diff']==[]
 assert request['pairs'][0]['estimate']==acceptance['fresh_dx_bfs_reference'] and request['pairs'][0]['kernel']=='bfs' and request['pairs'][0]['target']=='dx100'
 assert len(request['pairs'])==len(report['pairs'])==9
 assert (raw/'final-validate.stdout').read_text().strip()==acceptance['validation'] and acceptance['validation'].startswith('OK: ')
 return acceptance,lane,request,report
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('manifest','helper','checkout','branch'):p.add_argument('--'+name,required=True)
 p.add_argument('--push',action='store_true');args=p.parse_args()
 raw_manifest=json.loads(Path(args.manifest).read_text());assert hashlib.sha256(Path(args.helper).read_bytes()).hexdigest()==raw_manifest['helper']['sha256']
 f=load(args.helper,'lanl14_final');h,m=f.checked_manifest(args.manifest);h.free_all();h.capacity()
 raw=Path(m['raw']);source=Path(m['source']);before=h.checked(raw/'protected.json');records=raw/'records';acceptance,lane,request,report=success(h,m)
 assert h.digest({k:v for k,v in before.items() if k!='identity_sha256'})==m['protected_sha256']
 after=h.inventory(records);added=h.preservation(before['records'],after)
 assert added==acceptance['added_record_paths'] and len(added)==18 and all(p.startswith(('protocols/','estimates/')) and p.endswith('.yaml') for p in added)
 assert h.inventory(raw/'library')==h.inventory(source/'swdb-project/library')==before['library']
 assert h.inventory(source/'swdb-project/records')==before['records'] and h.inventory(source/'swdb-project/apps')==before['apps']
 artifacts,access,_,_,_,Store,identity=f.public_imports(source);store=Store(records)
 closure=[]
 for pair in request['pairs']:
  for name,kind in [('protocol','protocol'),('estimate','estimate')]:
   expected=pair[name];data=f.get(store,expected['id'],kind);actual=f.pin(h,store,data['id'])
   assert actual==expected and data['id'] not in {row['id'] for row in closure}
   if kind=='protocol':assert data['settings']['estimator_sha256']==m['estimator_sha256']
   else:assert data['estimator_sha256']==m['estimator_sha256']
   closure.append({**actual,'bytes':(records/actual['path']).stat().st_size})
 assert {row['path'] for row in closure}==set(added) and sum(row['kind']=='protocol' for row in closure)==9
 checkout=Path(args.checkout).resolve();assert str(checkout).startswith('/data1/yanruj/ArchEvolve-lanl-') and not checkout.exists()
 assert re.fullmatch('codex/lanl-generality-estimate-evidence-[a-z0-9-]+',args.branch)
 assert subprocess.run(['git','-C',str(source),'show-ref','--verify','--quiet','refs/heads/'+args.branch],timeout=30).returncode!=0
 assert h.git(source,'ls-remote','--heads','origin',args.branch)==''
 # No mutable Git checkout until the complete raw acceptance/source/byte proof.
 h.git(source,'worktree','add','-b',args.branch,checkout,m['source_commit']);paths=[]
 for path in added:
  dest=checkout/'swdb-project/records'/path;assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(records/path,dest)
  assert h.sha(dest)==after[path];paths.append('swdb-project/records/'+path)
 assert ctypes.CDLL(None).prctl(36,1,0,0,0)==0
 from swdb.processes import stop_group
 cleanup=load(m['cleanup_helper']['path'],'lanl14_final_export_cleanup');child=None
 def interrupted(signum,frame):raise InterruptedError('final export signal '+str(signum))
 for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,interrupted)
 try:
  with (raw/'export-validate.stdout').open('w') as out,(raw/'export-validate.stderr').open('w') as err:
   env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(checkout/'swdb-project'),'TMPDIR':str(raw/'temporary'),'OMP_THREAD_LIMIT':'16','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
   child=subprocess.Popen(['python3','-m','swdb','validate','--records',str(checkout/'swdb-project/records'),'--library',str(checkout/'swdb-project/library')],cwd=checkout/'swdb-project',env=env,stdout=out,stderr=err,start_new_session=True)
   assert child.wait(timeout=3600)==0,'Preserve failed evidence W; no commit/push'
 finally:
  for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,signal.SIG_IGN)
  stop_group(child,grace_seconds=15);assert cleanup.cleanup_owned()['survivors']=={}
 validation=(raw/'export-validate.stdout').read_text().strip();assert validation.startswith('OK: ')
 assert h.preservation(before['records'],h.inventory(checkout/'swdb-project/records'))==added
 assert h.inventory(checkout/'swdb-project/library')==before['library'] and h.inventory(checkout/'swdb-project/apps')==before['apps']
 proof=h.seal({'format':'swdb.lanl14-final-report-export.v1','updated':'2026-10-07 ET','created_utc':h.now(),'source_commit':m['source_commit'],'source_clean':True,
  'manifest_sha256':m['identity_sha256'],'helper_sha256':m['helper']['sha256'],'exporter_sha256':h.sha(__file__),'acceptance':acceptance,'lane':lane,
  'code_equality':report['code_equality'],'fresh_count_receipt':m['fresh_count_receipt'],'historical_count_file_pins':f.OLD_FILES,
  'new_records':closure,'nine_report_sha256':report['identity_sha256'],'new_canonical_records':18,'prior_record_library_app_bytes_preserved':True,
  'validation':validation,'provider_calls':0,'application_timings':0,'raw_transferred':False,'cleanup_survivors':{},
  'scope':'Nine fresh public estimates on one final complete bundle. Exact all-trial reports retain nulls/unknowns; MAPLE is estimate-only and Jacobi has no BF/BC CPU band transfer.'})
 stem='14-generality-final-'+m['tag'];folder=checkout/'swdb-project'/f.EVIDENCE
 for original,suffix in [(raw/'report/report.json','-report.json'),(raw/'report/report.md','-report.md'),(raw/'report-request.json','-request.json')]:
  dest=folder/(stem+suffix);assert not dest.exists();shutil.copyfile(original,dest);assert h.sha(dest)==h.sha(original);paths.append(dest.relative_to(checkout).as_posix())
 evidence=folder/(stem+'-export.json');assert not evidence.exists();h.dump(evidence,proof);paths.append(evidence.relative_to(checkout).as_posix())
 h.clean(source,m['source_commit']);f.require_bundle(h,source,m);h.free_all();h.git(checkout,'add','--',*paths)
 assert set(h.git(checkout,'diff','--cached','--name-only').splitlines())==set(paths)
 h.git(checkout,'commit','-m','Record nine final-bundle generality estimates and exact per-trial reports')
 if args.push:h.git(checkout,'push','-u','origin',args.branch)
 assert not h.git(checkout,'status','--porcelain');h.clean(source,m['source_commit'])
 print(json.dumps({'commit':h.git(checkout,'rev-parse','HEAD'),'branch':args.branch,'pushed':args.push,'new_canonical_records':18,'metadata_paths':4,'identity_sha256':proof['identity_sha256'],'validation':validation,'raw_transferred':False}))

if __name__=='__main__':main()
