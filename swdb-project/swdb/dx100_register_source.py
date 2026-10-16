"""2026-10-16 ET. Isolated u32 MMIO register source admission, normal return only.

No added volatile semantics. Exact compiler/body observations are evidence, not
proof of MMIO implementation or source/model contract-body correspondence.
"""
import hashlib,json,re,shlex,subprocess,tempfile
from pathlib import Path
from swdb import artifacts,stdlib_provenance
from swdb.dx100_register_model import OWNER,ENTRY,STATEMENT,CALLER,STATE,PROTOTYPES,CONTRACTS,MODEL
from swdb.dx100_size_source import SOURCE_PINS,_function_ir as _size_function_ir
from swdb.dx100_stream_source import _exact,_clean,_body,_parse_dump,_selected_frozen_body as _stream_frozen_body

KIND='dx100-u32-register-v1'
LAYOUT='dx100-u32-register-partial-v1'
PARTIAL_CONTRACT='contract.dx100_register_partial_fixture.v1'
PARTIAL_METHOD='method.dx100-register-partial-fixture-v1'
class Refused(ValueError):pass


def _function_ir(*args,**kwargs):
 try:return _size_function_ir(*args,**kwargs)
 except ValueError as exc:raise Refused(str(exc)) from None


def _selected_frozen_body(*args,**kwargs):
 try:return _stream_frozen_body(*args,**kwargs)
 except ValueError as exc:raise Refused(str(exc)) from None

def register_layout(data):return (data.get('model')or{}).get('layout')==LAYOUT

def policy(library,definition):
 try:
  if not isinstance(definition,dict)or set(definition)!={'kind','call','entry','sources'}or definition['kind']!=KIND or definition['call']not in PROTOTYPES or not _exact(definition['entry'],ENTRY):raise Refused('explicit isolated u32 register source/entry certificate required')
  if not isinstance(definition['sources'],list)or len(definition['sources'])!=len(SOURCE_PINS):raise Refused('all distinct immutable register source pins required')
  pins=[]
  for source in definition['sources']:
   library._pin(source);path=library.resolve(source).resolve()
   if artifacts.file_hash(path)!=SOURCE_PINS.get(path.name)or any(Path(p['path']).name==path.name for p in pins):raise Refused('register immutable source changed or repeated')
   pins.append({'path':str(path),'bytes':path.stat().st_size,'sha256':SOURCE_PINS[path.name]})
  return {'kind':KIND,'call':definition['call'],'entry':definition['entry'],'sources':pins,'termination_policy':'conditional normal return; no hardware liveness'}
 except (OSError,ValueError,KeyError,TypeError,AttributeError)as exc:return {'refused':str(exc)}

def check(library,data,texts,error):
 rows=[r for r in data.get('calls',[])if isinstance(r,dict)]
 definitions=[v['definition']for r in rows for v in [r,*r.get('instances',[])]if isinstance(v,dict)and isinstance(v.get('definition'),dict)]
 if not register_layout(data):
  if any(d.get('kind')==KIND for d in definitions):error('calls.definition','register definition needs the closed original-partial layout');return False
  return True
 valid=True
 def refuse(message):
  nonlocal valid
  valid=False;error('model.layout',message)
 active=[r for r in rows if r.get('supported')is not False]
 if len(active)!=2 or {r['call']for r in active}!=set(PROTOTYPES):refuse('register projection admits exactly set_reg/get_reg u32');return False
 for row in active:
  name=row['call'];variants=row.get('instances')
  if not isinstance(variants,list)or len(variants)!=1:refuse('register projection requires one explicit u32 instance per family');continue
  v=variants[0]
  if v.get('arguments')!=['unsigned int']or type(v.get('arity'))is not int or v['arity']!=(2 if name=='set_reg'else 1):refuse('register type/arity not supported')
  if v.get('prototype')!=PROTOTYPES[name]or _clean(v.get('contract',''))!=_clean(CONTRACTS[name]):refuse('register original partial ABI/value/frame contract changed')
  selected=policy(library,v.get('definition'))
  if 'refused'in selected or selected.get('call')!=name:refuse(selected.get('refused','register source call differs'))
  rules=[r for r in data.get('rules',[])if r.get('id')=='register_scope']
  if len(rules)!=1 or rules[0].get('statement')!=STATEMENT or rules[0].get('assumed')!={'owner':OWNER}or rules[0].get('record_assumption')is not True or 'register_scope'not in row.get('rules',[]):refuse('register scope/TCB premise must appear in every verdict')
 for key,want in [('model.state',STATE),('model.c',MODEL)]:
  if _clean(texts.get(key,''))!=_clean(want):refuse('register ordinary model changed')
 if any(_clean(texts.get(key,''))for key in ('model.logic','ghost.acsl'))or data.get('constants')or data.get('queries')or data.get('wp'):refuse('register projection adds no axiom/query or original-unit premise')
 return valid

def _bodies(tokens,dumps,sources):
 header=next(Path(p['path']).read_text()for p in sources if Path(p['path']).name=='MAA_gem5.hpp')
 expected={'set_reg':_body(header,'inline void set_reg('),'get_reg':_body(header,'inline volatile T1 get_reg('),'trust_fixture':_body(CALLER,'int trust_fixture(')}
 if set(dumps)!=set(expected):raise Refused('register frozen source census differs')
 found={}
 for name,want in expected.items():
  bound=_selected_frozen_body(_parse_dump(dumps[name]),name,tokens,template=name!='trust_fixture')
  if _clean(bound['body'])!=_clean(want):raise Refused('register effective source body/caller differs: '+name)
  found[name]=bound
 return found

def _probe():
 return '''
static_assert(sizeof(unsigned int)==4 && alignof(unsigned int)==4 && sizeof(void*)==8,"u32 register ABI");
extern "C" void __dx_set_source(int id,unsigned int value) { if(id<0 || id>=32)return; ::set_reg<unsigned int>(id,value); }
extern "C" void __dx_set_reference(int id,unsigned int value) { if(id<0 || id>=32)return; ((unsigned int*)::REG_noncacheable)[id]=value; __asm__ __volatile__("mfence;"); }
extern "C" unsigned int __dx_get_source(int id) { if(id<0 || id>=32)return 0; return ::get_reg<unsigned int>(id); }
extern "C" unsigned int __dx_get_reference(int id) { if(id<0 || id>=32)return 0; volatile unsigned int value=((unsigned int*)::REG_noncacheable)[id]; __asm__ __volatile__("mfence;"); return value; }
extern "C" int __dx_caller_reference() { ::set_reg<unsigned int>(0,7U); ::set_reg<unsigned int>(1,11U); return (int)(100U*::get_reg<unsigned int>(0)+::get_reg<unsigned int>(1)); }
'''

def _operations(module):
 normalize=lambda text:re.sub(r'\s+','',re.sub(r', ![A-Za-z_][\w.]* !\d+','',text))
 found={}
 alloc,alloc_body=_function_ir(module,'_Z9alloc_MAAv')
 addresses={'SPD_data_cacheable':17179869184,'SPD_data_noncacheable':17181966336,'SPD_size_noncacheable':17184063488,'SPD_ready_noncacheable':17184063552,'REG_noncacheable':17184063616,'INSTR_opcode_datatype_optype_tdst1_tdst2':17184063744,'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc':17184063752,'INSTR_baseaddr':17184063760}
 for name,address in addresses.items():
  if not re.search(r'store ptr inttoptr \(i64 '+str(address)+r' to ptr\), ptr @'+name+r', align 8',alloc_body):raise Refused('register source scalar mapping/geometry changed: '+name)
 if not re.search(r'store i64 17184063768, ptr @MAA_end_addr, align 8\b',alloc_body):raise Refused('register scalar mapping end address differs')
 if not re.search(r'^target datalayout = \"e-',module,re.M):raise Refused('register mapping requires explicit little endian ABI')
 found['mapping']={'source':alloc,'addresses':addresses,'scalar_bytes':128,'end_address':17184063768}
 for name in ('set','get'):
  source,body=_function_ir(module,'__dx_'+name+'_source');reference,other=_function_ir(module,'__dx_'+name+'_reference')
  if normalize(body)!=normalize(other):raise Refused('register bounded compiler effects differ: '+name+' '+body+' versus '+other)
  if body.count('"mfence;"')!=1 or '~{memory}'in body:raise Refused('register fence/clobber differs from actual source')
  if '@REG_noncacheable'not in body or not re.search(r'getelementptr(?: inbounds)?(?: nuw| nusw)? i32,',body):raise Refused('register source address/word stride not bound: '+body)
  # Preserve the actual NONvolatile pointed access; volatile applies only to
  # get_reg's local temporary. No invented MMIO qualification is admitted.
  if name=='set'and not re.search(r'\bstore i32 ',body):raise Refused('register nonvolatile typed write missing')
  if name=='get'and not re.search(r'\bload i32, ptr ',body):raise Refused('register nonvolatile typed read missing')
  found[name]={'source':source,'reference':reference,'body':body}
 source,body=_function_ir(module,'_Z13trust_fixturev');reference,other=_function_ir(module,'__dx_caller_reference')
 if normalize(body)!=normalize(other):raise Refused('register closed caller ordering/elision/alias effects differ')
 if body.count('"mfence;"')!=4:raise Refused('register closed caller fence count/order differs')
 found['caller']={'source':source,'reference':reference,'body':body,'nonvolatile_elision':'exact closed caller emitted effects retained; no source volatile strengthening'}
 return found


def certify(unit,declaration,selected,caller,*,standard,timeout):
 if 'refused'in selected:raise Refused(selected['refused'])
 loc=declaration.get('loc')or{};headers={Path(p['path']).name:p for p in selected['sources']}
 if loc.get('spellingLoc')or loc.get('expansionLoc')or Path(loc.get('_file',loc.get('file',''))).resolve()!=Path(headers['MAA_gem5.hpp']['path']):raise Refused('register definition must originate in exact immutable header')
 location=caller.get('loc')or{}
 if caller.get('name')!='trust_fixture'or caller.get('type',{}).get('qualType')!='int ()'or location.get('spellingLoc')or location.get('expansionLoc')or Path(location.get('_file',location.get('file',''))).resolve()!=unit.source.resolve():raise Refused('register requires direct closed original-partial caller')
 cache=getattr(unit,'_dx100_register_certificate',None)
 if cache is not None:return {**cache,'call':selected['call'],'source_mangled':declaration.get('mangledName')}
 runtime=stdlib_provenance.runtime_identity(unit.tool);source_hash=unit.source_digest
 def pin(path):
  p=Path(path).resolve();return {'path':str(p),'bytes':p.stat().st_size,'sha256':artifacts.file_hash(p)}
 def unchanged():
  if artifacts.file_hash(unit.source)!=source_hash or any(pin(p['path'])!=p for p in selected['sources']):raise Refused('register source changed during binding')
 def run(command):
  try:r=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
  except (OSError,subprocess.SubprocessError)as exc:raise Refused('register compiler binding did not finish: '+str(exc))from None
  if r.returncode:raise Refused('register compiler refused: '+r.stderr[-1200:])
  return r.stdout
 unchanged();commands=[];probe=_probe();dumps={}
 with tempfile.TemporaryDirectory(prefix='swdb-dx100-register-')as folder:
  path=Path(folder)/'probe.ii';dep=Path(folder)/'original.d'
  pre=[*unit.tool.command,'-x','c++','-std='+standard,'-fopenmp','-E','-MD','-MF',str(dep),'-I'+str(unit.source.parent)]
  pre+=['-I'+str(p)for p in unit.includes]+['-D'+d for d in unit.defines]+[str(unit.source)]
  tokens=run(pre);inputs=[pin(p)for p in sorted(set(shlex.split(dep.read_text().replace('\\\n','').split(':',1)[1])))]
  path.write_text(tokens+probe)
  for name in ('set_reg','get_reg','trust_fixture'):
   command=[*unit.tool.command,'-x','c++-cpp-output','-std='+standard,'-fopenmp','-fsyntax-only','-Xclang','-ast-dump=json','-Xclang','-ast-dump-filter='+name,str(path)]
   dumps[name]=run(command);commands.append(command)
  bodies=_bodies(tokens,dumps,selected['sources'])
  command=[*unit.tool.command,'-x','c++-cpp-output','-std='+standard,'-fopenmp','-O2','-S','-emit-llvm','-o','-',str(path)]
  module=run(command);operations=_operations(module)
  if any(pin(p['path'])!=p for p in inputs)or stdlib_provenance.runtime_identity(unit.tool)!=runtime:raise Refused('register compiler input/runtime changed')
 unchanged();digest=lambda t:hashlib.sha256(t.encode()).hexdigest()
 certificate={**selected,'source_path':str(unit.source.resolve()),'source_sha256':source_hash,'source_mangled':declaration.get('mangledName'),
 'compiler_inputs':inputs,'runtime_identity':runtime,'preprocess_command':pre,'body_dump_commands':commands,'compiler_command':command,
 'preprocessed_source':tokens,'preprocessed_source_sha256':digest(tokens),'probe_source':probe,'probe_source_sha256':digest(probe),
 'body_dumps':dumps,'body_dumps_sha256':{k:digest(v)for k,v in dumps.items()},'body_bindings':bodies,'llvm_module':module,'llvm_module_sha256':digest(module),'operations':operations,'scope_statement':STATEMENT}
 unit._dx100_register_certificate=certificate
 return certificate

def bindings(lowering):return [r['semantic_source']for r in getattr(lowering,'summaries',())if r.get('semantic_source',{}).get('kind')==KIND]

def recheck(lowering):
 found=[]
 for c in bindings(lowering):
  try:
   if c['kind']!=KIND or c['call']not in PROTOTYPES or not _exact(c['entry'],ENTRY)or c['scope_statement']!=STATEMENT:raise Refused('register scope/source/entry changed')
   for text,digest in [('preprocessed_source','preprocessed_source_sha256'),('probe_source','probe_source_sha256'),('llvm_module','llvm_module_sha256')]:
    if hashlib.sha256(c[text].encode()).hexdigest()!=c[digest]:raise Refused('register compiler evidence changed')
   if c['probe_source']!=_probe()or c['body_dumps_sha256']!={k:hashlib.sha256(v.encode()).hexdigest()for k,v in c['body_dumps'].items()}:raise Refused('register probe/body evidence changed')
   if artifacts.file_hash(c['source_path'])!=c['source_sha256']:raise Refused('register caller changed')
   for p in [*c['sources'],*c['compiler_inputs']]:
    if Path(p['path']).stat().st_size!=p['bytes']or artifacts.file_hash(p['path'])!=p['sha256']:raise Refused('register physical source/compiler input changed')
   if len(c['sources'])!=len(SOURCE_PINS)or {Path(p['path']).name:p['sha256']for p in c['sources']}!=SOURCE_PINS:raise Refused('register immutable source family changed')
   if _bodies(c['preprocessed_source'],c['body_dumps'],c['sources'])!=c['body_bindings']or _operations(c['llvm_module'])!=c['operations']:raise Refused('register source/compiled-effect metadata changed')
   found.append({k:c[k]for k in ('kind','call','entry','source_sha256','preprocessed_source_sha256','llvm_module_sha256','sources','compiler_inputs')})
  except (KeyError,TypeError,AttributeError,OSError,UnicodeError)as exc:raise Refused('register certificate unavailable: '+str(exc))from None
 return found

def unit_policy(library,entry):
 unit=entry.get('proof_unit')or{};ident='semantics.dx100_register_fixture_0_2';data=library.get(ident)
 if entry.get('id')!=PARTIAL_CONTRACT or entry.get('version')!='0.1'or unit.get('function')!='trust_fixture'or not isinstance(data,dict)or not register_layout(data)or ident not in library.files:raise Refused('register proof requires its distinct original-partial contract/unit version')
 expected={'kind':'partial-normal-return-v1','source_policy':KIND,'semantics':{'id':ident,'sha256':artifacts.file_hash(library.files[ident])}}
 if not _exact(unit.get('correctness_policy'),expected):raise Refused('register proof requires explicit original partial policy and exact semantics pin')
 return expected
