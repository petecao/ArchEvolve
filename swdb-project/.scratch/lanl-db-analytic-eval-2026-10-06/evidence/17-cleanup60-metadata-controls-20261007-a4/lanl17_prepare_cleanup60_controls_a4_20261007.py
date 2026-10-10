"""Source-only derived administrative cleanup controls; no imports/actions/tests."""
import ast
import datetime
import difflib
import hashlib
import json
from pathlib import Path

TMP=Path('/private/tmp')
OLD_HELPER='69dcfe546d3042228ccca4fb29e8409da88443ba15680f30bfdc929ea12ae2b9'
OLD_SUPERVISOR='16661d7a9347e328a5263b06d807f3632c5abcfcf41a0bd97655a6bba302176b'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
original=TMP/'lanl17_parent_helpers_caps_a3.py'
supervisor=TMP/'lanl17_metadata_supervisor_caps_a3.py'
assert sha(original)==OLD_HELPER and sha(supervisor)==OLD_SUPERVISOR
old=original.read_text();module=ast.parse(old)
dispatch=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='dispatch')
sites=[n for n in ast.walk(module) if isinstance(n,ast.Constant) and n.value=='--kill-after=40s']
assert len(sites)==1 and sites[0] in list(ast.walk(dispatch))
node=sites[0];assert node.lineno==467
assert old.count("'--kill-after=40s'")==1
new=old.replace("'--kill-after=40s'","'--kill-after=60s'",1)
assert new.replace("'--kill-after=60s'","'--kill-after=40s'",1)==old
helper=TMP/'lanl17_parent_helpers_cleanup60_a4.py';assert not helper.exists();helper.write_text(new)
helper_sha=sha(helper)
old_sup=supervisor.read_text();binding="HELPER_SHA='"+OLD_HELPER+"'";replacement="HELPER_SHA='"+helper_sha+"'"
assert old_sup.count(binding)==1
sup=TMP/'lanl17_metadata_supervisor_cleanup60_a4.py';assert not sup.exists();sup.write_text(old_sup.replace(binding,replacement,1))
assert sup.read_text().replace(replacement,binding,1)==old_sup
old_controls=TMP/'lanl17_metadata_supervisor_caps_a3_portable_controls.py'
controls=TMP/'lanl17_metadata_supervisor_cleanup60_a4_portable_controls.py';assert not controls.exists()
old_port=old_controls.read_text();old_sp=str(supervisor);old_hp=str(original)
assert old_port.count(old_sp)==old_port.count(old_hp)==1
controls.write_text(old_port.replace(old_sp,str(sup),1).replace(old_hp,str(helper),1))
assert controls.read_text().replace(str(sup),old_sp,1).replace(str(helper),old_hp,1)==old_port
fixture=TMP/'lanl17_metadata_supervisor_cleanup60_a4_linux_fixture.py';assert not fixture.exists()
fixture.write_bytes((TMP/'lanl17_metadata_supervisor_linux_fixture.py').read_bytes())
assert sha(fixture)=='a848ef2d5c6dba58e6814bf80d8bdf24edeb33812bda343ecf25ff6f28745b0f'
for path in (helper,sup,controls,fixture):ast.parse(path.read_text())
def cap_sites(text):
 values=[]
 for function in ast.parse(text).body:
  if isinstance(function,ast.FunctionDef) and function.name in ('prepare','finalize'):
   for n in ast.walk(function):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='run_cli':
     values.append({'function':function.name,'line':n.lineno,'cap':ast.literal_eval(n.args[4])})
 return sorted(values,key=lambda row:row['line'])
assert cap_sites(old)==cap_sites(new)
assert [row['cap'] for row in cap_sites(new)]==[3600,6000,3600,6000,14400,3600]
diff=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile=str(original),tofile=str(helper)))
patch=TMP/'lanl17-cleanup60-controls-a4-20261007.patch';patch.write_text(diff)
proof={'format':'swdb.lanl17-cleanup60-source-preparation.v1','updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'base_helper_sha256':OLD_HELPER,'base_supervisor_sha256':OLD_SUPERVISOR,
 'snapshots':{p.name:{'sha256':sha(p),'size_bytes':p.stat().st_size,'path':str(p)} for p in (helper,sup,controls,fixture,patch)},
 'only_helper_change':{'function':'dispatch','line':node.lineno,'column':node.col_offset,'old':'--kill-after=40s','new':'--kill-after=60s','decoded_literal_changes':1},
 'helper_full_byte_reversal_to69dc':True,'supervisor_HELPER_SHA_only_full_reversal_to1666':True,
 'portable_binding_only_two_paths_changed':True,'portable_wiring_cases_available':9,'portable_wiring_cases_run':0,
 'parameterized_a848_fixture_bytes_identical':True,'six_selected_metadata_caps_unchanged':cap_sites(new),
 'all_scientific_campaign_provider_defaultHOME_input_ROI_and_other_bytes_unchanged':True,
 'source_C':'f893fed400347ed23d92e917d8bde21b75e5375d','estimator_sha256':F6,'source_C_F6_untouched':True,
 'old69_166_actual_proofs_preserved':True,'fresh_original4d_smoke':'not_run','fresh_a848_fixture':'not_run',
 'future_actual_cleanup_proof_path':'/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json',
 'no_control_import_test_Store_catalog_action_ssh_or_population_execution':True,
 'scope':'Distinct future campaign cleanup grace60 administrative variant; parent review and new exact-hash actual cleanup admission required before prepare.'}
proof['identity_sha256']=dig(proof)
p=TMP/'lanl17-cleanup60-source-preparation-20261007-a4.json';p.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'helper':helper_sha,'supervisor':sha(sup),'portable_binding':sha(controls),'fixture':sha(fixture),'proof_seal':proof['identity_sha256'],'proof_file_sha256':sha(p),'metadata_cap_sites':cap_sites(new)},indent=2))
