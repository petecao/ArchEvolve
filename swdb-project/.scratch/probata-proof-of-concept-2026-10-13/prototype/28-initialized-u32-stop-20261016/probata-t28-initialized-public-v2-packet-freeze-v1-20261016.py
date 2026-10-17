"""Pure inert V2 packet author; no project import/tool execution."""
import hashlib,json,sys
from pathlib import Path
def nochild(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork'))or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('pure packet refuses '+event)
sys.addaudithook(nochild)
R=Path('/private/tmp');PY='/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12'
def pin(path):
 p=Path(path).resolve()
 with p.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest}
def write(name,value):
 p=R/name;assert not p.exists();p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return pin(p)
source=R/'probata-t28-initialized-u32-public-source-policy-v3-e99d09b1-20261016.json'
entry=R/'probata-t28-initialized-u32-public-control-entry-v2-20261016.py'
runtime=R/'probata-t28-initialized-u32-public-runtime-policy-template-v1-20261016.json'
assert pin(source)['sha256']=='7b1dc8c6eb4f4cf8f57051b0699fa34f744fa379f753fa85e28dc110c4ffb3e3'
assert pin(entry)['sha256']=='3e3077b35aff2c67b7e0ff9d1ea4e1743aadeb0e5ec63f3898702892fb1ddbee'
assert pin(runtime)['sha256']=='67804e55f69b188983493033ec8180f6c784b181831d0db12919b401bea7e0c0'
oldcommand=R/'probata-t28-initialized-u32-public-control-command-v1-188a478e-20261016.json'
command=json.loads(oldcommand.read_text());raw=R/'probata-t28-initialized-u32-public-compiler-standin-v2-e99d09b1-20261016'
oldentry=command['entry_argv'];argv=list(oldentry)
argv[3]=str(entry)
for key,value in {'--output':str(raw/'component'),'--source-policy':str(source),'--expected-commit':'e99d09b1699b32525cd4c44cead21ed2fc6f4917'}.items():argv[argv.index(key)+1]=value
guarded=command['guarded_inner_argv'];guarded[-len(oldentry):]=argv
guarded[guarded.index('--log')+1]=str(raw/'guard.log')
command.update(entry_argv=argv,guarded_inner_argv=guarded,root_creates_fresh_raw_parent=str(raw),
 source_commit='e99d09b1699b32525cd4c44cead21ed2fc6f4917',original_public_V1_FAILED=True,
 mandatory_private_bytecode_prefix=str(raw/'component/source-cache'),status='INERT ROOT REVIEW; publication/fresh admission and execution not implied')
cmd=write('probata-t28-initialized-u32-public-control-command-v2-e99d09b1-20261016.json',command)
refs=[entry,source,runtime,R/'probata-t28-initialized-u32-public-runtime-template-context-v1-20261016.json',R/'probata-t28-initialized-u32-public-control-plan-v2-e99d09b1-20261016.md',oldcommand,R/'probata-t28-initialized-u32-public-control-packet-v1-188a478e-20261016.json',R/'probata-root-initialized-public-execution-v1-20261016.json',R/'probata-t28-initialized-u32-public-control-entry-v1-20261016.py',R/'probata-t28-initialized-u32-route-evidence-v2-97a033a4-20261016.json',R/'probata-t28-initialized-u32-public-runtime-template-plan-v1-20261016.md',Path(__file__)]
for stem in ['probata-t28-initialized-frame-control-v1-20261016','probata-t28-initialized-public-v2-build-v1-20261016','probata-t28-initialized-public-bytecode-control-v1-20261016']:refs.append(R/(stem+'.py'))
for stem in ['probata-t28-initialized-frame-control-red-v1-20261016','probata-t28-initialized-frame-control-green-v1-20261016','probata-t28-initialized-public-v2-build-v1-20261016','probata-t28-initialized-public-bytecode-control-v1-20261016']:
 for suffix in ['.log','.log.summary.json','.log.wait.json']:refs.append(R/(stem+suffix))
refs.append(R/'probata-t28-initialized-public-bytecode-control-v1-20261016/result.json')
for stem in ['probata-t28-initialized-u32-frame-test-independent-source-review-v1-ece76ebc-20261016','probata-t25-copy-prefix-ten-case-independent-source-review-v2-e0e8a435-20261016','probata-t28-initialized-u32-public-control-independent-static-review-v1-188a478e-20261016']:
 for extension in ['md','json']:refs.append(R/(stem+'.'+extension))
packet=write('probata-t28-initialized-u32-public-control-packet-v2-e99d09b1-20261016.json',{
 'date':'2026-10-16 ET','status':'INERT source-policy/test-repair/private-cache successor; root alone fresh-admits',
 'source_commit':'e99d09b1699b32525cd4c44cead21ed2fc6f4917','command':cmd,'refs':[pin(p)for p in refs],
 'original_public_V1_status':'FAILED; immutable failure/result/raw preserved','V2_public_workflow_executed':False,
 'runtime_template_unchanged':True,'actual_formal_native_caller_body_hardware_or_whole_ticket_acceptance':False})
print(json.dumps({'command':cmd,'packet':packet},sort_keys=True))
