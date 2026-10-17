import datetime,hashlib,json,os,pathlib,shutil,subprocess
P=pathlib.Path
source=P('/data1/yanruj/probata-resume-20261016-2baf722f')
raw=P('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1')
uid=os.getuid();failures=[];selected=[];owned=0
for proc in sorted(P('/proc').iterdir()):
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid!=uid:continue
  owned+=1
  data=(proc/'cmdline').read_bytes()
  if len(data)>1048576:raise ValueError('oversize cmdline')
  argv=[x.decode('utf8','replace') for x in data.split(b'\0') if x]
  joined=' '.join(argv)
  tokens=('probata-resume-20261016','frama-c','why3server','cbmc','clang-22','clang++','pytest','execute.py','watch.py')
  if any(token in joined for token in tokens):selected.append({'pid':int(proc.name),'argv':argv})
 except (FileNotFoundError,ProcessLookupError):pass
 except Exception as e:failures.append({'pid':proc.name,'type':type(e).__name__})
leases={p.name:json.loads(p.read_bytes()) for p in P('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
branch=subprocess.check_output(['git','-C',str(source),'rev-parse','--abbrev-ref','HEAD'],text=True).strip()
status=subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True).strip()
value={'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uid':uid,'owned_processes_scanned':owned,'selected':selected,'read_failures':failures,'leases':leases,'source':{'path':str(source),'commit':commit,'branch':branch,'status':status},'raw_absent':not os.path.lexists(raw),'free_bytes':{p:shutil.disk_usage(p).free for p in ['/data','/data1']},'uptime':subprocess.check_output(['uptime'],text=True).strip()}
print(json.dumps(value,sort_keys=True))
assert len(leases)==3 and leases['mbit10-evaluation-node1.meta.json']['state']=='released' and leases['mbit10-evaluation.meta.json']['state']=='released'
assert not selected and not failures and value['raw_absent']
assert commit=='2baf722fdaa6cba24b859eae3172a6f597417d72' and branch=='HEAD' and not status
assert value['free_bytes']['/data']>=53687091200+268435456 and value['free_bytes']['/data1']>=10*1024**3
