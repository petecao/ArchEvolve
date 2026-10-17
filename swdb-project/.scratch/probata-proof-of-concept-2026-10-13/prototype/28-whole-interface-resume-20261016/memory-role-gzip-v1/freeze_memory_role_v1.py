"""2026-10-16 ET: pure source freeze, no target imports or execution."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
inverse=json.loads((HERE/'controller-inverse-v1.json').read_bytes())
text=(HERE/'controller_template_v1.py').read_text()
for change in reversed(inverse['edits']):
    at=change['offset'];assert text[at:at+len(change['new'])]==change['new'];text=text[:at]+change['old']+text[at+len(change['new']):]
assert text.encode()==Path(inverse['predecessor_template']['path']).read_bytes()
def functions(path):return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(path.read_bytes()).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
old=functions(Path(inverse['predecessor_template']['path']));new=functions(HERE/'controller_template_v1.py')
unchanged=[name for name in old if name!='main'];assert all(old[name]==new[name] for name in unchanged)
command=json.loads((HERE/'command_v1.json').read_bytes());policy=json.loads((HERE/'source_policy_v1.json').read_bytes())
assert policy['expected_duplicate_count'] is None and policy['expected_normalized_output_identities'] is None
assert command['stdin']==pin(HERE/'memory_role_controller_v1.py') and command['bootstrap']==pin(HERE/'bootstrap_v1.py')
assert command['source_policy']==pin(HERE/'source_policy_v1.json')
files=[HERE/name for name in ('PLAN.md','prepare_memory_role_v1.py','freeze_memory_role_v1.py','controller_template_v1.py',
    'memory_role_controller_v1.py','source_policy_v1.json','bootstrap_v1.py','command_v1.json','controller-inverse-v1.json',
    'test_memory_role_v1.py','pure-controls-v1.log')]
for path in files:
    if path.suffix=='.py':ast.parse(path.read_bytes())
basis=[WHOLE/'role-normalization-controller-v2/source-packet-v2.json',
    WHOLE/'role-normalized-gzip-v2/source-packet-v2.json',WHOLE/'role-normalized-gzip-v2/role_normalized_gzip_v2.py',
    WHOLE/'streaming-minify-v1/strict_minify_v2.py',WHOLE/'streaming-minify-v1/lossless_gzip_v2.py',
    WHOLE/'compiler-memory-capture-v1/memory-capture-source-packet-v1.json',
    WHOLE/'compiler-memory-capture-v1-actual/actual-observation-reconciliation-v2.json',
    WHOLE/'compiler-memory-capture-v1-actual/closure-stdout-v1.json']
value={'date':'2026-10-16 ET','schema':'memory-observation-role-gzip-source-packet-1',
    'status':'INERT_SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW_AND_NEW_ROOT_ONCE_ADMISSION',
    'files':[pin(path) for path in files],'basis':[pin(path) for path in basis],
    'exact_template_inverse_edits':len(inverse['edits']),'unchanged_predecessor_helper_ASTs':unchanged,
    'known_physical_inputs':len(policy['physical_inputs']),'fixed_new_output_files':14,'pure_controls':10,
    'single_complete_normalization_census_pass_plus_full_inverse':True,'preliminary_actual_census_required':False,
    'expected_duplicate_count':None,'expected_normalized_output_identities':None,
    'preserves_original_successful_G642_compiler_observation_only':True,
    'copies_V10_duplicate_failure_premise':False,'actual_transform_SSH_compiler_native_verifier_or_source_call_admission':False,
    'future_distinct_memory_source_ingress_required':True,'shared_production_or_predecessor_mutations':False}
target=HERE/'source-packet-v1.json'
with target.open('x') as stream:stream.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps(pin(target),sort_keys=True))
