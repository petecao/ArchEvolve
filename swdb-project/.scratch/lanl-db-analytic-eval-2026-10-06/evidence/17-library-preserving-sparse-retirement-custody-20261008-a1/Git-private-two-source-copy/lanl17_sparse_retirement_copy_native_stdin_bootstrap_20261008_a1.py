"""2026-10-08 ET: prospective stdin transport for one exact Git-pinned copy source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import signal
import stat
import subprocess
import sys

UID=114316761
PRIMARY=Path('/data1/yanruj/ArchEvolve')
BASE=PRIMARY.parent
REL='swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-library-preserving-sparse-retirement-custody-20261008-a1/Git-private-two-source-copy/lanl17_copy_sparse_retirement_sources_from_administrative_git_20261008_a1.py'
PINS={Path('/usr/bin/git'):(4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
      Path('/usr/bin/python3.12'):(8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f')}
STOP_SIGNAL=None
class Refused(Exception):pass
def interrupted(signum,frame):
    global STOP_SIGNAL
    if STOP_SIGNAL is None:STOP_SIGNAL=signum
    for name in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(name,signal.SIG_IGN)
def require(ok,code):
    if not ok:raise Refused(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return tuple(getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns'))
def native(p,size,digest):
    require(p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'native_route')
    s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o755 and s.st_size==size,'native_identity')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        b=f.read(size+1);require(len(b)==size and sha(b)==digest and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'native_returned_pin')
    return stamp(s)
def git(*args):
    env=dict(os.environ);env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_NO_LAZY_FETCH='1')
    p=subprocess.Popen(['/usr/bin/git','--no-pager','-C',str(PRIMARY),*args],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        out,err=p.communicate(timeout=30)
        require(STOP_SIGNAL is None and p.returncode==0 and len(out)<=512*1024 and len(err)<=64*1024,'readonly_bootstrap_git_refused_or_cap')
        return out
    finally:
        if p.poll() is None:
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait(timeout=5)
        p.stdout.close();p.stderr.close()
def main():
    a=argparse.ArgumentParser();a.add_argument('--copier-source-bytes',type=int,required=True);a.add_argument('--copier-source-sha256',required=True)
    known,rest=a.parse_known_args();os.umask(0o077)
    for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(sig,interrupted)
    require(os.uname().sysname=='Linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','host_or_account')
    require(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12'),'actual_native_python_route')
    require(not any(k.startswith('GIT_') for k in os.environ) and not any(os.environ.get(k) for k in ('PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_LIBRARY_PATH')),'startup_override')
    require(0<known.copier_source_bytes<=512*1024 and re.fullmatch('[a-f0-9]{64}',known.copier_source_sha256),'copier_explicit_pin')
    require(rest.count('--administrative40')==1 and rest.index('--administrative40')+1<len(rest),'required_administrative40')
    revision=rest[rest.index('--administrative40')+1];require(re.fullmatch('[a-f0-9]{40}',revision),'administrative40_shape')
    for path in (BASE,PRIMARY,PRIMARY/'.git'):
        require(path.resolve(strict=True)==path and not any(q.is_symlink() for q in (path,*path.parents)),'repository_route')
        s=path.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and not s.st_mode&0o5000,'repository_identity')
    require(stat.S_IMODE(BASE.lstat().st_mode)==0o700,'private_base')
    original={str(p):native(p,*pin) for p,pin in PINS.items()}
    row=git('ls-tree','-z',revision,'--',REL).rstrip(b'\0').split(b'\t')
    require(len(row)==2 and row[1].decode()==REL,'copier_exact_git_path')
    parts=row[0].split();require(len(parts)==3 and parts[0]==b'100644' and parts[1]==b'blob','copier_exact_git_mode')
    oid=parts[2].decode();require(int(git('cat-file','-s',oid).strip())==known.copier_source_bytes,'copier_git_size')
    b=git('cat-file','blob',oid);require(len(b)==known.copier_source_bytes and sha(b)==known.copier_source_sha256,'copier_returned_bytes_pin')
    require(STOP_SIGNAL is None and {str(p):native(p,*pin) for p,pin in PINS.items()}==original,'native_bootstrap_drift')
    sys.argv=[REL,*rest]
    # Reviewed returned bytes only: no administrative checkout, source import or selected control call.
    exec(compile(b,'git:'+revision+':'+REL,'exec'),{'__name__':'__main__','__file__':'git:'+revision+':'+REL})
if __name__=='__main__':
    try:main()
    except (Refused,OSError,ValueError,UnicodeError,subprocess.SubprocessError) as e:
        print(json.dumps({'format':'swdb.sparse-retirement-copy-stdin-refusal.v1','sealed':False,'error_class':type(e).__name__,'error_digest':sha(str(e).encode()),'received_signal':STOP_SIGNAL}));raise SystemExit(1)
