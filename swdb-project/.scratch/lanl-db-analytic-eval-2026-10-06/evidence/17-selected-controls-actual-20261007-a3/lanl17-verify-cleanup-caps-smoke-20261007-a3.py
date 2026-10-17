import datetime,hashlib,json,os,pathlib,subprocess
P=pathlib.Path;root=P('/data1/yanruj')
raw=P('/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a3')
control=P('/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-control-20261007-a3')
source=root/'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def sealed(p):
 d=json.loads(p.read_text());assert d['identity_sha256']==digest({k:v for k,v in d.items() if k!='identity_sha256'});return d
def git(*a):return subprocess.check_output(['git','-C',str(source),*a],text=True,timeout=120).strip()
assert os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()!=0
assert (control/'exit-code.txt').read_text().strip()=='0'
pre=sealed(control/'preregistration.json');assert pre['identity_sha256']=='4211ccb087923ab1d2ebe84c09d176ecb9f6a118a9fede2e91589bb73454a8ad'
lane=json.loads((control/'lane.json').read_text())['socket_lane']
assert lane['node']==1 and lane['lease_generation']==545 and lane['exit_code']==0 and lane['ended_utc'] and lane['numa_memory_policy']=='bind:1'
r=sealed(raw/'receipt.json')
assert r['identity_sha256']=='27024d06c22cb37995033a8db3010541a933b8e400e0ea2a06aba8a1449589b3'
assert r['passed'] is True and r['helper_sha256']=='69dcfe546d3042228ccca4fb29e8409da88443ba15680f30bfdc929ea12ae2b9'
assert r['smoke_script_sha256']=='4d0bdf1d4c8d2ce96d948085a785cde15c389a4c50413962bc7db14df57cf9d6'
assert r['processes_py_sha256']=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
assert r['cleanup']['subreaper'] is True and r['cleanup']['survivors']=={} and r['unrelated_sibling_survived'] is True
assert r['same_group_after_returned_leader']=='terminated' and r['detached_session']=='terminated_and_reaped'
assert r['provider_calls']==r['application_outcomes']==0
for key in r['owned_before'].values():
 try:now=(P('/proc')/str(key['pid'])/'stat').read_text().rsplit(')',1)[1].split();assert now[19]!=key['start_time']
 except (FileNotFoundError,ProcessLookupError):pass
assert git('rev-parse','HEAD')=='f893fed400347ed23d92e917d8bde21b75e5375d' and not git('status','--porcelain')
o={'format':'swdb.lanl17-selected-helper-linux-actual-compact.v1','verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'receipt':r,'receipt_file_sha256':sha(raw/'receipt.json'),'raw_directory':str(raw),'actual_cleanup_proof_path':str(raw/'receipt.json'),'lane':lane,'dispatch_preregistration':pre,'raw_transferred':False,'source_C_preserved':True,'scope':'Actual selected-helper process cleanup only; no scientific/metadata action, provider or application outcome.'}
o['identity_sha256']=digest(o);print(json.dumps(o,indent=2))
