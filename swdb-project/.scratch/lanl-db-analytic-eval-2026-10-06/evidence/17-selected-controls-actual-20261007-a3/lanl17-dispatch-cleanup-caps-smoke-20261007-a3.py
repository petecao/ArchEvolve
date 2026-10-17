import datetime,hashlib,json,os,pathlib,shlex,subprocess
P=pathlib.Path
root=P('/data1/yanruj');source=root/'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
helper=root/'lanl17-control-caps-20261007-a3.py';smoke=root/'lanl17-control-linux-smoke-20261006.py'
raw=P('/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a3')
control=P('/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-control-20261007-a3')
memacc=root/'Memacc-repro-20260925';relative='AgenticRefiner/scripts/host/socket_lane.sh';wrapper=memacc/relative
def command(argv):return subprocess.check_output(list(map(str,argv)),text=True,timeout=120).strip()
def git(folder,*args):return command(['git','-C',folder,*args])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()!=0
assert sha(helper)=='69dcfe546d3042228ccca4fb29e8409da88443ba15680f30bfdc929ea12ae2b9'
assert sha(smoke)=='4d0bdf1d4c8d2ce96d948085a785cde15c389a4c50413962bc7db14df57cf9d6'
assert not raw.exists() and not control.exists()
assert git(source,'rev-parse','HEAD')=='f893fed400347ed23d92e917d8bde21b75e5375d' and not git(source,'status','--porcelain')
leases={n:json.loads((root/'lact-host-lease'/(n+'.meta.json')).read_text()) for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
assert all(d['state']=='released' for d in leases.values())
for phase in ('development','holdout','band-report'):
 assert not P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+phase+'-20261006-a3').exists()
git(memacc,'fetch','origin','yanrujhou_main')
latest=subprocess.check_output(['git','-C',str(memacc),'show','origin/yanrujhou_main:'+relative],timeout=120)
assert latest==wrapper.read_bytes() and sha(wrapper)=='00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
capacity={m:os.statvfs(m).f_bavail*os.statvfs(m).f_frsize for m in ('/data1','/data')}
memory=int(next(x.split()[1] for x in P('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
assert memory>=80*1024**3 and capacity['/data1']>=21*1024**3 and capacity['/data']>=2*1024**3
control.mkdir()
proof={'format':'swdb.lanl17-selected-helper-smoke-dispatch.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'helper_sha256':sha(helper),'smoke_sha256':sha(smoke),'source_commit':'f893fed400347ed23d92e917d8bde21b75e5375d','source_clean':True,'wrapper_sha256':sha(wrapper),'leases':leases,'capacity_bytes':capacity,'memory_available_bytes':memory,'node':1,'outer_s':180,'outer_kill_after_s':60,'application_outcomes_collected':0,'provider_calls':0,'scope':'Actual process cleanup only; no scientific/campaign metadata action.'}
proof['identity_sha256']=hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
(control/'preregistration.json').write_text(json.dumps(proof,indent=2)+'\n')
argv=['timeout','--signal=TERM','--kill-after=60s','180s','bash',wrapper,'1','swdb-lanl17-cleanup-smoke-20261007-a3','--no-align','--record',control/'lane.json','--','python3',smoke,'--helper',helper,'--helper-sha',sha(helper),'--project',source/'swdb-project','--output',raw]
shell=' '.join(shlex.quote(str(v)) for v in argv)+' > '+shlex.quote(str(control/'wrapper.stdout'))+' 2> '+shlex.quote(str(control/'wrapper.stderr'))+'; lanl17_smoke_exit=$?; printf "%s\\n" "$lanl17_smoke_exit" > '+shlex.quote(str(control/'exit-code.txt'))
assert all(json.loads((root/'lact-host-lease'/(n+'.meta.json')).read_text())['state']=='released' for n in leases)
command(['tmux','new-session','-d','-s','swdb-lanl17-cleanup-smoke-20261007-a3',shell])
print(json.dumps({'dispatched':True,'control':str(control),'raw':str(raw),'node':1,'preregistration_identity':proof['identity_sha256']}))
