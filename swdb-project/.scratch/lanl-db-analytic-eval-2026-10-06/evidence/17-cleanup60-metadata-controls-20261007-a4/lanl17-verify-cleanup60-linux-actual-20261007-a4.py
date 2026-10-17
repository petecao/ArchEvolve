"""Admit selected cleanup proof bytes only; no numerical/campaign admission."""
import argparse,datetime,hashlib,json,os,pathlib,re,subprocess
P=pathlib.Path;p=argparse.ArgumentParser();p.add_argument('--kind',choices=('helper','supervisor'),required=True);p.add_argument('--preregistration-identity',required=True);p.add_argument('--generation',required=True,type=int);a=p.parse_args()
assert re.fullmatch('[0-9a-f]{64}',a.preregistration_identity) and a.generation>=547
H='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414';SUP='fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0';F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3';C='f893fed400347ed23d92e917d8bde21b75e5375d'
source=P('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1');root=P('/data/yanruj/EvolveSWDB_runs')
stem='lanl17-cleanup-smoke' if a.kind=='helper' else 'lanl17-metadata-supervisor-fixture';raw=root/(stem+'-20261007-a4');control=root/(stem+'-control-20261007-a4')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def sealed(f):
 assert f.is_file() and f.stat().st_size<=1024*1024
 d=json.loads(f.read_bytes());assert d['identity_sha256']==digest({k:v for k,v in d.items() if k!='identity_sha256'});return d
def git(*args):return subprocess.check_output(['git','-C',str(source),*args],text=True,timeout=120).strip()
def gone(row):
 try:assert (P('/proc')/str(row['pid'])/'stat').read_text().rsplit(')',1)[1].split()[19]!=str(row['start_time']),'Owned PID/start identity survived'
 except (FileNotFoundError,ProcessLookupError):pass
assert os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()!=0
assert (control/'exit-code.txt').read_text().strip()=='0'
pre=sealed(control/'preregistration.json');assert pre['identity_sha256']==a.preregistration_identity
assert pre['helper_sha256' if a.kind=='helper' else 'selected_helper_sha256']==H
assert pre['outer_s']==180 and pre['outer_kill_after_s']==60
lane=json.loads((control/'lane.json').read_bytes())['socket_lane']
assert lane['node']==1 and lane['lease_generation']==a.generation and lane['exit_code']==0 and lane['ended_utc'] and lane['numa_memory_policy']=='bind:1'
job='swdb-'+stem+'-20261007-a4';assert lane['job']==job and lane['lease_name']=='mbit10-evaluation-node1'
helper=P('/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py');supervisor=P('/data1/yanruj/lanl17-metadata-supervisor-cleanup60-20261007-a4.py')
assert sha(helper)==H and sha(supervisor)==SUP
receipt=sealed(raw/'receipt.json');assert receipt['passed'] is True and receipt['helper_sha256']==H and receipt['host']=='mbit10'
assert receipt['processes_py_sha256']=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
assert receipt['cleanup']['subreaper'] is True and receipt['cleanup']['survivors']=={} and receipt['provider_calls']==receipt['application_outcomes']==0
cases=[]
if a.kind=='helper':
 smoke=P('/data1/yanruj/lanl17-control-linux-smoke-20261006.py')
 assert receipt['smoke_script_sha256']==sha(smoke)=='4d0bdf1d4c8d2ce96d948085a785cde15c389a4c50413962bc7db14df57cf9d6'
 assert receipt['platform']=='linux' and receipt['unrelated_sibling_survived'] is True
 assert receipt['same_group_after_returned_leader']=='terminated' and receipt['detached_session']=='terminated_and_reaped'
 assert set(receipt['owned_before'])=={'same_group','escaped_session'}
 for row in receipt['owned_before'].values():gone(row)
 assert lane['command']==['python3',str(smoke),'--helper',str(helper),'--helper-sha',H,'--project',str(source/'swdb-project'),'--output',str(raw)]
 assert pre['leases']['mbit10-evaluation-node1']['lease']['generation']+1==a.generation
else:
 fixture=P('/data1/yanruj/lanl17-metadata-supervisor-linux-fixture-20261007-a1.py')
 assert receipt['fixture'] is True and receipt['uid']==os.getuid() and receipt['supervisor_sha256']==pre['supervisor_sha256']==SUP
 assert receipt['fixture_script_sha256']==sha(fixture)=='a848ef2d5c6dba58e6814bf80d8bdf24edeb33812bda343ecf25ff6f28745b0f'
 assert receipt['estimator_sha256']==F6 and receipt['cleanup_errors']==[] and receipt['failure_type'] is None
 assert [row['case'] for row in receipt['cases']]==['returned','timeout','term']
 for row,code in zip(receipt['cases'],(0,124,143)):
  assert row['passed'] is True and row['supervisor_exit']==code and row['unrelated_sibling_survived'] is True and row['owned_after']=='terminated_and_reaped'
  f=raw/row['case']/'supervisor-receipt.json';r=sealed(f)
  assert sha(f)==row['supervisor_receipt_sha256'] and r['identity_sha256']==row['supervisor_receipt_identity_sha256']
  assert r['supervisor_exit']==code and r['cleanup']['survivors']=={} and r['cleanup_errors']==[] and r['fixture'] is True
  for field in ('helper_sha256','supervisor_sha256','processes_py_sha256','estimator_sha256'):assert r[field]==receipt[field]
  for owned in row['owned_before'].values():gone(owned)
  cases.append({'case':row['case'],'receipt':r,'file_sha256':sha(f)})
 assert lane['command']==['python3',str(fixture),'--supervisor',str(supervisor),'--supervisor-sha',SUP,'--helper',str(helper),'--project',str(source/'swdb-project'),'--output',str(raw)]
leases={n:json.loads((P('/data1/yanruj/lact-host-lease')/(n+'.meta.json')).read_bytes()) for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')};assert all(x['state']=='released' for x in leases.values())
assert git('rev-parse','HEAD')==C and not git('status','--porcelain')
modules={f.relative_to(source/'swdb-project/swdb').as_posix():sha(f) for f in sorted((source/'swdb-project/swdb').rglob('*.py'))};assert len(modules)==185 and digest(modules)==F6
out={'format':'swdb.parent17-cleanup60-linux-actual-compact.v1','kind':a.kind,'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'receipt':receipt,'receipt_file_sha256':sha(raw/'receipt.json'),'case_receipts':cases,'lane':lane,'lane_file_sha256':sha(control/'lane.json'),'dispatch_preregistration':pre,'dispatch_preregistration_file_sha256':sha(control/'preregistration.json'),'source_C_preserved':True,'estimator_sha256':F6,'all_lanes_released':True,'actual_cleanup_proof_path':str(raw/'receipt.json') if a.kind=='helper' else None,'raw_directory':str(raw),'raw_transferred':False,'scope':'Actual exact-hash Linux cleanup only; no native timing, metadata population or campaign admission.'};out['identity_sha256']=digest(out);print(json.dumps(out,indent=2))
