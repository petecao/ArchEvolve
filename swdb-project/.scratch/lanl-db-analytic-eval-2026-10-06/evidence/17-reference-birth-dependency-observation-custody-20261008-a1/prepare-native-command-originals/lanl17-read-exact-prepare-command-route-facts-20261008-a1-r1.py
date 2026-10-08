"""2026-10-08 ET. Read-only exact public prepare command routes; no version/main/test."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time

UID=114316761
BASE=Path('/data1/yanruj')
PRIMARY=BASE/'ArchEvolve'
PREPARE_PATH='/usr/bin:/bin:/usr/local/bin'
EXPECTED='260a0d8ce9dce63a852d88e8cf2bb8cd484e78f1'
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+60
def need(ok,code):
    if not ok: raise ValueError(code)
def tick(): need(time.monotonic()<END,'query_deadline')
def stamp(p): return {k:getattr(p.lstat(),'st_'+k) for k in FIELDS}
def read(p,cap,owner=0):
    tick(); need(p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)), 'redirected_command')
    s=stamp(p); need(stat.S_ISREG(s['mode']) and s['uid']==owner and s['nlink']==1 and not s['mode']&0o7022 and 0<=s['size']<=cap,'command_identity_or_cap')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        with os.fdopen(fd,'rb',closefd=False) as f: raw=f.read(cap+1)
        fs={k:getattr(os.fstat(fd),'st_'+k) for k in FIELDS}
        need(len(raw)==s['size'] and fs==s==stamp(p),'command_changed')
    finally: os.close(fd)
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'stat':s}
def source_state():
    results={}
    for args in (('rev-parse','HEAD'),('branch','--show-current'),('rev-parse','origin/yanrujhou_main'),('status','--porcelain')):
        tick(); r=subprocess.run(['/usr/bin/git','--no-optional-locks','-C',str(PRIMARY),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,
            env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0'})
        need(r.returncode==0 and len(r.stdout)<=16384 and not r.stderr,'source_state_query_refused')
        results[' '.join(args)]=r.stdout.decode().strip()
    need(results['rev-parse HEAD']==results['rev-parse origin/yanrujhou_main']==EXPECTED and results['branch --show-current']=='yanrujhou_main' and results['status --porcelain']=='?? swdb-project/records/.retention.lock','source_context_not_expected')
    lock=PRIMARY/'swdb-project/records/.retention.lock'
    expected={'dev':2097,'ino':54947305,'mode':33206,'uid':UID,'gid':0,'nlink':1,'size':0,'mtime_ns':1791030933805697274,'ctime_ns':1791030933805697274}
    need(lock.resolve(strict=True)==lock and not any(q.is_symlink() for q in (lock,*lock.parents)) and stamp(lock)==expected,'original_empty_retention_identity')
    fd=os.open(lock,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        need(os.read(fd,1)==b'' and {k:getattr(os.fstat(fd),'st_'+k) for k in FIELDS}==expected==stamp(lock),'original_empty_retention_bytes_changed')
    finally:os.close(fd)
    results['original_empty_retention_byte_pin']={'path':str(lock),'bytes':0,'sha256':hashlib.sha256(b'').hexdigest(),'stat':expected}
    return results
def main():
    need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and sys.flags.dont_write_bytecode and sys.flags.no_user_site,'native_host_startup')
    need(not any(os.environ.get(k) for k in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONINSPECT','LD_PRELOAD','LD_LIBRARY_PATH')),'unsafe_startup')
    native=read(Path('/usr/bin/python3.12'),16*1024*1024); git=read(Path('/usr/bin/git'),16*1024*1024)
    need(native['bytes']==8020928 and native['sha256']=='e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
         and git['bytes']==4019024 and git['sha256']=='06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb','original_native_byte_pins')
    before=source_state(); commands={}
    for name in ('git','python3','tmux','numactl','strace','timeout','bash','node'):
        route=shutil.which(name,path=PREPARE_PATH); need(route is not None,'necessary_command_unavailable_'+name)
        alias=Path(route); p=alias.resolve(strict=True)
        need(p.is_relative_to(Path('/usr')),'native_command_outside_system')
        pin=read(p,64*1024*1024); need(pin['stat']['mode']&0o111,'command_not_executable')
        commands[name]={'configured_PATH_route':route,'resolved':pin}
    need(commands['git']['resolved']==git and commands['python3']['resolved']==native,'native_PATH_resolution_changed')
    after=source_state(); need(before==after,'source_context_changed')
    for row in commands.values(): need(read(Path(row['resolved']['path']),64*1024*1024)==row['resolved'],'command_postflight_changed')
    out={'format':'swdb.lanl17-necessary-prepare-command-route-original.v1','sealed':False,'observed_utc':datetime.now(timezone.utc).isoformat(),'explicit_prepare_PATH':PREPARE_PATH,'source_context_before':before,'source_context_after':after,'necessary_command_byte_pins':commands,'native_python':native,'native_git':git,'version_or_selected_main_test_provider_compiler_or_scientific_command_executed':False,'auth_read_or_remote_file_mutation':False}
    b=json.dumps(out,sort_keys=True,ensure_ascii=True).encode(); need(len(b)<=16384,'output_cap'); print(b.decode())
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda s,f:(_ for _ in ()).throw(TimeoutError('query_alarm'))); signal.alarm(60)
    try: main()
    except Exception as e:
        print(json.dumps({'format':'swdb.lanl17-necessary-prepare-command-route-refusal.v1','sealed':False,'error_class':type(e).__name__,'code':str(e) if isinstance(e,ValueError) else 'original_error_not_emitted','no_version_or_scientific_execution':True},sort_keys=True)); sys.exit(1)
    finally: signal.alarm(0)
