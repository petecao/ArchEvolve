"""2026-10-08 ET: prospective Git-only two-source copy; selected mains never invoked."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import selectors
import signal
import stat
import subprocess
import time

UID=114316761
BASE=Path('/data1/yanruj')
PRIMARY=BASE/'ArchEvolve'
FROZEN='5e12a9796432654d88def24ecea617d16ca605b2'
ADMIN_REF='refs/remotes/origin/codex/lanl17-storage-guard-cost'
EVIDENCE_DIR='swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-library-preserving-sparse-retirement-custody-20261008-a1'
STOP_SIGNAL=None
NATIVES={Path('/usr/bin/git'):(4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
         Path('/usr/bin/python3.12'):(8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f')}
MAX_SOURCE=512*1024
MAX_TOTAL=16*1024*1024
class Refused(Exception):pass
def interrupted(signum,frame):
    global STOP_SIGNAL
    if STOP_SIGNAL is None:STOP_SIGNAL=signum
    for name in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(name,signal.SIG_IGN)
def require(ok,code):
    if not ok:raise Refused(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def identity(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid')}
def canonical(p):
    require(p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'noncanonical_route')
def private_base():
    canonical(BASE);s=BASE.lstat()
    require(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700,'private_base_identity')
    return identity(s)
def read(p,cap,owner,mode=None):
    canonical(p);s=p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and not s.st_mode&0o7000 and s.st_size<=cap,'regular_file_identity_or_cap')
    if mode is not None:require(stat.S_IMODE(s.st_mode)==mode,'regular_file_mode')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        b=f.read(cap+1);require(len(b)==s.st_size and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'returned_byte_stat_drift')
    return b,stamp(s)
def core_state():
    base=private_base();canonical(PRIMARY);canonical(PRIMARY/'.git')
    for p in (PRIMARY,PRIMARY/'.git'):
        s=p.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and s.st_dev==base['dev'] and not s.st_mode&0o5000,'primary_directory_identity')
        require(not s.st_mode&0o2000 or s.st_gid==base['gid'],'primary_directory_setgid_identity')
    native={}
    for p,(size,digest) in NATIVES.items():
        b,s=read(p,16*1024*1024,0,0o755);require(len(b)==size and sha(b)==digest,'native_pin');native[str(p)]={'sha256':digest,'stat':s}
    config_b,config_s=read(PRIMARY/'.git/config',256*1024,UID)
    retention_b,retention_s=read(PRIMARY/'swdb-project/records/.retention.lock',0,UID)
    require(retention_b==b'','nonempty_original_retention')
    return {'base_identity':base,'primary_stat':stamp(PRIMARY.lstat()),'common_stat':stamp((PRIMARY/'.git').lstat()),
            'config':{'bytes':len(config_b),'sha256':sha(config_b),'stat':config_s},
            'retention':{'bytes':0,'sha256':sha(retention_b),'stat':retention_s},'native':native}
def stop(p):
    if p.poll() is not None:return
    try:os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.wait(timeout=5)
def git(*args,allowed=(0,)):
    require(STOP_SIGNAL is None and time.monotonic()<DEADLINE,'copy_interrupted_or_deadline')
    env=dict(os.environ);env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_NO_LAZY_FETCH='1',GIT_PAGER='cat')
    p=subprocess.Popen(['/usr/bin/git','--no-pager','-c','core.fsmonitor=false','-C',str(PRIMARY),*args],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    sel=selectors.DefaultSelector();out=bytearray();err=bytearray();end=min(DEADLINE,time.monotonic()+30)
    for f,buf in ((p.stdout,out),(p.stderr,err)):os.set_blocking(f.fileno(),False);sel.register(f,selectors.EVENT_READ,buf)
    try:
        while sel.get_map():
            require(STOP_SIGNAL is None and time.monotonic()<end,'readonly_git_interrupted_or_timeout')
            for key,_ in sel.select(min(0.2,max(0,end-time.monotonic()))):
                b=os.read(key.fileobj.fileno(),65536)
                if not b:sel.unregister(key.fileobj);continue
                key.data.extend(b);require(len(out)+len(err)<=MAX_TOTAL,'readonly_git_stream_cap')
        p.wait(timeout=max(0.01,min(5,DEADLINE-time.monotonic())))
        require(STOP_SIGNAL is None and p.returncode in allowed,'readonly_git_refused_or_interrupted')
        return bytes(out)
    finally:
        sel.close();stop(p);p.stdout.close();p.stderr.close()
def refs():
    require(git('rev-parse','HEAD').strip().decode()==FROZEN and git('symbolic-ref','--short','HEAD').strip()==b'yanrujhou_main','frozen_primary_head')
    for ref in ('refs/heads/yanrujhou_main','refs/remotes/origin/yanrujhou_main','refs/remotes/origin/codex/lanl-analytic-eval'):
        require(git('rev-parse','--verify',ref).strip().decode()==FROZEN,'frozen_main_ref')
    require(git('status','--porcelain=v1','--untracked-files=all')==b'?? swdb-project/records/.retention.lock\n','primary_tracked_or_untracked_change')
    require(not git('diff','--cached','--name-only') and not git('diff','--name-only'),'primary_tracked_change')
    return sha(git('for-each-ref','--format=%(refname) %(objectname)'))
def blob(revision,relative,size,digest):
    raw=git('ls-tree','-z',revision,'--',relative)
    row=raw.rstrip(b'\0').split(b'\t');require(len(row)==2 and row[1].decode()==relative,'exact_blob_path')
    parts=row[0].split();require(len(parts)==3 and parts[0]==b'100644' and parts[1]==b'blob','exact_blob_mode_type')
    require(int(git('cat-file','-s',parts[2].decode()).strip())==size,'exact_blob_size')
    b=git('cat-file','blob',parts[2].decode());require(len(b)==size and sha(b)==digest,'exact_blob_bytes')
    return b,parts[2].decode()
def main():
    global DEADLINE
    a=argparse.ArgumentParser()
    a.add_argument('--administrative40',required=True);a.add_argument('--evidence-directory',required=True);a.add_argument('--destination',required=True)
    for role in ('guard','wrapper'):
        a.add_argument('--'+role+'-basename',required=True);a.add_argument('--'+role+'-bytes',type=int,required=True);a.add_argument('--'+role+'-sha256',required=True)
    args=a.parse_args();os.umask(0o077);DEADLINE=time.monotonic()+180
    for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(sig,interrupted)
    require(os.uname().sysname=='Linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','account_or_host')
    require(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12'),'actual_native_python_route')
    require(not any(k.startswith('GIT_') for k in os.environ) and not any(os.environ.get(k) for k in ('PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_LIBRARY_PATH')),'startup_routing_override')
    require(re.fullmatch('[a-f0-9]{40}',args.administrative40) and args.administrative40!=FROZEN,'administrative_commit_required')
    directory=args.evidence_directory
    require(directory==EVIDENCE_DIR,'exact_evidence_directory')
    dest=Path(args.destination);require(dest.parent==BASE and re.fullmatch('lanl17-sparse-retirement-source-[a-z0-9-]{1,80}',dest.name) and not os.path.lexists(dest),'fresh_direct_base_destination')
    files={}
    for role in ('guard','wrapper'):
        name=getattr(args,role+'_basename');size=getattr(args,role+'_bytes');digest=getattr(args,role+'_sha256')
        require(re.fullmatch('[A-Za-z0-9_][A-Za-z0-9_.-]{0,150}[.]py',name) and name not in files,'exact_two_basename_whitelist')
        require(0<size<=MAX_SOURCE and re.fullmatch('[a-f0-9]{64}',digest),'source_size_or_sha_pin')
        files[name]={'role':role,'bytes':size,'sha256':digest,'relative_path':directory+'/selected-sparse-control-source/'+name}
    before=core_state();ref_pin=refs()
    require(git('rev-parse','--verify',ADMIN_REF).strip().decode()==args.administrative40,'delivered_administrative_ref')
    git('merge-base','--is-ancestor',FROZEN,args.administrative40)
    diff=git('diff','--name-status','--no-renames','-z',FROZEN,args.administrative40).split(b'\0')
    require(diff[-1]==b'' and len(diff)%2==1,'administrative_diff_shape')
    paths=[]
    for i in range(0,len(diff)-1,2):
        status,path=diff[i],diff[i+1].decode();require(status==b'A' and path.startswith(directory+'/'),'only_additive_expected_evidence_directory');paths.append(path)
    require(2<=len(paths)<=1024 and all(x['relative_path'] in paths for x in files.values()),'administrative_addition_cardinality')
    originals={}
    for name,row in files.items():originals[name]=blob(args.administrative40,row['relative_path'],row['bytes'],row['sha256'])
    require(core_state()==before and refs()==ref_pin,'prepublication_primary_drift')
    os.mkdir(dest,0o700);canonical(dest);dest_identity=identity(dest.lstat());require(stat.S_IMODE(dest.lstat().st_mode)==0o700,'fresh_destination_mode')
    result=[];private_stats={}
    for name,row in files.items():
        b,oid=originals[name];out=dest/name
        fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        with os.fdopen(fd,'wb') as f:require(f.write(b)==len(b),'short_copy');f.flush();os.fsync(f.fileno())
        got,s=read(out,MAX_SOURCE,UID,0o600);require(got==b,'postcopy_bytes');private_stats[name]=s
        result.append({**row,'git_blob':oid,'private_path':str(out),'private_stat':s})
    fd=os.open(dest,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:os.fsync(fd)
    finally:os.close(fd)
    require(sorted(p.name for p in dest.iterdir())==sorted(files) and identity(dest.lstat())==dest_identity,'exact_two_file_destination')
    for name,row in files.items():
        require(blob(args.administrative40,row['relative_path'],row['bytes'],row['sha256'])==originals[name],'final_blob_drift')
        require(read(dest/name,MAX_SOURCE,UID,0o600)==(originals[name][0],private_stats[name]),'final_copy_byte_or_stat_drift')
    require(core_state()==before and refs()==ref_pin,'final_primary_drift')
    receipt={'format':'swdb.git-only-sparse-retirement-two-source-private-copy.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'primary40':FROZEN,'administrative40':args.administrative40,'administrative_ref':ADMIN_REF,'evidence_directory':directory,'added_paths_count':len(paths),
             'destination':str(dest),'source_copies':result,'primary_common_config_native_retention_refs_unchanged':True,'primary_state':before,
             'selected_mains_invoked':False,'cleanup_capacity_or_scientific_admission':False}
    wire=json.dumps(receipt,sort_keys=True,separators=(',',':'));require(STOP_SIGNAL is None and len(wire.encode())<=16384,'compact_receipt_cap_or_interruption');print(wire)
if __name__=='__main__':
    try:main()
    except (Refused,OSError,ValueError,subprocess.SubprocessError,UnicodeError) as e:
        print(json.dumps({'format':'swdb.git-only-sparse-retirement-source-copy-refusal.v1','sealed':False,'error_class':type(e).__name__,'error_digest':sha(str(e).encode()),'partial_outputs_preserved':True,'received_signal':STOP_SIGNAL}));raise SystemExit(1)
