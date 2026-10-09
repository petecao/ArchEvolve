"""Created 2026-10-09 ET. SOURCE ONLY sensitive entry NAME/STAT diagnostic, NOT RUN.
No sensitive file contents, content hashes, symlink targets, backup/removal or index.
"""
import argparse,datetime,hashlib,json,os,pwd,signal,socket,stat,subprocess,sys,time,re
from pathlib import Path
UID=114316761
R='5e12a9796432654d88def24ecea617d16ca605b2'
HEAD='c4ab2fdbb0b0c57ee9f515522835897f24466d6b'
PRIMARY=Path('/data1/yanruj/ArchEvolve')
SOURCE=Path('/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5')
CANDIDATE=Path('/data1/yanruj/ArchEvolve-lanl-generality-final-20261007-a1')
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+180
ENTRY_CAP=65536
METADATA_CAP=8*1024**2
ARGS=None
def need(ok,reason):
    if not ok: raise ValueError(reason)

def tick(): need(time.monotonic()<END,'host_metadata_deadline')

def digest(b): return hashlib.sha256(b).hexdigest()

def stamp(s): return {k:getattr(s,'st_'+k) for k in FIELDS}

def kernel_bytes(p,cap,owner):
    tick();s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==owner,'kernel_identity')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'kernel_open_changed');b=f.read(cap+1)
        need(len(b)<=cap and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'kernel_cap_or_stat_changed')
    return b

def process_identity(pid):
    tick();need(type(pid) is int and pid>0,'process_PID_type');p=Path('/proc')/str(pid)
    s=p.stat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID,'owned_process_identity')
    b=kernel_bytes(p/'stat',8192,UID);parts=b.rsplit(b')',1)[1].split();need(len(parts)>=20,'process_stat_shape')
    need(b.split(b' ',1)[0]==str(pid).encode(),'process_stat_PID')
    parent=int(parts[1]);start=int(parts[19]);need(parent>0 and start>0,'process_parent_start')
    command=kernel_bytes(p/'cmdline',65536,UID);need(command.endswith(b'\0'),'process_cmdline_terminated')
    argv=command[:-1].split(b'\0');exe=os.readlink(p/'exe')
    b2=kernel_bytes(p/'stat',8192,UID);parts2=b2.rsplit(b')',1)[1].split()
    need(p.stat().st_uid==s.st_uid and p.stat().st_ino==s.st_ino and int(parts2[1])==parent and int(parts2[19])==start,'process_identity_race')
    need(kernel_bytes(p/'cmdline',65536,UID)==command and os.readlink(p/'exe')==exe,'process_command_exe_race')
    return {'pid':pid,'ppid':parent,'proc_inode':s.st_ino,'uid':s.st_uid,'start_ticks':start,'cmdline_sha256':digest(command),'exe_route_sha256':digest(os.fsencode(exe))},argv,exe

class Parser(argparse.ArgumentParser):
    def error(self,message):raise ValueError('argument_contract')

def hex64(v):need(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'actual_SHA');return v

def run(argv):
    tick();p=subprocess.run(argv,capture_output=True,timeout=min(15,max(.1,END-time.monotonic())),env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'},stdin=subprocess.DEVNULL)
    need(p.returncode==0 and len(p.stdout)<=65536 and len(p.stderr)<=65536,'metadata_command_exit_or_cap');return p.stdout.decode()

def root_tool_pin(route,n,h):
    p=Path(route);need(p.resolve(strict=True)==p and not any(x.is_symlink() for x in (p,*p.parents)),'native_tool_canonical')
    s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o755 and s.st_size==n<=16*1024*1024,'native_tool_root_regular_size_mode')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);count=0;hasher=hashlib.sha256()
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'native_tool_open_race')
        while True:
            tick();b=f.read(65536)
            if not b:break
            count+=len(b);need(count<=n,'native_tool_byte_cap');hasher.update(b)
        need(count==n and hasher.hexdigest()==h and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat()),'native_tool_hash_or_race')
    return {'path':route,'bytes':n,'sha256':h,'stat':stamp(s)}

def metadata_bytes(v):
    return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()

def transport_identity():
    own,argv,exe=process_identity(os.getpid())
    need(exe=='/usr/bin/python3.12' and len(argv)==7 and argv[:4]==[b'/usr/bin/python3.12',b'-I',b'-B',b'-c'],'exact_native_inline_argv')
    need(argv[5:]==[b'--source-sha256',ARGS.source_sha256.encode()] and digest(argv[4])==ARGS.source_sha256 and own['ppid']==os.getppid(),'exact_self_source_arguments')
    parent,pargv,pexe=process_identity(own['ppid'])
    need(pexe=='/usr/bin/timeout' and pargv==[b'/usr/bin/timeout',b'--signal=TERM',b'--kill-after=60s',b'240s',*argv],'exact_immediate_GNU240_K60_parent')
    return {'self':own,'parent':parent,'source_sha256':ARGS.source_sha256}

def metadata_git(root,*tail):
    return run(['/usr/bin/git','--no-replace-objects','-c','core.fsmonitor=false','-C',str(root),*tail]).strip()

def source_registration():
    for p in (PRIMARY,SOURCE,CANDIDATE):
        need(p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)) and p.is_dir() and p.stat().st_uid==UID,'owned_canonical_source_candidate')
    need(metadata_git(PRIMARY,'rev-parse','HEAD')==metadata_git(PRIMARY,'rev-parse','origin/yanrujhou_main')==metadata_git(SOURCE,'rev-parse','HEAD')==R,'source_PRIMARY_origin_S_R')
    need(metadata_git(PRIMARY,'branch','--show-current')=='yanrujhou_main','PRIMARY_branch')
    need(metadata_git(CANDIDATE,'rev-parse','HEAD')==HEAD and metadata_git(CANDIDATE,'rev-parse','--abbrev-ref','HEAD')=='HEAD','candidate_c4_detached')
    need(metadata_git(CANDIDATE,'status','--porcelain','--untracked-files=all')=='','candidate_clean')
    common=Path(metadata_git(CANDIDATE,'rev-parse','--git-common-dir'));gitdir=Path(metadata_git(CANDIDATE,'rev-parse','--git-dir'))
    need(common==PRIMARY/'.git' and common.resolve(strict=True)==common and common.stat().st_uid==UID,'candidate_PRIMARY_common')
    need(gitdir.parent==common/'worktrees' and gitdir.resolve(strict=True)==gitdir and gitdir.is_dir() and gitdir.stat().st_uid==UID and not any(q.is_symlink() for q in (gitdir,*gitdir.parents)),'candidate_registration_canonical_owned')
    need(not os.path.lexists(gitdir/'locked') and not os.path.lexists(gitdir/'index.lock'),'candidate_registration_unlocked')
    return {'candidate':str(CANDIDATE),'head':HEAD,'detached':True,'clean':True,'common_git':str(common),'git_directory':str(gitdir),'PRIMARY_head':R,'PRIMARY_origin':R,'SOURCE_head':R,'root_stat':stamp(CANDIDATE.lstat()),'git_directory_stat':stamp(gitdir.lstat())}

def name_inventory():
    rows=[];matches=[];todo=[CANDIDATE];size=2
    while todo:
        tick();p=todo.pop();s=p.lstat();relative=p.relative_to(CANDIDATE).as_posix()
        need(len(rows)<ENTRY_CAP and len(os.fsencode(relative))<=4096 and s.st_uid==UID,'entry_count_path_owner')
        kind='directory' if stat.S_ISDIR(s.st_mode) else 'regular' if stat.S_ISREG(s.st_mode) else 'symlink' if stat.S_ISLNK(s.st_mode) else 'other'
        row={'relative_path':relative,'kind':kind,'stat':stamp(s)}
        if kind=='directory':
            children=sorted(p.iterdir(),key=lambda q:os.fsencode(q.name));need(len(children)<=ENTRY_CAP and stamp(p.lstat())==stamp(s),'directory_listing_cap_or_race')
            todo.extend(reversed(children))
        size+=len(metadata_bytes(row));need(size<=METADATA_CAP,'name_stat_inventory_8MiB_cap');rows.append(row)
        if any(x in p.parts for x in ('.codex','.ssh','.aws')) or p.name in ('auth.json','provider.json','prompt.txt','feedback.txt'):matches.append(row)
    return rows,matches

def tracked_and_ignored(row):
    # Git reads its index/ignore rules; this helper never opens the selected entry.
    relative=row['relative_path'];pathspec=':(literal)'+relative
    raw=metadata_git(CANDIDATE,'ls-files','--format=%(objectmode) %(path)','-z','--',pathspec)
    records=[]
    for item in raw.split('\0'):
        if not item:continue
        mode,name=item.split(' ',1);need(mode in ('100644','100755','120000','160000'),'Git_index_mode');records.append((mode,name))
    need(len(records)<=ENTRY_CAP,'matching_index_entries_cap')
    tick();p=subprocess.run(['/usr/bin/git','--no-replace-objects','-c','core.fsmonitor=false','-C',str(CANDIDATE),'check-ignore','--no-index','-q','--',relative],capture_output=True,timeout=min(15,max(.1,END-time.monotonic())),env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'},stdin=subprocess.DEVNULL)
    need(p.returncode in (0,1) and not p.stdout and not p.stderr,'Git_ignore_metadata_exit')
    direct=[mode for mode,name in records if name==relative];need(len(direct)<=1,'duplicate_exact_tracked_entry')
    return {'exact_entry_tracked':bool(direct),'exact_entry_git_mode':direct[0] if direct else None,'tracked_descendant_count':sum(name.startswith(relative+'/') for mode,name in records),'ignored_by_rules_even_if_tracked':p.returncode==0,'credential_contents_read_or_hashed':False}

def observe():
    need(sys.platform=='linux' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and socket.gethostname().split('.')[0]=='mbit10','native_account_host')
    need(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12') and sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize,'isolated_native_python')
    transport=transport_identity();gitpin=root_tool_pin('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb');version=metadata_git(CANDIDATE,'--version');need(version=='git version 2.48.1','actual_native_Git_version')
    before=source_registration();first,matches=name_inventory();details=[]
    for row in matches:tick();details.append(row|{'Git_metadata':tracked_and_ignored(row)})
    second,after_matches=name_inventory();need(first==second and matches==after_matches,'complete_name_stat_nine_field_closure')
    for row in details:need(tracked_and_ignored(row)==row['Git_metadata'],'selected_Git_index_ignore_metadata_continuity')
    need(source_registration()==before and transport_identity()==transport and root_tool_pin('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb')==gitpin,'source_registration_native_Git_transport_continuity')
    result={'format':'swdb.lanl17-generality-sensitive-entry-name-stat-diagnostic.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metadata_observation_completed':True,'state':'observed','candidate':str(CANDIDATE),'head':HEAD,'entry_count_checked':len(first),'matching_entry_count':len(details),'matching_entries':details,'source_registration':before,'native_Git_version':version,'native_Git_pin':gitpin,'no_symlink_directories_followed':True,'selected_file_bodies_or_content_hashes_read':False,'symlink_targets_read':False,'original_preflight_privacy_gate_unchanged':True,'full_preflight_readiness_not_inferred':True,'no_use_proof_not_supplied':True,'backup_eligibility_only':False,'backup_created':False,'removal_admitted':False,'index_clearance':False,'scientific_admission':False}
    need(len(metadata_bytes(result))<=METADATA_CAP,'bounded_return_8MiB');return result

def main():
    global ARGS
    p=Parser(add_help=False);p.add_argument('--source-sha256',required=True);ARGS=p.parse_args();hex64(ARGS.source_sha256)
    sys.stdout.buffer.write(metadata_bytes(observe()))

def interrupted(number,frame):raise ValueError('sensitive_name_stat_signal_or_deadline')
for number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)
signal.alarm(180)
try:main()
except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,RecursionError,StopIteration,subprocess.SubprocessError) as exc:
    print(json.dumps({'format':'swdb.lanl17-generality-sensitive-entry-name-stat-diagnostic.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metadata_observation_completed':False,'state':'unknown','backup_eligibility_only':False,'backup_created':False,'removal_admitted':False,'index_clearance':False,'scientific_admission':False,'error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode())},sort_keys=True,allow_nan=False))
