"""2026-10-16 ET: mechanical source successor only, no project execution."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
V1=HERE.parent/'normalized-ingress-v1'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
source=V1/'proposed/normalized_capture_ingress_v1.py'
assert pin(source)['sha256']=='ee290e72feedf9b24d9bca299a2be7686ec217d1312bf6b99df651b534ed157d'
text=source.read_text();changes=[]
def replace(old,new):
    global text
    assert text.count(old)==1
    at=text.index(old);text=text[:at]+new+text[at+len(old):]
    changes.append({'offset':at,'old':old,'new':new})
replace('from swdb._dx100_whole import closed_python_surface as closed\n',
    'from swdb._dx100_whole import closed_python_surface as closed\nfrom swdb._dx100_whole import normalized_compiler_adapter_v1 as normalized_compiler\n')
wrapper=pin(HERE/'proposed/normalized_compiler_adapter_v1.py')
replace("CLOSED_SHA='748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af'\n",
    "CLOSED_SHA='748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af'\nNORMALIZED_COMPILER_SHA='"+wrapper['sha256']+"'\n")
replace("for module,expected in ((normalizer,NORMALIZER_SHA),(codec,CODEC_SHA),(closed,CLOSED_SHA)):",
    "for module,expected in ((normalizer,NORMALIZER_SHA),(codec,CODEC_SHA),(closed,CLOSED_SHA),\n        (normalized_compiler,NORMALIZED_COMPILER_SHA),(source.compiler,normalized_compiler.LEGACY_SHA)):")
# The new wrapper is an actual producer-manifest input. Its legacy dependency
# is the same source.compiler module already in the existing closure/read set.
replace("    prepared=source.compiler.prepare_unit(source.binder.__dict__,full_tu_raw=full_tu,abi_raw=reads.selected(original['abi']),",
    "    need(normalized_compiler.legacy is source.compiler,'normalized adapter must use the same unchanged legacy compiler module')\n"
    "    prepared=normalized_compiler.prepare_unit(source.binder.__dict__,transport_kind=KIND,full_tu_raw=full_tu,abi_raw=reads.selected(original['abi']),")
target=HERE/'proposed/normalized_capture_ingress_v2.py'
target.write_text(text);ast.parse(text)
restored=text
for row in reversed(changes):
    at=row['offset'];assert restored[at:at+len(row['new'])]==row['new'];restored=restored[:at]+row['old']+restored[at+len(row['new']):]
assert restored.encode()==source.read_bytes()
for name in ('closed_python_surface.py','lossless_gzip_v2.py','role_normalized_gzip_v2.py'):
    (HERE/'proposed'/name).write_bytes((V1/'proposed'/name).read_bytes())
value={'date':'2026-10-16 ET','schema':'normalized-ingress-v2-inverse-1','predecessor':pin(source),'successor':pin(target),
    'edits':changes,'exact_predecessor_reconstructed':True,'legacy_adapter_unchanged':pin(HERE.parent/'production-route-v3/proposed/swdb/_dx100_whole/compiler_unit_adapter_v3.py'),
    'legacy_complete_capture_unchanged':pin(V1/'legacy_complete_capture.txt'),'new_wrapper':pin(HERE/'proposed/normalized_compiler_adapter_v1.py'),
    'actual_ingress_or_compiler_or_native_or_proof':False}
(HERE/'inverse-v2.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps(pin(target),sort_keys=True))
