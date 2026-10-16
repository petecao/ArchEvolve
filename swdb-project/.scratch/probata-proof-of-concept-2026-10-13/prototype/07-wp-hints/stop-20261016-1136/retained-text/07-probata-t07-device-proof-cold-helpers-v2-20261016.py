"""Pure source-bound cold provenance/partial-observation helpers; no process or native API."""
from pathlib import Path
import json,hashlib,math,re
P=Path
ROOT=P('/private/tmp/probata-t07-device-diagnostic-proof-v2-bd2610b6-20261016');BASE=ROOT/'component'
ROOT_LAUNCH=P('/private/tmp/probata-root-t07-device-diagnostic-proof-launch-v1-20261016.py')
ROOT_LAUNCH_SHA='3f4f7564ccfdf03c079f1fbc20101239a510311ec2af1c6c054790f5e05eb7ec'
ROOT_RECEIPT=P('/private/tmp/probata-root-t07-device-diagnostic-proof-execution-v1-20261016.json')
ROOT_RECEIPT_SHA='1a34280a210040e44a7d2b2f00659a8e69de2f003bffe7330d0f27eb06c9893a'
LEASES={'/tmp/claude/swdb-verifier.lock','/tmp/claude/swdb-verifier.slot2.lock','/tmp/claude/swdb-native-b.lock'}
def H(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def check_output_scope(output,e):
 output=P(output)
 if output.exists() or output.is_symlink():raise RuntimeError('fresh non-symlink output required')
 protected=[ROOT,P(e['source_root']),ROOT_LAUNCH,ROOT_RECEIPT,P(__file__),P('/private/tmp/probata-t07-device-proof-cold-reader-v2-20261016.py'),P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-entry.py'),P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-expected.json'),P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-command.json'),P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-packet.json')]
 protected += [P(r['root']) for r in e['preserved_roots']]
 protected += [P(r['path']) for r in e['reference_pins']]
 protected += [P(e['journal']['path']),P(e['ipc_accounting_source']['path'])]
 runtime=e['runtime']
 for key in ['package_surfaces']:protected += [P(r['path']) for r in runtime[key]]
 for key in ['standard_headers','psutil_surface','why3_stdlib','wp_why3_support','why3_drivers']:protected.append(P(runtime[key]['path']))
 for key in ['configuration_files','native_closure','primary_sources','toolchain_artifacts']:protected += [P(r['path']) for r in runtime[key]]
 protected += [P(r['path']) for r in runtime['tools'].values()]+[P(runtime['python']['path'])]
 target=output.resolve()
 for p in protected:
  p=p.resolve()
  if target==p or target.is_relative_to(p) or p.is_relative_to(target):raise RuntimeError('output overlaps a source/runtime/retained/current protected path')
 return {'resolved_output':str(target),'protected_path_count':len(protected),'disjoint':True}
def validate_settlement(root,guard,producer,pre,e,command):
 # These are provenance obligations, not success requirements. Unhealthy actual
 # final states are returned explicitly; identities/schema cannot be waived.
 expected_pin={'path':str(ROOT_LAUNCH),'sha256':ROOT_LAUNCH_SHA,'bytes':7770}
 if not isinstance(root,dict) or root.get('root_entry')!=expected_pin or root.get('raw')!=str(ROOT):raise RuntimeError('root launcher/raw provenance mismatch')
 needed={'exit_code','elapsed_seconds','termination','minimum_observed_free_bytes','allowed_same_uid_zero_byte_tmp_why3server_sockets','guard','result','source_after','finite_settlement_sweeps','lease_paths_present_after','at_utc','date_ET','scope'}
 if not needed<=set(root):raise RuntimeError('final root receipt schema incomplete')
 if root['guard']!=guard or root['result']!=producer:raise RuntimeError('embedded root guard/result differs from exact actual physical files')
 if type(root['exit_code']) is not int or type(root['elapsed_seconds']) not in {int,float} or not math.isfinite(root['elapsed_seconds']) or root['elapsed_seconds']<0:raise RuntimeError('root final exit/time schema differs')
 source=root['source_after']
 if not isinstance(source,dict) or not isinstance(source.get('commit'),str) or not isinstance(source.get('status'),str):raise RuntimeError('source-after snapshot malformed')
 if not isinstance(root['at_utc'],str) or root['date_ET']!='2026-10-16' or not isinstance(root['scope'],str):raise RuntimeError('root date/scope schema differs')
 leases=root['lease_paths_present_after']
 if not isinstance(leases,list) or len(set(leases))!=len(leases) or any(p not in LEASES for p in leases):raise RuntimeError('root lease snapshot malformed')
 sweeps=root['finite_settlement_sweeps']
 if not isinstance(sweeps,list) or len(sweeps)!=3:raise RuntimeError('three final finite sweeps required')
 for r in sweeps:
  if not isinstance(r,dict) or not isinstance(r.get('active_selected_verifiers'),list) or not isinstance(r.get('inspection_denials'),list) or type(r.get('same_uid_metadata_count')) is not int or r['same_uid_metadata_count']<0:raise RuntimeError('finite sweep schema malformed')
  if any(type(p) is not int for p in r['inspection_denials']):raise RuntimeError('finite sweep denial metadata malformed')
  for p in r['active_selected_verifiers']:
   if not isinstance(p,dict) or type(p.get('pid')) is not int or not isinstance(p.get('name'),str) or type(p.get('birth')) not in {int,float}:raise RuntimeError('finite sweep process metadata malformed')
 expected_argv=[e['runtime']['python']['path'],'-B','/private/tmp/probata-mac-compiler-worker-b.py','--',e['runtime']['python']['path'],'-B',command['guard']['path'],'--log',str(ROOT/'guard.log'),'--cap-gb','8','--timeout','780','--queue-timeout','30','--owner','root-t07-device-full-proof-diagnostic','--',*command['argv']]
 if (not isinstance(pre,dict) or pre.get('root_entry')!=expected_pin or pre.get('source_commit')!=e['source_commit'] or pre.get('source_clean') is not True or pre.get('published_ancestor') is not True or pre.get('argv')!=expected_argv or pre.get('entry')!=command['entry'] or pre.get('expectation')!=command['expected']):raise RuntimeError('actual root preflight/command/source provenance mismatch')
 packet=P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-packet.json')
 if pre.get('packet')!={'path':str(packet),'sha256':H(packet),'bytes':packet.stat().st_size}:raise RuntimeError('actual preflight packet identity differs')
 termination=root['termination']
 if termination is not None and (not isinstance(termination,dict) or not {'at_seconds','bytes','special_outputs','free_bytes','action'}<=set(termination)):raise RuntimeError('root termination schema malformed')
 ipc=root['allowed_same_uid_zero_byte_tmp_why3server_sockets']
 if not isinstance(ipc,list) or len(set(ipc))!=len(ipc) or any(P(p).parent!=BASE/'tmp' or not re.fullmatch(r'why3server[0-9a-f]{6}sock',P(p).name) for p in ipc):raise RuntimeError('root observed IPC context differs')
 if type(root['minimum_observed_free_bytes']) is not int or root['minimum_observed_free_bytes']<0:raise RuntimeError('root capacity snapshot malformed')
 resources=False
 if guard is not None:
  if (not isinstance(guard,dict) or guard.get('cmd')!=command['argv'] or guard.get('log')!=str(ROOT/'guard.log') or guard.get('cap_gb')!=8 or guard.get('timeout_s')!=780 or guard.get('queue_timeout_s')!=30 or type(guard.get('exit_code')) is not int or not isinstance(guard.get('finished'),str) or not isinstance(guard.get('inspection_events'),list)):raise RuntimeError('exact final physical c6 guard/command/cap schema differs')
  if termination is None and root['exit_code']!=guard['exit_code']:raise RuntimeError('root and guard exits disagree without recorded outer termination')
  resources=not any(guard.get(k) for k in ['killed_by_watchdog','timed_out','queue_timed_out','inspection_failure','primary_inspection_failure','cleanup_inspection_failure','cleanup_inspection_failures','unconfirmed_children','error'])
 if producer is not None:
  if not isinstance(producer,dict) or producer.get('source_commit')!=e['source_commit'] or producer.get('proof_acceptance') is not False or producer.get('whole_TU_proof_acceptance') is not False or producer.get('Typed_source_Init_lifetime_TD_count_qualified') is not False or not isinstance(producer.get('cases'),list) or type(producer.get('execution_completed')) is not bool:raise RuntimeError('actual producer source/scope/result schema differs')
 source_clean=source=={'commit':e['source_commit'],'status':''}
 finite_empty=all(not s['active_selected_verifiers'] and not s['inspection_denials'] for s in sweeps)
 return dict(root_provenance_bound=True,guard_present=guard is not None,producer_result_present=producer is not None,source_after=source,source_clean_at_original_settlement=source_clean,guard_resource_cleanup_healthy=resources,original_finite_sweeps_empty_no_denials=finite_empty,original_lease_snapshot=leases,original_leases_absent=not leases,outer_termination=termination,original_guard_inspection_events=guard.get('inspection_events') if guard else None,original_guard_exit=guard.get('exit_code') if guard else None,original_root_exit=root['exit_code'],diagnostic_execution_completed=bool(producer and producer['execution_completed']),fully_healthy_complete_original_settlement=bool(resources and source_clean and finite_empty and not leases and termination is None and root['exit_code']==0 and producer and producer['execution_completed']),proof_acceptance=False)
def check_module_sources(base,e,commands):
 base=P(base);rows=[]
 for key,name in [('report_relative','proof_report'),('observer_relative','helper_backend_bindings'),(None,'helper_results')]:
  want=e['journal']['sha256'] if key is None else next(r['sha256'] for r in e['source_blobs'] if r['relative']==e[key])
  source=base/(name+'.ml');present=source.is_file()
  if present and H(source)!=want:raise RuntimeError('actual compiled module source copy differs from frozen source: '+name)
  matches=[r for r in commands if r.get('label')==name+'-compile']
  if len(matches)>1:raise RuntimeError('module compilation recorded more than once')
  expected=[e['runtime']['tools']['opam']['path'],'exec','--root=/Users/yanrujhou/.opam','--switch=framac-33','--',e['runtime']['tools']['ocamlfind']['path'],'ocamlopt','-shared','-linkall','-package','frama-c.kernel,frama-c-wp.core','-o',name+'.cmxs',name+'.ml']
  if matches and (matches[0]['argv']!=expected or matches[0]['cwd']!=str(base)):raise RuntimeError('actual module compilation command/cwd differs')
  rows.append(dict(module=name,source_present=present,source_hash=H(source) if present else None,source_equals_frozen=present,compile_command_recorded=bool(matches),compile_log_present=(base/(name+'-compile.log')).is_file(),compiled_artifact_present=(base/(name+'.cmxs')).is_file()))
 return dict(modules=rows,all_actual_source_copies_bound=all(r['source_equals_frozen'] for r in rows),all_fresh_compilation_artifacts_present=all(r['source_equals_frozen'] and r['compile_command_recorded'] and r['compile_log_present'] and r['compiled_artifact_present'] for r in rows))
def case_attempt(case,job,commands,expected_command):
 matches=[r for r in commands if r.get('label')==case['name']+'-proof']
 if len(matches)>1:raise RuntimeError('proof command recorded more than once')
 if matches and (matches[0]['argv']!=expected_command or matches[0]['cwd']!=str(job)):raise RuntimeError('proof attempt command/cwd differs')
 return dict(directory_present=P(job).is_dir(),proof_command_recorded=bool(matches),proof_attempt_recorded=bool(matches),attempt_boundary='command journal is written immediately before subprocess call; directory/command/log alone is not proof that Frama executed',proof_log_present=(P(job).parent/(case['name']+'-proof.log')).is_file(),proof_acceptance=False)
def require_current_journal(journal):
 if journal is None:raise RuntimeError('current-case journal missing or did not parse; never reuse prior case')
 if journal['truncated_last_record'] or journal['unobserved_goal_ids']:raise RuntimeError('current-case journal is incomplete')
def read_partial_prefix(text,baseline,case,source_texts,external_ids):
 # A source-coordinate observation report, not a property aliasing/proof reader.
 baseline_by={g['goal']:g for g in baseline['goals']};latest={};events=[];errors=[];truncated=False;coordinates=[]
 for filename,functions in case['body_source_files'].items():
  original=source_texts[filename];code=re.sub(r'/\*.*?\*/',lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group()),original,flags=re.S)
  for fn in functions:
   hits=list(re.finditer(r'\b'+re.escape(fn)+r'\s*\([^;{}]*\)\s*\{',code))
   if len(hits)!=1:raise RuntimeError('partial source-coordinate function definition ambiguous')
   a=hits[0].start();end=hits[0].end();depth=1
   while depth and end<len(code):
    if code[end]=='{':depth+=1
    elif code[end]=='}':depth-=1
    end+=1
   start=original.rfind('/*@',0,a);start=a if start<0 else start
   coordinates.append(dict(function=fn,source_file=filename,first_line=original.count('\n',0,start)+1,last_line=code.count('\n',0,end)+1))
 lines=text.splitlines()
 for number,line in enumerate(lines,1):
  try:event=json.loads(line)
  except json.JSONDecodeError:
   if number==len(lines) and not text.endswith('\n'):truncated=True
   else:errors.append(dict(line=number,error='non-final malformed JSON record'))
   continue
  if not isinstance(event,dict):errors.append(dict(line=number,error='journal event is not an object'));continue
  kind=event.get('event');events.append(event)
  if kind=='cleared':latest.clear();continue
  if kind not in {'modified','removed'}:errors.append(dict(line=number,error='unknown journal event'));continue
  r=event.get('row')
  if not isinstance(r,dict) or any(not isinstance(r.get(k),str) or not r[k] for k in ['goal','property']) or not (r.get('function') is None or isinstance(r['function'],str)) or type(r.get('line')) is not int or type(r.get('smoke')) is not bool or type(r.get('passed')) is not bool or not isinstance(r.get('results'),list):errors.append(dict(line=number,error='row identity/status schema differs'));continue
  for v in r['results']:
   if not isinstance(v,dict) or not isinstance(v.get('prover'),str) or type(v.get('external')) is not bool or v.get('verdict') not in {'untried','unknown','timeout','stepout','computing','valid','invalid','failed'} or type(v.get('cached')) is not bool:errors.append(dict(line=number,goal=r['goal'],error='raw result schema differs'));continue
   for key in ['solver_time','prover_time']:
    if type(v.get(key)) not in {int,float} or not math.isfinite(v[key]) or v[key]<0:errors.append(dict(line=number,goal=r['goal'],error='raw timing schema differs'))
   if type(v.get('prover_steps')) is not int or not isinstance(v.get('error_message'),str) or not isinstance(v.get('model'),str):errors.append(dict(line=number,goal=r['goal'],error='raw solver metadata schema differs'))
   pos=v.get('error_position')
   if pos is not None and (not isinstance(pos,dict) or not isinstance(pos.get('file'),str) or any(type(pos.get(k)) is not int for k in ['line','bol','cnum'])):errors.append(dict(line=number,goal=r['goal'],error='raw error position schema differs'))
  if kind=='modified':latest[r['goal']]=r
  else:latest.pop(r['goal'],None)
 observed=[]
 for gid,r in latest.items():
  old=baseline_by.get(gid);diff=[k for k in ['property','function','line','smoke'] if old is not None and old.get(k)!=r.get(k)]
  contexts=[c for c in case['all_direct_call_contexts'] if c['callee']==r['function'] and c['line']==r['line']]
  body=[c for c in coordinates if c['function']==r['function'] and c['first_line']<=r['line']<=c['last_line']]
  source_class='exact_callee_call_coordinate' if len(contexts)==1 else 'root_contract_or_body_coordinate' if len(body)==1 else 'unattributed_coordinate'
  observed.append(dict(actual_row=r,baseline_goal_present=old is not None,baseline_identity_differences=diff,baseline_property_id=old['property'] if old else None,source_coordinate_class=source_class,call_context=contexts[0] if len(contexts)==1 else None,root_coordinate=body[0] if len(body)==1 else None,raw_IDs_rewritten=False,goal_equivalence_or_proof_accepted=False))
 return dict(events=events,latest=latest,observations=observed,parse_errors=errors,truncated_last_record=truncated,observed_goal_count=len(latest),baseline_goal_count=len(baseline_by),baseline_unobserved_goal_ids=sorted(set(baseline_by)-set(latest)),actual_nonbaseline_goal_ids=sorted(set(latest)-set(baseline_by)),external_prover_ids_observed=sorted({v['prover'] for r in latest.values() for v in r['results'] if v.get('external')}),unexpected_external_prover_ids=sorted({v['prover'] for r in latest.values() for v in r['results'] if v.get('external') and v['prover'] not in external_ids}),cached_observations=[r['goal'] for r in latest.values() if any(v.get('cached') for v in r['results'])],scope='partial callback prefix only; no status/identity rewrites, baseline property mismatch stays unresolved, no final inventory/graph or proof acceptance',proof_acceptance=False)
