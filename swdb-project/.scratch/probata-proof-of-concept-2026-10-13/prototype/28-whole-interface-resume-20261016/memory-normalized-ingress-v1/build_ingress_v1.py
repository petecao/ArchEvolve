"""Compose exact reused physical utilities with the distinct memory gates."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
old=WHOLE/'normalized-ingress-v2/proposed/normalized_capture_ingress_v2.py'
text=old.read_text();wanted=('need','exact','same_bytes','stream_stable','make_dependencies','physical_runtime')
nodes={n.name:ast.get_source_segment(text,n) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
adapter=HERE/'proposed/memory_normalized_compiler_adapter_v1.py'
header='''"""Closed G642 memory-family source ingress. No compiler/native/proof execution."""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
from swdb import dx100_checked_source as source
from swdb._dx100_whole import lossless_gzip_v2 as codec
from swdb._dx100_whole import role_normalized_gzip_v2 as normalizer
from swdb._dx100_whole import closed_python_surface as closed
from swdb._dx100_whole import memory_normalized_compiler_adapter_v1 as memory_compiler
KIND='complete-memory-original-tu-paired-type-gzip-1'
COMMIT='2baf722fdaa6cba24b859eae3172a6f597417d72'
SOURCE_SHA='55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'
EXPANDED=201326592
FILE=134217728
TOTAL=268435456
CODEC_SHA='aae4a423216fcdca6b16f9eba370ec4c83615ed61ae79dd4b3d09e3bed1702ef'
NORMALIZER_SHA='6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941'
CLOSED_SHA='748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af'
'''+"MEMORY_COMPILER_SHA='"+hashlib.sha256(adapter.read_bytes()).hexdigest()+"'\n"
result=header+'\n\n'+'\n\n'.join(nodes[name] for name in wanted)+'\n\n'+(HERE/'ingress_body_v1.py').read_text()+'\n'
ast.parse(result)
(HERE/'proposed/memory_normalized_capture_ingress_v1.py').write_text(result)
(HERE/'shared-utility-inverse-v1.json').write_text(json.dumps({'source':str(old),'unchanged_functions':{name:hashlib.sha256(nodes[name].encode()).hexdigest() for name in wanted},
    'no_first_source_policy_result_or_stream_used_as_memory_authority':True},sort_keys=True,indent=2)+'\n')
print(json.dumps({'entry_bytes':len(result.encode()),'sha256':hashlib.sha256(result.encode()).hexdigest()}))
