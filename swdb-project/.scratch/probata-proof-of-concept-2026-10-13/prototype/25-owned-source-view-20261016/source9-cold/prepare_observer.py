"""2026-10-16 ET. Compiler-free author; local retained metadata/Git only."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
OLD=POC/'prototype/25-owned-transfer-20261016/cold-g621-v3/observer.py'
PACKET=HERE.parent/'public9-v3/inert-032e1851-public9-v3'
old=OLD.read_text();source=old;changes=[]
context=json.loads((HERE/'context.json').read_bytes())
expected=json.loads((HERE/'expected.frozen.json').read_bytes())
packet=json.loads((PACKET/'packet.json').read_bytes())

def replace(before,after,label,count=1):
    global source
    assert source.count(before)==count,(label,source.count(before),count)
    source=source.replace(before,after)
    changes.append({'label':label,'before':before,'after':after,'count':count})

replace('G621 ownership10','G623 source9','scope')
replace("probata-resume-20261016-d7f685c6-owned-transfer10-public-v2","probata-resume-20261016-032e1851-owned-source9-public-v3",'raw')
replace("owned-transfer10-public-v2-profile","owned-source9-public-v3-profile",'profile')
replace("/data1/yanruj/probata-resume-20261016-d7f685c6","/data1/yanruj/probata-resume-20261016-032e1851",'source')
replace("d7f685c6fdbd7ff776eb1eaccc40099a2c48dc08",expected['source_commit'],'commit')
replace("663fcd74640b4d04f7d3ae38b5587924fc10501cd82831a014f18e05eaf31c94",packet['entry']['sha256'],'entry')
replace("ff336dc468cb526061000c41125dabb1a285b5399f58ac27a3ca72f7a6ca46cf",packet['expected']['sha256'],'expected')
replace("12bcda644bfb6fde4877b6d5d82a2648c77e1b7b021ab154a4a198cae27bb0c1",context['frozen_root_command_file_sha256'],'unresolved command pin')
replace("38f8de3d374aae446abbf1e9f7e8d3fa23817d0074bc8320b1518659288480a4",context['resolved_root_command_sha256'],'resolved command pin')
replace("candidates = [PROFILE / 'canonical-inputs/theory/vector_owned_state.mlw'] if name == 'vector_owned_state.Owners' else [prefix / 'share/why3/stdlib' / filename, prefix / 'share/frama-c/share/wp/why3' / filename]",
        "project_modules = {'heap_reallocation.Heap':'heap_reallocation.mlw', 'vector_owned_state.Owners':'vector_owned_state.mlw', 'vector_owned_effects.OwnedEffects':'vector_owned_effects.mlw'}\n            candidates = [PROFILE/'canonical-inputs/theory'/project_modules[name]] if name in project_modules else [prefix/'share/why3/stdlib'/filename, prefix/'share/frama-c/share/wp/why3'/filename]",'all three project module roots')
replace("if name == 'vector_owned_state.Owners':\n                need(not propositions, 'Owners is definition-only, no desired axiom/lemma premise')",
        "if name in project_modules:\n                need(not propositions, 'all Heap/Owners/OwnedEffects project modules are definitions only')\n                wanted=CONTEXT['source_theories'][project_modules[name]]\n                need(pin(found[0])['sha256']==wanted['sha256'], 'complete original source theory pin')",'definitions only source modules')
replace("if name == 'vector_owned_state.Owners' else 'selected standard arithmetic/maps/Qed support TCB'","if name in project_modules else 'selected standard arithmetic/maps/Qed support TCB'",'project module classification')
replace("launch['timeout_seconds'] == 2100","launch['timeout_seconds'] == 2400",'whole duration')
replace("lane['lease_generation'] == 621","lane['lease_generation'] == 623",'generation')
replace("2026-10-16T21:51:35Z","2026-10-16T22:42:27Z",'start')
replace("2026-10-16T21:52:07Z","2026-10-16T22:45:42Z",'end')
replace("(2220 if name.startswith('outer') else 2100)","(2520 if name.startswith('outer') else 2400)",'outer duration')
replace('exact settled G621 lane','exact settled original G623 lane','lane label')
replace('exact settled184-file/54-directory raw membership','exact settled188-file/51-directory raw membership','membership label')
replace("== 184 and\n         sum(r.get('bytes', 0) for r in initial) == 21000828","== 188 and\n         sum(r.get('bytes', 0) for r in initial) == 21450336",'raw extent')
replace("owned-transfer10-public-v2-entry.py","owned-source9-public-v3-entry.py",'staged producer entry')
replace("len(canonical) == 21, 'complete21 canonical bytes'","len(canonical) == 29, 'complete29 canonical bytes'",'canonical census')
replace("result['all_ten_producer_proven'] is True","result['all_nine_producer_proven'] is False",'all nine actual outcomes')
replace("'settled ten producer results'","'settled nine producer results including original timeout'",'result label')
replace("list(semantic.GOALS), 'all ten distinct source duties in order'","list(semantic.CONCLUSIONS), 'all nine distinct source duties in order'",'nine formula census')
replace("outcome == run['outcome'] and outcome['verdict'] == 'proven' and not outcome['assumptions'] and\n             not outcome['unproven'] and outcome['reading'] == {'check': reading, 'verdict': 'proven'}, 'current normal outcome with no opaque premise'",
        "outcome == run['outcome'] and not outcome['assumptions'] and outcome['reading']['check']==reading\n             and outcome['reading']['verdict']==outcome['verdict'], 'unchanged current normal outcome, no opaque premise')\n        timed_out=ident=='swap.owner_correspondence'\n        need(outcome['verdict']==('not_proven' if timed_out else 'proven') and outcome['failure_class']==('timeout' if timed_out else None)\n             and bool(outcome['unproven'])==timed_out, 'exact original8 Valid and sole ordinary Timeout'",'normal outcome and timeout')
replace("goal['property'] == prop and goal['passed'] is True and goal['smoke'] is False and\n             goal['targets'] == [] and 'valid' in goal['results'] and goal['function'] is None, 'direct global native Valid'",
        "goal['property']==prop and goal['passed'] is (not timed_out) and goal['smoke'] is False\n             and goal['targets']==[] and goal['function'] is None\n             and (('valid' not in goal['results'] and 'timeout' in goal['results']) if timed_out else 'valid' in goal['results']), 'all original native outcomes retained'",'native timeout')
replace("any(p.get('success') for p in peer['provers']), 'ordinary/native/prover peer'","(not any(p.get('success') for p in peer['provers']) if timed_out else any(p.get('success') for p in peer['provers'])), 'ordinary/native/prover peer'",'timeout prover matrix')
replace("len(properties) == 2","len(properties) == 4",'property count')
replace("closure['exported_count'] == 2","closure['exported_count'] == 4",'registered property count')
replace("need(len(selected) == 2 and all(Path(r['relative']).suffix == '.psmt2' for r in selected), 'all two retained Alt-Ergo task artifacts')",
        "wanted=[r for r in context['task_artifacts'] if r['relative'].startswith(str(directory.relative_to(RAW))+'/')]\n        need(selected==wanted and len(selected)==(6 if ident.endswith('owner_correspondence') else 2), 'complete actual26-task solver/artifact census')",'all actual solver tasks')
replace("len(tasks) == 20 and len(leaves) == 10, 'complete ten-owner/twenty-task census'","len(tasks) == 26 and len(leaves) == 9, 'complete nine-owner/twenty-six-task census'",'total tasks')
replace("need('vector_owned_state.Owners' in graph, 'actual Owners import present')","need({'heap_reallocation.Heap','vector_owned_state.Owners','vector_owned_effects.OwnedEffects'}<=set(graph), 'all actual source imports present')",'complete source import roots')
# The exact number is derived from complete retained membership, not an invented constant.
replace("len(advertised) == len(set(advertised)) == 164","len(advertised) == len(set(advertised)) == len(profile_files)-1",'complete manifest membership')
replace("'COMPLETE_COLD_CAPTURE_PENDING_ENCODING_REVIEW' if unresolved else 'PASS_CONDITIONAL_OWNERSHIP10_MATH_COLD'","'COMPLETE_SOURCE9_COLD_PENDING_ENCODING_REVIEW' if unresolved else 'COMPLETE_SOURCE9_COLD_EIGHT_PROVEN_ONE_TIMEOUT'",'honest classification')
replace("'raw_files': 184,\n                  'raw_bytes': 21000828","'raw_files': 188,\n                  'raw_bytes': 21450336",'reported extent')
replace("'all_ten_conditional_math_semantically_reconciled': not unresolved,\n                  'consistency': context['constructive_consistency']","'all_nine_conditional_math_semantically_reconciled': not unresolved,\n                  'source_statement_census': context['source_statement_census'], 'source_type_semantics_established':False, 'all_nine_proven':False",'no vacuity or type adoption')
replace("Ten conditional unbounded mathematical registry duties only. Original8 move/swap bodies remain unproved context; no source field/ownership/lifetime/Heap/allocator/Typed/body/caller/default/public admission. Zero global check-lemma smokes are not empirical consistency evidence.","Nine conditional source/Heap/header duties; eight native Valid and one original normal Timeout retained. Complete source formula/hypothesis/import/encoding census is separate from mathematical adoption. Original8 move/swap bodies/layout/padding/payload/source ownership/Heap/Typed/cleanup/caller/default/public gates stay pending. Zero global check-lemma smokes are not empirical consistency evidence.",'scope statement')
replace("STATE = {'classification': 'REFUSED_OWNERSHIP10_PASSIVE_COLD'", "STATE = {'classification': 'REFUSED_SOURCE9_PASSIVE_COLD'",'initial refusal label')
replace("context = json.loads(CONTEXT_JSON)", "context = json.loads(CONTEXT_JSON)\n        globals()['CONTEXT']=context",'exact project-module context binding')
replace("ownership10_semantics","source9_semantics",'semantic namespace')
replace("pinned-ownership10-pure-terms","pinned-source9-pure-terms",'semantic source label')
replace("REFUSED_OWNERSHIP10_PASSIVE_COLD","REFUSED_SOURCE9_PASSIVE_COLD",'final refusal labels',2)
# Required semantic/read invariants added independently of the generic predecessor.
needle="    leaves, tasks, roots, unresolved = [], [], set(), []"
insert="""    need([semantic.source_statement(row['id']) for row in manifest['obligations']]==[row['statement'] for row in manifest['obligations']], 'all nine independently transcribed full ACSL statements')
    for name,row in context['source_theories'].items():
        need(pin(PROFILE/'canonical-inputs'/row['canonical_path'])['sha256']==row['sha256']\n             and pin(SOURCE/'swdb-project'/row['frozen_source_path'])['sha256']==row['sha256'], 'whole actual source theory/input inverse')
    need(result['layout']=={'executed':False,'units':0,'C_layout_assertions_adopted':False,'scope':'Math-only namespace repair; previous V2 layout observations remain separate and require complete dependency cold closure.'}, 'original9 never adopts separate layout observations')
    leaves, tasks, roots, unresolved = [], [], set(), []"""
replace(needle,insert,'independent source formula and theory/phase boundary')
replace("'native_provers': peer['provers'], 'common_theories': common, 'task_census': census}","'native_provers': peer['provers'], 'common_theories': common, 'task_census': census, 'normal_verdict':outcome['verdict'],'failure_class':outcome['failure_class']}",'retain reader decision')
# No actual source bytes were inspected remotely by this compiler-free author.
ast.parse(source)
for name in ('need','sha','compact','digest','identity','physical','read_bytes','pin','read','walk','git','audit','runtime','source_closure','strip_comments','normal_flags','resolved_command'):
    def node(text):return next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name==name)
    assert ast.dump(node(old),include_attributes=False)==ast.dump(node(source),include_attributes=False),name
(HERE/'observer.py').write_text(source)
(HERE/'observer-delta.json').write_text(json.dumps({'date':'2026-10-16 ET','changes':changes,'source':str(OLD),'source_sha256':hashlib.sha256(old.encode()).hexdigest(),'successor_sha256':hashlib.sha256(source.encode()).hexdigest(),'unchanged17helpers':True,'actual_execution':False},sort_keys=True,indent=2)+'\n')
print(json.dumps({'observer_sha256':hashlib.sha256(source.encode()).hexdigest(),'bytes':len(source.encode()),'edits':len(changes)}))
