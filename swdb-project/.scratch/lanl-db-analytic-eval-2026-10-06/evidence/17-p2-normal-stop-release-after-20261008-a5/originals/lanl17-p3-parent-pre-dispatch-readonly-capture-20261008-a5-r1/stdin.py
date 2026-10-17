CONFIG={'argv': ['/usr/bin/python3.12', '-I', '-B', '-c', 'import datetime,json,os,shutil,subprocess,time\nfrom pathlib import Path\nR="5e12a9796432654d88def24ecea617d16ca605b2"\nbase=Path("/data1/yanruj");raw=Path("/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5")\ndef run(a):\n p=subprocess.run(a,capture_output=True,timeout=15,env={"PATH":"/usr/bin:/bin","LC_ALL":"C","GIT_OPTIONAL_LOCKS":"0"});assert p.returncode==0 and len(p.stdout)<=65536;return p.stdout.decode()\nsources={str(p):{"head":run(["/usr/bin/git","-C",str(p),"rev-parse","HEAD"]).strip(),"status":run(["/usr/bin/git","-C",str(p),"status","--porcelain"])} for p in (base/"ArchEvolve",base/"ArchEvolve-lanl17-source-20261007-a5")}\nassert all(x["head"]==R for x in sources.values()) and sources[str(base/"ArchEvolve-lanl17-source-20261007-a5")]["status"]==""\norigin=run(["/usr/bin/git","-C",str(base/"ArchEvolve"),"rev-parse","origin/yanrujhou_main"]).strip();assert origin==R\nleases={name:json.loads((base/"lact-host-lease"/(name+".meta.json")).read_bytes()) for name in ("mbit10-evaluation-node0","mbit10-evaluation-node1","mbit10-evaluation")};assert all(d["state"]=="released" for d in leases.values())\nabsent={str(raw/route/"extensa-gem5-bfs-20261006-p3"):not os.path.lexists(raw/route/"extensa-gem5-bfs-20261006-p3") for route in("attempts","campaign-runs/extensa")};assert all(absent.values())\nmem={k:int(v.strip().split()[0])*1024 for k,v in (line.split(":",1) for line in Path("/proc/meminfo").read_text().splitlines()) if k=="MemAvailable"}\nfree={p:shutil.disk_usage(p).free for p in("/data1","/data")};assert mem["MemAvailable"]>=85899345920 and free["/data1"]>=22548578304 and free["/data"]>=25769803776\nprocs=run(["/usr/bin/ps","-eo","user,pid,ppid,pcpu,pmem,comm","--sort=-pcpu"]).splitlines()[:35]\nmpstat=run(["/usr/bin/mpstat","-P","ALL","1","1"]) if Path("/usr/bin/mpstat").exists() else "unavailable"\ngpu=run(["/usr/bin/nvidia-smi","--query-gpu=name,utilization.gpu,memory.used,memory.total","--format=csv,noheader"]) if Path("/usr/bin/nvidia-smi").exists() else "unavailable"\nassert all(json.loads((base/"lact-host-lease"/(n+".meta.json")).read_bytes())==d for n,d in leases.items())\nprint(json.dumps({"format":"swdb.lanl17-p3-parent-pre-dispatch-readonly.v1","checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"scientific_admission":False,"source":sources,"primary_origin":origin,"leases":leases,"p3_routes_absent":absent,"mem":mem,"free_bytes":free,"load":os.getloadavg(),"processes_top35_comm_only":procs,"cpu_activity":mpstat,"gpu":gpu},sort_keys=True))\n'], 'source_pins': [], 'collect': [], 'remote_seconds': 90, 'local_seconds': 180}

import base64,datetime,hashlib,json,os,pwd,signal,stat,subprocess,sys
from pathlib import Path
def require(ok,code):
 if not ok:raise ValueError(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return tuple(getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns'))
def original(p,maximum):
 p=Path(p);require(p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'canonical_original')
 s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==114316761 and s.st_nlink==1 and s.st_size<=maximum and not s.st_mode&0o022,'owned_bounded_file')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  require(stamp(os.fstat(f.fileno()))==stamp(s),'open_stat');b=f.read(maximum+1)
  require(len(b)==s.st_size<=maximum and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'exact_bytes_stat')
 return b
def exact(p,size,digest):
 b=original(p,size);require(len(b)==size and sha(b)==digest,'exact_size_digest');return b
require(os.getuid()==os.geteuid()==114316761 and os.uname().nodename.split('.')[0]=='mbit10' and pwd.getpwuid(os.getuid()).pw_name=='yanruj','actual_account_host')
require(Path('/proc/self/exe').resolve()==Path('/usr/bin/python3.12'),'native_python')
os.umask(0o077)
for pin in CONFIG['source_pins']:exact(pin['path'],pin['bytes'],pin['sha256'])
for item in CONFIG.get('stage',[]):
 p=Path(item['path']);require(p.is_absolute() and p.parent.resolve(strict=True)==p.parent and p.parent.stat().st_uid==os.getuid() and not any(q.is_symlink() for q in (p,*p.parents)),'fresh_owned_stage_route')
 b=base64.b64decode(item['base64'],validate=True);require(len(b)==item['bytes'] and sha(b)==item['sha256'],'stage_exact_reviewed_bytes')
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 exact(p,len(b),sha(b))
env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','PYTHON','LD_','DYLD_')) and k not in ('BASH_ENV','ENV')}
env.update(PATH='/usr/bin:/bin:/usr/local/bin',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONSAFEPATH='1')
env.update(CONFIG.get('environment',{}))
require(env.get('HOME')==pwd.getpwuid(os.getuid()).pw_dir,'original_home')
os.chdir(CONFIG.get('cwd','/data1/yanruj'))
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
if CONFIG.get('argv'):
 argv=['/usr/bin/timeout','--signal=TERM','--kill-after=60s',str(CONFIG['remote_seconds'])+'s',*CONFIG['argv']]
 result=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=CONFIG['remote_seconds']+70)
 require(len(result.stdout)<=8*1024*1024 and len(result.stderr)<=8*1024*1024,'metadata_stream_bound')
 code=result.returncode;stdout=result.stdout;stderr=result.stderr
else:argv=[];code=0;stdout=b'';stderr=b''
files={}
if code==0:
 for name in CONFIG.get('collect',[]):
  b=original(Path(name),8*1024*1024)
  files[name]={'path':name,'bytes':len(b),'sha256':sha(b),'base64':base64.b64encode(b).decode()}
for pin in CONFIG['source_pins']:exact(pin['path'],pin['bytes'],pin['sha256'])
packet={'format':'swdb.lanl17-parent-metadata-action-original.v1','sealed':False,'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'exit_code':code,'stdout_base64':base64.b64encode(stdout).decode(),'stderr_base64':base64.b64encode(stderr).decode(),'files':files,'scientific_admission':False}
raw=(json.dumps(packet,sort_keys=True,allow_nan=False)+'\n').encode();require(len(raw)<=16*1024*1024,'packet_bound');sys.stdout.buffer.write(raw)
raise SystemExit(0 if code==0 else 2)
