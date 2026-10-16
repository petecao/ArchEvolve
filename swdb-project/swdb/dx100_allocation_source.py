"""2026-10-16 ET. Closed source-bound software allocation, no device entry.

Compiler equality is a trusted compiler observation under checked source/body
bindings. This is not a hardware or general contract/body refinement theorem.
"""
import hashlib,json,re,shlex,subprocess,tempfile
from pathlib import Path
from swdb import artifacts,stdlib_provenance
from swdb.dx100_interface import HEADERS
from swdb.dx100_stream_source import _parse_dump,_body,_clean

KIND='dx100-software-allocation-v1'
LAYOUT='dx100-software-allocation-v1'
OWNER='Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'
STATEMENT=('Only the pinned init_MAA software-counter reset, unsigned-int/unsigned-long-long tile allocation '
 'and zero-argument register allocation are admitted in this unchanged synthetic caller. '
 'The counters and source assertions are modeled with signed-int bounds duties, including odd64-bit tile starts. '
 'No MMIO, hardware freshness, payload/register initialization, ownership enforcement or progress is established. '
 'Compiler/source identity is checked; contract/body correspondence remains an owned TCB duty pending Yan-Ru freeze review (59).')
STATE='int SPD_count;\nint REG_count;\nsigned char region_count;\n'
CONTRACTS={'init_MAA':r'assigns SPD_count, REG_count, region_count; ensures SPD_count == 0 && REG_count == 0 && region_count == 6;'}
PROTOTYPES={'init_MAA':'void init_MAA(void)'}
MODEL='void init_MAA(void) { REG_count=0; SPD_count=0; region_count=6; }\n'
for family,state in [('get_new_tile','SPD_count'),('get_new_reg','REG_count')]:
 for argument,suffix,width in [('unsigned int','unsigned_int',1),('unsigned long long','unsigned_long_long',2)]:
  symbol=family+'_'+suffix+('_args0'if family=='get_new_reg'else '')
  PROTOTYPES[symbol]='int '+symbol+'(void)'
  CONTRACTS[symbol]=(f'requires 0 <= {state} <= {32-width}; assigns {state}; '
    +rf'ensures \result == \old({state}) && {state} == \old({state}) + {width};')
  MODEL+='int '+symbol+'(void) { int width='+str(width)+'; DX_ASSERT(width==1 || width==2); int old='+state+'; '+state+' += width; DX_ASSERT('+state+'<=32); return old; }\n'

CANONICAL_CALLER=('int trust_fixture() { init_MAA(); int t0=get_new_tile<unsigned int>(); '
 'int t1=get_new_tile<unsigned long long>(); int r0=get_new_reg<unsigned long long>(); '
 'int r1=get_new_reg<unsigned int>(); return 1000*t0+100*t1+10*r0+r1; }\n')

class Refused(ValueError):pass

def allocation_layout(data):return (data.get('model')or{}).get('layout')==LAYOUT

def policy(library,definition):
 try:
  if not isinstance(definition,dict)or set(definition)!={'kind','call','sources'}or definition['kind']!=KIND or definition['call']not in {'init_MAA','get_new_tile','get_new_reg'}:
   raise Refused('closed software allocator source policy required')
  if not isinstance(definition['sources'],list)or len(definition['sources'])!=2:raise Refused('both immutable allocation headers required')
  pins=[]
  for source in definition['sources']:
   library._pin(source);path=library.resolve(source).resolve()
   if artifacts.file_hash(path)!=HEADERS.get(path.name)or any(Path(p['path']).name==path.name for p in pins):raise Refused('allocation source header changed or repeated')
   pins.append({'path':str(path),'sha256':HEADERS[path.name],'bytes':path.stat().st_size})
  return {'kind':KIND,'call':definition['call'],'sources':pins}
 except (OSError,ValueError,KeyError,TypeError,AttributeError)as exc:return {'refused':str(exc)}

def check(library,data,texts,error):
 rows=[r for r in data.get('calls',[])if isinstance(r,dict)]
 definitions=[v['definition']for r in rows for v in [r,*r.get('instances',[])]if isinstance(v,dict)and isinstance(v.get('definition'),dict)]
 if not allocation_layout(data):
  if any(d.get('kind')==KIND for d in definitions):error('calls.definition','software allocator definition needs its closed layout');return False
  return True
 valid=True
 def refuse(message):
  nonlocal valid
  valid=False;error('model.layout',message)
 active=[r for r in rows if r.get('supported')is True]
 if len(active)!=3 or {r['call']for r in active}!={'init_MAA','get_new_tile','get_new_reg'}:refuse('software allocator admits exactly init and two allocation families');return False
 for row in active:
  name=row['call'];variants=row.get('instances')if name!='init_MAA'else[row]
  if not isinstance(variants,list)or len(variants)!=(1 if name=='init_MAA'else 3 if name=='get_new_reg'else 2):refuse('software allocator exact typed/overload census required');continue
  for v in variants:
   if name=='get_new_reg'and v.get('arity')==1:
    if v!={'arguments':['unsigned int'],'arity':1,'declaration':'inline int get_new_reg(T1 data)','prototype':'int get_new_reg_unsigned_int_args1(unsigned int data)','contract':r'requires \false; assigns \nothing;'}:refuse('initialized register overload must remain explicitly unreachable/unsupported')
    continue
   symbol=name
   if name!='init_MAA':
    if v.get('arguments')not in [['unsigned int'],['unsigned long long']]or type(v.get('arity'))is not int or v['arity']!=0:refuse('software allocator requires exact zero-arity u32/u64 builtin instances');continue
    symbol=name+'_'+v['arguments'][0].replace(' ','_')+('_args0'if name=='get_new_reg'else '')
    if name=='get_new_reg'and v.get('declaration')!='inline int get_new_reg()':refuse('software allocator selects only the zero-argument register declaration')
   if v.get('prototype')!=PROTOTYPES[symbol]or _clean(v.get('contract',''))!=_clean(CONTRACTS[symbol]):refuse('software allocator prototype/contract changed')
   resolved=policy(library,v.get('definition'))
   if 'refused'in resolved or resolved.get('call')!=name:refuse(resolved.get('refused','allocation call policy changed'))
 for key,value in [('model.state',STATE),('model.c',MODEL)]:
  if _clean(texts.get(key,''))!=_clean(value):refuse('software allocator exact ordinary model required: '+key)
 for key in ['ghost.acsl','model.logic']:
  if _clean(texts.get(key,'')):refuse('software allocator has no ghost/logic axiom')
 if data.get('constants')or data.get('queries')or data.get('wp'):refuse('software allocator adds no unit premise/query/device constant')
 rule=next((r for r in data.get('rules',[])if r.get('id')=='software_allocation_scope'),{})
 if rule.get('statement')!=STATEMENT or rule.get('assumed')!={'owner':OWNER}or rule.get('record_assumption')is not True:refuse('software allocator owned source/TCB boundary changed')
 return valid

def _children(n):return n.get('inner',[])
def _walk(n):
 yield n
 for c in _children(n):yield from _walk(c)
def _slice(node,tokens):
 points=[(node.get('range')or{}).get(k,{})for k in ('begin','end')]
 if any(type(p.get('offset'))is not int or 'spellingLoc'in p or 'expansionLoc'in p for p in points):raise Refused('indirect allocator frozen body range')
 start,end=points[0]['offset'],points[1]['offset']+points[1]['tokLen']
 if not 0<=start<end<=len(tokens.encode()):raise Refused('invalid allocator frozen source extent')
 return start,end,tokens.encode()[start:end].decode()

def _expression(node):
 kind=node.get('kind');children=_children(node)
 if kind in {'ParenExpr','ImplicitCastExpr','CXXStaticCastExpr','CStyleCastExpr','CXXFunctionalCastExpr'}and len(children)==1:return _expression(children[0])
 if kind=='IntegerLiteral':return int(node['value'])
 if kind=='DeclRefExpr':return ('name',node.get('referencedDecl',{}).get('name'))
 if kind=='UnaryOperator'and len(children)==1:return (node.get('opcode'),_expression(children[0]))
 if kind=='BinaryOperator'and len(children)==2:return (node.get('opcode'),_expression(children[0]),_expression(children[1]))
 return ('unsupported',kind)

def _callee(node):
 if node.get('kind')!='CallExpr' or not _children(node):return None
 refs=[n for n in _walk(_children(node)[0])if n.get('kind')=='DeclRefExpr']
 return refs[0].get('referencedDecl',{}).get('name')if len(refs)==1 else None

def _strip_expr(node):
 while node.get('kind')in {'ParenExpr','ImplicitCastExpr','CXXStaticCastExpr','CStyleCastExpr','CXXFunctionalCastExpr'}and len(_children(node))==1:node=_children(node)[0]
 return node

def _assertion(node,expected,variable):
 # The source assert must still be present. Within the admitted arithmetic
 # domain it is true; outside it no assertion-failure behavior is summarized.
 calls=[n for n in _walk(node)if n.get('kind')=='CallExpr']
 names=[]
 for call in calls:
  refs=[n for n in _walk(_children(call)[0])if n.get('kind')=='DeclRefExpr']
  names.append(refs[0].get('referencedDecl',{}).get('name')if len(refs)==1 else None)
 if names.count('__assert_rtn')+names.count('__assert_fail')!=1 or any(n not in {'__assert_rtn','__assert_fail','__builtin_expect'}for n in names):raise Refused('allocator source assertion is absent or has unbound effects')
 operators=[n.get('opcode')for n in _walk(node)if n.get('kind')in {'BinaryOperator','CompoundAssignOperator','UnaryOperator'}]
 if any(o not in {'==','||','<=','*','!'}for o in operators):raise Refused('allocator source assertion contains unbound effects')
 # Exact original predicate text appears once as executable operators and as
 # diagnostic text. Bounds/width behavior also independently matches LLVM.
 binaries=[n.get('opcode')for n in _walk(node)if n.get('kind')=='BinaryOperator']
 if sorted(binaries)!=sorted(['==','==','||']if expected=='width'else ['<=','*']):raise Refused('allocator source assertion predicate changed')
 conditionals=[n for n in _walk(node)if n.get('kind')=='ConditionalOperator']
 if len(conditionals)!=1 or len(_children(conditionals[0]))!=3:raise Refused('allocator source assertion has no exact abort guard')
 condition,yes,no=_children(conditionals[0]);condition=_strip_expr(condition)
 if _callee(condition)=='__builtin_expect':
  args=_children(condition)[1:]
  if len(args)!=2 or _expression(args[1])!=0:raise Refused('allocator source assertion prediction changed')
  shape=_expression(args[0])
  if not isinstance(shape,tuple)or len(shape)!=2 or shape[0]!='!':raise Refused('allocator source assertion abort polarity changed')
  shape=shape[1];failure,success=yes,no
 else:shape=_expression(condition);failure,success=no,yes
 predicate=('||',('==',('name',variable),1),('==',('name',variable),2))if expected=='width'else ('<=',('name',variable),('*',4,8))
 if shape!=predicate or _callee(_strip_expr(failure))not in {'__assert_rtn','__assert_fail'}or _expression(success)!=0:
  raise Refused('allocator source assertion exact condition/abort branch changed')

def _bodies(tokens,dumps,sources):
 header=next(Path(p['path']).read_text()for p in sources if Path(p['path']).name=='MAA_gem5.hpp')
 result={}
 for name,signature in [('init_MAA','inline void init_MAA('),('get_new_tile','inline int get_new_tile('),('get_new_reg','inline int get_new_reg()'),('trust_fixture','int trust_fixture(')]:
  families=[n for n in _parse_dump(dumps[name])if n.get('name')==name and n.get('kind')==('FunctionTemplateDecl'if name.startswith('get_new_')else'FunctionDecl')]
  if name=='get_new_reg':families=[f for f in families if all(sum(c.get('kind')=='ParmVarDecl'for c in _children(n))==0 for n in _children(f)if n.get('kind')=='FunctionDecl')]
  if len(families)!=1:raise Refused('allocator source family/overload is not unique: '+name)
  variants=[n for n in _children(families[0])if n.get('kind')=='FunctionDecl']if name.startswith('get_new_')else families
  if name.startswith('get_new_'):
   variants=[n for n in variants if any(c.get('kind')=='TemplateArgument'and c.get('type',{}).get('qualType')in {'unsigned int','unsigned long long'}for c in _children(n))]
   if len(variants)!=2:raise Refused('allocator exact two typed source instances required')
  if not variants:raise Refused('allocator source body missing')
  for variant in variants:
   bodies=[n for n in _children(variant)if n.get('kind')=='CompoundStmt']
   if len(bodies)!=1:raise Refused('allocator source function has no unique body')
   body=bodies[0];begin,end,text=_slice(body,tokens)
   if name.startswith('get_new_'):
    statements=_children(body)
    if len(statements)!=6:raise Refused('allocator original assertions/statement census changed')
    replacements=[]
    for index,kind in [(1,'width'),(4,'bound')]:
     statement=statements[index]
     variable=('num_tiles_needed'if name=='get_new_tile'else'num_regs_needed')if kind=='width'else ('SPD_count'if name=='get_new_tile'else'REG_count')
     _assertion(statement,kind,variable);a,b,_=_slice(statement,tokens)
     variable='num_tiles_needed'if name=='get_new_tile'else'num_regs_needed'
     target='SPD_count <= NUM_TILES'if name=='get_new_tile'else'REG_count <= NUM_SCALAR_REGS'
     replacements.append((a-begin,b-begin,'assert('+ (variable+' == 1 || '+variable+' == 2'if kind=='width'else target)+')'))
    for a,b,replacement in sorted(replacements,reverse=True):text=text[:a]+replacement+text[b:]
   expected=_body(CANONICAL_CALLER,'int trust_fixture(')if name=='trust_fixture'else _body(header,signature)
   if _clean(text)!=_clean(expected):raise Refused('allocator effective canonical source body changed: '+name+' '+text[:350])
   key=name+('/'+next((c['type']['qualType']for c in _children(variant)if c.get('kind')=='TemplateArgument'),'')if name.startswith('get_new_')else'')
   result[key]={'begin':begin,'end':end,'body':tokens.encode()[begin:end].decode(),'function_type':variant.get('type',{}).get('qualType'),'mangled':variant.get('mangledName')}
 return result

def _probe():
 text='\nstatic_assert(sizeof(int)==4 && sizeof(unsigned int)==4 && sizeof(unsigned long long)==8,"closed allocator ABI");\n'
 text+='extern "C" void __dx_init_source() { ::init_MAA(); }\nextern "C" void __dx_init_reference() { ::REG_count=0; ::SPD_count=0; ::region_count=6; }\n'
 for family,counter in [('tile','SPD_count'),('reg','REG_count')]:
  for typ,width in [('unsigned int',1),('unsigned long long',2)]:
   suffix=family+str(width);guard='if(value<0 || value>'+str(32-width)+') return -1; '
   text+='extern "C" long long __dx_'+suffix+'_source(int value) { '+guard+'::'+counter+'=value; int old=::get_new_'+family+'<'+typ+'>(); return 1000000000LL*old + ::'+counter+'; }\n'
   text+='extern "C" long long __dx_'+suffix+'_reference(int value) { '+guard+'::'+counter+'=value+'+str(width)+'; return 1000000000LL*value + ::'+counter+'; }\n'
 return text

def _operations(module):
 from swdb.dx100_size_source import _function_ir
 normalize=lambda text:re.sub(r'\s+','',re.sub(r', ![A-Za-z_][\w.]* !\d+','',text))
 out={}
 for name in ['init','tile1','tile2','reg1','reg2']:
  src,body=_function_ir(module,'__dx_'+name+'_source');ref,reference=_function_ir(module,'__dx_'+name+'_reference')
  if normalize(body)!=normalize(reference):raise Refused('bounded allocator compiled effects differ from independent counter reference: '+name+' '+body+' vs '+reference)
  out[name]={'source':src,'reference':ref}
 return out

def certify(unit,declaration,selected,caller,*,standard,timeout):
 if 'refused'in selected:raise Refused(selected['refused'])
 headers={Path(p['path']).name:p for p in selected['sources']}
 loc=declaration.get('loc')or{}
 if loc.get('spellingLoc')or loc.get('expansionLoc')or Path(loc.get('_file',loc.get('file',''))).resolve()!=Path(headers['MAA_gem5.hpp']['path']):raise Refused('allocator definition must originate in exact immutable header')
 if caller.get('name')!='trust_fixture'or caller.get('type',{}).get('qualType')!='int ()':raise Refused('allocator admits only the closed original-total caller')
 cache=getattr(unit,'_dx100_allocation_certificate',None)
 if cache is not None:return {**cache,'call':selected['call'],'source_mangled':declaration.get('mangledName')}
 runtime=stdlib_provenance.runtime_identity(unit.tool);source_hash=unit.source_digest
 def pin(path):
  p=Path(path).resolve();return {'path':str(p),'bytes':p.stat().st_size,'sha256':artifacts.file_hash(p)}
 def unchanged():
  if artifacts.file_hash(unit.source)!=source_hash or any(pin(p['path'])!=p for p in selected['sources']):raise Refused('allocator source changed during compiler binding')
 def run(command):
  try:r=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
  except (OSError,subprocess.SubprocessError)as exc:raise Refused('allocator compiler did not finish: '+str(exc))from None
  if r.returncode:raise Refused('allocator compiler refused: '+r.stderr[-1200:])
  return r.stdout
 unchanged();commands=[];probe=_probe();dumps={}
 with tempfile.TemporaryDirectory(prefix='swdb-dx100-allocation-')as folder:
  path=Path(folder)/'probe.ii';dep=Path(folder)/'original.d'
  pre=[*unit.tool.command,'-x','c++','-std='+standard,'-fopenmp','-E','-MD','-MF',str(dep),'-I'+str(unit.source.parent)]
  pre+=['-I'+str(p)for p in unit.includes]+['-D'+d for d in unit.defines]+[str(unit.source)]
  tokens=run(pre);inputs=[pin(p)for p in sorted(set(shlex.split(dep.read_text().replace('\\\n','').split(':',1)[1])))]
  path.write_text(tokens+probe)
  for name in ['init_MAA','get_new_tile','get_new_reg','trust_fixture']:
   command=[*unit.tool.command,'-x','c++-cpp-output','-std='+standard,'-fopenmp','-fsyntax-only','-Xclang','-ast-dump=json','-Xclang','-ast-dump-filter='+name,str(path)]
   dumps[name]=run(command);commands.append(command)
  bodies=_bodies(tokens,dumps,selected['sources'])
  command=[*unit.tool.command,'-x','c++-cpp-output','-std='+standard,'-fopenmp','-O2','-S','-emit-llvm','-o','-',str(path)]
  module=run(command);operations=_operations(module)
  if any(pin(p['path'])!=p for p in inputs)or stdlib_provenance.runtime_identity(unit.tool)!=runtime:raise Refused('allocator compiler input/runtime changed')
 unchanged();digest=lambda x:hashlib.sha256(x.encode()).hexdigest()
 certificate={**selected,'source_path':str(unit.source.resolve()),'source_sha256':source_hash,'source_mangled':declaration.get('mangledName'),
  'compiler_inputs':inputs,'runtime_identity':runtime,'preprocess_command':pre,'body_dump_commands':commands,'compiler_command':command,
  'preprocessed_source':tokens,'preprocessed_source_sha256':digest(tokens),'probe_source':probe,'probe_source_sha256':digest(probe),
  'body_dumps':dumps,'body_dumps_sha256':{k:digest(v)for k,v in dumps.items()},'body_bindings':bodies,'llvm_module':module,'llvm_module_sha256':digest(module),'operations':operations}
 unit._dx100_allocation_certificate=certificate
 return certificate

def bindings(lowering):return [r['semantic_source']for r in getattr(lowering,'summaries',())if r.get('semantic_source',{}).get('kind')==KIND]

def recheck(lowering):
 found=[]
 for c in bindings(lowering):
  try:
   if c['kind']!=KIND or c['call']not in {'init_MAA','get_new_tile','get_new_reg'}:raise Refused('allocation source/call kind changed')
   for text,digest in [('preprocessed_source','preprocessed_source_sha256'),('probe_source','probe_source_sha256'),('llvm_module','llvm_module_sha256')]:
    if hashlib.sha256(c[text].encode()).hexdigest()!=c[digest]:raise Refused('allocator compiler evidence changed')
   if c['probe_source']!=_probe()or c['body_dumps_sha256']!={k:hashlib.sha256(v.encode()).hexdigest()for k,v in c['body_dumps'].items()}:raise Refused('allocator probe/body evidence changed')
   if artifacts.file_hash(c['source_path'])!=c['source_sha256']:raise Refused('allocator original source changed')
   for p in [*c['sources'],*c['compiler_inputs']]:
    if Path(p['path']).stat().st_size!=p['bytes']or artifacts.file_hash(p['path'])!=p['sha256']:raise Refused('allocator physical source/compiler input changed')
   if len(c['sources'])!=2 or {Path(p['path']).name:p['sha256']for p in c['sources']}!=HEADERS:raise Refused('allocator immutable headers changed')
   if _bodies(c['preprocessed_source'],c['body_dumps'],c['sources'])!=c['body_bindings']or _operations(c['llvm_module'])!=c['operations']:raise Refused('allocator checked source/body/effects metadata changed')
   found.append({k:c[k]for k in ['kind','call','source_sha256','preprocessed_source_sha256','llvm_module_sha256','sources','compiler_inputs']})
  except (KeyError,TypeError,AttributeError,OSError,UnicodeError)as exc:raise Refused('allocator source certificate unavailable: '+str(exc))from None
 return found
