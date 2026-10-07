import datetime,hashlib,json,os,pathlib,subprocess
P=pathlib.Path
raw=P('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a3')
control=P('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-control-20261007-a3')
source=P('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1');primary=P('/data1/yanruj/ArchEvolve')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def sealed(p):
 d=json.loads(p.read_text());assert d['identity_sha256']==digest({k:v for k,v in d.items() if k!='identity_sha256'});return d
def git(repo,*a):return subprocess.check_output(['git','-C',str(repo),*a],text=True,timeout=120).strip()
assert os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()!=0
assert (control/'exit-code.txt').read_text().strip()=='0'
pre=sealed(control/'preregistration.json')
assert pre['identity_sha256']=='9cbee64cbd2a4bc05fb091f2a38f198e81c67497a28eef0ef00ca95bce4bf1f6'
lane=json.loads((control/'lane.json').read_text())['socket_lane']
assert lane['node']==1 and lane['lease_generation']==546 and lane['exit_code']==0 and lane['ended_utc'] and lane['numa_memory_policy']=='bind:1'
leases={n:json.loads((P('/data1/yanruj/lact-host-lease')/(n+'.meta.json')).read_text()) for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
assert all(d['state']=='released' for d in leases.values())
assert git(source,'rev-parse','HEAD')=='f893fed400347ed23d92e917d8bde21b75e5375d' and not git(source,'status','--porcelain')
assert not git(primary,'diff','--name-only') and not git(primary,'diff','--cached','--name-only')
project=source/'swdb-project'
modules={p.relative_to(project/'swdb').as_posix():sha(p) for p in sorted((project/'swdb').rglob('*.py'))}
assert len(modules)==185 and digest(modules)=='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
actual=sealed(raw/'receipt.json')
assert actual['passed'] is True and actual['fixture'] is True and actual['host']=='mbit10' and actual['uid']==os.getuid()
assert actual['helper_sha256']=='69dcfe546d3042228ccca4fb29e8409da88443ba15680f30bfdc929ea12ae2b9'
assert actual['supervisor_sha256']=='16661d7a9347e328a5263b06d807f3632c5abcfcf41a0bd97655a6bba302176b'
assert actual['fixture_script_sha256']=='a848ef2d5c6dba58e6814bf80d8bdf24edeb33812bda343ecf25ff6f28745b0f'
assert actual['processes_py_sha256']=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
assert actual['estimator_sha256']==digest(modules) and actual['cleanup']['subreaper'] is True and actual['cleanup']['survivors']=={} and actual['cleanup_errors']==[]
assert actual['provider_calls']==actual['application_outcomes']==0 and actual['failure_type'] is None
assert [r['case'] for r in actual['cases']]==['returned','timeout','term']
cases=[]
for row,code in zip(actual['cases'],(0,124,143)):
 assert row['passed'] is True and row['supervisor_exit']==code and row['unrelated_sibling_survived'] is True and row['owned_after']=='terminated_and_reaped'
 path=raw/row['case']/'supervisor-receipt.json';proof=sealed(path)
 assert sha(path)==row['supervisor_receipt_sha256'] and proof['identity_sha256']==row['supervisor_receipt_identity_sha256']
 assert proof['supervisor_exit']==code and proof['cleanup']['survivors']=={} and proof['cleanup_errors']==[] and proof['fixture'] is True
 for field in ('helper_sha256','supervisor_sha256','processes_py_sha256','estimator_sha256'):
  assert proof[field]==actual[field]
 for key in row['owned_before'].values():
  proc=P('/proc')/str(key['pid'])
  try:now=(proc/'stat').read_text().rsplit(')',1)[1].split();assert now[19]!=key['start_time'],'Fixture PID remained unreaped'
  except (FileNotFoundError,ProcessLookupError):pass
 cases.append({'case':row['case'],'receipt':proof,'file_sha256':sha(path)})
output={'format':'swdb.lanl17-metadata-supervisor-actual-compact.v1','verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_directory':str(raw),'control_directory':str(control),'raw_transferred':False,'receipt':actual,'receipt_file_sha256':sha(raw/'receipt.json'),'case_receipts':cases,'dispatch_preregistration':pre,'dispatch_preregistration_file_sha256':sha(control/'preregistration.json'),'lane':lane,'lane_file_sha256':sha(control/'lane.json'),'source_C_preserved':True,'primary_source_commit':git(primary,'rev-parse','HEAD'),'python_modules':185,'estimator_sha256':digest(modules),'node1_released':True,'legacy_released':True,'node0_state_after_fixture':leases['mbit10-evaluation-node0']['state'],'scope':'Actual owned process fixture cleanup only, no campaign/model/population/performance admission; original091/a2 plus fresh selected69dc primitive proof retained.'}
output['identity_sha256']=digest(output)
print(json.dumps(output,indent=2))
