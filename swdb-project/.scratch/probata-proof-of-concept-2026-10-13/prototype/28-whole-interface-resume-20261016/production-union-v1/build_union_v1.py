"""2026-10-16 ET. Compose frozen source proposals only; no shared apply or Git."""
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import types
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;PROJECT=WHOLE.parents[3]
BASE=WHOLE/'production-route-v4';FINITE=WHOLE/'finite-trace-public-v4';ABI=WHOLE/'abi-semantic-dependents-v1'
OUT=HERE/'proposed';ROOT_COMMIT='001df353dc4aa46ab43c395997b760fb2b203ab2'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
assert PROJECT.name=='swdb-project'
base_table=json.loads((BASE/'production-paths-and-bases-v4.json').read_bytes())['paths']
assert len(base_table)==50
selected={};origins={};shared={}
for row in base_table:
    relative=row['path'].removeprefix('swdb-project/');source=Path(row['proposal']['path'])
    assert pin(source)==row['proposal']
    target=PROJECT/relative;current=pin(target)
    assert current['bytes']==row['proposal']['bytes'] and current['sha256']==row['proposal']['sha256'],relative
    selected[relative]=source;origins[relative]='reviewed coherent V5 byte-identical V4 production';shared[relative]=current
# The four finite hooks must still have their exact reviewed shared bases.
for name,row in json.loads((FINITE/'hook-inverse.json').read_bytes())['files'].items():
    assert pin(PROJECT/'swdb'/name)['sha256']==row['base_sha256'],name
for source in sorted((FINITE/'proposed').rglob('*')):
    if source.is_file():
        relative=source.relative_to(FINITE/'proposed').as_posix();selected[relative]=source;origins[relative]='reviewed finite V4'
for source in sorted((ABI/'proposed').rglob('*')):
    if source.is_file():
        relative=source.relative_to(ABI/'proposed').as_posix()
        selected[relative]=source;origins[relative]='explicit semantic ABI dependency over typed V4 source'
for relative,source in selected.items():
    target=OUT/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    if relative not in shared:shared[relative]=pin(PROJECT/relative) if (PROJECT/relative).is_file() else None
# No selected coherent base is dropped; finite hooks retain complete byte identity.
assert set(row['path'].removeprefix('swdb-project/') for row in base_table)<=set(selected)
for name in ('cbmc_adapter.py','formal_frame.py','proof_semantics.py','proof_setup.py'):
    assert (OUT/'swdb'/name).read_bytes()==(FINITE/'proposed/swdb'/name).read_bytes()
assert (OUT/'swdb/_dx100_finite/context_rule_scope_v1.py').read_bytes()==(FINITE/'proposed/swdb/_dx100_finite/context_rule_scope_v1.py').read_bytes()

def need(ok,message):
    if not ok:raise ValueError(message)
def projected_producer_paths(source_path,*,finite=False,source_paths=None):
    """Execute only the real producer_paths leaf without project imports.

    Module objects are explicit physical-role stand-ins; this establishes the
    path recipe, not imported-module origin or actual producer admission.
    """
    virtual=Path('/prospective-selected-producer')
    tree=ast.parse(source_path.read_bytes());ns={'Path':Path,'need':need,'__file__':str(virtual/'swdb'/source_path.name)}
    function=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='producer_paths'))
    imports=[n for n in tree.body if isinstance(n,ast.ImportFrom) and (n.module or '').startswith('swdb')]
    imports += [n for n in function.body if isinstance(n,ast.ImportFrom)]
    for node in imports:
        for alias in node.names:
            role=alias.asname or alias.name
            path=virtual/Path(node.module.replace('.','/'))/(alias.name+'.py')
            ns[role]=types.SimpleNamespace(__file__=str(path))
    if source_paths is not None:ns['dx100_checked_source']=types.SimpleNamespace(producer_paths=lambda:source_paths)
    function.body=[node for node in function.body if not isinstance(node,(ast.Import,ast.ImportFrom))]
    assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROUTE_PRODUCERS' for t in n.targets)]
    exec(compile(ast.Module(body=[*assignments,function],type_ignores=[]),'<exact-producer-path-leaf-no-project-import>','exec'),ns)
    return ns['producer_paths'](),virtual
source_roles,virtual=projected_producer_paths(OUT/'swdb/dx100_checked_source.py')
finite_roles,_=projected_producer_paths(OUT/'swdb/dx100_finite_trace.py',finite=True,source_paths=source_roles)
def roles(value):return {name:path.relative_to(virtual).as_posix() for name,path in sorted(value.items())}
source_map=roles(source_roles);finite_map=roles(finite_roles)
baseline=json.loads((WHOLE/'production-route-v5/profile/normal-producer-basis-v4.json').read_bytes())
all_members=sorted({row['relative'] for row in baseline['files']}|set(source_map.values())|set(finite_map.values())|set(selected))
member_rows=[];external_rows=[]
for relative in all_members:
    path=OUT/relative if relative in selected else PROJECT/relative
    actual=pin(path)
    member_rows.append({'relative':relative,'bytes':actual['bytes'],'sha256':actual['sha256']})
    if relative not in selected:external_rows.append({'relative':relative,'pin':actual})
recipe={'schema':'exact-source-and-finite-producer-role-recipe-1','date':'2026-10-16 ET',
    'SourceUnit_roles':source_map,'TraceUnit_roles':finite_map,'SourceUnit_role_count':len(source_map),
    'TraceUnit_role_count':len(finite_map),'distinct_physical_member_count':len(all_members),
    'fixed_paths_projected_from_real_leaf_functions_no_project_import':True,
    'imported_origin_or_published_commit_attested':False,'final_root_selected_producer_commit':None,
    'root_reported_current_published_base':ROOT_COMMIT,'files':member_rows,'unchanged_external_shared_files':external_rows}
write(HERE/'producer-member-recipe-v1.json',recipe)
basis={'schema':'prospective-coherent-SourceUnit-TraceUnit-producer-basis-1','date':'2026-10-16 ET',
    'root_base_commit':ROOT_COMMIT,'final_published_producer_commit':None,'actual_application_or_public_admission':False,'files':member_rows}
write(HERE/'profile/normal-producer-basis-union-v1.json',basis)
builder_path=WHOLE/'production-route-v5/profile/profile_builder_v4.py';text=builder_path.read_text();builder_edits=[]
for old,new in [("BASIS_SHA = 'c4cf8ed78e0a2085ea11d4d74a51979fb4d0dbc8e31d5892f16416d8a65b4212'", "BASIS_SHA = '"+pin(HERE/'profile/normal-producer-basis-union-v1.json')['sha256']+"'"),
    ('normal-producer-basis-v4.json','normal-producer-basis-union-v1.json')]:
    assert text.count(old)==1;builder_edits.append({'old':old,'new':new,'count':1});text=text.replace(old,new)
(HERE/'profile/profile_builder_union_v1.py').write_text(text)
write(HERE/'builder-inverse-v1.json',{'date':'2026-10-16 ET','basis':pin(builder_path),'replacements':builder_edits,
    'all_builder_functions_unchanged_except_basis_filename_in_producer_snapshot':True})
rows=[];patch=[]
for relative,source in sorted(selected.items()):
    target=OUT/relative;new=target.read_bytes();base=shared[relative]
    row={'relative':relative,'proposal':pin(target),'selected_frozen_source':pin(source),'lineage':origins[relative],
        'current_shared_base':base,'shared_written':False}
    rows.append(row)
    if base is not None and base['sha256']==sha(new):continue
    old='' if base is None else (PROJECT/relative).read_text()
    patch.extend(difflib.unified_diff(old.splitlines(True),new.decode().splitlines(True),
        fromfile='/dev/null' if base is None else 'a/swdb-project/'+relative,tofile='b/swdb-project/'+relative))
(HERE/'production-union-v1.patch').write_text(''.join(patch))
write(HERE/'production-paths-and-bases-v1.json',{'date':'2026-10-16 ET','root_reported_current_published_base':ROOT_COMMIT,
    'Git_readback_or_shared_apply_performed':False,'paths':rows,'producer_recipe':pin(HERE/'producer-member-recipe-v1.json'),
    'shared_fresh_overlap_check_before_apply_required':True})
print(json.dumps({'proposed_paths':len(rows),'patch_bytes':(HERE/'production-union-v1.patch').stat().st_size,
    'source_roles':len(source_map),'finite_roles':len(finite_map),'basis_members':len(member_rows),'builder':pin(HERE/'profile/profile_builder_union_v1.py')}))
