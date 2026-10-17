import ast,datetime,difflib,hashlib,json,os
from pathlib import Path
from zoneinfo import ZoneInfo
T=Path('/private/tmp');old=T/'lanl17_pre_full_index_host_observation_20261008_a5_r4.py';s=old.read_text();assert hashlib.sha256(s.encode()).hexdigest()=='fdc5376fc6838081806f1a48b236eaea3dba280f4ac6726bf4fe4f3db58f8c2f'
changes=[("d=strict(bodies[role]);need(d.get('format')", "d=strict(bodies[role]);need(type(d) is dict,'original_control_JSON_object');need(d.get('format')"),("    result=strict(bodies['final_export']);helper=strict(bodies['helper_stdout'])\n", "    result=strict(bodies['final_export']);helper=strict(bodies['helper_stdout']);need(type(result) is dict and type(helper) is dict,'original_export_helper_JSON_objects')\n")]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
ast.parse(s);source=T/'lanl17_pre_full_index_host_observation_20261008_a5_r5.py'
def write(p,b):
 if type(b)is str:b=b.encode()
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b)
 return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
pins=[write(source,s)];sha=pins[0]['sha256'];inv=s
for a,b in reversed(changes):assert inv.count(b)==1;inv=inv.replace(b,a)
assert inv==old.read_text()
for label,p in [('r4',old),('host-r2',T/'lanl17_finalize_parent_host_readonly_20261008_a5_r2.py')]:pins.append(write(T/f'lanl17-pre-full-index-host-observation-r5-complete-{label}-derivation-20261008-a5.diff',''.join(difflib.unified_diff(p.read_text().splitlines(True),s.splitlines(True),fromfile=str(p),tofile=str(source)))))
for i in range(1,5):
 p=T/f'lanl17-p{i}-pre-full-index-host-input-SOURCE-ONLY-draft-r4-20261008-a5.json';d=json.loads(p.read_text());d['source']=pins[0];d['input_template']['parent_review']['source_sha256']=sha;d['supersedes_source_only_input_draft']=str(p);pins.append(write(T/f'lanl17-p{i}-pre-full-index-host-input-SOURCE-ONLY-draft-r5-20261008-a5.json',json.dumps(d,sort_keys=True,indent=2)+'\n'))
p=T/'lanl17-pre-full-index-host-action-SOURCE-ONLY-draft-r6-20261008-a5.json';d=json.loads(p.read_text());d['source']=pins[0];d['config_template']['argv'][4]=s;d['config_template']['argv'][-1]=sha;d['supersedes_source_only_action_draft']=str(p);pins.append(write(T/'lanl17-pre-full-index-host-action-SOURCE-ONLY-draft-r7-20261008-a5.json',json.dumps(d,sort_keys=True,indent=2)+'\n'))
now=datetime.datetime.now(datetime.timezone.utc);v={'format':'swdb.lanl17-pre-full-index-closed-refusal-source-static-review.v1','prepared_ET':now.astimezone(ZoneInfo('America/Detroit')).strftime('%Y-%m-%d %H:%M ET'),'prepared_utc':now.isoformat(),'source_only_not_run':True,'scientific_admission':False,'executable':False,'checks':{'two_narrow_source_inverse_replacements_restore_R4':True,'AST_parse_only':True,'original_control_JSON_object_guard_precedes_get':True,'original_export_and_helper_JSON_object_guard_precedes_set_or_subscript':True,'all_29_roles_unchanged':True,'inherited_readers_native_process_continuity_guards_unchanged':True,'input_source_pin_propagated_all_four':True,'action_inline_source_and_sourceSHA_exact':True,'generic_H_M2_private_pins_only':True,'deadlines_unchanged':[45,60,180],'no_runtime_import_or_tests':True},'pins':pins}
pins.append(write(T/'lanl17-pre-full-index-closed-refusal-source-static-review-r5-20261008-a5.json',json.dumps(v,sort_keys=True,indent=2)+'\n'))
h=f"Prepared {v['prepared_ET']} ({v['prepared_utc']}).\n\nSelected SOURCE ONLY pair: source R5, action R7; four input drafts R5. All earlier sources/drafts remain preserved NOTRUN. No current fact, completed FINALIZE, ER commit, genuine approval or runtime result is supplied.\n\nFresh source R5 closes malformed original JSON refusal: original control seal inputs must be dict before .get; final export/helper stdout inputs must be dict before set/subscript. Without this guard malformed list/scalar could raise uncaught AttributeError. No original/control/schema guard is relaxed. Exact inverse restores source R4. Source hash propagates into every NONEXECUTABLE typed FUTURE input and action inline source.\n\nRead source R4 and action R6 handoffs for exact29-role map, explicit next-stage subsets, ER stop equality, UTC projection guard, empty argv0 inactivity/unknown handling, native514/FD9/kernel/physical185F6/tools/floors, private generic H/M2 pins and independent parent fact limits. Completion and actual-input root+peer review remain mandatory before any use; ready is point-in-time metadata only, no scientific admission.\n\n"
for p in pins:h+=f"- {p['path']}: {p['bytes']} B SHA256 {p['sha256']}\n"
pins.append(write(T/'lanl17-pre-full-index-selected-source-action-handoff-r7-20261008-a5.md',h));print(json.dumps(pins,indent=2))
