"""Isolated seven-Git-blob pure packet preparation only; no live project or tool import."""
import ast,hashlib,json,subprocess,sys,types
from pathlib import Path
REPO=Path('/private/tmp/probata-resume-t25');COMMIT='e99d09b1699b32525cd4c44cead21ed2fc6f4917';ROOT=Path('/private/tmp/probata-t25-prefix10-pure-canonical-v1-e99d09b1-20261016')
def git(*a):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(REPO),*a],timeout=60)
def sha(b):return hashlib.sha256(b).hexdigest()
ROOT.mkdir();(ROOT/'swdb').mkdir();rows=[]
for name in ['__init__.py','std_models.py','heap_model_vcs.py','vector_reallocation_model.py','vector_reallocation_inventory.py','vector_reallocation_vcs.py','heap_reallocation.mlw']:
 b=git('show',COMMIT+':swdb-project/swdb/'+name)
 if name.endswith('.py'):
  tree=ast.parse(b);imports={a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names}|{n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)};assert not(imports-{'hashlib','json','re','pathlib','ast','swdb','swdb.heap_model_vcs','swdb.vector_reallocation_inventory'})
 (ROOT/'swdb'/name).write_bytes(b);rows.append({'relative':'swdb/'+name,'sha256':sha(b),'bytes':len(b),'git_blob':git('rev-parse',COMMIT+':swdb-project/swdb/'+name).decode().strip()})
lowerer=git('show',COMMIT+':swdb-project/swdb/c_lowering.py');nodes=[n for n in ast.parse(lowerer).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in {'INTEGER_TYPES','FLOAT_TYPES','INTERNAL_TYPES'}];assert len(nodes)==3
for n in nodes:ast.literal_eval(n.value)
stub=types.ModuleType('swdb.c_lowering');exec(compile(ast.Module(body=nodes,type_ignores=[]),'<preparer-only frozen literals>','exec'),stub.__dict__);sys.modules['swdb.c_lowering']=stub
blocked=[]
def audit(event,args):
 if event in {'subprocess.Popen','os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen'}:blocked.append(event);raise RuntimeError('external/native execution forbidden')
sys.addaudithook(audit);sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from swdb import vector_reallocation_vcs as packets
assert Path(packets.__file__).resolve().parent==ROOT/'swdb'
manifest=packets.prepare('std_vector_int_realloc_v3_grow',ROOT/'canonical');assert packets.check('std_vector_int_realloc_v3_grow',ROOT/'canonical')==manifest
files=[{'path':str(p.relative_to(ROOT/'canonical')),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in sorted((ROOT/'canonical').rglob('*'))if p.is_file()]
group=next(g for g in manifest['logical_obligations']if g['id']=='grow.copy.step')['component_expansions'][0];assert group['id']=='grow.copy.step.advanced_copied_prefix'and len(group['parts'])==10 and len(manifest['obligations'])==61 and len(files)==70 and len([r for r in files if r['path'].startswith('references/')])==5 and not blocked
result={'scope':'Isolated exact seven Git blobs and literal-only type infrastructure; no live project-native/compiler/formal/SSH import or execution, not actual runtime overlay or proof.','source_commit':COMMIT,'files':rows,'lowerer_literal_source_sha256':sha(lowerer),'canonical_files':files,'manifest_sha256':sha((ROOT/'canonical/manifest.json').read_bytes()),'target_count':61,'focused_ids':group['parts'],'external_native_attempts':blocked}
(ROOT/'preparer-receipt.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['source_commit','target_count','manifest_sha256','external_native_attempts']}))
