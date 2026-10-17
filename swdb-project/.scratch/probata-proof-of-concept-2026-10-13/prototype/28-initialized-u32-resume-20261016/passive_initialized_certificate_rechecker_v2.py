"""2026-10-16 ET. INERT passive initialized-u32 certificate rechecker.

Exact pure producer primitives are copied from the reviewed integrated observer
and pinned below. The V2 published commit is explicit root input; None is pending. No production module, tool runner or compiler is imported/run.
Rechecking retained source/compiler observations does not prove source-model
agreement, portable MMIO ordering, hardware/liveness or original C++ bodies.
Those remain owned TCB duties. This module supplies no current0.2/full28 claim.
Use only after root reviews and pins these bytes and supplies the complete
record/evidence/runtime audit. Python3.11+ is required by the copied hash helper.
"""
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

ORIGIN_SOURCE_COMMIT = '04af74c121a733589fbe1a2087ad602deaef598b'
ORIGIN_PINS = [{'relative': 'swdb/dx100_initialized_register_source.py', 'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/swdb/dx100_initialized_register_source.py', 'bytes': 52100, 'sha256': '01c043e544e50c30fc3d92b6be5a8b097f4dfef0606f53c29068a2ba008ac145'}, {'relative': 'swdb/dx100_initialized_register_model.py', 'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/swdb/dx100_initialized_register_model.py', 'bytes': 2351, 'sha256': 'a568c08f6e8d928ecb46212b7120b29740d719c65ae7ae818b540bcf6790961f'}, {'relative': 'swdb/dx100_register_model.py', 'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/swdb/dx100_register_model.py', 'bytes': 2662, 'sha256': '1ca71b6f3661ce5544277bec1bb8f20c8db72461cd40b99f11a2a08e7381fb76'}, {'relative': 'swdb/dx100_size_source.py', 'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/swdb/dx100_size_source.py', 'bytes': 23156, 'sha256': 'fe070713b91257d73a77112a7114c3ec049d2dc3ca8dbe0c1dfa6404c35a70f3'}]
COPIED_SOURCE_NODES = [{'name': 'KIND', 'line_start': 17, 'line_end': 17, 'sha256': 'b24287a83b6e07a3777d384f0307d93d89f35214f4be31aa9bbc0f43b70ef97e'}, {'name': 'LAYOUT', 'line_start': 18, 'line_end': 18, 'sha256': 'c9b9769a48ae470f6225e62c76b0daa4d10705f0f59531aafd83f3555fa6107b'}, {'name': 'PARTIAL_CONTRACT', 'line_start': 19, 'line_end': 19, 'sha256': '41de0eed0d1eb676851d5ab3ba32e256efcca8720b5ac8e2c697574e2e128c8c'}, {'name': 'PARTIAL_METHOD', 'line_start': 20, 'line_end': 20, 'sha256': '6d0572a2fd5dd45bd0552e4a16351703a661be11eca467ec5f7072fc64aaed84'}, {'name': 'SEMANTICS_ID', 'line_start': 21, 'line_end': 21, 'sha256': 'bf3d55dd30d13d4d4ac712901c2a17cbde7956ce9b5dee6d52eb60826b336e52'}, {'name': 'Refused', 'line_start': 24, 'line_end': 25, 'sha256': '508737932b6b6f2e19e185da1da287e853ae2d8c36484ee458b75fdf537571e6'}, {'name': 'initialized_register_layout', 'line_start': 28, 'line_end': 29, 'sha256': '5e7d0ad076015c5886dab2e0a35d7791b4eb27bb06e2f19e3337d6576d9d4481'}, {'name': '_same', 'line_start': 32, 'line_end': 36, 'sha256': 'd4b0aa99a0230adb8ed4b584fe64e4b6deb3b706e8abbe81414824dc97b718d9'}, {'name': '_hash', 'line_start': 39, 'line_end': 40, 'sha256': '935e4a379afd7df42a4881fccf8f96faf5d0c0acc5aa4f83fe951496e2b9b51a'}, {'name': 'bindings', 'line_start': 146, 'line_end': 150, 'sha256': '417d668495c025cbb3237f1850ba1a21d366e61db34241def9ab9255a0f26439'}, {'name': '_function', 'line_start': 153, 'line_end': 156, 'sha256': '80cb059e5b38dbb8befce04facf89d8b6863d18a921915feb5e162a5eed8b894'}, {'name': '_flow', 'line_start': 159, 'line_end': 188, 'sha256': '545a0e1aa9eba9a501c0dd49957ea890511b776112655964e269d2cb78fc9eb3'}, {'name': '_FENCE', 'line_start': 191, 'line_end': 191, 'sha256': 'cf8814581106952782eba63bfa0757ffd3a7df3828b5e16a291200f5ddd8877b'}, {'name': '_ABORT', 'line_start': 192, 'line_end': 192, 'sha256': 'd87199e49e18f4e7ff07feb3a4702ae4dcdda5fb97b2336eb617fc365de0e820'}, {'name': '_counter_bound_flow', 'line_start': 195, 'line_end': 222, 'sha256': 'c9f11a27687b536e6ed1fe98c62f5ba7c171b8e2b443852c8a608a50cb91ab2b'}, {'name': '_operations', 'line_start': 225, 'line_end': 294, 'sha256': '24ab92b548942c7d314487a9659b58f01d8499cd42855d00bdefb1b3bc79cb05'}, {'name': 'observation', 'line_start': 297, 'line_end': 305, 'sha256': '2c8c1cc45718454f65fa136e61b284aebb49fe74eef6a439306c159910207f38'}, {'name': '_checked_sources', 'line_start': 308, 'line_end': 321, 'sha256': '61ecbdb469e3b08a3bff349251b88044b5b791735198f1ef3629a6649914d5b5'}, {'name': '_children', 'line_start': 322, 'line_end': 326, 'sha256': '6599a3fefdb761ad39c64e4b795169944cfae4470150bdcde107c272b9270367'}, {'name': '_walk', 'line_start': 329, 'line_end': 332, 'sha256': '97107e3e0be8adef1b8b7da963a5fc2cc7a17a111ba0fb1889433dcf3cb58eb1'}, {'name': '_parse_dump', 'line_start': 335, 'line_end': 345, 'sha256': 'a10de3eb45a3ed89bb24893ef92e567d7ae768cca4c0437f0fda43aedf4cd6b1'}, {'name': '_slice', 'line_start': 348, 'line_end': 359, 'sha256': '34afe327878395a7029569ad0830d0ccb46aff01a64b27f949b9e18f4f65a9b6'}, {'name': '_clean', 'line_start': 362, 'line_end': 365, 'sha256': 'ce4eddbb3fadc71db9147de038786f118de2bc10213bec63270f5d58966580df'}, {'name': '_body', 'line_start': 368, 'line_end': 380, 'sha256': 'bd55efd1f6a7c1f1862c1a407cfd369643d26530449c820b50be874f0716b5e9'}, {'name': '_strip_expr', 'line_start': 383, 'line_end': 386, 'sha256': '9db928aeb56dfdc9f6a2124a864909fefebae72b45766f6b4c062f63476acb13'}, {'name': '_expression', 'line_start': 389, 'line_end': 398, 'sha256': '5719f01138af70f06bd5dd92d345716691b75905d945d7a5aeb80b5834502bbf'}, {'name': '_callee', 'line_start': 401, 'line_end': 406, 'sha256': '6f293f1b6b46fb4a801e4ef823ed06a6aba8c6972e32bff8105c66102d835173'}, {'name': '_string', 'line_start': 409, 'line_end': 416, 'sha256': 'ca45e61e116671fcd0d7260e0957bf5b1e825dade8e71e11d7381a8670d858de'}, {'name': '_assert_function_diagnostic', 'line_start': 419, 'line_end': 434, 'sha256': '3fc7cf25750dbdee46efb5b044c2150b49159efc8da2a5f1264ec66c41195717'}, {'name': '_assert_source_location_diagnostics', 'line_start': 437, 'line_end': 461, 'sha256': 'aabcb3749b0441c3d07157b53a68342bef5179846cf5304c130ec328848b7695'}, {'name': '_assertion', 'line_start': 464, 'line_end': 524, 'sha256': '9afbbd0bbdee41c96521c261d2e5efa75015b319a82e9b861c21d6a79df2508d'}, {'name': '_bodies', 'line_start': 527, 'line_end': 575, 'sha256': 'e7fb12bca4d49d800f45f3512fb56a70100e0a0439ca72cb41e15ab514a724ed'}, {'name': '_probe', 'line_start': 578, 'line_end': 593, 'sha256': 'ce9b66bc58b9c8862f1892b5465d30e7e267d9a689d5d0bc8847d3316da738c5'}, {'name': '_pin', 'line_start': 596, 'line_end': 598, 'sha256': 'd5fdc9a46b6fda8cd35104657199d29acbf9eddfb3c4159cba3b0ea6483e65a2'}, {'name': '_checked_pin', 'line_start': 601, 'line_end': 605, 'sha256': 'a64e15e0f031f9ec14750e1ae232b5b93294766ef07d7ce011bb950d89835ccb'}, {'name': '_recipe', 'line_start': 608, 'line_end': 628, 'sha256': 'a75e9ca13475c88ff358bf938c60df2c3013a1a18ae3c950942d832e0a5db470'}, {'name': '_CERT_KEYS', 'line_start': 631, 'line_end': 634, 'sha256': '98b797555154670c56f7291ce4836955235288c160ef9dc2f85b00d4c1cee623'}, {'name': '_INPUT_TIMING', 'line_start': 635, 'line_end': 635, 'sha256': 'db5ecbcccc56158310bb8f4d1bd7c171442838849f06e86d2aa8a35fa158e93a'}, {'name': '_RUNTIME_SCOPE', 'line_start': 636, 'line_end': 636, 'sha256': '4111c7285f166dc2bb594d8c7406a7a119368f10ddcca64196c458acf618ad4e'}, {'name': 'recheck', 'line_start': 639, 'line_end': 672, 'sha256': 'edd07df03fa46a8059639366f294cd82b8c105932e05ebf97f231579f24b4fdd'}]
OWNER = 'Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'
ENTRY = {'kind': 'isolated-initialized-u32-register-core0-v1', 'core': 0, 'register_words': 32, 'guest_address_bits': 64, 'byte_order': 'little', 'epoch': 'configured scalar MMIO mapping with no queued register packets or device commands', 'interference': 'one thread; no other-core CPU or device accesses to the scalar region through return', 'mapping': 'pinned 4-core MMIO setup; aligned fault-free synchronous noncacheable scalar range128bytes', 'initial_values': 'unconstrained; cells0and1 are written before read', 'host_counter_objects': 'REG_count, SPD_count and region_count are disjoint from the configured scalar MMIO range'}
STATEMENT = 'This original partial synthetic unit uses one configured core0 scalar MMIO range of32 four-byte words, with aligned fault-free synchronous mapping, no queued register packet/device command, and no competing CPU/device access from any core through normal return. Initial RF values are unconstrained; both observed cells are overwritten. This conditional environment/source-model premise is owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59). The source casts away volatile on its typed MMIO dereference and mfence has no memory clobber; the certificate binds exact effective source and compiler-emitted effects under recorded flags, not portable MMIO ordering or implementation correctness. The simulator RF raw-byte storage typed access, object-lifetime and alias validity are scoped runtime/compiler TCB premises, not established by native sanitizers. Source/model contract-body agreement remains an owned unverified TCB duty. No hardware termination, freshness, general interference or whole-interface claim follows. Software-counter objects are disjoint from the scalar MMIO range. init_MAA resets only software counters and establishes no RF value or hardware freshness. Each initialized allocation has an ordinary pre-write signed-domain/capacity obligation, 0 <= REG_count <= 31; it is not an environment assumption. The exact original store and fence precede the final capacity assertion. The source/model correspondence and disjoint-address premise remain owned TCB duties pending Yan-Ru freeze review (59).'
CALLER = 'int trust_fixture() { init_MAA(); int first=get_new_reg<unsigned int>(7U); int second=get_new_reg<unsigned int>(11U); return (int)(100U*get_reg<unsigned int>(first)+get_reg<unsigned int>(second)); }\n'
STATE = 'int SPD_count;\nint REG_count;\nsigned char region_count;\nstatic unsigned int __swdb_dx_reg_words[32];\n'
PROTOTYPES = {'init_MAA': 'void init_MAA(void)', 'get_new_reg': 'int get_new_reg_unsigned_int_args1(unsigned int data)', 'get_reg': 'volatile unsigned int get_reg_unsigned_int(int reg_id)'}
CONTRACTS = {'init_MAA': 'assigns SPD_count, REG_count, region_count; ensures SPD_count == 0 && REG_count == 0 && region_count == 6;', 'get_new_reg': 'requires 0 <= REG_count <= 31; terminates \\false; assigns REG_count, __swdb_dx_reg_words[REG_count]; ensures \\result == \\old(REG_count) && REG_count == \\old(REG_count) + 1 && __swdb_dx_reg_words[\\result] == data;', 'get_reg': 'requires 0 <= reg_id < 32; terminates \\false; assigns \\nothing; ensures \\result == __swdb_dx_reg_words[reg_id];'}
MODEL = 'void init_MAA(void) { REG_count=0; SPD_count=0; region_count=6; }\nint get_new_reg_unsigned_int_args1(unsigned int data) { int width=1; DX_ASSERT(width==1 || width==2); int old=REG_count; REG_count+=width; __swdb_dx_reg_words[old]=data; DX_ASSERT(REG_count<=32); return old; }\nvolatile unsigned int get_reg_unsigned_int(int reg_id) { DX_ASSERT(0<=reg_id && reg_id<32); return __swdb_dx_reg_words[reg_id]; }\n'
SOURCE_PINS = {'MAA.hpp': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd', 'MAA_gem5.hpp': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174', 'MAA.cc': '058395cbd171ccf3746fb524967d2d205cb8d622d4aa06e8eef530b00dc21299', 'SPD.cc': '9e6bb3672be95954e8816c054b4032f95811a3085ca6df418aed90ad1e852b4a', 'SPD.hh': '70e02b0fea7693585fd9b8f318381c09e352df2fff58bb3f84021f4ea02e9737', 'CpuSidePort.cc': '886a0c1bbd437916d2fac62a2aa194e01f6996fae65dc56241fad601c5f0103b', 'IF.cc': 'fd7dd67f35f63ff6ed9ef0b8ce36cb60cc6d63b20fe9c0796e648bff82da6561'}

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


# Independent passive-reader adapters below. The producer primitives above are
# exact copies; these adapters add explicit record/runtime/scope entry points.
def verify_origin_freeze(project):
    """Match copied origins to a selected source tree, without importing it."""
    if not isinstance(ORIGIN_SOURCE_COMMIT, str) or not re.fullmatch(r'[0-9a-f]{40}', ORIGIN_SOURCE_COMMIT):
        raise Refused('V2 published source commit is pending root binding')
    project = Path(project).resolve()
    checked = []
    for expected in ORIGIN_PINS:
        actual = _pin(project / expected['relative'])
        if actual['bytes'] != expected['bytes'] or actual['sha256'] != expected['sha256']:
            raise Refused('passive rechecker origin freeze differs: ' + expected['relative'])
        checked.append(actual)
    return checked


def verify_certificate(certificate, *, expected_runtime):
    """Recheck one retained certificate; expected runtime comes from root admission.

    This compares the certificate's command/version/physical-driver identity.
    It does not admit the complete loader/package/configured-runtime closure.
    Ephemeral stage/dependency files need not survive: their exact recipe and
    retained source/probe/body/LLVM hashes are checked, with timing TCB preserved.
    """
    try:
        if type(certificate) is not dict or set(certificate) != _CERT_KEYS or certificate.get('kind') != KIND:
            raise Refused('exact closed initialized source certificate required')
        runtime = certificate['runtime_identity']
        if (type(runtime) is not dict or set(runtime) != {'command', 'version', 'driver'}
                or type(expected_runtime) is not dict or not _same(runtime, expected_runtime)):
            raise Refused('root-admitted certificate compiler runtime differs')
        if not isinstance(certificate['compiler_inputs'], list) or not certificate['compiler_inputs']:
            raise Refused('retained compiler input closure required')
        input_paths = [row['path'] for row in certificate['compiler_inputs']]
        if input_paths != sorted(set(input_paths)):
            raise Refused('compiler inputs must retain producer sorted unique physical paths')
        for key in ['source_sha256', 'preprocessed_source_sha256', 'probe_source_sha256', 'llvm_module_sha256']:
            if not isinstance(certificate[key], str) or not re.fullmatch('[a-f0-9]{64}', certificate[key]):
                raise Refused('certificate digest shape changed: ' + key)
        result = recheck(SimpleNamespace(summaries=[{'semantic_source': certificate}]))
        if len(result) != 1:
            raise Refused('exactly one initialized certificate must be rechecked')
        for physical in [*certificate['sources'], *certificate['compiler_inputs'], runtime['driver']]:
            _checked_pin(physical)
        return {'call': certificate['call'], 'checked': True, 'checked_fields': sorted(_CERT_KEYS),
                'compiler_inputs': len(certificate['compiler_inputs']), 'sources': len(certificate['sources']),
                'source_mangled': certificate['source_mangled'],
                'frozen_stage_expected_sha256': hashlib.sha256((certificate['preprocessed_source'] + certificate['probe_source']).encode()).hexdigest(),
                'retained_binding': result[0], 'compiler_inputs_collection': _INPUT_TIMING,
                'runtime_scope': _RUNTIME_SCOPE, 'source_model_agreement': 'owned TCB; not proved',
                'source_body_proof': False, 'hardware_or_liveness': False}
    except (OSError, KeyError, TypeError, AttributeError, ValueError, IndexError) as error:
        if isinstance(error, Refused):
            raise
        raise Refused('passive initialized certificate unavailable: ' + str(error)) from None


def verify_record_scope(record):
    """Check the original partial model/contract scope of an already parsed record.

    The parent reader owns record/evidence schema, all reference/version hashes,
    native goals/properties/DAG/Extern/CSV closure, and runtime/process settlement.
    No YAML library or project parser is imported here.
    """
    try:
        if type(record) is not dict or record['subject'] != {'kind': 'partial_library_summary', 'id': PARTIAL_CONTRACT}:
            raise Refused('original partial initialized summary subject required')
        semantics = record['pins']['proof_semantics']
        if (type(semantics) is not dict or semantics.get('id') != SEMANTICS_ID
                or not isinstance(semantics.get('sha256'), str)
                or not re.fullmatch('[a-f0-9]{64}', semantics['sha256'])):
            raise Refused('exact initialized semantics reference required')
        if record['pins']['method_version']['id'] != PARTIAL_METHOD:
            raise Refused('original partial initialized method required')
        settings = record['settings']['proof_semantics']
        if not _same(settings['unit_requires'], []) or not _same(settings['unit_ensures'], []):
            raise Refused('original unit must gain no added premise/postcondition')
        frame = ['REG_count', 'SPD_count', 'region_count', '__swdb_dx_reg_words[0..1]']
        if not _same(settings['original_assigns_frame'], frame):
            raise Refused('original counter/two-cell frame changed')
        wanted = {'kind': 'partial-normal-return-v1', 'source_policy': KIND, 'semantics': semantics}
        if not _same(settings['unit_correctness_policy'], wanted):
            raise Refused('original partial correctness policy changed')
        if settings['termination_policy'] != 'conditional normal return; no hardware liveness':
            raise Refused('initialized termination scope changed')
        certificates = settings['source_definitions']
        if (type(certificates) is not list or len(certificates) != 3
                or any(type(c) is not dict or c.get('kind') != KIND for c in certificates)
                or {c.get('call') for c in certificates} != set(PROTOTYPES)):
            raise Refused('one certificate for each original initialized call required')
        if not any(type(a) is dict and a.get('sentence') == STATEMENT for a in record['assumptions']):
            raise Refused('exact owned source-model/disjoint-address TCB statement missing')
        return {'subject': record['subject'], 'semantics': semantics, 'frame': frame,
                'termination_policy': settings['termination_policy'], 'certificates': certificates}
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        if isinstance(error, Refused):
            raise
        raise Refused('passive initialized record scope unavailable: ' + str(error)) from None


def verify_partial_wp_scope(text, expected_result):
    """Check the sole anchored target contract, without interpreting a proof."""
    if type(text) is not str or type(expected_result) is not int or expected_result not in (711, 1107):
        raise Refused('original initialized711/1107 WP scope required')
    anchor = '/* swdb-anchor trust_fixture.contract */'
    if text.count(anchor) != 1:
        raise Refused('sole original target contract anchor required')
    unit = text.split(anchor, 1)[1]
    formal = re.match(r'\s*/\*@(?P<contract>.*?)\*/\s*int trust_fixture\(void\)\s*\{', unit, re.S)
    if formal is None:
        raise Refused('target contract must immediately precede original function')
    clauses = [part for part in _clean(formal['contract']).split(';') if part]
    wanted = {'assignsREG_count,SPD_count,region_count,__swdb_dx_reg_words[0..1]',
              'ensures\\result==' + str(expected_result), 'terminates\\false'}
    if len(clauses) != 3 or set(clauses) != wanted:
        raise Refused('original target frame/result/partial termination clauses changed')
    if text.count(r'terminates \false;') != 3:
        raise Refused('original partial target/helper termination census changed')
    return {'expected_result': expected_result, 'target_clauses': 3, 'partial_termination_clauses': 3,
            'ordinary_prewrite_domain': CONTRACTS['get_new_reg'], 'adds_original_unit_premises': False}


def verify_initialized_record(record, *, project, expected_runtime, expected_result, wp_input_text):
    """Compose passive source certificates and contract scope with a parent reader.

    Successful return admits retained observations only. The parent must bind
    wp_input_text to its evidence hash and complete independent proof/TCB audit.
    """
    origins = verify_origin_freeze(project)
    scope = verify_record_scope(record)
    receipts = [verify_certificate(certificate, expected_runtime=expected_runtime) for certificate in scope.pop('certificates')]
    wp_scope = verify_partial_wp_scope(wp_input_text, expected_result)
    return {'scope': 'passive initialized source/compiler observation and original partial contract only',
            'origin_source_commit': ORIGIN_SOURCE_COMMIT, 'origin_pins': origins,
            'record_scope': scope, 'certificates': receipts, 'wp_scope': wp_scope,
            'requires_parent_complete_property_dag_csv_runtime_audit': True,
            'source_model_agreement': 'owned TCB, not a compiler or source-body theorem',
            'source_body_proof': False, 'hardware_or_liveness': False, 'current_0_2': False, 'full_ticket28': False}
