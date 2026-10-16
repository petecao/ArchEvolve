"""2026-10-16 ET. Pure passive timeout triage; source/JSON/log reads only.
No entry/reader main, compiler, formal, provider, native API or subprocess.
"""
from pathlib import Path
import collections,hashlib,json,os,re,sys
P=Path
def noexec(event,args):
 if event in {'subprocess.Popen','os.system','os.fork','os.forkpty','os.posix_spawn','os.posix_spawnp','ctypes.dlopen'} or event.startswith(('os.exec','os.spawn')):raise RuntimeError('pure triage execution refused: '+event)
sys.addaudithook(noexec)
out=P(sys.argv[1]);out.mkdir()
E=P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-expected.json');e=json.loads(E.read_bytes());c=e['cases'][0]
R=P('/private/tmp/probata-t07-device-diagnostic-proof-v2-bd2610b6-20261016');B=R/'component';J=B/'normal';C=P('/private/tmp/probata-t07-device-proof-cold-v2-20261016-output')
def pin(p):
 p=P(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def counter(rows):return [{'key':list(k) if isinstance(k,tuple) else k,'count':v} for k,v in sorted(collections.Counter(rows).items(),key=lambda x:str(x[0]))]
def family(g):
 gid=g['goal']
 if g['smoke']:return 'smoke'
 if 'assert_rte_initialization' in gid:return 'RTE initialization'
 if 'assert_rte_' in gid:return 'other RTE'
 if '_call_' in gid:return 'callee precondition'
 if '_assigns_' in gid:return 'frame/assigns'
 if '_ensures' in gid:return 'postcondition'
 if '_fixture_read_ready' in gid:return 'read readiness check'
 if '_terminates' in gid:return 'termination'
 return 'other'
cold=json.loads((C/'normal-partial-journal-observations.json').read_bytes());rows=[r['actual_row'] for r in cold['observations']]
obs={r['actual_row']['goal']:r for r in cold['observations']};base=json.loads(P(c['generation_inventory']['path']).read_bytes());by={g['goal']:g for g in base['goals']};props={p['property']:p for p in base['properties']}
def attribution(g):
 r=obs[g['goal']]
 if r['root_coordinate']:return r['root_coordinate']['function']
 if r['call_context']:return r['call_context']['caller']
 return 'UNATTRIBUTED'
groups=collections.defaultdict(list)
for g in rows:groups[attribution(g)].append(g)
def shape(g):return dict(goal=g['goal'],actual_property=g['property'],function=g['function'],line=g['line'],smoke=g['smoke'],family=family(g),raw_passed=g['passed'],raw_results=g['results'])
roots=[]
for name,gs in sorted(groups.items()):
 ext=[(g,v) for g in gs for v in g['results'] if v['external']]
 ordinary=[g for g in gs if not g['smoke']];smoke=[g for g in gs if g['smoke']]
 roots.append(dict(root=name,goals=len(gs),ordinary=len(ordinary),smoke=len(smoke),families=counter(family(g) for g in gs),raw_status=counter((g['smoke'],g['passed'],','.join(v['verdict'] for v in g['results'])) for g in gs),latest_unique_external_results=len(ext),external_states=counter((v['prover'],g['smoke'],v['verdict']) for g,v in ext),reported_external_prover_time_sum=sum(v['prover_time'] for g,v in ext),reported_qed_time_sum_once_per_goal=sum(max([v['solver_time'] for v in g['results']]or[0]) for g in gs),ordinary_without_any_raw_valid=[g['goal'] for g in ordinary if not any(v['verdict']=='valid' for v in g['results'])],smoke_raw_valid_or_failedpassed=[g['goal'] for g in smoke if not g['passed'] or any(v['verdict']=='valid' for v in g['results'])],unattempted_smokes=[g['goal'] for g in smoke if not any(v['external'] for v in g['results'])]))
events=[json.loads(s) for s in (J/'per-prover-journal.jsonl').read_text().splitlines()]
first={};last={};updates=collections.Counter();identitychanges={}
for ev in events:
 if ev.get('event')!='modified':continue
 g=ev['row'];gid=g['goal'];first.setdefault(gid,g);last[gid]=g;updates[gid]+=1
 sig={k:g[k] for k in ['property','function','line','smoke']}
 if sig!={k:first[gid][k] for k in sig}:identitychanges[gid]=[first[gid],g]
drift=[]
for g in rows:
 b=by.get(g['goal']);dif=[k for k in ['property','function','line','smoke'] if b and b[k]!=g[k]]
 if dif:
  bp=props[b['property']]
  drift.append(dict(goal=g['goal'],root=attribution(g),differences=dif,baseline_property=b['property'],actual_property=g['property'],baseline_property_description=bp['description'],baseline_property_kind=bp.get('kind'),baseline_property_origin=bp.get('origin'),baseline_property_function=bp.get('function'),baseline_property_line=bp.get('line'),actual_function=g['function'],actual_line=g['line'],same_literal_name_stem_after_numeric_suffix_removal=re.sub(r'_\d+$','',b['property'])==re.sub(r'_\d+$','',g['property']),alias_or_identity_equivalence_admitted=False))
log=(B/'normal-proof.log').read_text();timeoutlines=[s for s in log.splitlines() if re.search(r'\[wp\].*\[(Timeout|Failed|Unknown|Valid)\]',s)]
files=[E,J/'per-prover-journal.jsonl',C/'normal-partial-journal-observations.json',J/'wp-inventory.json',J/'backend-bindings.json',J/'per-prover-final.json',J/'normalized.c',J/'site_input.c',J/'dxc_summaries.h',B/'normal-proof.log',B/'result.json',P(c['generation_inventory']['path']),P('/private/tmp/probata-root-t07-device-diagnostic-proof-execution-v1-20261016.json')]
times=[]
for p in files:
 s=p.stat();times.append(dict(path=str(p),mtime_ns=s.st_mtime_ns,birthtime=getattr(s,'st_birthtime',None),ctime_ns=s.st_ctime_ns))
primary=[P('/Users/yanrujhou/.opam/framac-33/lib/frama-c/kernel/kernel_services/ast_data/property.ml'),P('/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/core/wpPropId.ml'),P('/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/core/wpo.ml'),P('/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/core/ProverTask.ml'),P('/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/core/ProverWhy3.ml'),P('/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/core/register.ml'),B/'helper_backend_bindings.ml',B/'helper_results.ml',B/'proof_report.ml']
payload=dict(date_ET='2026-10-16',scope=__doc__,roots=roots,event_count=len(events),event_kinds=counter(ev.get('event') for ev in events),first_latest_actual_identity_changes=identitychanges,latest_goals=len(rows),raw_goal_ids_equal_generation=set(last)==set(by),baseline_drift_count=len(drift),drift_fields=counter(tuple(x['differences']) for x in drift),drift_by_root=counter(x['root'] for x in drift),drift_same_numeric_stem=sum(x['same_literal_name_stem_after_numeric_suffix_removal'] for x in drift),property_drift=drift,most_updated_goals=updates.most_common(15),terminal_log_result_lines=timeoutlines,file_times=times,input_pins=[pin(p) for p in files],primary_pins=[pin(p) for p in primary],actual_snapshot_shapes={name:{k:len(v) for k,v in json.loads((J/name).read_bytes()).items() if isinstance(v,list)} for name in ['wp-inventory.json','backend-bindings.json','per-prover-final.json']},reported_times_are_not_wall_time=True,proof_acceptance=False,no_baseline_aliases=True)
(out/'triage.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({'goals':len(rows),'events':len(events),'drift':len(drift),'roots':[{'root':r['root'],'goals':r['goals'],'external_time_sum':r['reported_external_prover_time_sum'],'external_results':r['latest_unique_external_results']} for r in roots],'drift_fields':payload['drift_fields'],'first_latest_identity_change_count':len(identitychanges),'output':str(out)}))
