"""Freeze exact source-only finalization repair; no actual controller run."""
import ast
import base64
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'role-normalization-controller-v1'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def doc(path):return json.loads(path.read_bytes())
prior=doc(OLD/'source-packet-v1.json');assert pin(OLD/'source-packet-v1.json')['sha256']=='e79b5f08dde0be66b2ed1baec2feac30d9fe63ece45d1566700c895d2ddce9d1'
for row in prior['files']+prior['inputs']:assert pin(Path(row['path']))==row
inverse=doc(HERE/'settled-v2-inverse.json');template=(HERE/'controller_template.py').read_text()
for row in reversed(inverse['edits']):assert template.count(row['after'])==1;template=template.replace(row['after'],row['before'],1)
assert template==(OLD/'controller_template.py').read_text()
new=(HERE/'normalization_controller_v2.py').read_text();old=(OLD/'normalization_controller_v1.py').read_text()
def literal(source,name):
    return ast.literal_eval(next(n.value for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
new=new.replace(literal(new,'POLICY_B64'),literal(old,'POLICY_B64'),1)
for row in reversed(inverse['edits']):assert new.count(row['after'])==1;new=new.replace(row['after'],row['before'],1)
assert new==old
p=doc(HERE/'source_policy_v2.json');oldp=doc(OLD/'source_policy_v1.json');restored=dict(p,output_root=p['output_root'].replace('-v2','-v1'));assert restored==oldp
cmd=doc(HERE/'command_v2.json');oldcmd=doc(OLD/'command_v1.json');changed={'stdin','bootstrap','source_policy','python_argv','remote_argv','remote_shell_command'}
assert {k:v for k,v in cmd.items() if k not in changed}=={k:v for k,v in oldcmd.items() if k not in changed}
test=json.loads((HERE/'pure-controls.log').read_text().splitlines()[-1]);assert test['tests']==9 and test['failures']==test['errors']==test['skips']==0 and test['child_events']==[]
assert test['entry_sha256']==pin(HERE/'normalization_controller_v2.py')['sha256'] and test['actual_controller_bootstrap_or_resource_limits_executed'] is False
files=[pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name!='source-packet-v2.json']
packet={'schema':'passive-transform-settled-publication-source-packet-2','date':'2026-10-16 ET','status':'frozen SOURCE ONLY; new reviews/root actual-write admission required',
    'files':files,'inputs':prior['inputs'],'predecessor':pin(OLD/'source-packet-v1.json'),'predecessor_pin_rows_unchanged':len(prior['files']+prior['inputs']),
    'validation':test,'exact_template_inverse':True,'exact_rendered_entry_inverse_after_derived_policy':True,'policy_JSON_inverse':'only output_root v2 to v1',
    'command_changed_keys':sorted(changed),'limits':p['limits'],'late_failure_complete_result_requires_root_observed_zero_exit':True,
    'actual_controller_bootstrap_remote_or_normalization_executed':False,'original_capture_source_ABI_or_public_admission':False}
path=HERE/'source-packet-v2.json';path.write_text(json.dumps(packet,sort_keys=True,indent=2)+'\n');print(json.dumps({'packet':pin(path),'entry':pin(HERE/'normalization_controller_v2.py'),
    'policy':pin(HERE/'source_policy_v2.json'),'command':pin(HERE/'command_v2.json')}))
