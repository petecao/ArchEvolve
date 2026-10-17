import os,json,hashlib,stat,subprocess,signal,time
from pathlib import Path
signal.alarm(30)
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10')
SOURCE=Path('/data1/yanruj/probata-resume-20261016-2baf722f')
SELECTED=RAW/'control/source_call_fixture_v2.cpp'
EXPECTED='3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'
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
if lane['lease_generation']!=639 or lane['exit_code']!=1 or not lane.get('ended_utc'):raise ValueError('original refused G639 is not settled')
if any(r['exit_code']!=1 or r['timed_out']or r['out_of_memory']for r in resources):raise ValueError('original refused whole guard differs')
git=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(SOURCE)]
head=subprocess.check_output(git+['rev-parse','HEAD'],timeout=10).decode().strip()
dirty=subprocess.check_output(git+['status','--porcelain','--untracked-files=all'],timeout=10)
if head!='2baf722fdaa6cba24b859eae3172a6f597417d72'or dirty:raise ValueError('original source is not exact clean')
selected=read(SELECTED)
if hashlib.sha256(selected).hexdigest()!=EXPECTED:raise ValueError('selected original fixture differs')
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
needles=(str(RAW),str(SOURCE),'/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2','/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v2','/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v3','/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v5')
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
result={'classification':'SCOPED_ORIGINAL_G639_AND_NORMALIZED_TRANSPORT_OBSERVER_PREFLIGHT_WITH_EXACT_OS_PAM_SSH_TCB','original_generation':639,'original_ended_utc':lane['ended_utc'],'source_commit':head,'source_clean':not dirty,'selected_source_fixture_sha256':EXPECTED,'scans':rounds,'scoped_preflight_pass':not snapshot['selected_original_readers']and not snapshot['unreadable_own_processes']and snapshot['vanished_process_or_descriptor_observations']==0,'elapsed_seconds':time.monotonic()-started,'scope':'Fresh finite own-UID cmdline/environment/cwd/exe/fd original raw/source scan; exact root-approved systemd/PAM and current query SSH-parent/UID/birth/argv/root ancestry exceptions only. Any other unreadable process refuses; disappearing processes require a fresh full scan. Unrelated workloads remain outside this selected-source/raw claim. No universal kernel/helper descriptor visibility claim.'}
OUTPUT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v5')
if os.path.lexists(OUTPUT):raise ValueError('fresh observer output already exists')
leases={p.name:json.loads(read(p)) for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
if len(leases)!=3 or any(row['state']!='released' for row in leases.values()):raise ValueError('fresh released socket and legacy leases required')
import shutil
free={p:shutil.disk_usage(p).free for p in ('/data','/data1')}
if free['/data']<24*1024**3 or free['/data1']<10*1024**3:raise ValueError('unchanged V9 raw24GiB/source10GiB preflight floors required')
known={'/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/abi-ast.stderr': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/abi-preprocess.stderr': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/abi-preprocess.stdout': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/abi.ast.json': {'bytes': 127394, 'sha256': '0416fecb76bfec1cd375b8d0940de7b1306e9d9b3d591fd0683f544c080ddf15'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/caller-ast.stderr': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/caller-preprocess.stderr': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/caller-preprocess.stdout': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/caller.ast.gzip.json': {'bytes': 541, 'sha256': 'adde1b71f5019cebbb78c525d3b056b3a5badfb44e7f3a9a2df83a944859f5d3'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/caller.ast.json.gz': {'bytes': 39192152, 'sha256': '1e01a023699d56da8054533db08de4370e4cd9425b414d1bb772a0efaca3891b'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/commands.json': {'bytes': 6835, 'sha256': '7930be54f3cbbd77515b0dc8aec5b3511b959a6ba8f7d09e7e775127109365dc'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/result.json': {'bytes': 478, 'sha256': '404a0c416e893e9827fe313932f1fbec73652150b02bffb57f595af373310064'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/closed_python_surface.py': {'bytes': 18385, 'sha256': '748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/compiler_abi_probe_v1.cpp': {'bytes': 1588, 'sha256': 'c0f4f37ba62992b3de117f6117b134ad0ba663484c172ffa98081952f769bf34'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/compiler_unit_adapter_v4.py': {'bytes': 17211, 'sha256': '541c6af68717c5fba4968f23f123fdf51e79edd9a3dff501ff7fa025fc38f9b5'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/linux_compiler_capture_policy_v10.json': {'bytes': 666177, 'sha256': '8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/linux_compiler_capture_v10.py': {'bytes': 30011, 'sha256': '095eee7198167f5e89ae3a64deb2c42e8097951d957a91de0a7c8fd6efb60810'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/linux_native86_entry_v4.py': {'bytes': 23441, 'sha256': '9f63dbe826ca70f2ceacd37b56753a5f212811a5a377c7baed59da4de60b7721'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/lossless_gzip_v2.py': {'bytes': 6812, 'sha256': 'aae4a423216fcdca6b16f9eba370ec4c83615ed61ae79dd4b3d09e3bed1702ef'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/m5ops.h': {'bytes': 133, 'sha256': '4caae6752583fd058e911da16305fe5bebec0fa08d3242242af85494b2b90d7a'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/python_role_observer_v2.py': {'bytes': 2709, 'sha256': '9b100cbe2fdef3e7d429ccdf05d6489d44855a84328e2dd8532eb547beeaf43b'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/python_startup_roles_v2.py': {'bytes': 9610, 'sha256': '5e9d2e6dfa2aaa7999f4670a979d3cc32736b852a612f77d4e2f7c71bc229618'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/source_call_fixture_v2.cpp': {'bytes': 4524, 'sha256': '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/strict_minify_v2.py': {'bytes': 7959, 'sha256': 'b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/t28-linux-runtime-observer-v2-actual-20261016.json': {'bytes': 116503, 'sha256': '092397608fe3a08c42d85e9c8e121ed139f0d94e345a12ae3aaa57ad6e93a5f0'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/t28-selected-python-zlib-origin-observation-20261016.json': {'bytes': 1798, 'sha256': 'bc53f66a5c159b43af8b3fbc69a0ec367c39197589e57fd8af505e5730ae4e3d'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/whole_interface_v4.py': {'bytes': 34803, 'sha256': '217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/lane.json': {'bytes': 817, 'sha256': '5280fbcdb658f85c4d08f9322affe8248c04ea5cb10f70ef863025921ddc68ba'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/launch.json': {'bytes': 1596, 'sha256': 'd236c13c7d09fb8f7b986e274ab53c04791878892ac1dd164ac6ab5b2cefccf0'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/outer-resources.json': {'bytes': 174, 'sha256': '38e5ee1d89c8776abab52f82fbf18d420329b814cca8103469c39526bfe5cb5b'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/resources.json': {'bytes': 165, 'sha256': '8d87632e1c8d1e584bf9f4fb255be0499e09fac98c01ba021500708e2b29e884'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/source-after.json': {'bytes': 112, 'sha256': 'a185a8f90eeed849768421e0c786f76c8ae4c1573e2287ab6114d1098c7be818'}, '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project/apps/dx100/benchmarks/API/MAA.hpp': {'bytes': 1323, 'sha256': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd'}, '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project/apps/dx100/benchmarks/API/MAA_gem5.hpp': {'bytes': 27473, 'sha256': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174'}, '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project/tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json': {'bytes': 5481, 'sha256': 'd48a3971f2e9421e736d72ff160074f22e9cbbb7c9c756ef52457a5c4314b3b6'}, '/usr/bin/python3.12': {'bytes': 8020928, 'sha256': 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'}, '/usr/lib/x86_64-linux-gnu/libz.so.1.3': {'bytes': 113000, 'sha256': '86200da370f20476a2507e9097a789b5ef97269b4ca8d5e164ad82dab9d99892'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/capture-runtime-after.json': {'bytes': 9580, 'sha256': '9b80ab96d17393608722d248f22f41892ee1ce45bee14a1901c131afd812ed2c'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/capture-runtime-before.json': {'bytes': 9035, 'sha256': '9bf4dc41f2583017d5b5a8f1c7c983f8df9f4a0b3753868a132ba5930920acf9'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/capture-zlib-after.json': {'bytes': 628, 'sha256': '1452c916ee289ffbc21b097d5d191d93ac04a6caa8f40d4ffe13070c829ad2f3'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/capture-zlib-before.json': {'bytes': 628, 'sha256': '1452c916ee289ffbc21b097d5d191d93ac04a6caa8f40d4ffe13070c829ad2f3'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/compiler-observation.json': {'bytes': 408741, 'sha256': '0a85c7c097619c0eb80f11bf77a3f37725d17e16145fd99b0db8d9d5aaa55a13'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/component/caller.normalized.json.gz': {'bytes': 12787585, 'sha256': '4156be12cc79326a4d7559f3e801b9f41ba9d2e01478ea6040c97fb6588a142b'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/component/inputs-after.json': {'bytes': 7337, 'sha256': '1f66e91edc350f3c64acff86136eac5ca15157ddd6435c4fef8c85bca934f14e'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/component/inputs-before.json': {'bytes': 7337, 'sha256': '1f66e91edc350f3c64acff86136eac5ca15157ddd6435c4fef8c85bca934f14e'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/component/inverse.json': {'bytes': 609, 'sha256': '23915cad826a4b5cfe6e735f459bb1d7c7a23acdddcae344ff229681a43c7f75'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/component/rename-manifest.jsonl': {'bytes': 31776, 'sha256': 'f394231d47fa1b1fa9ce6fe7d0854cb17403f478adc1d1a4fe351d4aee97c4b1'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/component/transport.json': {'bytes': 8010, 'sha256': '25546fb9eaa2fdf59e34813bef2ff28a5abca5abfbbb0d61c9cd84f18ca8d1ad'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/control/census.json': {'bytes': 9181, 'sha256': 'df800e08c89abd76ef0ea7e713af9fd52315ae873accc8ea54ab5a760fa8a41b'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/control/controller.py': {'bytes': 82330, 'sha256': 'e37e893b31b9b0be5f1cd2a5953998393d6040ed2c0c2d45434012727673aa54'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/control/normalizer.py': {'bytes': 27967, 'sha256': '6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/control/policy.json': {'bytes': 14295, 'sha256': 'c9d01e061d2a8263de775e18259a4d6961d6ce8ca8bfdfdbe5ad71473b496d39'}, '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2/result.json': {'bytes': 10621, 'sha256': '387215380fc35422ec92ff0d751421a8d7e29a05555b3efa6c1169d9966f16a1'}}

for name,row in known.items():
 path=Path(name);before=path.lstat()
 if path.resolve(strict=True)!=path or not stat.S_ISREG(before.st_mode) or before.st_size!=row['bytes']:raise ValueError('known input physical shape differs')
 with path.open('rb') as handle:sha=hashlib.file_digest(handle,'sha256').hexdigest()
 after=path.lstat();fields=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
 if any(getattr(before,k)!=getattr(after,k) for k in fields) or sha!=row['sha256']:raise ValueError('known input identity changed')
original=json.loads(read(RAW/'component/result.json'))
if original['accepted'] is not False or original['error']!={'type':'Refused','message':'duplicate compiler JSON key'} or original['after_input_errors']!=[]:raise ValueError('original exact refusal changed')
commands=json.loads(read(RAW/'component/commands.json'))
if len(commands)!=4 or any(row['returncode']!=0 for row in commands):raise ValueError('original complete four compiler phases differ')
result.update(original_refusal=original['error'],known_input_count=len(known),known_input_map_sha256=hashlib.sha256(json.dumps(known,sort_keys=True,separators=(',',':')).encode()).hexdigest(),leases=leases,fresh_output_absent=True,free_bytes=free)
encoded=json.dumps(result,sort_keys=True).encode()
if len(encoded)>65536:raise ValueError('preflight metadata cap')
print(encoded.decode())
raise SystemExit(0 if result['scoped_preflight_pass']else 1)
