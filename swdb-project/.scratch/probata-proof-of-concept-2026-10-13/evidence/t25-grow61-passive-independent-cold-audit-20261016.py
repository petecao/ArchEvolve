"""2026-10-16 ET. Passive complete grow61 cold audit; no project/tool execution."""
from pathlib import Path
from collections import Counter
import ast,base64,copy,csv,datetime,hashlib,io,json,math,re,resource,signal,subprocess,sys,time,zlib
import yaml
H=lambda b:hashlib.sha256(b).hexdigest()
def sha(p):return pin(p)["sha256"]

def digest(v):return H(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())

def summary(v):
 b=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
 return {'type':type(v).__name__,'canonical_bytes':len(b),'sha256':H(b)}

def safe_atom(text):
 if isinstance(text,str)and len(text.encode())<=256 and re.fullmatch(r"[A-Za-z_~!@$%^&*=+<>.?/\-][A-Za-z0-9_~!@$%^&*=+<>.?/'\-]*",text):return text
 return {'omitted_non_symbolic_atom':True,**summary(text)}

def delimiter_hash(text):
 clean=why3_tokens(text);stack=[[]];pairs={')':'(',']':'[','}':'{'}
 for token in re.findall(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*|[0-9]+|[^\s]',clean):
  if token in '([{':stack.append([token])
  elif token in ')]}':
   if len(stack)==1 or stack[-1][0]!=pairs[token]:raise ValueError('unbalanced query delimiter')
   node=stack.pop();stack[-1].append(node)
  else:stack[-1].append(token)
 if len(stack)!=1:raise ValueError('unclosed query delimiter')
 return digest(stack[0])

def no_payload_fields(value):
 # Known reporter textual fields can contain C formulas or native errors.
 if isinstance(value,dict):
  return {k:({'omitted_text':True,**summary(v)}if k in {'description','predicate','errmsg','error','error_message','formula','statement','sequent','body','source_text','message'}else no_payload_fields(v))for k,v in value.items()}
 if isinstance(value,list):return [no_payload_fields(v)for v in value]
 return value

def inventory_metadata(inventory,target):
 properties=inventory['properties'];goals=inventory['goals'];ids=[p['property']for p in properties]
 if len(ids)!=len(set(ids)):raise ValueError('duplicate native property ID')
 byid={p['property']:p for p in properties};missing=[]
 for p in properties:
  missing.extend(x for x in p.get('dependencies',[])if x not in byid)
  if p.get('origin')is not None and p['origin']not in byid:missing.append(p['origin'])
 if missing or any(g['property']not in byid or any(t not in byid for t in g.get('targets',[]))for g in goals):raise ValueError('native closure reference is missing')
 visiting=set();done=set()
 def visit(name):
  if name in visiting:raise ValueError('native dependency cycle')
  if name in done:return
  visiting.add(name)
  for dep in byid[name].get('dependencies',[]):visit(dep)
  visiting.remove(name);done.add(name)
 for name in byid:visit(name)
 ordinary=[g for g in goals if not g.get('smoke')];lemmas=[p for p in properties if p.get('kind')=='lemma']
 owner=None
 if target['kind']=='check_lemma':
  owner=len(lemmas)==1 and not lemmas[0].get('dependencies')and not lemmas[0].get('extern')and lemmas[0]['property'].endswith('_'+target['goal'])and bool(ordinary)and all(g['property']==lemmas[0]['property']for g in ordinary)
  if not owner:raise ValueError('isolated source lemma ownership differs')
 elif target['kind']!='c_kernel':raise ValueError('unknown canonical leaf kind')
 return {'content':no_payload_fields(inventory),'sole_source_lemma_ownership':owner,'kernel_sole_lemma_gate_applied':False,'ordinary_goals':len(ordinary),'smoke_goals':sum(bool(g.get('smoke'))for g in goals),'property_count':len(properties),'dependency_edges':sum(len(p.get('dependencies',[]))for p in properties),'dependency_DAG_acyclic':True,'all_origins_and_targets_closed':True,'extern_properties':[p['property']for p in properties if p.get('extern')],'full_description_or_call_predicate_exported':False}

def why3_tokens(text):
 # Preserve offsets while masking nested comments/strings. No Why3 execution.
 out=list(text);i=0;depth=0
 while i<len(text):
  if text.startswith('(*',i):
   out[i:i+2]='  ';depth+=1;i+=2;continue
  if depth:
   if text.startswith('*)',i):out[i:i+2]='  ';depth-=1;i+=2
   else:
    if text[i]!='\n':out[i]=' '
    i+=1
   continue
  if text[i]=='"':
   out[i]=' ';i+=1
   while i<len(text)and text[i]!='"':
    if text[i]=='\\':out[i]=' ';i+=1
    if i<len(text)and text[i]!='\n':out[i]=' '
    i+=1
   if i>=len(text):raise ValueError('unterminated Why3 string')
   out[i]=' ';i+=1;continue
  i+=1
 if depth:raise ValueError('unterminated Why3 comment')
 return ''.join(out)

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
 for a,line in enumerate(lines):
  if not re.fullmatch(r'\s*theory WP\s*',line):continue
  ends=[i for i in range(a+1,len(lines))if re.fullmatch(r'\s*end\s*',lines[i])]
  if not ends:raise ValueError('unterminated WP theory')
  valid=[]
  for z in ends:
   block='\n'.join(lines[a:z+1])+'\n'
   try:clean=why3_tokens(block)
   except ValueError:continue
   valid.append((z,block,clean));break
  if not valid:raise ValueError('unbalanced printed WP theory')
  z,block,clean=valid[0]
  candidates=list(re.finditer(r'^([ \t]*)(type|constant|function|predicate|axiom|lemma|goal|use|clone|meta|inductive|val|let)\s+([^\s:(=]+)',clean,re.M))
  indent=min((len(m[1])for m in candidates),default=0);heads=[m for m in candidates if len(m[1])==indent];decls=[];queries=[]
  for i,m in enumerate(heads):
   end=heads[i+1].start()if i+1<len(heads)else clean.rfind('end');body=clean[m.start():end].strip();rawbody=block[m.start():end].strip()
   tokens=re.findall(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*|[0-9]+|[^\s]',body)
   refs=sorted(set(t for t in tokens if re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*',t)))
   row={'kind':m[2],'name':safe_atom(m[3]),'raw_body_utf8_sha256':H(rawbody.encode()),'canonical_whitespace_body_sha256':H(' '.join(body.split()).encode()),'lexical_tokens_sha256':digest(tokens),'token_count':len(tokens),'identifier_references':[safe_atom(x)for x in refs],'typed_AST_reconstructed':False}
   decls.append(row)
   if m[2]=='goal':
    if ':'not in body:raise ValueError('printed goal has no formula delimiter')
    query=body.split(':',1)[1].strip();canonical=' '.join(query.split())
    queries.append({'name':safe_atom(m[3]),'canonical_whitespace_formula_sha256':H(canonical.encode()),'canonical_utf8_bytes':len(canonical.encode()),'lexical_tokens_sha256':digest(re.findall(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*|[0-9]+|[^\s]',query)),'delimiter_tree_sha256':delimiter_hash(query),'formula_exported':False,'typed_AST_reconstructed':False})
  imports=re.findall(r'\(\*\s*use\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\*\)',block)
  blocks.append({'start_line':a+1,'end_line':z+1,'sha256_utf8_lines':H(block.encode()),'imports':imports,'declarations':decls,'declaration_kind_counts':dict(Counter(d['kind']for d in decls)),'queries':queries,'sequent_exported':False})
 return blocks

def materialized_smt(text):
 forms=smt_forms(text)
 if not forms or not all(isinstance(f,list)and f and isinstance(f[0],str)for f in forms):raise ValueError('malformed SMT top form')
 assertions=[];commands=[];declarations=[]
 def nodes(v):
  yield v
  if isinstance(v,list):
   for n in v:yield from nodes(n)
 for index,form in enumerate(forms):
  commands.append({'index':index,'head':form[0],'form_sha256':digest(form),'arity':len(form)-1})
  if form[0].startswith(('declare-','define-')):
   declarations.append({'index':index,'kind':form[0],'name':safe_atom(form[1])if len(form)>1 and isinstance(form[1],str)else None,'form_sha256':digest(form)})
  if form[0]!='assert':continue
  if len(form)!=2:raise ValueError('assert arity')
  labels=[];atoms=[];operator_heads=Counter();binders=[]
  for node in nodes(form[1]):
   if isinstance(node,str):atoms.append(node);continue
   if not node:continue
   if isinstance(node[0],str):operator_heads[node[0]]+=1
   if isinstance(node[0],str)and node[0]in {'forall','exists','let'}:
    binders.append({'kind':node[0],'binding_sha256':digest(node[1])if len(node)>1 else None,'bindings_count':len(node[1])if len(node)>1 and isinstance(node[1],list)else None})
   for j,token in enumerate(node):
    if token!=':named':continue
    if node[0]!='!'or j<2 or j+1>=len(node):raise ValueError('malformed named annotation')
    label=node[j+1]
    if not isinstance(label,str)or len(label.encode())>256 or not re.fullmatch(r'[A-Za-z~!@$%^&*_=+<>.?/\-][A-Za-z0-9~!@$%^&*_=+<>.?/\-]*',label):raise ValueError('named label is not bounded unquoted symbolic atom')
    if j+2!=len(node)and not(isinstance(node[j+2],str)and node[j+2].startswith(':')):raise ValueError('named annotation has multiple values')
    if label in labels:raise ValueError('duplicate named label')
    labels.append(label)
  symbols=sorted(set(x for x in atoms if not x.startswith((':','"'))and not re.fullmatch(r'-?[0-9]+(?:\.[0-9]+)?',x)))
  assertions.append({'index':index,'labels':labels,'body_sha256':digest(form[1]),'symbol_references':[safe_atom(x)for x in symbols],'operator_head_counts':[{'head':safe_atom(k),'count':v}for k,v in sorted(operator_heads.items())],'binders':binders,'node_count':sum(1 for _ in nodes(form[1]))})
 checks=[i for i,f in enumerate(forms)if f[0]=='check-sat'];last=next((f[1]for f in reversed(forms[:checks[0]])if f[0]=='assert'),None)if len(checks)==1 else None
 unwrapped=last[1]if isinstance(last,list)and last and last[0]=='!'and len(last)>=2 else last
 return {'top_level_command_count':len(forms),'command_heads':dict(Counter(f[0]for f in forms)),'commands':commands,'declarations':declarations,'assertions':assertions,'all_assertion_bodies_hashed':len(assertions)==sum(f[0]=='assert'for f in forms),'check_sat_indices':checks,'last_assertion_is_negation':isinstance(unwrapped,list)and bool(unwrapped)and unwrapped[0]=='not','last_assertion_canonical_sexpr_sha256':digest(last)if last is not None else None,'materialized_only':True,'actual_submission_attested':False,'full_SMT_AST_exported':False}

def pin(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb')as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':p.stat().st_size}

def whole(root):
 found={}
 if root.is_symlink()or not root.is_dir():raise ValueError('producer root missing/redirected')
 for p in sorted(root.rglob('*')):
  if p.is_symlink()or not(p.is_file()or p.is_dir()):raise ValueError('producer symlink/special input')
  if p.is_file():found[str(p.relative_to(root))]={k:v for k,v in pin(p).items()if k!='path'}
 return found

def properties_csv(text):
 # Exact frozen proof_setup._property_rows multiline TSV grammar; no project import.
 reader=csv.reader(io.StringIO(text),delimiter='\t');header=next(reader,[])
 if header!=['directory','file','line','function','property kind','status','property']:raise ValueError('property TSV header differs')
 rows=[]
 for cells in reader:
  if not cells:continue
  if len(cells)==len(header):rows.append(dict(zip(header,cells)))
  elif len(cells)==1 and cells[0][:1].isspace()and rows:rows[-1]['property']+='\n'+cells[0]
  else:raise ValueError('malformed property TSV continuation')
 return rows

def safe_smt(text):
 value=materialized_smt(text)
 allowed={'set-logic','set-option','set-info','declare-sort','declare-fun','declare-const','declare-datatype','declare-datatypes','define-sort','define-fun','define-fun-rec','define-funs-rec','assert','check-sat','check-sat-assuming','push','pop','get-model','get-value','get-info','get-unsat-core','get-proof','get-assignment','exit','reset','reset-assertions','echo'}
 if set(value['command_heads'])-allowed:raise ValueError('nonstandard SMT command head refused')
 return value

def reconcile_leaf(ordinary,inventory,record_goals,target):
 # Metadata reconciliation only, not a reimplementation/admission of read_wp_reports.
 # Frozen reader lines659-670 allow independently passed inventory-only goals;
 # _goal normalizes an attempted healthy nonvalid passed smoke to status=valid.
 if not isinstance(ordinary,list)or not isinstance(record_goals,list):raise ValueError('native/normalized report list required')
 raw={g.get('goal'):g for g in ordinary};generated={g.get('goal'):g for g in inventory['goals']};normalized={g.get('goal'):g for g in record_goals}
 if len(raw)!=len(ordinary)or len(generated)!=len(inventory['goals'])or len(normalized)!=len(record_goals)or None in raw or None in generated or None in normalized:raise ValueError('ambiguous native/normalized goal identity')
 if set(raw)-set(generated)or set(normalized)!=set(generated):raise ValueError('native/normalized complete goal membership differs')
 ledger=[];healthy={'unknown','timeout','stepout','invalid'}
 for name,expected in generated.items():
  observed=raw.get(name);goal=normalized[name];smoke=bool(expected.get('smoke'));results=expected.get('results')
  if not isinstance(results,list)or not results or any(not isinstance(x,str)for x in results):raise ValueError('actual native observations missing')
  if expected.get('passed')is not True:raise ValueError('known completed producer has unpassed generated goal')
  if smoke:
   if any(x not in healthy for x in results):raise ValueError('passed smoke lacks healthy nonvalid actual observation')
  elif 'valid'not in results:raise ValueError('ordinary generated goal lacks native Valid observation')
  if any(goal.get(k)!=expected.get(k)for k in ['property','function'])or bool(goal.get('smoke'))!=smoke or goal.get('status')!='valid':raise ValueError('record normalized goal identity/status differs')
  if observed is None:
   if goal.get('source')!='wp_inventory':raise ValueError('inventory-only normalized provenance differs')
   provenance='passed_native_inventory_only'
  else:
   if any(observed.get(k)!=expected.get(k)for k in ['property','function'])or bool(observed.get('smoke'))!=smoke or observed.get('passed')is not True:raise ValueError('native ordinary report disagrees with inventory')
   if goal.get('source')!='wp_json':raise ValueError('raw-report normalized provenance differs')
   verdict=observed.get('verdict')
   if smoke and(verdict not in healthy or verdict not in results):raise ValueError('raw smoke disagrees with healthy inventory observations')
   if not smoke and verdict!='valid':raise ValueError('raw ordinary verdict differs from Valid')
   provenance='passed_healthy_nonvalid_smoke'if smoke else 'direct_native_valid'
  ledger.append({'goal':name,'property':expected['property'],'function':expected.get('function'),'smoke':smoke,'normalized_status':goal['status'],'normalized_source':goal.get('source'),'native_report_present':observed is not None,'native_verdict':observed.get('verdict')if observed else None,'native_passed':observed.get('passed')if observed else None,'inventory_results':results,'inventory_passed':expected['passed'],'provenance':provenance})
 if target['kind']=='check_lemma'and(any(r['smoke']for r in ledger)or len(ledger)!=1):raise ValueError('isolated math report census differs')
 if target['kind']=='c_kernel'and(not any(r['smoke']for r in ledger)or not any(not r['smoke']for r in ledger)):raise ValueError('numeric ordinary/smoke census missing')
 return {'id':target['id'],'kind':target['kind'],'native_report_rows':len(ordinary),'native_report_verdicts':dict(Counter(g.get('verdict')for g in ordinary)),'generated_goals':len(generated),'normalized_ordinary':sum(not r['smoke']for r in ledger),'normalized_smoke':sum(r['smoke']for r in ledger),'inventory_only_ordinary':sum(not r['smoke']and not r['native_report_present']for r in ledger),'goals':ledger,'ordinary_Valid_and_smoke_operational_observations_separated':True,'reader_executed':False,'proof_acceptance':False}

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

def schema_merge(envelope,kind):
 s=copy.deepcopy(kind);s.pop('$id',None);props=copy.deepcopy(envelope['properties'])
 for k,v in kind.get('properties',{}).items():props[k]={'allOf':[props[k],v]}if k in props else v
 s.update(properties=props,required=list(dict.fromkeys(envelope.get('required',[])+kind.get('required',[]))),allOf=envelope.get('allOf',[])+kind.get('allOf',[]),type='object',additionalProperties=False)
 s['$defs']={**copy.deepcopy(envelope.get('$defs',{})),**kind.get('$defs',{})};return s

def schema_expand(schema,vocabs):
 if isinstance(schema,list):return [schema_expand(v,vocabs)for v in schema]
 if not isinstance(schema,dict):return schema
 node={k:schema_expand(v,vocabs)for k,v in schema.items()}
 if 'x-vocab'in node:
  values=list(vocabs[node['x-vocab']]);node['enum']=values+([None]if isinstance(node.get('type'),list)and'null'in node['type']else[])
 return node

def schema_validate(value,schema,root=None):
 # Exact closed subset used by the frozen merged envelope/proof schemas.
 # Unknown validation keywords fail closed; annotations retain standard behavior.
 root=schema if root is None else root
 if isinstance(schema,bool):assert schema;return
 allowed={'$schema','$id','$defs','title','description','type','properties','required','allOf','oneOf','anyOf','not','if','then','else','$ref','const','enum','additionalProperties','minLength','maxLength','pattern','propertyNames','minProperties','maxProperties','items','minItems','maxItems','minimum','maximum','uniqueItems'}
 assert isinstance(schema,dict)and all(k in allowed or k.startswith('x-')for k in schema),'unreviewed schema keyword'
 if '$ref'in schema:
  ref=schema['$ref'];assert ref.startswith('#/')
  node=root
  for part in ref[2:].split('/'):node=node[part.replace('~1','/').replace('~0','~')]
  schema_validate(value,node,root)
 def matches(sub):
  try:schema_validate(value,sub,root);return True
  except AssertionError:return False
 if 'type'in schema:
  kinds=schema['type']if isinstance(schema['type'],list)else[schema['type']]
  types={'object':isinstance(value,dict),'array':isinstance(value,list),'string':isinstance(value,str),'null':value is None,'boolean':type(value)is bool,'integer':type(value)is int,'number':type(value)in(int,float)and math.isfinite(value)}
  assert all(k in types for k in kinds)and any(types[k]for k in kinds)
 if 'const'in schema:assert type(value)is type(schema['const'])and value==schema['const']
 if 'enum'in schema:assert any(type(value)is type(v)and value==v for v in schema['enum'])
 if 'allOf'in schema:
  for sub in schema['allOf']:schema_validate(value,sub,root)
 if 'oneOf'in schema:assert sum(matches(sub)for sub in schema['oneOf'])==1
 if 'anyOf'in schema:assert any(matches(sub)for sub in schema['anyOf'])
 if 'not'in schema:assert not matches(schema['not'])
 if 'if'in schema:
  branch='then'if matches(schema['if'])else'else'
  if branch in schema:schema_validate(value,schema[branch],root)
 if isinstance(value,dict):
  assert all(k in value for k in schema.get('required',[]))
  assert len(value)>=schema.get('minProperties',0)and len(value)<=schema.get('maxProperties',len(value))
  props=schema.get('properties',{})
  for k,v in value.items():
   if 'propertyNames'in schema:schema_validate(k,schema['propertyNames'],root)
   if k in props:schema_validate(v,props[k],root)
   elif 'additionalProperties'in schema:schema_validate(v,schema['additionalProperties'],root)
 if isinstance(value,list):
  assert len(value)>=schema.get('minItems',0)and len(value)<=schema.get('maxItems',len(value))
  if schema.get('uniqueItems'):assert len({digest(x)for x in value})==len(value)
  if 'items'in schema:
   for item in value:schema_validate(item,schema['items'],root)
 if isinstance(value,str):
  assert len(value)>=schema.get('minLength',0)and len(value)<=schema.get('maxLength',len(value))
  if 'pattern'in schema:assert re.search(schema['pattern'],value)is not None
 if type(value)in(int,float):assert math.isfinite(value)and value>=schema.get('minimum',value)and value<=schema.get('maximum',value)
 # No x-ref field is present in this c_model record. Refuse new reference-bearing
 # instances rather than pretending to validate an unrelated record catalog.
 if 'x-ref'in schema and isinstance(value,str):raise AssertionError('new record reference requires separate catalog audit')

def source_why3_tokens(text):
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
   text=source_why3_tokens(path.read_text());module=name.rsplit('.',1)[1]
   found=list(re.finditer(r'^(?:module|theory) '+re.escape(module)+r'\b[^\n]*\n(.*?)^end\s*$',text,re.M|re.S));assert len(found)==1,'ambiguous import module boundary';body=found[0][1]
   edges=[]
   for match in re.finditer(r'^\s*(use|clone)\s+(?:(?:import|export)\s+)?([A-Za-z_]\w*(?:\.\w+)*)\b',body,re.M):
    kind,target=match.groups();full=target if '.' in target else name.rsplit('.',1)[0]+'.'+target;edges.append({'kind':kind,'target':full});visit(full)
   props=[{'kind':m[1],'name':m[2]} for m in re.finditer(r'^\s*(?:let\s+rec\s+)?(axiom|lemma|goal)\s+(\w+)',body,re.M)]
   if name=='heap_reallocation.Heap':assert props==[],'project desired-result premise in imported heap'
   closure[name]={'source':str(path),'sha256':pin(path),'module_body_sha256':H(body.encode()),'dependencies':edges,'proposition_declarations':props,'classification':'uniform project definitions' if name=='heap_reallocation.Heap' else 'selected trusted standard arithmetic/map/Qed foundation'}
  visiting.remove(name)
 for root in sorted(roots):visit(root)
 return closure

def check_task_context(task,support):
 assert len(task['check_sat_indices'])==1 and task['last_assertion_is_negation']
 assert set(task['command_heads'])<={'set-info','set-logic','assert','check-sat','get-info','declare-fun','declare-sort','declare-datatypes','define-fun'}
 check=task['check_sat_indices'][0];last=max(a['index']for a in task['assertions']if a['index']<check)
 for command in task['commands']:
  if command['head']=='get-info':assert command['index']>check and command['arity']==1 and command['form_sha256']==digest(['get-info',':reason-unknown'])
 assert all(a['index']<=last for a in task['assertions'])
 counts=Counter()
 for assertion in task['assertions']:
  if assertion['index']!=last:
   h=assertion['body_sha256'];assert h in support;counts[support[h]['family']]+=1
 return counts

def scope_record(record,expected):
 assert record['kind']=='proof'and record['status']=='draft'and record['evidence_kind']=='contract_fixture'
 assert record['subject']=={'kind':'c_model','id':expected['member']}and record['verdict']=='proven'and record.get('failure_class')is None
 assert record['bounds']=={'threads':1,'input_size':'unbounded'}and not record.get('unproven_properties')
 settings=record['settings'];view=settings['heap_model_view'];q=view['qualification']
 assert q['original_contract_proved']is False and view['generic_caller_composition']=='unsupported'
 assert q['typed_source_image']==expected['typed_source_image']and q['typed_source_image']['applicable']is True
 assert settings['verifier_launched']is True and settings['session']=='fresh'and settings['hint_count']==0
 assert all(r['verdict']=='proven'and r['failure_class']is None for r in settings['heap_model_runs'])
 assert [r['id']for r in settings['heap_model_runs']]==expected['target_ids']
 return settings,view


CHECK_COUNT = 0


def require(value, label):
 global CHECK_COUNT
 if not value:raise ValueError(label)
 CHECK_COUNT += 1


def main(cfg):
 signal.alarm(90)
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 started=time.monotonic();raw=Path(cfg['raw']);source=Path(cfg['source']);project=source/'swdb-project';profile=raw/cfg['profile']
 before=whole(raw)
 def J(p):return json.loads(Path(p).read_bytes())
 def physical(p,expected=None):
  p=Path(p);require(p.is_file()and not p.is_symlink(),'regular physical input '+str(p));actual=pin(p)
  if expected is not None:require(actual['sha256']==expected,'physical hash '+str(p))
  return actual
 def git(*a,input=None):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(source),*a],input=input,timeout=45)
 require(git('rev-parse','HEAD').decode().strip()==cfg['source_commit']and not git('status','--porcelain','--untracked-files=all'),'exact clean current source')
 e=J(profile/'expected.json');require(physical(profile/'expected.json')['sha256']==cfg['packet_pins']['expected.json']['sha256'],'independent reviewed expected')
 for name in [profile/'entry.py',raw/'qualified-grow61-entry.py']:physical(name,cfg['packet_pins']['entry.py']['sha256'])
 require(e['source_commit']==cfg['source_commit']and e['remote_project']==str(project),'selected source/context')
 launch=J(raw/'launch.json');actual_command=[s.replace('{SOURCE}',str(source)).replace('{OUTPUT}',str(raw))for s in cfg['command']]
 require(launch['command']==actual_command and launch['source']==str(source)and launch['source_commit']==cfg['source_commit'],'exact prospective launch command')
 for name,h in e['linux_launch_binding']['wrappers'].items():physical(raw/name,h);require(launch['reviewed_wrapper_reuse'][name]==h,'wrapper launch binding')
 guards={n:J(raw/n)for n in ['resources.json','outer-resources.json']}
 for n,g in guards.items():require(g['exit_code']==0 and not g['out_of_memory']and not g['timed_out']and g['peak_rss_bytes']<=8589934592,'healthy whole guard '+n)
 lane=J(raw/'lane.json')['socket_lane'];require(lane['node']==0 and lane['lease_generation']==604 and lane['exit_code']==0 and lane['numa_memory_policy']=='bind:0','settled node0 G604')
 require(J(raw/'source-after.json')=={'commit':cfg['source_commit'],'source_unchanged':True,'tracked_changes':''},'sourceafter exact clean')
 require(set(J(raw/'dispatch-environment.json'))=={'HOME','USER','LOGNAME','SHELL','PATH','LANG','LC_ALL'},'closed actual dispatch environment')
 for row in e['source_blobs']+e['test_helper_pins']:physical(project/row['relative'],row['sha256'])
 consumers=[J(profile/('source-consumer-closure-'+str(i)+'.json'))for i in range(3)]
 require(consumers[0]==consumers[1]==consumers[2],'three source consumer before/after receipts equal')
 consumer=consumers[0]
 require(consumer['count']==len(consumer['files'])and consumer['trees']==e['source_consumer_trees'],'consumer census and roots')
 for relative,row in consumer['trees'].items():require(git('rev-parse',cfg['source_commit']+':swdb-project/'+relative).decode().strip()==row['oid'],'selected consumer tree '+relative)
 paths=set()
 for relative in consumer['trees']:
  q=project/relative
  for p in ([q]if q.is_file()else q.rglob('*')):
   require(not p.is_symlink()and(p.is_file()or p.is_dir()),'regular source consumer')
   if p.is_file():paths.add(str(p.relative_to(project)))
 require(paths=={r['relative']for r in consumer['files']},'complete physical consumer membership')
 for row in consumer['files']:
  got=physical(row['path'],row['sha256']);require(got['bytes']==row['bytes'],'source consumer size')
 oids=git('hash-object','--no-filters','--stdin-paths',input=''.join(r['path']+'\n'for r in consumer['files']).encode()).decode().splitlines()
 require(oids==[r['git_blob']for r in consumer['files']],'physical consumer Git blob equality')
 runtime_pins=[]
 for row in [*e['tools'].values(),*e['wp_artifacts'],e['why3_config']]:runtime_pins.append(physical(row['path'],row['sha256']))
 prefix=Path(e['linux_prefix'])
 for key,root in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:
  actual=[]
  for p in sorted(root.rglob('*')):
   require(not p.is_symlink(),'regular installed import surface')
   if p.is_file():got=physical(p);runtime_pins.append(got);actual.append({'relative':str(p.relative_to(root)),'sha256':got['sha256']})
  require(actual==e['portable_import_surfaces'][key],'complete installed import surface '+key)
 for row in e['typed_machine_sources']:runtime_pins.append(physical(prefix/'lib/frama-c-wp/core'/row['name'],row['sha256']))
 for key in ['command_executable','driver']:physical(e['linux_clang_components'][key]['path'],e['linux_clang_components'][key]['sha256'])
 compiler_root=Path(e['linux_clang_components']['driver']['path']).parent.parent
 physical((compiler_root/'lib/libclang.so').resolve(),e['linux_clang_components']['parser']['sha256'])
 header_digest=hashlib.sha256();header_count=0
 for label,root in [('libc++',compiler_root/'include/c++/v1'),('clang-resource',compiler_root/'lib/clang/22/include')]:
  for p in sorted(root.rglob('*')):
   if p.is_file():
    got=physical(p);header_digest.update(label.encode()+b'\0'+str(p.relative_to(root)).encode()+b'\0');header_digest.update(bytes.fromhex(got['sha256']));header_count+=1
 require(e['linux_clang_components']['headers']=={'id':'llvm-standard-resource-headers','sha256':header_digest.hexdigest(),'files':header_count},'complete selected compiler headers')

 attribution=cfg['project_map_lambda_attribution'];source_row=attribution['source'];data=Path(source_row['path']).read_bytes()
 require(H(data)==source_row['sha256']and H(data[source_row['begin']:source_row['end']])==source_row['span_sha256'],'exact source project_int_region lambda attribution')
 expected_lambda=smt_forms('(forall ((h heap) (values (Array Int Int)) (b Int) (offset Int) (count Int) (p Int)) (= (select (fc h values b offset count) p) (ite (int_slot offset count p) (Integer (select values p)) (select (select (memory h) b) p))))')[0]
 require(digest(expected_lambda)==attribution['support_assertion_body_sha256'],'source-derived full lifted-map lambda AST')
 canonical=J(profile/'canonical-inputs/manifest.json');physical(profile/'canonical-inputs/manifest.json',e['canonical_manifest_sha256'])
 require(len(canonical['obligations'])==61 and [r['id']for r in canonical['obligations']]==e['target_ids'],'all61 canonical target order')
 require(canonical['logical_obligations']==e['logical_obligations']and canonical['typed_source_image']==e['typed_source_image']and canonical['model']==e['model'],'logical and typed canonical identities')
 require(canonical['caller_premises_added']==[]and canonical['preparation_only']is True and canonical['coverage_complete']is False,'canonical limitations unchanged')
 found={str(p.relative_to(profile/'canonical-inputs'))for p in (profile/'canonical-inputs').rglob('*')if p.is_file()}
 require(found=={r['path']for r in e['canonical_files']}|{'manifest.json'},'complete70 canonical physical membership')
 for row in e['canonical_files']:
  got=physical(profile/'canonical-inputs'/row['path'],row['sha256']);require(got['bytes']==row['bytes'],'canonical size')
 for target in canonical['obligations']:
  require(target['status']=='pending'and target['expected']=='proven'and target['dependencies']==[],'no prior/sibling result premise')
  for span in target['source_spans']:
   data=(profile/'canonical-inputs/qualified.c').read_bytes();require(H(data[span['begin']:span['end']])==span['sha256'],'target source span')
 result=J(profile/'result.json');public=J(profile/'public.stdout');record_path=(profile/'workspace/records'/public['path']).resolve()
 require(record_path.is_relative_to(profile/'workspace/records'),'public persisted path contained')
 physical(record_path,result['record']['sha256']);record=yaml.safe_load(record_path.read_bytes());require(record==public['record'],'persisted/public record exact equality')
 settings,view=scope_record(record,e)
 require(view['obligations']==canonical['obligations']and view['logical_obligations']==canonical['logical_obligations']and view['source_inventory']==canonical['source_inventory']and view['semantics']==canonical['semantics'],'public complete source/model view')
 checkers=checkers_identity(project)
 require(record['proof_setup_check']['check']==checkers['proof_setup_check']and record['verdict_reading']=={'check':checkers['verdict_reading'],'verdict':'proven'},'independent current checker/reader identities')
 require(record['proof_setup_check']['verdict']=='passed'and len(record['proof_setup_check']['runs'])==61,'complete current setup runs')
 for name,h in cfg['schema_hashes'].items():physical(project/'schemas'/(name+'.schema.json'),h);require(J(project/'schemas'/(name+'.schema.json'))==cfg['schema_inputs'][name],'frozen schema equality')
 vocabs={}
 for name,row in cfg['vocab_inputs'].items():
  q=project/'vocab'/(name+'.yaml');physical(q,row['sha256']);require(re.findall(r'^  - value: ([A-Za-z0-9_.-]+)\s*$',q.read_text(),re.M)==row['values'],'frozen vocabulary');vocabs[name]=row['values']
 schema_validate(record,schema_expand(schema_merge(cfg['schema_inputs']['envelope'],cfg['schema_inputs']['proof']),vocabs))
 runtime=J(profile/'heap-project-runtime-provenance.json')
 require(settings['compiler_runtime']==runtime['runtime']==e['linux_project_identity_derivation']['runtime'],'actual current compiler context')
 require(runtime['lowering_identity']==e['linux_project_identity_derivation']['predicted_identity']and source_identity(project,runtime['runtime'])['sha256']==runtime['lowering_identity']['c_lowering']['sha256'],'independently reconstructed lowerer digest')
 method_path=profile/'workspace/library/methods/wp-qualified-grow61-v1.yaml';method=yaml.safe_load(method_path.read_bytes());base=yaml.safe_load((method_path.parent/'wp-tracer-fixture.yaml').read_bytes());restored=copy.deepcopy(method)
 for key in ['id','sequence','description']:restored[key]=base[key]
 require(restored==base and method['id']==e['method_id']and method['sequence']==3,'method portfolio unchanged')
 require(record['pins']['method_version']=={'id':e['method_id'],'sha256':sha(method_path)}and record['proof_setup_check']['method_version']==record['pins']['method_version'],'actual method normal pin')
 require(record['pins']['code']==record['pins']['contract']=={'id':e['member'],'sha256':canonical['sources']['qualified.c']['sha256']}and record['pins']['summaries']==[],'qualified code/contract and empty summaries')
 require(settings['why3_config']==e['why3_config']and settings['vector_reallocation_typed_runtime']['heap_model']=='Typed'and settings['vector_reallocation_typed_runtime']['integer_model']=='Machine','Typed/Machine actual binding')
 foundation=settings['heap_model_foundations']
 require(foundation['why3_loadpath']==[str(prefix/'share/why3/stdlib')]and foundation['ocaml_package_paths']=={'wp_core':str(prefix/'lib/frama-c-wp/core'),'why3':str(prefix/'lib/why3')},'actual foundation package context')
 for row in foundation['sources']+settings['vector_reallocation_typed_runtime']['sources']:physical(row['path'],row['sha256'])
 physical(foundation['metadata_executable'],foundation['metadata_executable_sha256'])
 wp=Path(settings['heap_model_runs'][0]['cwd']).parent
 physical(wp/'heap-reader/proof_report.ml',sha(project/'swdb/proof_report.ml'))
 ledger=[];tasks=[];logs=[];roots=set();support=Counter();unknown_support={};offset=0
 for index,(run,target)in enumerate(zip(settings['heap_model_runs'],canonical['obligations'],strict=True)):
  ident=target['id'];directory=Path(run['cwd']);require(run['id']==ident and directory.is_relative_to(profile/'workspace/runs-outside-repo'),'run source owner '+ident)
  physical(directory/'wp_input.c',target['sha256']);require(run['input_sha256']==target['sha256'],'actual source input '+ident)
  inventory=J(directory/'wp-inventory.json');ordinary=J(directory/'wp-goals.json');native=inventory_metadata(inventory,target)
  require(inventory['complete']is True and inventory['version']=='1'and not native['extern_properties'],'complete no-Extern inventory '+ident)
  closure=inventory['property_closure'];require(closure['exported_count']==closure['registered_snapshot_count']==len(inventory['properties'])and not closure['unregistered_status_lookup_performed'],'complete property registry '+ident)
  require(all(p['status_registered']is True and p['property_export_origin']=='registered'and not p['generated_smoke_failure']for p in inventory['properties']),'registered properties '+ident)
  n=len(inventory['goals']);recon=reconcile_leaf(ordinary,inventory,record['goals'][offset:offset+n],target);offset+=n
  csvrows=properties_csv((directory/'wp-properties.csv').read_text())
  for row in csvrows:
   if row['status']not in {'Valid','Considered valid'}:require(row['status']=='Ignored'and row['property kind']=='precondition'and any(p['function']==row['function']and str(p['line'])==row['line']and str(p['description']).startswith('requires')for p in inventory['properties']),'explained CSV status '+ident)
  resources=J(directory/'resources.json');require(resources==run['resources']and resources['exit_code']==0 and not resources['out_of_memory']and not resources['timed_out'],'healthy leaf resources '+ident)
  setup=record['proof_setup_check']['runs'][index];require(setup['verdict']=='passed'and setup['hashes']['wp_input.c']==target['sha256']and setup['hashes']['heap_model_view']==record['pins']['heap_model_view_certificate']['sha256'],'setup certificate/source '+ident)
  require(run['reading']=={'check':checkers['verdict_reading'],'verdict':'proven'},'current per-leaf reading '+ident)
  command=run['command']
  for flag,value in [('-wp-cache','none'),('-wp-model','+real'),('-wp-prover','alt-ergo,z3,cvc5'),('-wp-timeout','30')]:require([command[j+1]for j,t in enumerate(command[:-1])if t==flag]==[value],'normal mandatory option '+flag)
  require(all(t in command for t in ['-wp-rte','-rte-initialized','@all','-wp-no-filter-init','-wp-smoke-tests','-wp-status-all'])and not any(t in command for t in ['-wp-fct','-wp-prop','-wp-gen']),'no proof filtering or missing checks')
  log=(directory/'frama-c.log').read_text();blocks=printed_blocks(log)
  direct=set(re.findall(r'\(\* use ([\w.]+) \*\)',log))|set(re.findall(r'\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)',log));roots.update(direct)
  qed_only=not blocks
  if qed_only:
   require(target['kind']=='check_lemma'and len(ordinary)==1 and ordinary[0]['verdict']=='valid'and any(p.get('prover')=='qed'and p.get('success')for p in ordinary[0]['provers'])and 'Prover Qed returns Valid'in log,'unprinted task requires direct native Qed '+ident)
  for block in blocks:require(not any(d['kind']in {'axiom','lemma','val'}for d in block['declarations']),'no desired theorem added to printed task '+ident)
  leaf_tasks=sorted(directory.rglob('*.psmt2'))+sorted(directory.rglob('*.smt2'))
  if qed_only:require(not leaf_tasks,'Qed-only source duty has no solver-materialized query '+ident)
  for task in leaf_tasks:
   actual=safe_smt(task.read_text());require(len(actual['check_sat_indices'])==1 and actual['last_assertion_is_negation'],'retained negated query '+ident)
   last=max(a['index']for a in actual['assertions']if a['index']<actual['check_sat_indices'][0]);families=Counter()
   for assertion in actual['assertions']:
    if assertion['index']==last:continue
    h=assertion['body_sha256']
    if h not in cfg['support_assertion_hashes']:unknown_support[h]={'first_task':str(task),'symbols':assertion['symbol_references'],'instances':unknown_support.get(h,{}).get('instances',0)+1}
    else:families[cfg['support_assertion_hashes'][h]['family']]+=1
   require(check_task_context(actual,cfg['support_assertion_hashes'])==families,'complete command/query/support context '+ident)
   support.update(families)
   require(not any('check_lemma_'in json.dumps(a)for a in actual['assertions'][:-1]),'no sibling theorem support '+ident)
   tasks.append({'id':ident,**pin(task),'assertions':len(actual['assertions']),'nongGoal_family_instances':dict(families),'last_goal_hash':actual['last_assertion_canonical_sexpr_sha256'],'materialized_only':True})
  logs.append({'id':ident,**pin(directory/'frama-c.log'),'qed_only_no_external_query':qed_only,'printed_queries':sum(len(b['queries'])for b in blocks),'direct_imports':sorted(direct),'printed_contexts':[{'sha256':b['sha256_utf8_lines'],'declaration_kinds':b['declaration_kind_counts'],'queries':b['queries']}for b in blocks]})
  ledger.append({'id':ident,'kind':target['kind'],'reconciliation':recon,'properties':native['property_count'],'DAG_edges':native['dependency_edges'],'CSV_rows':len(csvrows),'ordinary_report':pin(directory/'wp-goals.json'),'inventory':pin(directory/'wp-inventory.json'),'properties_csv':pin(directory/'wp-properties.csv')})
 require(offset==len(record['goals']),'complete aggregate goals consumed')
 signature=lambda g:json.dumps({k:g.get('normalized_status')if k=='status'and'normalized_status'in g else g.get(k)for k in ['goal','property','function','smoke','status']},sort_keys=True)
 require(Counter(signature(g)for r in ledger for g in r['reconciliation']['goals'])==Counter(map(signature,record['goals'])),'complete aggregate goal multiset including multiplicity')
 derived=J(profile/'derived-native-census.json')
 for actual,row in zip(ledger,derived['runs'],strict=True):
  require(row['id']==actual['id']and row['ordinary_goals']==actual['reconciliation']['normalized_ordinary']and row['smoke_goals']==actual['reconciliation']['normalized_smoke']and row['native_properties']==actual['properties'],'producer derived per-leaf census')
  for k in ['inventory','ordinary_report','properties_csv']:require(row[k]==actual[k],'producer derived actual report pin')
 ordinary_count=sum(r['reconciliation']['normalized_ordinary']for r in ledger);smoke_count=sum(r['reconciliation']['normalized_smoke']for r in ledger)
 require(ordinary_count==71 and smoke_count==1 and derived['total_ordinary']==ordinary_count and derived['total_smoke']==smoke_count and result['public_complete']and result['targets']==61 and result['ordinary_goals']==71 and result['smoke_goals']==1,'complete actual61 census')
 require(all(result[k]is False for k in ['model_proof_acceptance','original_v2_acceptance','caller_acceptance']),'larger acceptance flags not producer-granted')
 import_closure=imported_context(roots,prefix/'share/why3/stdlib',prefix/'share/frama-c/share/wp/why3',profile/'canonical-inputs/theory/heap_reallocation.mlw',sha)
 require(import_closure['heap_reallocation.Heap']['proposition_declarations']==[],'project Heap definitions only')
 for row in J(profile/'artifact-manifest.json'):physical(row['path'],row['sha256'])
 require({str(p)for p in raw.rglob('*')if p.is_file()and p.suffix in {'.smt2','.psmt2'}}=={t['path']for t in tasks},'all raw materialized task membership reconciled')
 require(whole(raw)==before,'complete raw pre/post physical hash identity')
 return {'created':'2026-10-16 ET','classification':'GROW61_PASSIVE_COLD_RECONCILIATION_CAPTURE','checks':CHECK_COUNT,'wall_seconds':time.monotonic()-started,'source_commit':cfg['source_commit'],'raw_root':str(raw),'raw_files':len(before),'raw_bytes':sum(r['bytes']for r in before.values()),'raw_manifest':before,'raw_pre_post_equal':True,'reviewed_entry':pin(profile/'entry.py'),'reviewed_expected':pin(profile/'expected.json'),'public_record':pin(record_path),'record_scope':{'subject':record['subject'],'status':record['status'],'evidence_kind':record['evidence_kind'],'bounds':record['bounds'],'assumptions':record['assumptions']},'current_checker_identities':checkers,'schema_record_validated':True,'source_consumers':{'files':consumer['count'],'bytes':consumer['total_bytes'],'identical_receipts':3,'physical_membership_sha256_and_Git_blob_equality':True},'compiler_headers':header_count,'runtime_pins':runtime_pins,'guard':guards,'lane':lane,'census':{'targets':len(ledger),'math_targets':sum(r['kind']=='check_lemma'for r in ledger),'numeric_targets':sum(r['kind']=='c_kernel'for r in ledger),'ordinary':ordinary_count,'smoke':smoke_count,'direct_native_valid':sum(g['provenance']=='direct_native_valid'for r in ledger for g in r['reconciliation']['goals']),'inventory_only_ordinary':sum(r['reconciliation']['inventory_only_ordinary']for r in ledger),'raw_native_verdicts':dict(sum((Counter(r['reconciliation']['native_report_verdicts'])for r in ledger),Counter()))},'leaves':ledger,'logs':logs,'materialized_tasks':tasks,'support_primary_family_instances':dict(support),'unknown_support_assertion_hashes':unknown_support,'full_import_closure':import_closure,'actual_submission_count':None,'submitted_byte_identity_attested':False,'typed_AST_translation_equivalence_proved':False,'compiler_WP_Why3_solver_and_foundation_TCB_explicit':True,'no_prior_or_sibling_proof_premises':True,'sourceafter_clean':True,'no_original_v2_default_catalog_Cpp_caller_or_ticket_acceptance':True,'scoped_decision_pending_primary_support_reconciliation':bool(unknown_support)}


if __name__=='__main__':
 try:
  if not __debug__:raise ValueError('nonoptimized auditor required')
  result=main(CFG)
  print(json.dumps(result,sort_keys=True,indent=2))
 except Exception as error:
  print(json.dumps({'classification':'REFUSED_PASSIVE_GROW61_AUDIT','error_type':type(error).__name__,'error':str(error),'checks':CHECK_COUNT,'acceptance':False}))
  raise SystemExit(1)
