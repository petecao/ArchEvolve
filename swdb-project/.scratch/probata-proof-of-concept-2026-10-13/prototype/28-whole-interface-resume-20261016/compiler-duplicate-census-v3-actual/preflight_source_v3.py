import resource
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
import hashlib,json,os,stat,time
from pathlib import Path
RAW='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10'
raw=Path(RAW)
expected={'component/caller.ast.gzip.json': {'bytes': 541, 'sha256': 'adde1b71f5019cebbb78c525d3b056b3a5badfb44e7f3a9a2df83a944859f5d3'}, 'component/commands.json': {'bytes': 6835, 'sha256': '7930be54f3cbbd77515b0dc8aec5b3511b959a6ba8f7d09e7e775127109365dc'}, 'component/result.json': {'bytes': 478, 'sha256': '404a0c416e893e9827fe313932f1fbec73652150b02bffb57f595af373310064'}, 'lane.json': {'bytes': 817, 'sha256': '5280fbcdb658f85c4d08f9322affe8248c04ea5cb10f70ef863025921ddc68ba'}, 'launch.json': {'bytes': 1596, 'sha256': 'd236c13c7d09fb8f7b986e274ab53c04791878892ac1dd164ac6ab5b2cefccf0'}, 'outer-resources.json': {'bytes': 174, 'sha256': '38e5ee1d89c8776abab52f82fbf18d420329b814cca8103469c39526bfe5cb5b'}, 'resources.json': {'bytes': 165, 'sha256': '8d87632e1c8d1e584bf9f4fb255be0499e09fac98c01ba021500708e2b29e884'}, 'source-after.json': {'bytes': 112, 'sha256': 'a185a8f90eeed849768421e0c786f76c8ae4c1573e2287ab6114d1098c7be818'}, 'component/caller.ast.json.gz': {'bytes': 39192152, 'sha256': '1e01a023699d56da8054533db08de4370e4cd9425b414d1bb772a0efaca3891b'}, 'control/linux_compiler_capture_policy_v10.json': {'bytes': 666177, 'sha256': '8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517'}}
started=time.monotonic()
def need(ok,message):
 if not ok:raise ValueError(message)
def pin(path):
 before=path.lstat();need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode),'canonical preflight input required')
 with path.open('rb') as stream:value=hashlib.file_digest(stream,'sha256').hexdigest()
 after=path.lstat();fields=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
 need(tuple(getattr(before,k) for k in fields)==tuple(getattr(after,k) for k in fields),'preflight input changed')
 return {'bytes':before.st_size,'sha256':value}
actual={}
for relative,row in expected.items():
 actual[relative]=pin(raw/relative);need(actual[relative]==row,'original G639 metadata/input changed: '+relative)
metadata={name:json.loads((raw/name).read_bytes()) for name in ('lane.json','source-after.json','component/result.json','outer-resources.json')}
need(metadata['lane.json']['socket_lane']['lease_generation']==639 and metadata['lane.json']['socket_lane']['node']==1 and metadata['lane.json']['socket_lane']['exit_code']==1,'original G639 settlement differs')
need(metadata['source-after.json']=={'commit':'2baf722fdaa6cba24b859eae3172a6f597417d72','source_unchanged':True,'tracked_changes':''},'source-after differs')
ancestors=set();pid=os.getpid()
for _ in range(64):
 if pid<=1:break
 ancestors.add(pid);pid=int(Path('/proc/'+str(pid)+'/stat').read_text().rsplit(') ',1)[1].split()[1])
need(pid<=1,'bounded passive ancestry required')
matched=[];races=[];denied=[];scanned=0
for item in sorted(Path('/proc').iterdir()):
 if not item.name.isdigit():continue
 scanned+=1;need(scanned<=20000 and time.monotonic()-started<20,'finite scoped process census bound')
 try:
  command=(item/'cmdline').read_bytes()
  if RAW.encode() in command or b'/data1/yanruj/probata-resume-20261016-2baf722f' in command:
   matched.append({'pid':int(item.name),'self_ancestry':int(item.name) in ancestors,'original_raw':RAW.encode() in command,'argv0':command.split(b'\x00',1)[0].decode(errors='replace')[:256],'argv_sha256':hashlib.sha256(command).hexdigest()})
 except FileNotFoundError:races.append(int(item.name))
 except PermissionError:denied.append(int(item.name))
need(len(matched)<=32 and len(races)<=128 and len(denied)<=128,'compact scoped census limit')
need(not any(row['original_raw'] and not row['self_ancestry'] for row in matched),'original capture process still active')
observation={'schema':'duplicate-diagnostic-preflight-1','raw':RAW,'pins':actual,'original_metadata':metadata,'processes_scanned':scanned,'selected_processes':matched,'process_exit_races':races,'process_permission_errors':denied,'all_host_empty_required':False,'artifact_writes':False,'compiler_or_diagnostic_executed':False,'wall_seconds':time.monotonic()-started}

policy=json.loads((raw/'control/linux_compiler_capture_policy_v10.json').read_bytes())
extra={}
for row in policy['source_inputs']:
 path=Path(policy['source_project'])/row['relative'];actual=pin(path)
 need(actual=={k:row[k] for k in ('bytes','sha256')},'current selected source/header input differs')
 extra[str(path)]=actual
for name,row in policy['controller_files'].items():
 path=raw/'control'/name;actual=pin(path);need(actual==row,'current control/input differs');extra[str(path)]=actual
runtime=[policy['zlib_binding']['physical_interpreter'],*policy['zlib_binding']['mapped_compression_objects']]
for row in runtime:
 path=Path(row['path']);actual=pin(path);need(actual=={k:row[k] for k in ('bytes','sha256')},'selected passive decoder runtime differs');extra[str(path)]=actual
observation['current_physical_source_control_decoder_pins']=extra
observation['runtime_scope']='exact physical selected interpreter and mapped compression object; full bind_zlib startup is also required by census'
print(json.dumps(observation,sort_keys=True))
