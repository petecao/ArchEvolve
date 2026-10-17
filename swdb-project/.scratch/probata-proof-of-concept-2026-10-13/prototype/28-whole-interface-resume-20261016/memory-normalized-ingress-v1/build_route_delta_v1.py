"""Propose only SourceUnit family/producer hooks; no shared edits or Git."""
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
base=WHOLE/'production-route-v4/proposed/swdb/dx100_checked_source.py'
text=base.read_text()
assert hashlib.sha256(text.encode()).hexdigest()=='eaf7b6609a3404c31655110b1de15541246d913b14b67b53ebb3f7acbcbb89a2'
edits=[]
old='from swdb._dx100_whole import normalized_capture_ingress_v2 as ingress'
new='from swdb._dx100_whole import capture_family_dispatch_v1 as ingress'
assert text.count(old)==3
text=text.replace(old,new);edits.append({'old':old,'new':new,'count':3})
old="need(capture.get('kind') == ingress.KIND, 'unknown complete capture input roles')"
new="need(capture.get('kind') in ingress.NORMALIZED_KINDS, 'unknown complete capture input roles')"
assert text.count(old)==1;text=text.replace(old,new);edits.append({'old':old,'new':new,'count':1})
old='    from swdb._dx100_whole import runtime_projection_v3, normalized_compiler_adapter_v1\n'
new=old+'    from swdb._dx100_whole import normalized_capture_ingress_v2, memory_normalized_capture_ingress_v1\n'+\
    '    from swdb._dx100_whole import memory_normalized_compiler_adapter_v1, memory_source_preparation_v1\n'
assert text.count(old)==1;text=text.replace(old,new);edits.append({'old':old,'new':new,'count':1})
old='        ingress, closed_python_surface, role_normalized_gzip_v2, lossless_gzip_v2, runtime_projection_v3, normalized_compiler_adapter_v1)'
new='        ingress, normalized_capture_ingress_v2, memory_normalized_capture_ingress_v1,\n'+\
    '        memory_normalized_compiler_adapter_v1, memory_source_preparation_v1,\n'+\
    '        closed_python_surface, role_normalized_gzip_v2, lossless_gzip_v2, runtime_projection_v3, normalized_compiler_adapter_v1)'
assert text.count(old)==1;text=text.replace(old,new);edits.append({'old':old,'new':new,'count':1})
old="        'dx100_checked_source.py': Path(__file__), 'dx100_whole_checked.py': Path(contracts.__file__),"
new=old+"\n        'memory_capture_facts_v1.json': Path(__file__).parent / '_dx100_whole/memory_capture_facts_v1.json',"
assert text.count(old)==1;text=text.replace(old,new);edits.append({'old':old,'new':new,'count':1})
out=HERE/'integration-source';out.mkdir(exist_ok=True)
(out/'dx100_checked_source.py').write_text(text)
patch=''.join(difflib.unified_diff(base.read_text().splitlines(True),text.splitlines(True),
    fromfile='a/swdb-project/swdb/dx100_checked_source.py',tofile='b/swdb-project/swdb/dx100_checked_source.py'))
(HERE/'source-family-hook-proposal-v1.patch').write_text(patch)
(HERE/'source-family-hook-inverse-v1.json').write_text(json.dumps({'schema':'memory-source-family-hook-inverse-1',
    'base':{'path':str(base),'sha256':hashlib.sha256(base.read_bytes()).hexdigest()},'replacements':edits,
    'shared_or_frozen_source_written':False,'future_fresh_producer_basis_method_and_receipts_required':True,
    'finite_branch_files_untouched':['cbmc_adapter.py','formal_frame.py','proof_semantics.py','proof_setup.py']},sort_keys=True,indent=2)+'\n')
