import datetime,hashlib,json,os,pathlib,shutil,stat
P=pathlib.Path;raw=P('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1');metadata={};pins={}
for name in ['launch.json','lane.json','outer-resources.json','resources.json','source-after.json','component/result.json','component/commands.json','component/caller.ast.gzip.json','capture-runtime-after.json']:
 p=raw/name
 if not p.exists():continue
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=1048576
 data=p.read_bytes();metadata[name]=json.loads(data);pins[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
leases={p.name:json.loads(p.read_bytes()) for p in P('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
selected=[];failures=[]
for p in sorted(P('/proc').iterdir()):
 if not p.name.isdigit():continue
 try:
  if p.stat().st_uid!=os.getuid():continue
  data=(p/'cmdline').read_bytes();assert len(data)<=1048576
  argv=[s.decode('utf8','replace') for s in data.split(b'\0') if s]
  if any(str(raw) in s or 'probata-resume-20261016-2baf722f-t28-memory-tu-v1' in s for s in argv):selected.append({'pid':int(p.name),'argv':argv})
 except (FileNotFoundError,ProcessLookupError):pass
 except Exception as e:failures.append({'pid':p.name,'type':type(e).__name__})
extent={'files':0,'bytes':0,'aliases':[],'special':[]}
for p in sorted(raw.rglob('*')):
 m=p.lstat()
 if stat.S_ISDIR(m.st_mode):continue
 if stat.S_ISREG(m.st_mode):extent['files']+=1;extent['bytes']+=m.st_size
 elif stat.S_ISLNK(m.st_mode):extent['aliases'].append(str(p.relative_to(raw)))
 else:extent['special'].append(str(p.relative_to(raw)))
value={'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_root':str(raw),'metadata':metadata,'pins':pins,'leases':leases,'selected_original_processes':selected,'process_read_failures':failures,'extent':extent,'raw_payload_transferred':False,'free_bytes':{p:shutil.disk_usage(p).free for p in ['/data','/data1']}}
print(json.dumps(value,sort_keys=True))
