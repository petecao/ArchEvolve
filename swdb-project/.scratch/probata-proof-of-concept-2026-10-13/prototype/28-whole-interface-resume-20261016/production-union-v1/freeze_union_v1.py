"""2026-10-16 ET. Freeze local source composition; no shared apply or execution."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import stat
import unittest
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
basis=[WHOLE/'production-route-v5/source-packet-v5.json',WHOLE/'finite-trace-public-v4/source-packet-v4.json',
    WHOLE/'abi-enum-repair-v1/source-packet-v1.json',WHOLE/'abi-memory-production-v1/source-packet-v1.json',
    WHOLE/'normalized-unit-envelope-v5/source-packet-v5.json',WHOLE/'abi-semantic-dependents-v1/exact-inverses-v1.json']
assert pin(basis[1])['sha256']=='2431067f155a79266ee6cd2afbe95fad2532f024632c93028462e5d8cb8bc260'
assert pin(basis[2])['sha256']=='bd81c1eb8d68968373a0bcd88cc171f542484ae34c2aace641379c60b692973f'
checked=[]
for path in basis[:4]:
    data=json.loads(path.read_bytes())
    for key in ('files','owned_files','basis_files'):
        for row in data.get(key,[]):
            selected=row.get('pin',row)
            if not all(k in selected for k in ('path','bytes','sha256')):continue
            actual=pin(Path(selected['path']));assert actual==selected,(path,key,selected['path']);checked.append(actual)
ns=runpy.run_path(str(HERE/'test_union_v1.py'),run_name='no_child_union_source_controls')
suite=unittest.defaultTestLoader.loadTestsFromTestCase(ns['Controls']);log=io.StringIO()
result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
(HERE/'pure-controls-v1.log').write_text(log.getvalue())
assert result.testsRun==8 and result.wasSuccessful() and not result.skipped
for row in checked:assert pin(Path(row['path']))==row
write(HERE/'pure-controls-v1.json',{'date':'2026-10-16 ET','tests':8,'failures':0,'errors':0,'skips':0,
    'log':pin(HERE/'pure-controls-v1.log'),'reviewed_packet_rows_rechecked':len(checked),
    'no_child_network_native_compiler_project_import_verifier_or_shared_apply':True})
files=[]
for path in sorted(HERE.rglob('*')):
    if path.is_dir() or path.name=='source-packet-v1.json':continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.suffix=='.py':ast.parse(path.read_bytes())
    files.append(pin(path))
paths=json.loads((HERE/'production-paths-and-bases-v1.json').read_bytes())['paths']
recipe=json.loads((HERE/'producer-member-recipe-v1.json').read_bytes())
packet={'schema':'coherent-ABI-semantic-and-finite-source-union-proposal-1','date':'2026-10-16 ET',
    'files':files,'basis':[pin(path) for path in basis],
    'production_paths':69,'patch':pin(HERE/'production-union-v1.patch'),
    'production_bases':pin(HERE/'production-paths-and-bases-v1.json'),
    'producer_recipe':pin(HERE/'producer-member-recipe-v1.json'),
    'prospective_producer_basis':pin(HERE/'profile/normal-producer-basis-union-v1.json'),
    'profile_builder':pin(HERE/'profile/profile_builder_union_v1.py'),'builder_inverse':pin(HERE/'builder-inverse-v1.json'),
    'root_reported_current_base':'001df353dc4aa46ab43c395997b760fb2b203ab2','final_published_producer_commit':None,
    'SourceUnit_roles':47,'TraceUnit_roles':70,'distinct_snapshot_members':79,'tests':8,
    'typed_V4_context_scope_and_finite_four_hooks_preserved':True,
    'generic_v3_remains_separate_from_semantic_v4':True,'WP_and_concurrent_unselected_files_preserved':True,
    'actual_Git_readback_shared_apply_installed_import_or_scientific_execution':False,
    'fresh_overlap_and_root_independent_source_review_before_apply_required':True,'actual_public_admission':False}
write(HERE/'source-packet-v1.json',packet)
print(json.dumps({name:pin(HERE/path) for name,path in {'packet':'source-packet-v1.json','patch':'production-union-v1.patch',
    'paths':'production-paths-and-bases-v1.json','recipe':'producer-member-recipe-v1.json','basis':'profile/normal-producer-basis-union-v1.json',
    'builder':'profile/profile_builder_union_v1.py'}.items()},sort_keys=True))
