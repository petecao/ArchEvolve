import resource
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(170,175))
import os,json,hashlib,stat,subprocess,signal,time,ast,sys,types,re,copy,io,shutil,zlib
from pathlib import Path
signal.alarm(180)
started=time.monotonic()
ROOT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1')
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10')
MEMORY=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1')
OBSERVER=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v3')
SOURCE=Path("/data1/yanruj/probata-resume-20261016-2baf722f")
COMMIT="2baf722fdaa6cba24b859eae3172a6f597417d72"
POLICY_SHA='3f20967eaeaa7a3469ef4a4b249c2ce2161ae0ec9a9eda41be80c6d950919ad4'
READS={}
TRANSPORT=None
WANTED_PAM=[{'cgroup': '0::/user.slice/user-114316761.slice/user@114316761.service/init.scope', 'cmdline': ['(sd-pam)'], 'comm': '(sd-pam)', 'exe_permission_protected': True, 'pid': 3261267, 'start_ticks': '645211088', 'status': ['Name:\t(sd-pam)', 'State:\tS (sleeping)', 'PPid:\t3261266', 'TracerPid:\t0', 'Uid:\t114316761\t114316761\t114316761\t114316761', 'Gid:\t114316761\t114316761\t114316761\t114316761', 'NSpid:\t3261267']}, {'cgroup': '0::/user.slice/user-114316761.slice/user@114316761.service/init.scope', 'cmdline': ['/usr/lib/systemd/systemd', '--user', '--deserialize=24'], 'comm': 'systemd', 'exe': {'bytes': 100816, 'gid': 0, 'literal': '/usr/lib/systemd/systemd', 'mode': 33261, 'physical': '/usr/lib/systemd/systemd', 'sha256': '9a813714ffd4dadb692afe44384c9c5b334fa323a4ec1dd5157aebdcbbb0667a', 'uid': 0}, 'pid': 3261266, 'start_ticks': '645211085', 'status': ['Name:\tsystemd', 'State:\tS (sleeping)', 'PPid:\t1', 'TracerPid:\t0', 'Uid:\t114316761\t114316761\t114316761\t114316761', 'Gid:\t114316761\t114316761\t114316761\t114316761', 'NSpid:\t3261266']}]
def pam_identity():
 rows=[]
 for template in WANTED_PAM:
  pid=template['pid'];root=Path('/proc')/str(pid);status=(root/'status').read_text();tail=(root/'stat').read_text().rsplit(')',1)[1].split()
  row={'pid':pid,'comm':(root/'comm').read_text().strip(),'start_ticks':tail[19],'cmdline':(root/'cmdline').read_bytes().decode().split(chr(0))[:-1],'status':[l for l in status.splitlines()if l.startswith(('Name:','State:','PPid:','TracerPid:','Uid:','Gid:','NSpid:'))],'cgroup':(root/'cgroup').read_text().strip()}
  try:
   exe=os.readlink(root/'exe');path=Path(exe);s=path.stat();row['exe']={'literal':exe,'physical':str(path.resolve()),'bytes':s.st_size,'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  except PermissionError:row['exe_permission_protected']=True
  rows.append(row)
 if rows!=WANTED_PAM:raise ValueError('exact admitted PAM/parent identity changed')
 return {'pid':3261267,'parent':3261266,'identity_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),'permission_protected_exe_cwd_fds_inherited_OS_PAM_TCB':True}

def transport_identity():
 rows=[];current=os.getpid()
 for _ in range(6):
  root=Path('/proc')/str(current);text=(root/'status').read_text();fields={l.split(':',1)[0]:l.split(':',1)[1].strip()for l in text.splitlines()if ':'in l};tail=(root/'stat').read_text().rsplit(')',1)[1].split();parent=int(fields['PPid'])
  rows.append({'pid':current,'parent':parent,'comm':(root/'comm').read_text().strip(),'start_ticks':tail[19],'uids':fields['Uid'].split(),'argv':(root/'cmdline').read_bytes().decode().split(chr(0))[:-1]})
  if parent==0:break
  current=parent
 if len(rows)<5:raise ValueError('complete current SSH transport ancestry required')
 if rows[0]['argv']!=['/usr/bin/python3','-I','-B','-']or rows[0]['comm']!='python3':raise ValueError('exact current metadata interpreter required')
 timeout=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','185s','/usr/bin/python3','-I','-B','-']
 if rows[1]['argv']!=timeout or rows[1]['comm']!='timeout':raise ValueError('exact current outer timeout required')
 if rows[2]['argv']!=['sshd: yanruj@notty','','']or rows[2]['comm']!='sshd'or rows[2]['uids']!=[str(os.getuid())]*4:raise ValueError('exact current same-UID SSH transport required')
 if rows[3]['argv']!=['sshd: yanruj [priv]','']or rows[3]['comm']!='sshd'or rows[3]['uids']!=['0']*4:raise ValueError('exact root privileged SSH parent required')
 if rows[4]['comm']!='sshd'or rows[4]['uids']!=['0']*4 or len(rows[4]['argv'])!=1 or not rows[4]['argv'][0].startswith('sshd: /usr/sbin/sshd -D [listener] '):raise ValueError('root SSH listener ancestry required')
 binary=Path('/usr/sbin/sshd');st=binary.stat()
 if st.st_uid!=0 or not stat.S_ISREG(st.st_mode):raise ValueError('root-owned physical SSH daemon binary required')
 return {'chain':rows,'daemon_binary':{'path':str(binary.resolve()),'bytes':st.st_size,'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()},'allowed_unreadable_current_transport_pid':rows[2]['pid']}

def scan():
 matches=[];unreadable=[];disappeared=0;checked=0;descriptors=0;os_helpers=[]
 for directory in sorted(Path('/proc').iterdir(),key=lambda p:p.name):
  if not directory.name.isdigit()or int(directory.name)==os.getpid():continue
  try:
   if directory.stat().st_uid!=os.getuid():continue
   checked+=1
   if checked>4096:raise ValueError('finite own process cap')
   command=(directory/'cmdline').read_bytes()
   if len(command)>1048576:raise ValueError('bounded command metadata')
   environment=(directory/'environ').read_bytes()
   if len(environment)>1048576:raise ValueError('bounded environment metadata')
   found=[n for n in needles if n.encode()in command or n.encode()in environment]
   for name in ('cwd','exe'):
    try:
     value=os.readlink(directory/name);found += [n for n in needles if n in value]
    except FileNotFoundError:disappeared+=1
   fds=list((directory/'fd').iterdir())
   if len(fds)>2048:raise ValueError('finite descriptor cap')
   for fd in fds:
    descriptors+=1
    if descriptors>32768:raise ValueError('finite aggregate descriptor cap')
    try:
     value=os.readlink(fd);found += [n for n in needles if n in value]
    except FileNotFoundError:disappeared+=1
   if found:matches.append({'pid':int(directory.name),'selected_roots':sorted(set(found))})
  except FileNotFoundError:disappeared+=1
  except PermissionError:
   if directory.name=='3261267':os_helpers.append(pam_identity())
   elif int(directory.name)==TRANSPORT['allowed_unreadable_current_transport_pid']:
    current=transport_identity()
    if [(r['pid'],r['parent'],r['start_ticks'],r['uids'])for r in current['chain']]!=[(r['pid'],r['parent'],r['start_ticks'],r['uids'])for r in TRANSPORT['chain']]:raise ValueError('current transport birth/ancestry changed')
    os_helpers.append({'current_query_transport':current})
   else:unreadable.append(int(directory.name))
 return {'own_processes_checked':checked,'descriptor_links_checked':descriptors,'vanished_process_or_descriptor_observations':disappeared,'selected_original_readers':matches,'unreadable_own_processes':unreadable,'exact_inherited_OS_PAM_helpers':os_helpers}
needles=('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10', '/data1/yanruj/probata-resume-20261016-2baf722f', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v2', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v3', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1')

def need(ok,message):
    if not ok:raise ValueError(message)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def stable(st):return tuple(getattr(st,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
def deadline():need(time.monotonic()-started<180,'retained ABI replay wall cap')
def strict(raw):
    def pairs(items):
        out={}
        for key,value in items:need(key not in out,'duplicate replay policy/metadata key');out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite replay metadata')))
def bounded(path,limit=8388608):
    path=Path(path);before=path.lstat();need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode) and 0<=before.st_size<=limit,'bounded canonical metadata input required')
    with path.open('rb') as handle:raw=handle.read(before.st_size+1)
    need(len(raw)==before.st_size and stable(path.lstat())==stable(before),'metadata input changed')
    return raw
def physical(row,retain=False):
    need(type(row) is dict and set(row)=={'path','bytes','sha256'} and type(row['path']) is str and type(row['bytes']) is int and 0<=row['bytes']<=1073741824,'closed bounded physical input required')
    path=Path(row['path']);before=path.lstat();need(path.is_absolute() and path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode) and before.st_size==row['bytes'],'physical selected extent/identity differs')
    need(not retain or row['bytes']<=8388608,'retained metadata cap')
    value=hashlib.sha256();count=0;parts=[]
    with path.open('rb') as handle:
        while True:
            deadline();chunk=handle.read(min(65536,row['bytes']-count+1))
            if not chunk:break
            count+=len(chunk);need(count<=row['bytes'],'selected input grew');value.update(chunk)
            if retain:parts.append(chunk)
    need(stable(path.lstat())==stable(before) and count==row['bytes'] and value.hexdigest()==row['sha256'],'physical selected input changed')
    old=READS.get(row['path']);need(old is None or old==row,'conflicting selected input identity');READS[row['path']]=row
    return b''.join(parts) if retain else row

def readonly(event,args):
    if event=='open':
        _path,mode,flags=args
        if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags&(1|2|64|512|1024):raise PermissionError('ABI replay is read-only')
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen','os.mkdir','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.chmod','os.chown','os.link','os.symlink','os.truncate','os.utime','os.chdir','os.putenv','os.unsetenv'}:raise PermissionError('ABI replay child/native/network/mutation refused')

def module_source(name,row):
    raw=physical(row,True);tree=ast.parse(raw)
    # The only nonstdlib imports are the helper's two fixed in-memory modules.
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):need(all(a.name.split('.')[0] in sys.stdlib_module_names for a in node.names),'unexpected primitive import')
        elif isinstance(node,ast.ImportFrom):need(node.module in ('swdb._dx100_whole','pathlib') or node.module.split('.')[0] in sys.stdlib_module_names,'unexpected primitive from-import')
    module=types.ModuleType(name);module.__file__=row['path'];sys.modules[name]=module
    exec(compile(tree,row['path'],'exec'),module.__dict__)
    return module

def checked_modules(policy):
    need(not any(name=='swdb' or name.startswith('swdb.') for name in sys.modules),'no project import before fixed module namespace')
    parent=types.ModuleType('swdb');parent.__path__=[]
    package=types.ModuleType('swdb._dx100_whole');package.__path__=[];parent._dx100_whole=package
    sys.modules['swdb']=parent;sys.modules['swdb._dx100_whole']=package
    normalizer=module_source('swdb._dx100_whole.role_normalized_gzip_v2',policy['controls']['normalizer'])
    tokens=module_source('swdb._dx100_whole.strict_minify_v2',policy['controls']['tokens'])
    package.role_normalized_gzip_v2=normalizer;package.strict_minify_v2=tokens
    helper=module_source('swdb._dx100_whole.abi_role_transport_v1',policy['controls']['helper']);package.abi_role_transport_v1=helper
    legacy=module_source('_retained_exact_legacy_abi',policy['controls']['legacy'])
    closed=module_source('_retained_closed_python',policy['controls']['python_surface'])
    binder=physical(policy['controls']['binder'],True);tree=ast.parse(binder)
    selected=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TYPE_KEYS' for t in n.targets)]
    selected += [n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in {'Refused','_need','validate_abi'}]
    need(len(selected)==4,'exact pure ABI validator source selection')
    api={'re':re};exec(compile(ast.Module(selected,type_ignores=[]),policy['controls']['binder']['path'],'exec'),api)
    origins={key:dict(path=row['path'],bytes=row['bytes'],sha256=row['sha256']) for key,row in policy['controls'].items()}
    return helper,legacy,api,origins,closed

def runtime_identity(policy,closed):
    need({name for name in sys.modules if name=='swdb' or name.startswith('swdb.')}=={'swdb','swdb._dx100_whole','swdb._dx100_whole.role_normalized_gzip_v2','swdb._dx100_whole.strict_minify_v2','swdb._dx100_whole.abi_role_transport_v1'}
        and sys.modules['swdb'].__path__==[] and sys.modules['swdb._dx100_whole'].__path__==[],'closed fixed module namespace changed')
    # Exact previously bound filesystem inventories also cover pure .py files;
    # runtime_hashes primarily names native binaries, not every stdlib .py.
    surface=closed.verify_python_metadata(policy['python_binding'])
    source_roots=[Path(name) for name in policy['python_binding']['surfaces']]
    result=[]
    for name,module in sorted(sys.modules.items()):
        if module is None:continue
        if name=='__main__' or name in ('swdb','swdb._dx100_whole','_retained_exact_legacy_abi','_retained_closed_python') or name.startswith('swdb._dx100_whole.'):continue
        path=getattr(module,'__file__',None)
        if not path:continue
        path=str(Path(path).resolve(strict=True));expected=policy['runtime_hashes'].get(path)
        if expected is None:
            need(any(Path(path).is_relative_to(root) for root in source_roots),'unbound executable stdlib module: '+name)
            expected=digest(bounded(path))
        st=Path(path).lstat();row={'path':path,'bytes':st.st_size,'sha256':expected};physical(row)
        result.append(dict(module=name,**row))
    mapped=[]
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields=line.split(None,5)
        if len(fields)==6 and 'x' in fields[1] and fields[5].startswith('/'):
            path=str(Path(fields[5]).resolve(strict=True));expected=policy['runtime_hashes'].get(path)
            need(expected is not None,'unbound mapped executable runtime: '+path)
            if path not in {row['path'] for row in mapped}:mapped.append(physical(dict(path=path,bytes=Path(path).lstat().st_size,sha256=expected)))
    need(mapped,'complete current executable runtime map required')
    return dict(module_origins=result,mapped_executable_files=sorted(mapped,key=lambda row:row['path']),python_surface=surface,frozen_builtin_and_OS_loader_TCB=True)

def settled(policy):
    lane=strict(bounded(RAW/'lane.json'))['socket_lane'];need(lane['lease_generation']==639 and lane['exit_code']==1 and lane.get('ended_utc'),'settled refused G639 required')
    old=strict(bounded(RAW/'component/result.json'));need(old['accepted'] is False and old['error']=={'type':'Refused','message':'duplicate compiler JSON key'} and old['after_input_errors']==[],'original V10 exact refusal changed')
    observer=strict(bounded(OBSERVER/'lane.json'))['socket_lane'];need(observer['lease_generation']==625 and observer['exit_code']==1 and observer.get('ended_utc'),'settled refused G625 required')
    envelope=strict(bounded(OBSERVER/'envelope-result.json'));inner=strict(bounded(OBSERVER/'observer/unit-observation-result.json'))
    need(envelope['observation_complete'] is False and envelope['after_input_errors']==[] and inner['observation_complete'] is False and inner['error']['type']=='Refused'
        and inner['compiler_native_solver_executed'] is False and inner['public_admission'] is False,'original G625 ABI observer refusal changed')
    memory=strict(bounded(MEMORY/'lane.json'))['socket_lane'];need(memory['lease_generation']==642 and memory['exit_code']==0 and memory.get('ended_utc'),'settled success-only G642 observation required')
    result=strict(bounded(MEMORY/'component/result.json'));need(result['accepted'] is True and result['compiler_observation_complete'] is True and result['error'] is None and result['after_input_errors']==[]
        and result['ABI_interpreted'] is False and result['source_call_admitted'] is False and result['native_or_solver_executed'] is False and result['public_proof'] is False,'G642 must remain observation-only')
    for root,code in ((RAW,1),(OBSERVER,1),(MEMORY,0)):
        for name in ('resources.json','outer-resources.json'):
            row=strict(bounded(root/name));need(row['exit_code']==code and row['timed_out'] is False and row['out_of_memory'] is False,'original settled guard differs')
        need(strict(bounded(root/'source-after.json'))=={'commit':COMMIT,'source_unchanged':True,'tracked_changes':''},'original source-after boundary differs')
    return dict(G639=dict(ended_utc=lane['ended_utc'],error=old['error']),G625=dict(ended_utc=observer['ended_utc'],private_error=inner['error']),G642=dict(ended_utc=memory['ended_utc'],ABI_interpreted=False,source_call_admitted=False))

def leases():
    rows={p.name:strict(bounded(p)) for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
    need(len(rows)==3 and all(row['state']=='released' for row in rows.values()),'fresh released socket and legacy leases required');return rows

def finite_scan():
    rounds=[]
    for _ in range(3):
        deadline();snapshot=scan();rounds.append(snapshot)
        if snapshot['vanished_process_or_descriptor_observations']==0:break
    need(not snapshot['selected_original_readers'] and not snapshot['unreadable_own_processes'] and snapshot['vanished_process_or_descriptor_observations']==0,'finite selected-original reader scan refused')
    return rounds

def replay(raw,probe,helper,legacy,api,family):
    # These are retained filtered ABI roots only. Their IDs are never joined to caller IDs.
    original_error=None
    try:legacy.observed_abi(raw,probe_path=Path(probe),api=api)
    except legacy.Refused as error:
        cause=error.__cause__
        need(str(error)=='malformed compiler JSON stream' and isinstance(cause,legacy.Refused) and str(cause)=='duplicate compiler JSON key','exact unchanged legacy ABI refusal differs')
        original_error=dict(type=type(error).__name__,message=str(error),cause=dict(type=type(cause).__name__,message=str(cause)))
    need(original_error is not None,'selected original strict ABI unexpectedly passed')
    derived,transport=helper.normalize_abi(raw)
    need(transport['selected_family']==family and transport['root_count']==29 and transport['role_renames']==4 and transport['source_ABI_or_public_admission'] is False,'complete closed-family ABI eligibility differs')
    observed=legacy.observed_abi(derived,probe_path=Path(probe),api=api)
    need(observed['root_count']==29 and observed['raw_probe_sha256']==digest(derived) and observed['public_admission'] is False,'unchanged complete ABI reader result differs')
    return dict(family=family,original_strict_refusal=original_error,original=dict(bytes=len(raw),sha256=digest(raw)),derived=dict(bytes=len(derived),sha256=digest(derived)),
        transport=transport,ABI_observation=observed,original_probe_path=probe,retained_metadata_interpretation_only=True,fresh_compiler_ABI_theorem=False,source_call_or_public_admission=False)

CONTROL_ROWS=[{'bytes': 7892, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1/control/abi_role_transport_v1.py', 'sha256': 'ea2e7e26ae154ccb9bd40204f75571ddca8fe50591a862d36abb140ec0893f8e'}, {'bytes': 15063, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1/control/compiler_unit_adapter_v3.py', 'sha256': '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'}, {'bytes': 34803, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1/control/whole_interface_v4.py', 'sha256': '217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8'}, {'bytes': 27967, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1/control/role_normalized_gzip_v2.py', 'sha256': '6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941'}, {'bytes': 7959, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1/control/strict_minify_v2.py', 'sha256': 'b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897'}, {'bytes': 18385, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1/control/closed_python_surface.py', 'sha256': '748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af'}, {'bytes': 438152, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1/control/policy.json', 'sha256': '3f20967eaeaa7a3469ef4a4b249c2ce2161ae0ec9a9eda41be80c6d950919ad4'}, {'bytes': 24950, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1/control/replay_entry_v1.py', 'sha256': '7a2b70e9c4883749b834f7598050420223bdc273548d68ea55eb88305edc31db'}]

def postflight():
    global TRANSPORT,READS
    READS={}
    policy_raw=bounded(ROOT/'control/policy.json');need(digest(policy_raw)==POLICY_SHA,'exact staged policy differs')
    policy=strict(policy_raw)
    for row in CONTROL_ROWS:physical(row)
    need({p.name for p in(ROOT/'control').iterdir()}==set(policy['control_membership']),'outer staged membership differs')
    for path,row in policy['known'].items():physical(dict(path=path,**row))
    git=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(SOURCE)]
    head=subprocess.check_output(git+['rev-parse','HEAD'],timeout=10).decode().strip()
    dirty=subprocess.check_output(git+['status','--porcelain','--untracked-files=all'],timeout=10)
    need(head==COMMIT and dirty==b'','outer exact clean original source differs')
    TRANSPORT=transport_identity();scans=finite_scan();current_leases=leases();originals=settled(policy)
    for root in(RAW,MEMORY):
        observation=strict(bounded(root/'component/compiler-observation.json'))
        for row in observation['inputs']:physical(row)
        for group in observation['groups']:
            for row in group['dependencies']:physical(row)
    sys.addaudithook(readonly)
    helper,legacy,api,origins,closed=checked_modules(policy)
    runtime=runtime_identity(policy,closed)
    for row in list(READS.values()):physical(row)
    need(settled(policy)==originals,'original settled outcome changed')
    later_leases=leases();later_scans=finite_scan()
    result=dict(schema='ABI-replay-refusal-outer-postflight-1',original_outcomes_unchanged=True,source_commit=head,source_clean=True,
        staged_controls=CONTROL_ROWS,source_raw_runtime_readset_count=len(READS),readset_sha256=digest(canonical(READS)),
        current_runtime_sha256=digest(canonical(runtime)),mapped_runtime_files=len(runtime['mapped_executable_files']),
        finite_before=scans,finite_after=later_scans,leases_before=current_leases,leases_after=later_leases,
        original_settlements=originals,postflight_only_no_ABI_replay=True,compiler_native_solver_executed=False,
        elapsed_seconds=time.monotonic()-started)
    encoded=canonical(result)+b'\n';need(len(encoded)<=65536,'outer metadata cap');deadline();sys.stdout.write(encoded.decode());sys.stdout.flush();deadline()
    return 0
if __name__=='__main__':raise SystemExit(postflight())
