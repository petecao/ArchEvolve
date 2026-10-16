"""Read/hash/pure-reader audit of the retained actual017 generation, 2026-10-16 ET.

No executable tool probes, package imports, formal jobs, original result rewrite
or solver/model-body acceptance. Every derived output uses a new exclusive path.
"""
from pathlib import Path
import hashlib,importlib.util,json,re
R=Path('/private/tmp/probata-t25-mac-qualified-generation-v1-01771a83-20261016')
C=R/'component'
OUT=Path('/private/tmp/probata-t25-qualified-generation-passive-audit-v3-01771a83-20261016');OUT.mkdir(exist_ok=False)
entry_path=Path('/private/tmp/probata-t25-qualified-generation-entry-v4-01771a83-20261016.py')
spec=importlib.util.spec_from_file_location('passive_reader',entry_path);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
checks=[];physical={};errors=[]
def sha(data):return hashlib.sha256(data).hexdigest()
def pin(p):
 p=Path(p);row={'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size};physical[str(p)]=row;return row

def require(ok,name):
 checks.append({'check':name,'passed':bool(ok)})
 if not ok:errors.append(name)

def write(path,value):
 with path.open('x') as f:f.write(json.dumps(value,sort_keys=True,indent=2)+'\n')

def strip_comments(text):
 out=list(text);i=0;depth=0
 while i<len(text):
  if depth:
   if text[i:i+2]=='(*' and text[i:i+3]!='(*)':depth+=1;out[i:i+2]=[' ',' '];i+=2
   elif text[i:i+2]=='*)':depth-=1;out[i:i+2]=[' ',' '];i+=2
   else:
    if text[i]!='\n':out[i]=' '
    i+=1
  elif text[i:i+2]=='(*' and text[i:i+3]!='(*)':depth=1;out[i:i+2]=[' ',' '];i+=2
  else:i+=1
 if depth:raise ValueError('unterminated nested Why3 source comment')
 return ''.join(out)

expected=json.loads((C/'expected.json').read_bytes());old=json.loads((C/'result.json').read_bytes())
selected=expected['selected'];runtime=expected['runtime'];inventory=json.loads((C/'lemma/wp-inventory.json').read_bytes())
log=(C/'frama-generation.log').read_text();guard=json.loads((R/'guard.log.summary.json').read_bytes())
require(sha((C/'entry.py').read_bytes())=='ce792616c5b5cba4ce84e0f385251155211609b86547b9bb1420eae38e9417fc','executed exactv3 entry unchanged')
require(pin(C/'expected.json')['sha256']=='866a8a3900722d86ae390e7f0e91cdb6e6b9d02524303e51777f7bc9008e7493','admitted expected recipe unchanged')
require(old['generation_completed'] is False and old['error']=='missing or duplicate inventory identities' and old['proof_acceptance'] is False,'original reader RED preserved')
require(guard['exit_code']==1 and guard['wall_s']<=600 and guard['peak_rss_mb']<8192 and not guard['killed_by_watchdog'] and not guard['timed_out'] and not guard['inspection_events'] and not guard['unconfirmed_children'] and guard['inspection_failure'] is None,'actual guard healthy expected reader failure and cleanup')
require(old['source_commit']==expected['source_commit']=='01771a839893975bba389ee0adcbec2aecdb88ac','exact017 source')
require(old['published_tip']=='2bf4a386423a3a427871fe10d15f8c1a6b6e1e29','retained actual publication ancestry receipt')
# Recheck every physical output admitted by the executed entry's own manifest,
# then exact recursive membership including files omitted only by root role.
manifest=json.loads((C/'artifact-manifest.json').read_bytes())
for row in manifest:require(pin(C/row['relative'])['sha256']==row['sha256'] and (C/row['relative']).stat().st_size==row['bytes'],'producer output '+row['relative'])
require({str(p.relative_to(C)) for p in C.rglob('*') if p.is_file()}=={r['relative'] for r in manifest}|{'result.json','artifact-manifest.json'},'all producer physical output membership exact')
for row in expected['source_blobs']:require(pin(C/'source'/row['relative'])['sha256']==row['sha256'],'staged exact017 source '+row['relative'])
require({str(p.relative_to(C/'source')) for p in (C/'source').rglob('*') if p.is_file()}=={r['relative']for r in expected['source_blobs']},'full310 staged source closure')
inputs=C/'inputs';canonical=json.loads((inputs/'manifest.json').read_bytes())
require(pin(inputs/'manifest.json')['sha256']==expected['manifest_sha256'] and len(canonical['obligations'])==20,'exact canonical20 packet manifest')
require([r for r in canonical['obligations'] if r['id']==selected['id']]==[selected],'selected exact independent projection target')
for row in canonical['obligations']:require(pin(inputs/row['path'])['sha256']==row['sha256'] and row['dependencies']==[],'independent canonical target '+row['id'])
require(pin(C/'lemma/wp_input.c')['sha256']==selected['sha256']==expected['selected_packet_sha256'],'actual selected input source binding')
require(pin(inputs/'theory/heap_reallocation.mlw')['sha256']==expected['theory_sha256'],'exact selected heap semantics')
reader.verify_runtime(runtime);checks.append({'check':'all selected physical runtime pins and exact import/package/native memberships rechecked without tool execution','passed':True})
for key in ('why3_stdlib','wp_why3_support','why3_drivers'):
 for row in runtime[key]['files']:pin(row['path'])
for tree in runtime['package_surfaces']:
 for row in tree['files']:pin(row['path'])
for row in [*runtime['tools'].values(),runtime['python'],*runtime['toolchain_artifacts'],*runtime['configuration_files'],*runtime['native_closure'],*runtime['primary_sources']]:pin(row['path'])
require(old['package_bindings']==runtime['package_bindings'],'actual OCaml query paths matched selected pinned packages')
require(pin(C/'proof_report.ml')['sha256']==pin(C/'source/swdb/proof_report.ml')['sha256'],'fresh native inventory reader source exact017')
for key,name in [('fresh_config','why3.conf'),('sentinel','prover-sentinel.py')]:require(pin(C/name)['sha256']==expected[key]['sha256'],'exact actual '+name)
require(not (C/'FORBIDDEN-PROVER-INVOKED.json').exists() and old['sentinel_invoked'] is False,'forbidden solver sentinel never observed')
require('-wp-gen'in old['command'] and '-wp-no-why3-detect'in old['command'] and old['command'][old['command'].index('-wp-prover')+1]=='cvc5' and '-wp-prop'not in old['command'],'generation-only exact selector and complete property selection')
require(all(flag in old['command']for flag in ['-wp-rte','-rte-initialized','@all','-wp-no-filter-init','-wp-smoke-tests','-wp-cache','none','-wp-status-all']), 'mandatory RTE/init/cache/smoke/status flags retained')
census=reader.generation_inventory(inventory,log,selected);write(OUT/'generation-census.json',census)
require(len(census['goals'])==1 and len(census['properties'])==2 and census['goals'][0]['results']==[] and census['goals'][0]['passed'] is False,'one actual ordinary generated no-result goal and both properties retained')
require((C/'lemma/wp-properties.csv').read_text().strip()=='directory\tfile\tline\tfunction\tproperty kind\tstatus\tproperty','actual untried property CSV header only; not proof evidence')
native=json.loads((C/'lemma/wp-native-goals.json').read_bytes())
require(len(native)==1 and native[0]['goal']==census['goals'][0]['goal'] and native[0]['verdict']=='none' and native[0]['passed'] is False and native[0]['smoke'] is False and all(p['success']==0 for p in native[0]['provers']),'native generation report records none, not solver Valid')
# Full emitted Why3 theory/task, not a prewritten packet substitution.
match=re.search(r'\[wp:print-generated\]\s*\n(  theory WP\n.*?\n  end)\n\[wp\]',log,re.S)
require(match is not None,'actual complete printed Why3 task framing')
task=match.group(1);(OUT/'emitted-task.mlw.txt').write_text(task+'\n')
code=strip_comments(task)
require(re.findall(r'^    (predicate|goal)\s+(\w+)',code,re.M)==[('predicate','P_t25_fields'),('predicate','P_t25_repr'),('predicate','P_t25v3_repr'),('goal','wp_goal')],'only three exact source predicate definitions and the generated goal')
require(not re.search(r'^\s*(?:axiom|lemma|constant|val)\b',code,re.M),'no explicit current/future project lemma or desired-result axiom in emitted task')
actual_goal=' '.join(code.split('goal wp_goal :',1)[1].rsplit('end',1)[0].split())
expected_goal=('forall i:int, i1:int, i2:int, heap:heap, i3:int, i4:int, i5:int, t:int -> int. '
 'bounded_int_values t i1 i5 -> P_t25_repr heap i4 i3 i i1 i5 i2 -> '
 r'i5 = 0 \/ not i4 = i -> P_t25v3_repr (project_int_region heap t i i1 i5) i4 i3 i i1 i5 i2')
require(actual_goal==expected_goal,'independent source-variable mapping to the exact functional int_values task formula')
heap=strip_comments((inputs/'theory/heap_reallocation.mlw').read_text())
require(not re.search(r'^\s*(?:axiom|lemma|goal)\b',heap,re.M),'project imported heap has only uniform definitions, no desired propositions')
require('type int_values = map int int' in heap,'source functional-map type alias explicit')
require('heap_reallocation::Heap::int_values' in log and 't:int ->\n       int.' in task,'actual importer resolved alias to unbounded functional integer map')
normalized=(C/'lemma/normalized.c').read_text()
banner='/* Generated by Frama-C */'
parts=normalized.split(banner)
require(not parts[0].strip() and len(parts)==4,'all three normalized snapshots from the three-stage command retained')
for i,part in enumerate(parts[1:],1):
 require(re.findall(r'\bcheck\s+lemma\s+(\w+)',part)==[selected['goal']] and
         re.findall(r'\blemma\s+(\w+)',part)==[selected['goal']],
         'normalized snapshot '+str(i)+' has only the exact original source check lemma')
require(len({p.strip() for p in parts[1:]})==1,'three complete normalized snapshot bodies are identical')
write(OUT/'normalized-snapshot-census.json',[{'snapshot':i,'sha256':sha((banner+part).encode()),
      'selected_check_lemma':selected['goal']}for i,part in enumerate(parts[1:],1)])

# Source-context special case: actual selected import only, never arbitrary empty IDs.
require((C/'lemma/wp_input.c').read_text().splitlines()[0]=='//@ import \\wp::why3: heap_reallocation::Heap;','exact source import owns unnamed IPModule metadata')
primary=Path('/Users/yanrujhou/.opam/framac-33/lib/frama-c/kernel/kernel_services/ast_data/property.ml')
pt=primary.read_text();pin(primary)
require('| IPModule _ -> []'in pt and '| IPAxiomatic _ | IPModule _ -> []'in pt and 'Format.fprintf fmt "module@ %s" im_name'in pt,'selected kernel source explains empty module identity and multiline pretty description')
# Conservative transitive source inventory of all actually configured/printed
# imports. Clone bodies/substitutions are retained; this is not a flattened list
# of instantiated Why3 Task axioms and does not certify standard-library lemmas.
roots=set(re.findall(r'\(\* use ([\w.]+) \*\)',task))
roots.update(re.findall(r'\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)',log))
std=Path(runtime['why3_stdlib']['path']);wp=Path(runtime['wp_why3_support']['path'])
closure={};visiting=set()
def module_source(name):
 if name=='why3.BuiltIn.BuiltIn':return None
 if name=='heap_reallocation.Heap':return inputs/'theory/heap_reallocation.mlw'
 file=name.rsplit('.',1)[0].replace('.','/')+'.mlw'
 candidates=[std/file,wp/file]
 found=[p for p in candidates if p.is_file()]
 if len(found)!=1:raise ValueError('unresolved or shadowed imported module '+name)
 return found[0]
def visit(name):
 if name in closure:return
 if name in visiting:raise ValueError('source import cycle '+name)
 visiting.add(name);p=module_source(name)
 if p is None:
  closure[name]={'scope':'Why3 intrinsic typed core; selected compiled package trust, not project desired propositions'}
 else:
  text=strip_comments(p.read_text());module=name.rsplit('.',1)[1]
  found=list(re.finditer(r'^(?:module|theory) '+re.escape(module)+r'\b[^\n]*\n(.*?)^end\s*$',text,re.M|re.S))
  if len(found)!=1:raise ValueError('module source boundary ambiguous '+name)
  body=found[0].group(1);deps=[]
  for edge in re.finditer(r'^\s*(use|clone)\s+(?:(?:import|export)\s+)?([A-Za-z_]\w*(?:\.\w+)*)\b',body,re.M):
   kind,target=edge.groups();full=target if '.'in target else name.rsplit('.',1)[0]+'.'+target
   deps.append({'kind':kind,'target':full,'source_line':text.count('\n',0,found[0].start(1)+edge.start())+1})
   visit(full)
  decls=[{'kind':m.group(1),'name':m.group(2),'line':text.count('\n',0,found[0].start(1)+m.start())+1}
         for m in re.finditer(r'^\s*(axiom|lemma|goal)\s+(\w+)',body,re.M)]
  closure[name]={'source':pin(p),'module_body_sha256':sha(body.encode()),'dependencies':deps,'proposition_declarations':decls,
                 'classification':'uniform project definitions'if name=='heap_reallocation.Heap'else 'selected standard arithmetic/maps/Qed trusted foundation',
                 'complete_module_text':body}
 visiting.remove(name)
for name in sorted(roots):visit(name)
write(OUT/'import-source-closure.json',{'direct_configured_or_emitted_roots':sorted(roots),'modules':closure,
 'boundary':'Transitive source declaration/clone inventory; clone substitutions retained in complete module text. No solver proof or flattened instantiated-task-axiom claim. All project current/future desired lemmas absent.'})
warnings=[line for line in log.splitlines()if re.search(r'\bwarning\b',line,re.I)]
want='Warning, file "'+str(inputs/'theory/heap_reallocation.mlw')+'", line 25, characters 18-23: unused variable dummy'
require(warnings==[want,want],'two exact known unused-dummy warnings, import and task compilation; no unclassified Warning forms')
write(OUT/'warnings.json',{'all':warnings,'count':2,'classification':'same dead dummy formal; no unsupported/type/init warning waived','contexts':'complete producer log retained'})
# Bind every retained producer physical file and all selected runtime/cold inputs.
for p in sorted(C.rglob('*')):
 if p.is_file():pin(p)
for p in [R/'guard.log.summary.json',R/'guard.log.wait.json',entry_path,Path(__file__)]:pin(p)
result={'created':'2026-10-16 ET','status':'PASS generation/import feasibility only'if not errors else 'FAIL passive closure',
 'errors':errors,'checks':checks,'source_commit':expected['source_commit'],'original_entry_exit':1,
 'original_reader_failure_preserved':True,'actual_wp_generation_succeeded':not errors,
 'solver_invoked':False,'scientific_verdict':'not_proven','model_body_or_caller_acceptance':False,'original_v2_acceptance':False,
 'actual_goals':1,'actual_properties':2,'ordinary_no_result':1,'smoke_generated':0,
 'import_source_modules':len(closure),'task_hypothesis_boundary':'project heap0desiredaxioms/lemmas; printedtask3sourcepredicate definitions+oneunprovedgoal; selected standardfoundation declarations explicitly inventoried',
 'variable_binding':{'h':'heap','values':'t:int -> int','r':'i4','o':'i3','b':'i','bo':'i1','s':'i5','c':'i2'},
 'physical_pins':list(physical.values()),'guard':guard,
 'runtime_scope':'Full57 stdlib,30 WP support,93 drivers and pinned selected compiled/native surfaces; OS dyld shared-cache remains trusted host boundary.',
 'no_rerun':True,'reader_successor':pin(entry_path),'produced':[pin(p)for p in sorted(OUT.iterdir())if p.is_file()]}
write(OUT/'audit.json',result)
print(json.dumps({'status':result['status'],'errors':errors,'checks':len(checks),'physical_files':len(physical),'modules':len(closure),'audit':pin(OUT/'audit.json')}))
raise SystemExit(bool(errors))
