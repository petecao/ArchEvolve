"""2026-10-16 ET. Pure source freeze; no import of proposed/project modules."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
POC=WHOLE.parents[1]
def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,value):
    with (HERE/name).open('x') as stream:stream.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
for source,name,expected in [
    (WHOLE/'role-normalized-gzip-v2/role_normalized_gzip_v2.py','role_normalized_gzip_v2.py','6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941'),
    (WHOLE/'streaming-minify-v1/lossless_gzip_v2.py','lossless_gzip_v2.py','aae4a423216fcdca6b16f9eba370ec4c83615ed61ae79dd4b3d09e3bed1702ef')]:
    data=source.read_bytes();assert hashlib.sha256(data).hexdigest()==expected
    with (HERE/'proposed'/name).open('xb') as stream:stream.write(data)
legacy=WHOLE/'production-route-v3/proposed/swdb/dx100_checked_source.py'
legacy_text=legacy.read_text();tree=ast.parse(legacy_text)
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='complete_capture')
function_text=ast.get_source_segment(legacy_text,function)
assert hashlib.sha256(function_text.encode()).hexdigest()=='cdfd56f5503d4068abe31037a2d121e5a81bfdd86889676a4563b25f37a94241'
with (HERE/'legacy_complete_capture.txt').open('x') as stream:stream.write(function_text)
native=WHOLE/'linux_native86_entry_v4.py';old=next(n for n in ast.parse(native.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='make_dependencies')
proposed=HERE/'proposed/normalized_capture_ingress_v1.py';new=next(n for n in ast.parse(proposed.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='make_dependencies')
assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
save('origin-receipt-v1.json',{'date':'2026-10-16 ET','legacy_module':pin(legacy),'legacy_function':pin(HERE/'legacy_complete_capture.txt'),
    'legacy_is_callthrough_only':True,'dependency_parser_origin':pin(native),
    'dependency_parser_AST_sha256':hashlib.sha256(ast.dump(new,include_attributes=False).encode()).hexdigest(),
    'physical_runtime':'same native source recipe, extended with tracked regular-file pins and full current pre/post membership checks',
    'closed_python_surface_original':pin(WHOLE.parent/'28-public-memory-trace-resume-20261016/closed_python_surface.py'),
    'closed_python_surface_copy':pin(HERE/'proposed/closed_python_surface.py'),
    'project_or_proposed_module_imported_or_actual_records_consumed':False})
files=[HERE/'PLAN.md',HERE/'capture-schema-v1.json',HERE/'test_ingress_v1.py',HERE/'pure-controls-v1.log',
    HERE/'freeze_v1.py',HERE/'origin-receipt-v1.json',HERE/'legacy_complete_capture.txt',*sorted((HERE/'proposed').glob('*.py'))]
for path in files:
    if path.suffix=='.py':ast.parse(path.read_bytes())
basis=[WHOLE/'production-route-v3/source-packet-v3.json',WHOLE/'role-normalization-controller-v2/source-packet-v2.json',
    WHOLE/'role-normalized-gzip-v2/source-packet-v2.json',WHOLE/'role-normalization-controller-v2-actual/actual-reconciliation-v2.json',
    WHOLE/'role-normalization-controller-v2-actual/root-observed-execution-v2.json',
    POC/'evidence/t28-role-normalization-controller-v2-root-admission-20261016.json']
save('source-packet-v1.json',{'date':'2026-10-16 ET','schema':'normalized-complete-tu-ingress-source-packet-1',
    'verdict':'INERT_SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW_AND_ROOT_ADMISSION','files':[pin(p) for p in files],'basis':[pin(p) for p in basis],
    'controls':9,'actual_transform_available':True,'actual_ingress_complete_TU_ABI_source_call_or_public_acceptance':False,
    'scope':'new isolated proposal only; no shared production or predecessor mutation',
    'preserves_original_V10_duplicate_refusal_and_plain_extent_refusal':True})
print(json.dumps(pin(HERE/'source-packet-v1.json'),sort_keys=True))
