"""INERT passive partial017 reader. No production imports, probes, tools, writes or dispatch."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sys,stat,ast,math
H=lambda b:hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def digest(v):return H(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
POLICY_SHA256='1fbde2d34e8929796811088799a2fa84ac8ba3eb5fd60ecaa11e266ca984c88b'
def lowerer_projection(project,compiler):
 # Pure byte expression from the exact pinned identity implementation; no locate/probe/import.
 folder=project/'swdb';read=lambda name:(folder/name).read_bytes()
 bounded=H(read('bounded_initialization.py')+read('proof_semantics.py')+read('bounded_std_initialization.py')).encode();pointer=sha(folder/'wp_pointer_bounds.py').encode()
 names=['array_domains.py','vector_ownership.py','vector_reallocation_model.py','vector_reallocation_calls.py','vector_reallocation_vcs.py','vector_reallocation_inventory.py','vector_reallocation_view.py','vector_reallocation_caller_vcs.py','heap_reallocation.mlw','vector_pipeline.py','model_domains.py','standard_model_view.py','helper_windows.py','nested_entry_reads.py','dx_array_domains.py','standard_range_calls.py','member_windows.py','stdlib_source_admission.py','dx100_source_selector.py']
 return H(read('c_lowering.py')+read('terminal_release.py')+read('cpu_effects.py')+read('cpu_memory_admission.py')+bounded+pointer+b''.join(read(n) for n in names)+json.dumps(compiler,sort_keys=True).encode())

def check_record(r,e):
 assert r['kind']=='proof' and r['evidence_kind']=='contract_fixture' and r['subject']=={'kind':'c_model','id':e['member']}
 assert r['verdict']=='not_proven' and r['failure_class']=='timeout' and r['status']=='draft' and r['bounds']=={'input_size':'unbounded','threads':1}
 assert len(r['goals'])==3 and [g['status'] for g in r['goals']]==['valid','valid','timeout'] and all(g['smoke'] is False and g['function'] is None and g['source']=='wp_json' for g in r['goals'])
 assert [g['solver'] for g in r['goals']]==['cvc5','cvc5',None]
 s=r['settings'];runs=s['heap_model_runs'];view=s['heap_model_view']
 assert len(runs)==3 and [v['id'] for v in runs]==e['target_ids'][:3] and len(e['target_ids'])==20
 assert [v['verdict'] for v in runs]==['proven','proven','not_proven'] and [v['failure_class'] for v in runs]==[None,None,'timeout']
 assert len(view['obligations'])==20 and [v['id'] for v in view['obligations']]==e['target_ids'] and all(v['status']=='pending' for v in view['obligations'])
 assert view['member']==e['member'] and view['model']==e['model'] and view['generic_caller_composition']=='unsupported' and view['qualification']['original_contract_proved'] is False
 assert s['verifier_launched'] is True and s['session']=='fresh' and s['hint_count']==0
 assert r['pins']['vector_reallocation_model']==e['model'] and r['pins']['method_version']['id']==e['method_id']
 assert r['proof_setup_check']['verdict']=='passed' and len(r['proof_setup_check']['runs'])==3 and r['proof_setup_check']['method_version']==r['pins']['method_version']
 assert len(r['unproven_properties'])==1 and r['unproven_properties'][0]['goal']==r['goals'][2]['goal'] and r['unproven_properties'][0]['failure_class']=='timeout'
 assert len(r['assumptions'])==9 and all(a['kind']=='trusted_tool' for a in r['assumptions']),'unexpected user assumption, desired lemma or imported helper clause'
 return {'attempted':3,'direct_valid':2,'timeout_target':runs[2]['id'],'unexecuted':e['target_ids'][3:],'model_acceptance':False,'caller_acceptance':False,'original_v2_acceptance':False}

def target_census(inv,native,record_goal,target,csv):
 goal='typed_real_check_lemma_'+target['goal'];prop='check_lemma_'+target['goal'];passed=record_goal['status']=='valid'
 assert inv['complete'] is True and inv['version']=='1' and len(inv['goals'])==len(native)==1 and len(inv['properties'])==2
 g=inv['goals'][0];n=native[0]
 assert g=={'function':None,'goal':goal,'line':74,'passed':passed,'property':prop,'results':['timeout','valid'] if passed else ['timeout','unknown','unknown'],'smoke':False,'targets':[]}
 props={v['property']:v for v in inv['properties']};assert set(props)=={'',prop}
 for ident,p in props.items():
  assert p['function'] is None and p['dependencies']==[] and p['origin'] is None and p['extern'] is False and p['emitter']=='' and p['generated_smoke_failure'] is False
  assert p['line']==(0 if ident=='' else 74) and p['kind']==('other' if ident=='' else 'lemma') and p['description']==('module\nheap_reallocation::Heap' if ident=='' else 'check lemma\n'+target['goal'])
 assert n['goal']==goal and n['property']==prop and n['line']==74 and n['passed']==passed and n['smoke'] is False and n['verdict']==('valid' if passed else 'timeout') and 'function' not in n
 assert Path(n['file']).name=='wp_input.c' and Path(n['file']).is_absolute()
 expected_provers=['qed','CVC5:1.2.1' if passed else 'Alt-Ergo:2.6.4'];assert [v['prover'] for v in n['provers']]==expected_provers
 assert [v['success'] for v in n['provers']]==([0,1] if passed else [0,0]) and all(type(v['success']) is int and type(v['time']) in [int,float] and math.isfinite(v['time']) and v['time']>=0 for v in n['provers'])
 assert n.get('proved',0)==(1 if passed else 0) and n.get('timeout',0)==(0 if passed else 1)
 assert csv=='directory\tfile\tline\tfunction\tproperty kind\tstatus\tproperty\n','mathematical lemma report has unexpected C properties'
 assert record_goal['goal']==goal and record_goal['property']==prop and record_goal['seconds']==(n['provers'][1]['time'] if passed else None)
 return {'goal':goal,'ordinary':1,'smokes':0,'properties':2,'CSV_rows':0,'direct_valid':passed,'portfolio_results':g['results'],'native_best':n['verdict'],'scope':'Isolated check lemma, no C body or generated smoke attempt in this target.'}

def why3_tokens(text):
 # Strip nested OCaml comments and strings without allowing hidden declarations.
 out=[];i=0;depth=0
 while i<len(text):
  if text.startswith('(*',i) and not text.startswith('(*)',i):depth+=1;i+=2;continue
  if depth:
   if text.startswith('*)',i):depth-=1;i+=2
   else:
    if text[i]=='\n':out.append('\n')
    i+=1
   continue
  if text[i]=='"':
   i+=1
   while i<len(text) and text[i]!='"':
    if text[i]=='\\':i+=1
    i+=1
   assert i<len(text),'unterminated Why3 string';i+=1;out.append(' ');continue
  out.append(text[i]);i+=1
 assert depth==0,'unterminated Why3 comment'
 return ''.join(out)





def check_module_manifest(metadata):
 # Source-manifest has208distinct files. Coordinator counted both one physical
 # SHA and one Git-blob comparison perfile, hence416checks, not416files.
 manifest=metadata['files']['source-manifest.json']['content']
 assert isinstance(manifest,dict) and len(manifest)==208,'selected module file census differs'
 assert metadata['module_physical_git_checks']==416==2*len(manifest),'module physical/Git check census differs'
 assert all(isinstance(k,str) and k.startswith('swdb-project/swdb/') and isinstance(v,str) and len(v)==64 and set(v)<=set('0123456789abcdef') for k,v in manifest.items()),'invalid module source pin'
 return {'files':len(manifest),'physical_git_checks':metadata['module_physical_git_checks']}

def audit(raw_arg,project_arg,policy_arg):
 raw=Path(raw_arg).resolve();project=Path(project_arg).resolve();pf=Path(policy_arg);assert sha(pf)==POLICY_SHA256
 p=json.loads(pf.read_text());e=p['expected'];m=p['metadata'];r=p['record'];root=raw/'qualified-grow-profile';checks=0;physical={}
 assert raw==Path(p['raw']) and project==Path(p['project']) and m['connection']['sha']==e['source_commit']==p['source_commit']
 def pin(path,h=None,n=None):
  nonlocal checks
  path=Path(path);actual=sha(path);size=path.stat().st_size;assert h is None or actual==h,'physical digest differs';assert n is None or size==n,'physical size differs'
  physical[str(path)]={'sha256':actual,'bytes':size};checks+=1;return actual
 def ref(row):return pin(row['path'],row['sha256'],row.get('bytes'))
 whole=m['whole_raw_manifest'];assert len(whole)==378 and sum(v['bytes'] for v in whole.values())==23369201
 # Exact root raw census; no writes, symlinks or special members accepted.
 def raw_members():
  rows={}
  for path in raw.rglob('*'):
   mode=path.lstat().st_mode;assert stat.S_ISDIR(mode) or stat.S_ISREG(mode),'special or symlink raw member'
   if stat.S_ISREG(mode):rows[str(path.relative_to(raw))]={'sha256':pin(path),'bytes':path.stat().st_size}
  return rows
 assert raw_members()==whole,'settled raw membership/bytes differs'
 for key,row in m['files'].items():pin(raw/key,row['sha256'],row['bytes'])
 for relative,h in m['files']['source-manifest.json']['content'].items():pin(project.parent/relative,h)
 module_counts=check_module_manifest(m)
 for row in e['source_blobs']:pin(project/row['relative'],row['sha256'])
 closures=[]
 for row in m['source_consumer_closures']:
  ref(row);c=json.loads(Path(row['path']).read_text());assert c['source_commit']==e['source_commit'] and c['trees']==e['source_consumer_trees'] and c['physical_git_blob_equality'] is True
  assert c['count']==len(c['files'])==1553 and c['total_bytes']==sum(v['bytes'] for v in c['files'])==1337447798;closures.append(c)
 assert closures[0]==closures[1] and len(closures)==2
 c=closures[0];wanted={v['relative'] for v in c['files']};found=set()
 for relative in e['source_consumer_trees']:
  tree=project/relative
  for q in ([tree] if tree.is_file() else tree.rglob('*')):
   mode=q.lstat().st_mode;assert stat.S_ISREG(mode) or stat.S_ISDIR(mode)
   if stat.S_ISREG(mode):found.add(str(q.relative_to(project)))
 assert found==wanted,'complete source-consumer membership differs'
 # One streamed pass hashes1.33GB into both SHA256 and raw Git blob IDs;
 # no git process, filter, production import or source payload output.
 source_stat={}
 for row in c['files']:
  path=Path(row['path']);assert path==project/row['relative'];before=path.stat();h=hashlib.sha256();git=hashlib.sha1(('blob '+str(before.st_size)+'\0').encode())
  with path.open('rb') as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block);git.update(block)
  after=path.stat();assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino) and before.st_size==row['bytes'] and h.hexdigest()==row['sha256'] and git.hexdigest()==row['git_blob']
  source_stat[str(path)]=(after.st_size,after.st_mtime_ns,after.st_ino);checks+=1
 # Both context-dependent compiler identities are independently recomputed.
 for key in ['runtime-provenance.json','qualified-grow-profile/heap-project-runtime-provenance.json']:
  context=m['files'][key]['content'];actual=json.loads((raw/key).read_text());assert actual==context
  assert actual['lowering_identity']['c_lowering']['sha256']==lowerer_projection(project,actual['runtime'])
  for name,row in e['linux_clang_components'].items():assert actual['runtime'][name]==row
  for name in ['driver','command_executable']:ref(actual['runtime'][name])
 context=m['files']['qualified-grow-profile/heap-project-runtime-provenance.json']['content'];assert r['settings']['compiler_runtime']==context['runtime']
 for row in e['tools'].values():ref(row)
 for row in e['wp_artifacts']:ref(row)
 ref(e['why3_config']);prefix=Path(e['linux_prefix'])
 for key,folder in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:
  rows=[]
  for path in sorted(folder.rglob('*')):
   mode=path.lstat().st_mode;assert stat.S_ISDIR(mode) or stat.S_ISREG(mode),'nonregular runtime support member'
   if stat.S_ISREG(mode):rows.append({'relative':str(path.relative_to(folder)),'sha256':pin(path)})
  assert rows==e['portable_import_surfaces'][key],'complete runtime support closure differs'
 for row in e['typed_machine_sources']:pin(prefix/'lib/frama-c-wp/core'/row['name'],row['sha256'])
 typed=r['settings']['vector_reallocation_typed_runtime'];assert typed['heap_model']=='Typed' and typed['integer_model']=='Machine' and typed['raw_effective_type_safety_proved'] is False
 assert {Path(v['path']).name:v['sha256'] for v in typed['sources']}=={v['name']:v['sha256'] for v in e['typed_machine_sources']}
 for row in typed['sources']:ref(row)
 compiler=r['settings']['compiler_runtime'];frontend=compiler['frontend'];resource=Path(frontend[frontend.index('-resource-dir')+1]);llvm=resource.parents[2];libs=[q.resolve() for q in [llvm/'lib/libclang.so',llvm/'lib/libclang.dylib'] if q.is_file()];assert len(libs)==1 and pin(libs[0])==compiler['parser']['sha256']
 hh=hashlib.sha256();count=0
 for label,folder in [('libc++',llvm/'include/c++/v1'),('clang-resource',resource/'include')]:
  for q in sorted(folder.rglob('*')):
   if q.is_file():hh.update(label.encode()+b'\0'+str(q.relative_to(folder)).encode()+b'\0');hh.update(bytes.fromhex(pin(q)));count+=1
 assert compiler['headers']=={'id':'llvm-standard-resource-headers','sha256':hh.hexdigest(),'files':count}
 foundation=r['settings']['heap_model_foundations'];assert r['pins']['heap_model_foundations']['sha256']==digest(foundation['sources'])
 for row in foundation['sources']:ref(row)
 for key in ['metadata_executable'] :pin(foundation[key],foundation[key+'_sha256'])
 setup=r['proof_setup_check'];source=(project/'swdb/proof_setup.py').read_text();tree=ast.parse(source);names=[]
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHECK_SOURCES' for t in node.targets):names=list(ast.literal_eval(node.value))
  if isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='CHECK_SOURCES':names.extend(ast.literal_eval(node.value))
 identity=digest([{'path':'swdb/'+n,'sha256':pin(project/'swdb'/n)} for n in names]+[{'path':'vocab/proof_failure_classes.yaml','sha256':pin(project/'vocab/proof_failure_classes.yaml')}])
 assert setup['check']==r['verdict_reading']['check']=={'version':'1','sha256':identity} and all(run['reading']['check']==setup['check'] for run in r['settings']['heap_model_runs'])
 for row in r['evidence']['reports']+[r['evidence']['adapter_log']]:ref(row)
 # The root supplied exact parsed YAML as compact metadata; actual YAML bytes
 # must match its capture. No YAML or production interpreter is imported here.
 pin(raw/p['record_key'],m['files'][p['record_key']]['sha256'],m['files'][p['record_key']]['bytes'])
 classification=check_record(r,e);check_bindings(r,project,pin)
 result=json.loads((root/'result.json').read_text());assert result==m['files']['qualified-grow-profile/result.json']['content']
 assert result['public_complete'] is False and result['model_proof_acceptance'] is False and result['caller_acceptance'] is False and result['original_v2_acceptance'] is False and result['cold_task_hypothesis_closure_pending'] is True
 assert result['public_command_launched'] is True and result['public_exit_code']==0 and result['ambient_wp_names']==[] and result['within_whole_budget'] is True
 for file in ['resources.json','outer-resources.json']:
  g=json.loads((raw/file).read_text());assert g['exit_code']==1 and not g['out_of_memory'] and not g['timed_out'] and 0<g['peak_rss_bytes']<8589934592 and 0<g['wall_seconds']<4200
 lane=json.loads((raw/'lane.json').read_text())['socket_lane'];assert lane['exit_code']==1 and lane['node']==0 and lane['lease_generation']==590
 assert m['finite_process_sweeps'] and len(m['finite_process_sweeps'])==3 and all(not s['selected_same_uid'] and not s['inspection_denial_pids'] for s in m['finite_process_sweeps'])
 assert len(m['leases'])==3 and {v['state'] for v in m['leases'].values()}=={'released'}
 before=m['prior_prepublic_raw_manifest'];assert len(before)==49
 old=Path('/data/yanruj/EvolveSWDB_runs/probata-reviewed-01771a83-t25-qualified-grow-public-v1')
 assert {str(q.relative_to(old)) for q in old.rglob('*') if q.is_file()}==set(before)
 for rel,row in before.items():pin(old/rel,row['sha256'],row['bytes'])
 canonical=p['canonical_manifest'];assert canonical['obligations']==r['settings']['heap_model_view']['obligations']
 assert sha(root/'canonical-inputs/manifest.json')==e['canonical_manifest_sha256']
 for filename,text in p['canonical_C'].items():assert H(text.encode())==sha(root/'canonical-inputs'/filename)
 heap=root/'canonical-inputs/theory/heap_reallocation.mlw';assert heap.read_text()==p['canonical_theory'] and not re.search(r'^\s*(?:axiom|lemma|goal)\b',why3_tokens(heap.read_text()),re.M),'project imported heap contains desired propositions'
 censuses=[]
 for index,run in enumerate(r['settings']['heap_model_runs']):
  d=Path(run['cwd']);target=canonical['obligations'][index];assert d.is_relative_to(root) and sha(d/'wp_input.c')==target['sha256']
  cmd=run['command'];assert cmd[0]==e['tools']['frama-c']['path'] and not any(q.startswith(('-wp-prop','-wp-gen','-wp-script','-wp-session','-wp-filter-init','-wp-no-rte')) for q in cmd)
  assert all(cmd.count(q)>=1 for q in ['-wp','-wp-rte','-wp-no-filter-init','-wp-smoke-tests','-wp-status-all','-wp-print']) and '-load-module' in cmd
  for flag,want in [('-wp-cache','none'),('-wp-model','+real'),('-rte-initialized','@all'),('-wp-par','1'),('-wp-prover','alt-ergo,z3,cvc5'),('-wp-timeout','30')]:assert [cmd[j+1] for j,q in enumerate(cmd[:-1]) if q==flag] and set(cmd[j+1] for j,q in enumerate(cmd[:-1]) if q==flag)=={want}
  assert run['resources']['exit_code']==0 and not run['resources']['out_of_memory'] and not run['resources']['timed_out']
  inv=json.loads((d/'wp-inventory.json').read_text());native=json.loads((d/'wp-goals.json').read_text());censuses.append(target_census(inv,native,r['goals'][index],target,(d/'wp-properties.csv').read_text()))
  assert native[0]['file']==str(d/'wp_input.c')
 # No later target may have a generated run directory or goal/native output.
 runsdir=Path(r['settings']['heap_model_runs'][0]['cwd']).parent
 assert {d.name for d in runsdir.glob('heap-job-*') if d.is_dir()}=={'heap-job-'+v for v in e['target_ids'][:3]}
 task_evidence=task_context_audit(p,root,pin)
 for path,st in source_stat.items():
  q=Path(path).stat();assert (q.st_size,q.st_mtime_ns,q.st_ino)==st,'source consumer changed during reader'
 assert raw_members()==whole,'raw changed during reader'
 return {'classification':'PASS_PARTIAL_CLASSIFICATION_ONLY','reader_sha256':sha(__file__),'policy_sha256':sha(pf),'physical_checks':checks,'physical_files':len(physical),'source_commit':e['source_commit'],'source_consumer_files':1553,'source_consumer_bytes':1337447798,'module_source_files':module_counts['files'],'module_physical_git_checks':module_counts['physical_git_checks'],'whole_raw_files':378,'whole_raw_bytes':23369201,'old49_unchanged':True,'classification_detail':classification,'actual_target_censuses':censuses,'task_context_evidence':task_evidence,'model_acceptance':False,'caller_acceptance':False,'original_v2_acceptance':False,'all20_complete':False,'refuted':False,'integrity_errors':[]}

def smt_tokens(text):
 tokens=[];i=0
 while i<len(text):
  c=text[i]
  if c.isspace():i+=1;continue
  if c==';':
   j=text.find('\n',i);i=len(text) if j<0 else j+1;continue
  if c in '()':tokens.append(c);i+=1;continue
  if c in '"|':
   delim=c;start=i;i+=1
   while i<len(text):
    if text[i]==delim:
     if delim=='"' and i+1<len(text) and text[i+1]=='"':i+=2;continue
     i+=1;break
    if text[i]=='\\' and delim=='|':i+=1
    i+=1
   else:raise AssertionError('unterminated SMT quoted token')
   tokens.append(text[start:i]);continue
  j=i
  while i<len(text) and not text[i].isspace() and text[i] not in '();':i+=1
  assert i>j;tokens.append(text[j:i])
 return tokens

def smt_forms(text):
 tokens=smt_tokens(text);stack=[];forms=[]
 for token in tokens:
  if token=='(':stack.append([])
  elif token==')':
   assert stack,'unmatched SMT close';form=stack.pop()
   if stack:stack[-1].append(form)
   else:forms.append(form)
  else:
   assert stack,'stray top-level SMT token';stack[-1].append(token)
 assert not stack,'unterminated SMT form';return forms

def printed_blocks(text):
 lines=text.splitlines();blocks=[]
 for a,s in enumerate(lines):
  if not re.fullmatch(r'\s*theory WP\s*',s):continue
  ends=[i for i in range(a+1,len(lines)) if re.fullmatch(r'\s*end\s*',lines[i])];assert ends,'unterminated WP theory';z=ends[0]
  block='\n'.join(lines[a:z+1])+'\n';clean=why3_tokens(block)
  candidates=list(re.finditer(r'^([ \t]*)(type|constant|function|predicate|axiom|lemma|goal|use|clone|meta|inductive|val|let)\s+([^\s:(=]+)',clean,re.M));indent=min((len(m[1]) for m in candidates),default=0);heads=[m for m in candidates if len(m[1])==indent];decls=[];queries=[]
  for index,m in enumerate(heads):
   end=heads[index+1].start() if index+1<len(heads) else clean.rfind('end');body=clean[m.start():end].strip();decls.append({'kind':m[2],'name':m[3],'canonical_whitespace_body_sha256':H(' '.join(body.split()).encode())})
   if m[2]=='goal':
    assert ':' in body;query=body.split(':',1)[1].strip();canonical=' '.join(query.split());assert len(canonical.encode())<=12288,'goal-only canonical text exceeds12KiB'
    queries.append({'name':m[3],'canonical_whitespace_formula':canonical,'sha256':H(canonical.encode())})
  imports=re.findall(r'\(\*\s*use\s+([^\s*]+)\s*\*\)',block)
  blocks.append({'start_line':a+1,'end_line':z+1,'sha256_utf8_lines':H(block.encode()),'imports':imports,'declarations':decls,'queries':queries})
 return blocks

def materialized_smt(text):
 forms=smt_forms(text);assert forms and all(isinstance(f,list) and f and isinstance(f[0],str) for f in forms),'malformed SMT top form'
 assertions=[]
 def nodes(v):
  yield v
  if isinstance(v,list):
   for n in v:yield from nodes(n)
 for index,form in enumerate(forms):
  if form[0]!='assert':continue
  assert len(form)==2,'assert arity';labels=[]
  for node in nodes(form[1]):
   if isinstance(node,list):labels.extend(node[j+1] for j,t in enumerate(node[:-1]) if t==':named')
  assertions.append({'index':index,'labels':labels,'body_sha256':digest(form[1])})
 checks=[i for i,f in enumerate(forms) if f[0]=='check-sat'];last=next((f[1] for f in reversed(forms[:checks[0]]) if f[0]=='assert'),None) if len(checks)==1 else None
 unwrapped=last[1] if isinstance(last,list) and last and last[0]=='!' and len(last)>=2 else last
 return {'top_level_command_count':len(forms),'command_heads':dict(Counter(f[0] for f in forms)),'assertions':assertions,'check_sat_indices':checks,'last_assertion_is_negation':isinstance(unwrapped,list) and bool(unwrapped) and unwrapped[0]=='not','last_assertion_canonical_sexpr_sha256':digest(last) if last is not None else None,'materialized_only':True,'actual_submission_attested':False}

def imported_context(roots,std,wp,heap,pin):
 closure={};visiting=set()
 def visit(name):
  if name in closure:return
  assert name not in visiting,'import cycle';visiting.add(name)
  if name=='why3.BuiltIn.BuiltIn':closure[name]={'classification':'selected Why3 intrinsic core trust'}
  else:
   if name=='heap_reallocation.Heap':path=heap
   else:
    rel=name.rsplit('.',1)[0].replace('.','/')+'.mlw';choices=[q for q in [std/rel,wp/rel] if q.is_file()];assert len(choices)==1,'shadowed/unresolved source module';path=choices[0]
   text=why3_tokens(path.read_text());module=name.rsplit('.',1)[1]
   found=list(re.finditer(r'^(?:module|theory) '+re.escape(module)+r'\b[^\n]*\n(.*?)^end\s*$',text,re.M|re.S));assert len(found)==1,'ambiguous import module boundary';body=found[0][1]
   edges=[]
   for match in re.finditer(r'^\s*(use|clone)\s+(?:(?:import|export)\s+)?([A-Za-z_]\w*(?:\.\w+)*)\b',body,re.M):
    kind,target=match.groups();full=target if '.' in target else name.rsplit('.',1)[0]+'.'+target;edges.append({'kind':kind,'target':full});visit(full)
   props=[{'kind':m[1],'name':m[2]} for m in re.finditer(r'^\s*(axiom|lemma|goal)\s+(\w+)',body,re.M)]
   if name=='heap_reallocation.Heap':assert props==[],'project desired-result premise in imported heap'
   closure[name]={'source':str(path),'sha256':pin(path),'module_body_sha256':H(body.encode()),'dependencies':edges,'proposition_declarations':props,'classification':'uniform project definitions' if name=='heap_reallocation.Heap' else 'selected trusted standard arithmetic/map/Qed foundation'}
  visiting.remove(name)
 for root in sorted(roots):visit(root)
 return closure

def task_context_audit(p,root,pin):
 expected=p['actual_task_metadata'];out={'printed_queries':[],'materialized_tasks':[]};roots=set();counts=[]
 kinds=[['function','function','constant','predicate','predicate','predicate','predicate','predicate','predicate','goal'],['predicate']*4+['goal'],['predicate']*3+['goal']]
 names=[['L_t25_initial','L_t25_allocated','L_t25_sample','P_t25_fields','P_t25_repr','P_t25v3_repr','P_t25v3_eligible','P_t25v3_copy_frame','P_t25v3_copy_inv','wp_goal'],['P_t25_fields','P_t25_repr','P_t25v3_repr','P_t25v3_eligible','wp_goal'],['P_t25_fields','P_t25_repr','P_t25v3_repr','wp_goal']]
 for index,row in enumerate(expected['logs']):
  pin(row['path'],row['sha256'],row['bytes']);text=Path(row['path']).read_text();blocks=printed_blocks(text);assert blocks==row['printed_theories'] and len(blocks)==1
  declarations=blocks[0]['declarations'];assert [d['kind'] for d in declarations]==kinds[index] and [d['name'] for d in declarations]==names[index],'only exact source definitions and single query permitted'
  query=blocks[0]['queries'];assert len(query)==1 and query[0]['name']=='wp_goal';actual_imports=sorted(set(re.findall(r'\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)',text))|set(blocks[0]['imports']));assert actual_imports==row['direct_imports'];roots.update(actual_imports);out['printed_queries'].append({'target':p['expected']['target_ids'][index],**blocks[0]})
  # Require every printed project symbol have a concrete defining equation;
  # an uninterpreted constant or undeclared desired proposition is refused.
  lines=text.splitlines();clean=why3_tokens('\n'.join(lines[blocks[0]['start_line']-1:blocks[0]['end_line']]))
  heads=list(re.finditer(r'^    (function|constant|predicate|goal)\s+([^\s:(=]+)',clean,re.M))
  assert len(heads)==len(declarations)
  for j,head in enumerate(heads[:-1]):assert '=' in clean[head.end():heads[j+1].start()],'source symbol lacks a defining equation'
  metadata=[{'line':i+1,'text':s} for i,s in enumerate(lines) if s.startswith(('Goal ','Prover ')) or any(v in s for v in ['Warning:','[Failure]','[Timeout]','Proved goals:'])]
  assert metadata==p['metadata']['retained_log_metadata'][index]['metadata_only_lines'],'all retained result/warning lines differ'
  counts.append(sum(s.startswith('Prover ') for s in lines))
 assert counts==[2,2,3]
 # Independently reviewed canonical source mappings for h,values,r,o,b,bo,s,c:
 # heap,t,i4,i3,i,i1,i5,i2. Concrete sample is unfolded as a source constant.
 q=[v['queries'][0]['canonical_whitespace_formula'] for v in out['printed_queries']]
 assert q[0]==r'((well_formed L_t25_sample /\ available L_t25_sample 2 128) /\ P_t25v3_eligible L_t25_sample 1 0 2 0 1 1) /\ P_t25v3_copy_inv L_t25_sample (allocate L_t25_sample 2 128) 1 0 2 0 1 1 3 2 0'
 assert q[1]==r'forall i:int, i1:int, i2:int, heap:heap, i3:int, i4:int, i5:int. let x = 8 + i3 in let x1 = 16 + i3 in P_t25v3_eligible heap i4 i3 i i1 i5 i2 -> ((((initialized_at heap i4 i3 /\ typed_reads heap i4 i3 8 8) /\ initialized_at heap i4 x) /\ initialized_at heap i4 x1) /\ typed_reads heap i4 x 8 8) /\ typed_reads heap i4 x1 8 8'
 assert q[2]==r'forall i:int, i1:int, i2:int, heap:heap, i3:int, i4:int, i5:int, t:int -> int. bounded_int_values t i1 i5 -> P_t25_repr heap i4 i3 i i1 i5 i2 -> i5 = 0 \/ not i4 = i -> P_t25v3_repr (project_int_region heap t i i1 i5) i4 i3 i i1 i5 i2'
 allowed={'bool.Bool','frama_c_wp.qed.Qed','heap_reallocation.Heap','int.Abs','int.ComputerDivision','int.Int','map.Map','real.RealInfix','why3.BuiltIn.BuiltIn'};assert roots==allowed
 prefix=Path(p['expected']['linux_prefix']);closure=imported_context(roots,prefix/'share/why3/stdlib',prefix/'share/frama-c/share/wp/why3',root/'canonical-inputs/theory/heap_reallocation.mlw',pin)
 actual_paths=sorted(q for row in expected['logs'] for q in (Path(row['path']).parent/'prover-files').rglob('*') if q.is_file() and q.suffix in ['.smt2','.psmt2'])
 assert {str(q) for q in actual_paths}=={t['path'] for t in expected['materialized_tasks']} and len(actual_paths)==14
 for task in expected['materialized_tasks']:
  pin(task['path'],task['sha256'],task['bytes']);census=materialized_smt(Path(task['path']).read_text());assert census=={k:v for k,v in task.items() if k not in {'path','sha256','bytes'}}
  assert census['last_assertion_is_negation'] and len(census['check_sat_indices'])==1
  forms=smt_forms(Path(task['path']).read_text());asserts=[v[1] for v in forms if v[0]=='assert'];final=asserts[-1];final=final[1] if final[0]=='!' else final;assert final[0]=='not' and all(v!=final[1] and v!='false' for v in asserts[:-1]),'desired result or false inserted as premise'
  out['materialized_tasks'].append(task)
 out.update(import_source_modules=closure,materialized_task_count=14,actual_submission_count=None,submitted_bytes_identity_qualified=False,project_imported_desired_axioms_or_lemmas=0,printed_project_desired_axioms_or_lemmas=0,source_query_mapping_checked=True,flattened_instantiated_standard_axioms_independently_proven=False,proof_boundary='Partial check-lemma observations under selected trusted WP/Why3/solver and explicit standard foundations. Printed project definitions and source-mapped queries checked. Materialized SMT assertion identities are pinned, not submitted-byte attestation or an independent proof of standard axioms. No full model/caller acceptance.')
 return out

def check_bindings(r,project,pin):
 s=r['settings'];v=s['heap_model_view'];pins=r['pins'];base=project/'swdb'
 assert pins['heap_model_view_certificate']=={'id':'qualified-vector-heap-certificate-1','sha256':digest(v)}
 names=('vector_reallocation_view.py','vector_reallocation_model.py','vector_reallocation_vcs.py','vector_reallocation_inventory.py','heap_reallocation.mlw','heap_model_vcs.py','heap_model_view.py')
 assert pins['heap_model_view_check']=={'id':'qualified-vector-heap-view-1','sha256':digest([{'path':n,'sha256':pin(base/n)} for n in names])}
 assert pins['std_models']['sha256']==pin(base/'std_models.py')
 model_names=('vector_reallocation_model.py','vector_reallocation_vcs.py','vector_reallocation_inventory.py','heap_reallocation.mlw','heap_model_vcs.py')
 assert pins['vector_reallocation_model']['sha256']==H(b''.join((base/n).read_bytes() for n in model_names)+pins['std_models']['sha256'].encode())
 assert r['proof_setup_check']['hashes']['compiler_runtime']==digest(s['compiler_runtime']) and pins['code']['sha256']==pins['contract']['sha256']==v['original_source']['sha256']
 for run,setup,target in zip(s['heap_model_runs'],r['proof_setup_check']['runs'],v['obligations']):
  h=setup['hashes'];assert setup['verdict']=='passed' and setup['tool']=='wp' and h['wp_input.c']==run['input_sha256']==target['sha256'] and h['compiler_runtime']==digest(s['compiler_runtime']) and h['heap_model_view']==pins['heap_model_view_certificate']['sha256']
  assert h['dx100_source_selector']==digest([]) and h['summaries']==digest([]) and h['summary_bindings']==digest([]) and h['stdlib_provenance']==digest({})
  plan={'command':run['command'],'flags':s['flags'],'inputs':h,'bounds':None,'method_version':pins['method_version']}
  assert digest(plan)==setup['run_plan_sha256'],'per-launch command/input/setup/method plan differs'
 assert r['proof_setup_check']['hashes']['wp_input.c']==v['obligations'][2]['sha256']

if __name__=='__main__':
 if not __debug__:raise SystemExit('optimized reader refused')
 try:print(json.dumps(audit(*sys.argv[1:]),sort_keys=True,indent=2))
 except Exception as error:
  tb=error.__traceback__;locations=[];source=Path(__file__).read_text();tree=ast.parse(source)
  while tb:
   if Path(tb.tb_frame.f_code.co_filename).resolve()==Path(__file__).resolve():
    line=tb.tb_lineno;nodes=[n for n in ast.walk(tree) if isinstance(n,ast.Assert) and n.lineno<=line<=getattr(n,'end_lineno',n.lineno)];expr=ast.get_source_segment(source,nodes[-1].test) if nodes else None;locations.append({'line':line,'function':tb.tb_frame.f_code.co_name,'assertion':expr[:1000] if expr else None})
   tb=tb.tb_next
  print(json.dumps({'status':'REFUSED','error_type':type(error).__name__,'locations':locations,'model_acceptance':False,'scope':'Partial cold classification refused; no raw/env/frame values exposed'},indent=2));raise SystemExit(1)
