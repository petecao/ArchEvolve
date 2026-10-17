"""2026-10-08 ET: finite private parent capture for reviewed metadata actions."""
import base64, datetime, hashlib, json, os, resource, shlex, signal, subprocess, sys, types
from pathlib import Path

def sha(raw): return hashlib.sha256(raw).hexdigest()
def require(ok, message):
    if not ok: raise ValueError(message)
def private(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as out: out.write(raw)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

BOOT = r'''
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
'''

def main():
    config_path, capture_path = map(Path, sys.argv[1:])
    config_raw = config_path.read_bytes(); config = json.loads(config_raw)
    root = capture_path
    require(root.parent == Path('/private/tmp') and not root.exists(), 'fresh_private_capture')
    ssh = Path('/usr/bin/ssh'); ssh_raw = ssh.read_bytes()
    require(len(ssh_raw)==1584560 and sha(ssh_raw)=='c7f9f9779c1dd141b04889c6cb214859d0702687e7fde34511bb5fa7af8951f1','native_ssh_pin')
    cleanup = Path('/Users/yanrujhou/.codex/worktrees/lanl-ticket17/ArchEvolve/swdb-project/swdb/processes.py')
    cleanup_raw = cleanup.read_bytes()
    require(len(cleanup_raw)==912 and sha(cleanup_raw)=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289','cleanup_source_pin')
    helpers = types.ModuleType('owned_metadata_ssh_cleanup'); exec(compile(cleanup_raw,str(cleanup),'exec'),helpers.__dict__)
    root.mkdir(mode=0o700)
    stdin = ('CONFIG='+repr(config)+'\n'+BOOT).encode(); private(root/'stdin.py',stdin)
    remote = ['/usr/bin/timeout','--signal=TERM','--kill-after=15s',str(config['remote_seconds']+70)+'s','/usr/bin/python3.12','-I','-B','-']
    argv = [str(ssh),'-T','-o','BatchMode=yes','-o','ConnectTimeout=30','mbit10','exec '+shlex.join(remote)]
    start = now(); private(root/'start.json',(json.dumps({'started_utc':start,'argv':argv,'config_sha256':sha(config_raw),'source_sha256':sha(Path(__file__).read_bytes()),'stdin_sha256':sha(stdin),'finite_local_seconds':config['local_seconds'],'no_retry':True},sort_keys=True)+'\n').encode())
    child=None; code=None; error=None
    watched=(signal.SIGTERM,signal.SIGINT,signal.SIGHUP); old={n:signal.getsignal(n) for n in watched}
    def interrupted(number,frame): raise RuntimeError('parent_signal_'+str(number))
    def limit(): resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    try:
        for n in watched: signal.signal(n,interrupted)
        with (root/'stdin.py').open('rb') as inp, (root/'stdout').open('xb') as out, (root/'stderr').open('xb') as err:
            os.chmod(root/'stdout',0o600); os.chmod(root/'stderr',0o600)
            child=subprocess.Popen(argv,stdin=inp,stdout=out,stderr=err,start_new_session=True,preexec_fn=limit)
            code=child.wait(timeout=config['local_seconds'])
    except BaseException as exc: error=type(exc).__name__
    finally:
        for n in watched: signal.signal(n,signal.SIG_IGN)
        helpers.stop_group(child,grace_seconds=15)
    pins={name:{'bytes':(root/name).stat().st_size,'sha256':sha((root/name).read_bytes())} for name in ('stdout','stderr')}
    transport={'started_utc':start,'ended_utc':now(),'SSH_exit_code':code,'error_type':error,'private_original_streams':pins,'remote_completion_not_inferred':True}
    private(root/'transport.json',(json.dumps(transport,sort_keys=True)+'\n').encode())
    for n,handler in old.items(): signal.signal(n,handler)
    print(json.dumps(transport,sort_keys=True)); return 0 if code==0 and error is None else 2
if __name__=='__main__': raise SystemExit(main())
