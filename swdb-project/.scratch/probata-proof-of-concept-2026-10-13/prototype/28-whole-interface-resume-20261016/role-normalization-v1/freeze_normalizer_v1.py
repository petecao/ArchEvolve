"""Freeze inert normalization proposal only; no actual normalized input/output."""
import ast
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
origin=WHOLE/'compiler-duplicate-census-v3/complete_duplicate_census_v3.py';raw=origin.read_text();tree=ast.parse(raw)
code=HERE/'role_normalizer_v1.py';source=code.read_text();new=ast.parse(source)
get=lambda t,n:next(x for x in t.body if getattr(x,'name',None)==n)
assert ast.dump(get(tree,'role'),include_attributes=False)==ast.dump(get(new,'role'),include_attributes=False)
body=ast.get_source_segment(source,get(new,'normalize'));inverse=json.loads((HERE/'exact-census-origin-v1.json').read_bytes())
for row in reversed(inverse['edits']):assert body.count(row['after'])==1;body=body.replace(row['after'],row['before'],1)
assert body==ast.get_source_segment(raw,get(tree,'census'))
test=json.loads((HERE/'pure-controls.log').read_text().splitlines()[-1]);assert test['tests']==9 and test['failures']==test['errors']==test['skips']==0 and test['child_events']==[] and test['source_sha256']==pin(code)['sha256']
files=[pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name!='source-packet-v1.json']
value={'schema':'prospective-paired-type-normalizer-source-1','date':'2026-10-16 ET','status':'frozen compiler-free SOURCE ONLY; independent review/actual census eligibility/root admission required',
    'files':files,'origin_census':pin(origin),'base_grammar':pin(WHOLE/'streaming-minify-v1/strict_minify_v2.py'),
    'complete_census_packet':pin(WHOLE/'compiler-duplicate-census-v3/complete-census-source-packet-v3.json'),
    'validation':test,'role_AST_exact':True,'census_function_inverse_exact':True,'actual_TU_bytes_read':False,
    'actual_normalized_AST_written':False,'normalized_AST_or_source_ABI_or_public_admission':False,
    'limits':{'normalized_file_bytes':134217728,'normalized_write_bytes':65536,'complete_manifest_bytes':33554432,'manifest_rows':100000,'manifest_row_bytes':4096},
    'aggregate_retained_quota_enforcement_is_future_controller_obligation':True,'generic_Type_and_specialized_Type_values_both_preserved':True,
    'original_and_normalized_token_identity_distinct':True,'V10_original_status_unchanged':True,'source_to_selected_binary_attestation_established':False}
path=HERE/'source-packet-v1.json';path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');print(json.dumps({'packet':pin(path),'code':pin(code)}))
