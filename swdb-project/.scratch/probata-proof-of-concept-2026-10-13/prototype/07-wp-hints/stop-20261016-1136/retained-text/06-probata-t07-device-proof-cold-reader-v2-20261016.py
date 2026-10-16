"""INERT passive settled device-proof cold reader V2. Execute only after root settlement.
No subprocess/tool/compiler/native/verifier/provider calls and no actual entry main.
"""
from pathlib import Path
import argparse,hashlib,json,runpy,os,stat,collections
P=Path
ENTRY=P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-entry.py');ENTRY_SHA='e7deacf1e271c291a3b40f3da4d917df8f8b5dc5bc12b07a361bb18af12aecba'
EXPECTED=P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-expected.json');EXPECTED_SHA='2a3a02e017e636abdcb8327505087adc2c8572d47bf5fdf8aab794e03ebb32d0'
ROOT=P('/private/tmp/probata-t07-device-diagnostic-proof-v2-bd2610b6-20261016');BASE=ROOT/'component'
HELPER=P('/private/tmp/probata-t07-device-proof-cold-helpers-v2-20261016.py');HELPER_SHA='744c569a6a2b3d2e2037583c9965aa9c80272450fbde7ffe90d6c2a3670a2a37'
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def pin(p):
 p=P(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--settlement',type=P,required=True);ap.add_argument('--settlement-sha',required=True);ap.add_argument('--guard-summary',type=P,required=True);ap.add_argument('--guard-sha',required=True);ap.add_argument('--output',type=P,required=True);ap.add_argument('--later-clearance',type=P);ap.add_argument('--later-clearance-sha');a=ap.parse_args()
 assert sha(ENTRY)==ENTRY_SHA and sha(EXPECTED)==EXPECTED_SHA
 assert sha(HELPER)==HELPER_SHA
 helpers=runpy.run_path(str(HELPER),run_name='passive_provenance_helpers')
 if a.settlement.resolve()!=helpers['ROOT_RECEIPT'].resolve() or a.settlement_sha!=helpers['ROOT_RECEIPT_SHA'] or sha(a.settlement)!=a.settlement_sha:raise RuntimeError('exact final root receipt role/hash required')
 if a.guard_summary.resolve()!=(ROOT/'guard.log.summary.json').resolve():raise RuntimeError('guard receipt must be the exact actual raw final file')
 if sha(helpers['ROOT_LAUNCH'])!=helpers['ROOT_LAUNCH_SHA']:raise RuntimeError('root launcher bytes changed')
 settlement=json.loads(a.settlement.read_bytes())
 guard=json.loads(a.guard_summary.read_bytes()) if a.guard_summary.is_file() else None
 if guard is None:
  if a.guard_sha!='absent':raise RuntimeError('missing guard must be explicitly declared absent')
 elif sha(a.guard_summary)!=a.guard_sha:raise RuntimeError('physical final guard hash differs')
 producer=json.loads((BASE/'result.json').read_bytes()) if (BASE/'result.json').is_file() else None
 m=runpy.run_path(str(ENTRY),run_name='passive_import_not_main');e=json.loads(EXPECTED.read_bytes())
 cp=P('/private/tmp/probata-t07-device-diagnostic-proof-v2-20261016-command.json')
 if sha(cp)!='b08868ad3dd2a65f6e3f7e51cbccaa64f32b6c4d0daa46b99a75fd75f222d5a6':raise RuntimeError('admitted command changed')
 command=json.loads(cp.read_bytes());pre=json.loads((ROOT/'root-preflight.json').read_bytes())
 context=helpers['validate_settlement'](settlement,guard,producer,pre,e,command)
 helpers['check_output_scope'](a.output,e)
 commands=json.loads((BASE/'commands.json').read_bytes()) if (BASE/'commands.json').is_file() else []
 modules=helpers['check_module_sources'](BASE,e,commands)
 later=None
 if bool(a.later_clearance)!=bool(a.later_clearance_sha):raise RuntimeError('later clearance requires paired path/hash')
 if a.later_clearance:
  if a.later_clearance.resolve()!=P('/private/tmp/probata-root-t07-device-proof-post-handoff-clearance-v1-20261016.json').resolve() or a.later_clearance_sha!='6729a43a272a12225221cc9b9a104b045c6a6fe8a54b65f290e26ff606ba242d' or sha(a.later_clearance)!=a.later_clearance_sha:raise RuntimeError('later clearance role/hash differs')
  later=json.loads(a.later_clearance.read_bytes())
  if later.get('original_root_receipt')!={'path':str(a.settlement),'sha256':a.settlement_sha} or later.get('source_after')!={'commit':e['source_commit'],'status':''} or later.get('B_flock_available_observed') is not True or len(later.get('finite_sweeps',[]))!=3 or any(r.get('active_selected_verifiers') or r.get('inspection_denials') or r.get('formal_native_lease_paths_present') for r in later['finite_sweeps']):raise RuntimeError('later finite clearance schema/context differs')
  # The original lease-present snapshot and failed/partial result are unchanged.
 a.output.mkdir()
 def snapshot(root):
  files=[];dirs=[];ipc=[]
  for p in sorted(root.rglob('*')):
   info=p.lstat();size,meta=m['output_entry_bytes'](p,info,BASE/'tmp',os.getuid())
   if stat.S_ISREG(info.st_mode):files.append(dict(path=str(p.relative_to(root)),bytes=size,sha256=sha(p)))
   elif stat.S_ISDIR(info.st_mode):dirs.append(str(p.relative_to(root)))
   else:ipc.append(meta)
  return dict(files=files,directories=dirs,IPC_metadata_only=ipc)
 before=snapshot(ROOT);write(a.output/'settled-raw-before.json',before)
 m['verify_preserved'](e);m['verify_runtime'](e['runtime'])
 recipe_copies=all(p.is_file() for p in [BASE/'entry.py',BASE/'expected.json'])
 if recipe_copies:assert sha(BASE/'entry.py')==ENTRY_SHA and sha(BASE/'expected.json')==EXPECTED_SHA
 config_present=(BASE/'why3.conf').is_file()
 if config_present:assert sha(BASE/'why3.conf')==e['fresh_config']['sha256']
 staged_all_present=all((BASE/'git-source'/r['relative']).is_file() for r in e['source_blobs'])
 for r in e['source_blobs']:
  p=BASE/'git-source'/r['relative']
  if p.is_file():
   raw=p.read_bytes();assert sha(p)==r['sha256'] and len(raw)==r['bytes'] and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['git_blob']
 if staged_all_present:assert {str(p.relative_to(BASE/'git-source')) for p in (BASE/'git-source').rglob('*') if p.is_file()}=={r['relative'] for r in e['source_blobs']}
 # The component manifest may legitimately be partial on refusal; reconcile any
 # available regular file list exactly, and disclose its original producer state.
 manifest=json.loads((BASE/'artifact-manifest.json').read_bytes()) if (BASE/'artifact-manifest.json').exists() else None
 if manifest is not None:
  for r in manifest['files']:assert sha(BASE/r['path'])==r['sha256'] and (BASE/r['path']).stat().st_size==r['bytes']
 commands=json.loads((BASE/'commands.json').read_bytes());proof_commands=[r for r in commands if r['label'].endswith('-proof')]
 assert all(r['label'] in {'normal-proof','omitted-output-proof'} for r in proof_commands) and len({r['label'] for r in proof_commands})==len(proof_commands)
 for r in proof_commands:
  cmd=r['argv'];case=next(c for c in e['cases'] if c['name']+'-proof'==r['label'])
  assert cmd==m['proof_command']([e['runtime']['tools']['opam']['path'],'exec','--root=/Users/yanrujhou/.opam','--switch=framac-33','--'],e['runtime'],BASE,case)
  assert '-wp-gen' not in cmd and all(x not in cmd for x in ['-wp-fct','-wp-prop','-wp-bhv','-wp-skip-fct'])
 results=[]
 for c in e['cases']:
  job=BASE/c['name'];journal=None;partial_journal=None
  row=dict(case=c['name'],**helpers['case_attempt'](c,job,commands,m['proof_command']([e['runtime']['tools']['opam']['path'],'exec','--root=/Users/yanrujhou/.opam','--switch=framac-33','--'],e['runtime'],BASE,c)),whole_TU_acceptance=False)
  if not job.exists():results.append(row);continue
  case={**e,**c,'case_directory':str(job)};row['present_files']=[p.name for p in job.iterdir() if p.is_file()]
  job_sources_present=all((job/name).is_file() for name in c['input_hashes'])
  for name,h in c['input_hashes'].items():
   if (job/name).is_file():assert sha(job/name)==h
  row['all_job_source_inputs_present']=job_sources_present
  baseline=json.loads(P(c['generation_inventory']['path']).read_bytes());inv=json.loads((job/'wp-inventory.json').read_bytes()) if (job/'wp-inventory.json').exists() else None
  binding=json.loads((job/'backend-bindings.json').read_bytes()) if (job/'backend-bindings.json').exists() else None
  final=json.loads((job/'per-prover-final.json').read_bytes()) if (job/'per-prover-final.json').exists() else None
  native=json.loads((job/'wp-native-goals.json').read_bytes()) if (job/'wp-native-goals.json').exists() else None
  log=(BASE/(c['name']+'-proof.log')).read_bytes().decode() if (BASE/(c['name']+'-proof.log')).exists() else ''
  if inv is not None:row['actual_universe_counts']={k:len(inv.get(k,[])) for k in ['goals','properties']}
  source=inv if inv is not None and inv.get('goals') else baseline
  if (job/'per-prover-journal.jsonl').exists():
   if job_sources_present:
    partial_journal=helpers['read_partial_prefix']((job/'per-prover-journal.jsonl').read_bytes().decode(),baseline,case,{name:(job/name).read_bytes().decode() for name in c['input_hashes']},e['expected_external_prover_ids'])
    write(a.output/(c['name']+'-partial-journal-observations.json'),{k:v for k,v in partial_journal.items() if k not in ['events','latest']})
    row['partial_journal_summary']={k:v for k,v in partial_journal.items() if k not in ['events','latest','observations']}
    row['partial_identity_difference_count']=sum(bool(r['baseline_identity_differences']) for r in partial_journal['observations'])
    row['proof_callback_observation_present']=bool(partial_journal['observed_goal_count'])
   if inv is not None:
    try:
     journal=m['read_journal']((job/'per-prover-journal.jsonl').read_bytes().decode(),source,e)
     js=dict(event_count=len(journal['events']),latest_goal_count=len(journal['latest']),truncated_last_record=journal['truncated_last_record'],unobserved_goal_ids=journal['unobserved_goal_ids'],proof_acceptance=False)
     write(a.output/(c['name']+'-journal-summary.json'),js);row['journal_summary']=js
    except Exception as error:row['journal_reader_refusal']=str(error);journal=None
   else:row['journal_boundary']='No final production inventory; source-coordinate prefix only. Actual IDs and baseline mismatches retained without aliasing or proof acceptance.'
  if all(x is not None for x in [inv,binding,final,native]):
   try:
    helpers['require_current_journal'](journal)
    assert final.get('complete_snapshot') is True
    census=m['read_inventory'](inv,log,case)
    status=m['read_device_proof'](inv,baseline,binding,final['goals'],native,e,case,log)
    warnings=m['proof_warning_census'](log,e,case,inv,binding)
    calls=[]
    for filename,functions in c['body_source_files'].items():calls+=m['direct_calls']((job/filename).read_bytes().decode(),functions,e['bodyless_allowlist'],case['helpers'],filename)
    assert calls==case['all_direct_call_contexts']
    norm=m['scan_normalized']((job/'normalized.c').read_bytes().decode(),case,calls);assert len(norm)==3
    fresh=m['read_result_rows'](final['goals'],inv,e)
    assert not journal['truncated_last_record'] and not journal['unobserved_goal_ids'] and journal['latest']==fresh
    if (job/'complete-diagnostic-census.json').exists():assert json.loads((job/'complete-diagnostic-census.json').read_bytes())==status
    if (job/'warning-census.json').exists():assert json.loads((job/'warning-census.json').read_bytes())==warnings
    write(a.output/(c['name']+'-complete-census.json'),status);write(a.output/(c['name']+'-warning-census.json'),warnings)
    props={p['property']:p for p in inv['properties']};obs={g['goal']:g for g in binding['goals']};nby={g['goal']:g for g in native}
    targets=[]
    for g in inv['goals']:
     p=props[g['property']];origin=props.get(p['origin'])
     if not g['smoke'] and (('initializ' in p['description'].lower() and 'rte' in p['emitter'].lower()) or (origin and 'initialized' in origin['description'])):
      targets.append(dict(goal=g,property=p,origin_property=origin,binding=obs[g['goal']],fresh_per_prover=fresh[g['goal']],native=nby.get(g['goal'])))
    write(a.output/(c['name']+'-all-initializedness-targets.json'),targets)
    stats=collections.Counter((g['smoke'],g['passed'],','.join(g['results'])) for g in inv['goals'])
    verdicts=collections.Counter((r['prover'],r['external'],r['verdict']) for g in final['goals'] for r in g['results'])
    row.update(structural_reconciliation=True,counts=status['counts'],roots=status['root_attribution'],ordinary_open=status['ordinary_open'],smoke_without_healthy_attempt_or_contradiction=status['smoke_without_healthy_attempt_or_contradiction'],errors_or_unfinished=status['errors_or_unfinished'],goal_status_counts=[dict(smoke=k[0],passed=k[1],results=k[2],count=v) for k,v in stats.items()],per_prover_verdict_counts=[dict(prover=k[0],external=k[1],verdict=k[2],count=v) for k,v in verdicts.items()],first_formula_and_backend_equal_generation=True,normalized_snapshots=3,extern_count=len(status['extern_property_ids']),dependency_edges=sum(len(p['dependencies']) for p in props.values()))
   except Exception as error:row.update(structural_reconciliation=False,strict_reader_refusal=dict(type=type(error).__name__,message=str(error)))
  else:row['complete_artifacts_available']=False
  results.append(row)
 m['verify_preserved'](e);m['verify_runtime'](e['runtime']);after=snapshot(ROOT);assert before==after;write(a.output/'settled-raw-after.json',after)
 summary=dict(date_ET='2026-10-16',scope='PASSIVE_SETTLED_DIAGNOSTIC_EVIDENCE_ONLY',producer_result=producer,root_settlement=pin(a.settlement),guard_summary=pin(a.guard_summary) if guard is not None else None,settlement_context=context,later_clearance=pin(a.later_clearance) if later is not None else None,later_clearance_scope='Separate later finite idle observation; never rewrites original lease/guard/result snapshot' if later is not None else None,module_source_validation=modules,guard_resource_healthy=context['guard_resource_cleanup_healthy'],all_guard_events=guard.get('inspection_events') if guard else None,cases=results,raw_unchanged=True,selected_runtime_source_preserved=bool(staged_all_present and recipe_copies and modules['all_actual_source_copies_bound'] and context['source_clean_at_original_settlement']),actual_proof_seconds=guard['wall_s'] if guard else None,actual_generation_plus_proof_seconds=47.1179103750037+guard['wall_s'] if guard else None,proof_acceptance=False,Typed_applicability_or_source_Init_lifetime_allocator_Graph_TD_count_qualified=False,reader=pin(__file__),actual_entry=pin(ENTRY))
 write(a.output/'summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k not in ['producer_result','all_guard_events','cases']}))
 return 0
if __name__=='__main__':raise SystemExit(main())
