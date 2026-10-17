"""2026-10-16 ET. INERT initialized-u32 passive goal/CSV closure obligations.

Copied reviewed generic reader primitives are explicitly source-derived. This is
an evidence reader, not a verifier or a source/model correspondence theorem.
No project imports, compiler discovery, process launch, or main entry point.
Raw/source/runtime/guard closure must be checked separately before acceptance.
The original closed CSV expectations intentionally refuse new property classes
until exact native evidence and primary reporter source justify an adaptation.
"""
from pathlib import Path
from collections import Counter
import csv
import io
import math
import json
import re
import hashlib

HELPERS = {"init_MAA", "get_new_reg_unsigned_int_args1", "get_reg_unsigned_int"}


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

def current_csv_active_v2(rows,props,generated,failed):
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
   assert desc.startswith('assert rte: initialization: ') and desc.endswith(';') and name in {'trust_fixture_assert_rte_initialization','trust_fixture_assert_rte_initialization_2'}
   expected[name]=('initialization',desc[len('assert rte: initialization: '):-1])
  else:assert (name==fn and desc=='default behavior' and p['property_variant']=='IPBehavior') or (name in smokes and p['property_variant']=='IPOther' and desc in {'wp_smoke_dead_call','wp_smoke_dead_code'}),'unmapped property omitted from CSV'
 matched={};implicit=[];extern=[];column_groups={}
 for row in rows:
  assert row['directory']=='.' and row['file']=='wp_input.c'
  candidates=[name for name,(kind,payload) in expected.items() if props[name]['function']==row['function'] and str(props[name]['line'])==str(row['line']) and kind==row['property kind'] and payload==norm(row['property'])]
  assert candidates,'CSV class/text/site not present in complete inventory'
  if len(candidates)>1:
   # Report.csv.ml:9-14,48-63 sorts with column but prints no column.
   # Only exact helper precondition instances in this closed caller may share
   # a displayed row. Preserve their inventory/goal IDs and row multiplicity;
   # never infer an individual CSV-row identity that the format omits.
   group=[props[name]for name in candidates]
   assert len(group)==2 and row['function']=='trust_fixture'and row['status']=='Valid'
   assert all(q['property_variant']=='IPPropertyInstance'and q['origin']and q['function']=='trust_fixture'for q in group)
   assert len({q['origin']for q in group})==1 and len({q['source_file']for q in group})==1
   assert len({q['call_context']['statement_id']for q in group})==len(group)
   assert all(q['call_context']['callee']==props[q['origin']]['function']in HELPERS and q['call_context']['caller']=='trust_fixture'for q in group)
   column_groups[tuple(sorted(candidates))]={'properties':sorted(candidates),'statement_ids':sorted(q['call_context']['statement_id']for q in group),'mapping':'CSV multiplicity only; distinct exact inventory/native callsite identities retained'}
  remaining=sorted(name for name in candidates if name not in matched);assert remaining,'extra duplicate CSV row'
  name=remaining[0];p=props[name];matched[name]=row;attached=[g for g in generated.values() if g['property']==name or name in g['targets']]
  if p['extern']:
   assert p['function'] in HELPERS and row['status']=='Considered valid' and not attached and p['origin'] is None and p['dependencies']==[]
   assert re.fullmatch(re.escape(p['function'])+r'_(assigns|ensures|terminates)(?:_[0-9]+)?',name)
   if name.endswith('_terminates'):assert expected[name][1]==r'\false'
   extern.append(name)
  elif p['function'] in HELPERS:
   if name.endswith('_exits'):
    assert row['status']=='Unknown' and expected[name][1]==r'\false' and attached==[] and p['dependencies']==[] and p['origin'] is None
    implicit.append(name)
   elif name=='init_MAA_terminates':
    assert row['status']=='Unknown' and expected[name][1]==r'\true' and attached==[] and p['dependencies']==[] and p['origin'] is None
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
 return {'CSV_rows':len(rows),'mapped_properties':len(matched),'implicit_helper_exits_unknown':implicit,'Extern_contract_properties':extern,'implicit_implementation_verified':False,'CSV_column_elision_groups':list(column_groups.values())}

def unused_arity0_v3(rows,props,generated,validated_query,expected_wp_input):
 """One canonical unused requires-false declaration, never an active helper."""
 assert validated_query['complete_ACSL_and_C_comparison'] is True and validated_query['unused_arity0_declaration_only'] is True
 assert validated_query['expected_result'] in {711,1107} and validated_query['reference_is_native_proof'] is False
 assert validated_query['reference_sha256']=={711:'a324f08bed8b8101fcff22461e408b440f2f227f0d4d4ac6f5dcbed1611bccdb',1107:'46244c04dd878c93606add23f68a68732a5fe550d3d6b7ca308fedd4312fe094'}[validated_query['expected_result']]
 fn='get_new_reg_unsigned_int_args0';ids={fn,fn+'_requires',fn+'_assigns'}
 subset={name:p for name,p in props.items() if p['function']==fn}
 assert set(subset)==ids
 common={'function':fn,'source_file':str(expected_wp_input),'emitter':'','origin':None,'call_context':None,'status_registered':True,'property_export_origin':'registered','generated_smoke_failure':False}
 expected={fn:{'kind':'other','property_variant':'IPBehavior','line':19,'extern':False,'description':'default behavior','dependencies':[fn+'_assigns']},fn+'_requires':{'kind':'contract','property_variant':'IPPredicate','line':17,'extern':False,'description':r'requires \false','dependencies':[]},fn+'_assigns':{'kind':'contract','property_variant':'IPAssigns','line':19,'extern':True,'description':r'assigns \nothing;','dependencies':[]}}
 for name,p in subset.items():
  want={'property':name,**common,**expected[name]};actual=dict(p,description=' '.join(p['description'].split()))
  assert actual==want,'unused requires-false overload property shape differs'
 assert not any(g['function']==fn or g['property'] in ids or set(g['targets'])&ids for g in generated.values()),'unused overload has a native goal or target'
 assert not any(p['origin'] in ids or set(p['dependencies'])&ids for name,p in props.items() if name not in ids),'unused overload has an active dependency or instance'
 ignored=[row for row in rows if row['function']==fn]
 wanted=[{'directory':'.','file':'wp_input.c','line':'17','function':fn,'property kind':'precondition','status':'Ignored','property':r'\false'},{'directory':'.','file':'wp_input.c','line':'19','function':fn,'property kind':'assigns clause','status':'Considered valid','property':r'assigns \nothing;'}]
 assert Counter(json.dumps(row,sort_keys=True)for row in ignored)==Counter(json.dumps(row,sort_keys=True)for row in wanted),'unused overload exact CSV classification differs'
 return {'function':fn,'property_ids':sorted(ids),'CSV_rows':ignored,'source_is_unused_requires_false_declaration':True,'active_helper':False,'native_goals':0,'precondition_proven':False,'implementation_proven':False}


def initialized_reads_v4(props,generated,validated_query,expected_wp_input):
 """Both source return operands keep distinct ordinary initialization goals."""
 assert validated_query['complete_ACSL_and_C_comparison'] is True
 number=validated_query['expected_result'];assert type(number) is int and number in {711,1107}
 assert validated_query['reference_sha256']=={711:'a324f08bed8b8101fcff22461e408b440f2f227f0d4d4ac6f5dcbed1611bccdb',1107:'46244c04dd878c93606add23f68a68732a5fe550d3d6b7ca308fedd4312fe094'}[number]
 assert validated_query['reference_is_native_proof'] is False
 first='trust_fixture_assert_rte_initialization';second=first+'_2'
 reads={first:('first',[]),second:('second',[first])}
 selected={name:p for name,p in props.items() if p['emitter']=='rte'}
 assert set(selected)==set(reads),'complete two-read source initialization census differs'
 for name,(local,dependencies) in reads.items():
  want={'property':name,'kind':'other','property_variant':'IPCodeAnnot','function':'trust_fixture',
   'source_file':str(expected_wp_input),'line':47,'extern':False,'emitter':'rte','origin':None,
   'call_context':None,'status_registered':True,'property_export_origin':'registered',
   'generated_smoke_failure':False,'description':'assert rte: initialization: '+r'\initialized(&'+local+');',
   'dependencies':dependencies}
  assert selected[name]==want,'source RTE read property/site/dependency differs'
  goals=[g for g in generated.values() if g['property']==name or name in g['targets']]
  assert goals==[{'goal':'typed_real_'+name,'property':name,'function':'trust_fixture','line':47,
   'passed':True,'smoke':False,'results':['valid'],'targets':[]}],'source RTE read lacks its unique direct Valid ordinary goal'
 return {'properties':list(reads),'source_locals':['first','second'],'source_line':47,
  'ordinary_direct_valid':2,'initialization_omitted_or_assumed':False}

def init_termination_v4(props,generated,validated_query,expected_wp_input):
 """Retain the sole registered unproved helper termination, never credit it."""
 assert validated_query['complete_ACSL_and_C_comparison'] is True and validated_query['reference_is_native_proof'] is False
 number=validated_query['expected_result'];assert type(number) is int and number in {711,1107}
 assert validated_query['reference_sha256']=={711:'a324f08bed8b8101fcff22461e408b440f2f227f0d4d4ac6f5dcbed1611bccdb',1107:'46244c04dd878c93606add23f68a68732a5fe550d3d6b7ca308fedd4312fe094'}[number]
 name='init_MAA_terminates'
 want={'property':name,'kind':'contract','property_variant':'IPPredicate','function':'init_MAA',
  'source_file':str(expected_wp_input),'line':27,'extern':False,'emitter':'','origin':None,
  'call_context':None,'status_registered':True,'property_export_origin':'registered',
  'generated_smoke_failure':False,'description':'terminates\n'+r'\true','dependencies':[]}
 assert props[name]==want,'implicit init termination property/site/status differs'
 assert not any(g['property']==name or name in g['targets'] for g in generated.values()),'unproved init termination acquired a native goal/target'
 assert not any(p['origin']==name or name in p['dependencies'] for key,p in props.items() if key!=name),'unproved init termination acquired an active dependency'
 return {'property':name,'CSV_status':'Unknown','native_goals':0,'Extern':False,
  'termination_proven':False,'partial_normal_return_scope_unchanged':True}

def current_csv(rows,props,generated,failed,*,validated_query,expected_wp_input):
 unused=unused_arity0_v3(rows,props,generated,validated_query,expected_wp_input)
 rte=initialized_reads_v4(props,generated,validated_query,expected_wp_input)
 termination=init_termination_v4(props,generated,validated_query,expected_wp_input)
 kept_rows=[row for row in rows if row['function']!=unused['function']]
 kept_props={name:p for name,p in props.items() if name not in unused['property_ids']}
 result=current_csv_active_v2(kept_rows,kept_props,generated,failed)
 assert result['CSV_rows']==len(kept_rows) and len(rows)==len(kept_rows)+2
 result['CSV_rows']=len(rows);result['unused_requires_false_overload']=unused
 result['source_initialization_reads']=rte
 result['unproved_init_termination']=termination
 return result

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

def current_goals(record,inventory,native,csvrows,expected_wp_input,*,validated_query):
 assert inventory['version']=='1' and inventory['complete'] is True
 closure=inventory['property_closure'];assert closure['registration_membership_refreshed_after_consolidation'] is True and closure['unregistered_status_lookup_performed'] is False and closure['unregistered_wp_smoke_properties']==closure['unregistered_wp_call_instances']==[]
 props=unique(inventory['properties'],'property')
 assert closure['initial_registered_snapshot_count']==closure['registered_snapshot_count']==closure['exported_count']==len(props)
 assert all(p['source_file']==str(expected_wp_input) for p in props.values()),'property source file differs from exact Frama scratch input'
 assert all(p['status_registered'] is True and p['property_export_origin']=='registered' and not p['generated_smoke_failure'] and set(p['dependencies'])<=set(props) and (p['origin'] is None or p['origin'] in props) for p in props.values())
 goals=unique(inventory['goals'],'goal');native=unique(native,'goal');saved=unique(record['goals'],'goal');assert set(goals)==set(native)==set(saved)
 unused=unused_arity0_v3(csvrows,props,goals,validated_query,expected_wp_input)
 extern=[p for p in props.values() if p['extern']];assert all(p['kind']=='contract' and (p['function'] in HELPERS or p['property']=='get_new_reg_unsigned_int_args0_assigns') for p in extern)
 sempin=record['pins']['proof_semantics'];assumed=[a for a in record['assumptions'] if a['kind']=='assumed_clause'];want=[{'kind':'assumed_clause','reference':sempin,'sentence':f"WP treats contract property {p['property']} of {p['function']} as Extern: {p['description'] or p['property']}."} for p in extern]
 assert Counter(json.dumps(x,sort_keys=True) for x in assumed)==Counter(json.dumps(x,sort_keys=True) for x in want),'uncertified/missing Extern assumption'
 failed=[];smokes=[];bridges=[]
 for name,g in goals.items():
  n=native[name];r=saved[name];p=props[g['property']]
  assert (g['function'],g['line'])==(p['function'],p['line']),'native inventory goal owner/site differs from its property'
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
  elif g['passed']:
   assert g['results']==['valid'] and n['verdict']=='valid' and r['status']=='valid','ordinary pass lacks direct Valid'
   assert winner is not None,'ordinary direct Valid lacks a successful native prover'
   assert type(n.get('proved'))is int and n['proved']==1,'ordinary direct Valid needs normalized proved=1'
   assert all(type(n.get(k,0))is int and n.get(k,0)==0 for k in ['failed','timeout','unknown','tactics','cached']),'ordinary Valid has contradictory normalized counters'
  else:
   assert name=='typed_real_trust_fixture_ensures' and g['property']=='trust_fixture_ensures' and g['function']=='trust_fixture' and set(g['results'])<={'timeout','unknown','stepout'} and n['verdict'] in {'timeout','unknown','stepout'} and r['solver'] is r['seconds'] is None
   failed.append(name)
 assert smokes and any(not g['smoke'] for g in goals.values())
 if record['verdict']=='proven':assert not failed and not record.get('failure_class') and not record.get('unproven_properties')
 else:
  assert record['verdict']=='not_proven' and record['failure_class'] in {'timeout','unknown'} and failed==['typed_real_trust_fixture_ensures']
  assert record.get('unproven_properties') and all(q.get('failure_class') in {'timeout','unknown'} and (not q.get('goal') or q['goal'] in failed) for q in record['unproven_properties'])
 cross=current_csv(csvrows,props,goals,failed,validated_query=validated_query,expected_wp_input=expected_wp_input)
 return {'goals':len(goals),'ordinary':len(goals)-len(smokes),'smoke':len(smokes),'properties':len(props),'Extern':len(extern),'failed_ordinary':failed,'helper_context_bridges':bridges,'smoke_display_stats':smokes,'CSV_crosswalk':cross,'healthy_negative':bool(failed),'refuted':False}

def dependency_DAG(inventory):
 props=unique(inventory['properties'],'property');seen=set();active=set()
 def visit(name):
  assert name in props and name not in active,'unknown/cyclic property dependency'
  if name in seen:return
  active.add(name)
  for dep in props[name]['dependencies']:visit(dep)
  active.remove(name);seen.add(name)
 for name in props:visit(name)
 return {'properties':len(props),'dependency_edges':sum(len(p['dependencies']) for p in props.values()),'acyclic':True,'origin_edges':'separate source/callsite attribution; not dependency edges'}


def initialized_wp_source(text, expected, reference_directory):
    """Compare the complete ACSL-bearing query against pre-run public source.

    References come from the separately audited compiler/stand-in V3 input. That
    profile supplies source text only, with no native proof verdict inherited.
    Ordinary comment bodies may vary. All other source text, including ACSL,
    whitespace, quoted text and preprocessor directives, must match exactly.
    """
    assert type(expected) is int and expected in {711, 1107}
    name = "cold-reference-wp-" + ("correct" if expected == 711 else "wrong") + ".c"
    reference = Path(reference_directory) / name
    data = reference.read_bytes()
    wanted = {711: "a324f08bed8b8101fcff22461e408b440f2f227f0d4d4ac6f5dcbed1611bccdb",
              1107: "46244c04dd878c93606add23f68a68732a5fe550d3d6b7ca308fedd4312fe094"}
    assert hashlib.sha256(data).hexdigest() == wanted[expected], "source reference changed"
    assert not re.search(r'\\[ \t\v\f\r]*\n|\?\?/', text), 'phase-one/two source transformations require separate review'
    def without_ordinary_comments(source):
        return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*(?![ \t]*@).*?\*/|//(?![ \t]*@)[^\n]*',
                      lambda match: match[0] if match[0].startswith(('"', "'")) else ' ',
                      source, flags=re.S)
    assert without_ordinary_comments(text) == without_ordinary_comments(data.decode()), "complete original query/ACSL differs"
    assert text.count(r"terminates \false;") == 3
    assert not re.search(r"\b(?:axiom|axiomatic|admit|assumes)\b|__VERIFIER_assume", text)
    assert len(re.findall(r'\bget_new_reg_unsigned_int_args0\s*\(',text))==1
    assert len(re.findall(r'/\*@\s*requires\s+\\false;\s+assigns\s+\\nothing;\s*\*/\s*int\s+get_new_reg_unsigned_int_args0\(void\);',text))==1
    return {"unused_arity0_declaration_only":True,"expected_result": expected, "reference_sha256": wanted[expected],
            "complete_ACSL_and_C_comparison": True, "reference_is_native_proof": False}
