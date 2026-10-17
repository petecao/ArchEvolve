import datetime,hashlib,json,os,pathlib,shlex,subprocess
P=pathlib.Path
supervisor=P('/data1/yanruj/lanl17-metadata-supervisor-cleanup60-20261007-a4.py')
fixture=P('/data1/yanruj/lanl17-metadata-supervisor-linux-fixture-20261007-a1.py')
helper=P('/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py')
raw=P('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a4')
control=P('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-control-20261007-a4')
source=P('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1')
primary=P('/data1/yanruj/ArchEvolve')
memacc=P('/data1/yanruj/Memacc-repro-20260925');relative='AgenticRefiner/scripts/host/socket_lane.sh';wrapper=memacc/relative
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args):return subprocess.check_output(list(map(str,args)),text=True,timeout=120).strip()
def git(repo,*args):return command(['git','-C',repo,*args])
assert os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()!=0
assert sha(supervisor)=='fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'
assert sha(fixture)=='a848ef2d5c6dba58e6814bf80d8bdf24edeb33812bda343ecf25ff6f28745b0f'
assert sha(helper)=='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
assert not raw.exists() and not control.exists()
assert git(source,'rev-parse','HEAD')=='f893fed400347ed23d92e917d8bde21b75e5375d' and not git(source,'status','--porcelain')
assert not git(primary,'diff','--name-only') and not git(primary,'diff','--cached','--name-only')
leases={n:json.loads((P('/data1/yanruj/lact-host-lease')/(n+'.meta.json')).read_text()) for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
assert all(d['state']=='released' for d in leases.values())
model=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a3')
assert (model/'runner-exit-code.txt').read_text().strip()=='0' and (model/'exit-code.txt').read_text().strip()=='0'
development=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-development-20261006-a3')
assert (development/'runner-exit-code.txt').read_text().strip()=='0' and (development/'exit-code.txt').read_text().strip()=='0'
accepted=json.loads((development/'acceptance.json').read_text())
assert accepted['identity_sha256']==hashlib.sha256(json.dumps({k:v for k,v in accepted.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
assert accepted['phase']=='development' and accepted['source_commit']=='f893fed400347ed23d92e917d8bde21b75e5375d' and accepted['source_clean'] is True and accepted['ready_for_holdout'] is True
assert json.loads((development/'final-cleanup.json').read_text())['survivors']=={}
development_lane=json.loads((development/'lane.json').read_text())['socket_lane']
assert development_lane['node']==0 and development_lane['numa_memory_policy']=='bind:0' and development_lane['exit_code']==0 and development_lane['ended_utc']
for phase in ('holdout','band-report'):
 assert not P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+phase+'-20261006-a3').exists()
git(memacc,'fetch','origin','yanrujhou_main')
latest=subprocess.check_output(['git','-C',str(memacc),'show','origin/yanrujhou_main:'+relative],timeout=120)
assert latest==wrapper.read_bytes() and sha(wrapper)=='00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
capacity={mount:os.statvfs(mount).f_bavail*os.statvfs(mount).f_frsize for mount in ('/data1','/data')}
available=int(next(line.split()[1] for line in P('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
assert available>=80*1024**3 and capacity['/data1']>=21*1024**3 and capacity['/data']>=2*1024**3
control.mkdir()
proof={'format':'swdb.lanl17-metadata-fixture-dispatch.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_C_preserved':True,'supervisor_sha256':sha(supervisor),'fixture_sha256':sha(fixture),'selected_helper_sha256':sha(helper),'wrapper_sha256':sha(wrapper),'both_lanes_free_before_dispatch':True,'prior_model_completed':True,'prior_development_completed':True,'holdout_report_absent':True,'capacity_bytes':capacity,'memory_available_bytes':available,'outer_s':180,'outer_kill_after_s':60,'fixture_alarm_s':120,'application_outcomes_collected':0,'provider_calls':0,'scope':'Owned Linux process fixture only; no model/population/campaign admission.'}
proof['identity_sha256']=hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
(control/'preregistration.json').write_text(json.dumps(proof,indent=2)+'\n')
argv=['timeout','--signal=TERM','--kill-after=60s','180s','bash',wrapper,'1','swdb-lanl17-metadata-supervisor-fixture-20261007-a4','--no-align','--record',control/'lane.json','--','python3',fixture,'--supervisor',supervisor,'--supervisor-sha',sha(supervisor),'--helper',helper,'--project',source/'swdb-project','--output',raw]
shell=' '.join(shlex.quote(str(v)) for v in argv)+' > '+shlex.quote(str(control/'wrapper.stdout'))+' 2> '+shlex.quote(str(control/'wrapper.stderr'))+'; lanl17_fixture_exit=$?; printf "%s\\n" "$lanl17_fixture_exit" > '+shlex.quote(str(control/'exit-code.txt'))
command(['tmux','new-session','-d','-s','swdb-lanl17-metadata-supervisor-fixture-20261007-a4',shell])
print(json.dumps({'dispatched':True,'control':str(control),'raw':str(raw),'preregistration_identity':proof['identity_sha256'],'node':1,'native_or_provider_commands':0}))
