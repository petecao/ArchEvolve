"""Compiler-free successor authoring only; never actual AST normalization."""
import ast
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'role-normalization-v1'
origin=OLD/'role_normalizer_v1.py';raw=origin.read_bytes();assert hashlib.sha256(raw).hexdigest()=='e0aeb03bcdbe59dee9f79495d822623bfcefc7184317abd7ae001a0ff212d9fe'
source=raw.decode();tree=ast.parse(source);edits=[]
# Preserve the plain-file V1 helper as historical source; it is not the V2 API.
body=ast.get_source_segment(source,next(n for n in tree.body if getattr(n,'name',None)=='normalize'))
def edit(before,after,count=1):
    global body
    assert body.count(before)==count,(before,body.count(before));body=body.replace(before,after);edits.append({'before':before,'after':after,'count':count})
edit("output_bytes+len(value)<=134217728,'normalized retained file cap exceeded'", "output_bytes+len(value)<=201326592,'normalized expanded token stream cap exceeded'")
edit('self.normalized_bytes<=134217728\n            group_rows=', 'self.normalized_bytes<=201326592\n            group_rows=')
edit('prospective_role_normalization_eligible','role_normalization_and_expanded_cap_eligible',2)
edit('prospective_normalization_refused','expanded_role_transport_refused')
edit('prospective_normalized_file_cap_fit','plain_normalized_file_cap_fit')
edit("schema='llvm22-original-tu-role-transport-1',normalized_AST_written=True,normalized_AST_admitted=False", "schema='llvm22-original-tu-role-expanded-2',normalized_expanded_stream_written=True,normalized_uncompressed_file_written=False,normalized_AST_admitted=False")
prefix=source[:source.index('def normalize(')]
prefix=prefix.replace('INERT prospective paired-Type lossless transport primitives.','INERT paired-Type normalized-gzip transport primitives.')
suffix=(HERE/'gzip_fragment_v2.py').read_text()
(HERE/'role_normalized_gzip_v2.py').write_text(prefix+body+'\n\n'+suffix)
restored=body
for row in reversed(edits):assert restored.count(row['after'])==row['count'];restored=restored.replace(row['after'],row['before'])
assert restored==ast.get_source_segment(source,next(n for n in tree.body if getattr(n,'name',None)=='normalize'))
(HERE/'normalizer-v2-inverse.json').write_text(json.dumps({'origin':{'path':str(origin),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
    'normalizer_function_exact_inverse':True,'role_AST_unchanged':True,'edits':edits,'actual_executed':False},sort_keys=True,indent=2)+'\n')
print('Authored normalized-gzip primitives only.')
