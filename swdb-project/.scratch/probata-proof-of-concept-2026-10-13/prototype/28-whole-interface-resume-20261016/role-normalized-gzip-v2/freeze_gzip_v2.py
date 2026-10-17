"""Freeze inert normalized-gzip proposal; no actual stream use."""
import ast
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'role-normalization-v1'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
code=HERE/'role_normalized_gzip_v2.py';source=code.read_text();old=(OLD/'role_normalizer_v1.py').read_text();newtree=ast.parse(source);oldtree=ast.parse(old)
get=lambda tree,name:next(n for n in tree.body if getattr(n,'name',None)==name)
assert ast.dump(get(newtree,'role'),include_attributes=False)==ast.dump(get(oldtree,'role'),include_attributes=False)
body=ast.get_source_segment(source,get(newtree,'normalize'));inverse=json.loads((HERE/'normalizer-v2-inverse.json').read_bytes())
for row in reversed(inverse['edits']):assert body.count(row['after'])==row['count'];body=body.replace(row['after'],row['before'])
assert body==ast.get_source_segment(old,get(oldtree,'normalize'))
test=json.loads((HERE/'pure-controls.log').read_text().splitlines()[-1]);assert test['tests']==7 and test['failures']==test['errors']==test['skips']==0 and test['child_events']==[] and test['source_sha256']==pin(code)['sha256']
actual=WHOLE/'compiler-duplicate-census-v3-actual/actual-reconciliation-v3.json';assert pin(actual)['sha256']=='8fa1dc683271c9c51ec5d2b8ccf0a2d8a7b76a868e5589d4b0d8d3b68684de24'
data={'schema':'paired-type-normalized-gzip-source-packet-2','date':'2026-10-16 ET','status':'frozen SOURCE ONLY; independent review and future physical controller/root admission required',
    'files':[pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name!='source-packet-v2.json'],
    'predecessor_packet':pin(OLD/'source-packet-v1.json'),'predecessor_source':pin(OLD/'role_normalizer_v1.py'),
    'actual_complete_census_extent_refusal':pin(actual),'base_grammar':pin(WHOLE/'streaming-minify-v1/strict_minify_v2.py'),
    'gzip_codec':pin(WHOLE/'streaming-minify-v1/lossless_gzip_v2.py'),'validation':test,'role_AST_exact':True,'normalizer_function_inverse_exact':True,
    'prospective_expanded_normalized_limit_bytes':201326592,'physical_gzip_limit_bytes':134217728,'aggregate_root_limit_bytes':268435456,
    'future_controller_owes_aggregate_quota_physical_runtime_and_resource_gates':True,'actual_TU_bytes_read':False,
    'actual_normalized_artifact_written':False,'normalized_AST_source_ABI_or_public_admission':False,'original_V10_status_unchanged':True,
    'plain_V1_extent_refusal_preserved':True,'actual_DOM_cost_or_success_inferred':False}
path=HERE/'source-packet-v2.json';path.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n');print(json.dumps({'packet':pin(path),'code':pin(code)}))
