"""2026-10-16 ET. Closed source policy for one u32 stream metadata observation.

Only conditional normal return is modeled. The entry environment and event
compression assumptions are explicit, owned and pending ticket59 review.
A valid policy is not itself the compiler/source correspondence certificate.
"""
from pathlib import Path
import re
from swdb import artifacts
from swdb.dx100_size_source import SOURCE_PINS as SIZE_SOURCE_PINS
from swdb.dx100_stream_model import normal_return_model

LAYOUT = 'dx100-one-u32-stream-partial-v1'
KIND = 'dx100-one-u32-stream-v1'
OWNER = 'Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'
ENTRY = {'kind': 'isolated-one-u32-stream-core0-v1', 'core': 0, 'tiles': 32, 'tile_words': 16384, 'register_words': 32, 'guest_address_bits': 64, 'byte_order': 'little', 'rf_i32': {'0': 0, '1': 1, '2': 1}, 'epoch': 'after-constructor-and-configured-quiescent-RF-before-one-command', 'input': {'symbol': 'stream_input', 'bytes': 64, 'alignment': 64, 'nonzero_guest_base': True, 'storage': 'initialized C static array', 'region': 'registered normal-memory line disjoint from MMIO', 'translation': 'stable synchronous fault-free64-byte mapping', 'visibility': 'coherent stable full physical line; no competing CPU/device writes from any core through return'}, 'commands': 'exactly one u32 stream load, no condition or competing command'}
BOOT_STATEMENT = 'This synthetic core0 unit starts with the pinned32-tile/16384-word SPD constructor state and configured4-core MMIO mapping, quiescent initialized signed-int32 RF values0/1/1 at registers0/1/2, and one registered initialized64-byte aligned normal-memory input line whose virtual base is nonzero, with stable synchronous fault-free translation and coherent no-interference visibility through normal return. These are conditional environment/source-model premises owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59); alloc/init do not establish them and arbitrary callers or physical boot are not established.'
NORMAL_RETURN_STATEMENT = 'All three MMIO helpers and this source unit are interpreted only on normal return; no termination, fairness or hardware-liveness theorem is claimed.'
COMPRESSION_STATEMENT = 'An acknowledgement establishes dispatch, not completion or still-unfinished hardware. In this isolated no-observation/no-interference caller, unobserved device events may be represented by a logically uncovered command and settled only at the returned real ready read; this source-model correspondence is owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59). All-schedule event refinement and contract/body agreement remain unverified owned TCB duties, not conclusions of finite native prefixes.'

SOURCE_PINS = {**SIZE_SOURCE_PINS,
    'IF.hh':'9dee4c4803a1780a41fb30b760775169000785019e6f5848689fc3f3034a1795',
    'StreamAccess.cc':'5fe78a94f0d690396cdfbcdd9b0082e57cbdb4a6b445a7282b2533a33852d47b',
    'StreamAccess.hh':'9ac9feb68adb525ca2d5c7d6e9046b5b0e399ad4c63a718fcca8f78cd521a3ec',
    'Tables.hh':'5ea6a7caff7ca690aa9ce19096c0e686dfa52716e4dbf19d17348c9235011b43',
    'Tables.cc':'9bd8aa4103fb6e7617fdd4c514a917329b8e7b8345738ed6e5d82f818df7dfa6',
}
PROTOTYPES = {
 'maa_stream_load':'void maa_stream_load_unsigned_int(unsigned int *data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile)',
 'wait_ready':'void wait_ready(int SPD_id)',
 'get_tile_size':'volatile unsigned short get_tile_size(int SPD_id)',
}

class Refused(ValueError):
    pass


def stream_layout(data):
    return (data.get('model') or {}).get('layout') == LAYOUT


def _exact(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected,dict):
        return set(actual)==set(expected) and all(_exact(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):
        return len(actual)==len(expected) and all(_exact(a,b) for a,b in zip(actual,expected))
    return actual==expected


def policy(library, definition):
    """Validate an explicit scoped entry; never infer it from a caller or allocation."""
    try:
        if not isinstance(definition,dict) or not _exact(definition.get('entry'),ENTRY):
            raise Refused('explicit isolated stream entry certificate is missing, changed or outside its closed domain')
        if set(definition)!={'kind','call','entry','sources'} or definition['kind']!=KIND or definition['call'] not in PROTOTYPES:
            raise Refused('isolated stream requires the closed source/call policy')
        if not isinstance(definition['sources'],list) or len(definition['sources'])!=len(SOURCE_PINS):
            raise Refused('isolated stream requires all distinct immutable source pins')
        pins=[]
        for source in definition['sources']:
            library._pin(source)
            path=library.resolve(source).resolve()
            pin={'path':str(path),'bytes':path.stat().st_size,'sha256':artifacts.file_hash(path)}
            if pin['sha256']!=SOURCE_PINS.get(path.name) or any(Path(p['path']).name==path.name for p in pins):
                raise Refused('isolated stream has a changed or repeated immutable source')
            pins.append(pin)
        return {'kind':KIND,'call':definition['call'],'entry':definition['entry'],'sources':pins,
                'termination_policy':normal_return_model()['termination_policy']}
    except (KeyError,TypeError,ValueError,OSError,AttributeError) as exc:
        return {'refused':str(exc)}


def check(library,data,texts,error):
    rows=[r for r in data.get('calls',[]) if isinstance(r,dict)]
    definitions=[]
    for row in rows:
        variants=row.get('instances')
        candidates=[row,*(variants if isinstance(variants,list) else [])]
        definitions += [v['definition'] for v in candidates if isinstance(v,dict) and isinstance(v.get('definition'),dict)]
    if not stream_layout(data):
        if any(d.get('kind')==KIND for d in definitions):
            error('calls.definition','isolated stream definition requires its closed partial-normal-return layout')
            return False
        return True
    valid=True
    def refuse(message):
        nonlocal valid
        valid=False;error('model.layout',message)
    active=[r for r in rows if r.get('supported') is not False]
    if {r.get('call') for r in active}!=set(PROTOTYPES) or len(active)!=3:
        refuse('isolated stream admits exactly one u32 stream, its real wait and size observation')
        return False
    clean=lambda text:re.sub(r'/\*.*?\*/|//[^\n]*|\s+','',text,flags=re.S)
    model=normal_return_model()
    for row in active:
        name=row['call'];variant=row
        if name=='maa_stream_load':
            instances=row.get('instances')
            if not isinstance(instances,list) or len(instances)!=1 or not isinstance(instances[0],dict):
                refuse('isolated stream requires one explicit u32 source instance');continue
            variant=instances[0]
            if variant.get('arguments')!=['unsigned int'] or type(variant.get('arity')) is not int or variant['arity']!=6:
                refuse('isolated stream requires its exact u32 six-argument source instance')
        elif 'instances' in row:
            refuse('isolated stream wait/size are direct source calls')
        selected=policy(library,variant.get('definition'))
        if 'refused' in selected:refuse(selected['refused'])
        elif selected['call']!=name:refuse('isolated stream source certificate names another call')
        key='maa_stream_load_unsigned_int' if name=='maa_stream_load' else name
        if variant.get('prototype')!=PROTOTYPES[name] or clean(variant.get('contract',''))!=clean(model['contracts'][key]):
            refuse('isolated stream needs the exact partial-return source ABI and metadata contract')
        for rule_id,statement in (('stream_epoch',BOOT_STATEMENT),('stream_normal_return',NORMAL_RETURN_STATEMENT),('stream_event_compression',COMPRESSION_STATEMENT)):
            rules=[r for r in data.get('rules',[]) if isinstance(r,dict) and r.get('id')==rule_id]
            if (len(rules)!=1 or rules[0].get('statement')!=statement or rules[0].get('record_assumption') is not True
                    or rules[0].get('assumed')!={'owner':OWNER} or rule_id not in row.get('rules',[])):
                refuse('isolated stream requires each exact owned entry/normal-return/event premise in every verdict')
    if any(clean(texts.get(k,'')) for k in ('ghost.acsl','model.logic')):
        refuse('isolated stream adds no ghost axioms or desired value premises')
    for key,want in (('model.state',model['state']),('model.c',model['c'])):
        if key in texts and clean(texts[key])!=clean(want):refuse('isolated stream metadata model changed')
    if data.get('constants') or data.get('queries') or data.get('wp') or not data.get('declaration_inventory'):
        refuse('isolated stream requires the full declaration inventory and no extra constants/queries/WP premises')
    return valid

CANONICAL_CALLER = ('int trust_fixture() { maa_stream_load<uint32_t>(stream_input,0,1,2,0,-1); '
                    'wait_ready(0); int observed=(int)get_tile_size(0); return observed; }')


def _clean(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*|\s+','',text,flags=re.S)


def _body(text, signature):
    at=text.index(signature);begin=text.index('{',at);depth=0
    for end in range(begin,len(text)):
        if text[end]=='{':depth+=1
        elif text[end]=='}':
            depth-=1
            if depth==0:return text[begin:end+1]
    raise Refused('immutable stream source body is not closed')


def _expected_bodies(header):
    return {name:_body(header,signature).replace('NA_UINT8','0xFF') for name,signature in (
        ('maa_stream_load','inline void maa_stream_load('),
        ('wait_ready','void wait_ready('),('get_tile_size','inline volatile uint16_t get_tile_size('),
        ('get_data_type','DataType get_data_type('))}


def _parse_dump(text):
    import json
    decoder=json.JSONDecoder();nodes=[];at=0
    while True:
        at=text.find('{',at)
        if at<0:return nodes
        node,at=decoder.raw_decode(text,at);nodes.append(node)


def _selected_frozen_body(nodes,name,tokens,*,template=False):
    families=[n for n in nodes if n.get('name')==name and n.get('kind')==('FunctionTemplateDecl' if template else 'FunctionDecl')]
    if len(families)!=1:raise Refused('stream frozen source has no unique global family '+name)
    functions=[n for n in families[0].get('inner',[]) if n.get('kind')=='FunctionDecl'] if template else families
    # The template pattern and selected instantiation have the same source body;
    # bind the one unsigned-int specialization, not a context-dependent overload.
    if template:
        functions=[n for n in functions if any(c.get('kind')=='TemplateArgument' and
            (c.get('type') or {}).get('qualType')=='unsigned int' for c in n.get('inner',[]))]
    if len(functions)!=1:raise Refused('stream frozen source has no unique selected instance '+name)
    function=functions[0]
    bodies=[n for n in function.get('inner',[]) if n.get('kind')=='CompoundStmt']
    if len(bodies)!=1:raise Refused('stream frozen selected definition has no single body '+name)
    points=[(bodies[0].get('range') or {}).get(k,{}) for k in ('begin','end')]
    if any('offset' not in p or 'spellingLoc' in p or 'expansionLoc' in p for p in points):
        raise Refused('stream frozen selected body has indirect source locations '+name)
    begin,end=points[0]['offset'],points[1]['offset']+points[1]['tokLen']
    if type(begin) is not int or type(end) is not int or not 0<=begin<end<=len(tokens.encode()):
        raise Refused('stream frozen selected body has invalid source extent')
    return {'begin':begin,'end':end,'body':tokens.encode()[begin:end].decode(),
            'function_type':function.get('type',{}).get('qualType'),
            'mangled':function.get('mangledName')}


def _check_frozen_bodies(tokens,body_bindings,sources):
    header=next(Path(p['path']).read_text() for p in sources if Path(p['path']).name=='MAA_gem5.hpp')
    expected={**_expected_bodies(header),'trust_fixture':_body(CANONICAL_CALLER,'int trust_fixture(')}
    if set(body_bindings)!=set(expected):raise Refused('stream frozen source body census changed')
    for name,binding in body_bindings.items():
        begin,end=binding['begin'],binding['end']
        text=tokens.encode()[begin:end].decode()
        if text!=binding['body'] or _clean(text)!=_clean(expected[name]):
            raise Refused('stream effective source body differs from immutable closed source: '+name)
    return expected


def _check_ir(module):
    from swdb.dx100_size_source import _function_ir,_check_getter_ir
    getter,flow,addresses=_check_getter_ir(module)
    stream,body=_function_ir(module,'__swdb_dx100_stream_certificate')
    if not re.search(r'void @__swdb_dx100_stream_certificate\(ptr\b',stream):
        raise Refused('stream source ABI is not void(u32 pointer)')
    lines=[re.sub(r', ![A-Za-z_][\w.]* !\d+','',s.strip()) for s in body.splitlines()
           if s.strip() and not re.match(r'^\w+:',s.strip())]
    patterns=[
      r'(?P<first>%[\w.]+) = load ptr, ptr @INSTR_opcode_datatype_optype_tdst1_tdst2, align 8',
      r'store volatile i64 16711935, ptr (?P<first>%[\w.]+), align 8',
      r'(?P<second>%[\w.]+) = load ptr, ptr @INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc, align 8',
      r'store volatile i64 -4294900993, ptr (?P<second>%[\w.]+), align 8',
      r'(?P<raw>%[\w.]+) = ptrtoint ptr (?P<input>%[\w.]+) to i64',
      r'(?P<third>%[\w.]+) = load ptr, ptr @INSTR_baseaddr, align 8',
      r'store volatile i64 (?P<raw>%[\w.]+), ptr (?P<third>%[\w.]+), align 8',
      r'(?:tail )?call void asm sideeffect "mfence;", "(?:~\{dirflag\},~\{fpsr\},~\{flags\})?"\(\)[^\n]*',
      r'ret void',
    ]
    captures={}
    if len(lines)!=len(patterns):raise Refused('stream compiled MMIO operation census differs: '+body)
    for line,pattern in zip(lines,patterns):
        match=re.fullmatch(pattern,line)
        if match is None:raise Refused('stream compiled MMIO operation differs: '+line+'; complete function '+body)
        for key,value in match.groupdict().items():
            if key in captures and captures[key]!=value:raise Refused('stream compiled MMIO SSA flow differs')
            captures[key]=value
    argument=re.search(r'@__swdb_dx100_stream_certificate\(ptr[^,)]* (%[\w.]+)\)',stream)
    if argument is None or argument[1]!=captures['input']:raise Refused('stream packet base does not use original input pointer')
    # The real wait is a volatile metadata read plus fence, never a demonic
    # logical query. Its return says nothing about how long hardware took.
    wait,wait_body=_function_ir(module,'__swdb_dx100_wait_certificate')
    expected=getter.replace('__swdb_dx100_size_certificate','__swdb_dx100_wait_certificate').replace('@SPD_size_noncacheable','@SPD_ready_noncacheable')
    # void wait omits the final volatile local load, but retains the original
    # volatile local store and lifetime interval around its fence.
    expected=re.sub(r'[^\n]* = load volatile i16, ptr [^\n]+\n(?=\s*call void @llvm\.lifetime\.end)', '',expected)
    expected=re.sub(r'ret i16 %[^\s]+','ret void',expected)
    # Function attributes differ between void and uint16; compare bodies only.
    expected_body=expected[expected.index('{')+1:expected.rindex('}')]
    normalize=lambda b:re.sub(r'\s+','',re.sub(r', ![A-Za-z_][\w.]* !\d+','',b))
    if normalize(wait_body)!=normalize(expected_body):
        raise Refused('stream real ready-read/fence operation differs: '+wait_body+'; expected '+expected_body)
    globals_found=[g.replace(' = dso_local global ',' = global ') for g in re.findall(r'^@stream_input =[^\n]*',module,re.M)]
    allowed_globals={
        '@stream_input = global <{ i32, [15 x i32] }> <{ i32 7, [15 x i32] zeroinitializer }>, align 64',
        '@stream_input = global [16 x i32] ['+', '.join(['i32 7']+['i32 0']*15)+'], align 64',
    }
    if len(globals_found)!=1 or globals_found[0] not in allowed_globals:
        raise Refused('stream original static input must retain its initialized64-byte extent and alignment: '+str(re.findall(r'^@stream_input =[^\n]*',module,re.M)))
    return {'stream':stream,'wait':wait,'size':getter,'stream_ssa':captures,'size_ssa':flow,'mmio_addresses':addresses}


def certify(unit,declaration,selected,caller,*,standard,timeout):
    """Bind original preprocessing, selected source bodies, ABI and MMIO operations.

    This closes compiler/source identity only. The source event-projection
    refinement remains an explicitly owned pending duty, not a theorem from IR.
    """
    import hashlib,json,shlex,subprocess,tempfile
    from swdb import stdlib_provenance
    if 'refused' in selected:raise Refused(selected['refused'])
    headers={Path(p['path']).name:p for p in selected['sources']}
    name=selected['call'];loc=declaration.get('loc') or {}
    if (loc.get('spellingLoc') or loc.get('expansionLoc') or
        Path(loc.get('_file',loc.get('file',''))).resolve()!=Path(headers['MAA_gem5.hpp']['path'])):
        raise Refused('stream call does not originate directly in the immutable MMIO header')
    location=caller.get('loc') or {}
    if (caller.get('name')!='trust_fixture' or caller.get('type',{}).get('qualType')!='int ()'
        or location.get('spellingLoc') or location.get('expansionLoc')
        or Path(location.get('_file',location.get('file',''))).resolve()!=unit.source.resolve()):
        raise Refused('stream admits only the direct unchanged closed source caller')
    cache=getattr(unit,'_dx100_one_stream_certificate',None)
    if cache is not None:return {**cache,'call':name,'source_mangled':declaration.get('mangledName')}
    runtime=stdlib_provenance.runtime_identity(unit.tool);source_hash=unit.source_digest
    def pin(path):
        path=Path(path).resolve();return {'path':str(path),'bytes':path.stat().st_size,'sha256':artifacts.file_hash(path)}
    def unchanged():
        if artifacts.file_hash(unit.source)!=source_hash or any(pin(p['path'])!=p for p in selected['sources']):
            raise Refused('stream physical source changed during source binding')
    def run(command):
        try:result=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
        except (OSError,subprocess.SubprocessError) as exc:raise Refused('stream compiler binding did not finish: '+str(exc)) from None
        if result.returncode:raise Refused('stream compiler binding refused: '+result.stderr[-1200:])
        return result.stdout
    unchanged()
    probe=('\nextern "C" void __swdb_dx100_stream_certificate(unsigned int *p) { ::maa_stream_load<unsigned int>(p,0,1,2,0,-1); }\n'
           'extern "C" void __swdb_dx100_wait_certificate(int id) { ::wait_ready(id); }\n'
           'extern "C" unsigned short __swdb_dx100_size_certificate(int id) { return ::get_tile_size(id); }\n')
    commands=[];bindings={}
    with tempfile.TemporaryDirectory(prefix='swdb-dx100-stream-') as folder:
        path=Path(folder)/'probe.ii';dep=Path(folder)/'original.d'
        pre=[*unit.tool.command,'-x','c++','-std='+standard,'-fopenmp','-E','-MD','-MF',str(dep),'-I'+str(unit.source.parent)]
        pre+=['-I'+str(p) for p in unit.includes]+['-D'+d for d in unit.defines]+[str(unit.source)]
        tokens=run(pre)
        inputs=[pin(p) for p in sorted(set(shlex.split(dep.read_text().replace('\\\n','').split(':',1)[1])))]
        path.write_text(tokens+probe)
        # Original preprocessing is frozen before any optimization or appended
        # probe. Dump offsets select real body tokens, not a matching string lure.
        for function in ('maa_stream_load','wait_ready','get_tile_size','get_data_type','trust_fixture'):
            cmd=[*unit.tool.command,'-x','c++-cpp-output','-std='+standard,'-fopenmp','-fsyntax-only','-Xclang','-ast-dump=json','-Xclang','-ast-dump-filter='+function,str(path)]
            dumped=run(cmd);commands.append(cmd)
            bindings[function]=_selected_frozen_body(_parse_dump(dumped),function,tokens,template=function in ('maa_stream_load','get_data_type'))
        _check_frozen_bodies(tokens,bindings,selected['sources'])
        command=[*unit.tool.command,'-x','c++-cpp-output','-std='+standard,'-fopenmp','-O2','-S','-emit-llvm','-o','-',str(path)]
        module=run(command);operations=_check_ir(module)
        if any(pin(p['path'])!=p for p in inputs) or stdlib_provenance.runtime_identity(unit.tool)!=runtime:
            raise Refused('stream compiler input/runtime changed during binding')
    unchanged();digest=lambda text:hashlib.sha256(text.encode()).hexdigest()
    certificate={**selected,'source_path':str(unit.source.resolve()),'source_sha256':source_hash,
      'source_mangled':declaration.get('mangledName'),'compiler_inputs':inputs,'runtime_identity':runtime,
      'preprocess_command':pre,'body_dump_commands':commands,'compiler_command':command,'body_bindings':bindings,
      'preprocessed_source':tokens,'preprocessed_source_sha256':digest(tokens),'probe_source':probe,'probe_source_sha256':digest(probe),
      'llvm_module':module,'llvm_module_sha256':digest(module),'operations':operations,
      'boot_statement':BOOT_STATEMENT,'normal_return_statement':NORMAL_RETURN_STATEMENT,
      'pending_source_refinement':COMPRESSION_STATEMENT}
    unit._dx100_one_stream_certificate=certificate
    return certificate


def bindings(lowering):
    return [row['semantic_source'] for row in getattr(lowering,'summaries',())
            if row.get('semantic_source',{}).get('kind')==KIND]


def recheck(lowering):
    import hashlib
    checked=[]
    for certificate in bindings(lowering):
        try:
            if (certificate['kind']!=KIND or certificate['call'] not in PROTOTYPES
                    or not _exact(certificate['entry'],ENTRY)
                    or certificate['boot_statement']!=BOOT_STATEMENT
                    or certificate['normal_return_statement']!=NORMAL_RETURN_STATEMENT
                    or certificate['pending_source_refinement']!=COMPRESSION_STATEMENT):
                raise Refused('stream source/entry/normal-return/refinement premise changed')
            for text,digest in (('preprocessed_source','preprocessed_source_sha256'),('probe_source','probe_source_sha256'),('llvm_module','llvm_module_sha256')):
                if hashlib.sha256(certificate[text].encode()).hexdigest()!=certificate[digest]:
                    raise Refused('stream frozen compiler evidence changed')
            if artifacts.file_hash(certificate['source_path'])!=certificate['source_sha256']:
                raise Refused('stream original source changed')
            for pin in [*certificate['sources'],*certificate['compiler_inputs']]:
                path=Path(pin['path'])
                if path.stat().st_size!=pin['bytes'] or artifacts.file_hash(path)!=pin['sha256']:
                    raise Refused('stream physical source/compiler input changed')
            if len(certificate['sources'])!=len(SOURCE_PINS) or {Path(p['path']).name:p['sha256'] for p in certificate['sources']}!=SOURCE_PINS:
                raise Refused('stream immutable source family changed')
            _check_frozen_bodies(certificate['preprocessed_source'],certificate['body_bindings'],certificate['sources'])
            if _check_ir(certificate['llvm_module'])!=certificate['operations']:
                raise Refused('stream compiled operation metadata changed')
            checked.append({k:certificate[k] for k in ('kind','call','entry','source_sha256','preprocessed_source_sha256','llvm_module_sha256','sources','compiler_inputs')})
        except (KeyError,TypeError,AttributeError,OSError,UnicodeError) as exc:
            raise Refused('stream source certificate unavailable: '+str(exc)) from None
    return checked

PARTIAL_SUBJECT = 'partial_library_summary'
PARTIAL_CONTRACT = 'contract.dx100_stream_partial_fixture.v1'
PARTIAL_METHOD = 'method.dx100-stream-partial-fixture-v1'


def unit_policy(library,entry):
    """A distinct original partial unit, never an overlay on a total contract.

    Its new subject kind cannot satisfy the existing library_summary dependency
    reader. The contract's own content hash includes this explicit policy and
    the exact semantics pin. No termination or liveness result is asserted.
    """
    unit=entry.get('proof_unit') or {}
    declared=unit.get('correctness_policy')
    ident='semantics.dx100_stream_fixture_0_2'
    data=library.get(ident)
    if (entry.get('id')!=PARTIAL_CONTRACT or entry.get('version')!='0.1'
            or unit.get('function')!='trust_fixture' or not isinstance(data,dict) or not stream_layout(data)
            or ident not in library.files):
        raise Refused('partial-normal-return proof requires the distinct closed partial contract/unit version')
    expected={'kind':'partial-normal-return-v1','source_policy':KIND,
              'semantics':{'id':ident,'sha256':artifacts.file_hash(library.files[ident])}}
    if not _exact(declared,expected):
        raise Refused('partial-normal-return proof requires an explicit original unit correctness_policy with exact semantics pin')
    return declared
