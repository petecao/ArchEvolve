from pathlib import Path
import ast,hashlib,json,re,subprocess
R=Path('/private/tmp/probata-resume-t07-private-array');C='9ef0603a70f32a30f3556080891457355ad7a5b3';P='swdb-project/.scratch/probata-proof-of-concept-2026-10-13/';B=P+'prototype/07-wp-hints/';H=lambda b:hashlib.sha256(b).hexdigest()
def blob(p,c=C):return subprocess.check_output(['git','show',c+':'+p],cwd=R)
e=json.loads(blob(P+'evidence/t07-selected-source-preparation-20261016.json'))
for x in e['source_files']:assert H(blob(x['path']))==x['sha256'];ast.parse(blob(x['path'])) if x['path'].endswith('.py') else None
manifest=Path(e['raw_artifact_manifest']['path']);assert H(manifest.read_bytes())==e['raw_artifact_manifest']['sha256'];m=json.loads(manifest.read_bytes());assert len(m['files'])==495
for x in m['files']:
 p=Path(x['path']);assert H(p.read_bytes())==x['sha256'] and p.stat().st_size==x['bytes'],str(p)
for k in ['source_record','full_include_closure']:
 p=Path(e[k]['path']);assert H(p.read_bytes())==e[k]['sha256']
record=json.loads(Path(e['source_record']['path']).read_bytes());out=Path(e['source_record']['path']).parent;main=out/'source/benchmarks/gapbs/src/bfs.cc';raw=main.read_bytes();assert H(raw)==e['selected_main_sha256'];o=record['selected_compiler_observations'];assert o==e['selected_compiler_observations'];closure=json.loads((out/'physical-include-closure.json').read_bytes());assert len(closure)==901
for x in closure:
 p=Path(x['path']);assert H(p.read_bytes())==x['sha256'] and p.stat().st_size==x['bytes'],str(p)
assert len({x['path'] for x in closure})==901
project=R/'swdb-project';app=project/'apps/dx100';n=0
for p,h in record['original_source_pins'].items():
 assert H((app/p).read_bytes())==h
 staged=out/'source'/p
 assert H(staged.read_bytes())==(e['selected_main_sha256'] if p=='benchmarks/gapbs/src/bfs.cc' else h);n+=1
for p,h in record['project_producer_pins'].items():assert H(blob('swdb-project/'+p))==h;assert H((project/p).read_bytes())==h
assert H((out/'source/benchmarks/gapbs/src/swdb_dxc_lowering.hpp').read_bytes())==record['project_producer_pins']['library/dx100/dxc_lowering.hpp']
# Independently inspect JSON trees as data; no project imports or functions.
def roots(p):
 s=p.read_bytes().decode();i=0;a=[];d=json.JSONDecoder()
 while i<len(s):
  while i<len(s) and s[i].isspace():i+=1
  if i==len(s):break
  x,i=d.raw_decode(s,i);a.append(x)
 return a
def walk(x,ps=()):
 yield x,ps
 for y in x.get('inner',[]):yield from walk(y,ps+(x,))
td=[x for x in roots(out/'TDStep-ast.stdout') if x.get('kind')=='FunctionDecl' and x.get('name')=='TDStep'];assert len(td)==1;td=td[0];assert Path(td['loc']['file']).resolve()==main.resolve()
local={x['id']:x for x,p in walk(td) if x.get('kind')=='VarDecl' and x.get('name')=='lqueue'};assert len(local)==1;local=next(iter(local.values()));assert local['type']['desugaredQualType']=='QueueBuffer<int>'
constructions=[x for x,p in walk(local) if x.get('kind')=='CXXConstructExpr'];assert len(constructions)==1 and constructions[0]['ctorType']['qualType']=='void (SlidingQueue<int> &, size_t)';defaults=[x for x,p in walk(constructions[0]) if x.get('kind')=='CXXDefaultArgExpr'];assert len(defaults)==1 and [x.get('value') for x,p in walk(defaults[0]) if x.get('kind')=='IntegerLiteral']==['16384']
s=o['stable_source_binding'];assert raw[slice(*s['declaration_byte_range'])]==b'QueueBuffer<NodeID> lqueue(queue)';assert all(raw[slice(*u['byte_range'])]==b'lqueue' for u in s['source_uses']);assert sorted(u['method'] for u in s['source_uses'])==['flush','push_back','push_back'];assert len(s['implicit_capture_byte_ranges'])==2
refs=[];caps=[]
for x,ps in walk(td):
 if x.get('kind')=='DeclRefExpr' and x.get('referencedDecl',{}).get('id')==local['id']:
  r=x['range'];span=[r['begin']['offset'],r['end']['offset']+r['end']['tokLen']]
  if ps[-1]['kind']=='CapturedStmt':caps.append(span);assert any(p['kind']=='OMPForDirective' for p in ps)
  else:
   members=[p for p in ps if p.get('kind')=='MemberExpr'];calls=[p for p in ps if p.get('kind')=='CXXMemberCallExpr'];assert members and calls;refs.append({'byte_range':span,'method':members[-1]['name']})
refs=list({tuple(x['byte_range']):x for x in refs}.values());assert sorted(refs,key=lambda x:x['byte_range'])==s['source_uses'] and caps==s['implicit_capture_byte_ranges'];assert all(any(u['byte_range']==c and u['method']=='push_back' for u in refs) for c in caps)
queue=[x for root in roots(out/'QueueBuffer-ast.stdout') for x,p in walk(root) if x.get('kind')=='ClassTemplateSpecializationDecl' and x.get('completeDefinition') and any(y.get('kind')=='TemplateArgument' and y.get('type',{}).get('qualType')=='int' for y in x.get('inner',[]))];assert len(queue)==1 and queue[0]['name']=='QueueBuffer'
fields={x['name']:x['type'].get('desugaredQualType',x['type']['qualType']) for x in queue[0]['inner'] if x.get('kind')=='FieldDecl'};assert fields==o['field_map']
news=[(x,p) for x,p in walk(queue[0]) if x.get('kind')=='CXXNewExpr'];deletes=[(x,p) for x,p in walk(queue[0]) if x.get('kind')=='CXXDeleteExpr'];assert len(news)==len(deletes)==1;new,np=news[0];delete,dp=deletes[0];assert new['isArray'] and new['type']['qualType']=='int *' and len(new['inner'])==1 and not new.get('initStyle');assert any(p.get('kind')=='CXXConstructorDecl' for p in np);assert delete['isArray'] and any(p.get('kind')=='CXXDestructorDecl' for p in dp)
commands=json.loads((out/'compiler-commands.json').read_bytes());assert len(commands)==6 and all(x['returncode']==0 for x in commands)
for x in commands:
 a=x['argv'];assert a[0]==o['compiler_path'];assert '--no-default-config' in a and '-isysroot' in a and a[a.index('-isysroot')+1]==o['explicit_SDK'];assert '-std=c++11' in a and '-DFUNC' in a and '-fopenmp' in a;assert not any(z in a for z in ['--version','-o','-c','-shared'])
assert H(Path(o['compiler_path']).read_bytes())==o['compiler_sha256'] and str(Path(o['compiler_path']).resolve())==o['compiler_resolved'];assert H((Path(o['explicit_SDK'])/'SDKSettings.json').read_bytes())==o['SDK_settings_sha256']
controls=json.loads((out.parent/'controls.json').read_bytes());assert H((out.parent/'controls.json').read_bytes())==e['controls']['receipt_sha256'];assert len(controls['records'])==35 and all(x['passed'] for x in controls['records'])
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',C],cwd=R).decode().splitlines();unchanged=[]
for p in paths:
 if any(p.startswith(B+d+'/') for d in ['standin','standin_outslot','standin_private_array','standin_outslot_canonical','standin_private_array_canonical']):assert blob(p)==blob(p,'b9b96fb85573c0292d2f7171b984cd2ee4076443');unchanged.append(p)
# Explicit composition equivalence by literal transcription, without executing project producers.
original=(app/'benchmarks/gapbs/src/bfs.cc').read_bytes().decode();lines=original.splitlines(keepends=True);scalar=''.join(l for i,l in enumerate(lines,1) if i not in set(range(63,226))|set(range(366,444)));selection='#ifdef MAA\n        return DOBFSMAA(g, sp.PickNext(), cli.logging_en());\n#else\n        return DOBFS(g, sp.PickNext(), cli.logging_en());\n#endif';assert scalar.count(selection)==1;scalar=scalar.replace(selection,'        return DOBFS(g, sp.PickNext(), cli.logging_en());');start=scalar.index('void TDStep(');end=scalar.index('\nint64_t TDStep2(',start);text=scalar[:start]+blob('swdb-project/library/dx100/bfs_read_offload.inc').decode()+scalar[end:];text=text.replace('#include <MAA_utility.hpp>','#include <MAA_utility.hpp>\n#include "swdb_dxc_lowering.hpp"',1)
producer=ast.parse(blob('swdb-project/swdb/certification.py'));fun=next(x for x in producer.body if isinstance(x,ast.FunctionDef) and x.name=='peter_source');assigns={x.targets[0].id:ast.literal_eval(x.value) for x in fun.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id in ['setup','guarded']};assert text.count(assigns['setup'])==1;text=text.replace(assigns['setup'],assigns['guarded'],1).replace('    return parent;\n}\n\n\nvoid PrintBFSStats','    __dxc_report();\n    return parent;\n}\n\n\nvoid PrintBFSStats',1);assert text.encode()==raw
result={'source_commit':C,'evidence_sha256':H(blob(P+'evidence/t07-selected-source-preparation-20261016.json')),'raw_manifest_sha256':H(manifest.read_bytes()),'raw_artifacts_checked':495,'include_closure_files_checked':901,'physical_original_and_staged_source_pairs_checked':n,'source_records_checked':3,'project_producer_pins_checked':4,'compiler_and_SDK_settings_pins_checked':2,'selected_main_sha256':H(raw),'composition_independently_reconstructed_without_project_execution':True,'independent_AST_observations':{'one_exact_main_TDStep':True,'one_QueueBuffer_int_local':True,'constructor_default':16384,'source_member_uses':refs,'same_dump_captures':caps,'new_array_no_initializer':True,'delete_array_in_dtor':True},'compiler_commands_read':6,'passing_control_records':35,'unchanged_hand_model_files':len(unchanged),'unchanged_directories':5,'hash_errors':[],'reviewer_actual_tool_execution':False,'reviewer_source_edits':False}
p=Path('/private/tmp/probata-t07-selected-source-passive-data-9ef0603a-20261016.json');p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
