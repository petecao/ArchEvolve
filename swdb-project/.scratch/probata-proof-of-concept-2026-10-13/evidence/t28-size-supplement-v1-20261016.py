"""Inert standalone passive size audit. Root alone executes on SETTLED raw.
Usage: python FILE RAW_ROOT FROZEN_CHECKOUT FULL_SHA POLICY_JSON
No subprocess, tool probe, production import or mutation of existing artifacts.
Exit0 clean pair; exit2 positive scoped acceptance plus explicitly diagnosed negative solver_error; exit1 integrity refusal. No refutation claim.
"""
from pathlib import Path
from collections import Counter
import ast,csv,hashlib,io,json,math,re,stat,sys,xml.etree.ElementTree as ET
import yaml
from jsonschema import Draft202012Validator

POLICY_SHA256='a922d10881a6faa9ecef1dde013f4b914caaaabc303aa4c3926dd1de4f497cc1'
LINEUP={'frama-c-wp':'33.0','z3':'5.1.0','cvc5':'1.2.1','alt-ergo':'2.6.4'}
HELPER='get_tile_size'
PURE='Only the source-certified size getter in its explicit synthetic fresh-SPD boot epoch is admitted; no device commands, arbitrary-entry freshness or timing reduction is used.'
HEADERS={'MAA.hpp':'4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd','MAA_gem5.hpp':'5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174'}

# Pure constants/functions copied by AST from pinned dx100_size_source.py; no production import.
LAYOUT = 'dx100-fresh-spd-size-v1'
CERTIFICATE_KIND = 'synthetic-fresh-spd-core0-v1'
BOOT_CERTIFICATE = {'kind': 'synthetic-fresh-spd-core0-v1', 'core': 0, 'tiles': 32, 'tile_words': 16384, 'guest_address_bits': 64, 'byte_order': 'little', 'epoch': 'after-constructor-and-address-setup-before-any-command'}
BOOT_STATEMENT = 'This synthetic fixture begins on core0 immediately after one pinned SPD constructor has completed with 32 tiles and 16,384 words per tile, and pinned 4-core MMIO-address setup has configured its globals, before commands or other accesses modify that instance. This is a conditional environment/source-model premise owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59); arbitrary callers and physical boot are not established. alloc_MAA/init_MAA do not establish freshness.'
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
SOURCE_PINS = {'MAA.hpp': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd', 'MAA_gem5.hpp': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174', 'MAA.cc': '058395cbd171ccf3746fb524967d2d205cb8d622d4aa06e8eef530b00dc21299', 'SPD.cc': '9e6bb3672be95954e8816c054b4032f95811a3085ca6df418aed90ad1e852b4a', 'SPD.hh': '70e02b0fea7693585fd9b8f318381c09e352df2fff58bb3f84021f4ea02e9737', 'CpuSidePort.cc': '886a0c1bbd437916d2fac62a2aa194e01f6996fae65dc56241fad601c5f0103b', 'IF.cc': 'fd7dd67f35f63ff6ed9ef0b8ce36cb60cc6d63b20fe9c0796e648bff82da6561'}
KIND = 'dx100-get-tile-size-v1'
PROTOTYPE = 'volatile unsigned short get_tile_size(int SPD_id)'
CONTRACT = 'requires 0 <= SPD_id < 32; assigns \\nothing; ensures \\result == __swdb_dx_size_bytes[2*SPD_id] + 256*__swdb_dx_size_bytes[2*SPD_id+1];'
STATE = 'static unsigned char __swdb_dx_size_bytes[64];\n'
MODEL = 'volatile unsigned short get_tile_size(int SPD_id) {\n  DX_ASSERT(0 <= SPD_id && SPD_id < 32);\n  return (unsigned short)(__swdb_dx_size_bytes[2*SPD_id] + 256U*__swdb_dx_size_bytes[2*SPD_id+1]);\n}\n'
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
CALLER_BINDING = {'function': 'trust_fixture', 'return_type': 'int', 'parameter_count': 0, 'local': 'observed', 'initializer_call': 'get_tile_size', 'literal_int_argument': 0, 'return_local': 'observed', 'other_statements': 0}
GETTER_BINDING = {'function': 'get_tile_size', 'body_statements': 'DeclStmt,GCCAsmStmt,ReturnStmt', 'source_body_macros': 0, 'volatile_metadata_bits': 16, 'index_bits': 32, 'packet_core': 0, 'packet_bytes': 2, 'required_status': 'Finished', 'covering_wait': False, 'ready_read_scope': 'separate blocking read returns1; not admitted here'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
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
def check_lineup(method,actual):
 assert actual==LINEUP,'captured root actual lineup mismatch'
 rows=unique(method['lineup'],'tool')
 assert all(rows[name]['version']==version for name,version in actual.items()),'generated fixture version differs from actual root pin'
def check_method_checks(method,checks):
 assert all(method['checks'].get(name)==value for name,value in checks.items()),'actual checker identity mismatch'
 assert set(method['checks'])==set(checks)|{'proof_hint_check'} and method['checks']['proof_hint_check']=={'version':'0'},'unexpected fixture checker shape'

def helper_dead_call_context(name,g,r,n,p):
 # Frama33 register.stats_to_json uses po_idx caller, while proof_report
 # uses Property.get_kf(property). Only this fixed helper dead-call smoke
 # may bridge those distinct fields; every identity/status/line stays checked.
 return bool(n is not None and name=='typed_real_get_tile_size_wp_smoke_dead_call_s65'
  and g['property']==r['property']==n['property']=='get_tile_size_wp_smoke_dead_call_s65'
  and g['function']==p['function']==HELPER and r['function']==n['function']=='trust_fixture'
  and g['smoke'] is True and r['smoke'] is True and n['smoke'] is True
  and g['passed'] is True and n['passed'] is True and r['status']=='valid'
  and type(g['line']) is int and g['line']>0 and g['line']==n['line']==p['line']
  and g['targets']==[] and p['dependencies']==[] and p.get('origin') is None
  and p['kind']=='other' and p['extern'] is False and p['generated_smoke_failure'] is False
  and g['results'] and set(g['results'])<={'timeout','unknown','stepout','invalid'})

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

def csv_attribution(properties,props,generated,failed):
 # Report.Description exports predicate payloads without ensures/exits/terminates
 # labels. Match class, exact property identity and payload, never line alone.
 def norm(text):return ' '.join(text.split())
 expected={};smoke_properties={g['property'] for g in generated.values() if g['smoke']}
 for ident,p in props.items():
  fn=p['function'];desc=norm(p['description'])
  assert fn in {HELPER,'trust_fixture'},'property owner outside fixed size profile'
  if p['kind']=='contract':
   forms={'requires':('precondition','requires'),'ensures':('postcondition','ensures'),'exits':('postcondition','exits'),'terminates':('termination clause','terminates'),'assigns':('assigns clause',None)}
   matches=[(suffix,kind,prefix) for suffix,(kind,prefix) in forms.items() if ident==fn+'_'+suffix]
   assert len(matches)==1,'unknown contract property class in fixed size inventory'
   suffix,kind,prefix=matches[0]
   if prefix:
    assert desc.startswith(prefix+' '),'inventory clause name/description mismatch'
    payload=desc[len(prefix)+1:]
   else:
    assert desc.startswith('assigns '),'inventory assigns description mismatch'
    payload=desc
   expected[ident]=(kind,payload)
  elif ident=='get_tile_size_requires_2':
   assert p['kind']=='other' and p['function']=='trust_fixture' and p['origin']=='get_tile_size_requires' and p['dependencies']==[] and p['extern'] is False and p['emitter']==''
   assert desc=="status of 'requires 0 ≤ SPD_id < 32' of get_tile_size at stmt 65",'call-site requires instance description differs'
   expected[ident]=('precondition of get_tile_size','0 ≤ SPD_id < 32')
  elif ident=='trust_fixture_assert_rte_initialization':
   prefix='assert rte: initialization: '
   assert p['kind']=='other' and p['emitter']=='rte' and desc.startswith(prefix) and desc.endswith(';'),'initialization class/description mismatch'
   payload=desc[len(prefix):-1]
   assert payload==r'\initialized(&observed)','unexpected selected initialization property'
   expected[ident]=('initialization',payload)
  else:
   behavior=ident==fn and p['kind']=='other' and desc=='default behavior'
   smoke=ident in smoke_properties and p['kind']=='other' and desc==('wp_smoke_dead_call' if fn==HELPER else 'wp_smoke_dead_code')
   assert behavior or smoke,'unmapped property silently excluded from CSV crosswalk'
 matched={};out={'rows':[],'selected_failed':[],'unselected_implicit_unknown':[]}
 for row in properties:
  assert row['file']=='wp_input.c' and row['directory']=='.','unexpected property report source'
  matches=[ident for ident,(kind,payload) in expected.items() if props[ident]['function']==row['function'] and str(props[ident]['line'])==str(row['line']) and kind==row['property kind'] and payload==norm(row['property'])]
  assert len(matches)==1,'CSV class/text/location does not identify one inventory property'
  ident=matches[0];p=props[ident]
  assert ident not in matched,'duplicate CSV property'
  matched[ident]=row;attached=[g for g in generated.values() if g['property']==ident or ident in g['targets']]
  if ident=='get_tile_size_requires':
   instance=props['get_tile_size_requires_2'];actual=[g for g in generated.values() if g['property']==instance['property']]
   assert row['status']=='Valid' and expected[ident][1]=='0 ≤ SPD_id < 32' and p['extern'] is False and p['origin'] is None and p['dependencies']==['get_tile_size_requires_2'] and p['emitter']==''
   assert not attached and len(actual)==1 and actual[0]['goal']=='typed_real_trust_fixture_call_get_tile_size_requires' and actual[0]['passed'] is True and actual[0]['smoke'] is False and actual[0]['results']==['valid'],'requires source-to-call instance lacks complete direct Valid evidence'
  elif p['function']==HELPER:
   implicit=ident in {HELPER+'_exits',HELPER+'_terminates'}
   if implicit:
    payload=r'\false' if ident.endswith('_exits') else r'\true'
    assert row['status']=='Unknown' and expected[ident][1]==payload and not attached,'unselected implicit helper clause has changed status/text or generated goal'
    assert p['extern'] is False and p['dependencies']==[] and p['origin'] is None and p['emitter']=='' and p['generated_smoke_failure'] is False,'implicit helper clause changed provenance'
    out['unselected_implicit_unknown'].append({'property':ident,'description':p['description'],'status':'Unknown','generated_goals':[],'implementation_verified':False,'boundary':'Unselected implicit helper clause; not a proven implementation or an added Extern assumption.'})
   else:
    assert ident in {HELPER+'_ensures',HELPER+'_assigns'} and row['status']=='Considered valid' and p['extern'] is True and not attached,'helper summary differs from exact Extern contract evidence'
  else:
   assert p['extern'] is False and attached and all(not g['smoke'] for g in attached),'selected clause lacks ordinary generated evidence'
   if row['status']=='Valid':
    assert all(g['passed'] and 'valid' in g['results'] for g in attached),'Valid CSV row masks a failed selected goal'
   else:
    assert row['status']=='Unknown' and ident=='trust_fixture_ensures','unexpected selected non-Valid property'
    doomed=[g['goal'] for g in attached]
    assert doomed and set(doomed)<=set(failed) and all(not g['passed'] for g in attached),'selected Unknown lacks exact failing ordinary ensures'
    out['selected_failed'].append({'property':ident,'goals':doomed,'payload':row['property'],'status':row['status']})
  out['rows'].append({'property':ident,'kind':row['property kind'],'status':row['status'],'function':row['function'],'line':row['line']})
 assert set(matched)==set(expected),'CSV report omits an inventory reportable clause'
 assert {x['property'] for x in out['unselected_implicit_unknown']}=={HELPER+'_exits',HELPER+'_terminates'},'missing exact implicit unselected helper clauses'
 return out

def check_goals(record,inventory,native,properties,semantics_pin,*,diagnose_solver_error=False):
 assert inventory['complete'] is True and inventory['version']=='1'
 generated=unique(inventory['goals'],'goal');reported=unique(native,'goal');recorded=unique(record['goals'],'goal');props=unique(inventory['properties'],'property')
 assert generated and set(recorded)==set(generated) and set(reported)<=set(generated),'complete goal census mismatch'
 assert all(set(p['dependencies'])<=set(props) and (not p.get('origin') or p['origin'] in props) for p in props.values()),'property dependency escapes complete inventory'
 assert all(not p['generated_smoke_failure'] for p in props.values()),'global generated smoke failure'
 extern=[p for p in props.values() if p['extern']]
 assert all(p['function']==HELPER and p['kind']=='contract' for p in extern),'uncertified Extern property'
 assumed=[a for a in record['assumptions'] if a['kind']=='assumed_clause']
 expected_assumed=[{'kind':'assumed_clause','reference':semantics_pin,'sentence':f"WP treats contract property {p['property']} of {HELPER} as Extern: {p['description'] or p['property']}."} for p in extern]
 assert Counter(json.dumps(a,sort_keys=True) for a in assumed)==Counter(json.dumps(a,sort_keys=True) for a in expected_assumed),'assumed_clause differs from exact source-certified helper Extern census'
 expected_goals={
  'typed_real_get_tile_size_wp_smoke_dead_call_s65':('get_tile_size_wp_smoke_dead_call_s65','get_tile_size',86,True),
  'typed_real_trust_fixture_wp_smoke_dead_code_s68':('trust_fixture_wp_smoke_dead_code_s68','trust_fixture',89,True),
  'typed_real_trust_fixture_terminates':('trust_fixture_terminates','trust_fixture',18,False),
  'typed_real_trust_fixture_ensures':('trust_fixture_ensures','trust_fixture',17,False),
  'typed_real_trust_fixture_exits':('trust_fixture_exits','trust_fixture',18,False),
  'typed_real_trust_fixture_assert_rte_initialization':('trust_fixture_assert_rte_initialization','trust_fixture',89,False),
  'typed_real_trust_fixture_call_get_tile_size_requires':('get_tile_size_requires_2','trust_fixture',86,False),
  **{'typed_real_trust_fixture_assigns_'+suffix:('trust_fixture_assigns','trust_fixture',17,False) for suffix in ['normal_part1','normal_part2','exit']}}
 assert set(generated)==set(reported)==set(expected_goals),'this fixed profile requires every original ordinary/smoke native attempt'
 assert all((g['property'],g['function'],g['line'],g['smoke'])==expected_goals[name] and g['targets']==[] for name,g in generated.items()),'fixed size goal/property/site census differs'
 assert set(props)=={'get_tile_size','trust_fixture','get_tile_size_requires','get_tile_size_requires_2','get_tile_size_assigns','get_tile_size_ensures','get_tile_size_exits','get_tile_size_terminates','get_tile_size_wp_smoke_dead_call_s65','trust_fixture_assigns','trust_fixture_ensures','trust_fixture_exits','trust_fixture_terminates','trust_fixture_assert_rte_initialization','trust_fixture_wp_smoke_dead_code_s68'},'fixed complete property census differs'
 assert {p['property'] for p in extern}=={'get_tile_size_assigns','get_tile_size_ensures'},'size Extern contract census differs'
 if diagnose_solver_error:
  assert record['verdict']=='not_proven' and record['failure_class']=='solver_error','diagnostic mode is exclusively the captured solver_error negative'
 failed=[];smokes=[];owner_context=[];smoke_stats=[];tool_error_goals=[]
 for name,g in generated.items():
  assert g['property'] in props and set(g['targets'])<=set(props),'goal property/target outside inventory'
  assert type(g['smoke']) is bool and type(g['passed']) is bool and isinstance(g['results'],list)
  r=recorded[name];bridge=helper_dead_call_context(name,g,r,reported.get(name),props[g['property']])
  assert (r['property'],r['smoke'])==(g['property'],g['smoke']) and (r['function']==g['function'] or bridge),'record context/property ownership mismatch'
  assert g['function']=='trust_fixture' or bridge,'unexpected selected function'
  if bridge:owner_context.append({'goal':name,'property':g['property'],'inventory_property_owner':g['function'],'native_record_context':r['function'],'line':g['line'],'basis':'Exact source-certified helper dead-call smoke only'})
  if name in reported:
   n=reported[name]
   assert (n['property'],n['line'],n['smoke'],n['passed'])==(g['property'],g['line'],g['smoke'],g['passed']) and (n['function']==g['function'] or bridge),'native context/property ownership mismatch'
   assert Path(n['file']).name=='wp_input.c' and Path(n['file']).is_absolute()
   assert isinstance(n['provers'],list)
   for prover in n['provers']:
    assert prover['prover'] in {'qed','Z3:5.1.0','CVC5:1.2.1','Alt-Ergo:2.6.4'},'unadmitted native prover label'
    assert prover['success'] in (0,1) and type(prover['time']) in (int,float) and math.isfinite(prover['time']) and prover['time']>=0
   winner=next((p for p in n['provers'] if p['success']),None)
   assert r['solver']==(winner['prover'].split(':')[0].lower() if winner else None) and r['seconds']==(float(winner['time'] or 0) if winner else None),'native solver/timing differs from record'
   expected_status='valid' if n['passed'] else str(n.get('verdict') or 'unknown').lower()
   assert r['source']=='wp_json' and r['status']==expected_status
  else:
   assert r['solver'] is None and r['seconds'] is None,'inventory-only goal invented solver/timing'
   assert r['source']=='wp_inventory' and r['status']==('valid' if g['passed'] and (g['smoke'] or 'valid' in g['results']) else 'unknown')
  if g['smoke']:
   assert g['passed'] and r['status']=='valid','failed or nonpassed smoke'
   smoke_stats.append(check_passed_smoke(g,reported.get(name)))
   smokes.append(name)
  elif g['passed']:
   assert g['results']==['valid'] and r['status']=='valid','ordinary pass without exclusive healthy direct Valid inventory result'
  else:
   if diagnose_solver_error:
    assert name=='typed_real_trust_fixture_ensures' and g['property']=='trust_fixture_ensures' and g['results']==['failed','unknown','timeout'],'solver-error diagnostic differs from exact captured ordinary ensures portfolio'
    assert name in reported and reported[name]['verdict']=='timeout' and reported[name]['passed'] is False and r['status']=='timeout' and r['solver'] is None and r['seconds'] is None,'solver-error diagnostic native/record best verdict differs'
    tool_error_goals.append(name)
   else:assert set(g['results'] or ['unknown'])<= {'unknown','timeout','stepout','untried'},'tool/resource failure in ordinary negative' 
   assert 'ensures' in name and r['status']!='valid','non-ensures ordinary failure'
   failed.append(name)
 assert smokes and any(not g['smoke'] for g in generated.values()),'missing ordinary/smoke coverage'
 attribution=csv_attribution(properties,props,generated,failed)
 if record['verdict']=='proven':assert not failed and not record.get('unproven_properties') and record.get('failure_class') is None
 else:
  assert record['verdict']=='not_proven' and failed and record['failure_class'] in ({'solver_error'} if diagnose_solver_error else {'unknown','timeout'})
  unproven=record['unproven_properties'];assert unproven and set(failed)<={p.get('goal') for p in unproven}
  assert all(p['failure_class'] in ({'solver_error'} if diagnose_solver_error else {'unknown','timeout'}) and (not p.get('goal') or p['goal'] in failed) for p in unproven),'unexplained unproven record property'
 if diagnose_solver_error:
  assert failed==tool_error_goals==['typed_real_trust_fixture_ensures'],'diagnostic includes unrelated ordinary failure'
  failed_csv=attribution['selected_failed'];assert len(failed_csv)==1 and failed_csv[0]['property']=='trust_fixture_ensures'
  expected_unproven=[{'failure_class':'solver_error','function':'trust_fixture','goal':failed[0],'kind':'postcondition','line':17,'property':failed_csv[0]['payload'],'status':'Unknown'},{'failure_class':'solver_error','goal':failed[0],'property':'trust_fixture_ensures','status':'timeout'}]
  assert Counter(json.dumps(p,sort_keys=True) for p in record['unproven_properties'])==Counter(json.dumps(p,sort_keys=True) for p in expected_unproven),'solver-error diagnostic unproven census differs from exact CSV/native rows' 
 return {'clean_acceptance':not diagnose_solver_error,'diagnostic_solver_error_goals':tool_error_goals,'solver_error_boundary':('Failed portfolio verdict is retained; the frozen reporter did not retain the per-prover error detail, so the cause remains undiagnosed.' if tool_error_goals else None),'refuted':False,'csv_attribution':attribution,'smoke_native_stats':smoke_stats,'owner_context_distinctions':owner_context,'goals':len(generated),'ordinary':len(generated)-len(smokes),'smokes':len(smokes),'properties':len(props),'extern_properties':[p['property'] for p in extern],'failed_ordinary':failed,'dependency_edges':sum(len(p['dependencies'])+bool(p.get('origin')) for p in props.values()),'initialized_property_descriptions':sum('initializ' in p['description'].lower() for p in props.values())}
def flags_ok(flags):
 def values(key):
  return [str(flags[i+1]) for i,f in enumerate(flags[:-1]) if f==key]+[str(f).split('=',1)[1] for f in flags if str(f).startswith(key+'=')]
 for required,opposite in [('-wp-rte','-wp-no-rte'),('-wp-no-filter-init','-wp-filter-init')]:
  assert flags.count(required)==1 and not any(f==opposite or str(f).startswith((required+'=',opposite+'=')) for f in flags)
 for key,value in [('-rte-initialized','@all'),('-wp-cache','none'),('-wp-par','1'),('-machdep','x86_64'),('-wp-model','+real'),('-wp-fct','trust_fixture')]:
  assert values(key) and set(values(key))=={value},'unsafe or missing '+key
 assert '-wp-smoke-tests' in flags
 assert not any(str(f).startswith(('-wp-prop','-wp-session','-wp-script','-wp-cache-dir','-load')) or 'warn-key' in str(f) for f in flags)
 assert values('-wp-prover') and all(set(v.split(','))=={'z3','cvc5','alt-ergo'} for v in values('-wp-prover'))
def check_definition(d,runtime,project,pin):
 assert set(d)=={'kind','entry','sources','projection','source_path','source_sha256','source_mangled','caller_shape','caller_binding','getter_binding','compiler_inputs','runtime_identity','preprocess_command','compiler_command','preprocessed_source','preprocessed_source_sha256','probe_source','probe_source_sha256','llvm_module','llvm_module_sha256','llvm_function','ssa_flow','mmio_addresses','boot_statement'},'certificate key closure differs'
 assert d['kind']==KIND and d['entry']==BOOT_CERTIFICATE and digest(d['projection'])==digest(constructor_projection(d['entry']))
 assert d['boot_statement']==BOOT_STATEMENT and d['runtime_identity']==runtime,'certificate boot/runtime differs'
 assert digest(d['caller_binding'])==digest(CALLER_BINDING) and digest(d['getter_binding'])==digest(GETTER_BINDING),'certificate source-binding metadata differs'
 assert d['source_mangled'] in {'_Z13get_tile_sizei','__Z13get_tile_sizei'}
 expected_source='#include '+json.dumps(str(project/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\nint trust_fixture() { int observed=(int)get_tile_size(0); return observed; }\n'
 assert d['caller_shape']=='int trust_fixture() { int observed=(int)get_tile_size(0); return observed; }'
 assert Path(d['source_path']).read_text()==expected_source and sha(d['source_path'])==d['source_sha256'],'original caller source differs'
 assert len(d['sources'])==len(SOURCE_PINS) and {Path(p['path']).name:p['sha256'] for p in d['sources']}==SOURCE_PINS
 for item in d['sources']+d['compiler_inputs']:pin(item['path'],item['sha256'],item.get('bytes'))
 assert d['compiler_inputs'] and len({p['path'] for p in d['compiler_inputs']})==len(d['compiler_inputs'])
 inputs={str(Path(p['path']).resolve()) for p in d['compiler_inputs']};assert str(Path(d['source_path']).resolve()) in inputs
 assert all(str(Path(h['path']).resolve()) in inputs for h in d['sources'] if Path(h['path']).suffix=='.hpp')
 markers={str(Path(json.loads(m)).resolve()) for m in re.findall(r'^#\s+\d+\s+("[^"\n]+")',d['preprocessed_source'],re.M) if not json.loads(m).startswith('<')}
 assert markers<=inputs,'preprocessed physical input omitted'
 for text in ('preprocessed_source','probe_source','llvm_module'):assert hashlib.sha256(d[text].encode()).hexdigest()==d[text+'_sha256']
 getter='inline volatile uint16_t get_tile_size(int SPD_id) { volatile uint16_t sz = SPD_size_noncacheable[SPD_id]; __asm__ __volatile__("mfence;"); return sz; }'
 clean=lambda text:re.sub(r'\s+','',text)
 assert clean(getter) in clean(d['preprocessed_source']) and clean(d['caller_shape']) in clean(d['preprocessed_source']),'frozen effective source getter/caller differs'
 expected_probe='\nextern "C" unsigned short __swdb_dx100_size_certificate(int id) { return ::get_tile_size(id); }\n';assert d['probe_source']==expected_probe
 command=d['compiler_command'];assert command[:len(runtime['command'])]==runtime['command']
 assert command[len(runtime['command']):-1]==['-x','c++-cpp-output','-std=c++17','-fopenmp','-O2','-S','-emit-llvm','-o','-']
 preprocess=d['preprocess_command'];assert preprocess[:len(runtime['command'])+4]==runtime['command']+['-x','c++','-std=c++17','-fopenmp'] and '-E' in preprocess and '-MD' in preprocess and preprocess[-1]==d['source_path'] and not any(x.startswith('-O') for x in preprocess)
 function,flow,addresses=_check_getter_ir(d['llvm_module'])
 assert (function,flow,addresses)==(d['llvm_function'],d['ssa_flow'],d['mmio_addresses']),'frozen LLVM flow/address metadata differs'
 return {'source_sha256':d['source_sha256'],'preprocessed_source_sha256':d['preprocessed_source_sha256'],'llvm_module_sha256':d['llvm_module_sha256'],'compiler_input_count':len(inputs),'boot_entry':d['entry'],'projection':d['projection'],'bindings':{'caller':CALLER_BINDING,'getter':GETTER_BINDING},'independently_replayed_frozen_llvm':True,'independently_replayed_original_ast':False,'ast_boundary':'Producer AST object was not retained. Exact pinned producer AST checker bytes and returned binding metadata are checked; no independent discarded-AST replay is claimed.'}

def check_wp_input(text,expected):
 clean=lambda value:re.sub(r'/\*.*?\*/|//[^\n]*|\s+','',value,flags=re.S)
 contracts=re.findall(r'/\*@(?P<contract>.*?)\*/',text,re.S)
 assert len(contracts)==2 and [re.sub(r'\s+','',c) for c in contracts]==[re.sub(r'\s+','',CONTRACT),r'assigns__swdb_dx_size_bytes[0..63];ensures\result=='+str(expected)+';'],'original helper/unit contract or private frame differs'
 wanted=('#include <stdbool.h>\n#include <stddef.h>\n#include <stdint.h>\n'+STATE+
  PROTOTYPE+';\n'+PROTOTYPE+';\nint trust_fixture(void);\nint trust_fixture(void) {\n'+
  '\n'.join(constructor_projection(BOOT_CERTIFICATE)['entry_assignments'])+'\nint observed = (int)(get_tile_size(0) + 0);\nreturn observed;\n}\n')
 assert clean(text)==clean(wanted),'WP input has extra premises, writes, effects, or changed source/call/initialization'
 return {'ordinary_private_initialization_assignments':64,'helper_requires':'0 <= SPD_id < 32','unit_requires':[],'original_unit_assigns':r'\nothing','formal_private_frame':'__swdb_dx_size_bytes[0 .. 63]','model_definition_injected':False,'hidden_frame_boundary':'Only private representation initialization is adapted; original public memory write allowance remains empty.'}

def audit(raw,checkout,full_sha,policy_path):
 raw=Path(raw).resolve();checkout=Path(checkout).resolve();project=checkout/'swdb-project';profile=raw/'size-profile';policy_path=Path(policy_path)
 assert sha(policy_path)==POLICY_SHA256 and re.fullmatch(r'[0-9a-f]{40}',full_sha),'unreviewed policy/commit'
 policy=json.loads(policy_path.read_text());physical={};checks=0
 def pin(path,digest_expected=None,size=None):
  nonlocal checks
  path=Path(path);h=sha(path);n=path.stat().st_size
  assert digest_expected is None or h==digest_expected,'changed physical bytes: '+str(path)
  assert size is None or n==size
  physical[str(path)]={'sha256':h,'bytes':n};checks+=1;return h
 for name,h in policy['production_files'].items():pin(project/name,h)
 producer=(project/'swdb/dx100_size_source.py').read_text();reader=Path(__file__).read_text();producer_tree=ast.parse(producer);reader_tree=ast.parse(reader)
 for name in ['Refused','constructor_projection','_function_ir','_check_getter_ir']:
  old=next(n for n in producer_tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==name);new=next(n for n in reader_tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==name)
  assert ast.get_source_segment(producer,old)==ast.get_source_segment(reader,new),'copied pure certificate checker bytes differ'
 for name in ['source-commit.txt','profile.txt','exit-code.txt','selected-tests.txt','junit.xml','source-manifest.json','runtime-provenance.json']:pin(profile/name)
 for name in ['size-project-runtime-provenance.json','selected-size-tool-metadata.json']:pin(raw/name)
 assert (profile/'source-commit.txt').read_text().strip()==full_sha and (profile/'profile.txt').read_text().strip()=='pair'
 assert (profile/'exit-code.txt').read_text().strip()=='0','not a successful actual workflow; no proof acceptance'
 selected=(profile/'selected-tests.txt').read_text().splitlines();base='tests/test_dx100_size_actual.py::test_actual_wp_source_size_first_gate'
 assert selected==[base+'[correct-size]',base+'[wrong-size]']
 suites=ET.parse(profile/'junit.xml').getroot().findall('testsuite');assert suites
 counts={k:sum(int(s.attrib[k]) for s in suites) for k in ['tests','failures','errors','skipped']};assert counts=={'tests':len(selected),'failures':0,'errors':0,'skipped':0}
 testcases=[t for s in suites for t in s.findall('testcase')];assert {t.attrib['name'] for t in testcases}=={x.split('::')[-1] for x in selected}
 manifest=json.loads((profile/'source-manifest.json').read_text());assert len({p['path'] for p in manifest})==len(manifest)
 for row in manifest:assert not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts;pin(project/row['path'],row['sha256'],row.get('bytes'))
 manifest_names={p['path'] for p in manifest};actual_swdb={str(p.relative_to(project)) for p in (project/'swdb').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 assert {p for p in manifest_names if p.startswith('swdb/')}==actual_swdb,'source manifest omits runtime module membership'
 runtime=json.loads((profile/'runtime-provenance.json').read_text());project_runtime=json.loads((raw/'size-project-runtime-provenance.json').read_text());selected_tools=json.loads((raw/'selected-size-tool-metadata.json').read_text())
 admission=policy['selected_admission']
 assert full_sha==admission['source_commit'] and selected_tools['actual_size_lineup']==runtime['actual_size_lineup']==LINEUP and selected_tools['source_commit']==full_sha
 assert set(selected_tools['tools'])==set(admission['tools']) and all(got['sha256']==admission['tools'][name]['sha256'] and Path(got['path']).resolve()==Path(admission['tools'][name]['path']).resolve() for name,got in selected_tools['tools'].items())
 assert selected_tools['config']['sha256']==admission['config']['sha256'] and Path(selected_tools['config']['path']).resolve()==Path(admission['config']['path']).resolve() and selected_tools['source_files']==admission['source_files']
 assert {str(Path(r['path']).resolve()):r['sha256'] for r in selected_tools['wp_artifacts']}=={str(Path(p).resolve()):h for p,h in admission['wp_artifacts'].items()}
 assert selected_tools['stdlib']=={'path':admission['why3_stdlib'],'count':admission['stdlib_count'],'sha256':admission['stdlib_sha256']}
 stdroot=Path(selected_tools['stdlib']['path']);assert stdroot.is_dir() and not stdroot.is_symlink(),'stdlib root is not a real directory'
 stdrows=[]
 for path in sorted(stdroot.rglob('*')):
  mode=path.lstat().st_mode
  assert not stat.S_ISLNK(mode) and (stat.S_ISDIR(mode) or stat.S_ISREG(mode)),'stdlib symlink or special member'
  if stat.S_ISREG(mode):
   assert path.suffix=='.mlw','unexpected non-MLW stdlib file'
   stdrows.append({'path':str(path.relative_to(stdroot)),'sha256':pin(path)})
 assert len(stdrows)==selected_tools['stdlib']['count'] and digest(stdrows)==selected_tools['stdlib']['sha256']
 assert project_runtime['cwd']==str(project) and runtime['lowering']==project_runtime['lowering_identity'] and runtime['compiler']==project_runtime['runtime'],'project/bootstrap runtime mismatch'
 compiler=project_runtime['runtime'];assert compiler.get('driver') and compiler.get('command_executable') and 'unavailable' not in compiler
 for row in [compiler['driver'],compiler['command_executable']]:pin(row['path'],row['sha256'])
 assert compiler['check']=={'id':'swdb-stdlib-provenance-1','sha256':sha(project/'swdb/stdlib_provenance.py')}
 for row in selected_tools['tools'].values():pin(row['path'],row['sha256'])
 for row in selected_tools['wp_artifacts']:pin(row['path'],row['sha256'])
 pin(selected_tools['config']['path'],selected_tools['config']['sha256'])
 for name,h in selected_tools['source_files'].items():pin(project/name,h)
 frontend=compiler['frontend'];resource=Path(frontend[frontend.index('-resource-dir')+1]);llvmroot=resource.parents[2];libraries=[p.resolve() for p in [llvmroot/'lib/libclang.dylib',llvmroot/'lib/libclang.so'] if p.is_file()]
 assert len(libraries)==1 and pin(libraries[0])==compiler['parser']['sha256']
 header_digest=hashlib.sha256();header_count=0
 for label,folder in [('libc++',llvmroot/'include/c++/v1'),('clang-resource',resource/'include')]:
  assert folder.is_dir()
  for path in sorted(folder.rglob('*')):
   if path.is_file():header_digest.update(label.encode()+b'\0'+str(path.relative_to(folder)).encode()+b'\0');header_digest.update(bytes.fromhex(pin(path)));header_count+=1
 assert compiler['headers']=={'id':'llvm-standard-resource-headers','sha256':header_digest.hexdigest(),'files':header_count}
 setup_tree=ast.parse((project/'swdb/proof_setup.py').read_text());sources=[]
 for node in setup_tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHECK_SOURCES' for t in node.targets):sources=list(ast.literal_eval(node.value))
  elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='CHECK_SOURCES':sources+=list(ast.literal_eval(node.value))
 checker_inputs=[{'path':'swdb/'+name,'sha256':pin(project/'swdb'/name)} for name in sources]+[{'path':'vocab/proof_failure_classes.yaml','sha256':pin(project/'vocab/proof_failure_classes.yaml')}]
 checkid={'version':'1','sha256':digest(checker_inputs)};assert runtime['checks']=={'proof_setup_check':checkid,'verdict_reading':checkid}
 schema=json.loads((project/'schemas/proof.schema.json').read_text());validator=Draft202012Validator(schema)
 interface=json.loads((project/'tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json').read_text());records=[];expected_contract_values=[]
 for path in sorted((profile/'pytest').rglob('records/proofs/*.yaml')):
  record=yaml.safe_load(path.read_text());validator.validate(record);assert record['id']==path.stem and str(path)==policy['record_pins'][record['id']]['path'] and sha(path)==policy['record_pins'][record['id']]['sha256'];case=path.parents[2];library=case/'library';assert not (case/'must-not-launch-solver').exists()
  assert record['kind']=='proof' and record['subject']=={'kind':'library_summary','id':'contract.dx100_trust_fixture'}
  assert record['evidence_kind']=='contract_fixture' and record['job']['adapter']=='wp'
  methodpath=next(p for p in (library/'methods').glob('*.yaml') if yaml.safe_load(p.read_text()).get('id')==record['pins']['method_version']['id']);method=yaml.safe_load(methodpath.read_text());pin(methodpath,record['pins']['method_version']['sha256']);check_lineup(method,runtime['actual_size_lineup'])
  assert method['id']=='method.dx100-size-fixture-0-2' and method['evidence_kind']==record['evidence_kind']
  assert project_runtime['lowering_identity']['c_lowering'] in method['c_lowering']['translators'] and record['pins']['naming_rules']==project_runtime['lowering_identity']['naming_rules']
  check_method_checks(method,runtime['checks'])
  contract=yaml.safe_load((library/'rewrite_contracts/trust.yaml').read_text());assert record['pins']['code']==record['pins']['contract']=={'id':contract['id'],'sha256':digest(contract)}
  acsl=re.sub(r'\s+','',contract['clauses'][0]['acsl']['text']);match=re.fullmatch(r'assigns\\nothing;ensures\\result==([01]);',acsl);assert match
  expected=int(match.group(1));expected_contract_values.append(expected);assert record['verdict']==('proven' if expected==0 else 'not_proven')
  assert not contract['concurrency_frame'] and contract['proof_unit']['function']=='trust_fixture' and not contract['proof_unit'].get('array_domains')
  semantic_path=library/'proof_semantics/dx100_trust_fixture.yaml';data=yaml.safe_load(semantic_path.read_text());sem_pin={'id':data['id'],'sha256':pin(semantic_path,record['pins']['proof_semantics']['sha256'])};assert record['pins']['proof_semantics']==sem_pin
  assert data['rules']==policy['semantic_rules'],'TRUST/boot/source rules differ from captured exact policy'
  assert {r['id']:r['statement'] for r in data['rules'] if r.get('record_assumption') is True}==dict(policy['trust_metadata'],fresh_spd_epoch=BOOT_STATEMENT)
  assert (library/data['model']['c']['path']).read_text()==MODEL
  assert data['id']=='semantics.dx100_size_fixture_0_2' and data['model']['layout']==LAYOUT
  assert data['declaration_inventory']=={k:interface[k] for k in ('sources','declarations')}
  names={d['name'] for d in interface['declarations']};calls=unique(data['calls'],'call');assert set(calls)==names and [n for n,r in calls.items() if r.get('supported') is not False]==['get_tile_size']
  assert not data['constants'] and not data['queries'] and not data['wp']
  for name,row in calls.items():
   if name!='get_tile_size':assert row['supported'] is False and re.sub(r'\s+','',row['contract'])==r'requires\false;assigns\nothing;'
  active=calls['get_tile_size'];assert active['prototype']==PROTOTYPE and re.sub(r'\s+','',active['contract'])==re.sub(r'\s+','',CONTRACT) and active['rules']==['fresh_spd_epoch','size_response']
  assert active['definition']['kind']==KIND and active['definition']['entry']==BOOT_CERTIFICATE
  assert {Path(p['path']).name:p['sha256'] for p in active['definition']['sources']}==SOURCE_PINS
  epoch=next(r for r in data['rules'] if r['id']=='fresh_spd_epoch');assert epoch['assumed']=={'owner':OWNER}
  for item in walk(data):
   if isinstance(item.get('path'),str) and isinstance(item.get('sha256'),str):
    target=Path(item['path']) if Path(item['path']).is_absolute() else {'library':library,'project':project}[item.get('root','library')]/item['path'];pin(target,item['sha256'])
  for section,key in [('ghost','acsl'),('model','logic')]:
   text=(library/data[section][key]['path']).read_text();assert not re.sub(r'/\*.*?\*/|//[^\n]*|\s+','',text,flags=re.S)
  assert (library/data['model']['state']['path']).read_text()==STATE
  pin(library/'proof_semantics/dx100_bfs_0_1.yaml',sha(project/'library/proof_semantics/dx100_bfs_0_1.yaml'))
  settings=record['settings'];flags_ok(settings['flags']);assert settings['session']=='fresh' and settings['verifier_launched'] is True and settings['rss_cap_bytes']==8589934592
  assert settings['compiler_runtime']==compiler and settings['proof_semantics']['unit_requires']==settings['proof_semantics']['unit_ensures']==[]
  assert settings['proof_semantics']['calls']==['get_tile_size'] and settings['proof_semantics']['probes']==[]
  semsettings=settings['proof_semantics'];assert semsettings['id']==data['id']
  assert semsettings['entry_projection']=={'kind':CERTIFICATE_KIND,'bytes':64,'owner':OWNER,'statement':BOOT_STATEMENT}
  definitions=semsettings['source_definitions'];assert len(definitions)==1
  definition=definitions[0];certificate=check_definition(definition,compiler,project,pin)
  setup=record['proof_setup_check'];assert setup['verdict']=='passed' and setup['check']==checkid and setup['method_version']==record['pins']['method_version']
  assert record['verdict_reading']=={'check':checkid,'verdict':record['verdict']}
  witness=[{key:definition[key] for key in ('kind','entry','projection','source_sha256','preprocessed_source_sha256','llvm_module_sha256','sources','compiler_inputs')}]
  assert setup['hashes']['dx100_source_selector']==digest([]) and setup['hashes']['dx100_size_source']==digest(witness) and setup['hashes']['compiler_runtime']==digest(compiler)
  assert setup['runs'] and all(r['verdict']=='passed' and r['tool']=='wp' and r['hashes']['dx100_source_selector']==digest([]) and r['hashes']['dx100_size_source']==digest(witness) and r['hashes']['compiler_runtime']==digest(compiler) for r in setup['runs'])
  reports=unique(record['evidence']['reports'],'name');required={'c_lowering','anchors','wp_input','wp_log','wp_goals','wp_properties','wp_inventory','wp_normalized'};assert required<=set(reports)
  pin(record['evidence']['adapter_log']['path'],record['evidence']['adapter_log']['sha256'])
  for row in reports.values():pin(row['path'],row['sha256'])
  for item in walk(record):
   if isinstance(item.get('path'),str) and Path(item['path']).is_absolute() and re.fullmatch(r'[0-9a-f]{64}',str(item.get('sha256',''))):pin(item['path'],item['sha256'],item.get('bytes'))
  assert record['pins']['c_lowering']=={'id':'trust_fixture.c','sha256':reports['c_lowering']['sha256']} and setup['hashes']['lowering']==reports['c_lowering']['sha256'] and setup['hashes']['wp_input.c']==reports['wp_input']['sha256']
  anchors=json.loads(Path(reports['anchors']['path']).read_text());assert anchors['c_lowering_sha256']==reports['c_lowering']['sha256'] and anchors['function']=='trust_fixture'
  anchored=[row['semantic_source'] for row in anchors.get('summaries',[]) if row.get('semantic_source')];assert anchored==[definition]
  wp_input=Path(reports['wp_input']['path']).read_text();formal_input=check_wp_input(wp_input,expected)
  for key in ['wp_input','wp_normalized']:
   assert not re.search(r'dx_state_initialized|dx_memory_clear_after_stall|\bdx_tile|\bDX_NT\b|as if it finished at issue',Path(reports[key]['path']).read_text())
  expected_trust=[{'kind':'proof_semantics','reference':{'id':data['id']+'#'+r['id'],'sha256':sem_pin['sha256']},'sentence':r['statement']} for r in data['rules'] if r.get('record_assumption') is True]+[{'kind':'proof_semantics','reference':sem_pin,'sentence':PURE}]
  assert Counter(json.dumps(a,sort_keys=True) for a in record['assumptions'] if a['kind']=='proof_semantics')==Counter(json.dumps(a,sort_keys=True) for a in expected_trust)
  assert all(a['kind'] in {'trusted_tool','proof_semantics','assumed_clause'} for a in record['assumptions']) and not any('as if it finished at issue' in a['sentence'] or 'WP model-domain preconditions' in a['sentence'] for a in record['assumptions'])
  expected_tools=[project_runtime['lowering_identity']['c_lowering'],project_runtime['lowering_identity']['clang']]+[{'id':tool+'-'+version,'sha256':selected_tools['tools']['frama-c' if tool=='frama-c-wp' else tool]['sha256']} for tool,version in LINEUP.items()]
  assert Counter(json.dumps(a['reference'],sort_keys=True) for a in record['assumptions'] if a['kind']=='trusted_tool')==Counter(json.dumps(a,sort_keys=True) for a in expected_tools)
  census=check_goals(record,json.loads(Path(reports['wp_inventory']['path']).read_text()),json.loads(Path(reports['wp_goals']['path']).read_text()),csv_properties(Path(reports['wp_properties']['path']).read_text()),sem_pin,diagnose_solver_error=(expected==1 and record.get('failure_class')=='solver_error'))
  records.append({'record':str(path),'id':record['id'],'verdict':record['verdict'],'failure_class':record.get('failure_class'),'contract_result':expected,'certificate':certificate,'formal_input':formal_input,'census':census,'trust_metadata_fragments':[a['reference']['id'] for a in expected_trust if '#' in a['reference']['id']]});pin(path)
 assert {r['id'] for r in records}==set(policy['record_pins']),'actual record identity census differs'
 assert len(records)==len(selected) and sorted(expected_contract_values)==[0,1] and len({r['certificate']['source_sha256'] for r in records})==1,'missing/duplicate/changed-source pair records'
 for path,row in physical.items():assert sha(path)==row['sha256'],'physical reference changed during cold audit'
 positive=[r for r in records if r['contract_result']==0];negative=[r for r in records if r['contract_result']==1]
 assert len(positive)==len(negative)==1
 positive_acceptance=positive[0]['verdict']=='proven' and positive[0]['census']['clean_acceptance'];negative_acceptance=negative[0]['census']['clean_acceptance']
 return {'classification_audit':'PASS','positive_scoped_acceptance':positive_acceptance,'negative_clean_acceptance':negative_acceptance,'pair_acceptance':positive_acceptance and negative_acceptance,'negative_refuted':False,'actual_pytest_status':'Original producer pytest2pass/exit0 preserved; clean negative acceptance separately refused if solver_error','scope':'Passive supplemental actual size record/property/smoke/certificate/runtime audit only; coordinator separately owns admission/resources/leases/whole-raw membership','source_commit':full_sha,'source_policy':{'path':str(policy_path),'sha256':sha(policy_path)},'reader_sha256':sha(__file__),'profile':'pair','counts':counts,'records':records,'physical_pin_checks':checks,'physical_files':len(physical),'physical_references':physical,'integrity_errors':[],'legacy_boundary':'Explicit pinned TRUST metadata remains reported; no legacy device premises/reduction is admitted. Only exact source-certified helper Extern assumed_clause is allowed.','actual_tool_probe_invocations':0,'full_device_or_ticket_acceptance':False}

if __name__=='__main__':
 if not __debug__:raise SystemExit('Optimized Python refused')
 try:
  result=audit(*sys.argv[1:]);print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(0 if result['pair_acceptance'] else 2)
 except Exception as error:
  print(json.dumps({'integrity_errors':[failure_location(error)],'scope':'Supplemental audit refused; no acceptance or mutation','reader_sha256':sha(__file__)},indent=2));raise SystemExit(1)
