"""2026-10-08 ET. Prospective read-only native-stdin query; no target imports or writes."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import signal
import socket
import stat
import subprocess
import sys
import time

BASE=Path('/data1/yanruj')
PRIMARY=BASE/'ArchEvolve'
COMMON=PRIMARY/'.git'
UID=114316761
GIT_SHA='06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'
PY_SHA='e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
KEYS={'extensions.worktreeconfig','core.bare','core.worktree','core.sparsecheckout','core.sparsecheckoutcone','index.sparse'}
MAX_FILE=256*1024
MAX_OUTPUT=64*1024
MAX_REGISTRATIONS=64
STAMP=('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_blocks','st_mtime_ns','st_ctime_ns')
def require(ok,code):
    if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stamp(s):return {k:getattr(s,k) for k in STAMP}
def timeout(_signum,_frame):raise TimeoutError('finite_query_deadline')
def directory(p):
    require(p.is_absolute() and all(not q.is_symlink() for q in (p,*p.parents)),'directory_redirect')
    s=p.lstat()
    require(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and not s.st_mode&(stat.S_ISUID|stat.S_ISVTX),'directory_identity')
    require(not s.st_mode&stat.S_ISGID or s.st_gid==base_stat.st_gid,'directory_setgid_identity')
    require(s.st_dev==base_stat.st_dev,'directory_device')
    return stamp(s)
def read(p, maximum=MAX_FILE, native=False):
    require(p.is_absolute() and all(not q.is_symlink() for q in (p,*p.parents)),'file_redirect')
    with p.open('rb') as f:
        before=f.fileno();s=os.fstat(before)
        require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==(0 if native else UID) and not s.st_mode&0o7000,'file_identity')
        require(s.st_size<=maximum,'file_cap')
        raw=f.read(maximum+1);end=os.fstat(before)
    require(len(raw)==s.st_size and stamp(s)==stamp(end)==stamp(p.lstat()),'file_changed')
    return raw,{'path':str(p),'bytes':len(raw),'sha256':sha(raw),'stat':stamp(s)}
def native(p,size,digest):
    resolved=p.resolve(strict=True)
    raw,pin=read(resolved,16*1024*1024,native=True)
    require(len(raw)==size and sha(raw)==digest and stat.S_IMODE(pin['stat']['st_mode'])==0o755,'native_pin')
    return pin
def git(*args,maximum=MAX_OUTPUT):
    require(time.monotonic()<deadline,'query_deadline')
    # Repository/common/worktree configuration only: no account/system config,
    # URL use, lazy fetch, credential lookup, pager, optional index lock or hook.
    env={'PATH':'/usr/bin:/bin','LANG':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null',
         'GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0','GIT_NO_LAZY_FETCH':'1','GIT_PAGER':'cat'}
    result=subprocess.run(['/usr/bin/git','-c','protocol.allow=never','-c','core.fsmonitor=false','-C',str(PRIMARY),*args],
        env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(20,max(.1,deadline-time.monotonic())),check=False)
    require(result.returncode==0 and len(result.stdout)<=maximum and len(result.stderr)<=4096,'readonly_git_refused_or_cap')
    return result.stdout

def config_rows(raw):
    require(raw.endswith(b'\0'),'config_wire_terminator')
    pieces=raw[:-1].split(b'\0')
    require(len(pieces)%3==0,'config_wire_triplets')
    rows=[]; include_count=0
    for i in range(0,len(pieces),3):
        scope,origin,item=pieces[i:i+3]
        key,sep,value=item.partition(b'\n')
        require(scope in (b'system',b'global',b'local',b'worktree',b'command',b'unknown'),'config_wire_scope')
        if key.lower().startswith((b'include.',b'includeif.')):include_count+=1
        if key.lower() not in {k.encode() for k in KEYS}:continue
        name=key.decode('ascii').lower()
        row={'key':name,'scope':scope.decode(),'origin_bytes':len(origin),'origin_sha256':sha(origin),
             'value_present':bool(sep),'value_bytes':len(value),'value_sha256':sha(value)}
        if origin.startswith(b'file:'):
            text=origin[5:].decode('utf-8',errors='strict');p=Path(text)
            if not p.is_absolute():p=PRIMARY/p
            if '..' not in p.parts and p.is_relative_to(COMMON) and not {'auth.json','.codex','.ssh','.aws'}.intersection(p.parts):
                row['repository_origin_path']=str(p)
                row['repository_origin_literal']=origin.decode('utf-8')
        elif origin==b'command line:':row['origin_class']='command_line'
        if name!='core.worktree':
            literal=value.lower()
            allowed={b'true':True,b'yes':True,b'on':True,b'1':True,b'false':False,b'no':False,b'off':False,b'0':False,b'':False}
            row['recognized_boolean']=not sep or literal in allowed
            if row['recognized_boolean']:row['boolean_value']=True if not sep else allowed[literal]
        else:
            try:text=value.decode('utf-8',errors='strict')
            except UnicodeError:text=''
            p=Path(text)
            if text and '\n' not in text and p.is_absolute() and '..' not in p.parts and p.is_relative_to(BASE) and not {'.codex','.ssh','.aws','auth.json'}.intersection(p.parts):
                row['public_absolute_worktree_value']=text
            else:row['unrecognized_or_relative_worktree_value_not_disclosed']=True
        rows.append(row)
    return rows,include_count

def snapshot():
    state={'base':directory(BASE),'primary':directory(PRIMARY),'common_git':directory(COMMON)}
    data,state['common_configuration']=read(COMMON/'config')
    configs=[COMMON/'config.worktree']
    registration_root=COMMON/'worktrees'
    if registration_root.exists():
        state['registration_root']=directory(registration_root)
        names=sorted(p.name for p in registration_root.iterdir())
        require(len(names)<=MAX_REGISTRATIONS,'registration_cap')
        state['registration_names']=names
        state['registrations']={name:directory(registration_root/name) for name in names}
        configs.extend(registration_root/name/'config.worktree' for name in names)
    else:state['registration_root_absent']=True
    inventory=[]
    for p in configs:
        if p.exists() or p.is_symlink():
            _raw,pin=read(p);inventory.append({'exists':True,**pin})
        else:inventory.append({'path':str(p),'exists':False})
    state['registered_worktree_configurations']=inventory
    return state

if __name__=='__main__':
    try:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--expected-primary40',required=True)
        a=parser.parse_args()
        require(re.fullmatch('[0-9a-f]{40}',a.expected_primary40),'explicit_primary_commit')
        require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','account_platform')
        require(sys.dont_write_bytecode and sys.flags.no_user_site and sys.flags.isolated==0,'native_B_s_stdin_required')
        require(not any(k.startswith('GIT_') for k in os.environ),'caller_git_override_refused')
        require(not os.environ.get('PYTHONPATH') and not os.environ.get('PYTHONHOME'),'caller_python_override_refused')
        base_stat=BASE.lstat()
        require(stat.S_ISDIR(base_stat.st_mode) and stat.S_IMODE(base_stat.st_mode)==0o700 and base_stat.st_uid==UID and not BASE.is_symlink(),'private_BASE')
        signal.signal(signal.SIGALRM,timeout);signal.alarm(60);deadline=time.monotonic()+55
        native_before={'git':native(Path('/usr/bin/git'),4019024,GIT_SHA),
                       'python':native(Path('/usr/bin/python3.12'),8020928,PY_SHA)}
        require(Path(sys.executable).resolve(strict=True)==Path(native_before['python']['path']),'actual_native_python')
        before=snapshot()
        version=git('--version').decode('ascii').strip()
        require(re.fullmatch(r'git version 2\.[0-9]+(?:\.[0-9]+)?(?:[^\r\n]{0,80})?',version),'Git2_version')
        head=git('rev-parse','HEAD').decode('ascii').strip()
        require(head==a.expected_primary40,'primary_HEAD_changed')
        branch=git('branch','--show-current').decode('ascii').strip()
        status=git('status','--porcelain','--untracked-files=all')
        configuration=git('config','--no-includes','--show-origin','--show-scope','--null','--list',maximum=MAX_FILE)
        selected,include_count=config_rows(configuration)
        after=snapshot()
        native_after={'git':native(Path('/usr/bin/git'),4019024,GIT_SHA),
                      'python':native(Path('/usr/bin/python3.12'),8020928,PY_SHA)}
        require(before==after and native_before==native_after,'configuration_or_native_identity_changed')
        require(git('rev-parse','HEAD').decode('ascii').strip()==head and git('status','--porcelain','--untracked-files=all')==status,'primary_changed')
        status_rows=status.decode('utf-8',errors='strict').splitlines()
        public_status=[]
        for row in status_rows:
            require(len(row)>=3,'status_wire')
            public_status.append({'code':row[:2],'path_sha256':sha(row[3:].encode()),
                                  **({'path':row[3:]} if row[3:]=='swdb-project/records/.retention.lock' else {})})
        result={'format':'swdb.lanl17-git-common-sparse-configuration-observation.v1','sealed':False,
                'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'scope':'read-only repository/common/worktree settings; account/system/include configuration excluded; no migration or storage admission',
                'native':native_before,'git_version':version,'primary_HEAD':head,'primary_branch':branch,
                'primary_status_rows':public_status,'configuration_scope':'direct_repository_only_no_system_global_or_includes',
                'include_directives_not_followed_count':include_count,
                'selected_configuration':selected,'configuration_inventory':before,
                'source_config_bytes_not_disclosed':True,'URLs_credentials_unselected_config_not_disclosed':True,
                'before_after_identity_stable':True,'query_has_no_config_or_Git_write_commands':True}
        encoded=json.dumps(result,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
        require(len(encoded)<=MAX_OUTPUT,'bounded_result')
        signal.alarm(0)
        sys.stdout.buffer.write(encoded+b'\n')
    except (ValueError,OSError,UnicodeError,TimeoutError,subprocess.SubprocessError) as exc:
        sys.stdout.write(json.dumps({'format':'swdb.lanl17-git-common-sparse-configuration-refusal.v1','sealed':False,
            'exception_class':type(exc).__name__,'message_sha256':sha(str(exc).encode()),'raw_diagnostic_disclosed':False})+'\n')
        raise SystemExit(1)
