"""Pin pure V2 packet only; no compiler, remote, actual reader or bootstrap."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'compiler-duplicate-census-v1'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def doc(path):return json.loads(path.read_bytes())
def save(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
prior=doc(OLD/'complete-census-source-packet-v1.json')
assert pin(OLD/'complete-census-source-packet-v1.json')['sha256']=='ec60c53d8f872bdeae24d5951ac70460bc25ecb640cc3e95e8b9fa171a88498b'
for row in prior['files']+prior['inputs']+prior['primary_sources']+[prior['prior_actual_first_duplicate']]:assert pin(Path(row['path']))==row
inverse=doc(HERE/'census-v2-inverse.json');restored=(HERE/'complete_duplicate_census_v2.py').read_text()
for row in reversed(inverse['edits']):assert restored.count(row['after'])==1;restored=restored.replace(row['after'],row['before'],1)
assert restored==(OLD/'complete_duplicate_census_v1.py').read_text()
boot_inverse=doc(HERE/'bootstrap-v3-inverse.json');restored=(HERE/'readonly_bootstrap_v3.py').read_text()
for row in reversed(boot_inverse['edits']):assert restored.count(row['after'])==1;restored=restored.replace(row['after'],row['before'],1)
assert restored==(OLD/'readonly_bootstrap_v2.py').read_text()
old_command=doc(OLD/'complete-census-command-v1.json');new_command=doc(HERE/'complete-census-command-v2.json')
changed={'bootstrap','stdin','python_argv','remote_argv','remote_shell_command','predecessor_command','scope'}
assert {k:v for k,v in old_command.items() if k not in changed}=={k:v for k,v in new_command.items() if k not in changed}
for key in ('python_argv','remote_argv'):
    assert [restored if item==(HERE/'readonly_bootstrap_v3.py').read_text() else item for item in new_command[key]]==old_command[key]
c=doclog= json.loads((HERE/'pure-census-controls.log').read_text().splitlines()[-1]);b=json.loads((HERE/'pure-bootstrap-controls.log').read_text().splitlines()[-1])
assert c['tests']==15 and b['tests']==4
for value in (c,b):assert value['failures']==value['errors']==value['skips']==0
assert c['child_events']==[] and c['source_sha256']==pin(HERE/'complete_duplicate_census_v2.py')['sha256']
assert b['bootstrap_executed'] is False and b['resource_limits_or_actual_reader_executed'] is False and b['bootstrap_sha256']==pin(HERE/'readonly_bootstrap_v3.py')['sha256']
names=('complete_duplicate_census_v2.py','prepare_census_v2.py','prepare_controls_v2.py','freeze_census_v2.py','test_complete_census_v2.py','test_readonly_bootstrap_v3.py',
    'pure-census-controls.log','pure-bootstrap-controls.log','pure-census-controls-inherited-display-red.log','readonly_bootstrap_v3.py','census-v2-inverse.json','bootstrap-v3-inverse.json','complete-census-command-v2.json','PLAN.md')
save('complete-census-source-packet-v2.json',{'date':'2026-10-16 ET','schema':'complete-census-source-packet-2',
    'status':'frozen SOURCE ONLY; new independent review and root admission required','files':[pin(HERE/n) for n in names],
    'predecessor':pin(OLD/'complete-census-source-packet-v1.json'),'predecessor_files_rehashed_unchanged':len(prior['files']+prior['inputs']+prior['primary_sources'])+1,
    'inputs':prior['inputs'],'primary_sources':prior['primary_sources'],'prior_actual_first_duplicate':prior['prior_actual_first_duplicate'],
    'validation':{'census':c,'bootstrap':b},'source_exact_inverse':True,'bootstrap_exact_inverse':True,'command_changed_keys':sorted(changed),
    'stdout_complete_line_limit_bytes':32768,'display_rows_may_be_omitted_with_full_digest_and_counts':True,
    'retained_AST_or_normalized_writes':False,'original_raw_limit_bytes':2147483648,'hash_only_prospective_token_limit_bytes':2149580800,
    'actual_capture_retained_caps_unchanged':True,'selected_binary_to_release_source_attestation_established':False,
    'arbitrary_duplicate_keys_admitted':False,'public_source_ABI_or_proof_admission':False,'actual_census_executed':False,'old_once_only_admission_reused':False})
print(json.dumps({'packet':pin(HERE/'complete-census-source-packet-v2.json'),'code':pin(HERE/'complete_duplicate_census_v2.py'),'bootstrap':pin(HERE/'readonly_bootstrap_v3.py'),'command':pin(HERE/'complete-census-command-v2.json')}))
