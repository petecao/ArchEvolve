"""Source/test/bootstrap/command preparation only; no remote or reader call."""
import hashlib
import json
from pathlib import Path
import shlex
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'compiler-duplicate-diagnostic-v1';POC=WHOLE.parents[1]
def pin(path):
 raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
payload=pin(HERE/'complete_duplicate_census_v1.py');boot=(OLD/'readonly_bootstrap_v1.py').read_text();edits=[]
for old,new in [('11892',str(payload['bytes']+1)),('11891',str(payload['bytes'])),('fc301fccbc15d345ed34add46a8c1b9072c619b1a23b61efbfdaa1602b0cf179',payload['sha256']),('<reviewed-duplicate-metadata-stdin>','<reviewed-complete-duplicate-census-stdin>')]:
 assert boot.count(old)==1;edits.append({'old':old,'new':new});boot=boot.replace(old,new,1)
(HERE/'readonly_bootstrap_v2.py').write_text(boot)
restored=boot
for edit in reversed(edits):assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'],1)
assert restored==(OLD/'readonly_bootstrap_v1.py').read_text()
save('bootstrap-inverse-v1.json',{'predecessor':pin(OLD/'readonly_bootstrap_v1.py'),'successor':pin(HERE/'readonly_bootstrap_v2.py'),'edits':edits,'exact_inverse':True,'caps_audit_environment_unchanged':True})
prior=json.loads((OLD/'duplicate-diagnostic-command-v1.json').read_bytes());python_argv=list(prior['python_argv']);python_argv[4]=boot
env=prior['closed_environment'];remote=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','120s','/usr/bin/env','-i',*[k+'='+v for k,v in env.items()],*python_argv]
command={key:prior[key] for key in ('closed_environment','local_transport_timeout_seconds','outer_timeout_seconds','kill_grace_seconds','address_space_bytes','CPU_seconds','internal_wall_seconds','stdout_bytes','selected_policy','selected_python_physical_pin','selected_libz_physical_pins')}
command.update(date='2026-10-16 ET',scope='SOURCE ONLY: complete retained-TU duplicate census; new root admission required',bootstrap=pin(HERE/'readonly_bootstrap_v2.py'),stdin=payload,python_argv=python_argv,
 remote_argv=remote,remote_shell_command=shlex.join(remote),stdin_byte_fidelity=True,remote_staging_or_raw_mutations=False,actual_executed=False,prior_once_only_admission_reused=False,
 root_transport_tools_TCB=['/usr/bin/timeout','/usr/bin/env','SSH transport'],predecessor_command=pin(OLD/'duplicate-diagnostic-command-v1.json'))
save('complete-census-command-v1.json',command)
report=json.loads((HERE/'pure-census-controls.log').read_text().splitlines()[-1]);assert report['tests']==12 and report['failures']==report['errors']==report['skips']==0 and report['child_events']==[] and report['source_sha256']==payload['sha256']
validation={'census':report};bl=HERE/'pure-bootstrap-controls.log'
if bl.exists():
 b=json.loads(bl.read_text().splitlines()[-1]);assert b['tests']==4 and b['failures']==b['errors']==b['skips']==0 and b['bootstrap_sha256']==pin(HERE/'readonly_bootstrap_v2.py')['sha256'];validation['bootstrap']=b
files=[pin(HERE/name) for name in ('complete_duplicate_census_v1.py','census_parser_fragment_v1.py','author_census_v1.py','test_complete_census_v1.py','pure-census-controls.log','PLAN.md','readonly_bootstrap_v2.py','bootstrap-inverse-v1.json','complete-census-command-v1.json','prepare_census_packet_v1.py')]
if bl.exists():files += [pin(HERE/'test_readonly_bootstrap_v2.py'),pin(bl)]
primary=[pin(path) for path in sorted((HERE/'primary').iterdir()) if path.is_file()]
inputs=[pin(WHOLE/'streaming-minify-v1'/name) for name in ('strict_minify_v2.py','lossless_gzip_v2.py')]
inputs += [pin(WHOLE/'compiler-capture-v10'/name) for name in ('linux_compiler_capture_v10.py','linux_compiler_capture_policy_v10.json','linux_compiler_capture_command_v10.json')]
save('complete-census-source-packet-v1.json',{'date':'2026-10-16 ET','status':'SOURCE ONLY; complete ordered-pair census and prospective role transport hash; no actual run/admission',
 'files':files,'inputs':inputs,'primary_sources':primary,'prior_actual_first_duplicate':pin(OLD/'actual-reconciliation-v1.json'),'validation':validation,
 'retained_AST_or_normalized_writes':False,'original_raw_limit_bytes':2147483648,'hash_only_prospective_token_limit_bytes':2149580800,
 'actual_capture_retained_caps_unchanged':True,'selected_binary_to_release_source_attestation_established':False,
 'arbitrary_duplicate_keys_admitted':False,'public_source_ABI_or_proof_admission':False})
print(json.dumps(pin(HERE/'complete-census-source-packet-v1.json')))
