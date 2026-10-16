"""2026-10-15 ET. One reviewed exact-source profile with an explicit production-change allowlist."""
import hashlib,json,pathlib,re,subprocess,sys
sha,kind,seconds,node,command_path,change_review_path=sys.argv[1:]
assert re.fullmatch('[0-9a-f]{40}',sha) and re.fullmatch('[a-z0-9-]{1,60}',kind)
seconds=int(seconds);node=int(node)
assert 600 <= seconds <= 21600 and node in (0,1)
command=json.loads(pathlib.Path(command_path).read_text())
assert isinstance(command,list) and command and all(isinstance(s,str) for s in command)
review=json.loads(pathlib.Path(change_review_path).read_text())
assert review['source_commit']==sha and review['baseline']=='0e7f232762e4555aa9435a3a3622923fad8ee928'
changes=review['files_after']
assert isinstance(changes,dict)
assert isinstance(review['readers'],list) and 'root' in review['readers'] and all(isinstance(x,str) and x for x in review['readers'])
for name,h in changes.items():
 assert name.startswith(('swdb-project/swdb/','swdb-project/library/')) and '..' not in pathlib.PurePosixPath(name).parts
 assert h is None or re.fullmatch('[0-9a-f]{64}',h)
evidence=review['review_evidence']
assert hashlib.sha256(pathlib.Path(evidence['path']).read_bytes()).hexdigest()==evidence['sha256']
review_pin={'path':str(pathlib.Path(change_review_path).resolve()),'sha256':hashlib.sha256(pathlib.Path(change_review_path).read_bytes()).hexdigest(),'content':review}
cfg={'sha':sha,'kind':kind,'seconds':seconds,'node':node,'command':command,'change_review':review_pin}
script='cfg='+repr(cfg)+'\n'+r'''
import datetime,hashlib,json,pathlib,shlex,subprocess
P=pathlib.Path
sha=cfg['sha'];node=cfg['node'];seconds=cfg['seconds']
source=P('/data1/yanruj/probata-composed-0e7f2327') if sha=='0e7f232762e4555aa9435a3a3622923fad8ee928' else P('/data1/yanruj/probata-reviewed-'+sha[:8])
old=P('/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative')
control=P('/data1/yanruj/Memacc-evolveswdb-lane');repo=P('/data1/yanruj/ArchEvolve')
def cmd(a):return subprocess.check_output(a,text=True).strip()
leases={p.name:json.loads(p.read_text()) for p in P('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
assert len(leases)==3
assert leases[f'mbit10-evaluation-node{node}.meta.json']['state']=='released'
assert leases['mbit10-evaluation.meta.json']['state']=='released'
pre={k:cmd(v) for k,v in {'uptime':['uptime'],'disk':['df','-h','/data1','/data'],'memory':['free','-h'],'users':['who'],'cpu':['lscpu'],'numa':['numactl','--hardware'],'kernel':['uname','-a']}.items()}
pre['leases']=leases
pre['cpu_policy']={str(p):p.read_text().strip() if p.exists() else 'unavailable' for p in map(P,['/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor','/sys/devices/system/cpu/intel_pstate/no_turbo'])}
gpu=subprocess.run(['nvidia-smi'],text=True,capture_output=True);pre['gpu']={'exit_code':gpu.returncode,'stdout':gpu.stdout,'stderr':gpu.stderr}
subprocess.run(['git','-C',str(control),'-c','fetch.recurseSubmodules=false','fetch','--no-tags','origin','yanrujhou_main'],check=True)
wrapper=control/'AgenticRefiner/scripts/host/socket_lane.sh'
blob=subprocess.check_output(['git','-C',str(control),'show','FETCH_HEAD:AgenticRefiner/scripts/host/socket_lane.sh'])
assert wrapper.read_bytes()==blob
assert hashlib.sha256(blob).hexdigest()=='00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
pre['wrapper']={'sha256':hashlib.sha256(blob).hexdigest(),'fetched_commit':cmd(['git','-C',str(control),'rev-parse','FETCH_HEAD'])}
pre['primary_source']={'branch':cmd(['git','-C',str(repo),'rev-parse','--abbrev-ref','HEAD']),'commit':cmd(['git','-C',str(repo),'rev-parse','HEAD'])}
subprocess.run(['git','-C',str(repo),'fetch','--no-tags','origin','codex/probata-resume-20261015'],check=True)
subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',sha,'FETCH_HEAD'],check=True)
review=cfg['change_review']['content']; changes=review['files_after']
actual=cmd(['git','-C',str(repo),'diff','--name-only','--no-renames',review['baseline'],sha,'--','swdb-project/swdb','swdb-project/library']).splitlines()
assert set(actual)==set(changes),('reviewed production-change set mismatch',actual,list(changes))
for name,h in changes.items():
 blob=subprocess.run(['git','-C',str(repo),'show',sha+':'+name],capture_output=True)
 if h is None:assert blob.returncode!=0,name
 else:assert blob.returncode==0 and hashlib.sha256(blob.stdout).hexdigest()==h,name
pre['reviewed_source_changes']=cfg['change_review']
if not source.exists():subprocess.run(['git','-C',str(repo),'worktree','add','--detach',str(source),sha],check=True)
assert cmd(['git','-C',str(source),'rev-parse','HEAD'])==sha
assert cmd(['git','-C',str(source),'rev-parse','--abbrev-ref','HEAD'])=='HEAD'
assert not cmd(['git','-C',str(source),'status','--porcelain'])
for name,h in changes.items():
 if h is None:assert not (source/name).exists(),name
 else:assert hashlib.sha256((source/name).read_bytes()).hexdigest()==h,name
pre['source_branch']=cmd(['git','-C',str(source),'rev-parse','--abbrev-ref','HEAD'])
out=P('/data/yanruj/EvolveSWDB_runs/probata-reviewed-'+sha[:8]+'-'+cfg['kind']);out.mkdir(exist_ok=False)
launch=json.loads((old/'launch.json').read_text())
launch.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),node=node,timeout_seconds=seconds,source=str(source),source_commit=sha,log_name='acceptance.log',readers=review['readers'])
launch['command']=[s.replace('{SOURCE}',str(source)).replace('{OUTPUT}',str(out)) for s in cfg['command']]
launch['reviewed_wrapper_reuse']={n:hashlib.sha256((old/n).read_bytes()).hexdigest() for n in ('execute.py','watch.py')}
assert launch['reviewed_wrapper_reuse']=={'execute.py':'ea774376014605a6ad31356a35abccef729f42e327ce07f4075853743dbcb612','watch.py':'4485ae66aa50c65f2b579f84836576aa67b54431978da71cac6eea6a68ecd07c'}
(out/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');(out/'preflight.json').write_text(json.dumps(pre,indent=2)+'\n')
for n in ('execute.py','watch.py'):(out/n).write_bytes((old/n).read_bytes())
assert hashlib.sha256((old/'run.sh').read_bytes()).hexdigest()=='650f815cb7562767829d94e8868da56990c98301376b999af6c659fbe499fcf3'
run=(old/'run.sh').read_text()
assert str(old) in run and '/data1/yanruj/probata-composed-0e7f2327' in run
(out/'run.sh').write_text(run.replace(str(old),str(out)).replace('/data1/yanruj/probata-composed-0e7f2327',str(source)))
session='probata-reviewed-'+sha[:8]+'-'+cfg['kind']
argv=['bash',str(wrapper),str(node),session,'--record',str(out/'lane.json'),'--','timeout','--signal=TERM','--kill-after=60',str(seconds+120),'bash',str(out/'run.sh')]
(out/'dispatch-argv.json').write_text(json.dumps(argv,indent=2)+'\n')
subprocess.run(['tmux','new-session','-d','-s',session,'-c',str(control/'AgenticRefiner'),shlex.join(argv)+' >'+shlex.quote(str(out/'dispatch.log'))+' 2>&1'],check=True)
print(json.dumps({'launch':launch,'output':str(out),'session':session,'wrapper':pre['wrapper']},indent=2))
'''
r=subprocess.run(['ssh','mbit10','python3','-'],input=script,text=True,capture_output=True)
print(r.stdout);print(r.stderr,file=sys.stderr);sys.exit(r.returncode)
