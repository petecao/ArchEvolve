import os,json,hashlib,stat,subprocess,signal,time,shutil
from pathlib import Path
signal.alarm(30)
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-abb598a4-t25-owned-swap-header3-public-v1')
SOURCE=Path('/data1/yanruj/probata-resume-20261016-abb598a4')
started=time.monotonic()
def read(path,cap=1048576):
 st=path.lstat()
 if not stat.S_ISREG(st.st_mode) or st.st_size>cap:raise ValueError('bounded regular metadata required')
 with path.open('rb')as f:data=f.read(cap+1)
 if len(data)>cap:raise ValueError('metadata cap')
 return data
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
 timeout=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','35s','/usr/bin/python3','-I','-B','-']
 if rows[1]['argv']!=timeout or rows[1]['comm']!='timeout':raise ValueError('exact current outer timeout required')
 if rows[2]['argv']!=['sshd: yanruj@notty','','']or rows[2]['comm']!='sshd'or rows[2]['uids']!=[str(os.getuid())]*4:raise ValueError('exact current same-UID SSH transport required')
 if rows[3]['argv']!=['sshd: yanruj [priv]','']or rows[3]['comm']!='sshd'or rows[3]['uids']!=['0']*4:raise ValueError('exact root privileged SSH parent required')
 if rows[4]['comm']!='sshd'or rows[4]['uids']!=['0']*4 or len(rows[4]['argv'])!=1 or not rows[4]['argv'][0].startswith('sshd: /usr/sbin/sshd -D [listener] '):raise ValueError('root SSH listener ancestry required')
 binary=Path('/usr/sbin/sshd');st=binary.stat()
 if st.st_uid!=0 or not stat.S_ISREG(st.st_mode):raise ValueError('root-owned physical SSH daemon binary required')
 return {'chain':rows,'daemon_binary':{'path':str(binary.resolve()),'bytes':st.st_size,'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()},'allowed_unreadable_current_transport_pid':rows[2]['pid']}
TRANSPORT=transport_identity()
needles=(str(RAW),str(SOURCE))
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
rounds=[]
for attempt in range(3):
 snapshot=scan();rounds.append(snapshot)
 if snapshot['vanished_process_or_descriptor_observations']==0:break
result={'classification':'HEADER3_SETTLED_TARGET_POSTFLIGHT_WITH_EXACT_INHERITED_OS_PAM_SSH_TCB','source_commit':'abb598a485cca67c77798e690382b44beb48c9e3','scans':rounds,'scoped_preflight_pass':not snapshot['selected_original_readers']and not snapshot['unreadable_own_processes']and snapshot['vanished_process_or_descriptor_observations']==0,'scope':'Settled finite own-UID cmdline/environment/cwd/exe/fd scan for only this fresh source/raw target. Exact inherited PAM and current SSH birth/parent/UID/argv identity checks; no arbitrary unreadable process exception. No universal OS visibility claim.'}
for path in (RAW,SOURCE):
 if path.resolve(strict=True)!=path or not stat.S_ISDIR(path.lstat().st_mode):raise ValueError('settled Header3 source and raw must be canonical physical directories')
lane= json.loads(read(RAW/'lane.json'))['socket_lane']
if lane['node']!=1 or lane['lease_generation']!=int('644') or not lane.get('ended_utc'):raise ValueError('exact Header3 node1 generation must be settled')
settled={name:json.loads(read(RAW/name))for name in ('resources.json','outer-resources.json','source-after.json')}
leases={p.name:json.loads(read(p))for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
if len(leases)!=3 or leases['mbit10-evaluation-node1.meta.json']['state']!='released' or leases['mbit10-evaluation.meta.json']['state']!='released':raise ValueError('fresh target node1 and legacy leases must be released')
free={p:shutil.disk_usage(p).free for p in ('/data','/data1')}
if free['/data']<24*1024**3 or free['/data1']<10*1024**3+6223086+1073741824:raise ValueError('unchanged raw24GiB/source10GiB plus exact projection and1GiB headroom required')
memory={}
for line in Path('/proc/meminfo').read_text().splitlines():
 key,_,value=line.partition(':')
 if key in ('MemTotal','MemAvailable'):memory[key+'_bytes']=int(value.split()[0])*1024
if memory['MemAvailable_bytes']<9*1024**3:raise ValueError('at least9GiB available for one8GiB guarded worker required')
env={'HOME':'/nonexistent','PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
def git(root,*args):return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(root),*args],env=env,timeout=10).decode().strip()
control=Path('/data1/yanruj/Memacc-evolveswdb-lane')
script=control/'AgenticRefiner/scripts/host/socket_lane.sh'
hostlock=control/'AgenticRefiner/scripts/host/hostlock.sh'
wrapper_commit=git(control,'rev-parse','HEAD')
if wrapper_commit!='76cca359136794afa5ede975cfac8293cfa2ab9a':raise ValueError('exact observed lane checkout commit differs')
wrapper_fetched_commit=git(control,'rev-parse','FETCH_HEAD')
if wrapper_fetched_commit!='41f22f0ba765adcd4f4188aca91009ea0fe5a22b':raise ValueError('exact reviewed fetched lane commit differs')
def wrapper_blob(revision,relative):return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(control),'show',revision+':'+relative],env=env,timeout=10)
for wrapper_path,expected_hash in ((script,'00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'),(hostlock,'50745f827bac2a3db4fc56fdedc95f6fb57fb4b39cf9b269796c77c0274dc996')):
 physical=read(wrapper_path)
 if hashlib.sha256(physical).hexdigest()!=expected_hash:raise ValueError('exact reviewed lane or hostlock script differs')
 relative=str(wrapper_path.relative_to(control))
 if wrapper_blob('HEAD',relative)!=physical or wrapper_blob('FETCH_HEAD',relative)!=physical:raise ValueError('physical lane/hostlock must match both exact Git trees')
if git(control,'status','--porcelain','--','AgenticRefiner/scripts/host/socket_lane.sh','AgenticRefiner/scripts/host/hostlock.sh'):raise ValueError('selected reviewed wrapper checkout must be clean')
old_sources={}
for suffix in ('1433b8f5','2baf722f','d7f685c6','36266e10','032e1851','a102e275'):
 path=Path('/data1/yanruj/probata-resume-20261016-'+suffix)
 if path.resolve(strict=True)!=path or not stat.S_ISDIR(path.lstat().st_mode):raise ValueError('required retained old source must remain a physical directory')
 old_sources[str(path)]={'commit':git(path,'rev-parse','HEAD'),'branch':git(path,'rev-parse','--abbrev-ref','HEAD')}
primary=Path('/data1/yanruj/ArchEvolve')
if git(SOURCE,'rev-parse','HEAD')!='abb598a485cca67c77798e690382b44beb48c9e3' or git(SOURCE,'rev-parse','--abbrev-ref','HEAD')!='HEAD' or git(SOURCE,'status','--porcelain','--untracked-files=all','--ignored'):raise ValueError('settled exact source must remain detached and clean')
result.update(lane=lane,settled_guards=settled,leases=leases,free_bytes=free,memory=memory,load_average=Path('/proc/loadavg').read_text().strip(),primary_branch=git(primary,'rev-parse','--abbrev-ref','HEAD'),primary_commit=git(primary,'rev-parse','HEAD'),retained_old_sources=old_sources,wrapper_commit=wrapper_commit,settled_source_and_raw_present=True,elapsed_seconds=time.monotonic()-started)
encoded=json.dumps(result,sort_keys=True).encode()
if len(encoded)>65536:raise ValueError('preflight metadata cap')
print(encoded.decode())
raise SystemExit(0 if result['scoped_preflight_pass']else 1)
