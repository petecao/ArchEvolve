"""Portable metadata/source controls only. Prepared 2026-10-07 ET.
No SSH, native application, provider or remote mutation.
"""
import copy,importlib.util,json,sys,tempfile
from pathlib import Path

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f=load('/private/tmp/lanl14_final_reports_catalog_caps_a4.py','final')
e=load('/private/tmp/lanl14_final_export_catalog_caps_a4.py','export')
h=f.count_helper('/private/tmp/lanl14_count_dispatch.py')
source=Path('/Users/yanrujhou/.codex/worktrees/lanl-ticket14/ArchEvolve')
sys.path.insert(0,str(source/'swdb-project'))
from swdb import access,artifacts
checks=[]
def refuse(name,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError,FileNotFoundError):checks.append(name);return
 raise AssertionError('Control did not refuse '+name)
assert h.digest({'unicode':'é'})==artifacts.digest({'unicode':'é'});checks.append('canonical_unicode_digest')
refuse('local_host_refused',h.host)
assert len(f.CHARS)==9 and next(iter(f.CHARS))==('bfs','dx100');checks.append('fresh_dx_bfs_first_nine_unique_scopes')
assert set(f.THREADS.values())=={1,2,4};checks.append('target_threads_explicit')
with tempfile.TemporaryDirectory(prefix='lanl14-final-controls-',dir='/private/tmp') as tmp:
 root=Path(tmp);(root/'swdb-project/swdb').mkdir(parents=True);(root/'swdb-project/swdb/model.py').write_text('x=1\n')
 manifest={'module_hashes':f.modules(h,root),'estimator_sha256':h.digest(f.modules(h,root))}
 f.require_bundle(h,root,manifest);checks.append('same_complete_bundle_admitted')
 (root/'swdb-project/swdb/model.py').write_text('x=2\n');refuse('changed_mechanism_bundle_refused',lambda:f.require_bundle(h,root,manifest))
 good={'trials':[{'regions':[{'operation_counts':{'integer':{'scope':'per_trial'}},'dynamic_counts':{'trips':{'scope':'per_trial'}},
  'access_patterns':[{'element_count':{'scope':'per_trial'},'bytes_accessed':{'scope':'per_trial'}}]}],
  'unmodeled_calls':[{'execution_count':{'scope':'per_trial'},'size_bytes':{'scope':'per_trial'}}]}]}
 f.fresh_access_scope(good);checks.append('fresh_producer_actual_access_fields_admitted')
 bad=copy.deepcopy(good);bad['trials'][0]['regions'][0]['access_patterns'][0]['bytes_accessed']['scope']='per_run';refuse('old_fresh_byte_scope_refused',lambda:f.fresh_access_scope(bad))
 bad=copy.deepcopy(good);del bad['trials'][0]['regions'][0]['access_patterns'][0]['bytes_accessed'];refuse('missing_fresh_byte_fact_refused',lambda:f.fresh_access_scope(bad))
 class Store:
  def get(self,rid,kind):return {'kind':'workload_characterization','id':rid}
 store=Store();allowed=[{'id':rid,'sha256':h.digest(store.get(rid,None))} for rid in sorted(f.CPU_ALLOWED)]
 target={'extensions':{'cpu_services_binding':{'characterization_allowlist':allowed}},'mechanisms':[{'selector':{'characterization_allowlist':allowed}}]}
 f.cpu_allowlist(h,store,target);checks.append('exact_four_bf_bc_cpu_allowlist_admitted')
 bad=copy.deepcopy(target);bad['extensions']['cpu_services_binding']['characterization_allowlist'].append({'id':'pagerank','sha256':'0'*64});refuse('jacobi_cpu_transfer_refused',lambda:f.cpu_allowlist(h,store,bad))
 bad=copy.deepcopy(target);bad['mechanisms'][0]['selector']['characterization_allowlist'][0]['sha256']='0'*64;refuse('cpu_source_scope_pin_change_refused',lambda:f.cpu_allowlist(h,store,bad))
 actual=access.read_record(source/'swdb-project/records/workload_characterizations/bfs.functional.kron-g16.t4.characterization.objects.a2.yaml')
 f.require_observer(h,source,actual);checks.append('actual_historical_dx_observer_runtime_bytes_unchanged')
 bad=copy.deepcopy(actual);bad['binding']['execution_receipt']['plugin_source_sha256']='0'*64;refuse('changed_observer_requires_fresh_count',lambda:f.require_observer(h,source,bad))
 assert h.sha(source/'swdb-project/records/workload_characterizations/bfs.functional.kron-g16.t4.characterization.objects.a2.yaml')==f.OLD_FILES[actual['id']];checks.append('actual_historical_dx_record_bytes_preserved')
 raw=root/'raw';control=raw/'control';control.mkdir(parents=True);(raw/'report').mkdir();(control/'helper.py').write_bytes(Path('/private/tmp/lanl14_final_reports_catalog_caps_a4.py').read_bytes())
 m={'raw':str(raw),'source_commit':'fixture-source','identity_sha256':'fixture-manifest','tag':'fixture','estimator_sha256':'fixture-bundle','module_hashes':{'fixture.py':'fixture-sha'},'helper':{'sha256':h.sha(control/'helper.py')}}
 pairs=[{'kernel':k,'target':t,'estimate':{'id':k+'.'+t}} for k,t in f.CHARS]
 request=h.seal({'pairs':pairs});h.dump(raw/'report-request.json',request)
 report=h.seal({'request_sha256':request['identity_sha256'],'pairs':pairs,'code_equality':{'estimator_sha256':m['estimator_sha256'],'module_hashes':m['module_hashes'],'estimator_and_mechanism_diff':[]}});h.dump(raw/'report/report.json',report)
 command=['python3',str(control/'helper.py'),'run','--manifest',str(raw/'manifest.json')]
 dispatch=h.seal({'manifest_sha256':m['identity_sha256'],'node':1,'job':'swdb-lanl14-reports-fixture','command':command});h.dump(control/'dispatch.json',dispatch)
 lane={'exit_code':0,'ended_utc':'fixture-end','job':dispatch['job'],'node':1,'lease_name':'mbit10-evaluation-node1','numa_memory_policy':'bind:1','command':command};h.dump(control/'lane.json',{'socket_lane':lane})
 acceptance=h.seal({'manifest_sha256':m['identity_sha256'],'source_commit':m['source_commit'],'source_clean':True,'all_nine_public_estimates':True,'prior_record_library_app_bytes_preserved':True,'raw_transferred':False,
  'provider_calls':0,'application_timings':0,'report_sha256':report['identity_sha256'],'request_sha256':request['identity_sha256'],'fresh_dx_bfs_reference':pairs[0]['estimate'],'validation':'OK: fixture validation'})
 h.dump(control/'acceptance.json',acceptance);h.dump(control/'final-cleanup.json',{'survivors':{}});(raw/'final-validate.stdout').write_text(acceptance['validation'])
 for name in ('runner-exit-code.txt','wrapper-exit-code.txt'):(control/name).write_text('0\n')
 e.success(h,m);checks.append('sealed_successful_nine_export_fixture_admitted')
 (control/'runner-exit-code.txt').write_text('1\n');refuse('failed_attempt_export_refused',lambda:e.success(h,m));(control/'runner-exit-code.txt').write_text('0\n')
 bad=copy.deepcopy(lane);bad['command']=['foreign'];h.dump(control/'lane.json',{'socket_lane':bad});refuse('different_lane_command_export_refused',lambda:e.success(h,m));h.dump(control/'lane.json',{'socket_lane':lane})
 bad=copy.deepcopy(report);bad['code_equality']['estimator_sha256']='different';bad=h.seal({k:v for k,v in bad.items() if k!='identity_sha256'});h.dump(raw/'report/report.json',bad)
 bad_acceptance={k:v for k,v in acceptance.items() if k!='identity_sha256'};bad_acceptance['report_sha256']=bad['identity_sha256'];h.dump(control/'acceptance.json',h.seal(bad_acceptance))
 refuse('repinned_mixed_bundle_export_refused',lambda:e.success(h,m))
bc=access.read_record(Path('/Users/yanrujhou/.codex/worktrees/lanl-ticket11/ArchEvolve/swdb-project/records/workload_characterizations/bc.kron-g16.t1.characterization.objects.a1.yaml'))
f.argument_scope(bc,'bc','cpu');checks.append('actual_historical_cpu_bc_i1_admitted')
bad=copy.deepcopy(bc);bad['source']['run_arguments']=bad['source']['run_arguments'][:-2]
refuse('cpu_bc_missing_i1_refused',lambda:f.argument_scope(bad,'bc','cpu'))
f.argument_scope({'source':{'run_arguments':['-g','16','-k','16','-n','5']}},'bc','dx100');checks.append('bc_dx_func_arguments_unchanged')
assert h.sha('/private/tmp/lanl14_count_dispatch.py')==f.COUNT_HELPER_SHA;checks.append('active_count_dispatcher_unchanged')
print(json.dumps({'format':'swdb.lanl14-final-portable-controls.v1','updated':'2026-10-07 ET','checks':checks,'passed':len(checks),
 'helper_sha256':h.sha('/private/tmp/lanl14_final_reports_catalog_caps_a4.py'),'exporter_sha256':h.sha('/private/tmp/lanl14_final_export_catalog_caps_a4.py'),'native_execution':0,'provider_calls':0,'remote_actions':0,
 'actual_final_cpu_target_and_count_export_still_required':True,'linux_cleanup_proof_reused_only_after_exact_source_admission':True},indent=2))
