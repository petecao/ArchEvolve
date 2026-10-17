"""2026-10-16 ET. Git-only idle-primary synchronization at user stop; no evaluation."""
import os,json,hashlib,stat,subprocess,signal,time,shutil,datetime,sys,fcntl
from pathlib import Path
signal.alarm(30)
EXPECTED='bfc3d5df3278415403a25e3547b838f7f9c991e8'
assert len(EXPECTED)==40 and all(c in '0123456789abcdef' for c in EXPECTED)
REPO=Path('/data1/yanruj/ArchEvolve')
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

TRANSPORT=transport_identity()
needles=(str(REPO),)
rounds=[]
for attempt in range(3):
 snapshot=scan();rounds.append(snapshot)
 if not snapshot['vanished_process_or_descriptor_observations']:break
assert not snapshot['selected_original_readers'] and not snapshot['unreadable_own_processes'] and not snapshot['vanished_process_or_descriptor_observations'],snapshot
leases={p.name:json.loads(p.read_bytes()) for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
assert len(leases)==3 and all(x['state']=='released' for x in leases.values()),leases
locks={}
for name in ['mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1']:
 with (Path('/data1/yanruj/lact-host-lease')/(name+'.lease')).open('rb') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[name]=True;fcntl.flock(f,fcntl.LOCK_UN)
free={p:shutil.disk_usage(p).free for p in ['/data1','/data']}
# Preserve the established10GiB floor plus1GiB fetch headroom; check source growth after fetch.
assert free['/data1']>11*1024**3,free
GIT=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-c','submodule.recurse=false']
def git(root,*args):
 return subprocess.check_output(GIT+['-C',str(root),*args],text=True,timeout=20).strip()
def state(root):
 return {'head':git(root,'rev-parse','HEAD'),'branch':git(root,'branch','--show-current'),'status':git(root,'status','--porcelain=v1','--untracked-files=all')}
protected_roots=sorted({p for pattern in ['probata-reviewed-*','probata-resume-*'] for p in Path('/data1/yanruj').glob(pattern) if (p/'.git').exists()})
protected={str(p):state(p) for p in protected_roots}
before=state(REPO);assert before['branch']=='yanrujhou_main'
assert not git(REPO,'diff','--name-only') and not git(REPO,'diff','--cached','--name-only')
assert git(REPO,'ls-files','--others','--exclude-standard').splitlines()==['swdb-project/records/.retention.lock']
lock=REPO/'swdb-project/records/.retention.lock'
def lock_identity():
 st=lock.lstat();return {'sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),'bytes':st.st_size,'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid}
lock_before=lock_identity()
fetch=git(REPO,'fetch','--no-tags','--recurse-submodules=no','origin','yanrujhou_main')
assert git(REPO,'rev-parse','FETCH_HEAD')==EXPECTED
changed=git(REPO,'diff','--name-only','--no-renames','HEAD',EXPECTED).splitlines()
sizes={line.split('\t',1)[1]:int(line.split('\t',1)[0].split()[3]) for line in git(REPO,'ls-tree','-r','-l',EXPECTED).splitlines() if line.split('\t',1)[0].split()[1]=='blob'}
source_growth_bytes=sum(sizes.get(p,0) for p in changed)
assert source_growth_bytes<256*1024**2
assert shutil.disk_usage('/data1').free>10*1024**3+source_growth_bytes+512*1024**2
assert subprocess.run(GIT+['-C',str(REPO),'merge-base','--is-ancestor','HEAD',EXPECTED],timeout=10).returncode==0
merge=git(REPO,'merge','--no-stat','--ff-only',EXPECTED)
after=state(REPO);assert after==dict(before,head=EXPECTED)
assert lock_before==lock_identity()
protected_after={str(p):state(p) for p in protected_roots};assert protected_after==protected
result={'schema':'probata-pause-primary-git-sync-v1','date_et':'2026-10-16','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected':EXPECTED,'primary_before':before,'primary_after':after,'finite_primary_reader_scans':rounds,'lease_states':{k:v['state'] for k,v in leases.items()},'kernel_locks_available':locks,'free_before':free,'free_after':{p:shutil.disk_usage(p).free for p in ['/data1','/data']},'retention_lock_unchanged':lock_before,'protected_sources_before':protected,'protected_sources_unchanged':True,'protected_source_count':len(protected),'source_growth_bytes':source_growth_bytes,'fetch_stdout':fetch,'merge_stdout':merge,'no_compiler_native_verifier_tests_or_evaluation':True,'raw_evidence_or_immutable_source_modified':False,'scope':'Primary source Git-only ff after finite primary reader scan; this is not the missing G626 raw/source/wrapper-after postflight'}
encoded=json.dumps(result,sort_keys=True)
assert len(encoded.encode())<131072
print(encoded)
