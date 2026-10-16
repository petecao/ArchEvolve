"""2026-10-16 ET. Closed synthetic fresh-SPD entry projection for the size getter.

The constructor projection is inert until a source/epoch policy admits it. It
never establishes that an arbitrary caller starts at this synthetic boot epoch.
"""

LAYOUT = 'dx100-fresh-spd-size-v1'
CERTIFICATE_KIND = 'synthetic-fresh-spd-core0-v1'
BOOT_CERTIFICATE = {
    'kind': CERTIFICATE_KIND, 'core': 0, 'tiles': 32, 'tile_words': 16384,
    'guest_address_bits': 64, 'byte_order': 'little',
    'epoch': 'after-constructor-and-address-setup-before-any-command',
}
BOOT_STATEMENT = (
    'This synthetic fixture begins on core0 immediately after one pinned SPD constructor has completed '
    'with 32 tiles and 16,384 words per tile, and pinned 4-core MMIO-address setup has configured its globals, before commands or other accesses modify '
    'that instance. This is a conditional environment/source-model premise owned by the Probata '
    'proof-semantics maintainer, pending Yan-Ru freeze review (59); arbitrary callers and physical boot '
    'are not established. alloc_MAA/init_MAA do not establish freshness.'
)
OWNER = 'Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'


class Refused(ValueError):
    pass


def constructor_projection(certificate):
    """Closed native/C-state projection, requiring independent source admission.

    SPD.cc's pinned constructor sets every size uint16 to zero, every status to
    Finished2 and every ready counter to zero. This projection initializes only
    size bytes: no payload, command, owner or arbitrary-entry guarantee follows.
    """
    if (not isinstance(certificate, dict) or certificate != BOOT_CERTIFICATE
            or any(type(certificate[k]) is not type(v) for k,v in BOOT_CERTIFICATE.items())):
        raise Refused('fresh SPD constructor certificate is missing, changed or outside the closed boot epoch')
    return {'source_initial_values': {'status': 2, 'size': 0, 'ready': 0},
            'metadata_bytes': 64,
            'entry_assignments': [f'__swdb_dx_size_bytes[{i}] = 0;' for i in range(64)]}

# Immutable e4fc4af source projection, not a generic header exemption.
SOURCE_PINS = {
    'MAA.hpp':'4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd',
    'MAA_gem5.hpp':'5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174',
    'MAA.cc':'058395cbd171ccf3746fb524967d2d205cb8d622d4aa06e8eef530b00dc21299',
    'SPD.cc':'9e6bb3672be95954e8816c054b4032f95811a3085ca6df418aed90ad1e852b4a',
    'SPD.hh':'70e02b0fea7693585fd9b8f318381c09e352df2fff58bb3f84021f4ea02e9737',
    'CpuSidePort.cc':'886a0c1bbd437916d2fac62a2aa194e01f6996fae65dc56241fad601c5f0103b',
    'IF.cc':'fd7dd67f35f63ff6ed9ef0b8ce36cb60cc6d63b20fe9c0796e648bff82da6561',
}
KIND = 'dx100-get-tile-size-v1'
PROTOTYPE = 'volatile unsigned short get_tile_size(int SPD_id)'
CONTRACT = (r'requires 0 <= SPD_id < 32; assigns \nothing; ensures \result == '
            r'__swdb_dx_size_bytes[2*SPD_id] + 256*__swdb_dx_size_bytes[2*SPD_id+1];')
STATE = 'static unsigned char __swdb_dx_size_bytes[64];\n'
MODEL = ('volatile unsigned short get_tile_size(int SPD_id) {\n'
         '  DX_ASSERT(0 <= SPD_id && SPD_id < 32);\n'
         '  return (unsigned short)(__swdb_dx_size_bytes[2*SPD_id] + 256U*__swdb_dx_size_bytes[2*SPD_id+1]);\n}\n')


def size_layout(data):
    return (data.get('model') or {}).get('layout') == LAYOUT


def _pin(path):
    from pathlib import Path
    from swdb import artifacts
    path=Path(path).resolve()
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':artifacts.file_hash(path)}


def policy(library,definition):
    """An explicitly declared source/boot certificate, never inferred from calls."""
    from pathlib import Path
    try:
        if not isinstance(definition,dict) or set(definition)!={'kind','entry','sources'} or definition.get('kind')!=KIND:
            raise Refused('fresh SPD constructor certificate requires the closed source/entry policy')
        projection=constructor_projection(definition['entry'])
        if not isinstance(definition['sources'],list) or len(definition['sources'])!=len(SOURCE_PINS):
            raise Refused('fresh SPD constructor certificate requires all distinct immutable source pins')
        pins=[]
        for source in definition['sources']:
            library._pin(source);path=library.resolve(source).resolve();pin=_pin(path)
            if pin['sha256']!=SOURCE_PINS.get(path.name) or any(Path(p['path']).name==path.name for p in pins):
                raise Refused('fresh SPD constructor certificate has changed or repeated source')
            pins.append(pin)
        return {'kind':KIND,'entry':dict(definition['entry']),'sources':pins,'projection':projection}
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        return {'refused':str(exc)}


def check(library,data,texts,error):
    import re
    rows=[r for r in data.get('calls',[]) if isinstance(r,dict)]
    active=[r for r in rows if r.get('supported') is not False]
    if not size_layout(data):
        if any('definition' in r for r in rows):
            error('calls.definition','source size definition requires its closed fresh-SPD layout')
            return False
        return True
    valid=True
    def refuse(message):
        nonlocal valid
        valid=False;error('model.layout',message)
    if len(active)!=1 or active[0].get('call')!='get_tile_size':
        refuse('fresh-SPD layout admits only the source-certified size getter')
        return False
    selected=policy(library,active[0].get('definition'))
    if 'refused' in selected:refuse(selected['refused'])
    clean=lambda text:re.sub(r'/\*.*?\*/|//[^\n]*|\s+','',text,flags=re.S)
    if active[0].get('prototype')!=PROTOTYPE or clean(active[0].get('contract',''))!=clean(CONTRACT):
        refuse('fresh-SPD size getter needs the exact source ABI and byte-response contract')
    if any(clean(texts.get(k,'')) for k in ('ghost.acsl','model.logic')):
        refuse('fresh-SPD layout has no ghost state or added axioms')
    for key,want in (('model.state',STATE),('model.c',MODEL)):
        if key in texts and clean(texts[key])!=clean(want):refuse('fresh-SPD layout has a changed state/model body')
    if data.get('constants') or data.get('queries') or data.get('wp') or not data.get('declaration_inventory'):
        refuse('fresh-SPD layout requires full declaration inventory and no extra constants/queries/WP premises')
    rules=[r for r in data.get('rules',[]) if r.get('id')=='fresh_spd_epoch']
    if (len(rules)!=1 or rules[0].get('statement')!=BOOT_STATEMENT or rules[0].get('record_assumption') is not True
            or rules[0].get('assumed')!={'owner':OWNER} or 'fresh_spd_epoch' not in active[0].get('rules',[])):
        refuse('fresh SPD constructor certificate needs its exact owned boot-epoch assumption in every verdict')
    return valid


def _function_ir(module,name):
    import re
    matches=list(re.finditer(r'^define\b[^\n{]*@'+re.escape(name)+r'\([^\n]*\)[^\n{]*\{(?P<body>.*?)^}',module,re.M|re.S))
    if len(matches)!=1:raise Refused('size source has no unique compiled function '+name)
    return matches[0].group(),matches[0]['body']


def _check_getter_ir(module):
    """Closed SSA path for the exact volatile16 source load/local/fence/return."""
    import re
    function,body=_function_ir(module,'__swdb_dx100_size_certificate')
    if not re.search(r'\bi16\s+@__swdb_dx100_size_certificate\(i32\b',function):
        raise Refused('size getter source ABI differs from uint16(int32)')
    # The asm literal itself contains a semicolon; preserve that one statement.
    lines=[line.strip() for line in body.splitlines() if line.strip() and not re.match(r'^\w+:',line.strip())]
    lines=[re.sub(r', ![A-Za-z_][\w.]* !\d+','',line) for line in lines]
    patterns=[
        r'(?P<local>%[\w.]+) = alloca i16, align 2',
        r'call void @llvm\.lifetime\.start\.p0\((?:i64 2, )?ptr[^,)]* (?P<local>%[\w.]+)\)',
        r'(?P<base>%[\w.]+) = load ptr, ptr @SPD_size_noncacheable, align 8',
        r'(?P<offset>%[\w.]+) = sext i32 (?P<argument>%[\w.]+) to i64',
        r'(?P<address>%[\w.]+) = getelementptr(?: inbounds)? i16, ptr (?P<base>%[\w.]+), i64 (?P<offset>%[\w.]+)',
        r'(?P<loaded>%[\w.]+) = load volatile i16, ptr (?P<address>%[\w.]+), align 2',
        r'store volatile i16 (?P<loaded>%[\w.]+), ptr (?P<local>%[\w.]+), align 2',
        r'(?:tail )?call void asm sideeffect "mfence;", "(?:~\{dirflag\},~\{fpsr\},~\{flags\})?"\(\)[^\n]*',
        r'(?P<result>%[\w.]+) = load volatile i16, ptr (?P<local>%[\w.]+), align 2',
        r'call void @llvm\.lifetime\.end\.p0\((?:i64 2, )?ptr[^,)]* (?P<local>%[\w.]+)\)',
        r'ret i16 (?P<result>%[\w.]+)',
    ]
    bindings={}
    if len(lines)!=len(patterns):raise Refused('size getter compiled operation census differs: '+body[:1800])
    for line,pattern in zip(lines,patterns):
        match=re.fullmatch(pattern,line)
        if match is None:raise Refused('size getter compiled operation differs: '+line+'; complete function: '+body)
        for key,value in match.groupdict().items():
            if key in bindings and bindings[key]!=value:raise Refused('size getter compiled SSA flow differs')
            bindings[key]=value
    parameter=re.search(r'@__swdb_dx100_size_certificate\(i32[^,)]* (%[\w.]+)\)',function)
    if parameter is None or parameter[1]!=bindings['argument']:
        raise Refused('size getter address is not derived from its original signed index')
    if not re.search(r'^target datalayout = "e-',module,re.M):raise Refused('size getter needs the explicit little-endian guest correspondence')
    alloc,_=_function_ir(module,'_Z9alloc_MAAv')
    addresses={'SPD_data_cacheable':17179869184,'SPD_data_noncacheable':17181966336,
               'SPD_size_noncacheable':17184063488,'SPD_ready_noncacheable':17184063552,
               'REG_noncacheable':17184063616,'INSTR_opcode_datatype_optype_tdst1_tdst2':17184063744,
               'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc':17184063752,
               'INSTR_baseaddr':17184063760}
    for name,value in addresses.items():
        if not re.search(r'store ptr inttoptr \(i64 '+str(value)+r' to ptr\), ptr @'+name+r', align 8\b',alloc):
            raise Refused('source MMIO address setup/geometry differs: '+name)
    if not re.search(r'store i64 17184063768, ptr @MAA_end_addr, align 8\b',alloc):
        raise Refused('source MMIO end/geometry differs')
    return function,bindings,addresses



CALLER_BINDING = {'function':'trust_fixture','return_type':'int','parameter_count':0,
                  'local':'observed','initializer_call':'get_tile_size','literal_int_argument':0,
                  'return_local':'observed','other_statements':0}


def _check_caller_ast(caller):
    """No macros/text literals may hide effects in this closed synthetic caller.

    The local declaration and return reference are compared inside this one
    compiler AST object. No declaration IDs cross dumps, processes or records.
    """
    def children(node):return node.get('inner') or []
    def need(condition):
        if not condition:raise Refused('fresh-SPD closed caller AST has changed statements, values or effects')
    bodies=[n for n in children(caller) if n.get('kind')=='CompoundStmt']
    need(len(bodies)==1)
    statements=children(bodies[0]);need(len(statements)==2)
    declaration,returned=statements
    need(declaration.get('kind')=='DeclStmt' and returned.get('kind')=='ReturnStmt')
    variables=children(declaration);need(len(variables)==1)
    variable=variables[0]
    need(variable.get('kind')=='VarDecl' and variable.get('name')=='observed'
         and (variable.get('type') or {}).get('qualType')=='int' and len(children(variable))==1)
    cast=children(variable)[0]
    need(cast.get('kind')=='CStyleCastExpr' and cast.get('castKind') in ('IntegralCast','NoOp')
         and (cast.get('type') or {}).get('qualType')=='int' and len(children(cast))==1)
    call=children(cast)[0]
    if cast.get('castKind')=='NoOp':
        # Clang22 represents explicit (int) as a no-op wrapper around the
        # actual integral promotion, not an arbitrary expression wrapper.
        need(call.get('kind')=='ImplicitCastExpr' and call.get('castKind')=='IntegralCast'
             and (call.get('type') or {}).get('qualType')=='int' and len(children(call))==1)
        call=children(call)[0]
    need(call.get('kind')=='CallExpr' and len(children(call))==2)
    callee,argument=children(call)
    need(callee.get('kind')=='ImplicitCastExpr' and callee.get('castKind')=='FunctionToPointerDecay'
         and len(children(callee))==1)
    reference=children(callee)[0]
    need(reference.get('kind')=='DeclRefExpr'
         and (reference.get('referencedDecl') or {}).get('kind')=='FunctionDecl'
         and (reference.get('referencedDecl') or {}).get('name')=='get_tile_size')
    need(argument.get('kind')=='IntegerLiteral' and argument.get('value')=='0'
         and (argument.get('type') or {}).get('qualType')=='int')
    need(len(children(returned))==1)
    conversion=children(returned)[0]
    need(conversion.get('kind')=='ImplicitCastExpr' and conversion.get('castKind')=='LValueToRValue'
         and len(children(conversion))==1)
    result=children(conversion)[0]
    need(result.get('kind')=='DeclRefExpr' and variable.get('id') is not None
         and (result.get('referencedDecl') or {}).get('id')==variable['id'])
    return dict(CALLER_BINDING)


GETTER_BINDING = {'function':'get_tile_size','body_statements':'DeclStmt,GCCAsmStmt,ReturnStmt',
                  'source_body_macros':0,'volatile_metadata_bits':16,'index_bits':32,
                  'packet_core':0,'packet_bytes':2,'required_status':'Finished',
                  'covering_wait':False,'ready_read_scope':'separate blocking read returns1; not admitted here'}


def _check_direct_getter_ast(declaration):
    """Optimized equivalence cannot establish definedness of extra source work.

    The immutable getter has exactly three direct statements and no body
    macros. Refuse macro-inserted work before the compiler may optimize it away.
    ABI/load/address/SSA/fence checks independently bind the accepted body.
    """
    bodies=[n for n in declaration.get('inner',[]) if n.get('kind')=='CompoundStmt']
    if (len(bodies)!=1 or [n.get('kind') for n in bodies[0].get('inner',[])]
            !=['DeclStmt','GCCAsmStmt','ReturnStmt']):
        raise Refused('size effective getter/caller tokens differ: changed direct getter AST statements')
    stack=[bodies[0]]
    while stack:
        node=stack.pop()
        if isinstance(node,dict):
            if 'spellingLoc' in node or 'expansionLoc' in node:
                raise Refused('size effective getter/caller tokens differ: getter body contains a macro expansion')
            stack.extend(node.values())
        elif isinstance(node,list):stack.extend(node)
    return dict(GETTER_BINDING)

def certify(unit,declaration,selected,caller,*,standard,timeout):
    import hashlib,re,shlex,subprocess,tempfile
    from pathlib import Path
    from swdb import artifacts,stdlib_provenance
    if 'refused' in selected:raise Refused(selected['refused'])
    headers={Path(p['path']).name:p for p in selected['sources']}
    location=declaration.get('loc') or {}
    if (location.get('spellingLoc') or location.get('expansionLoc') or
            Path(location.get('_file',location.get('file',''))).resolve()!=Path(headers['MAA_gem5.hpp']['path'])):
        raise Refused('size getter definition does not originate in the immutable MMIO header')
    if declaration.get('mangledName') not in ('_Z13get_tile_sizei','__Z13get_tile_sizei'):
        raise Refused('size getter has no unique canonical source family')
    if unit.ctype((declaration.get('type') or {}).get('qualType','').split('(')[0].strip())!='volatile unsigned short':
        raise Refused('size getter source return ABI differs')
    families=[n for n in unit.dump('get_tile_size') if n.get('kind')=='FunctionDecl' and n.get('name')=='get_tile_size']
    if len(families)!=1:raise Refused('size getter source family is ambiguous')
    getter_binding=_check_direct_getter_ast(declaration)
    caller_location=caller.get('loc') or {}
    if (caller_location.get('spellingLoc') or caller_location.get('expansionLoc') or
            Path(caller_location.get('_file',caller_location.get('file',''))).resolve()!=unit.source.resolve()):
        raise Refused('fresh-SPD caller does not originate directly in the original proof unit')
    if caller.get('name')!='trust_fixture' or (caller.get('type') or {}).get('qualType')!='int ()':
        raise Refused('fresh-SPD first gate admits only the closed synthetic caller shape')
    points=[(caller.get('range') or {}).get(k) or {} for k in ('begin','end')]
    if any('offset' not in p or p.get('spellingLoc') or p.get('expansionLoc') for p in points):
        raise Refused('fresh-SPD caller has no direct unique source range')
    original=unit.source.read_bytes()[points[0]['offset']:points[1]['offset']+points[1]['tokLen']].decode()
    canonical='int trust_fixture() { int observed=(int)get_tile_size(0); return observed; }'
    clean=lambda text:re.sub(r'\s+','',text)
    if clean(original)!=clean(canonical):raise Refused('fresh-SPD caller mutates or leaves the closed boot epoch')
    caller_binding=_check_caller_ast(caller)
    source_sha=unit.source_digest;runtime=stdlib_provenance.runtime_identity(unit.tool)
    def unchanged():
        if artifacts.file_hash(unit.source)!=source_sha or any(_pin(p['path'])!=p for p in selected['sources']):
            raise Refused('fresh-SPD source/epoch certificate changed during binding')
    unchanged()
    probe='\nextern "C" unsigned short __swdb_dx100_size_certificate(int id) { return ::get_tile_size(id); }\n'
    with tempfile.TemporaryDirectory(prefix='swdb-dx100-size-') as folder:
        path=Path(folder)/'probe.ii';dep=Path(folder)/'original.d'
        pre=[*unit.tool.command,'-x','c++','-std='+standard,'-fopenmp','-E','-MD','-MF',str(dep),'-I'+str(unit.source.parent)]
        pre+=['-I'+str(p) for p in unit.includes]+['-D'+d for d in unit.defines]+[str(unit.source)]
        try:result=subprocess.run(pre,capture_output=True,text=True,timeout=timeout)
        except (OSError,subprocess.SubprocessError) as exc:raise Refused('size original preprocessing failed: '+str(exc)) from None
        if result.returncode:raise Refused('size original preprocessing refused: '+result.stderr[-500:])
        tokens=result.stdout
        getter='inline volatile uint16_t get_tile_size(int SPD_id) { volatile uint16_t sz = SPD_size_noncacheable[SPD_id]; __asm__ __volatile__("mfence;"); return sz; }'
        if clean(getter) not in clean(tokens) or clean(canonical) not in clean(tokens):
            raise Refused('size effective getter/caller tokens differ from the closed source body')
        inputs=[_pin(p) for p in sorted(set(shlex.split(dep.read_text().replace('\\\n','').split(':',1)[1])))]
        path.write_text(tokens+probe)
        command=[*unit.tool.command,'-x','c++-cpp-output','-std='+standard,'-fopenmp','-O2','-S','-emit-llvm','-o','-',str(path)]
        try:compiled=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
        except (OSError,subprocess.SubprocessError) as exc:raise Refused('size compiler certificate failed: '+str(exc)) from None
        if compiled.returncode:raise Refused('size compiler certificate refused: '+compiled.stderr[-800:])
        function,flow,addresses=_check_getter_ir(compiled.stdout)
        if any(_pin(p['path'])!=p for p in inputs) or stdlib_provenance.runtime_identity(unit.tool)!=runtime:
            raise Refused('size compiler input/runtime changed during binding')
    unchanged()
    digest=lambda text:hashlib.sha256(text.encode()).hexdigest()
    return {**selected,'source_path':str(unit.source.resolve()),'source_sha256':source_sha,
            'source_mangled':declaration['mangledName'],'caller_shape':canonical,'caller_binding':caller_binding,
            'getter_binding':getter_binding,
            'compiler_inputs':inputs,'runtime_identity':runtime,'preprocess_command':pre,'compiler_command':command,
            'preprocessed_source':tokens,'preprocessed_source_sha256':digest(tokens),'probe_source':probe,
            'probe_source_sha256':digest(probe),'llvm_module':compiled.stdout,'llvm_module_sha256':digest(compiled.stdout),
            'llvm_function':function,'ssa_flow':flow,'mmio_addresses':addresses,'boot_statement':BOOT_STATEMENT}


def bindings(lowering):
    return [row['semantic_source'] for row in getattr(lowering,'summaries',()) if row.get('semantic_source',{}).get('kind')==KIND]


def recheck(lowering):
    import hashlib
    from swdb import artifacts
    checked=[]
    for certificate in bindings(lowering):
        try:
            if certificate['kind']!=KIND or certificate['boot_statement']!=BOOT_STATEMENT:
                raise Refused('fresh-SPD source/epoch kind or premise changed')
            if certificate['getter_binding']!=GETTER_BINDING:
                raise Refused('fresh-SPD direct getter AST binding changed')
            if certificate['caller_binding']!=CALLER_BINDING:
                raise Refused('fresh-SPD closed caller AST binding changed')
            if constructor_projection(certificate['entry'])!=certificate['projection']:
                raise Refused('fresh-SPD constructor byte projection changed')
            for text,digest in (('preprocessed_source','preprocessed_source_sha256'),('probe_source','probe_source_sha256'),('llvm_module','llvm_module_sha256')):
                if hashlib.sha256(certificate[text].encode()).hexdigest()!=certificate[digest]:
                    raise Refused('fresh-SPD frozen compiler evidence changed')
            if artifacts.file_hash(certificate['source_path'])!=certificate['source_sha256']:
                raise Refused('fresh-SPD original source changed')
            for p in [*certificate['sources'],*certificate['compiler_inputs']]:
                if _pin(p['path'])!=p:raise Refused('fresh-SPD physical source/compiler input changed')
            function,flow,addresses=_check_getter_ir(certificate['llvm_module'])
            if (function!=certificate['llvm_function'] or flow!=certificate['ssa_flow']
                    or addresses!=certificate['mmio_addresses']):
                raise Refused('fresh-SPD compiled operation metadata changed')
            from pathlib import Path
            if (len(certificate['sources'])!=len(SOURCE_PINS) or
                    {Path(p['path']).name:p['sha256'] for p in certificate['sources']}!=SOURCE_PINS):
                raise Refused('fresh-SPD immutable source family changed')
            checked.append({k:certificate[k] for k in ('kind','entry','projection','source_sha256','preprocessed_source_sha256','llvm_module_sha256','sources','compiler_inputs')})
        except (KeyError,TypeError,AttributeError,OSError) as exc:
            raise Refused('fresh-SPD certificate unavailable: '+str(exc)) from None
    return checked
