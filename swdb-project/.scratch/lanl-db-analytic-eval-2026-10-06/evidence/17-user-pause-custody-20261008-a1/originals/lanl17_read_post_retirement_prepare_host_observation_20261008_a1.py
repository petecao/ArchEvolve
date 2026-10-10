"""2026-10-08 ET. SOURCE ONLY / NOT RUN: one read-only post-RETIRE host observation.
No retirement/prepare/capacity/science admission, versions, selected mains or auth contents.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
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
PATH='/usr/bin:/bin:/usr/local/bin'
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+60
MAX_RETURN=16384
LEASE_NAMES=('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')
ABSENT=(BASE/'ArchEvolve-lanl17-source-20261007-a4',
        BASE/'ArchEvolve-lanl17-freeze-evidence-20261007-a4',
        BASE/'ArchEvolve-lanl17-actual-report-evidence-20261007-a4',
        Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4'),
        Path('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a4'),
        Path('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a4'))
# Original c6eb byte observations; runtime rechecks, not inferred current availability.
KNOWN={
 'git':('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
 'python3':('/usr/bin/python3.12',8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),
 'tmux':('/usr/bin/tmux',1102608,'034b15c64035f783d43862f2775eb4828f61571ca62c8199796000b97d556ecd'),
 'numactl':('/usr/bin/numactl',36080,'f3944bcd7848d64424f8daf27f350b03d7f3281b2fb9be5eaaba0ddd0e72efb8'),
 'strace':('/usr/bin/strace',2087432,'28f957c227012de0b18d1bd7fff2d396cb693ea60ed8013be68de071e84b5001'),
 'timeout':('/usr/bin/timeout',39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),
 'bash':('/usr/bin/bash',1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),
 'node':('/usr/bin/node',91392840,'3b442520134d4247f8d97ad4dc2d1443bdad6f0ebef670f06295743e864a37aa')}
PUBLISHED=((BASE/'lanl17-dx100-hooks-20261008-a1/post-checkout',17300,
             'd340f59f529d146ce4070843fc3314b0ab0b98cb1bacd79b2e9d61b726d07527',0o700),
           (BASE/'lanl17-dx100-deployment-20261008-a1/request.json',13676,
             'afaac0bf5e02b742318fcd1709546622f212ea73117d17e9e6e1c7ff13278822',0o600))
RETENTION_STAT={'dev':2097,'ino':54947305,'mode':33206,'uid':UID,'gid':0,'nlink':1,
                'size':0,'mtime_ns':1791030933805697274,'ctime_ns':1791030933805697274}

class Refused(ValueError):pass

def need(ok,code):
    if not ok:raise Refused(code)

def tick():need(time.monotonic()<END,'query_deadline')

def stamp(s):return {k:getattr(s,'st_'+k) for k in FIELDS}

def canonical(p):
    need(p.is_absolute() and p.resolve(strict=True)==p
         and not any(q.is_symlink() for q in (p,*p.parents)),'canonical_nonsymlink_route')

def file_pin(p,cap,owner,mode=None,writable=False):
    tick();canonical(p);s=p.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1
         and not s.st_mode&0o7000 and 0<=s.st_size<=cap
         and (writable or not s.st_mode&0o022)
         and (mode is None or stat.S_IMODE(s.st_mode)==mode),'file_identity_mode_or_cap')
    h=hashlib.sha256();n=0;fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'file_open_changed')
        while True:
            tick();b=f.read(min(1024*1024,cap-n+1))
            if not b:break
            n+=len(b);need(n<=cap,'file_read_cap');h.update(b)
        need(n==s.st_size and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),
             'returned_bytes_or_file_stat_changed')
    return {'path':str(p),'bytes':n,'sha256':h.hexdigest(),'stat':stamp(s)}

def metadata(p,cap):
    tick();canonical(p);s=p.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1
         and not s.st_mode&0o7000 and 0<=s.st_size<=cap,'metadata_identity_or_cap')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'metadata_open_changed');b=f.read(cap+1)
        need(len(b)==s.st_size<=cap and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),
             'metadata_returned_bytes_or_stat_changed')
    return b,{'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'stat':stamp(s)}

def strict(b):
    def pairs(items):
        d={}
        for k,v in items:need(k not in d,'duplicate_JSON_key');d[k]=v
        return d
    def bad(value):raise Refused('nonfinite_JSON')
    v=json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
    need(type(v) is dict,'metadata_object_required');return v

def command(argv):
    tick();r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(10,END-time.monotonic()),
                           env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0'})
    need(r.returncode==0 and not r.stderr and len(r.stdout)<=MAX_RETURN,'readonly_command_refused')
    return r.stdout

def source_state(expected):
    results={}
    for args in (('rev-parse','HEAD'),('branch','--show-current'),('rev-parse','origin/yanrujhou_main'),
                 ('diff','--name-only'),('diff','--cached','--name-only'),
                 ('status','--porcelain','--untracked-files=all')):
        b=command(['/usr/bin/git','--no-replace-objects','--no-optional-locks','-c','core.fsmonitor=false',
                   '-C',str(PRIMARY),*args]);results[' '.join(args)]=b.decode().strip()
    need(results['rev-parse HEAD']==results['rev-parse origin/yanrujhou_main']==expected
         and results['branch --show-current']=='yanrujhou_main'
         and not results['diff --name-only'] and not results['diff --cached --name-only']
         and results['status --porcelain --untracked-files=all']=='?? swdb-project/records/.retention.lock',
         'PRIMARY_not_expected_or_clean')
    pin=file_pin(PRIMARY/'swdb-project/records/.retention.lock',0,UID,writable=True)
    need(pin['stat']==RETENTION_STAT and pin['sha256']==hashlib.sha256(b'').hexdigest(),
         'original_empty_retention_changed')
    results['original_empty_retention_byte_pin']=pin;return results

def leases():
    result={}
    for name in LEASE_NAMES:
        b,pin=metadata(BASE/'lact-host-lease'/(name+'.meta.json'),32768);v=strict(b)
        need(v['state']=='released','all_three_leases_must_be_released')
        result[name]={'state':v['state'],'original_file_pin':pin}
    return result

def directory_identity(p,private=False):
    canonical(p);s=p.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and not s.st_mode&(stat.S_ISUID|stat.S_ISVTX)
         and (not private or stat.S_IMODE(s.st_mode)==0o700),'owned_directory_identity')
    return {k:stamp(s)[k] for k in ('dev','ino','mode','uid','gid')}

def absent():
    result={str(p):not os.path.lexists(p) for p in ABSENT}
    need(all(result.values()),'all_six_reserved_routes_must_be_absent');return result

def command_routes():
    rows={}
    for name in (*KNOWN,'sha256sum','wc','mkdir','df'):
        tick();route=shutil.which(name,path=PATH);need(route is not None,'fixed_command_missing')
        alias=Path(route);before=alias.lstat();p=alias.resolve(strict=True)
        need(p.is_relative_to(Path('/usr')) and before.st_uid==0 and before.st_gid==0
             and before.st_nlink==1 and (stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode)),
             'system_command_alias_identity')
        cap=(128 if name=='node' else 64)*1024*1024;pin=file_pin(p,cap,0)
        need(pin['stat']['gid']==0 and stat.S_IMODE(pin['stat']['mode'])==0o755
             and os.access(p,os.X_OK) and stamp(alias.lstat())==stamp(before)
             and alias.resolve(strict=True)==p,'native_command_route_changed')
        if name in KNOWN:
            path,size,dig=KNOWN[name]
            need(pin['path']==path and pin['bytes']==size and pin['sha256']==dig,'original_native_byte_pin_changed')
        rows[name]={'configured_PATH_route':route,'alias_stat':stamp(before),'resolved':pin}
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    p.add_argument('--expected-primary40',required=True);a=p.parse_args()
    need(re.fullmatch('[a-f0-9]{40}',a.expected_primary40) is not None,'full_expected_PRIMARY_required')
    need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10'
         and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj'
         and sys.flags.dont_write_bytecode and sys.flags.no_user_site and not sys.flags.optimize,
         'native_mbit10_account_flags')
    need(not any(os.environ.get(k) for k in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONINSPECT',
         'PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','BASH_ENV','ENV')),'unsafe_startup_routing')
    need(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12'),'native_Python_runtime')
    directories={str(x):directory_identity(x,x==BASE or x in [p.parent for p,*unused in PUBLISHED])
                 for x in (BASE,PRIMARY,*(row[0].parent for row in PUBLISHED))}
    routes=command_routes();before=source_state(a.expected_primary40);lease_before=leases();missing=absent()
    published=[]
    for path,size,dig,mode in PUBLISHED:
        pin=file_pin(path,262144,UID,mode);need(pin['bytes']==size and pin['sha256']==dig,
                                              'published_hook_request_changed');published.append(pin)
    account_home=pwd.getpwuid(UID).pw_dir;login=BASE/'.codex'
    login_exists=login.is_dir();auth_exists=(login/'auth.json').is_file() if login_exists else False
    env={'account_HOME_matches_pwd':os.environ.get('HOME')==account_home,
         'CODEX_HOME_present':bool(os.environ.get('CODEX_HOME')),
         'CODEX_HOME_matches_original_public_route':os.environ.get('CODEX_HOME')==str(login),
         'original_task_token_present':bool(os.environ.get('SWDB_LANL17_ORIGINAL_CODEX_HOME')),
         'original_task_token_matches_public_route':os.environ.get('SWDB_LANL17_ORIGINAL_CODEX_HOME')==str(login),
         'original_login_directory_exists':login_exists,'authentication_file_exists_only':auth_exists,
         'authentication_contents_read':False,'HOME_CODEX_HOME_or_token_modified':False,
         'sanitized_prepare_PATH':PATH}
    with Path('/proc/meminfo').open('rb') as f:mem=f.read(65537)
    need(len(mem)<=65536,'kernel_meminfo_cap')
    matches=[r for r in mem.splitlines() if r.startswith(b'MemAvailable:')]
    need(len(matches)==1 and matches[0].split()[2]==b'kB','kernel_MemAvailable_shape')
    memory=int(matches[0].split()[1])*1024
    available={str(x):os.statvfs(x).f_bavail*os.statvfs(x).f_frsize for x in ('/data1','/data')}
    load=os.getloadavg();df=command([routes['df']['resolved']['path'],'-B1','--output=target,size,used,avail','/data1','/data']).decode()
    after=source_state(a.expected_primary40);lease_after=leases()
    need(before==after and lease_before==lease_after and absent()==missing,'source_lease_or_absent_scope_changed')
    for path,size,dig,mode in PUBLISHED:
        need(file_pin(path,262144,UID,mode)==next(x for x in published if x['path']==str(path)),
             'published_input_postflight_changed')
    for name,row in routes.items():
        need(file_pin(Path(row['resolved']['path']),(128 if name=='node' else 64)*1024*1024,0)==row['resolved']
             and stamp(Path(row['configured_PATH_route']).lstat())==row['alias_stat']
             and Path(row['configured_PATH_route']).resolve(strict=True)==Path(row['resolved']['path']),
             'native_command_postflight_changed')
    need(all(directory_identity(Path(k),k==str(BASE) or k in [str(p.parent) for p,*unused in PUBLISHED])==v
             for k,v in directories.items()),'owned_directory_identity_changed')
    tick();out={'format':'swdb.lanl17-post-retirement-prepare-host-original.v1','sealed':False,
         'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'expected_primary':a.expected_primary40,'source_context_before':before,'source_context_after':after,
         'necessary_command_byte_pins':routes,'private_storage_directory_identities':directories,
         'released_leases_before':lease_before,'released_leases_after':lease_after,
         'all_six_reserved_paths_absent':missing,'published_hook_request_byte_pins':published,
         'account_environment_existence_observation':env,'actual_free_bytes':available,
         'memory_available_bytes':memory,'load_average':load,'df_mount_bytes':df,
         'unchanged_helper_floor_observations':{'memory80GiB':memory>=80*1024**3,
             'data1_21GiB':available['/data1']>=21*1024**3,'data_single_lane24GiB':available['/data']>=24*1024**3},
         'retirement_or_prepare_capacity_or_scientific_admission':False,
         'RAW_body_or_completed_proofs_or_scientific_modules_read':False,
         'selected_main_test_version_provider_compiler_executed':False,
         'remote_file_or_ref_or_config_mutated':False}
    raw=json.dumps(out,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
    need(len(raw)<=MAX_RETURN,'original_output_cap');sys.stdout.buffer.write(raw+b'\n')

if __name__=='__main__':
    def alarm(number,frame):raise Refused('query_alarm')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(60)
    try:main()
    except Exception as e:
        raw=json.dumps({'format':'swdb.lanl17-post-retirement-prepare-host-refusal.v1','sealed':False,
             'error_class':type(e).__name__,'error_sha256':hashlib.sha256(str(e).encode()).hexdigest(),
             'retirement_or_prepare_or_capacity_or_scientific_admission':False},separators=(',',':')).encode()
        sys.stdout.buffer.write(raw+b'\n');raise SystemExit(1)
    finally:signal.alarm(0)
