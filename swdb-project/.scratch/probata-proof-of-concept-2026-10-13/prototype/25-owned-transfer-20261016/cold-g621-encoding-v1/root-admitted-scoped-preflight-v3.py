import os,json,hashlib,stat,subprocess,signal,time
from pathlib import Path
signal.alarm(30)
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-d7f685c6-owned-transfer10-public-v2')
SOURCE=Path('/data1/yanruj/probata-resume-20261016-d7f685c6')
SELECTED=SOURCE/'swdb-project/swdb/vector_owned_state.mlw'
EXPECTED='a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6'
started=time.monotonic()
def read(path,cap=1048576):
 st=path.lstat()
 if not stat.S_ISREG(st.st_mode) or st.st_size>cap:raise ValueError('bounded regular metadata required')
 with path.open('rb')as f:data=f.read(cap+1)
 if len(data)>cap:raise ValueError('metadata cap')
 return data
for path in (RAW,SOURCE):
 if not stat.S_ISDIR(path.lstat().st_mode)or path.resolve(strict=True)!=path:raise ValueError('physical selected root required')
lane=json.loads(read(RAW/'lane.json'))['socket_lane']
resources=[json.loads(read(RAW/name))for name in ('resources.json','outer-resources.json')]
if lane['lease_generation']!=621 or lane['exit_code']!=0 or not lane.get('ended_utc'):raise ValueError('original G621 is not settled')
if any(r['exit_code'] or r['timed_out']or r['out_of_memory']for r in resources):raise ValueError('original whole guard differs')
git=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(SOURCE)]
head=subprocess.check_output(git+['rev-parse','HEAD'],timeout=10).decode().strip()
dirty=subprocess.check_output(git+['status','--porcelain','--untracked-files=all'],timeout=10)
if head!='d7f685c6fdbd7ff776eb1eaccc40099a2c48dc08'or dirty:raise ValueError('original source is not exact clean')
selected=read(SELECTED)
if hashlib.sha256(selected).hexdigest()!=EXPECTED:raise ValueError('selected original theory differs')
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
   found=[n for n in needles if n.encode()in command]
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
result={'classification':'SCOPED_ORIGINAL_G621_PREFLIGHT_V3_WITH_EXACT_OS_PAM_SSH_TCB','original_generation':621,'original_ended_utc':lane['ended_utc'],'source_commit':head,'source_clean':not dirty,'selected_theory_sha256':EXPECTED,'scans':rounds,'scoped_preflight_pass':not snapshot['selected_original_readers']and not snapshot['unreadable_own_processes']and snapshot['vanished_process_or_descriptor_observations']==0,'elapsed_seconds':time.monotonic()-started,'scope':'Fresh finite own-UID cmdline/cwd/exe/fd original raw/source scan; exact root-approved systemd/PAM and current query SSH-parent/UID/birth/argv/root ancestry exceptions only. Any other unreadable process refuses; disappearing processes require a fresh full scan. Unrelated032e science permitted. No universal kernel/helper descriptor visibility claim.'}
encoded=json.dumps(result,sort_keys=True).encode()
if len(encoded)>65536:raise ValueError('preflight metadata cap')
print(encoded.decode())
raise SystemExit(0 if result['scoped_preflight_pass']else 1)
