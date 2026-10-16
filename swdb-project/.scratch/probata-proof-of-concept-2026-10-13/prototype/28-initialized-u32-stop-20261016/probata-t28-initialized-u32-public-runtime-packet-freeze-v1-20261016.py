"""Pure inert JSON/hash author only; no project imports or tool calls."""
import hashlib,json,sys
from pathlib import Path
def nochild(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork'))or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('pure packet refuses '+event)
sys.addaudithook(nochild)
ROOT=Path('/private/tmp');P='/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12'
def pin(path):
 p=Path(path).resolve()
 with p.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest}
def write(path,value):
 p=ROOT/path;assert not p.exists();p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');return pin(p)
ENTRY=ROOT/'probata-t28-initialized-u32-public-control-entry-v1-20261016.py'
POLICY=ROOT/'probata-t28-initialized-u32-public-runtime-policy-template-v1-20261016.json'
CONTEXT=ROOT/'probata-t28-initialized-u32-public-runtime-template-context-v1-20261016.json'
SOURCE=ROOT/'probata-t28-initialized-u32-route-evidence-v2-97a033a4-20261016.json'
assert pin(ENTRY)['sha256']=='5557ff0afc1ea95946e657286dfeb6fb7a6175eb9ae3de7aed365bcb42d9bc5c'
assert pin(POLICY)['sha256']=='67804e55f69b188983493033ec8180f6c784b181831d0db12919b401bea7e0c0'
assert pin(SOURCE)['sha256']=='59f21010f1f61bc0f231578e9af19859dbb22b9286906599043eaf9a163679e3'
project=ROOT/'probata-resume-t25-pair/swdb-project'
raw=ROOT/'probata-t28-initialized-u32-public-compiler-standin-v1-188a478e-20261016'
entryargv=[P,'-I','-B',str(ENTRY),'--project',str(project),'--output',str(raw/'component'),'--source-policy',str(SOURCE),'--runtime-policy',str(POLICY),'--runtime-sha256',pin(POLICY)['sha256'],'--expected-commit','188a478eaf29089050b70adfbc4a546d20440cb4']
B=ROOT/'probata-mac-compiler-worker-b.py'
C6=ROOT/'probata-resume-t07-private-array/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/counted_verifier.py'
command=write('probata-t28-initialized-u32-public-control-command-v1-188a478e-20261016.json',{
 'status':'INERT ROOT REVIEW ONLY; not independently outer-admitted or launched',
 'cwd':str(project),'entry_argv':entryargv,'guarded_inner_argv':[P,str(B),'--',P,str(C6),'--log',str(raw/'guard.log'),'--cap-gb','8','--timeout','240','--queue-timeout','30','--owner','t28-initialized-public-compiler-standin','--lock','/tmp/claude/swdb-verifier.lock','--',*entryargv],
 'root_creates_fresh_raw_parent':str(raw),'entry_creates_fresh_component':True,
 'mandatory_independent_outer':{'timeout_s':300,'rss_cap_bytes':8*1024**3,'workers':1,'whole_request':True},
 'mandatory_fresh_root_preflight':['complete clean published188a source and tracked consumer closure','all runtime physical pins and selected tree memberships/configuration','fixtures/hooks/selected source and observer inputs','free capacity50GiB plus256MiB, shared B/formal leases and finite process inspections','root outer source/remaining-budget/raw-preservation checks'],
 'actual_formal_acceptance':False,'native_caller_execution':False,'workflow_launched':False})
paths=[ENTRY,POLICY,CONTEXT,SOURCE,B,C6,Path(__file__),ROOT/'probata-t28-initialized-u32-public-control-plan-v1-20261016.md',ROOT/'probata-t28-initialized-u32-public-control-plan-draft-20261016.md',ROOT/'probata-t28-initialized-u32-public-runtime-template-plan-v1-20261016.md',ROOT/'probata-t28-initialized-u32-register-independent-source-review-v3-97a033a4-20261016.md',ROOT/'probata-t28-initialized-u32-register-independent-source-review-v3-97a033a4-20261016.json',ROOT/'probata-root-initialized-u32-compiler-observation-execution-v1-20261016.json',ROOT/'probata-t28-initialized-u32-compiler-observe-provenance-addendum-v1-20261016.md']
for version in [1,2]:
 paths.append(ROOT/f'probata-t28-initialized-runtime-template-build-v{version}-20261016.py')
 for suffix in ['', '.summary.json','.wait.json']:paths.append(ROOT/f'probata-t28-initialized-runtime-template-build-v{version}-20261016.log{suffix}')
packet=write('probata-t28-initialized-u32-public-control-packet-v1-188a478e-20261016.json',{
 'status':'INERT runtime-template and compiler/scripted-persistence proposal; root alone fresh-admits',
 'date':'2026-10-16 ET','source_commit':'188a478eaf29089050b70adfbc4a546d20440cb4','reviewed_runtime_candidate':'97a033a4f171c6c0c4e42726947ee8e8099f0252',
 'command':command,'refs':[pin(path)for path in paths],
 'runtime_flat_pin_count':4489,'runtime_template_complete_LLVM_dynamic_closure':False,
 'existing_template_builder_v1_failed_not_workflow':True,'public_workflow_executed':False,
 'real_compiler_and_OCaml_module_permitted_only_after_root_review':True,'real_formal_or_native_caller_permitted':False,
 'source_body_hardware_or_full_ticket_acceptance':False})
print(json.dumps({'command':command,'packet':packet},sort_keys=True))
