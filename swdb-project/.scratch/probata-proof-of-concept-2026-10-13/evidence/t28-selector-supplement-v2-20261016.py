"""Inert standalone passive selector audit. Root alone executes on SETTLED raw.
Usage: python FILE RAW_ROOT FROZEN_CHECKOUT FULL_SHA POLICY_JSON
No subprocess, tool probe, production import or mutation of existing artifacts.
"""
from pathlib import Path
from collections import Counter
import ast,csv,hashlib,io,json,math,re,sys,xml.etree.ElementTree as ET
import yaml
from jsonschema import Draft202012Validator

POLICY_SHA256='b0bb71936a841b48c786f54f5efa9a13a9b2b381af748ab174f69aac7db91c37'
LINEUP={'frama-c-wp':'33.0','z3':'5.1.0','cvc5':'1.2.1','alt-ergo':'2.6.4'}
HELPER='get_data_type_unsigned_int'
PURE='Only the source-certified get_data_type<unsigned int>() helper is admitted; all other interface calls are explicitly refused. No device commands or timing reduction are used.'
HEADERS={'MAA.hpp':'4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd','MAA_gem5.hpp':'5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174'}

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
 return bool(n is not None and name=='typed_real_get_data_type_unsigned_int_wp_smoke_dead_call_s1'
  and g['property']==r['property']==n['property']=='get_data_type_unsigned_int_wp_smoke_dead_call_s1'
  and g['function']==p['function']==HELPER and r['function']==n['function']=='trust_fixture'
  and g['smoke'] is True and r['smoke'] is True and n['smoke'] is True
  and g['passed'] is True and n['passed'] is True and r['status']=='valid'
  and type(g['line']) is int and g['line']>0 and g['line']==n['line']==p['line']
  and g['targets']==[] and p['dependencies']==[] and p.get('origin') is None
  and p['kind']=='other' and p['extern'] is False and p['generated_smoke_failure'] is False
  and g['results'] and set(g['results'])<={'valid','timeout','unknown','stepout','untried'})

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

def check_goals(record,inventory,native,properties,semantics_pin):
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
 failed=[];smokes=[];owner_context=[]
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
   smokes.append(name)
  elif g['passed']:
   assert 'valid' in g['results'] and r['status']=='valid','ordinary pass without direct Valid inventory result'
  else:
   assert set(g['results'] or ['unknown'])<= {'unknown','timeout','stepout','untried'},'tool/resource failure in ordinary negative'
   assert 'ensures' in name and r['status']!='valid','non-ensures ordinary failure'
   failed.append(name)
 assert smokes and any(not g['smoke'] for g in generated.values()),'missing ordinary/smoke coverage'
 for row in properties:
  candidates=[p for p in props.values() if (p.get('function') or '')==row['function'] and str(p['line'])==str(row['line'])]
  assert candidates,'CSV property escapes complete inventory'
  if row['status']=='Considered valid':assert row['function']==HELPER and any(p['extern'] for p in candidates),'untrusted considered-valid property'
  elif row['status']!='Valid':
   assert failed and row['function']=='trust_fixture' and 'ensures' in row['property'],'unclassified non-Valid CSV property'
   assert any(generated[name]['property'] in {p['property'] for p in candidates} or str(generated[name]['line'])==str(row['line']) for name in failed),'unattributed failing property'
 if record['verdict']=='proven':assert not failed and not record.get('unproven_properties')
 else:
  assert record['verdict']=='not_proven' and failed and record['failure_class'] in {'unknown','timeout'}
  unproven=record['unproven_properties'];assert unproven and set(failed)<={p.get('goal') for p in unproven}
  assert all(p['failure_class'] in {'unknown','timeout'} and (not p.get('goal') or p['goal'] in failed) for p in unproven),'unexplained unproven record property'
 return {'owner_context_distinctions':owner_context,'goals':len(generated),'ordinary':len(generated)-len(smokes),'smokes':len(smokes),'properties':len(props),'extern_properties':[p['property'] for p in extern],'failed_ordinary':failed,'dependency_edges':sum(len(p['dependencies'])+bool(p.get('origin')) for p in props.values()),'initialized_property_descriptions':sum('initializ' in p['description'].lower() for p in props.values())}
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
 assert d['kind']=='dx100-get-data-type-u32-v1' and d['arguments']==['unsigned int'] and type(d['value']) is int and d['value']==0
 assert d['runtime_identity']==runtime,'certificate uses a different actual compiler runtime'
 assert d['source_mangled'] in {'_Z13get_data_typeIjE8DataTypev','__Z13get_data_typeIjE8DataTypev'}
 expected_source='#include '+json.dumps(str(project/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\nint trust_fixture() { int observed=(int)get_data_type<uint32_t>(); return observed; }\n'
 assert Path(d['source_path']).read_text()==expected_source and sha(d['source_path'])==d['source_sha256'],'main source drift'
 assert {Path(p['path']).name:p['sha256'] for p in d['headers']}==HEADERS
 for item in d['headers']+d['compiler_inputs']:pin(item['path'],item['sha256'],item.get('bytes'))
 assert d['compiler_inputs'] and len({p['path'] for p in d['compiler_inputs']})==len(d['compiler_inputs'])
 inputs={str(Path(p['path']).resolve()) for p in d['compiler_inputs']};assert str(Path(d['source_path']).resolve()) in inputs and all(str(Path(h['path']).resolve()) in inputs for h in d['headers'])
 markers={str(Path(json.loads(m)).resolve()) for m in re.findall(r'^#\s+\d+\s+("[^"\n]+")',d['preprocessed_source'],re.M) if not json.loads(m).startswith('<')}
 assert markers<=inputs,'preprocessed physical header omitted from certificate inputs'
 for text in ('preprocessed_source','probe_source','llvm_module'):assert hashlib.sha256(d[text].encode()).hexdigest()==d[text+'_sha256']
 assert d['preprocessed_bytes']==len(d['preprocessed_source'].encode())
 expected_probe='\nextern "C" unsigned int __swdb_dx100_u32_type_certificate() { return (unsigned int)::get_data_type<unsigned int>(); }\n'
 assert d['probe_source']==expected_probe
 command=d['compiler_command'];assert command[:len(runtime['command'])]==runtime['command']
 assert command[len(runtime['command']):-1]==['-x','c++-cpp-output','-std=c++17','-fopenmp','-O2','-S','-emit-llvm','-o','-']
 preprocess=d['preprocess_command'];assert preprocess[:len(runtime['command'])+4]==runtime['command']+['-x','c++','-std=c++17','-fopenmp'] and '-E' in preprocess and '-MD' in preprocess and preprocess[-1]==d['source_path'] and not any(x.startswith('-O') for x in preprocess)
 matches=list(re.finditer(r'^define\b[^\n{]*@__swdb_dx100_u32_type_certificate\([^)]*\)[^\n{]*\{(?P<body>.*?)^}',d['llvm_module'],re.M|re.S));assert len(matches)==1 and matches[0].group()==d['llvm_function']
 body=re.sub(r';[^\n]*','',matches[0]['body']);body=re.sub(r'^\s*[A-Za-z_][\w.]*:\s*','',body,flags=re.M).strip();assert body=='ret i32 0','certificate does not have unique constant return body'
 return {'source_sha256':d['source_sha256'],'preprocessed_source_sha256':d['preprocessed_source_sha256'],'llvm_module_sha256':d['llvm_module_sha256'],'compiler_input_count':len(inputs)}

def audit(raw,checkout,full_sha,policy_path):
 raw=Path(raw).resolve();checkout=Path(checkout).resolve();project=checkout/'swdb-project';profile=raw/'selector-profile';policy_path=Path(policy_path)
 assert sha(policy_path)==POLICY_SHA256 and re.fullmatch(r'[0-9a-f]{40}',full_sha),'unreviewed policy/commit'
 policy=json.loads(policy_path.read_text());physical={};checks=0
 def pin(path,digest_expected=None,size=None):
  nonlocal checks
  path=Path(path);h=sha(path);n=path.stat().st_size
  assert digest_expected is None or h==digest_expected,'changed physical bytes: '+str(path)
  assert size is None or n==size
  physical[str(path)]={'sha256':h,'bytes':n};checks+=1;return h
 for name,h in policy['production_files'].items():pin(project/name,h)
 for name in ['source-commit.txt','profile.txt','exit-code.txt','selected-tests.txt','junit.xml','source-manifest.json','runtime-provenance.json']:pin(profile/name)
 for name in ['selector-project-runtime-provenance.json','selected-selector-tool-metadata.json']:pin(raw/name)
 assert (profile/'source-commit.txt').read_text().strip()==full_sha and (profile/'profile.txt').read_text().strip()=='pair'
 assert (profile/'exit-code.txt').read_text().strip()=='0','not a successful actual workflow; no proof acceptance'
 selected=(profile/'selected-tests.txt').read_text().splitlines();base='tests/test_dx100_selector_actual.py::test_actual_wp_source_selector_first_gate'
 assert selected==[base+'[positive]',base+'[wrong-enum]']
 suites=ET.parse(profile/'junit.xml').getroot().findall('testsuite');assert suites
 counts={k:sum(int(s.attrib[k]) for s in suites) for k in ['tests','failures','errors','skipped']};assert counts=={'tests':len(selected),'failures':0,'errors':0,'skipped':0}
 testcases=[t for s in suites for t in s.findall('testcase')];assert {t.attrib['name'] for t in testcases}=={x.split('::')[-1] for x in selected}
 manifest=json.loads((profile/'source-manifest.json').read_text());assert len({p['path'] for p in manifest})==len(manifest)
 for row in manifest:assert not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts;pin(project/row['path'],row['sha256'],row.get('bytes'))
 manifest_names={p['path'] for p in manifest};actual_swdb={str(p.relative_to(project)) for p in (project/'swdb').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 assert {p for p in manifest_names if p.startswith('swdb/')}==actual_swdb,'source manifest omits runtime module membership'
 runtime=json.loads((profile/'runtime-provenance.json').read_text());project_runtime=json.loads((raw/'selector-project-runtime-provenance.json').read_text());selected_tools=json.loads((raw/'selected-selector-tool-metadata.json').read_text())
 admission=policy['selected_admission']
 assert full_sha==admission['source_commit'] and selected_tools['actual_selector_lineup']==runtime['actual_selector_lineup']==LINEUP and selected_tools['source_commit']==full_sha
 assert set(selected_tools['tools'])==set(admission['tools']) and all(got['sha256']==admission['tools'][name]['sha256'] and Path(got['path']).resolve()==Path(admission['tools'][name]['path']).resolve() for name,got in selected_tools['tools'].items())
 assert selected_tools['config']['sha256']==admission['config']['sha256'] and Path(selected_tools['config']['path']).resolve()==Path(admission['config']['path']).resolve() and selected_tools['source_files']==admission['source_files']
 assert {str(Path(r['path']).resolve()):r['sha256'] for r in selected_tools['wp_artifacts']}=={str(Path(p).resolve()):h for p,h in admission['wp_artifacts'].items()}
 assert selected_tools['stdlib']=={'path':admission['why3_stdlib'],'count':admission['stdlib_count'],'sha256':admission['stdlib_sha256']}
 stdroot=Path(selected_tools['stdlib']['path']);stdrows=[{'path':str(p.relative_to(stdroot)),'sha256':pin(p)} for p in sorted(stdroot.rglob('*.mlw'))]
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
  record=yaml.safe_load(path.read_text());validator.validate(record);case=path.parents[2];library=case/'library';assert not (case/'must-not-launch-solver').exists()
  assert record['kind']=='proof' and record['subject']=={'kind':'library_summary','id':'contract.dx100_trust_fixture'}
  assert record['evidence_kind']=='contract_fixture' and record['job']['adapter']=='wp'
  methodpath=next(p for p in (library/'methods').glob('*.yaml') if yaml.safe_load(p.read_text()).get('id')==record['pins']['method_version']['id']);method=yaml.safe_load(methodpath.read_text());pin(methodpath,record['pins']['method_version']['sha256']);check_lineup(method,runtime['actual_selector_lineup'])
  assert method['id']=='method.dx100-selector-fixture-0-2' and method['evidence_kind']==record['evidence_kind']
  assert project_runtime['lowering_identity']['c_lowering'] in method['c_lowering']['translators'] and record['pins']['naming_rules']==project_runtime['lowering_identity']['naming_rules']
  check_method_checks(method,runtime['checks'])
  contract=yaml.safe_load((library/'rewrite_contracts/trust.yaml').read_text());assert record['pins']['code']==record['pins']['contract']=={'id':contract['id'],'sha256':digest(contract)}
  acsl=re.sub(r'\s+','',contract['clauses'][0]['acsl']['text']);match=re.fullmatch(r'assigns\\nothing;ensures\\result==([01]);',acsl);assert match
  expected=int(match.group(1));expected_contract_values.append(expected);assert record['verdict']==('proven' if expected==0 else 'not_proven')
  assert not contract['concurrency_frame'] and contract['proof_unit']['function']=='trust_fixture' and not contract['proof_unit'].get('array_domains')
  semantic_path=library/'proof_semantics/dx100_trust_fixture.yaml';data=yaml.safe_load(semantic_path.read_text());sem_pin={'id':data['id'],'sha256':pin(semantic_path,record['pins']['proof_semantics']['sha256'])};assert record['pins']['proof_semantics']==sem_pin
  assert {r['id']:r['statement'] for r in data['rules'] if r.get('record_assumption') is True}==policy['trust_metadata']
  assert (library/data['model']['c']['path']).read_text()=='unsigned char get_data_type_unsigned_int(void) { return 0; }\n'
  assert data['id']=='semantics.dx100_selector_fixture_0_2' and data['model']['layout']=='dx100-pure-selector-u32-v1'
  assert data['declaration_inventory']=={k:interface[k] for k in ('sources','declarations')}
  names={d['name'] for d in interface['declarations']};calls=unique(data['calls'],'call');assert set(calls)==names and [n for n,r in calls.items() if r.get('supported') is not False]==['get_data_type']
  assert not data['constants'] and not data['queries'] and not data['wp']
  for name,row in calls.items():
   if name!='get_data_type':assert row['supported'] is False and re.sub(r'\s+','',row['contract'])==r'requires\false;assigns\nothing;'
  active=calls['get_data_type']['instances'];assert len(active)==1 and active[0]['arguments']==['unsigned int'] and active[0]['arity']==0
  assert re.sub(r'\s+','',active[0]['contract'])==r'assigns\nothing;ensures\result==0;'
  for item in walk(data):
   if isinstance(item.get('path'),str) and isinstance(item.get('sha256'),str):
    target=Path(item['path']) if Path(item['path']).is_absolute() else {'library':library,'project':project}[item.get('root','library')]/item['path'];pin(target,item['sha256'])
  for section,key in [('ghost','acsl'),('model','state'),('model','logic')]:
   text=(library/data[section][key]['path']).read_text();assert not re.sub(r'/\*.*?\*/|//[^\n]*|\s+','',text,flags=re.S)
  pin(library/'proof_semantics/dx100_bfs_0_1.yaml',sha(project/'library/proof_semantics/dx100_bfs_0_1.yaml'))
  settings=record['settings'];flags_ok(settings['flags']);assert settings['session']=='fresh' and settings['verifier_launched'] is True and settings['rss_cap_bytes']==8589934592
  assert settings['compiler_runtime']==compiler and settings['proof_semantics']['unit_requires']==settings['proof_semantics']['unit_ensures']==[]
  assert settings['proof_semantics']['calls']==['get_data_type'] and settings['proof_semantics']['probes']==[]
  bindings=settings['proof_semantics']['instances'];assert len(bindings)==1 and bindings[0]['name']=='get_data_type' and bindings[0]['c_name']==HELPER
  definition=bindings[0]['definition'];certificate=check_definition(definition,compiler,project,pin)
  setup=record['proof_setup_check'];assert setup['verdict']=='passed' and setup['check']==checkid and setup['method_version']==record['pins']['method_version']
  assert record['verdict_reading']=={'check':checkid,'verdict':record['verdict']}
  witness=[{key:definition[key] for key in ('kind','source_sha256','preprocessed_source_sha256','llvm_module_sha256','compiler_inputs')}]
  assert setup['hashes']['dx100_source_selector']==digest(witness) and setup['hashes']['compiler_runtime']==digest(compiler)
  assert setup['runs'] and all(r['verdict']=='passed' and r['tool']=='wp' and r['hashes']['dx100_source_selector']==digest(witness) and r['hashes']['compiler_runtime']==digest(compiler) for r in setup['runs'])
  reports=unique(record['evidence']['reports'],'name');required={'c_lowering','anchors','wp_input','wp_log','wp_goals','wp_properties','wp_inventory','wp_normalized'};assert required<=set(reports)
  pin(record['evidence']['adapter_log']['path'],record['evidence']['adapter_log']['sha256'])
  for row in reports.values():pin(row['path'],row['sha256'])
  for item in walk(record):
   if isinstance(item.get('path'),str) and Path(item['path']).is_absolute() and re.fullmatch(r'[0-9a-f]{64}',str(item.get('sha256',''))):pin(item['path'],item['sha256'],item.get('bytes'))
  assert record['pins']['c_lowering']=={'id':'trust_fixture.c','sha256':reports['c_lowering']['sha256']} and setup['hashes']['lowering']==reports['c_lowering']['sha256'] and setup['hashes']['wp_input.c']==reports['wp_input']['sha256']
  anchors=json.loads(Path(reports['anchors']['path']).read_text());assert anchors['c_lowering_sha256']==reports['c_lowering']['sha256'] and anchors['function']=='trust_fixture'
  anchored=[s['semantic_instance']['definition'] for s in anchors.get('summaries',[]) if s.get('semantic_instance',{}).get('definition')];assert anchored==[definition]
  wp_input=Path(reports['wp_input']['path']).read_text();assert not re.search(r'\brequires\b|\baxiom\b|dx_state_initialized|dx_memory_clear_after_stall|\bdx_tile|\bDX_NT\b|__VERIFIER_assume|__CPROVER_assume',wp_input)
  assert 'get_data_type_unsigned_int' in wp_input
  for key in ['wp_input','wp_normalized']:
   assert not re.search(r'dx_state_initialized|dx_memory_clear_after_stall|\bdx_tile|\bDX_NT\b|as if it finished at issue',Path(reports[key]['path']).read_text())
  expected_trust=[{'kind':'proof_semantics','reference':{'id':data['id']+'#'+r['id'],'sha256':sem_pin['sha256']},'sentence':r['statement']} for r in data['rules'] if r.get('record_assumption') is True]+[{'kind':'proof_semantics','reference':sem_pin,'sentence':PURE}]
  assert Counter(json.dumps(a,sort_keys=True) for a in record['assumptions'] if a['kind']=='proof_semantics')==Counter(json.dumps(a,sort_keys=True) for a in expected_trust)
  assert all(a['kind'] in {'trusted_tool','proof_semantics','assumed_clause'} for a in record['assumptions']) and not any('as if it finished at issue' in a['sentence'] or 'WP model-domain preconditions' in a['sentence'] for a in record['assumptions'])
  expected_tools=[project_runtime['lowering_identity']['c_lowering'],project_runtime['lowering_identity']['clang']]+[{'id':tool+'-'+version,'sha256':selected_tools['tools']['frama-c' if tool=='frama-c-wp' else tool]['sha256']} for tool,version in LINEUP.items()]
  assert Counter(json.dumps(a['reference'],sort_keys=True) for a in record['assumptions'] if a['kind']=='trusted_tool')==Counter(json.dumps(a,sort_keys=True) for a in expected_tools)
  census=check_goals(record,json.loads(Path(reports['wp_inventory']['path']).read_text()),json.loads(Path(reports['wp_goals']['path']).read_text()),csv_properties(Path(reports['wp_properties']['path']).read_text()),sem_pin)
  records.append({'record':str(path),'id':record['id'],'verdict':record['verdict'],'failure_class':record.get('failure_class'),'contract_result':expected,'certificate':certificate,'census':census,'trust_metadata_fragments':[a['reference']['id'] for a in expected_trust if '#' in a['reference']['id']]});pin(path)
 assert len(records)==len(selected) and sorted(expected_contract_values)==[0,1] and len({r['certificate']['source_sha256'] for r in records})==1,'missing/duplicate/changed-source pair records'
 for path,row in physical.items():assert sha(path)==row['sha256'],'physical reference changed during cold audit'
 return {'scope':'Passive supplemental actual selector record/property/smoke/certificate/runtime audit only; coordinator separately owns admission/resources/leases/whole-raw membership','source_commit':full_sha,'source_policy':{'path':str(policy_path),'sha256':sha(policy_path)},'reader_sha256':sha(__file__),'profile':'pair','counts':counts,'records':records,'physical_pin_checks':checks,'physical_files':len(physical),'physical_references':physical,'integrity_errors':[],'legacy_boundary':'Explicit pinned TRUST metadata remains reported; no legacy device premises/reduction is admitted. Only exact source-certified helper Extern assumed_clause is allowed.','actual_tool_probe_invocations':0,'full_device_or_ticket_acceptance':False}

if __name__=='__main__':
 if not __debug__:raise SystemExit('Optimized Python refused')
 try:print(json.dumps(audit(*sys.argv[1:]),indent=2,sort_keys=True))
 except Exception as error:
  print(json.dumps({'integrity_errors':[failure_location(error)],'scope':'Supplemental audit refused; no acceptance or mutation','reader_sha256':sha(__file__)},indent=2));raise SystemExit(1)
