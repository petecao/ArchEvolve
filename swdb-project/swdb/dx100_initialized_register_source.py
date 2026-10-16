"""2026-10-16 ET. Closed initialized-u32 normal-return source admission.

This namespace is separate from the accepted uninitialized allocator and scalar
register fixture. Compiler observations and source-model agreement are owned
TCB duties; no RF freshness, arbitrary caller, or hardware liveness is granted.
"""
import hashlib
import json
import re
from pathlib import Path

from swdb.dx100_initialized_register_model import (
    OWNER, ENTRY, STATEMENT, CALLER, STATE, PROTOTYPES, CONTRACTS, MODEL,
)
from swdb.dx100_size_source import SOURCE_PINS

KIND='dx100-initialized-u32-register-v1'
LAYOUT='dx100-initialized-u32-register-partial-v1'
PARTIAL_CONTRACT='contract.dx100_initialized_register_partial_fixture.v1'
PARTIAL_METHOD='method.dx100-initialized-register-partial-fixture-v1'
SEMANTICS_ID='semantics.dx100_initialized_register_fixture_0_2'


class Refused(ValueError):
    pass


def initialized_register_layout(data):
    return isinstance(data,dict) and isinstance(data.get('model'),dict) and data['model'].get('layout')==LAYOUT


def _same(left,right):
    if type(left)is not type(right):return False
    if isinstance(left,dict):return left.keys()==right.keys() and all(_same(left[k],right[k])for k in left)
    if isinstance(left,list):return len(left)==len(right) and all(_same(a,b)for a,b in zip(left,right))
    return left==right


def _hash(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def _logical_reference(library,reference):
    # Library.resolve intentionally dereferences safe aliases inside a root.
    # This distinct source policy checks the original reference before that.
    from swdb import paths
    root=reference.get('root','library')
    bases={'library':getattr(library,'root',None),'project':paths.HOME,'repository':paths.HOME.parent}
    if root not in bases or bases[root]is None:raise Refused('initialized source needs a declared reference root')
    base=Path(bases[root]);relative=Path(reference['path'])
    if not base.is_absolute()or relative.is_absolute()or '..'in relative.parts:
        raise Refused('initialized source reference must stay relative to its declared root')
    current=base
    if current.is_symlink():raise Refused('initialized source declared root must be physical')
    for part in relative.parts:
        current=current/part
        if current.is_symlink():raise Refused('initialized-register source reference contains a symbolic link')


def policy(library,definition):
    try:
        if not isinstance(definition,dict)or set(definition)!={'kind','call','entry','sources'}or definition['kind']!=KIND or definition['call']not in PROTOTYPES or not _same(definition['entry'],ENTRY):
            raise Refused('explicit distinct initialized-u32 source/entry certificate required')
        if not isinstance(definition['sources'],list)or len(definition['sources'])!=len(SOURCE_PINS):
            raise Refused('all seven distinct immutable initialized-register sources required')
        pins=[]
        for source in definition['sources']:
            _logical_reference(library,source)
            original=library.resolve(source)
            if original.is_symlink():raise Refused('initialized-register immutable source must not be a symbolic link')
            library._pin(source);path=original.resolve()
            if not path.is_file()or _hash(path)!=SOURCE_PINS.get(path.name)or any(Path(p['path']).name==path.name for p in pins):
                raise Refused('initialized-register immutable source changed or repeated')
            pins.append({'path':str(path),'bytes':path.stat().st_size,'sha256':SOURCE_PINS[path.name]})
        return {'kind':KIND,'call':definition['call'],'entry':definition['entry'],'sources':pins,
                'termination_policy':'conditional normal return; no hardware liveness'}
    except (OSError,ValueError,KeyError,TypeError,AttributeError)as exc:
        return {'refused':str(exc)}


def check(library,data,texts,error):
    rows=[r for r in data.get('calls',[])if isinstance(r,dict)]
    definitions=[v['definition']for r in rows for v in [r,*r.get('instances',[])]
                 if isinstance(v,dict)and isinstance(v.get('definition'),dict)]
    if not initialized_register_layout(data):
        if any(d.get('kind')==KIND for d in definitions):
            error('calls.definition','initialized-register definition needs its distinct closed layout')
            return False
        return True
    if data.get('id')!=SEMANTICS_ID:
        error('id','initialized-register route requires its exact fixed semantics entry identity')
        return False
    valid=True
    def refuse(message):
        nonlocal valid
        valid=False;error('model.layout',message)
    active=[r for r in rows if r.get('supported')is not False]
    if len(active)!=3 or {r.get('call')for r in active}!=set(PROTOTYPES):
        refuse('initialized-register admits exactly init_MAA and arity1 u32 get_new_reg/get_reg')
        return False
    for row in active:
        name=row['call'];variants=[row]if name=='init_MAA'else row.get('instances')
        if not isinstance(variants,list)or len(variants)!=(2 if name=='get_new_reg'else 1):
            refuse('initialized-register exact typed/overload inventory required');continue
        if name=='get_new_reg':
            unreachable={'arguments':['unsigned int'],'arity':0,'declaration':'inline int get_new_reg()',
                         'prototype':'int get_new_reg_unsigned_int_args0(void)',
                         'contract':r'requires \false; assigns \nothing;'}
            if not _same(variants[1],unreachable):refuse('zero-argument register overload must remain explicitly unreachable')
        v=variants[0]
        if name!='init_MAA':
            if v.get('arguments')!=['unsigned int']or type(v.get('arity'))is not int or v['arity']!=1:
                refuse('initialized-register source requires exactly arity1 unsigned int')
            if name=='get_new_reg'and v.get('declaration')!='inline int get_new_reg(T1 data)':
                refuse('initialized register must select the original one-argument declaration')
        if v.get('prototype')!=PROTOTYPES[name]or v.get('contract')!=CONTRACTS[name]:
            refuse('initialized-register ordinary prewrite/value/frame contract changed')
        selected=policy(library,v.get('definition'))
        if 'refused'in selected or selected.get('call')!=name:
            refuse(selected.get('refused','initialized-register source call differs'))
        rules=[r for r in data.get('rules',[])if r.get('id')=='register_scope']
        if len(rules)!=1 or rules[0].get('statement')!=STATEMENT or rules[0].get('assumed')!={'owner':OWNER}or rules[0].get('record_assumption')is not True or 'register_scope'not in row.get('rules',[]):
            refuse('initialized-register disjoint-address/source TCB must appear in every verdict')
    for key,value in [('model.state',STATE),('model.c',MODEL),
                      ('model.logic','/* No added axioms. */\n'),
                      ('ghost.acsl','/* Ordinary register-word projection. */\n')]:
        if texts.get(key)!=value:refuse('initialized-register exact ordinary projection changed: '+key)
    if data.get('constants')or data.get('queries')or data.get('wp'):
        refuse('initialized-register adds no constant/query/axiom or original-unit premise')
    return valid


def unit_policy(library,entry):
    if not isinstance(entry,dict):raise Refused('initialized register requires its distinct original partial unit')
    unit=entry.get('proof_unit')or{}
    data=library.get(SEMANTICS_ID)
    if not isinstance(unit,dict)or entry.get('id')!=PARTIAL_CONTRACT or entry.get('version')!='0.1'or unit.get('function')!='trust_fixture'or not initialized_register_layout(data)or SEMANTICS_ID not in library.files:
        raise Refused('initialized register requires its distinct original partial contract/unit version')
    expected={'kind':'partial-normal-return-v1','source_policy':KIND,
              'semantics':{'id':SEMANTICS_ID,'sha256':_hash(library.files[SEMANTICS_ID])}}
    if not _same(unit.get('correctness_policy'),expected):
        raise Refused('initialized register requires its explicit partial policy and exact semantics pin')
    return expected


def bindings(lowering):
    """Collect candidate receipts; only recheck may validate their contents."""
    return [row['semantic_source']for row in getattr(lowering,'summaries',())
            if isinstance(row,dict)and isinstance(row.get('semantic_source'),dict)
            and row['semantic_source'].get('kind')==KIND]


def _function(module,name):
    matches=list(re.finditer(r'^define ([^\n]*@'+re.escape(name)+r'\([^\n]*\)[^\n]*) \{\n(.*?)^\}',module,re.M|re.S))
    if len(matches)!=1:raise Refused('initialized register needs one complete emitted function: '+name)
    return matches[0].group(1),matches[0].group(2)


def _flow(function,body,patterns,parameters):
    """Check every emitted instruction and preserve shared SSA/block identities."""
    bindings={}
    params=re.search(r'@[^ (]+\((.*?)\)',function)
    if params is None:raise Refused('initialized register emitted parameter list missing')
    actual=re.findall(r'i32\b[^,%)]* (%[\w.]+)',params[1])
    if len(actual)!=len(parameters)or actual!=['%'+str(i)for i in range(len(parameters))]:raise Refused('initialized register emitted i32 ABI/unnamed entry shape differs')
    if not re.search(r'\bi32 @',function):raise Refused('initialized register emitted return ABI differs')
    bindings.update(zip(parameters,actual))
    bindings['entry']='%'+str(len(parameters))
    lines=[]
    for line in body.splitlines():
        line=line.strip()
        if not line:continue
        if re.match(r'^[\w.]+:',line):line='LABEL %'+line.split(':',1)[0]
        line=re.sub(r', ![A-Za-z_][\w.]* !\d+','',line)
        line=re.sub(r' #\d+$','',line)
        lines.append(line)
    if len(lines)!=len(patterns):raise Refused('initialized register emitted instruction/block census differs')
    # A repeated {field} refers to the same SSA value or block throughout.
    for line,pattern in zip(lines,patterns):
        names=re.findall(r'(?<!\\)\{([a-z][a-z0-9_]*)\}',pattern)
        for name in names:
            pattern=pattern.replace('{'+name+'}', '(?P<'+name+'>%[\\w.]+)',1)
        match=re.fullmatch(pattern,line)
        if match is None:raise Refused('initialized register emitted source operation differs: '+line)
        for name,value in match.groupdict().items():
            if name in bindings and bindings[name]!=value:raise Refused('initialized register emitted SSA/control flow differs: '+name)
            bindings[name]=value
    return bindings


_FENCE=r'(?:tail )?call void asm sideeffect "mfence;", "(?:~\{dirflag\},~\{fpsr\},~\{flags\})?"\(\)'
_ABORT=r'(?:tail )?call void @__(?:assert_rtn|assert_fail)\(ptr noundef nonnull @[\w.]+, ptr noundef nonnull @[\w.]+, i32 noundef 125, ptr noundef nonnull @[\w.]+\)'


def _counter_bound_flow(function, body, patterns, parameters, profile):
    """Keep signed counter comparisons paired with their exact branch roles."""
    guards = {
        'bounded': [('late', 'reload', 'bad', 'finish')],
        'caller': [('late_first', 'reload_first', 'bad_first', 'good_first'),
                   ('late_second', 'reload_second', 'bad_second', 'good_second')],
    }
    if profile not in guards: raise Refused('initialized counter guard profile is not closed')
    alternate = list(patterns)
    for result, operand, bad, good in guards[profile]:
        comparison = '{' + result + '} = icmp sgt i32 {' + operand + '}, 32'
        branch = 'br i1 {' + result + '}, label {' + bad + '}, label {' + good + '}'
        if patterns.count(comparison) != 1: raise Refused('initialized signed counter comparison anchor changed')
        index = patterns.index(comparison)
        if index + 1 >= len(patterns) or patterns[index + 1] != branch:
            raise Refused('initialized signed counter branch anchor changed')
        alternate[index] = '{' + result + '} = icmp slt i32 {' + operand + '}, 33'
        alternate[index + 1] = 'br i1 {' + result + '}, label {' + good + '}, label {' + bad + '}'
    try:
        bindings = _flow(function, body, patterns, parameters)
    except Refused:
        bindings = _flow(function, body, alternate, parameters)
    for result, _operand, _bad, _good in guards[profile]:
        # Every instruction is checked by _flow; also bind this comparison's
        # sole consumer rather than admitting a value-bearing extra use.
        uses = re.findall(r'(?<![\w.])' + re.escape(bindings[result]) + r'(?![\w.])', body)
        if len(uses) != 2: raise Refused('initialized counter comparison does not have one exact branch consumer')
    return bindings


def _operations(module):
    if not re.search(r'^target datalayout = "e-',module,re.M):raise Refused('initialized register requires observed little-endian ABI')
    signature,body=_function(module,'__dx_initialized_bounded_source')
    bounded=[
        r'{guard} = icmp ugt i32 {old}, 31',r'br i1 {guard}, label {finish}, label {good}',r'LABEL {good}',
        r'{next} = add(?: nuw)? nsw i32 {old}, 1',r'store i32 {next}, ptr @REG_count, align 4',
        r'{base} = load ptr, ptr @REG_noncacheable, align 8',r'{offset} = zext(?: nneg)? i32 {old} to i64',
        r'{address} = getelementptr(?: inbounds)?(?: nuw)? i32, ptr {base}, i64 {offset}',
        r'store i32 {data}, ptr {address}, align 4',_FENCE,
        r'{reload} = load i32, ptr @REG_count, align 4',r'{late} = icmp sgt i32 {reload}, 32',
        r'br i1 {late}, label {bad}, label {finish}',r'LABEL {bad}',_ABORT,r'unreachable',
        r'LABEL {finish}',r'{result} = phi i32 \[ -1, {entry} \], \[ {old}, {good} \]',r'ret i32 {result}',
    ]
    initialized=_counter_bound_flow(signature,body,bounded,['old','data'],'bounded')
    initialized_signature=signature
    signature,getter=_function(module,'__dx_initialized_get_source')
    getpatterns=[
        r'{local} = alloca i32, align 4',r'{guard} = icmp ugt i32 {id}, 31',
        r'br i1 {guard}, label {finish}, label {good}',r'LABEL {good}',
        r'call void @llvm\.lifetime\.start\.p0\((?:i64 4, )?ptr(?: nonnull)? {local}\)',
        r'{base} = load ptr, ptr @REG_noncacheable, align 8',r'{offset} = zext(?: nneg)? i32 {id} to i64',
        r'{address} = getelementptr(?: inbounds)?(?: nuw)? i32, ptr {base}, i64 {offset}',
        r'{loaded} = load i32, ptr {address}, align 4',r'store volatile i32 {loaded}, ptr {local}, align 4',_FENCE,
        r'{value} = load volatile i32, ptr {local}, align 4',
        r'call void @llvm\.lifetime\.end\.p0\((?:i64 4, )?ptr(?: nonnull)? {local}\)',r'br label {finish}',
        r'LABEL {finish}',r'{result} = phi i32 \[ {value}, {good} \], \[ 0, {entry} \]',r'ret i32 {result}',
    ]
    get=_flow(signature,getter,getpatterns,['id'])
    signature,caller=_function(module,'_Z13trust_fixturev')
    callerpatterns=[
        r'{local_second} = alloca i32, align 4',r'{local_first} = alloca i32, align 4',
        r'store i32 0, ptr @SPD_count, align 4',r'store i8 6, ptr @region_count, align 1',
        r'store i32 1, ptr @REG_count, align 4',r'{base_first} = load ptr, ptr @REG_noncacheable, align 8',
        r'store i32 7, ptr {base_first}, align 4',_FENCE,
        r'{reload_first} = load i32, ptr @REG_count, align 4',r'{late_first} = icmp sgt i32 {reload_first}, 32',
        r'br i1 {late_first}, label {bad_first}, label {good_first}',r'LABEL {bad_first}',_ABORT,r'unreachable',
        r'LABEL {good_first}',r'{next} = add nsw i32 {reload_first}, 1',r'store i32 {next}, ptr @REG_count, align 4',
        r'{base_second} = load ptr, ptr @REG_noncacheable, align 8',r'{offset_second} = sext i32 {reload_first} to i64',
        r'{address_second} = getelementptr(?: inbounds)? i32, ptr {base_second}, i64 {offset_second}',
        r'store i32 11, ptr {address_second}, align 4',_FENCE,
        r'{reload_second} = load i32, ptr @REG_count, align 4',r'{late_second} = icmp sgt i32 {reload_second}, 32',
        r'br i1 {late_second}, label {bad_second}, label {good_second}',r'LABEL {bad_second}',_ABORT,r'unreachable',
        r'LABEL {good_second}',
        r'call void @llvm\.lifetime\.start\.p0\((?:i64 4, )?ptr(?: nonnull)? {local_first}\)',
        r'{read_base_first} = load ptr, ptr @REG_noncacheable, align 8',r'{read_first} = load i32, ptr {read_base_first}, align 4',
        r'store volatile i32 {read_first}, ptr {local_first}, align 4',_FENCE,
        r'{value_first} = load volatile i32, ptr {local_first}, align 4',
        r'call void @llvm\.lifetime\.end\.p0\((?:i64 4, )?ptr(?: nonnull)? {local_first}\)',r'{scaled} = mul i32 {value_first}, 100',
        r'call void @llvm\.lifetime\.start\.p0\((?:i64 4, )?ptr(?: nonnull)? {local_second}\)',
        r'{read_base_second} = load ptr, ptr @REG_noncacheable, align 8',
        r'{read_address_second} = getelementptr(?: inbounds)? i32, ptr {read_base_second}, i64 {offset_second}',
        r'{read_second} = load i32, ptr {read_address_second}, align 4',r'store volatile i32 {read_second}, ptr {local_second}, align 4',_FENCE,
        r'{value_second} = load volatile i32, ptr {local_second}, align 4',
        r'call void @llvm\.lifetime\.end\.p0\((?:i64 4, )?ptr(?: nonnull)? {local_second}\)',
        r'{result} = add i32 {value_second}, {scaled}',r'ret i32 {result}',
    ]
    closed=_counter_bound_flow(signature,caller,callerpatterns,[],'caller')
    alloc_signature,alloc=_function(module,'_Z9alloc_MAAv')
    addresses={'SPD_data_cacheable':17179869184,'SPD_data_noncacheable':17181966336,'SPD_size_noncacheable':17184063488,
               'SPD_ready_noncacheable':17184063552,'REG_noncacheable':17184063616,'INSTR_opcode_datatype_optype_tdst1_tdst2':17184063744,
               'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc':17184063752,'INSTR_baseaddr':17184063760}
    for name,address in addresses.items():
        if not re.search(r'store ptr inttoptr \(i64 '+str(address)+r' to ptr\), ptr @'+name+r', align 8\b',alloc):
            raise Refused('initialized register mapping geometry differs: '+name)
    if not re.search(r'store i64 17184063768, ptr @MAA_end_addr, align 8\b',alloc):raise Refused('initialized register mapping end differs')
    return {'initialized':{'function':initialized_signature,'body':body,'ssa':initialized,'poststore_counter_reload':True,'normal_return_only':True},
            'getter':{'body':getter,'ssa':get,'pointed_access_volatile':False,'local_temporary_volatile':True},
            'caller':{'body':caller,'ssa':closed,'fences':4,'poststore_counter_reloads':2},
            'mapping':{'function':alloc_signature,'addresses':addresses,'scalar_bytes':128,'end_address':17184063768},
            'source_model_correspondence':'owned TCB, including counter objects/MMIO disjointness; not a compiler theorem'}


def observation(tokens,dumps,module,sources):
    """Validate retained original-source/compiler observations without tools."""
    try:
        _checked_sources(sources)
        return {'scope':'source/compiler observation; source-model agreement remains owned TCB',
                'body_bindings':_bodies(tokens,dumps,sources),'operations':_operations(module),'source_body_proof':False}
    except (OSError,KeyError,TypeError,AttributeError,ValueError)as exc:
        if isinstance(exc,Refused):raise
        raise Refused('initialized original source/compiler observation unavailable: '+str(exc))from None


def _checked_sources(sources):
    if not isinstance(sources,list)or len(sources)!=len(SOURCE_PINS):raise Refused('initialized register needs all seven source pins')
    found={}
    for pin in sources:
        if not isinstance(pin,dict)or set(pin)!={'path','bytes','sha256'}or type(pin['bytes'])is not int:
            raise Refused('initialized register physical source pin shape changed')
        path=Path(pin['path'])
        if not path.is_absolute()or path.is_symlink()or str(path.resolve())!=str(path)or path.name in found:
            raise Refused('initialized register source path must be canonical, unique and physical')
        if pin['sha256']!=SOURCE_PINS.get(path.name)or path.stat().st_size!=pin['bytes']or _hash(path)!=pin['sha256']:
            raise Refused('initialized register immutable source changed')
        found[path.name]=pin
    if set(found)!=set(SOURCE_PINS):raise Refused('initialized register source family differs')
    return found
def _children(node):
    children = node.get('inner', [])
    if not isinstance(children, list) or any(not isinstance(child, dict) for child in children):
        raise Refused('initialized AST children are malformed')
    return children


def _walk(node):
    yield node
    for child in _children(node):
        yield from _walk(child)


def _parse_dump(text):
    decoder = json.JSONDecoder(); nodes = []; at = 0
    while at < len(text):
        while at < len(text) and text[at].isspace(): at += 1
        if at == len(text): break
        try: node, at = decoder.raw_decode(text, at)
        except (ValueError, TypeError) as exc: raise Refused('initialized AST dump is not complete JSON: ' + str(exc)) from None
        if not isinstance(node, dict): raise Refused('initialized AST root is not a declaration')
        nodes.append(node)
    if not nodes: raise Refused('initialized AST dump is empty')
    return nodes


def _slice(node, tokens):
    points = [(node.get('range') or {}).get(key, {}) for key in ('begin', 'end')]
    if any(not isinstance(point, dict) or type(point.get('offset')) is not int
           or type(point.get('tokLen')) is not int or point['tokLen'] < 1
           or 'spellingLoc' in point or 'expansionLoc' in point for point in points):
        raise Refused('initialized frozen body has indirect or unavailable source locations')
    start, end = points[0]['offset'], points[1]['offset'] + points[1]['tokLen']
    raw = tokens.encode()
    if not 0 <= start < end <= len(raw): raise Refused('initialized frozen body source extent is invalid')
    try: text = raw[start:end].decode()
    except UnicodeError as exc: raise Refused('initialized frozen source extent is not UTF-8: ' + str(exc)) from None
    return start, end, text


def _clean(text):
    # Preserve string/character contents, including assembly text and diagnostics.
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*|\s+',
                  lambda match: match[0] if match[0].startswith(('"', "'")) else '', text, flags=re.S)


def _body(text, signature):
    matches = list(re.finditer(r'(?m)^\s*' + re.escape(signature), text))
    if len(matches) != 1: raise Refused('initialized original source signature is not unique: ' + signature)
    begin = text.find('{', matches[0].end())
    if begin < 0: raise Refused('initialized original source body is missing')
    depth = 0
    for match in re.finditer(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*|[{}]', text[begin:], re.S):
        token = match[0]
        if token == '{': depth += 1
        elif token == '}':
            depth -= 1
            if depth == 0: return text[begin:begin + match.end()]
    raise Refused('initialized original source body is not closed')


def _strip_expr(node):
    while node.get('kind') in {'ParenExpr', 'ImplicitCastExpr', 'CXXStaticCastExpr', 'CStyleCastExpr', 'CXXFunctionalCastExpr'} and len(_children(node)) == 1:
        node = _children(node)[0]
    return node


def _expression(node):
    node = _strip_expr(node); children = _children(node); kind = node.get('kind')
    if kind == 'IntegerLiteral' and not children:
        try: return int(node['value'])
        except (ValueError, TypeError, KeyError): raise Refused('initialized assertion integer is malformed') from None
    if kind == 'DeclRefExpr' and not children:
        return ('name', node.get('referencedDecl', {}).get('name'))
    if kind == 'UnaryOperator' and len(children) == 1: return (node.get('opcode'), _expression(children[0]))
    if kind == 'BinaryOperator' and len(children) == 2: return (node.get('opcode'), _expression(children[0]), _expression(children[1]))
    return ('unsupported', kind)


def _callee(node):
    if node.get('kind') != 'CallExpr' or not _children(node): return None
    reference = _strip_expr(_children(node)[0])
    if reference.get('kind') != 'DeclRefExpr' or _children(reference): return None
    declaration = reference.get('referencedDecl', {})
    return declaration.get('name') if declaration.get('kind') == 'FunctionDecl' else None


def _string(node):
    node = _strip_expr(node)
    if node.get('kind') != 'StringLiteral' or _children(node): raise Refused('initialized assertion diagnostic is not a literal')
    try: value = json.loads(node.get('value', ''))
    except (ValueError, TypeError): raise Refused('initialized assertion diagnostic literal is unavailable') from None
    if not isinstance(value, str) or node.get('type', {}).get('qualType') != 'const char[' + str(len(value) + 1) + ']':
        raise Refused('initialized assertion diagnostic type/extent changed')
    return value


def _assert_function_diagnostic(call):
    """Qualify ONLY glibc's fourth diagnostic argument, never executable code."""
    if _callee(call) != '__assert_fail' or len(_children(call)) != 5: return None
    reference = _strip_expr(_children(call)[0]); declaration = reference.get('referencedDecl', {})
    signature = 'void (const char *, const char *, unsigned int, const char *) __attribute__((noreturn)) noexcept(true)'
    if declaration.get('type', {}).get('qualType') != signature or reference.get('type', {}).get('qualType') != signature: return None
    argument = _children(call)[4]
    if argument.get('kind') != 'ImplicitCastExpr' or argument.get('castKind') != 'ArrayToPointerDecay' or argument.get('type', {}).get('qualType') != 'const char *' or len(_children(argument)) != 1: return None
    wrapper = _children(argument)[0]
    if wrapper.get('kind') != 'UnaryOperator' or wrapper.get('opcode') != '__extension__' or wrapper.get('isPostfix') is not False or wrapper.get('canOverflow') is not False or len(_children(wrapper)) != 1: return None
    predefined = _children(wrapper)[0]
    if predefined.get('kind') != 'PredefinedExpr' or predefined.get('name') != '__PRETTY_FUNCTION__' or len(_children(predefined)) != 1: return None
    literal = _children(predefined)[0]
    if _string(literal) != 'int get_new_reg(T1) [T1 = unsigned int]': return None
    if not wrapper.get('type') == predefined.get('type') == literal.get('type'): return None
    return wrapper


def _assert_source_location_diagnostics(call, tokens, expected):
    """Admit only frozen-TU file/line builtins in glibc abort diagnostics."""
    arguments = _children(call)[1:]
    if len(arguments) != 4 or not any(item.get('kind') == 'SourceLocExpr' for item in arguments): return ()
    if _assert_function_diagnostic(call) is None or not isinstance(tokens, str):
        raise Refused('initialized source-location diagnostics lack their exact abort/source binding')
    file, line = arguments[1:3]
    start, stop, _ = _slice(call, tokens); previous_end = start
    for item, builtin, result_type in ((file, '__builtin_FILE', 'const char *'), (line, '__builtin_LINE', 'unsigned int')):
        if set(item) != {'id', 'kind', 'range', 'type', 'valueCategory'} or not isinstance(item.get('id'), str) or not re.fullmatch(r'0x[0-9a-f]+', item['id']) or item.get('kind') != 'SourceLocExpr' or _children(item) or item.get('valueCategory') != 'prvalue' or item.get('type') != {'qualType': result_type} or set(item.get('range', {})) != {'begin', 'end'}:
            raise Refused('initialized source-location diagnostic is not an exact typed leaf')
        begin, end, text = _slice(item, tokens)
        if not previous_end <= begin < end <= stop or _clean(text) != builtin + '()':
            raise Refused('initialized source-location diagnostic builtin/extent changed')
        previous_end = end
        prefix = tokens.encode()[:begin].decode()
        markers = list(re.finditer(r'(?m)^#[ \t]+([1-9][0-9]*)[ \t]+("(?:\\.|[^"\\])*")(?:[ \t]+[1-4])*[ \t]*\n', prefix))
        if not markers: raise Refused('initialized source-location diagnostic has no frozen line marker')
        marker = markers[-1]
        try: source_file = json.loads(marker[2])
        except (ValueError, TypeError): raise Refused('initialized source-location diagnostic file marker is malformed') from None
        source_line = int(marker[1]) + prefix[marker.end():].count('\n')
        if not isinstance(source_file, str) or Path(source_file).name != 'MAA_gem5.hpp' or source_line != (121 if expected == 'width' else 125):
            raise Refused('initialized source-location diagnostic original file/line changed')
    return file, line


def _assertion(node, expected, variable, tokens=None):
    tree = list(_walk(node)); calls = [item for item in tree if item.get('kind') == 'CallExpr']
    names = [_callee(call) for call in calls]
    if names.count('__assert_rtn') + names.count('__assert_fail') != 1 or any(name not in {'__assert_rtn', '__assert_fail', '__builtin_expect'} for name in names) or names.count('__builtin_expect') > 1:
        raise Refused('initialized source assertion is absent or has unbound calls')
    abort = next(call for call in calls if _callee(call) in {'__assert_rtn', '__assert_fail'})
    diagnostic = _assert_function_diagnostic(abort)
    if _callee(abort) == '__assert_fail' and diagnostic is None: raise Refused('initialized Linux assertion diagnostic is not exact arity1 u32')
    source_locations = _assert_source_location_diagnostics(abort, tokens, expected)
    allowed = {'ParenExpr', 'ImplicitCastExpr', 'CXXStaticCastExpr', 'CStyleCastExpr', 'CXXFunctionalCastExpr',
               'UnaryOperator', 'BinaryOperator', 'ConditionalOperator', 'CallExpr', 'DeclRefExpr',
               'IntegerLiteral', 'PredefinedExpr', 'StringLiteral'}
    if any(item.get('kind') not in allowed and not any(item is bound for bound in source_locations) for item in tree): raise Refused('initialized assertion contains an unchecked AST effect')
    for item in tree:
        kind = item.get('kind')
        if kind == 'UnaryOperator' and item is not diagnostic and item.get('opcode') != '!':
            raise Refused('initialized assertion contains an unchecked unary effect')
        if kind == 'DeclRefExpr':
            declaration = item.get('referencedDecl', {}); name = declaration.get('name')
            if name == variable:
                if declaration.get('kind') != 'VarDecl' or declaration.get('type', {}).get('qualType') != 'int' or item.get('type', {}).get('qualType') != 'int':
                    raise Refused('initialized assertion counter/width source type changed')
            elif name not in {'__assert_rtn', '__assert_fail', '__builtin_expect'}:
                raise Refused('initialized assertion reads an unbound object')
        if kind.endswith('CastExpr'):
            cast = item.get('castKind'); target = item.get('type', {}).get('qualType')
            if cast not in {'LValueToRValue', 'IntegralCast', 'IntegralToBoolean', 'NoOp', 'ToVoid', 'FunctionToPointerDecay', 'BuiltinFnToFnPtr', 'ArrayToPointerDecay'}:
                raise Refused('initialized assertion contains an unchecked cast')
            if cast == 'IntegralCast' and target not in {'long', 'unsigned int'}: raise Refused('initialized assertion integral conversion changed')
            if cast == 'IntegralCast' and target == 'unsigned int' and _expression(item) not in {121, 125}: raise Refused('initialized assertion unsigned diagnostic conversion changed')
    binaries = [item.get('opcode') for item in tree if item.get('kind') == 'BinaryOperator']
    if sorted(binaries) != sorted(['==', '==', '||'] if expected == 'width' else ['<=', '*']): raise Refused('initialized assertion predicate census changed')
    conditional = _strip_expr(node)
    if conditional.get('kind') != 'ConditionalOperator' or len(_children(conditional)) != 3 or sum(item.get('kind') == 'ConditionalOperator' for item in tree) != 1:
        raise Refused('initialized assertion has no exact abort guard')
    condition, yes, no = _children(conditional); condition = _strip_expr(condition)
    if _callee(condition) == '__builtin_expect':
        args = _children(condition)[1:]
        if len(args) != 2 or _expression(args[1]) != 0: raise Refused('initialized assertion branch prediction changed')
        shape = _expression(args[0])
        if not isinstance(shape, tuple) or len(shape) != 2 or shape[0] != '!': raise Refused('initialized assertion abort polarity changed')
        shape, failure, success = shape[1], yes, no
    else: shape, failure, success = _expression(condition), no, yes
    predicate = ('||', ('==', ('name', variable), 1), ('==', ('name', variable), 2)) if expected == 'width' else ('<=', ('name', variable), ('*', 4, 8))
    if shape != predicate or _strip_expr(failure) is not abort or _expression(success) != 0:
        raise Refused('initialized assertion condition/abort branch changed')
    arguments = _children(abort)[1:]
    if len(arguments) != 4: raise Refused('initialized assertion abort arity changed')
    predicate_text = 'num_regs_needed == 1 || num_regs_needed == 2' if expected == 'width' else 'REG_count <= NUM_SCALAR_REGS'
    if _callee(abort) == '__assert_rtn':
        signature = 'void (const char *, const char *, int, const char *) __attribute__((noreturn))'
        reference = _strip_expr(_children(abort)[0])
        if reference.get('type', {}).get('qualType') != signature or reference.get('referencedDecl', {}).get('type', {}).get('qualType') != signature:
            raise Refused('initialized Mac assertion abort signature changed')
        function = _strip_expr(arguments[0])
        if function.get('kind') != 'PredefinedExpr' or function.get('name') != '__func__' or len(_children(function)) != 1 or _string(_children(function)[0]) != 'get_new_reg':
            raise Refused('initialized Mac assertion function diagnostic changed')
        file, line, message = arguments[1:]
    else: message, file, line, _function = arguments
    if (not source_locations and (Path(_string(file)).name != 'MAA_gem5.hpp' or _expression(line) != (121 if expected == 'width' else 125))) or _string(message) != predicate_text:
        raise Refused('initialized assertion original source diagnostic changed')


def _bodies(tokens, dumps, sources):
    signatures = {'init_MAA': ('inline void init_MAA(', 'void ()', []),
                  'get_new_reg': ('inline int get_new_reg(T1 data)', 'int (unsigned int)', ['unsigned int']),
                  'set_reg': ('inline void set_reg(', 'void (int, unsigned int)', ['int', 'unsigned int']),
                  'get_reg': ('inline volatile T1 get_reg(', 'volatile unsigned int (int)', ['int']),
                  'trust_fixture': ('int trust_fixture(', 'int ()', [])}
    if not isinstance(tokens, str) or not isinstance(dumps, dict) or set(dumps) != set(signatures): raise Refused('initialized source body census differs')
    headers = [Path(pin['path']) for pin in sources if Path(pin['path']).name == 'MAA_gem5.hpp']
    if len(headers) != 1: raise Refused('initialized source requires one already pinned original header')
    header = headers[0].read_text(); result = {}
    for name, (signature, function_type, parameter_types) in signatures.items():
        template = name in {'get_new_reg', 'set_reg', 'get_reg'}
        families = [node for node in _parse_dump(dumps[name]) if node.get('name') == name and node.get('kind') == ('FunctionTemplateDecl' if template else 'FunctionDecl')]
        if template:
            families = [family for family in families if all(sum(child.get('kind') == 'ParmVarDecl' for child in _children(function)) == len(parameter_types)
                        for function in _children(family) if function.get('kind') == 'FunctionDecl')]
        if len(families) != 1: raise Refused('initialized source family/arity is not unique: ' + name)
        variants = [node for node in _children(families[0]) if node.get('kind') == 'FunctionDecl'] if template else families
        if template:
            variants = [node for node in variants if [child.get('type', {}).get('qualType') for child in _children(node) if child.get('kind') == 'TemplateArgument'] == ['unsigned int']]
        if len(variants) != 1: raise Refused('initialized source has no unique u32 instance: ' + name)
        function = variants[0]
        if function.get('type', {}).get('qualType') != function_type or [child.get('type', {}).get('qualType') for child in _children(function) if child.get('kind') == 'ParmVarDecl'] != parameter_types or not isinstance(function.get('mangledName'), str) or not function['mangledName']:
            raise Refused('initialized source type/arity/mangled binding changed: ' + name)
        compounds = [node for node in _children(function) if node.get('kind') == 'CompoundStmt']
        if len(compounds) != 1: raise Refused('initialized source body is missing or repeated: ' + name)
        body = compounds[0]; begin, end, text = _slice(body, tokens); original = text
        if name == 'get_new_reg':
            statements = _children(body)
            if len(statements) != 7 or _callee(statements[4]) != 'set_reg': raise Refused('initialized register seven-statement/store census changed')
            call = statements[4]; arguments = _children(call)[1:]; reference = _strip_expr(_children(call)[0])
            if reference.get('type', {}).get('qualType') != 'void (int, unsigned int)' or reference.get('referencedDecl', {}).get('type', {}).get('qualType') != 'void (int, unsigned int)' or len(arguments) != 2 or [_expression(argument) for argument in arguments] != [('name', 'reg_id'), ('name', 'data')]:
                raise Refused('initialized register store must retain its exact arity1-u32 source call')
            replacements = []
            for index, kind, variable in [(1, 'width', 'num_regs_needed'), (5, 'bound', 'REG_count')]:
                statement = statements[index]; _assertion(statement, kind, variable, tokens)
                start, stop, _ = _slice(statement, tokens)
                if not begin <= start < stop <= end: raise Refused('initialized assertion leaves its source body')
                replacement = 'assert(num_regs_needed == 1 || num_regs_needed == 2)' if kind == 'width' else 'assert(REG_count <= NUM_SCALAR_REGS)'
                replacements.append((start - begin, stop - begin, replacement))
            raw = text.encode()
            for start, stop, replacement in sorted(replacements, reverse=True): raw = raw[:start] + replacement.encode() + raw[stop:]
            text = raw.decode()
        expected = _body(CALLER if name == 'trust_fixture' else header, signature)
        if _clean(text) != _clean(expected): raise Refused('initialized effective complete source body differs: ' + name)
        result[name] = {'begin': begin, 'end': end, 'body': original, 'function_type': function_type,
                        'parameter_types': parameter_types, 'mangled': function['mangledName'],
                        'template_arguments': ['unsigned int'] if template else []}
    return result


def _probe():
    # Identical to the root-retained original-source observation, 2026-10-16 ET.
    return '''
static_assert(sizeof(int)==4 && alignof(int)==4 && sizeof(unsigned int)==4 &&
              alignof(unsigned int)==4 && sizeof(uint32_t)==4 && sizeof(void*)==8,
              "initialized u32 closed ABI");
extern "C" int __dx_initialized_bounded_source(int value,unsigned int data) {
 if(value<0 || value>31) return -1;
 ::REG_count=value;
 return ::get_new_reg<unsigned int>(data);
}
extern "C" unsigned int __dx_initialized_get_source(int id) {
 if(id<0 || id>=32)return 0;
 return ::get_reg<unsigned int>(id);
}
'''


def _pin(path):
    path=Path(path).resolve()
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':_hash(path)}


def _checked_pin(pin):
    if not isinstance(pin,dict)or set(pin)!={'path','bytes','sha256'}or type(pin['bytes'])is not int:
        raise Refused('initialized physical input pin is malformed')
    path=Path(pin['path'])
    if not path.is_absolute()or path.is_symlink()or _pin(path)!=pin:raise Refused('initialized physical compiler/caller input changed')


def _recipe(c):
    runtime=c['runtime_identity'];stem=runtime['command']
    if (not isinstance(stem,list)or len(stem)!=1 or not isinstance(stem[0],str)
            or not Path(stem[0]).is_absolute()or not re.fullmatch(r'\d+\.\d+\.\d+',runtime['version'])
            or str(Path(stem[0]).resolve())!=runtime['driver']['path']):
        raise Refused('initialized compiler command/version/physical binding changed')
    _checked_pin(runtime['driver'])
    if c['standard']!='c++17'or c['defines']!=[]or not isinstance(c['includes'],list)or not c['includes']:
        raise Refused('initialized original compiler language or ambient macro policy changed')
    if len(c['includes'])!=len(set(c['includes']))or any(not isinstance(p,str)or not Path(p).is_absolute()for p in c['includes']):
        raise Refused('initialized original include context is malformed')
    if not all(isinstance(c[key],str)and Path(c[key]).is_absolute()for key in ('source_path','stage_path','dependency_path')):
        raise Refused('initialized compiler path context changed')
    prefix=[*stem,'-x','c++','-std=c++17','-fopenmp',*['-I'+p for p in c['includes']]]
    expected=[*prefix,'-E','-MD','-MF',c['dependency_path'],c['source_path']]
    frozen=[*stem,'-x','c++-cpp-output','-std=c++17','-fopenmp']
    bodies=[[*frozen,'-fsyntax-only','-Xclang','-ast-dump=json','-Xclang','-ast-dump-filter='+name,c['stage_path']]
            for name in ('init_MAA','get_new_reg','set_reg','get_reg','trust_fixture')]
    compiler=[*frozen,'-O2','-S','-emit-llvm','-o','-',c['stage_path']]
    if c['preprocess_command']!=expected or c['body_dump_commands']!=bodies or c['compiler_command']!=compiler:
        raise Refused('initialized exact original preprocessing/AST/LLVM recipe changed')


_CERT_KEYS=set('kind call entry sources termination_policy scope_statement source_path source_sha256 source_mangled '
               'runtime_identity compiler_inputs standard includes defines stage_path dependency_path preprocess_command '
               'body_dump_commands compiler_command preprocessed_source preprocessed_source_sha256 probe_source probe_source_sha256 '
               'body_dumps body_dumps_sha256 llvm_module llvm_module_sha256 observation compiler_inputs_collection runtime_scope'.split())
_INPUT_TIMING='first collected after original preprocessing; rechecked after capture'
_RUNTIME_SCOPE='selected command/version and driver bytes; complete setup/runtime admission remains separate'


def recheck(lowering):
    """Recompute every source/effect binding and physical pin before launch."""
    found=[]
    for c in bindings(lowering):
        try:
            if set(c)!=_CERT_KEYS or c['call']not in PROTOTYPES or not _same(c['entry'],ENTRY)or c['scope_statement']!=STATEMENT:
                raise Refused('initialized source/call/entry/owned scope changed')
            if c['termination_policy']!='conditional normal return; no hardware liveness'or c['compiler_inputs_collection']!=_INPUT_TIMING or c['runtime_scope']!=_RUNTIME_SCOPE:
                raise Refused('initialized observation provenance boundary changed')
            for text,digest in [('preprocessed_source','preprocessed_source_sha256'),('probe_source','probe_source_sha256'),('llvm_module','llvm_module_sha256')]:
                if hashlib.sha256(c[text].encode()).hexdigest()!=c[digest]:raise Refused('initialized retained compiler evidence changed')
            if c['probe_source']!=_probe()or c['body_dumps_sha256']!={k:hashlib.sha256(v.encode()).hexdigest()for k,v in c['body_dumps'].items()}:
                raise Refused('initialized ABI probe or complete body evidence changed')
            headers=_checked_sources(c['sources']);_recipe(c)
            expected='#include '+json.dumps(headers['MAA_gem5.hpp']['path'])+'\n'+CALLER
            if Path(c['source_path']).read_text()!=expected or _hash(c['source_path'])!=c['source_sha256']:
                raise Refused('initialized exact original closed caller translation unit changed')
            if not isinstance(c['compiler_inputs'],list)or not c['compiler_inputs']:
                raise Refused('initialized complete used-header input closure missing')
            inputs={}
            for pin in c['compiler_inputs']:
                _checked_pin(pin)
                if pin['path']in inputs:raise Refused('initialized repeated physical compiler input')
                inputs[pin['path']]=pin
            if c['source_path']not in inputs or any(headers[name]['path']not in inputs for name in ('MAA.hpp','MAA_gem5.hpp')):
                raise Refused('initialized original caller/header omitted from used-input closure')
            observed=observation(c['preprocessed_source'],c['body_dumps'],c['llvm_module'],c['sources'])
            if not _same(observed,c['observation'])or c['source_mangled']!=observed['body_bindings'][c['call']]['mangled']:
                raise Refused('initialized original source/SSA observation binding changed')
            found.append({k:c[k]for k in ('kind','call','entry','source_sha256','preprocessed_source_sha256','llvm_module_sha256','sources','compiler_inputs')})
        except (OSError,KeyError,TypeError,AttributeError,ValueError)as exc:
            if isinstance(exc,Refused):raise
            raise Refused('initialized certificate unavailable: '+str(exc))from None
    return found


def certify(unit,declaration,selected,caller,*,standard,timeout):
    """Collect the closed original TU using selected compiler observations.

    The owned source/model/MMIO assumptions remain explicit. This constructor
    does not add a premise, execute the caller, or prove a helper body.
    """
    import os,shlex,subprocess,tempfile,time
    from types import SimpleNamespace
    try:
        if not isinstance(selected,dict)or selected.get('kind')!=KIND or selected.get('call')not in PROTOTYPES or not _same(selected.get('entry'),ENTRY):
            raise Refused('initialized closed source definition refused')
        headers=_checked_sources(selected['sources']);name=selected['call']
        expected_types={'init_MAA':'void ()','get_new_reg':'int (unsigned int)','get_reg':'volatile unsigned int (int)'}
        loc=declaration.get('loc')or{};where=caller.get('loc')or{}
        if (declaration.get('name')!=name or declaration.get('type',{}).get('qualType')!=expected_types[name]
                or loc.get('spellingLoc')or loc.get('expansionLoc')
                or Path(loc.get('_file',loc.get('file',''))).resolve()!=Path(headers['MAA_gem5.hpp']['path'])):
            raise Refused('initialized declaration must be its original typed immutable-header definition')
        if (caller.get('name')!='trust_fixture'or caller.get('type',{}).get('qualType')!='int ()'
                or where.get('spellingLoc')or where.get('expansionLoc')
                or Path(where.get('_file',where.get('file',''))).resolve()!=unit.source.resolve()):
            raise Refused('initialized source requires its direct unchanged closed caller')
        if standard!='c++17'or unit.defines or type(timeout)not in (int,float)or timeout<=1:
            raise Refused('initialized compiler language/macros or active budget unsupported')
        cached=getattr(unit,'_dx100_initialized_register_certificate',None)
        if cached is not None:
            answer={**cached,'call':name,'source_mangled':declaration.get('mangledName')}
            recheck(SimpleNamespace(summaries=[{'semantic_source':answer}]))
            return answer
        command=list(unit.tool.command)
        if len(command)!=1 or not Path(command[0]).is_absolute():raise Refused('initialized compiler must be one selected absolute driver')
        runtime={'command':command,'version':unit.tool.version,'driver':_pin(command[0])}
        source_path=str(unit.source.resolve());source_hash=unit.source_digest
        expected='#include '+json.dumps(headers['MAA_gem5.hpp']['path'])+'\n'+CALLER
        if unit.source.read_text()!=expected or _hash(unit.source)!=source_hash:raise Refused('initialized original caller TU changed')
        includes=list(dict.fromkeys(str(Path(p).resolve())for p in [unit.source.parent,*unit.includes,Path(headers['MAA_gem5.hpp']['path']).parent]))
        deadline=time.monotonic()+float(timeout);probe=_probe();dumps={}
        # Preserve counted/watch ownership context, never record its token.
        env={k:os.environ[k]for k in ('HOME','TMPDIR','SWDB_VERIFIER_RUN_TOKEN','SWDB_WATCHDOG_TAG','SWDB_VERIFIER_LOCK','SWDB_VERIFIER_RSS_CAP_BYTES')if k in os.environ}
        env.update(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
        def run(argv):
            remaining=deadline-time.monotonic()-0.25
            if remaining<=0:raise Refused('initialized whole compiler-observation budget exhausted')
            try:result=subprocess.run(argv,capture_output=True,text=True,timeout=min(float(timeout),remaining),env=env)
            except (OSError,subprocess.SubprocessError)as exc:raise Refused('initialized compiler observation did not finish: '+str(exc))from None
            if result.returncode:raise Refused('initialized compiler refused source observation: '+result.stderr[-1200:])
            return result.stdout
        with tempfile.TemporaryDirectory(prefix='swdb-dx100-initialized-register-')as folder:
            path=Path(folder)/'probe.ii';dep=Path(folder)/'original.d'
            prefix=[*command,'-x','c++','-std=c++17','-fopenmp',*['-I'+p for p in includes]]
            pre=[*prefix,'-E','-MD','-MF',str(dep),source_path]
            tokens=run(pre)
            dependencies=shlex.split(dep.read_text().replace('\\\n','').split(':',1)[1])
            inputs=[_pin(p)for p in sorted({str(Path(p).resolve())for p in dependencies})]
            path.write_text(tokens+probe);frozen=[*command,'-x','c++-cpp-output','-std=c++17','-fopenmp'];commands=[]
            for family in ('init_MAA','get_new_reg','set_reg','get_reg','trust_fixture'):
                argv=[*frozen,'-fsyntax-only','-Xclang','-ast-dump=json','-Xclang','-ast-dump-filter='+family,str(path)]
                dumps[family]=run(argv);commands.append(argv)
            compiler=[*frozen,'-O2','-S','-emit-llvm','-o','-',str(path)]
            module=run(compiler)
            observed=observation(tokens,dumps,module,selected['sources'])
            digest=lambda text:hashlib.sha256(text.encode()).hexdigest()
            answer={**selected,'scope_statement':STATEMENT,'source_path':source_path,'source_sha256':source_hash,
                'source_mangled':declaration.get('mangledName'),'runtime_identity':runtime,'compiler_inputs':inputs,
                'standard':standard,'includes':includes,'defines':[],'stage_path':str(path),'dependency_path':str(dep),
                'preprocess_command':pre,'body_dump_commands':commands,'compiler_command':compiler,
                'preprocessed_source':tokens,'preprocessed_source_sha256':digest(tokens),'probe_source':probe,'probe_source_sha256':digest(probe),
                'body_dumps':dumps,'body_dumps_sha256':{k:digest(v)for k,v in dumps.items()},'llvm_module':module,'llvm_module_sha256':digest(module),
                'observation':observed,'compiler_inputs_collection':_INPUT_TIMING,'runtime_scope':_RUNTIME_SCOPE}
            recheck(SimpleNamespace(summaries=[{'semantic_source':answer}]))
        unit._dx100_initialized_register_certificate=answer
        return answer
    except (OSError,KeyError,TypeError,AttributeError,ValueError,IndexError)as exc:
        if isinstance(exc,Refused):raise
        raise Refused('initialized source/compiler certificate unavailable: '+str(exc))from None
