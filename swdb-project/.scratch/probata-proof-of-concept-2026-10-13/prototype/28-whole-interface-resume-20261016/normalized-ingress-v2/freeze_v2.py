"""2026-10-16 ET: pure source packet freeze, no project or target execution."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
inverse=json.loads((HERE/'inverse-v2.json').read_bytes())
assert len(inverse['edits'])==4
restored=(HERE/'proposed/normalized_capture_ingress_v2.py').read_text()
for change in reversed(inverse['edits']):
    at=change['offset'];assert restored[at:at+len(change['new'])]==change['new']
    restored=restored[:at]+change['old']+restored[at+len(change['new']):]
assert restored.encode()==Path(inverse['predecessor']['path']).read_bytes()
files=[HERE/'INTEGRATION.md',HERE/'prepare_v2.py',HERE/'freeze_v2.py',HERE/'inverse-v2.json',HERE/'test_ingress_v2.py',
    HERE/'pure-controls-v2.log',*sorted((HERE/'proposed').glob('*.py'))]
for path in files:
    if path.suffix=='.py':ast.parse(path.read_bytes())
basis=[WHOLE/'normalized-ingress-v1/source-packet-v1.json',
    WHOLE/'normalized-ingress-v1/independent-ingress-v1-source-review-20261016.json',
    WHOLE/'normalized-ingress-v1/capture-schema-v1.json',
    WHOLE/'production-route-v3/proposed/swdb/_dx100_whole/compiler_unit_adapter_v3.py',
    WHOLE/'role-normalization-controller-v2-actual/actual-reconciliation-v2.json',
    WHOLE/'role-normalization-controller-v2-actual/root-observed-execution-v2.json']
value={'schema':'normalized-complete-tu-ingress-source-packet-2','date':'2026-10-16 ET',
    'verdict':'INERT_SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW_AND_ROOT_ADMISSION',
    'files':[pin(path) for path in files],'basis':[pin(path) for path in basis],
    'changes':'four exact ingress edits plus the isolated exact-transport adapter; all other ingress helper ASTs and three primitives unchanged',
    'controls':7,'real_legacy_consumer_function_AST_exercised_on_tiny_literal_JSON':True,
    'test_namespace_identity_substitution_and_inert_ABI_source_reads_explicit':True,
    'actual_large_AST_or_ABI_or_source_call_or_public_acceptance':False,
    'legacy_512MiB_function_and_complete_capture_preserved':True,
    'normalized_effective_limit_bytes':201326592,'legacy_internal_implementation_ceiling_bytes':536870912,
    'original_V10_duplicate_refusal_and_plain_file_extent_refusal_preserved':True,
    'shared_production_or_frozen_predecessor_edits':False}
target=HERE/'source-packet-v2.json'
with target.open('x') as stream:stream.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps(pin(target),sort_keys=True))
