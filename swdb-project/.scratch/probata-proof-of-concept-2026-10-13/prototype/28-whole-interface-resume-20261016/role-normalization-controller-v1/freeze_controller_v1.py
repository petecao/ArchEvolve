"""Freeze source proposal only; no actual controller or bootstrap execution."""
import ast
import base64
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
source=(HERE/'normalization_controller_v1.py').read_bytes();ast.parse(source);ast.parse((HERE/'bootstrap_v1.py').read_bytes())
test=json.loads((HERE/'pure-controls.log').read_text().splitlines()[-1]);assert test['tests']==7 and test['failures']==test['errors']==test['skips']==0 and test['child_events']==[]
assert test['entry_sha256']==hashlib.sha256(source).hexdigest() and test['actual_controller_bootstrap_or_resource_limits_executed'] is False
policy=json.loads((HERE/'source_policy_v1.json').read_bytes());command=json.loads((HERE/'command_v1.json').read_bytes())
assert command['stdin']==pin(HERE/'normalization_controller_v1.py') and command['bootstrap']==pin(HERE/'bootstrap_v1.py') and command['source_policy']==pin(HERE/'source_policy_v1.json')
files=[pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name!='source-packet-v1.json']
inputs=[pin(WHOLE/'role-normalized-gzip-v2/source-packet-v2.json'),pin(WHOLE/'role-normalized-gzip-v2/role_normalized_gzip_v2.py'),
    pin(WHOLE/'compiler-duplicate-census-v3-actual/actual-census-stdout-v3.json'),pin(WHOLE/'compiler-duplicate-census-v3-actual/actual-reconciliation-v3.json'),
    pin(WHOLE/'streaming-minify-v1/strict_minify_v2.py'),pin(WHOLE/'streaming-minify-v1/lossless_gzip_v2.py')]
value={'schema':'passive-paired-type-transform-controller-source-packet-1','date':'2026-10-16 ET','status':'frozen SOURCE ONLY; independent review and new root actual-write admission required',
    'files':files,'inputs':inputs,'validation':test,'selected_remote_input_pin_count':len(policy['physical_inputs']),'limits':policy['limits'],
    'scope':'byte-transform only; no accepted compiler capture/source/call/ABI/proof/public/current0.2/full28 claim',
    'original_V10_refusal_and_plain_file_extent_refusal_preserved':True,'actual_normalized_artifacts_written':False,
    'prior_once_only_census_approval_reused':False,'actual_controller_bootstrap_or_resource_limits_executed':False}
path=HERE/'source-packet-v1.json';path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');print(json.dumps({'packet':pin(path),'entry':pin(HERE/'normalization_controller_v1.py'),
    'policy':pin(HERE/'source_policy_v1.json'),'command':pin(HERE/'command_v1.json')}))
