"""Pure author: successor source pins/entry from preserved V1; no tools."""
import ast,copy,hashlib,json,sys
from pathlib import Path
def nochild(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork'))or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('pure V2 author refuses '+event)
sys.addaudithook(nochild)
R=Path('/private/tmp');P=R/'probata-resume-t25-pair/swdb-project'
def pin(path):
 p=Path(path).resolve()
 with p.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest}
def write(path,value):
 path=Path(path);assert not path.exists();path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return pin(path)
old=R/'probata-t28-initialized-u32-route-evidence-v2-97a033a4-20261016.json'
assert pin(old)['sha256']=='59f21010f1f61bc0f231578e9af19859dbb22b9286906599043eaf9a163679e3'
original=json.loads(old.read_text());changed=[];sources=[]
for row in original['source_paths']:
 now=pin(row['path']);sources.append(now)
 if row!=now:changed.append({'old':row,'new':now})
assert len(sources)==13 and len(changed)==1
assert Path(changed[0]['old']['path']).relative_to(P)==Path('tests/test_dx100_initialized_register.py')
assert changed[0]['new']['sha256']=='1c8bb3fb666d8645f8bfc5449a0b760f9ef8fbff9c527eba059805e3e58b5703'
root=R/'probata-root-initialized-public-execution-v1-20261016.json'
assert pin(root)['sha256']=='2d8adc7dd839233329c94fafac326b7c574ac69a37c519f45e7e176ba6bdf139'
refs=[root,R/'probata-t28-initialized-frame-control-v1-20261016.py']
for color in ['red','green']:
 for suffix in ['','.summary.json','.wait.json']:refs.append(R/f'probata-t28-initialized-frame-control-{color}-v1-20261016.log{suffix}')
for extension in ['md','json']:refs.append(R/f'probata-t28-initialized-u32-frame-test-independent-source-review-v1-ece76ebc-20261016.{extension}')
policy_path=R/'probata-t28-initialized-u32-public-source-policy-v3-e99d09b1-20261016.json'
policy=write(policy_path,{'date':'2026-10-16 ET','scope':'13 initialized selected pins only; root separately binds full combined source/consumers',
 'source_candidate':'e99d09b1699b32525cd4c44cead21ed2fc6f4917','source_paths':sources,'original97_source_policy':pin(old),
 'exact_initialized_change_since97':changed,'original_initialized_production_unchanged':True,
 'separate_prefix_production_review':pin(R/'probata-t25-copy-prefix-ten-case-independent-source-review-v2-e0e8a435-20261016.md'),
 'source_control_refs':[pin(p)for p in refs],'original_public_V1_status':'FAILED test frame whitespace assertion; never a PASS',
 'actual_formal_or_body_acceptance':False})
entry=R/'probata-t28-initialized-u32-public-control-entry-v1-20261016.py'
assert pin(entry)['sha256']=='5557ff0afc1ea95946e657286dfeb6fb7a6175eb9ae3de7aed365bcb42d9bc5c'
text=entry.read_text();oldsha='59f21010f1f61bc0f231578e9af19859dbb22b9286906599043eaf9a163679e3';assert text.count(oldsha)==1
text=text.replace(oldsha,policy['sha256']).replace('independently reviewed97 source-policy metadata changed','explicit successor source-policy metadata changed').replace('97 selected source byte changed: ','successor selected source byte changed: ')
anchor=" out.mkdir();save(out/'source-before.json',before);save(out/'runtime-before.json',runtime)"
assert text.count(anchor)==1
text=text.replace(anchor,anchor+"\n pycache=out/'source-cache'\n if pycache.exists()or pycache.is_symlink():raise ValueError('fresh nonexistent private bytecode cache prefix required')")
anchor="  'OPAM_SWITCH_PREFIX':runtime['opam_switch_prefix'],'TMPDIR':str(out/'tmp')}";assert text.count(anchor)==1
text=text.replace(anchor,"  'OPAM_SWITCH_PREFIX':runtime['opam_switch_prefix'],'TMPDIR':str(out/'tmp'),'PYTHONPYCACHEPREFIX':str(pycache)}")
anchor="   'runtime_pins_unchanged':runtime_equal,'raw_bytes_before_receipt':total,'scope':'compiler/scripted-persistence observation only',";assert text.count(anchor)==1
text=text.replace(anchor,"   'python_bytecode_cache':{'prefix':str(pycache),'fresh_nonexistent_before_child':True,'exists_after':pycache.exists(),'policy':'-B and PYTHONDONTWRITEBYTECODE plus fresh prefix; no ignored author pyc consumption'},\n"+anchor)
anchor=" if code!=0 or error or after!=before or not runtime_equal or not clean or total>LIMIT:return 1";assert text.count(anchor)==1
text=text.replace(anchor," if code!=0 or error or after!=before or not runtime_equal or not clean or total>LIMIT or pycache.exists():return 1")
ast.parse(text)
new=R/'probata-t28-initialized-u32-public-control-entry-v2-20261016.py';assert not new.exists();new.write_text(text)
print(json.dumps({'source_policy':policy,'entry':pin(new),'initialized_changed_path':changed[0],'scope':'INERT; no public workflow/compiler/prover/native execution'},sort_keys=True))
