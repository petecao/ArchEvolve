"""Source-only assembly of root-required finite read-only preflight, no SSH."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;POC=HERE.parent.parents[1]
settled=json.loads((POC/'evidence/t28-capture-v10-root-settled-observation-20261016.json').read_bytes())['runs']['capture-v10']
script='''import resource
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
import hashlib,json,os,stat,time
from pathlib import Path
raw=Path(RAW)
expected=EXPECTED
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
   matched.append({'pid':int(item.name),'self_ancestry':int(item.name) in ancestors,'original_raw':RAW.encode() in command,'argv0':command.split(b'\\x00',1)[0].decode(errors='replace')[:256],'argv_sha256':hashlib.sha256(command).hexdigest()})
 except FileNotFoundError:races.append(int(item.name))
 except PermissionError:denied.append(int(item.name))
need(len(matched)<=32 and len(races)<=128 and len(denied)<=128,'compact scoped census limit')
need(not any(row['original_raw'] and not row['self_ancestry'] for row in matched),'original capture process still active')
print(json.dumps({'schema':'duplicate-diagnostic-preflight-1','raw':RAW,'pins':actual,'original_metadata':metadata,'processes_scanned':scanned,'selected_processes':matched,'process_exit_races':races,'process_permission_errors':denied,'all_host_empty_required':False,'artifact_writes':False,'compiler_or_diagnostic_executed':False,'wall_seconds':time.monotonic()-started},sort_keys=True))
'''
expected=settled['pins'].copy();expected['component/caller.ast.json.gz']={'bytes':39192152,'sha256':'1e01a023699d56da8054533db08de4370e4cd9425b414d1bb772a0efaca3891b'}
expected['control/linux_compiler_capture_policy_v10.json']={'bytes':666177,'sha256':'8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517'}
script=script.replace('raw=Path(RAW)','RAW='+repr(settled['raw_root'])+'\nraw=Path(RAW)').replace('expected=EXPECTED','expected='+repr(expected))
(HERE/'preflight_source_v1.py').write_text(script)
print('authored only')
