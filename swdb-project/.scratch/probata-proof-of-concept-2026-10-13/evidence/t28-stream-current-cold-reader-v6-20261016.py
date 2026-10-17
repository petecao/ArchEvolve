"""INERT passive current c241 stream audit; no production imports/tools/network."""
from pathlib import Path
from collections import Counter
import ast,shlex,csv,hashlib,io,json,math,re,stat,sys,xml.etree.ElementTree as ET
import yaml
H=lambda b:hashlib.sha256(b).hexdigest()
POLICY_SHA256='1649856fd197077a6cd2b6d402b94a268e2d40e3ade60dc531ba88ab35db5c74'
SOURCE_PINS = {'MAA.hpp': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd', 'MAA_gem5.hpp': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174', 'MAA.cc': '058395cbd171ccf3746fb524967d2d205cb8d622d4aa06e8eef530b00dc21299', 'SPD.cc': '9e6bb3672be95954e8816c054b4032f95811a3085ca6df418aed90ad1e852b4a', 'SPD.hh': '70e02b0fea7693585fd9b8f318381c09e352df2fff58bb3f84021f4ea02e9737', 'CpuSidePort.cc': '886a0c1bbd437916d2fac62a2aa194e01f6996fae65dc56241fad601c5f0103b', 'IF.cc': 'fd7dd67f35f63ff6ed9ef0b8ce36cb60cc6d63b20fe9c0796e648bff82da6561', 'IF.hh': '9dee4c4803a1780a41fb30b760775169000785019e6f5848689fc3f3034a1795', 'StreamAccess.cc': '5fe78a94f0d690396cdfbcdd9b0082e57cbdb4a6b445a7282b2533a33852d47b', 'StreamAccess.hh': '9ac9feb68adb525ca2d5c7d6e9046b5b0e399ad4c63a718fcca8f78cd521a3ec', 'Tables.hh': '5ea6a7caff7ca690aa9ce19096c0e686dfa52716e4dbf19d17348c9235011b43', 'Tables.cc': '9bd8aa4103fb6e7617fdd4c514a917329b8e7b8345738ed6e5d82f818df7dfa6'}
KIND = 'dx100-one-u32-stream-v1'
OWNER = 'Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'
ENTRY = {'kind': 'isolated-one-u32-stream-core0-v1', 'core': 0, 'tiles': 32, 'tile_words': 16384, 'register_words': 32, 'guest_address_bits': 64, 'byte_order': 'little', 'rf_i32': {'0': 0, '1': 1, '2': 1}, 'epoch': 'after-constructor-and-configured-quiescent-RF-before-one-command', 'input': {'symbol': 'stream_input', 'bytes': 64, 'alignment': 64, 'nonzero_guest_base': True, 'storage': 'initialized C static array', 'region': 'registered normal-memory line disjoint from MMIO', 'translation': 'stable synchronous fault-free64-byte mapping', 'visibility': 'coherent stable full physical line; no competing CPU/device writes from any core through return'}, 'commands': 'exactly one u32 stream load, no condition or competing command'}
BOOT_STATEMENT = 'This synthetic core0 unit starts with the pinned32-tile/16384-word SPD constructor state and configured4-core MMIO mapping, quiescent initialized signed-int32 RF values0/1/1 at registers0/1/2, and one registered initialized64-byte aligned normal-memory input line whose virtual base is nonzero, with stable synchronous fault-free translation and coherent no-interference visibility through normal return. These are conditional environment/source-model premises owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59); alloc/init do not establish them and arbitrary callers or physical boot are not established.'
NORMAL_RETURN_STATEMENT = 'All three MMIO helpers and this source unit are interpreted only on normal return; no termination, fairness or hardware-liveness theorem is claimed.'
COMPRESSION_STATEMENT = 'An acknowledgement establishes dispatch, not completion or still-unfinished hardware. In this isolated no-observation/no-interference caller, unobserved device events may be represented by a logically uncovered command and settled only at the returned real ready read; this source-model correspondence is owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59). All-schedule event refinement and contract/body agreement remain unverified owned TCB duties, not conclusions of finite native prefixes.'
PROTOTYPES = {'maa_stream_load': 'void maa_stream_load_unsigned_int(unsigned int *data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile)', 'wait_ready': 'void wait_ready(int SPD_id)', 'get_tile_size': 'volatile unsigned short get_tile_size(int SPD_id)'}
CANONICAL_CALLER = 'int trust_fixture() { maa_stream_load<uint32_t>(stream_input,0,1,2,0,-1); wait_ready(0); int observed=(int)get_tile_size(0); return observed; }'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()

def primary_source_bindings(references,project,reporter_sha):
 # Finite path correction only. Hash equality is required independently on Linux;
 # no case-insensitive filesystem lookup or version-based equivalence is used.
 assert len(references)==17
 root='/data1/yanruj/probata-verifiers/opam/framac-33/lib/'
 aliases={root+'frama-c-wp/core/CfgWP.ml':root+'frama-c-wp/core/cfgWP.ml',root+'frama-c-wp/core/proofEngine.ml':root+'frama-c-wp/core/ProofEngine.ml',root+'frama-c-wp/core/vCS.ml':root+'frama-c-wp/core/VCS.ml'}
 archive='/private/tmp/probata-t28-selector-frozen-review-21edecf2-20261016/swdb/proof_report.ml'
 archive_sha='0c00ed3567f3803f16735dbf95daa0f997c2f6bddefcf6fb2133fff7a862cc0d'
 assert len({(q['linux_path'],q['sha256']) for q in references})==17
 out={};historical=[];used=set()
 for index,q in enumerate(references):
  path=q['linux_path'];want=q['sha256'];assert re.fullmatch('[0-9a-f]{64}',want)
  if path==archive:
   assert want==archive_sha;historical.append({'reference_index':index,'path':path,'sha256':want,'role':'historical_local_reporter_reference_only'});continue
  assert path.startswith(root) and '..' not in Path(path).parts
  actual=aliases.get(path,path)
  if path in aliases:used.add(path)
  if actual in out:assert out[actual]['sha256']==want
  else:out[actual]={'linux_path':actual,'sha256':want,'reference_indices':[],'role':'selected_native_primary_source'}
  out[actual]['reference_indices'].append(index)
 assert used==set(aliases) and len(historical)==1 and len(out)==15
 assert re.fullmatch('[0-9a-f]{64}',reporter_sha) and reporter_sha!=archive_sha
 current=str(Path(project)/'swdb/proof_report.ml');assert current not in out
 out[current]={'linux_path':current,'sha256':reporter_sha,'reference_indices':[],'role':'current_project_reporter'}
 return {'runtime_sources':[out[k] for k in sorted(out)],'historical_local_references':historical,'reference_occurrences':17,'unique_native_sources':15,'current_project_reporters':1}

def digest(v):return H(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())

def source_identity(project,compiler):
 # Read the pinned primary identity expression, interpreting only its small
 # byte/hash/concatenation vocabulary. No Python eval or production import.
 folder=project/'swdb';text=(folder/'c_lowering.py').read_text();tree=ast.parse(text);identity=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='identity')
 digest_assignment=next(n for n in identity.body if isinstance(n,ast.Assign) and any(isinstance(q,ast.Name) and q.id=='digest' for q in n.targets));root=digest_assignment.value.func.value.args[0]
 def flatten(n):return flatten(n.left)+flatten(n.right) if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add) else [n]
 source_names=[];bytes_parts=[]
 bounded=H((folder/'bounded_initialization.py').read_bytes()+(folder/'proof_semantics.py').read_bytes()+(folder/'bounded_std_initialization.py').read_bytes()).encode()
 for n in flatten(root):
  expr=ast.get_source_segment(text,n)
  if expr=='here.read_bytes()':name='c_lowering.py';data=(folder/name).read_bytes()
  elif expr=='Path(terminal_release.__file__).read_bytes()':name='terminal_release.py';data=(folder/name).read_bytes()
  elif expr=='Path(cpu_effects.__file__).read_bytes()':name='cpu_effects.py';data=(folder/name).read_bytes()
  elif expr=='policy':name='cpu_memory_admission.py';data=(folder/name).read_bytes()
  elif expr=='bounded_initialization.identity()["sha256"].encode()':name='bounded_initialization composite';data=bounded
  elif expr=='wp_pointer_bounds.identity()["sha256"].encode()':name='wp_pointer_bounds.py sha';data=sha(folder/'wp_pointer_bounds.py').encode()
  elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='read_bytes' and isinstance(n.func.value,ast.Call) and isinstance(n.func.value.func,ast.Attribute) and n.func.value.func.attr=='with_name' and isinstance(n.func.value.func.value,ast.Name) and n.func.value.func.value.id=='here':
   name=ast.literal_eval(n.func.value.args[0]);assert isinstance(name,str) and '/' not in name;data=(folder/name).read_bytes()
  elif expr=='json.dumps(stdlib_provenance.runtime_identity(tool), sort_keys=True).encode()':name='captured compiler context';data=json.dumps(compiler,sort_keys=True).encode()
  else:raise AssertionError('unreviewed lowerer identity byte expression')
  source_names.append(name);bytes_parts.append(data)
 return {'sha256':H(b''.join(bytes_parts)),'byte_expression_components':source_names}

def checker_dependencies(project):
 # Exact typed interpretation of the pinned primary identity's dependency list,
 # including ordered vocabulary extensions. No production import or eval.
 text=(project/'swdb/proof_setup.py').read_text();tree=ast.parse(text);names=[];versions={}
 for n in tree.body:
  if isinstance(n,ast.Assign):
   for target in n.targets:
    if isinstance(target,ast.Name) and target.id in {'SETUP_VERSION','READING_VERSION'}:versions[target.id]=ast.literal_eval(n.value)
    if isinstance(target,ast.Name) and target.id=='CHECK_SOURCES':names=list(ast.literal_eval(n.value))
  if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='CHECK_SOURCES':names.extend(ast.literal_eval(n.value))
 identity=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='identity')
 extensions=[n.value for n in identity.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='dependencies' and n.value.func.attr=='extend']
 assert len(extensions)==1 and len(extensions[0].args)==1 and not extensions[0].keywords,'unreviewed primary dependency extension'
 gen=extensions[0].args[0];assert isinstance(gen,ast.GeneratorExp) and len(gen.generators)==1 and isinstance(gen.elt,ast.Tuple) and len(gen.elt.elts)==2,'unreviewed vocabulary extension shape'
 binding=gen.generators[0];assert isinstance(binding.target,ast.Name) and binding.target.id=='name' and not binding.ifs and not binding.is_async
 def shape(node):return ast.dump(node,include_attributes=False)
 expected=ast.parse('("vocab/"+name,paths.VOCAB/name)',mode='eval').body
 assert shape(gen.elt)==shape(expected),'unreviewed identity dependency path expression'
 vocab=ast.literal_eval(binding.iter);assert isinstance(vocab,tuple) and vocab==('proof_failure_classes.yaml','proof_subject_kinds.yaml'),'ordered exact e4 vocabulary closure differs'
 assert names and len(names)==len(set(names)) and all(isinstance(n,str) and '/' not in n for n in names)
 return {'versions':versions,'paths':['swdb/'+n for n in names]+['vocab/'+n for n in vocab]}

def checkers_identity(project):
 dependencies=checker_dependencies(project);d=digest([{'path':name,'sha256':sha(project/name)} for name in dependencies['paths']]);v=dependencies['versions']
 return {'proof_setup_check':{'version':v['SETUP_VERSION'],'sha256':d},'verdict_reading':{'version':v['READING_VERSION'],'sha256':d}}
def _function_ir(module, name):
    import re
    matches = list(re.finditer('^define\\b[^\\n{]*@' + re.escape(name) + '\\([^\\n]*\\)[^\\n{]*\\{(?P<body>.*?)^}', module, re.M | re.S))
    if len(matches) != 1:
        raise Refused('size source has no unique compiled function ' + name)
    return (matches[0].group(), matches[0]['body'])

def _check_getter_ir(module):
    """Closed SSA path for the exact volatile16 source load/local/fence/return."""
    import re
    function, body = _function_ir(module, '__swdb_dx100_size_certificate')
    if not re.search('\\bi16\\s+@__swdb_dx100_size_certificate\\(i32\\b', function):
        raise Refused('size getter source ABI differs from uint16(int32)')
    lines = [line.strip() for line in body.splitlines() if line.strip() and (not re.match('^\\w+:', line.strip()))]
    lines = [re.sub(', ![A-Za-z_][\\w.]* !\\d+', '', line) for line in lines]
    patterns = ['(?P<local>%[\\w.]+) = alloca i16, align 2', 'call void @llvm\\.lifetime\\.start\\.p0\\((?:i64 2, )?ptr[^,)]* (?P<local>%[\\w.]+)\\)', '(?P<base>%[\\w.]+) = load ptr, ptr @SPD_size_noncacheable, align 8', '(?P<offset>%[\\w.]+) = sext i32 (?P<argument>%[\\w.]+) to i64', '(?P<address>%[\\w.]+) = getelementptr(?: inbounds)? i16, ptr (?P<base>%[\\w.]+), i64 (?P<offset>%[\\w.]+)', '(?P<loaded>%[\\w.]+) = load volatile i16, ptr (?P<address>%[\\w.]+), align 2', 'store volatile i16 (?P<loaded>%[\\w.]+), ptr (?P<local>%[\\w.]+), align 2', '(?:tail )?call void asm sideeffect "mfence;", "(?:~\\{dirflag\\},~\\{fpsr\\},~\\{flags\\})?"\\(\\)[^\\n]*', '(?P<result>%[\\w.]+) = load volatile i16, ptr (?P<local>%[\\w.]+), align 2', 'call void @llvm\\.lifetime\\.end\\.p0\\((?:i64 2, )?ptr[^,)]* (?P<local>%[\\w.]+)\\)', 'ret i16 (?P<result>%[\\w.]+)']
    bindings = {}
    if len(lines) != len(patterns):
        raise Refused('size getter compiled operation census differs: ' + body[:1800])
    for line, pattern in zip(lines, patterns):
        match = re.fullmatch(pattern, line)
        if match is None:
            raise Refused('size getter compiled operation differs: ' + line + '; complete function: ' + body)
        for key, value in match.groupdict().items():
            if key in bindings and bindings[key] != value:
                raise Refused('size getter compiled SSA flow differs')
            bindings[key] = value
    parameter = re.search('@__swdb_dx100_size_certificate\\(i32[^,)]* (%[\\w.]+)\\)', function)
    if parameter is None or parameter[1] != bindings['argument']:
        raise Refused('size getter address is not derived from its original signed index')
    if not re.search('^target datalayout = "e-', module, re.M):
        raise Refused('size getter needs the explicit little-endian guest correspondence')
    alloc, _ = _function_ir(module, '_Z9alloc_MAAv')
    addresses = {'SPD_data_cacheable': 17179869184, 'SPD_data_noncacheable': 17181966336, 'SPD_size_noncacheable': 17184063488, 'SPD_ready_noncacheable': 17184063552, 'REG_noncacheable': 17184063616, 'INSTR_opcode_datatype_optype_tdst1_tdst2': 17184063744, 'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc': 17184063752, 'INSTR_baseaddr': 17184063760}
    for name, value in addresses.items():
        if not re.search('store ptr inttoptr \\(i64 ' + str(value) + ' to ptr\\), ptr @' + name + ', align 8\\b', alloc):
            raise Refused('source MMIO address setup/geometry differs: ' + name)
    if not re.search('store i64 17184063768, ptr @MAA_end_addr, align 8\\b', alloc):
        raise Refused('source MMIO end/geometry differs')
    return (function, bindings, addresses)

class Refused(ValueError):
    pass

def _clean(text):
    return re.sub('/\\*.*?\\*/|//[^\\n]*|\\s+', '', text, flags=re.S)

def _body(text, signature):
    at = text.index(signature)
    begin = text.index('{', at)
    depth = 0
    for end in range(begin, len(text)):
        if text[end] == '{':
            depth += 1
        elif text[end] == '}':
            depth -= 1
            if depth == 0:
                return text[begin:end + 1]
    raise Refused('immutable stream source body is not closed')

def _expected_bodies(header):
    return {name: _body(header, signature).replace('NA_UINT8', '0xFF') for name, signature in (('maa_stream_load', 'inline void maa_stream_load('), ('wait_ready', 'void wait_ready('), ('get_tile_size', 'inline volatile uint16_t get_tile_size('), ('get_data_type', 'DataType get_data_type('))}

def _check_frozen_bodies(tokens, body_bindings, sources):
    header = next((Path(p['path']).read_text() for p in sources if Path(p['path']).name == 'MAA_gem5.hpp'))
    expected = {**_expected_bodies(header), 'trust_fixture': _body(CANONICAL_CALLER, 'int trust_fixture(')}
    if set(body_bindings) != set(expected):
        raise Refused('stream frozen source body census changed')
    for name, binding in body_bindings.items():
        begin, end = (binding['begin'], binding['end'])
        text = tokens.encode()[begin:end].decode()
        if text != binding['body'] or _clean(text) != _clean(expected[name]):
            raise Refused('stream effective source body differs from immutable closed source: ' + name)
    return expected

def _check_ir(module):
    getter, flow, addresses = _check_getter_ir(module)
    stream, body = _function_ir(module, '__swdb_dx100_stream_certificate')
    if not re.search('void @__swdb_dx100_stream_certificate\\(ptr\\b', stream):
        raise Refused('stream source ABI is not void(u32 pointer)')
    lines = [re.sub(', ![A-Za-z_][\\w.]* !\\d+', '', s.strip()) for s in body.splitlines() if s.strip() and (not re.match('^\\w+:', s.strip()))]
    patterns = ['(?P<first>%[\\w.]+) = load ptr, ptr @INSTR_opcode_datatype_optype_tdst1_tdst2, align 8', 'store volatile i64 16711935, ptr (?P<first>%[\\w.]+), align 8', '(?P<second>%[\\w.]+) = load ptr, ptr @INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc, align 8', 'store volatile i64 -4294900993, ptr (?P<second>%[\\w.]+), align 8', '(?P<raw>%[\\w.]+) = ptrtoint ptr (?P<input>%[\\w.]+) to i64', '(?P<third>%[\\w.]+) = load ptr, ptr @INSTR_baseaddr, align 8', 'store volatile i64 (?P<raw>%[\\w.]+), ptr (?P<third>%[\\w.]+), align 8', '(?:tail )?call void asm sideeffect "mfence;", "(?:~\\{dirflag\\},~\\{fpsr\\},~\\{flags\\})?"\\(\\)[^\\n]*', 'ret void']
    captures = {}
    if len(lines) != len(patterns):
        raise Refused('stream compiled MMIO operation census differs: ' + body)
    for line, pattern in zip(lines, patterns):
        match = re.fullmatch(pattern, line)
        if match is None:
            raise Refused('stream compiled MMIO operation differs: ' + line + '; complete function ' + body)
        for key, value in match.groupdict().items():
            if key in captures and captures[key] != value:
                raise Refused('stream compiled MMIO SSA flow differs')
            captures[key] = value
    argument = re.search('@__swdb_dx100_stream_certificate\\(ptr[^,)]* (%[\\w.]+)\\)', stream)
    if argument is None or argument[1] != captures['input']:
        raise Refused('stream packet base does not use original input pointer')
    wait, wait_body = _function_ir(module, '__swdb_dx100_wait_certificate')
    expected = getter.replace('__swdb_dx100_size_certificate', '__swdb_dx100_wait_certificate').replace('@SPD_size_noncacheable', '@SPD_ready_noncacheable')
    expected = re.sub('[^\\n]* = load volatile i16, ptr [^\\n]+\\n(?=\\s*call void @llvm\\.lifetime\\.end)', '', expected)
    expected = re.sub('ret i16 %[^\\s]+', 'ret void', expected)
    expected_body = expected[expected.index('{') + 1:expected.rindex('}')]
    normalize = lambda b: re.sub('\\s+', '', re.sub(', ![A-Za-z_][\\w.]* !\\d+', '', b))
    if normalize(wait_body) != normalize(expected_body):
        raise Refused('stream real ready-read/fence operation differs: ' + wait_body + '; expected ' + expected_body)
    globals_found = [g.replace(' = dso_local global ', ' = global ') for g in re.findall('^@stream_input =[^\\n]*', module, re.M)]
    allowed_globals = {'@stream_input = global <{ i32, [15 x i32] }> <{ i32 7, [15 x i32] zeroinitializer }>, align 64', '@stream_input = global [16 x i32] [' + ', '.join(['i32 7'] + ['i32 0'] * 15) + '], align 64'}
    if len(globals_found) != 1 or globals_found[0] not in allowed_globals:
        raise Refused('stream original static input must retain its initialized64-byte extent and alignment: ' + str(re.findall('^@stream_input =[^\\n]*', module, re.M)))
    return {'stream': stream, 'wait': wait, 'size': getter, 'stream_ssa': captures, 'size_ssa': flow, 'mmio_addresses': addresses}

HELPERS={"maa_stream_load_unsigned_int","wait_ready","get_tile_size"}
LINEUP={"frama-c-wp":"33.0","z3":"5.1.0","cvc5":"1.2.1","alt-ergo":"2.6.4"}

def walk(value):
 if isinstance(value,dict):
  yield value
  for child in value.values():yield from walk(child)
 elif isinstance(value,list):
  for child in value:yield from walk(child)

def unique(rows,key):
 result={row[key]:row for row in rows};assert None not in result and len(result)==len(rows),'duplicate/missing '+key
 return result

def csv_properties(text):
 reader=csv.reader(io.StringIO(text),delimiter='\t');header=next(reader,[])
 assert header==['directory','file','line','function','property kind','status','property'],'property TSV header'
 result=[]
 for cells in reader:
  if not cells:continue
  if len(cells)==len(header):result.append(dict(zip(header,cells)))
  else:
   assert len(cells)==1 and cells[0][:1].isspace() and result,'malformed property TSV continuation'
   result[-1]['property']+='\n'+cells[0]
 assert result,'empty property report'
 return result

def check_passed_smoke(g,n):
 # Exact unsplit/noScript Stats.results(~smoke=true) display semantics:
 # raw best stays nonvalid, but vsmoked makes proved=1 and psmoked/qsmoked
 # normalize the winning smoke result to success=1,time=0 (not direct Valid).
 healthy={'unknown','timeout','stepout','invalid'}
 assert g['passed'] is True and g['results'] and set(g['results'])<=healthy,'passed smoke has missing, Valid, untried, or unhealthy inventory results'
 assert n is not None and n['passed'] is True,'this fixed actual profile requires retained native evidence for every smoke'
 raw=str(n.get('verdict','')).lower()
 assert raw in healthy and raw in g['results'],'passed smoke has contradictory or unhealthy raw best verdict'
 assert 'script' not in n and 'subgoals' not in n,'fixed profile requires unsplit/noScript smoke stats'
 assert type(n.get('proved')) is int and n['proved']==1,'healthy unsplit smoke requires normalized proved=1'
 assert all(type(n.get(k,0)) is int and n.get(k,0)==0 for k in ['failed','timeout','unknown','tactics','cached']),'contradictory normalized smoke counters'
 rows=unique(n['provers'],'prover');assert rows,'missing native smoke prover observations'
 if set(rows)=={'qed'}:
  assert rows['qed']['success']==1 and rows['qed']['time']==0,'qsmoked healthy result must be success1/time0'
 else:
  assert len(rows)==2 and 'qed' in rows,'unsplit external smoke requires Qed plus one best external prover'
  best=next(p for name,p in rows.items() if name!='qed')
  assert rows['qed']['success']==0 and best['success']==1 and best['time']==0,'psmoked healthy result must normalize external success1/time0'
 return {'goal':g['goal'],'raw_best_verdict':raw,'normalized_smoke_proved':n['proved'],'native_display_provers':n['provers'],'display_boundary':'Native success/proved and record solver/seconds are smoke-normalized display fields, not a direct Valid proof or external prover runtime.'}

def failure_location(error):
 # Static source expressions only: never expose frame locals, environment,
 # exception payload/validation instance, argv, or traceback source values.
 lines=[];tb=error.__traceback__;source=Path(__file__).read_text();tree=ast.parse(source)
 while tb:
  frame=tb.tb_frame
  if Path(frame.f_code.co_filename).resolve()==Path(__file__).resolve():
   line=tb.tb_lineno
   expressions=[n for n in ast.walk(tree) if isinstance(n,ast.Assert) and n.lineno<=line<=getattr(n,'end_lineno',n.lineno)]
   expr=ast.get_source_segment(source,expressions[-1].test) if expressions else None
   lines.append({'file':Path(__file__).name,'function':frame.f_code.co_name,'line':line,'assertion':expr[:1000] if expr else None})
  tb=tb.tb_next
 return {'class':type(error).__name__,'message':'Passive audit refused; inspect the pinned source locations.','locations':lines}
def same_shape(actual,expected,fields,key):
 a=unique(actual,key);b=unique(expected,key);assert set(a)==set(b),'retained complete identity census changed'
 for name in a:assert {f:a[name][f] for f in fields}=={f:b[name][f] for f in fields},'retained source/property/site shape differs'
 return a

def current_csv(rows,props,generated,failed):
 norm=lambda x:' '.join(x.split());expected={};smokes={g['property'] for g in generated.values() if g['smoke']}
 for name,p in props.items():
  desc=norm(p['description']);fn=p['function'];assert fn in HELPERS|{'trust_fixture'}
  if p['kind']=='contract':
   m=re.fullmatch(re.escape(fn)+r'_(requires|ensures|exits|terminates|assigns)(?:_[0-9]+)?',name);assert m,'unmapped contract class'
   clause=m[1];k={'requires':'precondition','ensures':'postcondition','exits':'postcondition','terminates':'termination clause','assigns':'assigns clause'}[clause]
   assert desc.startswith(clause+' ');payload=desc if clause=='assigns' else desc[len(clause)+1:];expected[name]=(k,payload)
  elif p['origin']:
   origin=props[p['origin']];callee=origin['function'];assert p['property_variant']=='IPPropertyInstance' and fn=='trust_fixture' and callee in HELPERS
   m=re.fullmatch(r"status of 'requires (.*)' of "+re.escape(callee)+r' at stmt ([0-9]+)',desc);assert m and norm(origin['description'])=='requires '+m[1]
   context=p['call_context'];assert context['caller']=='trust_fixture' and context['callee']==callee and context['line']==p['line'] and context['origin']==p['origin'] and context['statement_id']==int(m[2]) and context['source_file']==p['source_file']
   expected[name]=('precondition of '+callee,m[1])
  elif p['emitter']=='rte':
   assert desc.startswith('assert rte: initialization: ') and desc.endswith(';') and name=='trust_fixture_assert_rte_initialization'
   expected[name]=('initialization',desc[len('assert rte: initialization: '):-1])
  else:assert (name==fn and desc=='default behavior' and p['property_variant']=='IPBehavior') or (name in smokes and p['property_variant']=='IPOther' and desc in {'wp_smoke_dead_call','wp_smoke_dead_code'}),'unmapped property omitted from CSV'
 matched={};implicit=[];extern=[]
 for row in rows:
  assert row['directory']=='.' and row['file']=='wp_input.c'
  candidates=[name for name,(kind,payload) in expected.items() if props[name]['function']==row['function'] and str(props[name]['line'])==str(row['line']) and kind==row['property kind'] and payload==norm(row['property'])]
  assert len(candidates)==1 and candidates[0] not in matched,'CSV class/text/site not unique'
  name=candidates[0];p=props[name];matched[name]=row;attached=[g for g in generated.values() if g['property']==name or name in g['targets']]
  if p['extern']:
   assert p['function'] in HELPERS and row['status']=='Considered valid' and not attached and p['origin'] is None and p['dependencies']==[]
   assert re.fullmatch(re.escape(p['function'])+r'_(assigns|ensures|terminates)(?:_[0-9]+)?',name)
   if name.endswith('_terminates'):assert expected[name][1]==r'\false'
   extern.append(name)
  elif p['function'] in HELPERS:
   if name.endswith('_exits'):
    assert row['status']=='Unknown' and expected[name][1]==r'\false' and attached==[] and p['dependencies']==[] and p['origin'] is None
    implicit.append(name)
   else:
    assert '_requires' in name and row['status']=='Valid' and attached==[] and p['dependencies']
    instances=[props[k] for k in p['dependencies']];assert all(q['origin']==name for q in instances)
    for q in instances:
     actual=[g for g in generated.values() if g['property']==q['property']];assert len(actual)==1 and not actual[0]['smoke'] and actual[0]['passed'] and actual[0]['results']==['valid']
  else:
   assert attached and all(not g['smoke'] for g in attached)
   if row['status']=='Valid':assert all(g['passed'] and g['results']==['valid'] for g in attached)
   else:assert row['status']=='Unknown' and name=='trust_fixture_ensures' and all(not g['passed'] and g['goal'] in failed for g in attached)
 assert set(matched)==set(expected) and set(implicit)=={fn+'_exits' for fn in HELPERS}
 return {'CSV_rows':len(rows),'mapped_properties':len(matched),'implicit_helper_exits_unknown':implicit,'Extern_contract_properties':extern,'implicit_implementation_verified':False}

def retained_wp_input_path(exported):
 # proof.py creates run/scratch; wp_adapter._wp copies exported run/wp input.
 exported=Path(exported)
 assert exported.is_absolute() and exported.name=='wp_input.c' and exported.parent.name=='wp','exported WP input outside exact public job layout'
 return exported.parent.parent/'scratch/wp_input.c'

def ephemeral_wp_context(exported,command):
 # proof.py:532 removes scratch on completion. Exact paths are native context,
 # not retained physical artifacts; setup input/module checks attest launch bytes.
 scratch_input=retained_wp_input_path(exported);scratch=scratch_input.parent
 assert command.count('-load-module')==1 and command.count('wp_input.c')==1
 module=Path(command[command.index('-load-module')+1])
 assert module==scratch/'proof_report.cmxs'
 return {'exported':str(exported),'Frama_scratch':str(scratch_input),'report_module_context':str(module),'scratch_physical_retained':False,'compiled_module_physical_retained':False,'attribution':'exact command/native context plus pinned source and passed prelaunch checker; scratch removed by proof.py finally'}

def current_goals(record,inventory,native,csvrows,expected,expected_wp_input):
 assert inventory['version']=='1' and inventory['complete'] is True
 closure=inventory['property_closure'];assert closure['registration_membership_refreshed_after_consolidation'] is True and closure['unregistered_status_lookup_performed'] is False and closure['unregistered_wp_smoke_properties']==closure['unregistered_wp_call_instances']==[]
 props=same_shape(inventory['properties'],expected['inventory']['properties'],['function','kind','emitter','origin','dependencies','extern','generated_smoke_failure','line','description','status_registered','property_export_origin','property_variant','source_file','call_context'],'property')
 assert closure['initial_registered_snapshot_count']==closure['registered_snapshot_count']==closure['exported_count']==len(props)
 assert all(p['source_file']==str(expected_wp_input) for p in props.values()),'property source file differs from exact Frama scratch input'
 assert all(p['status_registered'] is True and p['property_export_origin']=='registered' and not p['generated_smoke_failure'] and set(p['dependencies'])<=set(props) and (p['origin'] is None or p['origin'] in props) for p in props.values())
 goals=same_shape(inventory['goals'],expected['inventory']['goals'],['property','function','line','smoke','targets'],'goal');native=unique(native,'goal');saved=unique(record['goals'],'goal');assert set(goals)==set(native)==set(saved)
 extern=[p for p in props.values() if p['extern']];assert all(p['kind']=='contract' and p['function'] in HELPERS for p in extern)
 sempin=record['pins']['proof_semantics'];assumed=[a for a in record['assumptions'] if a['kind']=='assumed_clause'];want=[{'kind':'assumed_clause','reference':sempin,'sentence':f"WP treats contract property {p['property']} of {p['function']} as Extern: {p['description'] or p['property']}."} for p in extern]
 assert Counter(json.dumps(x,sort_keys=True) for x in assumed)==Counter(json.dumps(x,sort_keys=True) for x in want),'uncertified/missing Extern assumption'
 failed=[];smokes=[];bridges=[]
 for name,g in goals.items():
  n=native[name];r=saved[name];p=props[g['property']]
  assert type(g['passed']) is bool and type(g['smoke']) is bool and g['targets']==[] and isinstance(g['results'],list) and g['results']
  assert all(v in {'valid','timeout','unknown','stepout','invalid'} for v in g['results']),'tool/resource/untried/future verdict refused'
  bridge=(g['smoke'] and g['function'] in HELPERS and p['description']=='wp_smoke_dead_call' and name=='typed_real_'+g['property'] and re.fullmatch(re.escape(g['function'])+r'_wp_smoke_dead_call_s[0-9]+',g['property']) and p['kind']=='other' and p['property_variant']=='IPOther' and p['dependencies']==[] and p['origin'] is None and p['extern'] is False and p['emitter']=='' and n['function']==r['function']=='trust_fixture')
  assert n['function']==r['function']==g['function'] or bridge,'ordinary owner or unrelated helper context mismatch'
  assert (n['property'],n['line'],n['smoke'],n['passed'])==(g['property'],g['line'],g['smoke'],g['passed'])
  assert (r['property'],r['smoke'])==(g['property'],g['smoke']) and r['source']=='wp_json' and r['status']==('valid' if n['passed'] else n['verdict'].lower())
  assert Path(n['file']).is_absolute() and Path(n['file'])==expected_wp_input,'native goal source differs from exact Frama scratch input';provers=unique(n['provers'],'prover');assert provers
  for q in provers.values():assert q['prover'] in {'qed','Z3:5.1.0','CVC5:1.2.1','Alt-Ergo:2.6.4'} and type(q['success']) is int and q['success'] in (0,1) and type(q['time']) in (int,float) and math.isfinite(q['time']) and q['time']>=0
  winner=next((q for q in provers.values() if q['success']),None);assert r['solver']==(winner['prover'].split(':')[0].lower() if winner else None) and r['seconds']==(float(winner['time'] or 0) if winner else None)
  if bridge:bridges.append(name)
  if g['smoke']:smokes.append(check_passed_smoke(g,n))
  elif g['passed']:assert g['results']==['valid'] and n['verdict']=='valid' and r['status']=='valid','ordinary pass lacks direct Valid'
  else:
   assert name=='typed_real_trust_fixture_ensures' and g['property']=='trust_fixture_ensures' and g['function']=='trust_fixture' and set(g['results'])<={'timeout','unknown','stepout'} and n['verdict'] in {'timeout','unknown','stepout'} and r['solver'] is r['seconds'] is None
   failed.append(name)
 assert smokes and any(not g['smoke'] for g in goals.values())
 if record['verdict']=='proven':assert not failed and not record.get('failure_class') and not record.get('unproven_properties')
 else:
  assert record['verdict']=='not_proven' and record['failure_class'] in {'timeout','unknown'} and failed==['typed_real_trust_fixture_ensures']
  assert record.get('unproven_properties') and all(q.get('failure_class') in {'timeout','unknown'} and (not q.get('goal') or q['goal'] in failed) for q in record['unproven_properties'])
 cross=current_csv(csvrows,props,goals,failed)
 return {'goals':len(goals),'ordinary':len(goals)-len(smokes),'smoke':len(smokes),'properties':len(props),'Extern':len(extern),'failed_ordinary':failed,'helper_context_bridges':bridges,'smoke_display_stats':smokes,'CSV_crosswalk':cross,'healthy_negative':bool(failed),'refuted':False}

def wp_source_shape(text,model,expected):
 assert type(expected) is int and expected in {0,1}
 annotations=re.findall(r'/\*@([^*]*(?:\*(?!/)[^*]*)*)\*/',text,re.S)
 assert not any(re.search(r'\b(?:axiom|axiomatic|admit|assumes)\b',a) for a in annotations)
 assert not re.search(r'__VERIFIER_assume|\\assumes',text)
 assert text.count(r'terminates \false;')==4 and text.count(model['entry'][0])==1
 clauses=re.findall(r'/\*@(?P<body>[^*]*(?:\*(?!/)[^*]*)*)\*/\s*(?P<proto>(?:volatile\s+)?(?:unsigned\s+short|void)\s+(?P<fn>get_tile_size|wait_ready|maa_stream_load_unsigned_int)\s*\([^)]*\))',text,re.S)
 assert {name for body,proto,name in clauses}==HELPERS and len(clauses)==3
 for body,proto,name in clauses:
  assert _clean(body)==_clean(model['contracts'][name])
  public='maa_stream_load' if name=='maa_stream_load_unsigned_int' else name
  assert _clean(proto)==_clean(PROTOTYPES[public])
 unit=re.findall(r'/\*@([^*]*(?:\*(?!/)[^*]*)*)\*/\s*int\s+trust_fixture\s*\(\s*(?:void\s*)?\)',text,re.S)
 assert len(unit)==1 and _clean(unit[0])==_clean(r'terminates \false; assigns __swdb_dx_stream_meta; ensures \result == '+str(expected)+';')
 return True

def stream_certificate(c,compiler,pin):
 assert c['kind']==KIND and c['call'] in {'maa_stream_load','wait_ready','get_tile_size'} and c['entry']==ENTRY
 assert c['boot_statement']==BOOT_STATEMENT and c['normal_return_statement']==NORMAL_RETURN_STATEMENT and c['pending_source_refinement']==COMPRESSION_STATEMENT
 assert c['runtime_identity']==compiler and c['termination_policy']=='conditional normal return; no hardware liveness'
 assert len(c['sources'])==len(SOURCE_PINS) and {Path(r['path']).name:r['sha256'] for r in c['sources']}==SOURCE_PINS
 for q in [*c['sources'],*c['compiler_inputs']]:pin(q['path'],q['sha256'],q['bytes'])
 pin(c['source_path'],c['source_sha256'])
 for key in ['preprocessed_source','probe_source','llvm_module']:assert H(c[key].encode())==c[key+'_sha256']
 _check_frozen_bodies(c['preprocessed_source'],c['body_bindings'],c['sources']);assert _check_ir(c['llvm_module'])==c['operations']
 return {k:c[k] for k in ['kind','call','entry','source_sha256','preprocessed_source_sha256','llvm_module_sha256','sources','compiler_inputs']}

def fixture_job_bounds(project):
 tree=ast.parse((project/'tests/testkit/dx100_trust.py').read_text());values=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='run_swdb':
   for index,arg in enumerate(node.args):
    if isinstance(arg,ast.Constant)and arg.value=='--bounds':
     assert index+1<len(node.args)and isinstance(node.args[index+1],ast.Constant)
     values.append(json.loads(node.args[index+1].value))
 assert values==[{'threads':1,'input_size':1}],'public fixture launch bounds changed'
 return values[0]

def expected_fixture_method(project,checker,lowering,naming):
 # Replay only the explicit data transformations in the pinned public fixture.
 # No production import, generated method execution or provider/tool query.
 base=yaml.safe_load((project/'tests/fixtures/proof/methods/contract-fixture-1.yaml').read_text())
 folder=project/'swdb';tree=ast.parse((folder/'cbmc_translator.py').read_text());values={}
 for node in tree.body:
  if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'TOOL_ID','TOOL_VERSION'}:values[node.targets[0].id]=ast.literal_eval(node.value)
 cbmc={'id':values['TOOL_ID']+'-'+values['TOOL_VERSION'],'sha256':H((folder/'cbmc_translator.py').read_bytes()+(folder/'bounded_entry_windows.py').read_bytes())}
 constants=ast.parse((folder/'cbmc_adapter.py').read_text());frozen=next(ast.literal_eval(q.value) for q in constants.body if isinstance(q,ast.Assign) and any(isinstance(n,ast.Name) and n.id=='FROZEN'for n in q.targets))
 base['c_lowering']['translators']=[lowering['c_lowering'],cbmc]
 next(q for q in base['lineup']if q['tool']=='cbmc')['flags']=list(frozen)
 next(q for q in base['lineup']if q['tool']=='frama-c-wp')['flags']+=['-rte-initialized','@all','-wp-no-filter-init','-machdep','x86_64']
 base.update(id='method.dx100-stream-partial-fixture-v1',sequence=2)
 base['checks'].update(checker);base['c_lowering']['naming_rules']=naming
 next(q for q in base['lineup']if q['tool']=='frama-c-wp')['flags']+=['-wp-prover','z3,cvc5,alt-ergo']
 for q in base['lineup']:
  if q['tool']in LINEUP:q['version']=LINEUP[q['tool']]
 return base

def record_envelope(r,expected,checker,compiler):
 assert r['id']==expected['id'] and r['subject']=={'kind':'partial_library_summary','id':'contract.dx100_stream_partial_fixture.v1'} and r['evidence_kind']=='contract_fixture' and r['bounds']=={'threads':1,'input_size':'unbounded'}
 settings=r['settings'];pins=r['pins'];setup=r['proof_setup_check']
 assert setup['method_version']==pins['method_version']
 # proof_setup.read_wp_reports.outcome binds reading.verdict to the actual verdict;
 # only setup verdict denotes a passed admission check.
 assert r['verdict'] in {'proven','not_proven'}
 assert setup['verdict']=='passed' and setup['check']==checker['proof_setup_check'] and r['verdict_reading']=={'check':checker['verdict_reading'],'verdict':r['verdict']}
 assert settings['compiler_runtime']==compiler and settings['flags']==expected['record_metadata']['settings']['flags'] and settings['rss_cap_bytes']==8589934592 and settings['wp_seconds_per_solver']==30 and settings['verifier_launched'] is True and settings['session']=='fresh' and settings['hint_count']==0 and settings['warning_levels']=='default' and settings['machdep']=='x86_64'
 return {'record_id':r['id'],'setup_admission':'passed','fresh_verdict_reading':r['verdict']}

def audit_records(p,raw,project,compiler,lowering,pin):
 out=[];sources=[];inputs=[];structural=[];policy_ids=[]
 for expected in p['records']:
  rp=Path(expected['path']);pin(rp,expected['sha256']);r=yaml.safe_load(rp.read_text());fixture=rp.parent.parent.parent;library=fixture/'library'
  settings=r['settings'];pins=r['pins'];setup=r['proof_setup_check'];checker=checkers_identity(project)
  record_envelope(r,expected,checker,compiler)
  methodfile=library/'methods/dx100-stream-partial-fixture-v1.yaml';method=yaml.safe_load(methodfile.read_text());assert pins['method_version']=={'id':'method.dx100-stream-partial-fixture-v1','sha256':pin(methodfile)}
  assert method==expected_fixture_method(project,checker,lowering,p['expected']['naming']),'complete source-derived fixture method differs'
  selected={q['tool']:q for q in method['lineup'] if q['tool'] in LINEUP};assert set(selected)==set(LINEUP) and all(selected[k]['version']==v for k,v in LINEUP.items())
  assert method['id']=='method.dx100-stream-partial-fixture-v1' and selected['frama-c-wp']['flags']==settings['flags'][:13]
  semfile=library/'proof_semantics/dx100_trust_fixture.yaml';sempin={'id':'semantics.dx100_stream_fixture_0_2','sha256':pin(semfile)};assert pins['proof_semantics']==sempin
  sem=yaml.safe_load(semfile.read_text());s=settings['proof_semantics'];assert s['id']==sempin['id'] and s['calls']==['get_tile_size','maa_stream_load','wait_ready'] and s['probes']==[] and s['unit_requires']==s['unit_ensures']==[]
  assert s['unit_correctness_policy']=={'kind':'partial-normal-return-v1','semantics':sempin,'source_policy':KIND} and s['termination_policy']=='conditional normal return; no hardware liveness' and s['source_refinement']=='owned TCB correspondence; all-schedule refinement and contract/body agreement unverified'
  assert s['entry_projection']=={'kind':ENTRY['kind'],'owner':OWNER,'statement':BOOT_STATEMENT}
  definitions=s['source_definitions'];assert len(definitions)==3 and {c['call'] for c in definitions}=={'maa_stream_load','wait_ready','get_tile_size'}
  checked=[stream_certificate(c,compiler,pin) for c in definitions];sourcefile=Path(definitions[0]['source_path']);source=sourcefile.read_text()
  canonical='#include '+json.dumps(str(project/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\nalignas(64) uint32_t stream_input[16]={7};\n'+CANONICAL_CALLER+'\n';assert source==canonical
  sources.append(source);assert all(c['source_path']==str(sourcefile) and c['source_sha256']==H(source.encode()) for c in definitions)
  active=[row for row in sem['calls'] if row.get('supported') is not False];assert len(active)==3 and {q['call'] for q in active}==set(PROTOTYPES)
  for q in active:
   v=q['instances'][0] if q['call']=='maa_stream_load' else q
   assert v['prototype']==PROTOTYPES[q['call']] and _clean(v['contract'])==_clean(p['model']['contracts']['maa_stream_load_unsigned_int' if q['call']=='maa_stream_load' else q['call']])
   assert v['definition']['entry']==ENTRY and v['definition']['kind']==KIND and v['definition']['call']==q['call']
  assert not sem['constants'] and not sem['queries'] and not sem['wp'] and sem['declaration_inventory']
  for key,want in [('state',p['model']['state']),('c',p['model']['c'])]:
   row=sem['model'][key];q=library/row['path'];pin(q,row['sha256']);assert q.read_text()==want
  for row in [sem['model']['logic'],sem['ghost']['acsl']]:
   q=library/row['path'];pin(q,row['sha256']);assert _clean(q.read_text())==''
  rules={q['id']:q for q in sem['rules']};required={k:rules[k]['statement'] for k in ['mmio_ordering','cross_core_filter','cross_core_write_buffer','no_stale_cpu_copy','one_instance','stream_epoch','stream_normal_return','stream_event_compression']}
  assert required['stream_epoch']==BOOT_STATEMENT and required['stream_normal_return']==NORMAL_RETURN_STATEMENT and required['stream_event_compression']==COMPRESSION_STATEMENT
  assert {k:required[k] for k in p['trust_statements']}==p['trust_statements']
  for key,statement in required.items():
   assert rules[key]['record_assumption'] is True and rules[key]['assumed']=={'owner':'Eric' if key=='no_stale_cpu_copy' else OWNER}
   assert {'kind':'proof_semantics','reference':{'id':sempin['id']+'#'+key,'sha256':sempin['sha256']},'sentence':statement} in r['assumptions']
  assert Counter((a['kind'],json.dumps(a.get('reference'),sort_keys=True),a['sentence']) for a in r['assumptions'] if a['kind']!='assumed_clause')==Counter((a['kind'],json.dumps(a.get('reference'),sort_keys=True),a['sentence']) for a in expected['record_metadata']['assumptions'] if a['kind']!='assumed_clause')
  assert not any(a['kind']=='reduction' or 'as if it finished at issue' in a['sentence'] for a in r['assumptions'])
  reports=unique(r['evidence']['reports'],'name');assert set(reports)==set(q['name'] for q in expected['record_metadata']['evidence']['reports'])
  for q in [r['evidence']['adapter_log'],*reports.values()]:
   path=Path(q['path']);assert raw in path.parents;pin(path,q['sha256'])
  wp=Path(reports['wp_input']['path']);scratch_input=retained_wp_input_path(wp);assert not scratch_input.parent.exists(),'expected completed job scratch cleanup';text=wp.read_text();inputs.append(text)
  wp_source_shape(text,p['model'],1 if r['verdict']=='proven' else 0)
  inv=json.loads(Path(reports['wp_inventory']['path']).read_text());native=json.loads(Path(reports['wp_goals']['path']).read_text());csvrows=csv_properties(Path(reports['wp_properties']['path']).read_text())
  goalout=current_goals(r,inv,native,csvrows,expected,scratch_input)
  contractfile=library/'rewrite_contracts/trust.yaml';contract=yaml.safe_load(contractfile.read_text());pin(contractfile);assert contract['proof_unit']['correctness_policy']==s['unit_correctness_policy'] and pins['contract']=={'id':contract['id'],'sha256':digest(contract)} and pins['code']==pins['contract']
  assert contract['proof_unit']['source']['sha256']==H(source.encode()) and 'array_domains' not in contract['proof_unit'] and contract['concurrency_frame']==[]
  h=setup['hashes'];assert h['contract']==pins['contract']['sha256'];lowering_file=Path(reports['c_lowering']['path']);assert pins['c_lowering']['sha256']==pin(lowering_file)==h['lowering']
  assert h['wp_input.c']==pin(wp) and h['compiler_runtime']==digest(compiler) and h['dx100_stream_source']==digest(checked) and h['dx100_size_source']==h['dx100_source_selector']==h['summaries']==h['summary_bindings']==digest([]) and h['stdlib_provenance']==digest({})
  assert len(setup['runs'])==1 and setup['runs'][0]['hashes']=={k:v for k,v in h.items() if k not in {'contract','run_plan'}}
  log=Path(r['evidence']['adapter_log']['path']).read_text();commands=[shlex.split(z[len('command: '):]) for z in log.splitlines() if z.startswith('command: ')];assert len(commands)==1
  command=commands[0];assert command[0]==p['expected']['tools']['frama-c']['path'] and command.count('-load-module')==1;ephemeral_context=ephemeral_wp_context(wp,command);assert '\ncwd: scratch\n' in log
  assert digest({'command':command,'flags':settings['flags'],'inputs':setup['runs'][0]['hashes'],'bounds':fixture_job_bounds(project),'method_version':pins['method_version']})==setup['runs'][0]['run_plan_sha256']
  structural.append([{k:g[k] for k in ['goal','property','function','line','smoke','targets']} for g in inv['goals']]);policy_ids.append(s['unit_correctness_policy'])
  out.append({'id':r['id'],'verdict':r['verdict'],'failure_class':r.get('failure_class'),'goal_audit':goalout,'source_certificates_rechecked':len(checked),'source_certificate_sha256':digest(checked),'native_input_attribution':{**ephemeral_context,'exported_and_prelaunch_input_sha256':sha(wp),'project_reporter_sha256':p['expected']['source_files']['swdb/proof_report.ml']},'owned_rule_assumptions':len(required),'conditional_normal_return_only':True})
 assert len(out)==2 and out[0]['verdict']=='proven' and out[1]['verdict']=='not_proven' and sources[0]==sources[1] and structural[0]==structural[1] and policy_ids[0]==policy_ids[1]
 # The result contract is the sole caller-query semantic difference.
 assert ''.join(inputs[0].split()).replace(r'ensures\result==1;',r'ensures\result==0;')==''.join(inputs[1].split())
 return {'records':out,'pair_scoped_partial_acceptance':True,'negative_refuted':False,'full28_or_current02':False,'hardware_liveness':False,'source_event_refinement':False,'model_contract_body_refinement':False}

def validate_launch_metadata(actual,captured,entry_sha256):
 # The root capture redacts only the long inline entry-code slot. Full physical
 # launch SHA/bytes are checked independently; every other field stays exact.
 assert isinstance(actual,dict) and isinstance(captured,dict)
 command=actual.get('command');expected=captured.get('command')
 assert isinstance(command,list) and isinstance(expected,list) and len(command)==len(expected)==9 and command[-4]=='-c'
 code=command[-3];assert isinstance(code,str) and code
 marker=expected[-3];assert isinstance(marker,dict) and set(marker)=={'omitted_payload','utf8_bytes','sha256_utf8'} and marker['omitted_payload'] is True
 observed={'omitted_payload':True,'utf8_bytes':len(code.encode()),'sha256_utf8':H(code.encode())}
 assert observed==marker and observed['sha256_utf8']==entry_sha256,'inline entry code differs from selected exact bytes'
 normalized=json.loads(json.dumps(actual));normalized['command'][-3]=observed
 assert normalized==captured,'full launch fields differ from complete compact capture'
 return {'compact_metadata_equivalent':True,'entry_code_utf8_bytes':observed['utf8_bytes'],'entry_code_sha256':observed['sha256_utf8']}

def audit(raw_arg,project_arg,policy_arg):
 raw=Path(raw_arg).resolve();project=Path(project_arg).resolve();pf=Path(policy_arg);assert sha(pf)==POLICY_SHA256
 p=json.loads(pf.read_text());e=p['expected'];assert raw==Path(p['raw']) and project==Path(p['project']);checks=0;physical={}
 def pin(path,expected=None,size=None):
  nonlocal checks
  path=Path(path);actual=sha(path);n=path.stat().st_size;assert expected is None or actual==expected,'physical hash differs';assert size is None or n==size,'physical bytes differ';checks+=1;physical[str(path)]={'sha256':actual,'bytes':n};return actual
 def raw_snapshot():
  files={};links={}
  for q in sorted(raw.rglob('*')):
   rel=str(q.relative_to(raw));mode=q.lstat().st_mode
   if stat.S_ISLNK(mode):links[rel]={'target':str(q.readlink())};continue
   assert stat.S_ISDIR(mode) or stat.S_ISREG(mode),'raw special member'
   if stat.S_ISREG(mode):files[rel]={'sha256':pin(q),'bytes':q.stat().st_size}
  assert 1<=len(files)<=20000 and sum(v['bytes'] for v in files.values())<=8589934592,'raw capture bounds exceeded'
  return {'files':files,'symlinks':links}
 before=raw_snapshot();assert before==p['raw_manifest'],'settled complete raw manifest differs';raw_files=before['files'];assert {'resources.json','outer-resources.json','lane.json','stream-collection.json','stream-profile/pytest.log','stream-profile/report.jsonl','source-after.json'}<=set(raw_files)
 launch_path=raw/'launch.json';fullpin=p['launch_physical_pin'];assert Path(fullpin['path'])==launch_path;pin(launch_path,fullpin['sha256'],fullpin['bytes']);launch=json.loads(launch_path.read_text());launch_attribution=validate_launch_metadata(launch,p['admission']['launch'],p['entry_reference']['sha256']);assert launch['source_commit']==e['source_commit'] and launch['node']==p['lane']['node'] and launch['timeout_seconds']==1200 and launch['rss_cap_bytes']==8589934592 and launch['workers']==1
 assert H(launch['command'][-3].encode())==p['entry_reference']['sha256'] and launch['command'][-2:]==[str(project),str(raw)]
 for n,h in launch['reviewed_wrapper_reuse'].items():pin(raw/n,h)
 resources={n:json.loads((raw/n).read_text()) for n in ['resources.json','outer-resources.json']}
 for n,g in resources.items():assert g['exit_code']==0 and not g['out_of_memory'] and not g['timed_out'] and 0<g['peak_rss_bytes']<8589934592 and 0<g['wall_seconds']<1200
 lane=json.loads((raw/'lane.json').read_text())['socket_lane'];assert lane==p['lane'] and lane['node'] in {0,1} and lane['exit_code']==0 and lane['job']==raw.name
 assert json.loads((raw/'source-after.json').read_text())=={'commit':e['source_commit'],'source_unchanged':True,'tracked_changes':''}
 module_manifest=json.loads((raw/'source-manifest.json').read_text());wanted={'swdb-project/'+name:h for name,h in e['source_files'].items() if name.startswith('swdb/') and name.count('/')==1 and name.endswith('.py')};assert module_manifest==wanted and len(wanted)==p['admission']['module_physical_and_git_checks']
 for rel,h in module_manifest.items():pin(project.parent/rel,h)
 assert len(e['source_files'])==465
 selected_source_preservation=[]
 for rel,h in e['source_files'].items():
  q=project/rel;pin(q,h);data=q.read_bytes();selected_source_preservation.append({'relative':rel,'sha256':h,'bytes':len(data),'git_blob_sha1':hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()})
 # Complete pre/post-bootstrap consumer receipts, never a scientific catalog read.
 closure_paths=[raw/'stream-source-consumer-closure-before.json',raw/'stream-source-consumer-closure-after-bootstrap.json'];closures=[json.loads(q.read_text()) for q in closure_paths];assert closures[0]==closures[1];closure=closures[0]
 assert closure['source_commit']==e['source_commit'] and closure['trees']==e['source_consumer_trees'] and closure['physical_git_blob_equality'] is True and closure['count']==len(closure['files'])==1542
 assert len({v['relative'] for v in closure['files']})==1542 and closure['total_bytes']==sum(v['bytes'] for v in closure['files'])
 found=set()
 for rel in e['source_consumer_trees']:
  tree=project/rel
  for q in ([tree] if tree.is_file() else tree.rglob('*')):
   mode=q.lstat().st_mode;assert stat.S_ISREG(mode) or stat.S_ISDIR(mode),'consumer symlink/special member'
   if stat.S_ISREG(mode):found.add(str(q.relative_to(project)))
 assert found=={v['relative'] for v in closure['files']},'complete consumer membership differs'
 source_stats={}
 for row in closure['files']:
  q=Path(row['path']);assert q==project/row['relative'];a=q.stat();h=hashlib.sha256();git=hashlib.sha1(('blob '+str(a.st_size)+'\0').encode())
  with q.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk);git.update(chunk)
  z=q.stat();assert (a.st_size,a.st_mtime_ns,a.st_ino)==(z.st_size,z.st_mtime_ns,z.st_ino) and a.st_size==row['bytes'] and h.hexdigest()==row['sha256'] and git.hexdigest()==row['git_blob']
  source_stats[str(q)]=(z.st_size,z.st_mtime_ns,z.st_ino);checks+=1
 # No version/config/compiler/prover query is made. These are selected bytes.
 for row in e['tools'].values():pin(row['path'],row['sha256'])
 for path,h in e['wp_artifacts'].items():pin(path,h)
 pin(e['config']['path'],e['config']['sha256']);prefix=Path(e['why3_stdlib']).parents[2]
 for key,folder in [('why3_stdlib',Path(e['why3_stdlib'])),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:
  rows=[]
  for q in sorted(folder.rglob('*')):
   mode=q.lstat().st_mode;assert stat.S_ISREG(mode) or stat.S_ISDIR(mode)
   if stat.S_ISREG(mode):rows.append({'relative':str(q.relative_to(folder)),'sha256':pin(q)})
  assert rows==e['portable_import_surfaces'][key],'complete runtime import surface differs'
 selected=json.loads((raw/'selected-stream-tool-metadata.json').read_text());assert selected['source_commit']==e['source_commit'] and selected['source_files']==e['source_files'] and selected['actual_stream_lineup']==e['actual_stream_lineup'] and selected['ambient_wp_names']==[]
 assert selected['config']==e['config'] and all(row['accepted'] is True and row['exit_code']==0 for row in selected['packages'].values())
 contexts={}
 for name in ['runtime-provenance.json','stream-project-runtime-provenance.json']:
  row=json.loads((raw/name).read_text());runtime=row['runtime'];derived=source_identity(project,runtime);assert derived['sha256']==row['lowering_identity']['c_lowering']['sha256'] and row['lowering_identity']['naming_rules']==e['naming']
  for key,want in e['linux_clang_components'].items():assert runtime[key]==want
  contexts[name]={'lowering_identity':row['lowering_identity'],'compiler':runtime,'independent_lowerer_recomputed':True}
 compiler=contexts['stream-project-runtime-provenance.json']['compiler'];frontend=compiler['frontend'];resource=Path(frontend[frontend.index('-resource-dir')+1]);llvm=resource.parents[2]
 for key in ['driver','command_executable']:pin(compiler[key]['path'],compiler[key]['sha256'])
 libs=[q.resolve() for q in [llvm/'lib/libclang.so',llvm/'lib/libclang.dylib'] if q.is_file()];assert len(libs)==1 and pin(libs[0])==compiler['parser']['sha256']
 hh=hashlib.sha256();count=0
 for label,folder in [('libc++',llvm/'include/c++/v1'),('clang-resource',resource/'include')]:
  for q in sorted(folder.rglob('*')):
   if q.is_file():hh.update(label.encode()+b'\0'+str(q.relative_to(folder)).encode()+b'\0');hh.update(bytes.fromhex(pin(q)));count+=1
 assert compiler['headers']=={'id':'llvm-standard-resource-headers','sha256':hh.hexdigest(),'files':count}
 profile=raw/'stream-profile';profile_runtime=json.loads((profile/'runtime-provenance.json').read_text());assert profile_runtime['compiler']==contexts['stream-project-runtime-provenance.json']['compiler'] and profile_runtime['lowering']==contexts['stream-project-runtime-provenance.json']['lowering_identity'] and profile_runtime['actual_stream_lineup']==e['actual_stream_lineup']
 assert profile_runtime['checks']==checkers_identity(project),'captured E4 checker identity differs'
 # Pin exact current registration-refresh reporter8b84.
 pin(project/'swdb/proof_report.ml',e['source_files']['swdb/proof_report.ml'])
 collection=json.loads((raw/'stream-collection.json').read_text());assert collection=={'cwd':str(project),'expected':p['selection'],'selected':p['selection'],'exit_code':0}
 assert (profile/'selected-tests.txt').read_text().splitlines()==p['selection'] and (profile/'profile.txt').read_text().strip()=='pair' and (profile/'exit-code.txt').read_text().strip()=='0' and (profile/'source-commit.txt').read_text().strip()==e['source_commit']
 report=[json.loads(z) for z in (profile/'report.jsonl').read_text().splitlines() if z.strip()];test=[q for q in report if q.get('$report_type')=='TestReport'];assert len(test)==6 and {q['nodeid'] for q in test}==set(p['selection']) and all(q['outcome']=='passed' for q in test)
 for name in p['selection']:assert {q['when'] for q in test if q['nodeid']==name}=={'setup','call','teardown'}
 cases=list(ET.parse(profile/'junit.xml').getroot().iter('testcase'));assert len(cases)==2 and all(not list(q.iter('failure')) and not list(q.iter('error')) for q in cases)
 primary_attribution=primary_source_bindings(p['primary_sources'],project,e['source_files']['swdb/proof_report.ml']);assert primary_attribution==p['primary_source_attribution']
 for primary in primary_attribution['runtime_sources']:pin(primary['linux_path'],primary['sha256'])
 records=audit_records(p,raw,project,compiler,contexts['stream-project-runtime-provenance.json']['lowering_identity'],pin)
 for name,st in source_stats.items():
  q=Path(name).stat();assert (q.st_size,q.st_mtime_ns,q.st_ino)==st,'consumer changed during capture'
 for path,want in list(physical.items()):assert sha(path)==want['sha256'] and Path(path).stat().st_size==want['bytes'],'physical source/runtime/report bytes changed during cold audit'
 assert raw_snapshot()==before,'raw changed during passive capture/audit'
 return {'classification':'PASS_SCOPED_PARTIAL_STREAM_PAIR','source_commit':e['source_commit'],'reader_sha256':sha(__file__),'policy_sha256':sha(pf),'launch_attribution':{'physical':fullpin,**launch_attribution},'checks':checks,'indexed_physical_files':len(physical),'module_files':len(wanted),'selected_source_files':465,'consumer_files':1542,'consumer_bytes':closure['total_bytes'],'whole_raw_regular_files':len(raw_files),'whole_raw_regular_bytes':sum(v['bytes'] for v in raw_files.values()),'runtime_contexts':contexts,'original_resources':resources,'lane':lane,'record_audit':records,'primary_source_attribution':primary_attribution,'reporter_sha256':e['source_files']['swdb/proof_report.ml'],'integrity_errors':[],'source_refinement':False,'model_contract_body_refinement':False,'hardware_liveness':False,'payload_CPU_read':False,'full28_or_current02':False,'root_owns_process_lease_settlement':True}

if __name__=='__main__':
 if not __debug__:raise SystemExit('optimized reader refused')
 try:print(json.dumps(audit(*sys.argv[1:]),sort_keys=True,indent=2))
 except Exception as error:
  print(json.dumps({'classification':'REFUSED','failure':failure_location(error),'scientific_acceptance':False},sort_keys=True));raise SystemExit(1)
