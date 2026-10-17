"""2026-10-16 ET. Inert source-preserving C++ counterpart, never lowered-C reuse.

Only the pinned first source scope is admitted by this preparation. Actual
compiler/runtime lineage, external receiver premises and scientific jobs remain
root-owned. Shared concrete memory/MMIO semantics and checked source projection
are explicit TCB; C++ executes the original expression/control/assertion tokens.
"""
import hashlib
import json
from pathlib import Path
import re
import stat

SOURCE_SHA='3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'
HEADER_PINS={'MAA.hpp':'4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd',
 'MAA_gem5.hpp':'5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174'}
PINS={
 'whole_interface_v4.py':'217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8',
 'source_dispatch_v3.py':'d05d3ba716af2d88703636ffbf57bf0834acd5e59ee7ce3aebe0a72648a8b703',
 'source_argument_staging_v2.py':'79bdae72fd7b4de05771776684b5c6af275afb736313ece1df8790ae57ae6178',
 'source_statements_v2.py':'49832255fef43afa51078479770d62f01e7e539e4f71f4034e3f2648cb867738',
 'receiver-state-draws-v2/receiver_state_draws_v2.py':'f6c19464a6587b4fbd4a6278dc66be97f1c4ab16d46b2db8cd6b804d41608a5f'}
TYPE_KEYS=('uint32_t','int32_t','float','uint64_t','int64_t','double')
SUFFIX=('u32','i32','f32','u64','i64','f64')
POINTERS={'index_data','source_data','result_data','min_data','max_data','address_only'}
ARRAYS={'data','limits'}


class Refused(ValueError):pass


def need(ok,message):
    if not ok:raise Refused(message)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def digest(value):return hashlib.sha256(canonical(value)).hexdigest()

def sha(value):return hashlib.sha256(value).hexdigest()


def file_pin(path,expected=None):
    path=Path(path);before=path.lstat();stable=lambda s:tuple(getattr(s,k) for k in
        ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
    need(stat.S_ISREG(before.st_mode) and path.resolve(strict=True)==path,'canonical physical source required')
    raw=path.read_bytes();need(stable(before)==stable(path.lstat()),'source changed during projection read')
    need(expected is None or sha(raw)==expected,'exact projection component/source changed')
    return raw,{'path':str(path),'bytes':len(raw),'sha256':sha(raw)}


def component(whole,name):
    raw,pin=file_pin(Path(whole)/name,PINS[name]);namespace={'__name__':'owned_cxx_projection','__file__':pin['path']}
    exec(compile(raw,pin['path'],'exec'),namespace);return namespace,pin


def walk(node):
    if not isinstance(node,dict):return
    yield node
    for child in node.get('inner',[]):yield from walk(child)


def check_edits(source,edits):
    need(type(source) is str and type(edits) is list and edits,'original source and nonempty fixed edits required')
    result=[];cursor=0
    for edit in sorted(edits,key=lambda row:row['begin']):
        need(set(edit)=={'begin','end','before','after','kind','declaration_id'} and type(edit['begin']) is int and type(edit['end']) is int
            and cursor<=edit['begin']<edit['end']<=len(source),'overlapping/malformed source projection edit')
        need(source[edit['begin']:edit['end']]==edit['before'] and '\n' not in edit['before'] and '\n' not in edit['after'],
            'exact single-line declarator/include edit required')
        need(edit['kind'] in {'api-include','ordinary-array-declarator','cacheable-pointer-declarator','noncacheable-address-declarator'},
            'source expression/control edit outside profile')
        result += [source[cursor:edit['begin']],edit['after']];cursor=edit['end']
    result.append(source[cursor:]);projected=''.join(result)
    inverse=projected;shift=0;inverse_rows=[]
    for edit in sorted(edits,key=lambda row:row['begin']):
        begin=edit['begin']+shift;end=begin+len(edit['after']);inverse_rows.append((begin,end,edit['before']))
        shift+=len(edit['after'])-len(edit['before'])
    for begin,end,before in reversed(inverse_rows):inverse=inverse[:begin]+before+inverse[end:]
    need(inverse==source,'source-preserving edit inverse differs')
    return projected


def enum_text(project):
    headers={name:file_pin(Path(project)/'apps/dx100/benchmarks/API'/name,expected)[0].decode('ascii') for name,expected in HEADER_PINS.items()}
    result=[]
    for header,name in (('MAA.hpp','Operation_t'),('MAA_gem5.hpp','OpcodeType'),('MAA_gem5.hpp','DataType')):
        match=re.search(r'\benum(?: class)? '+name+r'(?: : uint8_t)?\s*\{[^}]*\};',headers[header])
        need(match,'exact original interface enum missing');result.append(match[0])
    return '\n'.join(result)


BASE=r'''/* Fixed C++ pointer/lifetime projection over the bound concrete memory model. */
#include <cstdint>
#include <climits>
#include <initializer_list>
#include <type_traits>
static_assert(CHAR_BIT==8 && sizeof(int)==4 && sizeof(void*)==8,"runtime-source-ABI");
#if !defined(__BYTE_ORDER__) || __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error unsupported_runtime_source_byte_order
#endif
__ENUMS__
static constexpr unsigned dws_cxx_thread = __THREAD__u;
static void dws_cxx_enter(unsigned object) {switch(object) {__ENTER__ default:SWDB_CHECK(0,"runtime-allocation-object");}}
static void dws_cxx_leave(unsigned object) {switch(object) {__LEAVE__ default:SWDB_CHECK(0,"runtime-allocation-object");}}
static dws_pointer dws_cxx_live(dws_pointer p) {
  if(p.kind==1) dws_local_require_v1(p.object,dws_cxx_thread);
  (void)dws_pointer_bytes(p);return p;
}
struct dws_cxx_erased {
  dws_pointer value;
  explicit dws_cxx_erased(dws_pointer p):value(dws_cxx_live(p)) {}
  dws_pointer get() const {return dws_cxx_live(value);}
};
template<class T> struct dws_cxx_traits;
__TRAITS__
template<class T> struct dws_cxx_reference {
  dws_pointer value;
  explicit dws_cxx_reference(dws_pointer p):value(dws_cxx_live(p)) {}
  operator T() const {return dws_cxx_traits<T>::load(dws_cxx_live(value));}
  dws_cxx_reference& operator=(T v) {dws_cxx_traits<T>::store(dws_cxx_live(value),v);return *this;}
  /* First source scope writes scalar values only. A proxy RHS would postpone
     its CPU read until after LHS formation; refuse rather than change order. */
  dws_cxx_reference& operator=(const dws_cxx_reference&)=delete;
};
template<class T> struct dws_cxx_pointer {
  dws_pointer value;
  explicit dws_cxx_pointer(dws_pointer p):value(dws_cxx_live(p)) {SWDB_CHECK(p.dtype==dws_cxx_traits<T>::dtype,"runtime-pointer-type");}
  operator dws_cxx_erased() const {return dws_cxx_erased(dws_cxx_live(value));}
  dws_cxx_pointer operator+(long long n) const {return dws_cxx_pointer(dws_pointer_offset(dws_cxx_live(value),n));}
  dws_cxx_reference<T> operator[](long long n) const {return dws_cxx_reference<T>(dws_pointer_offset(dws_cxx_live(value),n));}
};
template<class T> struct dws_cxx_address {
  dws_pointer value;
  explicit dws_cxx_address(dws_pointer p):value(p) {SWDB_CHECK(p.kind==3 && p.dtype==dws_cxx_traits<T>::dtype,"runtime-address-only");}
};
template<class T,unsigned N,unsigned Object> struct dws_cxx_array {
  dws_pointer value;
  dws_cxx_array()=delete;
  dws_cxx_array(std::initializer_list<T> values):value(dws_object_pointer(Object)) {
    SWDB_CHECK(value.dtype==dws_cxx_traits<T>::dtype && dws_objects[Object].extent==N,"runtime-array-source-type");
    SWDB_CHECK(values.size()<=N,"runtime-array-initializer-domain");dws_cxx_enter(Object);
    unsigned i=0;for(T item:values)dws_cxx_traits<T>::store(dws_cxx_live(dws_pointer_offset(value,i++)),item);
    for(;i<N;++i)dws_cxx_traits<T>::store(dws_cxx_live(dws_pointer_offset(value,i)),T{});
  }
  dws_cxx_array(const dws_cxx_array&)=delete;
  dws_cxx_array& operator=(const dws_cxx_array&)=delete;
  ~dws_cxx_array() {dws_cxx_leave(Object);}
  operator dws_cxx_erased() const {return dws_cxx_erased(dws_cxx_live(value));}
  dws_cxx_pointer<T> operator+(long long n) const {return dws_cxx_pointer<T>(dws_pointer_offset(dws_cxx_live(value),n));}
  dws_cxx_reference<T> operator[](long long n) const {return dws_cxx_reference<T>(dws_pointer_offset(dws_cxx_live(value),n));}
};
'''


def render_header(api,dispatch,project,declarations,abi,allocations,thread):
    need(type(thread) is int and thread in (0,1),'explicit admitted runtime thread required')
    api['validate_abi'](abi);need(declarations==api['inventory'](project),'fresh exact 27-declaration source inventory required')
    _routes,instances=dispatch['render_routes'](api,declarations,abi)
    need(len(instances)==132,'complete fixed runtime route matrix required')
    lookup={(r['name'],r['formal_arity'],r['dtype']):r for r in instances}
    traits=[]
    for dtype,(ctype,suffix,width,alignment) in enumerate(zip(TYPE_KEYS,SUFFIX,abi['sizes'],abi['alignments'])):
        traits.append('template<> struct dws_cxx_traits<'+ctype+'> {static constexpr unsigned dtype='+str(dtype)+'u;'
            'static_assert(sizeof('+ctype+')=='+str(width)+' && alignof('+ctype+')=='+str(alignment)+',"runtime-scalar-ABI");'
            'static '+ctype+' load(dws_pointer p) {return dws_cpu_load_'+suffix+'(dws_cxx_thread,p,0);}'
            'static void store(dws_pointer p,'+ctype+' v) {dws_cpu_store_'+suffix+'(dws_cxx_thread,p,0,v);}};')
    enter=''.join('case '+str(i)+':dws_local_enter_'+str(i)+'_v1();break;' for i in range(len(allocations)))
    leave=''.join('case '+str(i)+':dws_local_leave_'+str(i)+'_v1();break;' for i in range(len(allocations)))
    header=BASE.replace('__ENUMS__',enum_text(project)).replace('__THREAD__',str(thread)).replace('__TRAITS__','\n'.join(traits)).replace('__ENTER__',enter).replace('__LEAVE__',leave)
    wrappers=[];inventory=[]
    for row in declarations:
        name=row['name'];result=row['returns'].replace('volatile ','').strip()
        if '*' in result:result='dws_cxx_address<T>' if name=='get_noncacheable_tile_pointer' else 'dws_cxx_pointer<T>'
        elif result=='T1':result='T'
        params=[];args=[]
        for parameter in row['parameters']:
            typ=parameter['type'].replace('volatile ','').strip();var=parameter['name']
            converted='dws_cxx_erased' if '*' in typ else 'T' if typ=='T1' else typ
            declaration=converted+' '+var
            if parameter.get('default') is not None:
                need(parameter['default']==-1,'exact default -1 required');declaration+=' = -1'
            params.append(declaration);args.append(var+'.get()' if '*' in typ else 'static_cast<int>('+var+')' if typ=='Operation_t' else var)
        prefix='template<class T> ' if row['template'] else ''
        bodies=[]
        for dtype in range(6) if row['template'] else (None,):
            route=lookup[(name,row['formal_arity'],dtype)]['c_name'];call=route+'('+','.join(['dws_cxx_thread',*args])+')'
            statement=call+';return;' if result=='void' else 'return '+result+'('+call+');' if result in ('DataType','dws_cxx_address<T>','dws_cxx_pointer<T>') else 'return '+call+';'
            if row['template']:statement=('if' if dtype==0 else 'else if')+' constexpr(std::is_same_v<T,'+TYPE_KEYS[dtype]+'>) {'+statement+'}'
            bodies.append(statement)
        if row['template']:
            bodies.append('else {return static_cast<DataType>(dws_get_data_type_other(dws_cxx_thread));}' if name=='get_data_type'
                else 'else {static_assert(!std::is_same_v<T,T>,"unadmitted-runtime-interface-type");}')
        wrappers.append(prefix+'static '+result+' '+name+'('+','.join(params)+') {'+''.join(bodies)+'}')
        inventory.append({'name':name,'formal_arity':row['formal_arity'],'template':row['template'],
            'source_line':row['line'],'source_header_sha256':row['header_sha256'],'source_body_sha256':row['body_sha256']})
    need(len(wrappers)==27 and len({r['name'] for r in inventory})==26,'complete runtime 26-name/27-declaration matrix required')
    return header+'\n'+'\n'.join(wrappers)+'\n',inventory,instances


def recheck_receiver(receiver_api,receiver,policy_pin):
    need(type(receiver) is dict and set(receiver)=={'binding','c_text','draw_plan','integration'},'exact prepared receiver object required')
    selected=receiver_api['Pin'].parse(policy_pin)
    prepared=receiver_api['prepare'](receiver_api['OwnedSelection'](selected))
    exact={'binding':json.loads(prepared.binding_json),'c_text':prepared.c_text,
        'draw_plan':json.loads(prepared.draw_plan_json),'integration':json.loads(prepared.integration_plan_json)}
    need(receiver==exact,'fresh physical receiver selection/preparation differs')
    return receiver_api['document'](selected)


def _projection(whole,project,*,source_path,normalized_tu,caller,declarations,abi,atlas,allocations,thread,
                unit_preparation,statement_preparation,assertion_header_pin,receiver,receiver_policy_pin):
    whole,project=Path(whole).resolve(strict=True),Path(project).resolve(strict=True)
    source_raw,source_pin=file_pin(Path(source_path),SOURCE_SHA);source=source_raw.decode('ascii')
    modules={};pins=[]
    for name in PINS:modules[name],pin=component(whole,name);pins.append(pin)
    api=modules['whole_interface_v4.py'];dispatch=modules['source_dispatch_v3.py'];staging=modules['source_argument_staging_v2.py']
    statement=modules['source_statements_v2.py'];receiver_api=modules['receiver-state-draws-v2/receiver_state_draws_v2.py']
    need(normalized_tu.get('kind')=='TranslationUnitDecl','one complete actual original TU required')
    need(declarations==api['inventory'](project),'actual two-header declaration binding changed')
    need(api['HEADER_PINS']==HEADER_PINS,'exact source header pin matrix differs')
    header_pins=[file_pin(project/'apps/dx100/benchmarks/API'/name,expected)[1] for name,expected in HEADER_PINS.items()]
    need(unit_preparation.get('normalized_full_tu_sha256')==digest(normalized_tu)
        and unit_preparation.get('original_source_sha256')==source_pin['sha256'],'full original unit/source receipt differs')
    owners=[n for n in walk(normalized_tu) if n.get('kind')=='FunctionDecl' and n.get('mangledName')==caller
        and any(c.get('kind')=='CompoundStmt' for c in n.get('inner',[]))]
    need(len(owners)==1 and owners[0].get('name')=='whole_interface_source_fixture','one exact first-scope original caller required')
    owner=owners[0];body=next(n for n in owner['inner'] if n.get('kind')=='CompoundStmt')
    need(owner.get('loc',{}).get('_file')==str(Path(source_path).resolve()),'actual original physical caller differs')
    receiver_policy=recheck_receiver(receiver_api,receiver,receiver_policy_pin)
    binding=receiver['binding'];need(sha(receiver['c_text'].encode())==binding['receiver_c_sha256']
        and digest(receiver['draw_plan'])==binding['harness_draw_plan_sha256']
        and digest(receiver['integration'])==binding['integration_plan_sha256'],'receiver/draw/linkage bytes differ')
    need(receiver_policy['full_tu_canonical_sha256']==digest(normalized_tu),'selected receiver/original full TU identity differs')
    selected_inputs=binding['input_pins']
    need(selected_inputs['source']==source_pin and selected_inputs['assertion_header']==assertion_header_pin
        and selected_inputs['capture_receipt']['sha256']==unit_preparation['compiler_capture_receipt_sha256'],
        'receiver original source/assertion/compiler receipt differs')
    for name,expected in (('source_atlas',atlas),('statement_preparation',statement_preparation),('abi_observation',unit_preparation['abi_observation'])):
        need(receiver_api['document'](receiver_api['Pin'].parse(selected_inputs[name]))==expected,'selected receiver source observation differs: '+name)
    need(unit_preparation['abi_observation']['abi']==abi,'selected receiver/runtime scalar ABI differs')
    need(receiver['integration']['allocation_hooks']==allocations,'receiver and source runtime lifetimes differ')
    receiver_api['check_allocations'](allocations,atlas,source_pin['sha256'],2 if thread==1 else 1)
    need(all(row['caller']==caller and row['allocation_thread']==thread for row in allocations),'first source runtime allocation/thread binding differs')
    # Re-execute the complete original-body validator, using emitted C only as
    # a certificate comparison. None of that C text becomes this counterpart.
    stager=staging['Stager'](api,dispatch,normalized_tu,caller=caller,source_path=source_path,source_text=source,
        declarations=declarations,abi=abi,atlas=atlas,live_local_ids=set(),thread='owned_thread')
    checked=statement['Lowerer'](stager,unit_preparation,assertion_header_pin=assertion_header_pin).lower()
    need(checked==statement_preparation,'fresh complete original statement/CPU/assertion/lifetime certificate differs')
    need(type(allocations) is list and len(allocations)==2,'two exact original array objects required')
    locals={n.get('id'):n for n in walk(body) if n.get('kind')=='VarDecl'}
    need(len(locals)==len([n for n in walk(body) if n.get('kind')=='VarDecl']),'unique local declaration identities required')
    edits=[];array_names=set();pointer_names=set();calls={tuple(row['call_range']):row for row in unit_preparation['calls'] if row['caller_mangled']==caller}
    include='#include "MAA_gem5.hpp"';need(source.count(include)==1,'one exact original API include required')
    start=source.index(include);edits.append({'begin':start,'end':start+len(include),'before':include,
        'after':'#include "dws_original_runtime.hpp"','kind':'api-include','declaration_id':None})
    for row,obj in zip(allocations,atlas['objects']):
        node=locals.get(row['local_id']);need(node is not None and digest(node)==row['declaration_sha256'],'actual source array declaration differs')
        begin,end=api['_span'](node);need([begin,end]==row['declaration_range'] and row['scope_end_offset']==api['_span'](body)[1],
            'actual source declaration/lifetime range differs')
        name=node['name'];array_names.add(name);text=source[begin:end]
        match=re.match(r'(std::(?:u?int32_t))\s+'+re.escape(name)+r'\s*\[\s*2\s*\]',text)
        need(match and obj['extent']==2 and obj['dtype']==(0 if match[1]=='std::uint32_t' else 1),'exact original typed array prefix required')
        prefix=match[0];replacement='dws_cxx_array<'+match[1]+',2,'+str(row['object_index'])+'> '+name
        edits.append({'begin':begin,'end':begin+len(prefix),'before':prefix,'after':replacement,
            'kind':'ordinary-array-declarator','declaration_id':node['id']})
    for node in locals.values():
        typ=node.get('type',{}).get('qualType','')
        if '*' not in typ:continue
        name=node.get('name');pointer_names.add(name)
        call_nodes=[n for n in walk(node) if n.get('kind')=='CallExpr']
        need(len(call_nodes)==1,'one exact source getter initializes each runtime descriptor')
        call=call_nodes[0];record=calls.get(tuple(api['_span'](call)))
        need(record is not None and record['name'] in {'get_cacheable_tile_pointer','get_noncacheable_tile_pointer'},'closed source pointer getter required')
        fresh=api['recheck_binding'](record,normalized_tu,caller=caller,call_range=record['call_range'],source_path=source_path,source_text=source,declarations=declarations,abi=abi)
        dtype=fresh['dtype'];need(dtype in (0,1),'first runtime fixture pointer types are uint32/int32')
        begin,end=api['_span'](node);text=source[begin:end]
        match=re.match(r'(volatile\s+)?(std::(?:u?int32_t))\s*\*\s*'+re.escape(name),text)
        opaque=record['name']=='get_noncacheable_tile_pointer'
        need(match and bool(match[1])==opaque and match[2]==('std::uint32_t' if dtype==0 else 'std::int32_t'),'actual pointer source declarator differs')
        prefix=match[0];replacement=('dws_cxx_address<' if opaque else 'dws_cxx_pointer<')+match[2]+'> '+name
        edits.append({'begin':begin,'end':begin+len(prefix),'before':prefix,'after':replacement,
            'kind':'noncacheable-address-declarator' if opaque else 'cacheable-pointer-declarator','declaration_id':node['id']})
    need(array_names==ARRAYS and pointer_names==POINTERS and len(edits)==9,'complete first-scope runtime declaration-edit census required')
    projected=check_edits(source,edits)
    # API calls and assert expressions remain byte-identical original slices.
    for begin,end in calls:
        need(not any(e['begin']<end and begin<e['end'] for e in edits),'runtime edit overlaps an original API expression')
    for site in statement_preparation['assertions']:
        offset=site['offset'];need(not any(e['begin']<=offset<e['end'] for e in edits),'runtime edit overlaps original assertion')
    header,inventory,instances=render_header(api,dispatch,project,declarations,abi,allocations,thread)
    manifest={'schema':'whole-interface-source-cxx-projection-edits-1','original_source':source_pin,
        'original_normalized_TU_sha256':digest(normalized_tu),'caller_mangled':caller,'caller_declaration_id':owner['id'],
        'edits':sorted(edits,key=lambda row:row['begin']),'exact_textual_inverse':True,'original_control_scalar_API_and_assertion_tokens_preserved':True,
        'original_statement_certificate_sha256':digest(statement_preparation),'receiver_binding_sha256':digest(binding),
        'receiver_policy_pin':receiver_policy_pin,
        'source_atlas_sha256':digest(atlas),'abi_sha256':digest(abi),'allocation_records_sha256':digest(allocations),
        'runtime_header_sha256':sha(header.encode()),'projected_original_file_sha256':sha(projected.encode()),
        'generated_lowered_C_body_used':False,'actual_compiler_or_runtime_inferred':False}
    cxx='#line 1 '+json.dumps(str(source_path))+'\n'+projected
    identity={'schema':'whole-interface-source-cxx-runtime-1','components':pins,'source_headers':header_pins,'runtime_header_sha256':sha(header.encode()),
        'cxx_source_sha256':sha(cxx.encode()),'edit_manifest_sha256':digest(manifest),'source_declarations':inventory,
        'source_route_instances':instances,'thread':thread,'harness_draw_plan_sha256':binding['harness_draw_plan_sha256'],
        'shared_TCB':['owned physical/object mapping','owned concrete memory/MMIO/value model','checked source declarator/API projection',
            'selected original and projected C++ compiler/runtime profiles'],
        'independent_from_lowered_C_expression_execution':True,'raw_MMIO_execution':False,'hardware_body_theorem_required':False,
        'actual_compile_or_scientific_execution':False,'public_admission':False}
    for pin in [*pins,*header_pins]:file_pin(pin['path'],pin['sha256'])
    file_pin(source_path,source_pin['sha256'])
    recheck_receiver(receiver_api,receiver,receiver_policy_pin)
    return {'cxx_text':cxx,'runtime_header':header,'edit_manifest':manifest,'runtime_identity':identity}


def projection(whole,project,**inputs):
    """Closed first-source preparation; malformed/unsupported inputs refuse."""
    try:return _projection(whole,project,**inputs)
    except Refused:raise
    except (OSError,TypeError,KeyError,AttributeError,ValueError,OverflowError,RecursionError) as error:
        raise Refused('unavailable, malformed or inconsistent source runtime projection input') from error


# 2026-10-16 ET. Separate fixed three-caller memory profile. The entire V3
# module above remains byte-exact, including its first3148 public API/path.
MEMORY_SOURCE_SHA='55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'
MEMORY_PINS={
 'whole_interface_v4.py':'217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8',
 'source_dispatch_v3.py':'d05d3ba716af2d88703636ffbf57bf0834acd5e59ee7ce3aebe0a72648a8b703',
 'source_argument_staging_v2.py':'79bdae72fd7b4de05771776684b5c6af275afb736313ece1df8790ae57ae6178',
 'source_statements_v2.py':'49832255fef43afa51078479770d62f01e7e539e4f71f4034e3f2648cb867738',
 'source-memory-selection-v1/source_memory_selection_v1.py':'498f1eb7a2f4e824e4ec0d484fcd0730ac2eb4bb98ab03c740e36e943a523767',
 'receiver-memory-v1/receiver_memory_v1.py':'f8cf91dee0e7b442812065b7935e176df48a417a308eb3798104b4320f654f23'}


def memory_component(whole,name):
    """Fixed immutable sources only; external metadata cannot select a module."""
    need(name in MEMORY_PINS,'unreviewed memory runtime component')
    raw,pin=file_pin(Path(whole)/name,MEMORY_PINS[name])
    namespace={'__name__':'owned_memory_cxx_projection','__file__':pin['path']}
    exec(compile(raw,pin['path'],'exec'),namespace)
    return namespace,pin


def memory_object(atlas,allocations,profile,caller,thread,api,owner):
    """One live source-local line; physical alignment is an owned input check."""
    need(type(thread) is int and thread==0 and profile['thread']==thread,
         'exact selected one-thread memory trace required')
    need(type(atlas) is dict and type(atlas.get('objects')) is list and len(atlas['objects'])==1
         and type(allocations) is list and len(allocations)==1,
         'one selected original memory array required')
    obj,row=atlas['objects'][0],allocations[0]
    need(profile['objects']==[{'name':'data','dtype':0,'extent':16,'bytes':64,
        'requires_owned_physical_alignment':64,'alignment_inferred_from_source':False}],
        'fixed u32 full-line source profile differs')
    need(type(obj.get('dtype')) is int and obj['dtype']==0 and type(obj.get('extent')) is int and obj['extent']==16
         and type(obj.get('physical_base')) is int and obj['physical_base']%64==0
         and obj.get('base_cell')==0 and obj.get('cell_ids')==list(range(16)),
         'exact16-cell u32 mapping requires independently owned64-byte physical alignment')
    need(type(row.get('object_index')) is int and row['object_index']==0
         and row.get('object_id')==obj.get('object_id') and row.get('caller')==caller
         and type(row.get('allocation_thread')) is int and row['allocation_thread']==thread,
         'selected original local allocation/caller/thread differs')
    bodies=[node for node in owner.get('inner',[]) if node.get('kind')=='CompoundStmt']
    need(len(bodies)==1,'one exact selected source body required')
    body=bodies[0]
    local_rows=[node for node in walk(body) if node.get('kind')=='VarDecl']
    locals_by_id={node.get('id'):node for node in local_rows}
    need(len(locals_by_id)==len(local_rows),'unique selected local declaration identities required')
    node=locals_by_id.get(row.get('local_id'))
    need(node is not None and node.get('name')=='data' and digest(node)==row.get('declaration_sha256')
         and api['_span'](node)==row.get('declaration_range')
         and row.get('scope_end_offset')==api['_span'](body)[1],
         'exact selected original array declaration/scope required')
    return body,locals_by_id,node


def _memory_projection(whole,project,*,source_path,normalized_tu,function,caller,declarations,abi,atlas,allocations,
                       thread,unit_preparation,statement_preparation,assertion_header_pin,receiver,receiver_policy_pin):
    whole,project=Path(whole).resolve(strict=True),Path(project).resolve(strict=True)
    raw,source_pin=file_pin(Path(source_path),MEMORY_SOURCE_SHA);source=raw.decode('ascii')
    modules={};pins=[]
    for name in MEMORY_PINS:
        modules[name],selected=memory_component(whole,name);pins.append(selected)
    api=modules['whole_interface_v4.py'];dispatch=modules['source_dispatch_v3.py']
    staging=modules['source_argument_staging_v2.py'];statement=modules['source_statements_v2.py']
    selection=modules['source-memory-selection-v1/source_memory_selection_v1.py']
    receiver_api=modules['receiver-memory-v1/receiver_memory_v1.py']
    need(api['HEADER_PINS']==HEADER_PINS and declarations==api['inventory'](project),
         'complete original two-header declaration identity differs')
    header_pins=[file_pin(project/'apps/dx100/benchmarks/API'/name,expected)[1] for name,expected in HEADER_PINS.items()]
    initial_tu_sha=digest(normalized_tu)
    cut=selection['selected_root'](api,normalized_tu=normalized_tu,source_path=source_path,
        preparation=unit_preparation,function=function,declarations=declarations,abi=abi)
    profile=cut['profile']
    need(profile==selection['profile'](function) and caller==profile['caller_mangled']
         and profile['source_sha256']==MEMORY_SOURCE_SHA and cut['original_normalized_tu_sha256']==initial_tu_sha,
         'exact memory source/caller/root selection required')
    owners=[node for node in walk(normalized_tu) if node.get('kind')=='FunctionDecl'
        and node.get('id')==cut['selected_declaration_id']]
    need(len(owners)==1 and digest(owners[0])==cut['selected_declaration_sha256'],
         'selected actual source definition differs')
    owner=owners[0]
    receiver_policy=recheck_receiver(receiver_api,receiver,receiver_policy_pin)
    need(receiver_policy['full_tu_canonical_sha256']==initial_tu_sha
         and receiver_policy['inputs']['source']==source_pin
         and receiver_policy['inputs']['assertion_header']==assertion_header_pin,
         'selected memory receiver/source/TU/assertion identity differs')
    binding=receiver['binding'];selected_inputs=binding['input_pins']
    need(selected_inputs==receiver_policy['inputs'] and selected_inputs['source']==source_pin
         and selected_inputs['assertion_header']==assertion_header_pin
         and selected_inputs['capture_receipt']['sha256']==unit_preparation['compiler_capture_receipt_sha256'],
         'memory receiver input/compiler receipt linkage differs')
    need(sha(receiver['c_text'].encode())==binding['receiver_c_sha256']
         and digest(receiver['draw_plan'])==binding['harness_draw_plan_sha256']
         and digest(receiver['integration'])==binding['integration_plan_sha256'],
         'memory receiver/draw/integration bytes differ')
    for name,expected in (('source_atlas',atlas),('statement_preparation',statement_preparation),
                         ('abi_observation',unit_preparation['abi_observation'])):
        need(receiver_api['document'](receiver_api['Pin'].parse(selected_inputs[name]))==expected,
             'exact selected memory receiver observation differs: '+name)
    need(unit_preparation['abi_observation']['abi']==abi
         and receiver['integration']['allocation_hooks']==allocations,
         'selected memory runtime ABI/allocation binding differs')
    receiver_api['check_allocations'](allocations,atlas,MEMORY_SOURCE_SHA,1)
    body,locals_by_id,array=memory_object(atlas,allocations,profile,caller,thread,api,owner)
    need(not any(node.get('kind') in {'ForStmt','WhileStmt','DoStmt'} for node in walk(body)),
         'this exact memory source profile has no original loops')
    stager=staging['Stager'](api,dispatch,normalized_tu,caller=caller,source_path=source_path,source_text=source,
        declarations=declarations,abi=abi,atlas=atlas,live_local_ids=set(),thread='owned_thread')
    checked=statement['Lowerer'](stager,unit_preparation,assertion_header_pin=assertion_header_pin).lower()
    need(checked==statement_preparation,'fresh complete selected memory body/CPU/lifetime certificate differs')
    rooted=cut['counterpart_root_source']
    need(type(rooted) is str and len(rooted)==len(source)
         and sha(rooted.encode())==cut['counterpart_root_source_sha256'],
         'selected counterpart root text differs')
    edits=[]
    include='#include "MAA_gem5.hpp"';need(rooted.count(include)==1,'one unchanged original API include required')
    begin=rooted.index(include);edits.append({'begin':begin,'end':begin+len(include),'before':include,
        'after':'#include "dws_original_runtime.hpp"','kind':'api-include','declaration_id':None})
    begin,end=api['_span'](array);array_text=source[begin:end]
    match=re.match(r'std::uint32_t\s+data\s*\[\s*16\s*\]',array_text)
    need(match is not None,'exact selected original u32 array declarator required')
    edits.append({'begin':begin,'end':begin+len(match[0]),'before':match[0],
        'after':'dws_cxx_array<std::uint32_t,16,0> data','kind':'ordinary-array-declarator','declaration_id':array['id']})
    selected_calls=[row for row in unit_preparation['calls'] if row['caller_mangled']==caller]
    calls={tuple(row['call_range']):row for row in selected_calls}
    need(digest(selected_calls)==cut['selected_API_call_binding_sha256'] and len(calls)==len(selected_calls),
         'exact selected original API call identity differs')
    pointer_names=set()
    for node in locals_by_id.values():
        if '*' not in node.get('type',{}).get('qualType',''):continue
        need(node.get('name')=='index_data','only the selected original u32 getter local is supported')
        pointer_names.add(node['name'])
        call_nodes=[child for child in walk(node) if child.get('kind')=='CallExpr']
        need(len(call_nodes)==1,'one actual original getter initializer required')
        record=calls.get(tuple(api['_span'](call_nodes[0])))
        need(record is not None and record['name']=='get_cacheable_tile_pointer',
             'fixed original cacheable getter required')
        fresh=api['recheck_binding'](record,normalized_tu,caller=caller,call_range=record['call_range'],
            source_path=source_path,source_text=source,declarations=declarations,abi=abi)
        need(type(fresh['dtype']) is int and fresh['dtype']==0,'memory getter must retain its actual u32 type')
        begin,end=api['_span'](node)
        match=re.match(r'std::uint32_t\s*\*\s*index_data',source[begin:end])
        need(match is not None,'exact selected original u32 pointer declarator required')
        edits.append({'begin':begin,'end':begin+len(match[0]),'before':match[0],
            'after':'dws_cxx_pointer<std::uint32_t> index_data','kind':'cacheable-pointer-declarator','declaration_id':node['id']})
    need(pointer_names==set(profile['pointer_locals']) and len(edits)==2+len(profile['pointer_locals']),
         'complete selected memory declaration-edit census differs')
    for begin,end in calls:
        need(not any(edit['begin']<end and begin<edit['end'] for edit in edits),
             'memory runtime edit overlaps an original API expression')
    need(statement_preparation['assertions']==[],'fixed memory callers contain no original source assertions')
    projected=check_edits(rooted,edits)
    header,inventory,instances=render_header(api,dispatch,project,declarations,abi,allocations,thread)
    manifest={'schema':'three-source-memory-cxx-projection-edits-1','original_source':source_pin,
        'original_normalized_TU_sha256':initial_tu_sha,'selected_original_root':cut,
        'caller_mangled':caller,'caller_declaration_id':owner['id'],'edits':sorted(edits,key=lambda row:row['begin']),
        'exact_textual_inverse_to_selected_root':True,'original_selected_control_scalar_API_tokens_preserved':True,
        'original_statement_certificate_sha256':digest(statement_preparation),'receiver_binding_sha256':digest(binding),
        'receiver_policy_pin':receiver_policy_pin,'source_atlas_sha256':digest(atlas),'abi_sha256':digest(abi),
        'allocation_records_sha256':digest(allocations),'physical_line_alignment':64,
        'alignment_inferred_from_source':False,'runtime_header_sha256':sha(header.encode()),
        'projected_original_file_sha256':sha(projected.encode()),'generated_lowered_C_body_used':False,
        'actual_compiler_or_runtime_inferred':False,'source_function_result_or_prediction_used_by_runtime':False}
    cxx='#line 1 '+json.dumps(str(source_path))+'\n'+projected
    identity={'schema':'three-source-memory-cxx-runtime-1','components':pins,'source_headers':header_pins,
        'runtime_header_sha256':sha(header.encode()),'cxx_source_sha256':sha(cxx.encode()),'edit_manifest_sha256':digest(manifest),
        'source_declarations':inventory,'source_route_instances':instances,'thread':thread,
        'harness_draw_plan_sha256':binding['harness_draw_plan_sha256'],
        'shared_TCB':['owned physical/object mapping','owned concrete memory/MMIO/value model',
            'checked selected-source-root/declarator/API projection','selected original and projected C++ compiler/runtime profiles'],
        'same_TU_graph_modified_or_filtered':False,'one_fresh_selected_call_per_program_required':True,
        'raw_MMIO_execution':False,'actual_compile_or_scientific_execution':False,'public_admission':False}
    need(digest(normalized_tu)==initial_tu_sha,'complete original TU changed during memory projection')
    need(selection['selected_root'](api,normalized_tu=normalized_tu,source_path=source_path,
        preparation=unit_preparation,function=function,declarations=declarations,abi=abi)==cut,
        'fresh selected original root/call closure differs after projection')
    for selected in [*pins,*header_pins]:file_pin(selected['path'],selected['sha256'])
    file_pin(source_path,MEMORY_SOURCE_SHA)
    need(recheck_receiver(receiver_api,receiver,receiver_policy_pin)==receiver_policy,
         'selected memory receiver changed after projection')
    return {'cxx_text':cxx,'runtime_header':header,'edit_manifest':manifest,'runtime_identity':identity}


def memory_projection(whole,project,**inputs):
    """Separate memory-profile entry; no arbitrary source or receiver fallback."""
    try:return _memory_projection(whole,project,**inputs)
    except Refused:raise
    except (OSError,TypeError,KeyError,AttributeError,ValueError,OverflowError,RecursionError) as error:
        raise Refused('unavailable, malformed or inconsistent selected memory runtime input') from error
