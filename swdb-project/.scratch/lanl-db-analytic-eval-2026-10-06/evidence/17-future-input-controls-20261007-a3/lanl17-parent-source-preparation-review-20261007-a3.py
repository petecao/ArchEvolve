"""Independent source-only pins/AST verification; no selected control execution."""
import ast,datetime,difflib,hashlib,json,pathlib
P=pathlib.Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(path,digest,bytes_count=None):
    p=P(path);assert p.is_file() and not p.is_symlink()
    raw=p.read_bytes();assert sha(raw)==digest
    if bytes_count is not None:assert len(raw)==bytes_count
    return {'path':str(p),'bytes':len(raw),'sha256':digest}
def proof(path,digest):
    d=json.loads(P(path).read_bytes());assert d['identity_sha256']==digest
    assert sha(json.dumps({k:v for k,v in d.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())==digest
    return d
def recursive_pins(value):
    if isinstance(value,dict):
        if {'path','bytes','sha256'}<=set(value):pin(value['path'],value['sha256'],value['bytes'])
        for child in value.values():recursive_pins(child)
    elif isinstance(value,list):
        for child in value:recursive_pins(child)
sources=[
pin('/private/tmp/lanl17_assemble_selected_actual_input_pins_r1_20261007.py','de669e4c0928876f9d033f6d9c1fc820ab3a1eb915aba20c5b6755b9866d7e6a',33584),
pin('/private/tmp/lanl17_write_parent_input_specification_20261007.py','339ea0dc1abb6778f0f016e9c03f2b29c5f1916154b668f5416747b2768a9231',11868),
pin('/private/tmp/lanl17_parent_capture_projection_producer_a3_20261007.py','32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6',46165)]
prep=proof('/private/tmp/lanl17-accepted-pins-and-spec-writer-source-preparation-20261007-r1.json','5575c718cb6f2daed42e34f60bd171f15008ce4142e63d06924d6e9f46f2ea6a');recursive_pins(prep)
a3=proof('/private/tmp/lanl17-parent-capture-producer-source-proof-20261007-a3.json','64fa86ec7bda1032360e6b2500649d7b0e89069e3956d7f6bf302ce5891d1880');recursive_pins(a3)
a2=proof('/private/tmp/lanl17-parent-capture-producer-source-proof-20261007-a2.json','c4ce07ad8c2a0233ec970e9ecd36a503aa923909ac96dc51fbb8c60c38958ee1');recursive_pins(a2)
a1=proof('/private/tmp/lanl17-parent-capture-producer-source-proof-20261007.json','b00291db64339e7c8564c8efd1937e82ca37fc4a5bfcfed51ff5c17d96fda081');recursive_pins(a1)
original=proof('/private/tmp/lanl17-accepted-pins-assembler-source-preparation-20261007.json','4080fc6f9305e9b08b3ab2f58cd8d3001ae121303b1324bb7a1745578d9e180a');recursive_pins(original)
for s in sources:
    raw=P(s['path']).read_bytes();ast.parse(raw);compile(raw,s['path'],'exec')
old=P('/private/tmp/lanl17_assemble_selected_actual_input_pins_20261007.py').read_text()
new=P(sources[0]['path']).read_text()
diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='/private/tmp/lanl17_assemble_selected_actual_input_pins_20261007.py',tofile=sources[0]['path']))
assert diff==P('/private/tmp/lanl17-accepted-pins-assembler-r1-20261007.diff').read_text()
assert sum(line.startswith('@@ ') for line in diff.splitlines())==3
producer_old=P('/private/tmp/lanl17_parent_capture_projection_producer_a2_20261007.py').read_text()
producer_new=P(sources[2]['path']).read_text()
producer_diff=''.join(difflib.unified_diff(producer_old.splitlines(True),producer_new.splitlines(True),fromfile='lanl17_parent_capture_projection_producer_a2_20261007.py',tofile='lanl17_parent_capture_projection_producer_a3_20261007.py'))
assert producer_diff==P('/private/tmp/lanl17-parent-capture-producer-custody-corrections-20261007-a3.patch').read_text()
trees=[ast.parse(producer_old),ast.parse(producer_new)]
def named(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
before,after=map(named,trees)
assert set(after)-set(before)=={'returned_bytes','manifest_output_roots'}
assert {k for k in before if before[k]!=after[k]}=={'Inputs','main'}
auditor=ast.parse(P('/private/tmp/lanl17_selected_record_trajectory_auditor_a2r1s1_20261007.py').read_bytes())
required={'RecordLoader','no_duplicates','public_token','public_scalar','public_fields','excluded_fields','project_calls','project_candidate','project_iteration','project_state'}
original_named=named(auditor)
assert all(after[k]==original_named[k] for k in required)
def assignments(tree):return {ast.unparse(n.targets[0]):ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.Assign)}
oa,na=assignments(auditor),assignments(trees[1])
assert all(na[k]==oa[k] for k in ('RecordLoader.yaml_implicit_resolvers','CALL_KEYS','CANDIDATE_KEYS','STATE_KEYS','PROJECTION_CONTRACT'))
def constructor(tree):return [ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.Expr) and ast.unparse(n).startswith('RecordLoader.add_constructor(')]
assert constructor(auditor)==constructor(trees[1]) and len(constructor(auditor))==1
review={'format':'swdb.lanl17-parent-source-preparation-review.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_ensure_ascii':True,
        'selected_prospective_sources':sources,'parent_full_source_and_diff_read':True,
        'independent_checks':{'all_explicit_original_file_pins':True,'five_original_preparation_seals_explicit_ensure_ascii_true':True,'assembler_exact_three_hunk_diff':True,'producer_exact_narrow_diff':True,'producer_changed_only_Inputs_main_and_two_new_helpers':True,'sixteen_safe_projection_AST_symbols_match_unchanged_auditor':True,'syntax_code_objects_without_execution':True},
        'approval':'Selected prospective source preparation only; each future actual request, original-input inventory and parent specification requires separate original-artifact review before use.',
        'original_a1_a2_chronology':'Preserved preparation originals; superseded for prospective runtime. Original proofs remain source-only, not actual admission.',
        'source_contract_review':['M2 helper28d/source R/F6/policy/identity binds output exclusion of exact source/raw/four campaign paths.','Parsed request and originals verify exact bounded returned bytes plus fd/path identity before parsing.','Own producer source/request/originals rechecked before publication and success; assembler own source before publication.','YAML exceptions use bounded class/message digest diagnostics.','Timestamp resolvers and explicit original canonical policies agree with unchanged auditor.','Spec writer adds only new identity to already parent-reviewed unsealed template; no observations/templates invented.'],
        'selected_controls_imported_or_executed':False,'actual_inputs_constructed_or_read':False,'Store_provider_native_remote_actions':False,'synthetic_runtime_tests':False,'scientific_admission':False}
review['identity_sha256']=sha(json.dumps(review,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
out=P('/private/tmp/lanl17-parent-source-preparation-review-20261007-a3.json');assert not out.exists()
out.write_text(json.dumps(review,indent=2,ensure_ascii=True,allow_nan=False)+'\n')
print(json.dumps({'path':str(out),'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'identity_sha256':review['identity_sha256'],'scope':'Independent source-only verification, no runtime admission'}))
